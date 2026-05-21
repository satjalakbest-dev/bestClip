#!/usr/bin/env python3
"""
Step 2: Generate Thai voiceover audio from script
Usage: python scripts/generate_audio.py --script output/script.json --engine edge
Engines: edge (default, free, online) | f5 (local GPU, RTX 3070)
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent


# ─────────────────────────────────────────────
# Edge-TTS Engine (free, online, good quality)
# ─────────────────────────────────────────────

async def generate_edge_tts(text: str, output_path: str, voice: str):
    try:
        import edge_tts
    except ImportError:
        print("❌ Run: pip install edge-tts")
        sys.exit(1)

    communicate = edge_tts.Communicate(text, voice, rate="+5%")
    await communicate.save(output_path)


async def run_edge_tts(segments: list, voice: str, audio_dir: Path):
    """Generate all segments with Edge-TTS"""
    print(f"\n🎙️  Edge-TTS | Voice: {voice}")
    print(f"   Segments: {len(segments)}")

    results = []
    for i, seg in enumerate(segments):
        filename = f"segment_{i+1:02d}_{seg['id']}.mp3"
        output_path = str(audio_dir / filename)
        print(f"   [{i+1}/{len(segments)}] {seg['id']} — {len(seg['text'])} chars")

        await generate_edge_tts(seg["text"], output_path, voice)

        # Get duration
        duration = get_audio_duration(output_path)
        results.append({
            "id": seg["id"],
            "file": filename,
            "duration_seconds": duration,
            "text": seg["text"]
        })
        print(f"            ✅ {filename} ({duration:.1f}s)")

    return results


# ─────────────────────────────────────────────
# F5-TTS Engine (local GPU, best quality)
# ─────────────────────────────────────────────

def run_f5_tts(segments: list, audio_dir: Path, ref_audio: str = None):
    """Generate all segments with F5-TTS Thai"""
    try:
        from f5_tts_th.tts import TTS
        import soundfile as sf
        import numpy as np
    except ImportError:
        print("❌ Run: pip install f5-tts-th soundfile")
        sys.exit(1)

    ref_audio = ref_audio or str(ROOT / "assets/samples/reference_voice.wav")
    if not Path(ref_audio).exists():
        print(f"❌ Reference audio not found: {ref_audio}")
        print("   Put a 5-10 second Thai speech WAV file at assets/samples/reference_voice.wav")
        sys.exit(1)

    print(f"\n🎙️  F5-TTS Thai | RTX 3070 8GB")
    print(f"   Reference: {ref_audio}")
    print(f"   Segments : {len(segments)}")

    tts = TTS(model="v1")

    # Read ref text from file if exists, otherwise use placeholder
    ref_text_path = ROOT / "assets/samples/reference_text.txt"
    ref_text = ref_text_path.read_text(encoding="utf-8").strip() if ref_text_path.exists() else ""

    results = []
    for i, seg in enumerate(segments):
        filename = f"segment_{i+1:02d}_{seg['id']}.wav"
        output_path = str(audio_dir / filename)
        print(f"   [{i+1}/{len(segments)}] {seg['id']} — {len(seg['text'])} chars")

        # F5-TTS has max length — split long text
        text = seg["text"]
        if len(text) > 300:
            chunks = split_thai_text(text, max_chars=280)
            audio_chunks = []
            for chunk in chunks:
                wav = tts.infer(
                    ref_audio=ref_audio,
                    ref_text=ref_text,
                    gen_text=chunk,
                    step=32,
                    cfg=2.0,
                    speed=1.0
                )
                audio_chunks.append(wav)
            # Concatenate with small silence between
            silence = np.zeros(int(24000 * 0.3), dtype=np.float32)
            combined = np.concatenate([c for chunk_arr in [(a, silence) for a in audio_chunks] for c in chunk_arr][:-1])
            sf.write(output_path, combined, 24000)
        else:
            wav = tts.infer(
                ref_audio=ref_audio,
                ref_text=ref_text,
                gen_text=text,
                step=32,
                cfg=2.0,
                speed=1.0
            )
            sf.write(output_path, wav, 24000)

        duration = get_audio_duration(output_path)
        results.append({
            "id": seg["id"],
            "file": filename,
            "duration_seconds": duration,
            "text": text
        })
        print(f"            ✅ {filename} ({duration:.1f}s)")

    return results


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def get_audio_duration(path: str) -> float:
    """Get audio duration using mutagen or ffprobe"""
    try:
        from mutagen.mp3 import MP3
        from mutagen.wave import WAVE
        from mutagen import File
        audio = File(path)
        return audio.info.length
    except Exception:
        pass
    # Fallback: use ffprobe
    import subprocess
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", path
    ], capture_output=True, text=True)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return float(data["streams"][0].get("duration", 0))
    return 0.0


def split_thai_text(text: str, max_chars: int = 280) -> list:
    """Split Thai text at sentence boundaries"""
    sentences = []
    for part in text.replace("!", "!|").replace("?", "?|").replace(".", ".|").split("|"):
        part = part.strip()
        if part:
            sentences.append(part)

    chunks = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) <= max_chars:
            current += " " + sent if current else sent
        else:
            if current:
                chunks.append(current)
            current = sent
    if current:
        chunks.append(current)
    return chunks


def extract_segments(script: dict) -> list:
    """Extract all narration segments from script"""
    segments = []

    # Intro
    if "intro" in script:
        segments.append({
            "id": "intro",
            "text": script["intro"]["narration"]
        })

    # Chapters
    for ch in script.get("chapters", []):
        segments.append({
            "id": f"ch_{ch['id']:02d}",
            "text": ch["narration"]
        })

    # Outro
    if "outro" in script:
        segments.append({
            "id": "outro",
            "text": script["outro"]["narration"]
        })

    return segments


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", default="output/script.json")
    parser.add_argument("--engine", choices=["edge", "f5"], default="edge")
    parser.add_argument("--voice", default="th-TH-NiwatNeural",
                        help="Edge-TTS voice (th-TH-NiwatNeural or th-TH-PremwadeeNeural)")
    parser.add_argument("--ref-audio", help="F5-TTS reference WAV path")
    args = parser.parse_args()

    # Load script
    with open(args.script, encoding="utf-8") as f:
        script = json.load(f)

    audio_dir = ROOT / "output/audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    segments = extract_segments(script)
    print(f"📊 Found {len(segments)} narration segments")

    # Generate audio
    if args.engine == "edge":
        results = asyncio.run(run_edge_tts(segments, args.voice, audio_dir))
    else:
        results = run_f5_tts(segments, audio_dir, args.ref_audio)

    # Save manifest
    manifest_path = ROOT / "output/audio/manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total_duration = sum(r["duration_seconds"] for r in results)
    print(f"\n✅ Audio complete!")
    print(f"   Files    : {len(results)} segments")
    print(f"   Duration : {total_duration/60:.1f} minutes")
    print(f"   Manifest : {manifest_path}")


if __name__ == "__main__":
    main()
