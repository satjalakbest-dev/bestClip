# bestClip

ระบบสร้างวิดีโอ YouTube ภาษาไทยสายการเงิน/ธุรกิจแบบอัตโนมัติ สไตล์ Chie-Su / BlueOclock: สคริปต์ภาษาไทย, เสียงบรรยาย AI, ภาพประกอบ AI, ซับไตเติล และไฟล์ MP4 พร้อมใช้งาน

> สถานะปัจจุบัน: pipeline หลักเป็น Python + FFmpeg และมีโครง AI Studio v2 สำหรับแยกงานเป็น project folder พร้อม style bible, voice direction, visual brief และ QA gates

---

## Quick Start

```powershell
# 1) ติดตั้ง Python dependencies
pip install -r requirements.txt

# 2) สร้างไฟล์ environment
Copy-Item .env.example .env
# แก้ .env แล้วใส่ ANTHROPIC_API_KEY อย่างน้อย

# 3) ติดตั้ง FFmpeg และตรวจว่าเรียกได้จาก PATH
ffmpeg -version

# 4) รัน pipeline เต็มจาก topic
python workflow/pipeline.py --topic "Warren Buffett ถือเงินสด 12 ล้านล้าน"
```

ผลลัพธ์หลัก:

```text
output/final/video_final.mp4
```

ถ้ามี `script.json` อยู่แล้ว สามารถข้ามขั้นเขียนสคริปต์ได้:

```powershell
python workflow/pipeline.py --script output/script.json
```

---

## Pipeline ปัจจุบัน

```text
Topic
  |
  v
scripts/generate_script.py       Claude API -> output/script.json
  |
  v
scripts/generate_audio.py        Edge-TTS หรือ F5-TTS -> output/audio/*
  |
  v
scripts/generate_subtitles.py    SRT/VTT จาก narration + audio duration
  |
  v
scripts/generate_images.py       Gemini/Codex/ComfyUI/Pollinations/placeholder
  |
  v
scripts/render_video.py          FFmpeg render -> output/final/video_final.mp4
```

หมายเหตุสำคัญ:

- `workflow/pipeline.py` ยังไม่เรียก `scripts/research.py` อัตโนมัติ ต้องรัน research แยกเองถ้าต้องการ
- renderer ที่ใช้จริงตอนนี้คือ `scripts/render_video.py` ด้วย FFmpeg ไม่ใช่ Remotion
- `generate_audio.py` และ `generate_images.py` รองรับ v2 artifacts เช่น voice direction และ visual brief แล้ว แต่ pipeline หลักยังไม่ได้ส่ง flag เหล่านี้ให้อัตโนมัติ

---

## Requirements

### จำเป็น

| Component | ใช้ทำอะไร |
|---|---|
| Python 3.10+ | รัน pipeline และ scripts |
| FFmpeg + ffprobe | render video, concat audio, อ่าน duration |
| `ANTHROPIC_API_KEY` | สร้าง `script.json` ด้วย Claude |
| Internet | Edge-TTS และ image services |

### Optional

| Component | ใช้ทำอะไร |
|---|---|
| `GOOGLE_API_KEY` + `google-generativeai` | `scripts/research.py` ด้วย Gemini |
| `GEMINI_API_KEY` + `google-generativeai` | สร้างภาพผ่าน Gemini image generation |
| ComfyUI + FLUX.1 | สร้างภาพ local GPU |
| Codex CLI | image generation path แบบ agent-assisted |
| F5-TTS Thai | voice cloning/offline TTS |
| Node.js 18+ | ทดลอง Remotion renderer |
| PyYAML | ใช้ `--profile`, `--voice-direction`, `--visual-brief` |

ติดตั้ง optional บางตัวตามที่ต้องใช้:

```powershell
pip install google-generativeai pyyaml
pip install f5-tts-th soundfile torch torchaudio
```

---

## Environment Variables

ดู template ที่ `.env.example` สำหรับค่าหลัก ส่วน `GEMINI_API_KEY` ให้เพิ่มเองถ้าต้องใช้ Gemini image generation

| Variable | Required | Default | Description |
|---|---:|---|---|
| `ANTHROPIC_API_KEY` | Yes | - | Claude API สำหรับ script generation |
| `GOOGLE_API_KEY` | No | - | Gemini research ใน `scripts/research.py` |
| `GEMINI_API_KEY` | No | - | Gemini image generation ใน `scripts/generate_images.py` |
| `TTS_ENGINE` | No | `edge` | ค่า config; pipeline รับผ่าน `--tts-engine` |
| `TTS_VOICE` | No | `th-TH-NiwatNeural` | ค่า config; pipeline รับผ่าน `--voice` |
| `COMFYUI_URL` | No | `http://127.0.0.1:8188` | URL สำหรับ ComfyUI |
| `CHANNEL_NAME` | No | `Your Channel Name` | ชื่อช่องใน metadata/brand |
| `SUBTITLE_MODE` | No | `burned` | `burned`, `soft`, หรือ `clean` สำหรับ final video |

---

## Commands

