import json
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
MODEL = "gpt-5.6-luna"

load_dotenv(ROOT / ".env")
_client = None


def client():
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def load_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def chat(messages, json_mode=False):
    kwargs = {"model": MODEL, "messages": messages}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    r = client().chat.completions.create(**kwargs)
    return r.choices[0].message.content, r.usage


def parse_json(text):
    if text is None:
        return None
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return None