import json
import os
from pathlib import Path

from dotenv import load_dotenv
from jsonschema import validate
from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]

load_dotenv(ROOT / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-5.6-luna"


EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {"type": "string"},
        "full_name": {"type": ["string", "null"]},
        "degree": {"type": ["string", "null"]},
        "graduation_year": {"type": ["integer", "null"]},
        "gpa_4_scale": {"type": ["number", "null"]},
        "gpa_original": {"type": ["number", "null"]},
        "gpa_original_scale": {"type": ["string", "null"]},
        "languages": {
            "type": "array",
            "items": {"type": "string"}
        },
        "published_peer_reviewed_outputs": {"type": ["integer", "null"]},
        "relevant_experience_months": {"type": ["integer", "null"]},
        "evidence": {
            "type": "object",
            "additionalProperties": {"type": ["string", "null"]}
        },
        "ambiguities": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [
        "candidate_id",
        "full_name",
        "degree",
        "graduation_year",
        "gpa_4_scale",
        "gpa_original",
        "gpa_original_scale",
        "languages",
        "published_peer_reviewed_outputs",
        "relevant_experience_months",
        "evidence",
        "ambiguities"
    ],
    "additionalProperties": False
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def call_model(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


def extract_candidate(candidate_id, story):
    prompt = f"""
Extract a structured CV from this scholarship application.

Candidate ID: {candidate_id}

Rules:
- A fact the story does not state is null. Never estimate.
- Never infer GPA from a degree, university, distinction, or overall impression.
- If GPA uses another scale, convert it to a 4.0 scale and record the original scale.
- A paper counts as published only if the story says published or accepted.
- Submitted, under review, in preparation, planned and in press are NOT published.
- Record non-published outputs separately when relevant.
- Count relevant experience in months.
- Overlapping periods count only once.
- A period without dates is not countable.
- If the story contradicts itself, do not resolve it and do not average it.
  Set the contradicted field to null and record the contradiction in ambiguities.
- Every non-null extracted field must have an evidence quote.
- Return exactly one JSON object following the schema.

Schema:
{json.dumps(EXTRACTION_SCHEMA, ensure_ascii=False, indent=2)}

Story:
{story}
"""

    result = call_model([
        {
            "role": "system",
            "content": "You extract factual structured CV data from application stories."
        },
        {
            "role": "user",
            "content": prompt
        }
    ])

    validate(instance=result, schema=EXTRACTION_SCHEMA)
    return result


def score_candidates(records, rubric):
    prompt = f"""
Score the scholarship candidates using this rubric.

Rubric:
{json.dumps(rubric, ensure_ascii=False, indent=2)}

Candidate records:
{json.dumps(records, ensure_ascii=False, indent=2)}

Return exactly one JSON object with a "scores" array.

For every candidate provide:
- candidate_id
- academic: integer from 0 to 5
- research: integer from 0 to 5
- experience: integer from 0 to 5

Do not calculate weighted totals.
Do not choose a winner.
Return only the three criterion scores for each candidate.
"""

    schema = {
        "type": "object",
        "properties": {
            "scores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "candidate_id": {"type": "string"},
                        "academic": {"type": "integer", "minimum": 0, "maximum": 5},
                        "research": {"type": "integer", "minimum": 0, "maximum": 5},
                        "experience": {"type": "integer", "minimum": 0, "maximum": 5}
                    },
                    "required": [
                        "candidate_id",
                        "academic",
                        "research",
                        "experience"
                    ],
                    "additionalProperties": False
                }
            }
        },
        "required": ["scores"],
        "additionalProperties": False
    }

    result = call_model([
        {
            "role": "system",
            "content": "You score scholarship candidates using the supplied rubric."
        },
        {
            "role": "user",
            "content": prompt
        }
    ])

    validate(instance=result, schema=schema)
    return result["scores"]


def prose_ranking(records, rubric):
    return call_model([
        {
            "role": "system",
            "content": (
                "You are evaluating candidates using the provided rubric. "
                "Return your answer as JSON."
            )
        },
        {
            "role": "user",
            "content": (
                "Based on the extracted candidate records and rubric below, "
                "answer who should win. Return JSON with these fields: "
                "ranking, winner, and reasoning.\n\n"
                f"Rubric:\n{json.dumps(rubric, ensure_ascii=False, indent=2)}\n\n"
                f"Candidates:\n{json.dumps(records, ensure_ascii=False, indent=2)}"
            )
        }
    ])


def main():
    rubric = load_json(ROOT / "data" / "candidate_rubric.json")
    candidates_dir = ROOT / "data" / "candidates"

    records = []

    print("===== EXTRACTION =====")

    for path in sorted(candidates_dir.glob("story-*.md")):
        candidate_id = path.stem
        story = path.read_text(encoding="utf-8")

        try:
            record = extract_candidate(candidate_id, story)
            records.append(record)

            print(f"\n{candidate_id}")
            print(json.dumps(record, ensure_ascii=False, indent=2))

        except Exception as error:
            print(f"\n{candidate_id} FAILED:", error)

    print("\n===== SCORES =====")

    scores = score_candidates(records, rubric)

    results = []

    for score in scores:
        total = round(
            0.5 * score["academic"]
            + 0.3 * score["research"]
            + 0.2 * score["experience"],
            2
        )

        results.append({
            **score,
            "weighted_total": total
        })

    for result in results:
        print(
            result["candidate_id"],
            "| academic =", result["academic"],
            "| research =", result["research"],
            "| experience =", result["experience"],
            "| total =", result["weighted_total"]
        )

    winner = max(results, key=lambda x: x["weighted_total"])

    print("\nWinner computed by code:", winner["candidate_id"])

    print("\n===== PROSE RANKING =====")

    prose = prose_ranking(records, rubric)
    print(json.dumps(prose, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()