### Full Pipeline

```powershell
python workflow/pipeline.py --topic "หัวข้อวิดีโอ"
python workflow/pipeline.py --script output/script.json
python workflow/pipeline.py --topic "หัวข้อ" --skip-images
python workflow/pipeline.py --topic "หัวข้อ" --skip-audio
python workflow/pipeline.py --topic "หัวข้อ" --tts-engine edge --voice th-TH-PremwadeeNeural
```

### Individual Steps

```powershell
# Optional research
python scripts/research.py --topic "Warren Buffett ถือเงินสด" --output output/research.json

# Script generation
python scripts/generate_script.py --topic "Warren Buffett ถือเงินสด" --output output/script.json

# Audio: default Edge-TTS
python scripts/generate_audio.py --script output/script.json --engine edge --voice th-TH-NiwatNeural

# Audio: v2 voice profile + voice direction
python scripts/generate_audio.py --script output/script.json --engine edge --profile storyteller_male --voice-direction output/voice_direction.yaml --normalize

# Subtitles
python scripts/generate_subtitles.py --script output/script.json --audio-manifest output/audio/manifest.json --output output/subtitles/subtitles.srt

# Images
python scripts/generate_images.py --script output/script.json --method auto
python scripts/generate_images.py --script output/script.json --method pollinations
python scripts/generate_images.py --script output/script.json --method comfyui --comfyui-url http://127.0.0.1:8188
python scripts/generate_images.py --script output/script.json --visual-brief output/visual_brief.yaml

# Final render
python scripts/render_video.py --script output/script.json
python scripts/render_video.py --script output/script.json --subtitle-mode soft --output output/final/video_softsubs.mp4
python scripts/render_video.py --script output/script.json --subtitle-mode clean --no-logo
```

---

## TTS

### Edge-TTS

ค่า default คือเสียงผู้ชายไทย:

| Voice | ID |
|---|---|
| Male | `th-TH-NiwatNeural` |
| Female | `th-TH-PremwadeeNeural` |

`generate_audio.py` จะสร้างไฟล์ตาม segment:

```text
output/audio/
├── segment_01_intro.mp3
├── segment_02_ch_01.mp3
└── manifest.json
```

### Voice Profile / Voice Direction

ไฟล์ profile อยู่ที่:

```text
studio/style-bible/voice-profiles.yaml
```

profiles ที่มีตอนนี้:

- `storyteller_male`
- `energetic_female`
- `analytical_neutral`

voice direction YAML รองรับ prosody ต่อ chapter/segment เช่น rate, pitch, volume, pauses และ normalization target

### F5-TTS

ใช้สำหรับ local GPU / voice cloning:

```powershell
python scripts/generate_audio.py --script output/script.json --engine f5 --ref-audio assets/samples/reference_voice.wav
```

---

## Image Generation

`scripts/generate_images.py --method auto` เลือก backend ตามของที่มีในเครื่อง:

1. Gemini ถ้ามี `GEMINI_API_KEY` และติดตั้ง `google-generativeai`
2. Codex CLI ถ้าพบ `codex` ใน PATH
3. ComfyUI ถ้า server ตอบที่ `COMFYUI_URL`
4. Pollinations.ai ถ้ามี `requests`
5. Placeholder image จาก Pillow

รองรับ visual brief:

```powershell
python scripts/generate_images.py --script output/script.json --visual-brief output/visual_brief.yaml
```

ภาพจะถูกเขียนไปที่:

```text
output/images/
├── intro.png
├── ch_01.png
├── ch_02.png
├── outro.png
└── manifest.json
```

---

## Rendering

ตัว render หลักคือ FFmpeg:

```powershell
python scripts/render_video.py --script output/script.json
```

รองรับ subtitle mode:

| Mode | ผลลัพธ์ |
|---|---|
| `burned` | ฝังซับลงวิดีโอถาวร |
| `soft` | mux SRT เป็น mov_text subtitle track |
| `clean` | ไม่มีซับ |

spec ปัจจุบัน:

| Property | Value |
|---|---|
| Resolution | 1920x1080 |
| FPS | 30 |
| Video codec | H.264 |
| Audio codec | AAC |
| Audio bitrate | 192kbps |
| Pixel format | yuv420p |

---

## AI Studio v2

repo นี้มีโครงสร้าง v2 สำหรับทำงานแบบ production project แยกจาก `output/` เดิม

สร้าง project ใหม่:

```powershell
python workflow/create_project.py --topic "Warren Buffett ถือเงินสด 12 ล้านล้าน" --profile storyteller_male
```

โครงสร้าง project:

```text
projects/{yyyymmdd}_{slug}/
├── project.yaml
├── 01-research/
├── 02-script/
├── 03-voice-direction/
├── 04-audio/
├── 05-visual-briefs/
├── 06-images/
├── 07-assembly/
├── 08-qa-reports/
└── 09-final/
```

ตัวอย่างที่มีใน repo:

```text
projects/20260521_warren-buffett-12/
```

project นี้มี final outputs แล้ว:

