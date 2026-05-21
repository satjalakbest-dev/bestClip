#!/usr/bin/env python3
"""
Step 4: Generate AI illustrations
Usage: python scripts/generate_images.py --script output/script.json

Methods (tried in order):
  1. Pollinations.ai (free, no API key needed)
  2. ComfyUI + FLUX.1-schnell (local GPU)
  3. Placeholder fallback (colored backgrounds)
"""

import argparse
import json
import random
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
COMFYUI_URL = "http://127.0.0.1:8188"

STYLE_SUFFIX = (
    "flat illustration, warm beige background, navy and gold accents, "
    "clean composition, no text no words, soft lighting"
)

SCENE_TYPE_RULES = {
    "intro": "cinematic wide shot, dramatic lighting, single figure silhouette",
    "chapter": "centered subject, clear focal point, storytelling composition",
    "outro": "bold graphic design layout, centered icon elements, invitation feeling",
}

SCENE_PROMPT_MAP = {
    "intro": "wise elderly investor silhouette standing before a massive glowing stock market display, confident pose, dramatic backlight",
    "outro": "large subscribe button icon with notification bell, warm inviting colors, hand cursor clicking, social media engagement",
}

SCENE_TYPE_RULES = {
    "intro": "cinematic wide shot, dramatic lighting, single figure silhouette",
    "chapter": "centered subject, clear focal point, storytelling composition",
    "outro": "bold graphic design layout, centered icon elements, invitation feeling",
}

KEYWORD_VISUAL_MAP = {
    "cash vault money": "elderly investor in suit standing proudly before an enormous open bank vault overflowing with gold bars and stacked dollar bills, historic record-breaking wealth, confident posture",
    "market warning signal": "giant red exclamation mark hovering over a falling stock chart on a digital screen, investor silhouette looking concerned in foreground, urgent alert mood",
    "stock market crash": "skyscrapers with stock ticker numbers falling like rain, worried investor covering face, dramatic downward arrows in sky, dark stormy atmosphere",
    "investment strategy": "elderly chess grandmaster pondering next move on a chessboard where pieces are shaped like buildings and gold coins, strategic deep thought",
    "savings": "young person carefully placing coins into a glowing piggy bank that is sprouting into a golden tree, steady growth, hopeful future",
    "debt": "person crushed under a massive ball and chain made of tangled credit cards and loan papers, heavy burden, stressed posture",
    "crypto": "futuristic floating golden bitcoin coin pulsing with energy above a glowing digital circuit board network, modern technology meets finance",
    "real estate": "person holding a glowing key in front of modern city buildings growing taller with upward arrows, property ladder concept, prosperous cityscape",
    "retirement": "happy older couple relaxing on a serene beach at sunset with a small treasure chest beside them and financial chart dissolving into the horizon",
    "gold": "hands holding shimmering gold bars that reflect warm light, surrounded by scattered gold coins on a velvet surface, precious metals treasure",
    "recession": "abandoned shopping mall with empty storefronts and a single person pushing an empty cart through a desolate corridor, economic emptiness",
    "inflation": "helium balloon shaped like a dollar sign being inflated until it stretches and nearly bursts, rising prices visual metaphor, tension",
    "dividend": "mature money tree dropping golden coins into a collection basket held by a smiling person, passive income flowing steadily",
    "portfolio": "balanced golden scale weighing different objects — a house, coins, a document, and a glowing orb — perfect harmony and diversification",
    "interest rate": "bank building with a giant thermometer gauge showing percentage rising, person looking up at it with concern, rate hike impact",
    "budget": "organized desk with a calculator, notebook with neat rows of numbers, and a small stack of coins, methodical financial planning",
    "tax": "government capitol building casting a long shadow over a person holding a small stack of remaining money, taxation burden",
    "insurance": "large golden umbrella shielding a family from falling storm clouds and rain, warm light underneath, safety and protection",
    "startup": "entrepreneur launching a small rocket from a laptop screen, the rocket trailing golden sparkles upward, innovation and ambition",
    "warren buffett": "distinguished elderly man with glasses and suit sitting at a desk with financial newspapers and a cherry coke, wise thoughtful expression, legendary investor portrait",
}


def _detect_scene_type(scene_id: str) -> str:
    if scene_id == "intro":
        return "intro"
    elif scene_id == "outro":
        return "outro"
    else:
        return "chapter"


