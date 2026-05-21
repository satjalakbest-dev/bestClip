#!/usr/bin/env python3
"""
bestClip Pipeline Orchestrator
Run: python workflow/pipeline.py --topic "Your topic here"
"""

import argparse
import subprocess
import sys
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent


def run_step(name: str, cmd: list, required: bool = True) -> bool:
    print(f"\n{'='*60}")
    print(f"  STEP: {name}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"\n❌ FAILED: {name}")
        if required:
            sys.exit(1)
        return False
    print(f"\n✅ DONE: {name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="bestClip Full Pipeline")
    parser.add_argument("--topic", type=str, help="Video topic in Thai")
    parser.add_argument("--script", type=str, help="Skip to step 2 with existing script.json")
    parser.add_argument("--skip-images", action="store_true", help="Skip image generation")
    parser.add_argument("--skip-audio", action="store_true", help="Skip audio generation")
    parser.add_argument("--tts-engine", choices=["edge", "f5"], default="edge",
                        help="TTS engine: edge (online, free) or f5 (local GPU)")
    parser.add_argument("--voice", type=str, default="th-TH-NiwatNeural",
                        help="Edge-TTS voice name")
    args = parser.parse_args()

    # Setup output directories
    for d in ["output/audio", "output/images", "output/subtitles", "output/final"]:
        (ROOT / d).mkdir(parents=True, exist_ok=True)

    script_path = args.script or str(ROOT / "output/script.json")

    print("\n🎬 bestClip Pipeline Starting...")
    print(f"   Topic  : {args.topic or '(from existing script)'}")
    print(f"   TTS    : {args.tts_engine} / {args.voice}")

    # Step 1: Generate Script
    if not args.script:
        if not args.topic:
            print("❌ Error: provide --topic or --script")
            sys.exit(1)
        run_step("Generate Script", [
            sys.executable, "scripts/generate_script.py",
            "--topic", args.topic,
            "--output", script_path
        ])

    # Validate script
    with open(script_path, encoding="utf-8") as f:
        script = json.load(f)
    print(f"\n📋 Script: {script['title']} ({len(script['chapters'])} chapters)")

    # Step 2: Generate Audio
    if not args.skip_audio:
        run_step("Generate Thai Audio", [
            sys.executable, "scripts/generate_audio.py",
            "--script", script_path,
            "--engine", args.tts_engine,
            "--voice", args.voice
        ])

    # Step 3: Generate Subtitles
    run_step("Generate Subtitles (SRT)", [
        sys.executable, "scripts/generate_subtitles.py",
        "--script", script_path
    ])

    # Step 4: Generate Images
    if not args.skip_images:
        run_step("Generate AI Illustrations", [
            sys.executable, "scripts/generate_images.py",
            "--script", script_path
        ], required=False)  # Non-fatal — can use fallbacks

    # Step 5: Render Video
    run_step("Render Final Video (Remotion)", [
        sys.executable, "scripts/render_video.py",
        "--script", script_path
    ])

    output = ROOT / "output/final/video_final.mp4"
    print(f"\n🎉 Pipeline Complete!")
    print(f"   Output: {output}")


if __name__ == "__main__":
    main()