```text
09-final/video_clean.mp4
09-final/video_burned.mp4
09-final/video_th_softsubs.mp4
```

---

## Style Bible

creative source of truth อยู่ใน `studio/style-bible/`

```text
studio/style-bible/
├── colors.yaml
├── visual-style.yaml
└── voice-profiles.yaml
```

brand ปัจจุบัน:

| Token | Hex | Usage |
|---|---|---|
| Trust Blue | `#1B5299` | brand/header |
| Navy Dark | `#1a2744` | text/overlay |
| Muted Gold | `#C9A84C` | accent/highlight |
| Warm Cream | `#F5F0E8` | background |

ข้อกำหนด visual หลัก: editorial flat illustration, ไม่มีตัวหนังสือในภาพ generated, ไม่มี stock/copyrighted images, ใช้ 16:9 landscape

---

## Script JSON Schema

ขั้นต่ำที่ pipeline ใช้ได้:

```json
{
  "title": "ชื่อวิดีโอภาษาไทย",
  "title_en": "English title",
  "brand": {
    "color_primary": "#1B5299",
    "color_secondary": "#FFFFFF",
    "channel_name": "Chie-Su"
  },
  "intro": {
    "narration": "ข้อความเปิดวิดีโอ",
    "visual_description": "English image prompt",
    "duration_seconds": 20
  },
  "chapters": [
    {
      "id": 1,
      "title": "ชื่อ Chapter",
      "timestamp_start": "00:00",
      "narration": "ข้อความบรรยายภาษาไทย",
      "visual_description": "English image prompt",
      "image_keyword": "cash vault money",
      "duration_seconds": 110,
      "key_points": ["ประเด็นสำคัญ"]
    }
  ],
  "outro": {
    "narration": "บทสรุปและ CTA",
    "duration_seconds": 30
  }
}
```

schema ที่ใช้งานจริงใน sample v2 อาจมี field เพิ่ม เช่น `act`, `emotional_beat`, `voice_direction`, `visual_brief`, `color_accent`

---

## Project Structure

```text
bestClip/
├── README.md
├── CLAUDE.md
├── PLAN.md
├── requirements.txt
├── package.json
├── .env.example
├── workflow/
│   ├── pipeline.py
│   └── create_project.py
├── scripts/
│   ├── research.py
│   ├── generate_script.py
│   ├── generate_audio.py
│   ├── generate_subtitles.py
│   ├── generate_images.py
│   ├── generate_test_image.py
│   └── render_video.py
├── studio/
│   ├── style-bible/
│   ├── templates/
│   └── content-calendar/
├── projects/
│   ├── template/
│   └── 20260521_warren-buffett-12/
├── remotion/
│   └── src/
├── assets/
│   └── samples/
└── output/
    ├── script.json
    ├── voice_direction.yaml
    ├── visual_brief.yaml
    ├── audio/
    ├── images/
    ├── subtitles/
    └── final/
```

---

## Remotion

มี React/Remotion composition ใน `remotion/src/` และ npm scripts ใน `package.json`

```powershell
npm install
npm run start
npm run preview
npm run render
```

สถานะ: Remotion เป็น renderer ทางเลือก/ทดลอง โค้ด pipeline ปัจจุบันไม่ได้เรียก Remotion และ final video ใช้ FFmpeg เป็นหลัก

---

## Troubleshooting

| ปัญหา | วิธีตรวจ/แก้ |
|---|---|
| `ANTHROPIC_API_KEY` missing | ใส่ key ใน `.env` หรือ environment |
| `ffmpeg not found` | ติดตั้ง FFmpeg และเพิ่มลง PATH |
| ไม่มีเสียง | ตรวจ `output/audio/manifest.json` และไฟล์ `output/audio/*` |
| subtitle timing ไม่ตรง | รัน audio ก่อน subtitles เพื่อให้ใช้ duration จริงจาก manifest |
| ซับไม่ถูกฝัง | ตรวจ `SUBTITLE_MODE` หรือส่ง `--subtitle-mode burned` |
| ComfyUI ใช้ไม่ได้ | เปิด ComfyUI ที่ `COMFYUI_URL` และตรวจ model paths |
| Gemini image ไม่ทำงาน | ติดตั้ง `google-generativeai` และตั้ง `GEMINI_API_KEY` |
| F5-TTS หา reference ไม่เจอ | วาง WAV ที่ `assets/samples/reference_voice.wav` หรือส่ง `--ref-audio` |
| Thai profile/brief YAML error | ติดตั้ง `pyyaml` |

---

## Current Limitations

- research step ยังไม่ถูกเชื่อมเข้า full pipeline อัตโนมัติ
- pipeline หลักยังไม่ auto-pass `output/voice_direction.yaml` และ `output/visual_brief.yaml`
- generated script prompt ใน `scripts/generate_script.py` ยังเป็น schema รุ่น baseline มากกว่า schema v2 เต็ม
- `projects/` workflow เป็น production structure แล้ว แต่ scripts หลักส่วนใหญ่ยังเขียน output ไปที่ `output/`

---

## License

MIT
