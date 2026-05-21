#!/usr/bin/env python3
"""
Research helper using Google Gemini
Usage: python scripts/research.py --topic "Warren Buffett ถือเงินสด"
Outputs structured research notes for script generation
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


RESEARCH_PROMPT = """คุณเป็นนักวิจัยที่ช่วยสร้างเนื้อหาวิดีโอการเงินภาษาไทย

หัวข้อ: {topic}

ทำการวิจัยและสรุปเป็น JSON ดังนี้:
{{
  "topic": "{topic}",
  "key_facts": ["ข้อเท็จจริงสำคัญ 1", "2", "3", ...],
  "timeline": [
    {{"date": "วันที่", "event": "เหตุการณ์"}}
  ],
  "statistics": [
    {{"label": "ชื่อสถิติ", "value": "ตัวเลข", "source": "แหล่งที่มา"}}
  ],
  "expert_quotes": [
    {{"person": "ชื่อ", "quote": "คำพูด", "context": "บริบท"}}
  ],
  "chapter_ideas": [
    {{"title": "ชื่อหัวข้อ", "angle": "มุมมอง", "key_message": "ข้อความหลัก"}}
  ],
  "controversy_or_debate": "ประเด็นถกเถียงถ้ามี",
  "actionable_takeaways": ["สิ่งที่คนดูทำได้ 1", "2", "3"]
}}

ตอบเป็น JSON เท่านั้น"""


def research_with_gemini(topic: str) -> dict:
    try:
        import google.generativeai as genai
    except ImportError:
        print("❌ Run: pip install google-generativeai")
        sys.exit(1)

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Set GOOGLE_API_KEY in .env")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    print(f"🔍 Researching: {topic}")
    print("   Using Gemini 2.5 Flash...")

    response = model.generate_content(
        RESEARCH_PROMPT.format(topic=topic),
        generation_config={"temperature": 0.3, "max_output_tokens": 4000}
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--output", default="output/research.json")
    args = parser.parse_args()

    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    research = research_with_gemini(args.topic)

    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(research, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Research saved: {output_path}")
    print(f"   Key facts : {len(research.get('key_facts', []))}")
    print(f"   Chapters  : {len(research.get('chapter_ideas', []))}")
    print(f"\n📋 Chapter Ideas:")
    for ch in research.get("chapter_ideas", []):
        print(f"   → {ch['title']}")

    print(f"\n💡 Use this research with:")
    print(f"   python scripts/generate_script.py --topic '{args.topic}'")


if __name__ == "__main__":
    main()
