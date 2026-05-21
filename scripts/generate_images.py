#!/usr/bin/env python3
"""
Step 4: Generate AI illustrations using ComfyUI + FLUX.1-schnell
Usage: python scripts/generate_images.py --script output/script.json
Requires: ComfyUI running at http://127.0.0.1:8188 with FLUX.1-schnell model
RTX 3070 8GB: Use FLUX.1-schnell fp8 quantized (~5-6GB VRAM)
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import random
from pathlib import Path

ROOT = Path(__file__).parent.parent
COMFYUI_URL = "http://127.0.0.1:8188"

# BlueOclock visual style constants
STYLE_SUFFIX = (
    "minimalist flat illustration, warm cream background color #F5F0E8, "
    "navy dark blue accents #1a2744, muted gold highlights, "
    "soft watercolor texture, professional business concept art, "
    "no text no words no letters, clean composition, "
    "16:9 aspect ratio, soft natural lighting, subtle shadows"
)

NEGATIVE_PROMPT = (
    "text, words, letters, watermark, logo, signature, "
    "photorealistic, photograph, 3d render, dark background, "
    "neon colors, violent, disturbing, nsfw"
)


def build_flux_workflow(prompt: str, seed: int = None) -> dict:
    """ComfyUI workflow for FLUX.1-schnell (fast, 8GB friendly)"""
    seed = seed or random.randint(1, 99999999)
    full_prompt = f"{prompt}, {STYLE_SUFFIX}"

    return {
        "6": {
            "inputs": {
                "text": full_prompt,
                "clip": ["30", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "8": {
            "inputs": {
                "samples": ["31", 0],
                "vae": ["30", 2]
            },
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {
                "filename_prefix": "bestclip_scene",
                "images": ["8", 0]
            },
            "class_type": "SaveImage"
        },
        "27": {
            "inputs": {
                "width": 1920,
                "height": 1080,
                "batch_size": 1
            },
            "class_type": "EmptySD3LatentImage"
        },
        "30": {
            "inputs": {
                "ckpt_name": "flux1-schnell-fp8.safetensors"
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "31": {
            "inputs": {
                "model": ["30", 0],
                "conditioning": ["6", 0],
                "latent_image": ["27", 0],
                "noise_seed": seed,
                "steps": 4,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            },
            "class_type": "KSampler"
        }
    }


def queue_prompt(workflow: dict) -> str:
    """Submit workflow to ComfyUI and return prompt_id"""
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())
        return result["prompt_id"]


def wait_for_completion(prompt_id: str, timeout: int = 300) -> dict:
    """Poll until job is done, return output info"""
    start = time.time()
    while time.time() - start < timeout:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as r:
            history = json.loads(r.read())
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(2)
    raise TimeoutError(f"ComfyUI job timed out after {timeout}s")


def download_image(filename: str, subfolder: str, output_path: str):
    """Download generated image from ComfyUI"""
    params = urllib.parse.urlencode({
        "filename": filename,
        "subfolder": subfolder,
        "type": "output"
    })
    url = f"{COMFYUI_URL}/view?{params}"
    urllib.request.urlretrieve(url, output_path)


def generate_image(prompt: str, output_path: str, scene_id: str) -> bool:
    """Generate single image with ComfyUI"""
    try:
        workflow = build_flux_workflow(prompt)
        print(f"   Queuing: {scene_id}")
        prompt_id = queue_prompt(workflow)
        print(f"   Waiting: {prompt_id[:8]}...")

        result = wait_for_completion(prompt_id)
        outputs = result.get("outputs", {})

        for node_id, node_output in outputs.items():
            if "images" in node_output:
                img_info = node_output["images"][0]
                download_image(img_info["filename"], img_info.get("subfolder", ""), output_path)
                print(f"   ✅ Saved: {Path(output_path).name}")
                return True

        print(f"   ⚠️  No image output for {scene_id}")
        return False

    except ConnectionRefusedError:
        print(f"   ❌ ComfyUI not running at {COMFYUI_URL}")
        print(f"      Start ComfyUI first: python ComfyUI/main.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def create_placeholder_image(output_path: str, text: str):
    """Create a placeholder when ComfyUI is not available"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (1920, 1080), color=(245, 240, 232))
        draw = ImageDraw.Draw(img)
        # Draw centered text
        draw.text((960, 540), text[:50], fill=(27, 82, 153), anchor="mm")
        img.save(output_path)
        print(f"   📦 Placeholder: {Path(output_path).name}")
    except ImportError:
        # Create tiny valid PNG without PIL
        print(f"   ⚠️  Skipped (install Pillow for placeholders): {Path(output_path).name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", default="output/script.json")
    parser.add_argument("--comfyui-url", default=COMFYUI_URL)
    parser.add_argument("--placeholder", action="store_true",
                        help="Create placeholder images if ComfyUI unavailable")
    args = parser.parse_args()

    global COMFYUI_URL
    COMFYUI_URL = args.comfyui_url

    with open(args.script, encoding="utf-8") as f:
        script = json.load(f)

    images_dir = ROOT / "output/images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Check if ComfyUI is reachable
    comfyui_available = False
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=3) as r:
            comfyui_available = r.status == 200
        print(f"✅ ComfyUI connected at {COMFYUI_URL}")
    except Exception:
        print(f"⚠️  ComfyUI not available at {COMFYUI_URL}")
        if not args.placeholder:
            print("   Use --placeholder flag to create placeholder images")
            print("   Or start ComfyUI: python ComfyUI/main.py --lowvram")
            sys.exit(1)

    # Generate intro image
    scenes = []
    if "intro" in script:
        scenes.append(("intro", script["intro"].get("visual_description", "professional finance intro")))

    for ch in script.get("chapters", []):
        scene_id = f"ch_{ch['id']:02d}"
        scenes.append((scene_id, ch.get("visual_description", f"business concept {ch['title']}")))

    if "outro" in script:
        scenes.append(("outro", "professional outro, thank you, subscribe concept"))

    print(f"\n🎨 Generating {len(scenes)} illustrations...")
    manifest = []

    for scene_id, visual_desc in scenes:
        output_path = str(images_dir / f"{scene_id}.png")

        if Path(output_path).exists():
            print(f"   ⏭️  Skip (exists): {scene_id}.png")
            manifest.append({"id": scene_id, "file": f"{scene_id}.png"})
            continue

        if comfyui_available:
            ok = generate_image(visual_desc, output_path, scene_id)
            if not ok and args.placeholder:
                create_placeholder_image(output_path, visual_desc)
        else:
            create_placeholder_image(output_path, visual_desc)

        manifest.append({"id": scene_id, "file": f"{scene_id}.png"})
        time.sleep(0.5)  # Brief pause between jobs

    # Save manifest
    manifest_path = images_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Images complete!")
    print(f"   Count   : {len(manifest)}")
    print(f"   Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