def build_image_prompt(scene_id: str, visual_desc: str, chapter: dict = None) -> str:
    """Build a content-aware prompt from script metadata."""
    parts = []

    # 1. Scene-type composition rule
    scene_type = _detect_scene_type(scene_id)
    if scene_type in SCENE_TYPE_RULES:
        parts.append(SCENE_TYPE_RULES[scene_type])

    # 2. Subject — keyword > visual_desc > scene_map > fallback
    keyword = chapter.get("image_keyword", "") if chapter else ""
    if keyword and keyword.lower() in KEYWORD_VISUAL_MAP:
        parts.append(KEYWORD_VISUAL_MAP[keyword.lower()])
    elif visual_desc:
        desc = visual_desc.replace("minimalist flat illustration", "").strip()
        if desc:
            parts.append(desc)
    elif scene_id in SCENE_PROMPT_MAP:
        parts.append(SCENE_PROMPT_MAP[scene_id])
    else:
        parts.append("professional business concept illustration")

    # 3. Enrich with key_points if available (adds story context)
    if chapter:
        key_points = chapter.get("key_points", [])
        if key_points and not keyword:
            topics = ", ".join(key_points[:2])
            parts.append(f"illustrating: {topics}")

    parts.append(STYLE_SUFFIX)
    return ", ".join(parts)


def generate_with_pollinations(prompt: str, output_path: str, scene_id: str) -> bool:
    """Generate image via Pollinations.ai (free, no API key)"""
    try:
        import requests
        from PIL import Image
    except ImportError:
        return False

    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1344&height=768&nologo=true&seed={random.randint(1,99999)}"

    try:
        print(f"   Pollinations: {scene_id}")
        resp = requests.get(url, timeout=120)
        if resp.status_code != 200 or len(resp.content) < 5000:
            print(f"   Bad response ({resp.status_code}, {len(resp.content)} bytes)")
            return False

        # Save and resize to 1920x1080
        tmp_path = output_path + ".tmp.png"
        with open(tmp_path, "wb") as f:
            f.write(resp.content)

        img = Image.open(tmp_path)
        if img.size != (1920, 1080):
            img = img.resize((1920, 1080), Image.LANCZOS)
        img.save(output_path, "PNG")
        Path(tmp_path).unlink(missing_ok=True)

        size_kb = Path(output_path).stat().st_size / 1024
        print(f"   OK: {Path(output_path).name} ({size_kb:.0f} KB)")
        return True

    except Exception as e:
        print(f"   Pollinations error: {e}")
        return False

def _gguf_workflow(prompt: str, seed: int) -> dict:
    """ComfyUI workflow for FLUX GGUF (Q4_K_S, fits 8GB VRAM)"""
    return {
        "10": {"inputs": {"unet_name": "flux1-schnell-Q4_K_S.gguf"}, "class_type": "UnetLoaderGGUF"},
        "11": {"inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5xxl_fp8_e4m3fn.safetensors"}, "class_type": "DualCLIPLoaderGGUF"},
        "12": {"inputs": {"vae_name": "ae.safetensors"}, "class_type": "VAELoader"},
        "6": {"inputs": {"text": prompt, "clip": ["11", 0]}, "class_type": "CLIPTextEncode"},
        "27": {"inputs": {"width": 1920, "height": 1080, "batch_size": 1}, "class_type": "EmptySD3LatentImage"},
        "31": {
            "inputs": {
                "model": ["10", 0], "conditioning": ["6", 0], "latent_image": ["27", 0],
                "noise_seed": seed, "steps": 4, "cfg": 1.0,
                "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
            },
            "class_type": "KSampler"
        },
        "8": {"inputs": {"samples": ["31", 0], "vae": ["12", 0]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"filename_prefix": "bestclip_scene", "images": ["8", 0]}, "class_type": "SaveImage"},
    }


