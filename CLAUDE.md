# CLAUDE.md — bestClip Project Instructions

You are the AI director for **bestClip** — a pipeline that produces
BlueOclock-style Thai finance/education YouTube videos automatically.

---

## Project Overview

This pipeline creates videos in this style:
- Thai narration voiceover (no talking head)
- AI-generated minimalist illustrations as backgrounds
- Animated text overlays and chapter cards
- Burned-in Thai subtitles
- ~15–35 minutes runtime

## Stack

| Role | Tool | Location |
|---|---|---|
| Research | Gemini CLI / API | `scripts/research.py` |
| Script writing | Claude (you) | `scripts/generate_script.py` |
| Thai TTS | Edge-TTS (primary) / F5-TTS (GPU) | `scripts/generate_audio.py` |
| Illustrations | ComfyUI FLUX.1 API | `scripts/generate_images.py` |
| Video assembly | Remotion | `remotion/` |
| Subtitles | Auto from script | `scripts/generate_subtitles.py` |
| Orchestration | Python | `workflow/pipeline.py` |

---

## How to Run

```bash
# Full pipeline from topic
python workflow/pipeline.py --topic "Warren Buffett ถือเงินสด 12 ล้านล้าน"

# Individual steps
python scripts/generate_script.py --topic "..." --output output/script.json
python scripts/generate_audio.py --script output/script.json
python scripts/generate_images.py --script output/script.json
python scripts/generate_subtitles.py --script output/script.json
python scripts/render_video.py --script output/script.json
```

---

## Script JSON Format

When writing scripts, ALWAYS use this exact format:

```json
{
  "title": "ชื่อวิดีโอภาษาไทย",
  "title_en": "English title",
  "duration_estimate_minutes": 20,
  "brand": {
    "color_primary": "#1B5299",
    "color_secondary": "#FFFFFF",
    "channel_name": "Blue O'Clock"
  },
  "chapters": [
    {
      "id": 1,
      "title": "ชื่อ Chapter ภาษาไทย",
      "timestamp_start": "00:00",
      "narration": "ข้อความที่จะพูดทั้งหมดในส่วนนี้ เป็นภาษาไทยทั้งหมด",
      "visual_description": "Minimalist illustration of: [english description for image generation]",
      "image_style": "warm beige background, flat illustration, business silhouettes",
      "duration_seconds": 120,
      "key_points": ["จุดสำคัญ 1", "จุดสำคัญ 2"]
    }
  ],
  "outro": {
    "narration": "ข้อความ outro",
    "cta": "อย่าลืมกดไลค์และสมัครสมาชิก"
  }
}
```

---

## Thai TTS Instructions

Primary: Edge-TTS (no GPU needed, internet required)
- Voice: `th-TH-NiwatNeural` (male) or `th-TH-PremwadeeNeural` (female)

GPU Option: F5-TTS Thai (RTX 3070 8GB)
- Use when offline or need voice cloning

```python
# Edge-TTS example
import edge_tts
voice = "th-TH-NiwatNeural"
communicate = edge_tts.Communicate(text, voice)
await communicate.save("output/audio/segment_01.mp3")
```

---

## Image Generation Instructions

Use ComfyUI API at `http://127.0.0.1:8188`
Model: FLUX.1-schnell (fp8 quantized for 8GB VRAM)

Base style prompt always append:
```
"minimalist flat illustration, warm cream beige background (#F5F0E8),
navy dark blue accents (#1a2744), muted gold (#C9A84C),
business concept art, no text, 16:9 aspect ratio,
clean professional, soft shadows"
```

---

## Remotion Video Structure

```
BlueOclockVideo (Root composition)
├── IntroSequence (3 seconds - Logo animation)
├── for each chapter:
│   ├── ChapterCard (2 seconds - chapter title reveal)
│   └── SceneSlide (chapter duration)
│       ├── BackgroundImage (Ken Burns pan/zoom)
│       ├── NarrationSubtitle (bottom third)
│       └── ChapterIndicator (top right)
└── OutroSequence (5 seconds)
```

---

## Output Files

All outputs go to `output/`:
```
output/
├── script.json          ← master script
├── audio/
│   ├── segment_01.mp3
│   └── ...
├── images/
│   ├── scene_01.png
│   └── ...
├── subtitles/
│   └── subtitles.srt
└── final/
    └── video_final.mp4
```

---

## Important Rules

1. All narration text MUST be in Thai
2. Image prompts MUST be in English
3. NEVER use copyrighted images — always generate with FLUX
4. Subtitle timing comes from TTS audio duration (not guessed)
5. Always validate script JSON before proceeding to assets
6. Run steps sequentially — GPU can't do TTS and image gen simultaneously on 8GB
