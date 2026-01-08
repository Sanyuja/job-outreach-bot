import os
import glob
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set in .env")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

BASE_DIR = os.path.dirname(__file__)
SAMPLES_DIR = os.path.join(BASE_DIR, "style_samples")
PROFILE_PATH = os.path.join(BASE_DIR, "style_profile.json")


def load_samples(max_chars_per_sample: int = 1500):
    files = sorted(glob.glob(os.path.join(SAMPLES_DIR, "*.txt")))
    texts = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read().strip()
            if not txt:
                continue
            texts.append(txt[:max_chars_per_sample])
    if not texts:
        raise RuntimeError(f"No .txt files found in {SAMPLES_DIR}")
    return texts


def build_style_profile():
    samples = load_samples()
    joined = "\n\n--- SAMPLE ---\n\n".join(samples)

    prompt = f"""
You are a writing style analyst.

You will be given multiple messages written by the SAME person (Sanyuja).
Your job is to analyze how she writes and then summarize her style.

Messages (verbatim):

{joined}

Return STRICTLY a JSON object with these keys:
- "tone": short description of overall tone (e.g., "warm, confident, direct")
- "formality": "informal" | "semi-formal" | "formal"
- "sentence_style": notes on average sentence length, rhythm, structure
- "voice_principles": list of short bullets with rules like "use first person", "show rather than tell"
- "phrases_to_use": list of words/phrases she naturally uses
- "phrases_to_avoid": list of words/phrases that do NOT sound like her (e.g. corporate cliches)
- "do_nots": list of behavioral rules (e.g. "do not sound desperate", "do not over-apologize")

Make it concise but specific. Do NOT wrap in markdown. Only output JSON.
    """

    completion = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct",
        messages=[
            {"role": "system", "content": "You are a precise writing style analyst. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content
    profile = json.loads(content)

    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    print(f"✅ Style profile saved to {PROFILE_PATH}")


def load_style_profile():
    if not os.path.exists(PROFILE_PATH):
        raise RuntimeError(
            f"Style profile not found at {PROFILE_PATH}. Run this file to generate it first."
        )
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    build_style_profile()