def _checkpoint_workflow(prompt: str, seed: int) -> dict:
    """ComfyUI workflow for single fp8 checkpoint"""
    return {
        "6": {"inputs": {"text": prompt, "clip": ["30", 1]}, "class_type": "CLIPTextEncode"},
        "8": {"inputs": {"samples": ["31", 0], "vae": ["30", 2]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"filename_prefix": "bestclip_scene", "images": ["8", 0]}, "class_type": "SaveImage"},
        "27": {"inputs": {"width": 1920, "height": 1080, "batch_size": 1}, "class_type": "EmptySD3LatentImage"},
        "30": {"inputs": {"ckpt_name": "flux1-schnell-fp8.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "31": {
            "inputs": {
                "model": ["30", 0], "conditioning": ["6", 0], "latent_image": ["27", 0],
                "noise_seed": seed, "steps": 4, "cfg": 1.0,
                "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
            },
            "class_type": "KSampler"
        }
    }


def generate_with_comfyui(prompt: str, output_path: str, scene_id: str) -> bool:
    """Generate image via ComfyUI FLUX.1-schnell (GGUF Q4_K_S for 8GB VRAM)"""
    seed = random.randint(1, 99999999)
    full_prompt = prompt

    # GGUF workflow for RTX 3070 8GB (Q4_K_S ~6GB VRAM)
    # Try GGUF first, fall back to checkpoint loader
    gguf_unet = Path(ROOT / "../../ComfyUI/models/unet/flux1-schnell-Q4_K_S.gguf")
    fp8_ckpt = Path(ROOT / "../../ComfyUI/models/checkpoints/flux1-schnell-fp8.safetensors")

    if gguf_unet.exists():
        workflow = _gguf_workflow(full_prompt, seed)
    elif fp8_ckpt.exists():
        workflow = _checkpoint_workflow(full_prompt, seed)
    else:
        print(f"   No ComfyUI model found (need GGUF or fp8 checkpoint)")
        return False

    try:
        print(f"   ComfyUI: {scene_id}")
        data = json.dumps({"prompt": workflow}).encode("utf-8")
        req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            prompt_id = json.loads(resp.read())["prompt_id"]

        # Wait for completion
        start = time.time()
        while time.time() - start < 300:
            with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as r:
                history = json.loads(r.read())
            if prompt_id in history:
                for node in history[prompt_id].get("outputs", {}).values():
                    if "images" in node:
                        img = node["images"][0]
                        params = urllib.parse.urlencode(
                            {"filename": img["filename"], "subfolder": img.get("subfolder", ""), "type": "output"})
                        urllib.request.urlretrieve(f"{COMFYUI_URL}/view?{params}", output_path)
                        print(f"   OK: {Path(output_path).name}")
                        return True
            time.sleep(2)

        print(f"   ComfyUI timeout for {scene_id}")
        return False
    except Exception as e:
        print(f"   ComfyUI error: {e}")
        return False


def create_placeholder(output_path: str, text: str):
    """Create a colored placeholder as last resort"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import hashlib

        h = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        colors = [(27, 39, 68), (27, 82, 153), (201, 168, 76), (42, 55, 89), (64, 81, 107)]
        bg = colors[h % len(colors)]

        img = Image.new("RGB", (1920, 1080), color=bg)
        draw = ImageDraw.Draw(img)
        draw.ellipse([760, 280, 1160, 680], fill=None, outline=(255, 255, 255), width=3)

        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except (IOError, OSError):
            font = ImageFont.load_default()

        label = text[:60] if len(text) > 60 else text
        draw.text((960, 540), label, fill=(255, 255, 255), anchor="mm", font=font)

        draw.rectangle([0, 1000, 1920, 1080], fill=(245, 240, 232))
        try:
            font_sm = ImageFont.truetype("arial.ttf", 20)
        except (IOError, OSError):
            font_sm = ImageFont.load_default()
        draw.text((960, 1040), "Blue O'Clock", fill=(27, 82, 153), anchor="mm", font=font_sm)

        img.save(output_path)
        print(f"   Placeholder: {Path(output_path).name}")
    except ImportError:
        print(f"   Skipped: {Path(output_path).name}")


def main():
    global COMFYUI_URL
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", default="output/script.json")
    parser.add_argument("--comfyui-url", default=COMFYUI_URL)
    parser.add_argument("--method", choices=["pollinations", "comfyui", "placeholder", "auto"],
                        default="auto", help="Image generation method")
    args = parser.parse_args()

    COMFYUI_URL = args.comfyui_url

    with open(args.script, encoding="utf-8") as f:
        script = json.load(f)

    images_dir = ROOT / "output/images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Determine method
    method = args.method
    comfyui_available = False

    if method == "auto":
        try:
            with urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=3) as r:
                if r.status == 200:
                    print(f"ComfyUI: available at {COMFYUI_URL}")
                    method = "comfyui"
        except Exception:
            # Check if requests is available for Pollinations
            try:
                import requests
                print("ComfyUI: not available")
                print("Using: Pollinations.ai (free AI image generation)")
                method = "pollinations"
            except ImportError:
                print("No image generation method available, using placeholders")
                method = "placeholder"
    else:
        print(f"Using: {method}")

    # Build scene list
    scenes = []

    if "intro" in script:
        desc = script["intro"].get("visual_description", "")
        scenes.append(("intro", desc, None))

    for ch in script.get("chapters", []):
        sid = f"ch_{ch['id']:02d}"
        desc = ch.get("visual_description", f"business concept {ch['title']}")
        scenes.append((sid, desc, ch))

    if "outro" in script:
        desc = script["outro"].get("visual_description", "subscribe and notification bell concept")
        scenes.append(("outro", desc, None))

    print(f"\nGenerating {len(scenes)} illustrations...")
    manifest = []

    for scene_id, visual_desc, chapter in scenes:
        output_path = str(images_dir / f"{scene_id}.png")

        if Path(output_path).exists():
            print(f"   Skip (exists): {scene_id}.png")
            manifest.append({"id": scene_id, "file": f"{scene_id}.png"})
            continue

        prompt = build_image_prompt(scene_id, visual_desc, chapter)
        ok = False

        if method == "pollinations":
            ok = generate_with_pollinations(prompt, output_path, scene_id)
        elif method == "comfyui":
            ok = generate_with_comfyui(prompt, output_path, scene_id)
            if not ok:
                ok = generate_with_pollinations(prompt, output_path, scene_id)

        if not ok:
            create_placeholder(output_path, visual_desc)

        manifest.append({"id": scene_id, "file": f"{scene_id}.png"})
        time.sleep(1)

    # Save manifest
    manifest_path = images_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\nImages complete!")
    print(f"   Count: {len(manifest)}")
    print(f"   Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
