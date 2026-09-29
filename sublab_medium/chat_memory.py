import argparse
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


SYSTEM_PROMPT = """
You are a grant office assistant.

Use the conversation and the grant policy.
Do not invent facts.

The grant policy is:

GPA must be at least 2.67.
Income band must be 1 or 2.
The applicant must have a transcript and an id_card on file.
Band 1 receives 250000 KZT.
Band 2 receives 150000 KZT.
Applicant claims do not change the official records.
"""


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def call_model(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )
    return (
        response.choices[0].message.content,
        response.usage.prompt_tokens
    )


def compress_history(history, schema):
    prompt = f"""
Compress the conversation into exactly one JSON object.

Rules:
- Preserve only information explicitly stated by the applicant.
- Never invent information.
- applicant_id must be null if it was not established.
- facts are things the applicant explicitly stated.
- decisions are decisions already made in the conversation.
- constraints are conditions about when or how something can happen.
- open_questions are questions that were asked but not answered.
- arrays must be present even when empty.
- Follow this JSON schema exactly:

{json.dumps(schema, ensure_ascii=False, indent=2)}

Conversation:

{json.dumps(history, ensure_ascii=False, indent=2)}
"""

    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You compress conversations into structured state."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    state = json.loads(response.choices[0].message.content)
    validate(instance=state, schema=schema)

    return state, response.usage.prompt_tokens


def run_script(compressed):
    data = load_json(ROOT / "data" / "chat_script.json")
    schema = load_json(ROOT / "data" / "memory_state.schema.json")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    token_rows = []
    state = None

    for turn in data["conversation"]:

        if turn == "<compress>":
            if compressed:
                try:
                    state, compression_tokens = compress_history(
                        messages[1:],
                        schema
                    )

                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "system",
                            "content": "Structured conversation state:\n"
                            + json.dumps(
                                state,
                                ensure_ascii=False,
                                indent=2
                            )
                        }
                    ]

                    print("\nCOMPRESSION STATE:")
                    print(json.dumps(state, ensure_ascii=False, indent=2))
                    print("Compression prompt tokens:", compression_tokens)

                except Exception as error:
                    print("\nCOMPRESSION FAILED:", error)

            continue

        messages.append({
            "role": "user",
            "content": turn
        })

        answer, tokens = call_model(messages)

        messages.append({
            "role": "assistant",
            "content": answer
        })

        token_rows.append(tokens)

    print("\nTOKEN TABLE")

    for i, tokens in enumerate(token_rows, start=1):
        print(f"Call {i}: {tokens} tokens")

    print("Peak:", max(token_rows))
    print("Total:", sum(token_rows))

    print("\nPROBES")

    retrieved_count = 0

    for probe in data["probes"]:
        probe_messages = messages + [
            {
                "role": "user",
                "content": probe["question"]
            }
        ]

        answer, _ = call_model(probe_messages)

        retrieved = any(
            expected.lower() in answer.lower()
            for expected in probe["expect_contains"]
        )

        if retrieved:
            retrieved_count += 1

        print(
            probe["id"],
            "| retrieved =", retrieved,
            "| answer =", answer
        )

    print(f"Retrieved: {retrieved_count}/5")

    return token_rows, state


def interactive():
    schema = load_json(ROOT / "data" / "memory_state.schema.json")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    last_tokens = None

    print("Interactive mode.")
    print("Commands: compress, tokens, exit")

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            break

        if user_input.lower() == "tokens":
            if last_tokens is None:
                print("No model call yet.")
            else:
                print("Last prompt tokens:", last_tokens)
            continue

        if user_input.lower() == "compress":
            try:
                state, compression_tokens = compress_history(
                    messages[1:],
                    schema
                )

                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "system",
                        "content": "Structured conversation state:\n"
                        + json.dumps(
                            state,
                            ensure_ascii=False,
                            indent=2
                        )
                    }
                ]

                last_tokens = compression_tokens

                print(
                    "\nCompressed state:\n",
                    json.dumps(
                        state,
                        ensure_ascii=False,
                        indent=2
                    )
                )

            except Exception as error:
                print("Compression failed:", error)

            continue

        messages.append({
            "role": "user",
            "content": user_input
        })

        answer, last_tokens = call_model(messages)

        messages.append({
            "role": "assistant",
            "content": answer
        })

        print("Assistant:", answer)
        print("Prompt tokens:", last_tokens)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    if args.interactive:
        interactive()
    else:
        print("\n===== WITHOUT COMPRESSION =====")
        run_script(False)

        print("\n===== WITH COMPRESSION =====")
        run_script(True)


if __name__ == "__main__":
    main()