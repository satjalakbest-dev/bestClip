# bestClip

**Thai Finance YouTube Video Pipeline — BlueOclock Style**

สร้างวิดีโอวิเคราะห์การเงินภาษาไทยแบบอัตโนมัติ ตั้งแต่ topic จนถึง MP4 พร้อมเสียงบรรยาย AI ภาพประกอบ ซับไตเติล และ chapter cards

---

## Quick Start

```bash
# 1. Clone & Install
git clone https://github.com/satjalakbest-dev/bestClip.git
cd bestClip
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env — fill in ANTHROPIC_API_KEY (required), GOOGLE_API_KEY (optional)

# 3. Run full pipeline
python workflow/pipeline.py --topic "Warren Buffett ถือเงินสด 12 ล้านล้าน"

# 4. Output
# output/final/video_final.mp4
```

---

## Pipeline Flow

```
Topic String
    |
    v
[Step 0] Research          scripts/research.py        (optional)
    |  output/research.json
    v
[Step 1] Script Gen        scripts/generate_script.py  (Claude API)
    |  output/script.json
    v
[Step 2] Thai Audio        scripts/generate_audio.py   (Edge-TTS / F5-TTS)
    |  output/audio/*.mp3 + manifest.json
    v
[Step 3] Subtitles         scripts/generate_subtitles.py
    |  output/subtitles/subtitles.srt
    v
[Step 4] AI Images         scripts/generate_images.py  (Pollinations / ComfyUI)
    |  output/images/*.png + manifest.json
    v
[Step 5] Render Video      scripts/render_video.py     (FFmpeg)
    |
    v
output/final/video_final.mp4   (1920x1080 H.264 + AAC 192kbps)
```

### Step Details

| Step | Script | Input | Output | Required |
|---|---|---|---|---|
| 0. Research | `research.py` | Topic | `research.json` | No (optional) |
| 1. Script | `generate_script.py` | Topic | `script.json` | Yes (Anthropic API key) |
| 2. Audio | `generate_audio.py` | `script.json` | `audio/*.mp3` | Yes |
| 3. Subtitles | `generate_subtitles.py` | `script.json` + audio timing | `subtitles.srt` | Yes |
| 4. Images | `generate_images.py` | `script.json` | `images/*.png` | Yes (Pollinations free) |
| 5. Render | `render_video.py` | All above | `video_final.mp4` | Yes (FFmpeg) |

---

## Requirements

### Required

| Component | Version | Purpose |
|---|---|---|
| Python | >= 3.10 | Pipeline scripts |
| FFmpeg | Latest | Video rendering |
| Anthropic API Key | - | Script generation (Claude Opus) |
| Internet | - | Edge-TTS + Pollinations.ai |

### Optional

| Component | Purpose |
|---|---|
| NVIDIA GPU (8GB+ VRAM) | ComfyUI FLUX.1 images + F5-TTS voice cloning |
| Google API Key | Gemini research step |
| ComfyUI | Local AI image generation (FLUX.1-schnell GGUF) |
| Node.js >= 18 | Remotion alternative renderer |

### Python Dependencies

```
anthropic>=0.40.0       # Claude API (script generation)
edge-tts>=6.1.12        # Thai TTS (free, online)
mutagen>=1.47.0         # Audio duration detection
Pillow>=10.0.0          # Image processing
python-dotenv>=1.0.0    # .env loading
requests>=2.31.0        # Pollinations.ai / ComfyUI API calls
tqdm>=4.66.0            # Progress bars
```

Optional: `f5-tts-th`, `soundfile`, `torch`, `torchaudio` (GPU TTS) / `google-generativeai` (Gemini research)

---

## Image Generation Methods

Images are generated in priority order (auto mode):

### 1. ComfyUI + FLUX.1-schnell (Local GPU — Best Quality)

Best quality, requires NVIDIA GPU with 8GB+ VRAM.

```bash
# Install ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI && pip install -r requirements.txt

# Download model components:
# models/unet/flux1-schnell-Q4_K_S.gguf      (~6.5GB, fits 8GB VRAM)
# models/clip/clip_l.safetensors              (235MB)
# models/clip/t5xxl_fp8_e4m3fn.safetensors    (~4.7GB)
# models/vae/ae.safetensors                    (320MB)

# Start ComfyUI
python main.py --lowvram --listen 127.0.0.1 --port 8188

# Pipeline will auto-detect ComfyUI
python workflow/pipeline.py --topic "..."
```

### 2. Pollinations.ai (Free — No API Key)

Default fallback when ComfyUI is not running. Free, no signup required.

```bash
# This runs automatically if ComfyUI is unavailable
python scripts/generate_images.py --method pollinations --script output/script.json
```

### 3. Placeholder Fallback

Colored backgrounds with text labels. Last resort when both methods fail.

### Prompt System

`generate_images.py` uses a content-aware prompt builder:

- **KEYWORD_VISUAL_MAP** — 20+ finance topics mapped to detailed story-driven English prompts
- **SCENE_TYPE_RULES** — Different composition per scene type (intro/chapter/outro)
- **key_points enrichment** — Pulls chapter key_points for additional context
- **STYLE_SUFFIX** — Consistent brand style (warm beige, navy, gold accents)

```python
# Example prompt output:
# "centered subject, clear focal point, storytelling composition,
#  elderly investor in suit standing proudly before an enormous open bank vault...
#  flat illustration, warm beige background, navy and gold accents,
#  clean composition, no text no words, soft lighting"
```

---

