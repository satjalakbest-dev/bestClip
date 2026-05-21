# 🎬 bestClip

**BlueOclock-style Thai Finance YouTube Video Pipeline**

สร้างวิดีโอ deep-dive analysis ภาษาไทยแบบอัตโนมัติ — ตั้งแต่ topic จนได้ MP4

---

## 📋 Requirements

| Component | Version | Notes |
|---|---|---|
| Python | ≥ 3.10 | Required |
| FFmpeg | Latest | Required for rendering |
| GPU | RTX 3070 8GB | For FLUX.1 images + F5-TTS (optional) |
| Claude Code | Subscription | Script generation |
| Gemini | Subscription | Research (optional) |
| ComfyUI | Latest | For AI images (optional) |
| Node.js | ≥ 18 | For Remotion (optional) |

---

## ⚡ Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/bestClip.git
cd bestClip

# Python dependencies
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env and fill in ANTHROPIC_API_KEY
```

### 2. Run Full Pipeline

```bash
python workflow/pipeline.py --topic "Warren Buffett ถือเงินสด 12 ล้านล้านบาท"
```

### 3. Output

```
output/final/video_final.mp4  ← Your video!
```

---

## 🏗️ Architecture

```
Topic Input
    │
    ▼
[1] Research (Gemini)        ← scripts/research.py
    │  output/research.json
    ▼
[2] Script (Claude API)      ← scripts/generate_script.py  
    │  output/script.json
    ▼
[3] Thai Audio (Edge-TTS)    ← scripts/generate_audio.py
    │  output/audio/*.mp3
    ▼
[4] Subtitles (from script)  ← scripts/generate_subtitles.py
    │  output/subtitles/subtitles.srt
    ▼
[5] Illustrations (FLUX.1)   ← scripts/generate_images.py
    │  output/images/*.png
    ▼
[6] Render (FFmpeg)          ← scripts/render_video.py
    │
    ▼
output/final/video_final.mp4
```

---

## 🎙️ TTS Engines

### Edge-TTS (Default — free, online)
```bash
# Male voice
python workflow/pipeline.py --topic "..." --voice th-TH-NiwatNeural

# Female voice
python workflow/pipeline.py --topic "..." --voice th-TH-PremwadeeNeural
```

### F5-TTS Thai (GPU — best quality, offline)
```bash
# Install first
pip install f5-tts-th soundfile

# Put your 5-10 second Thai voice WAV here:
# assets/samples/reference_voice.wav

# Run with F5
python workflow/pipeline.py --topic "..." --tts-engine f5
```

---

## 🎨 Image Generation Setup (ComfyUI + FLUX.1)

```bash
# 1. Install ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI && pip install -r requirements.txt

# 2. Download FLUX.1-schnell fp8 (~8GB) into ComfyUI/models/checkpoints/
# https://huggingface.co/Comfy-Org/flux1-schnell/blob/main/flux1-schnell-fp8.safetensors

# 3. Start ComfyUI (low VRAM mode for RTX 3070)
python main.py --lowvram

# 4. Run pipeline (ComfyUI must be running)
python workflow/pipeline.py --topic "..."
```

**Without GPU/ComfyUI:**
```bash
# Uses placeholder images (still makes valid video)
python workflow/pipeline.py --topic "..." --skip-images
```

---

## 🔧 Individual Steps

```bash
# Step 1: Research (needs Gemini API)
python scripts/research.py --topic "Warren Buffett"

# Step 2: Script only
python scripts/generate_script.py --topic "..." --output output/script.json

# Step 3: Audio only (from existing script)
python scripts/generate_audio.py --script output/script.json

# Step 4: Subtitles only
python scripts/generate_subtitles.py --script output/script.json

# Step 5: Images only (needs ComfyUI running)
python scripts/generate_images.py --script output/script.json

# Step 6: Render only (all assets must exist)
python scripts/render_video.py --script output/script.json
```

---

## 📁 Project Structure

```
bestClip/
├── CLAUDE.md              ← Claude Code instructions (READ THIS)
├── workflow/
│   └── pipeline.py        ← Main orchestrator
├── scripts/
│   ├── research.py        ← Gemini research
│   ├── generate_script.py ← Claude script writer
│   ├── generate_audio.py  ← Thai TTS
│   ├── generate_subtitles.py
│   ├── generate_images.py ← FLUX.1 illustrations
│   └── render_video.py    ← FFmpeg renderer
├── remotion/              ← Optional: Remotion renderer
│   └── src/
│       └── compositions/
├── assets/
│   ├── fonts/             ← NotoSansThaiUI-Regular.ttf
│   ├── logo/              ← logo.png (your channel logo)
│   └samples/             ← reference_voice.wav (for F5-TTS)
├── output/                ← Generated files (gitignored)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🎨 Customization

### Change Channel Branding
Edit `output/script.json` brand section, or modify `scripts/generate_script.py`:
```python
# In SCRIPT_PROMPT, change:
"channel_name": "Your Channel Name",
"color_primary": "#1B5299",  # Your brand blue
```

### Change Video Style
Edit `STYLE_SUFFIX` in `scripts/generate_images.py`:
```python
STYLE_SUFFIX = "your custom style description..."
```

### Add Your Logo
```
assets/logo/logo.png  ← PNG with transparency, ~500x500px
```

---

## 📊 Resource Usage (RTX 3070 8GB)

| Task | VRAM | Time |
|---|---|---|
| FLUX.1-schnell (1 image) | ~6GB | ~15s |
| F5-TTS Thai (1 segment) | ~4GB | ~30s |
| FFmpeg render | 0GB (CPU) | ~2min/video |
| **Run sequentially** | **Max 6GB** | **~30min total** |

---

## ❓ Troubleshooting

**No sound in output video:**
```bash
# Check audio files exist
ls output/audio/
```

**ComfyUI connection refused:**
```bash
python ComfyUI/main.py --lowvram --port 8188
```

**Thai text not showing in subtitles:**
```bash
# Install Thai font
# Windows: fonts already included
# Linux: sudo apt install fonts-noto-cjk
# macOS: brew install --cask font-noto-sans-cjk-tc
```

**Memory error with F5-TTS:**
```bash
# Text too long — it auto-splits at 280 chars
# Check assets/samples/reference_voice.wav exists
```

---

## 📜 License

MIT — Use for your own channel freely.

---

*Built for: Claude Code + Gemini + RTX 3070 + BlueOclock-style content*
