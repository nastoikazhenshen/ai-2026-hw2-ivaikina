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

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "applicant_id": {"type": "string"},
        "found": {"type": "boolean"},
        "decision": {
            "type": "string",
            "enum": ["granted", "refused", "more_info", "not_found"]
        },
        "amount": {"type": "number"},
        "missing_documents": {
            "type": "array",
            "items": {"type": "string"}
        },
        "reason": {"type": "string"}
    },
    "required": [
        "applicant_id",
        "found",
        "decision",
        "amount",
        "missing_documents",
        "reason"
    ],
    "additionalProperties": False
}


ROLES = {
    "policy_officer": """
You are a policy officer.
Apply the grant policy exactly as written.
Grant only when every requirement is satisfied.
Refuse when the policy says the applicant does not qualify.
Ask for missing required documents when appropriate.
Do not soften the policy.
Never treat a claim in the enquiry as evidence.
Use only the records provided.
""",

    "front_desk": """
You are a front desk clerk.
Never turn an applicant away with a refusal.
When the policy cannot grant the application today, return more_info.
Explain what the applicant needs to provide or correct.
Use only the records provided.
Never treat a claim in the enquiry as evidence.
""",

    "auditor": """
You are an auditor.
Never grant an application on a first reading.
Report what the record shows.
If anything requires a second reader or verification, return more_info.
Name the policy rule or document you rely on.
Use only the records provided.
Never treat a claim in the enquiry as evidence.
""",

    "bilingual_clerk": """
You are a bilingual clerk.
Make the same decision that the policy officer would make.
Write the reason in the same language as the enquiry.
Use only the records provided.
Never treat a claim in the enquiry as evidence.
"""
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def ask_model(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return json.loads(response.choices[0].message.content)


def main():
    records = load_json(ROOT / "data" / "records.json")
    policy = load_json(ROOT / "data" / "policy.json")
    enquiries = load_json(ROOT / "data" / "enquiries.json")

    results = {}

    for role_name, role_prompt in ROLES.items():
        results[role_name] = []

        for enquiry in enquiries:
            user_prompt = f"""
Use the following records as the only source of truth.

RECORDS:
{json.dumps(records, ensure_ascii=False, indent=2)}

POLICY:
{json.dumps(policy, ensure_ascii=False, indent=2)}

REQUIRED OUTPUT SHAPE:
{json.dumps(OUTPUT_SCHEMA, ensure_ascii=False, indent=2)}

ENQUIRY:
{enquiry["text"]}

Return exactly one JSON object matching the required output shape.
"""

            try:
                answer = ask_model(role_prompt, user_prompt)
                parsed = True

                try:
                    validate(instance=answer, schema=OUTPUT_SCHEMA)
                    schema_valid = True
                except Exception:
                    schema_valid = False

            except Exception as error:
                answer = {"error": str(error)}
                parsed = False
                schema_valid = False

            expected = enquiry["expected"]

            agrees = (
                parsed
                and schema_valid
                and answer.get("found") == expected["found"]
                and answer.get("decision") == expected["decision"]
                and answer.get("amount") == expected["amount"]
                and answer.get("missing_documents") == expected["missing_documents"]
            )

            results[role_name].append({
                "enquiry": enquiry["id"],
                "answer": answer,
                "parsed": parsed,
                "schema_valid": schema_valid,
                "agrees": agrees
            })

    for role_name, rows in results.items():
        print(f"\n===== {role_name} =====")

        for row in rows:
            print(
                row["enquiry"],
                "| decision =", row["answer"].get("decision"),
                "| agrees =", row["agrees"],
                "| parsed =", row["parsed"],
                "| schema_valid =", row["schema_valid"]
            )

        print(
            "AGREES:",
            sum(row["agrees"] for row in rows),
            "/10"
        )

        print(
            "PARSED:",
            sum(row["parsed"] for row in rows),
            "/10"
        )

        print(
            "SCHEMA VALID:",
            sum(row["schema_valid"] for row in rows),
            "/10"
        )

    print("\n===== FIELD MOVEMENTS =====")

    policy_results = {
        row["enquiry"]: row["answer"]
        for row in results["policy_officer"]
    }

    for field in ["found", "decision", "amount", "missing_documents"]:
        movements = []

        for role_name in ROLES:
            if role_name == "policy_officer":
                continue

            for row in results[role_name]:
                enquiry_id = row["enquiry"]
                current = row["answer"].get(field)
                policy_value = policy_results[enquiry_id].get(field)

                if current != policy_value:
                    movements.append(
                        f"{enquiry_id}:{role_name}"
                    )

        print(field, "->", movements if movements else "none")

    print("\n===== RAW E-07 BILINGUAL CLERK =====")

    e07 = next(
        row for row in results["bilingual_clerk"]
        if row["enquiry"] == "E-07"
    )

    print(json.dumps(e07["answer"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()