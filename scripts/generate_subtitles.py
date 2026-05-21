#!/usr/bin/env python3
"""
Step 3: Generate SRT subtitles from script + audio durations
Usage: python scripts/generate_subtitles.py --script output/script.json
Note: Uses actual audio file durations for perfect sync (no ASR needed!)
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def ms_to_srt_time(ms: float) -> str:
    """Convert milliseconds to SRT timestamp HH:MM:SS,mmm"""
    ms = int(ms)
    hours = ms // 3_600_000
    ms %= 3_600_000
    minutes = ms // 60_000
    ms %= 60_000
    seconds = ms // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def split_into_subtitle_lines(text: str, max_chars: int = 50) -> list:
    """Split narration text into subtitle-sized chunks for Thai"""
    # Remove double spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Split at natural Thai pause points
    sentences = re.split(r"(?<=[.!?ๆ])\s+|(?<=\s{0}[,،])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    lines = []
    current = ""
    for sent in sentences:
        words = sent.split(" ")
        for word in words:
            test = (current + " " + word).strip()
            if len(test) <= max_chars:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
    if current:
        lines.append(current)

    # Merge very short lines (strict: combined length stays within max_chars)
    merged = []
    i = 0
    while i < len(lines):
        if i + 1 < len(lines) and len(lines[i]) + len(lines[i+1]) + 1 <= max_chars:
            merged.append(lines[i] + " " + lines[i+1])
            i += 2
        else:
            merged.append(lines[i])
            i += 1

    return merged if merged else [text[:max_chars]]


def generate_srt(script: dict, audio_manifest: list = None) -> str:
    """
    Generate SRT content.
    If audio_manifest provided, uses real timings.
    Otherwise estimates based on character count (fallback).
    """
    CHARS_PER_SECOND = 6.5  # Average Thai speech rate

    srt_entries = []
    entry_index = 1
    current_ms = 0

    # Build segment durations map
    duration_map = {}
    if audio_manifest:
        for item in audio_manifest:
            duration_map[item["id"]] = item["duration_seconds"] * 1000  # to ms

    def process_segment(seg_id: str, text: str):
        nonlocal entry_index, current_ms

        # Get duration
        if seg_id in duration_map:
            total_ms = duration_map[seg_id]
        else:
            total_ms = (len(text) / CHARS_PER_SECOND) * 1000

        lines = split_into_subtitle_lines(text, max_chars=50)
        ms_per_line = total_ms / max(len(lines), 1)

        for line in lines:
            start_ms = current_ms
            end_ms = current_ms + ms_per_line

            srt_entries.append(
                f"{entry_index}\n"
                f"{ms_to_srt_time(start_ms)} --> {ms_to_srt_time(end_ms)}\n"
                f"{line}\n"
            )
            entry_index += 1
            current_ms = end_ms

        # Small gap between segments
        current_ms += 200

    # Process intro
    if "intro" in script:
        process_segment("intro", script["intro"]["narration"])

    # Process chapters
    for ch in script.get("chapters", []):
        process_segment(f"ch_{ch['id']:02d}", ch["narration"])

    # Process outro
    if "outro" in script:
        process_segment("outro", script["outro"]["narration"])

    return "\n".join(srt_entries)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", default="output/script.json")
    parser.add_argument("--audio-manifest", default="output/audio/manifest.json")
    parser.add_argument("--output", default="output/subtitles/subtitles.srt")
    args = parser.parse_args()

    with open(args.script, encoding="utf-8") as f:
        script = json.load(f)

    # Load audio manifest if available
    audio_manifest = None
    manifest_path = Path(args.audio_manifest)
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            audio_manifest = json.load(f)
        print(f"✅ Using real audio timing from {manifest_path}")
    else:
        print("⚠️  No audio manifest found — estimating timing from character count")

    srt_content = generate_srt(script, audio_manifest)

    # Save SRT
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(srt_content, encoding="utf-8")

    # Count entries
    count = srt_content.count("\n\n")
    print(f"✅ Subtitles: {output_path}")
    print(f"   Entries: {count}")

    # Also save as VTT (for web use)
    vtt_path = output_path.with_suffix(".vtt")
    vtt = "WEBVTT\n\n" + srt_content.replace(",", ".")
    vtt_path.write_text(vtt, encoding="utf-8")
    print(f"   VTT: {vtt_path}")


if __name__ == "__main__":
    main()
