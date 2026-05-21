#!/usr/bin/env python3
"""
Step 1: Generate Thai video script using Claude API
Usage: python scripts/generate_script.py --topic "Warren Buffett ถือเงินสด" --output output/script.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("❌ Run: pip install anthropic")
    sys.exit(1)


SCRIPT_PROMPT = """คุณคือนักเขียนสคริปต์วิดีโอ YouTube ภาษาไทยสำหรับช่อง Blue O'Clock
สไตล์วิดีโอ: Deep-dive analysis การเงิน/ธุรกิจ เหมือน BlueOclock บน YouTube

สร้าง script วิดีโอยาว 15-20 นาทีเรื่อง: {topic}

กฎสำคัญ:
- Narration ต้องเป็นภาษาไทยทั้งหมด เป็นธรรมชาติ ฟังแล้วไหลลื่น
- ต้องมี hook ที่น่าสนใจใน chapter แรก
- แต่ละ chapter ควรมีเวลา 90-150 วินาที
- visual_description ต้องเป็นภาษาอังกฤษสำหรับ AI image generation
- ต้องมี 8-12 chapters
- อย่าใส่ตัวเลขหรือสัญลักษณ์พิเศษที่ TTS อ่านไม่ออก

ตอบกลับเป็น JSON เท่านั้น ไม่มี markdown backticks ไม่มีข้อความอื่น:

{{
  "title": "ชื่อวิดีโอภาษาไทยที่ดึงดูด",
  "title_en": "English subtitle",
  "topic": "{topic}",
  "created_at": "{timestamp}",
  "duration_estimate_minutes": 20,
  "brand": {{
    "color_primary": "#1B5299",
    "color_secondary": "#FFFFFF",
    "channel_name": "Your Channel"
  }},
  "intro": {{
    "narration": "ข้อความเปิดวิดีโอ ดึงดูดคนดู สั้นๆ 15-20 วินาที",
    "visual_description": "dramatic opening visual description in English",
    "duration_seconds": 20
  }},
  "chapters": [
    {{
      "id": 1,
      "title": "ชื่อ Chapter",
      "timestamp_start": "00:00",
      "narration": "เนื้อหาการพูดทั้งหมดในส่วนนี้ ยาวพอสำหรับ 90-120 วินาที",
      "visual_description": "flat minimalist illustration of: [scene in english], warm beige background",
      "image_keyword": "short 3-word image search keyword",
      "duration_seconds": 110,
      "key_points": ["จุดสำคัญ"]
    }}
  ],
  "outro": {{
    "narration": "บทสรุปและ call to action",
    "duration_seconds": 30
  }}
}}"""


def generate_script(topic: str, output_path: str):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    print(f"📝 Generating script for: {topic}")
    print("   Calling Claude API...")

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": SCRIPT_PROMPT.format(
                topic=topic,
                timestamp=datetime.now().isoformat()
            )
        }]
    )

    raw = message.content[0].text.strip()

    # Clean up if model added backticks
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    try:
        script = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        # Save raw for debugging
        Path("output/script_raw.txt").write_text(raw, encoding="utf-8")
        print("   Raw output saved to output/script_raw.txt")
        sys.exit(1)

    # Add computed timestamps
    total_seconds = 0
    for ch in script.get("chapters", []):
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        ch["timestamp_start"] = f"{minutes:02d}:{seconds:02d}"
        total_seconds += ch.get("duration_seconds", 120)

    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Script saved: {output_path}")
    print(f"   Title   : {script['title']}")
    print(f"   Chapters: {len(script['chapters'])}")
    print(f"   Est. Duration: ~{script.get('duration_estimate_minutes', '?')} min")
    print("\n📋 Chapter List:")
    for ch in script["chapters"]:
        print(f"   [{ch['timestamp_start']}] {ch['title']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True, help="Video topic in Thai")
    parser.add_argument("--output", default="output/script.json")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ Set ANTHROPIC_API_KEY in .env file")
        sys.exit(1)

    generate_script(args.topic, args.output)


if __name__ == "__main__":
    # Load .env
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    main()