## TTS Engines

### Edge-TTS (Default — Free, Online)

| Voice | ID | Gender |
|---|---|---|
| Niwat | `th-TH-NiwatNeural` | Male (default) |
| Premwadee | `th-TH-PremwadeeNeural` | Female |

```bash
python workflow/pipeline.py --topic "..." --voice th-TH-PremwadeeNeural
```

### F5-TTS Thai (GPU — Voice Cloning, Offline)

```bash
pip install f5-tts-th soundfile

# Place reference voice (5-10s Thai WAV):
# assets/samples/reference_voice.wav

python workflow/pipeline.py --topic "..." --tts-engine f5
```

---

## Individual Scripts

```bash
# Step 0: Research (optional, needs Google API key)
python scripts/research.py --topic "Warren Buffett" --output output/research.json

# Step 1: Generate script
python scripts/generate_script.py --topic "..." --output output/script.json

# Step 2: Generate audio
python scripts/generate_audio.py --script output/script.json

# Step 3: Generate subtitles
python scripts/generate_subtitles.py --script output/script.json

# Step 4: Generate images
python scripts/generate_images.py --script output/script.json --method auto

# Step 5: Render video
python scripts/render_video.py --script output/script.json
```

---

## Script JSON Format

```json
{
  "title": "Thai video title",
  "title_en": "English title",
  "brand": {
    "color_primary": "#1B5299",
    "channel_name": "Blue O'Clock"
  },
  "intro": {
    "narration": "Thai narration text...",
    "visual_description": "English description for image generation",
    "duration_seconds": 6
  },
  "chapters": [
    {
      "id": 1,
      "title": "Chapter title in Thai",
      "narration": "Full Thai narration for this segment",
      "visual_description": "English image prompt",
      "image_keyword": "cash vault money",
      "duration_seconds": 120,
      "key_points": ["Point 1", "Point 2"]
    }
  ],
  "outro": {
    "narration": "Outro Thai text with CTA",
    "duration_seconds": 5
  }
}
```

---

## Project Structure

```
bestClip/
├── CLAUDE.md                  # Claude Code project instructions
├── README.md
├── requirements.txt
├── package.json               # Remotion Node dependencies
├── .env.example               # Environment variables template
├── workflow/
│   └── pipeline.py            # Main orchestrator (runs all steps)
├── scripts/
│   ├── research.py            # Step 0: Gemini research (optional)
│   ├── generate_script.py     # Step 1: Claude API script generation
│   ├── generate_audio.py      # Step 2: Thai TTS (Edge-TTS / F5-TTS)
│   ├── generate_subtitles.py  # Step 3: SRT/VTT from script + audio timing
│   ├── generate_images.py     # Step 4: AI illustrations
│   ├── render_video.py        # Step 5: FFmpeg final render
│   └── generate_test_image.py # Utility: test image without AI
├── remotion/                  # Optional: Remotion React renderer
│   └── src/
│       ├── Root.tsx
│       └── compositions/
│           ├── BlueOclockVideo.tsx
│           └── Components.tsx
├── assets/
│   ├── fonts/                 # NotoSansThaiUI-Regular.ttf
│   ├── logo/                  # Channel logo (PNG, transparent)
│   └── samples/               # F5-TTS reference voice WAV files
└── output/                    # Generated files (gitignored)
    ├── script.json
    ├── audio/
    ├── images/
    ├── subtitles/
    └── final/
        └── video_final.mp4
```

---

## Video Output Specs

| Property | Value |
|---|---|
| Resolution | 1920x1080 |
| Video codec | H.264 |
| Frame rate | 30fps |
| Audio codec | AAC 192kbps stereo |
| Sample rate | 44100Hz |
| Subtitles | Burned-in (Thai) |
| Target duration | 15-35 minutes |

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | - | Claude API for script generation |
| `GOOGLE_API_KEY` | No | - | Gemini API for research |
| `TTS_ENGINE` | No | `edge` | `edge` or `f5` |
| `TTS_VOICE` | No | `th-TH-NiwatNeural` | Edge-TTS voice ID |
| `COMFYUI_URL` | No | `http://127.0.0.1:8188` | ComfyUI server URL |
| `CHANNEL_NAME` | No | `Blue O'Clock` | Display name in video |

---

## Resource Usage (RTX 3070 8GB)

| Task | VRAM | Time (per unit) |
|---|---|---|
| FLUX.1-schnell GGUF Q4 (1 image) | ~6GB | ~15s |
| Pollinations.ai (1 image) | 0GB (API call) | ~10s |
| Edge-TTS (1 segment) | 0GB | ~3s |
| F5-TTS Thai (1 segment) | ~4GB | ~30s |
| FFmpeg render (full video) | 0GB (CPU) | ~2min |

---

## Troubleshooting

| Issue | Solution |
|---|---|
| No sound in video | Check `output/audio/*.mp3` files exist |
| ComfyUI connection refused | Start ComfyUI: `python main.py --lowvram --port 8188` |
| Pollinations 403 error | Ensure `requests` library is installed (`pip install requests`) |
| Thai subtitles not rendering | Ensure Thai font is installed (NotoSansThai in `assets/fonts/`) |
| F5-TTS memory error | Text auto-splits at 280 chars; check reference WAV exists |
| Images don't match content | Improve `image_keyword` in script.json or edit `KEYWORD_VISUAL_MAP` |

---

## License

MIT

---

*Built for: Claude Code + Pollinations.ai + Edge-TTS + FFmpeg*
