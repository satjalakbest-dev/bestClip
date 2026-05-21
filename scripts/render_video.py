#!/usr/bin/env python3
"""
Step 5: Render final video using FFmpeg
Combines: images + audio + subtitles → MP4
Usage: python scripts/render_video.py --script output/script.json

No Node.js required — pure FFmpeg.
For Remotion-based rendering, see scripts/render_remotion.py
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Video settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30


def check_ffmpeg():
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if result.returncode != 0:
        print("❌ FFmpeg not found. Install: https://ffmpeg.org/download.html")
        sys.exit(1)


def load_manifests() -> tuple:
    """Load audio and image manifests"""
    audio_manifest_path = ROOT / "output/audio/manifest.json"
    image_manifest_path = ROOT / "output/images/manifest.json"

    audio_map = {}
    if audio_manifest_path.exists():
        with open(audio_manifest_path, encoding="utf-8") as f:
            for item in json.load(f):
                audio_map[item["id"]] = item

    image_map = {}
    if image_manifest_path.exists():
        with open(image_manifest_path, encoding="utf-8") as f:
            for item in json.load(f):
                image_map[item["id"]] = item

    return audio_map, image_map


def build_segment_list(script: dict, audio_map: dict, image_map: dict) -> list:
    """Build ordered list of segments with all asset paths"""
    segments = []

    def add_segment(seg_id: str, title: str = ""):
        audio_info = audio_map.get(seg_id, {})
        image_info = image_map.get(seg_id, {})

        audio_file = ROOT / "output/audio" / audio_info.get("file", "")
        image_file = ROOT / "output/images" / image_info.get("file", f"{seg_id}.png")

        # Fallback image: use last valid image
        if not image_file.exists():
            for f in sorted((ROOT / "output/images").glob("*.png")):
                image_file = f
                break

        duration = audio_info.get("duration_seconds", 5.0)

        segments.append({
            "id": seg_id,
            "title": title,
            "audio": str(audio_file) if audio_file.exists() else None,
            "image": str(image_file) if image_file.exists() else None,
            "duration": duration,
        })

    if "intro" in script:
        add_segment("intro", "Intro")

    for ch in script.get("chapters", []):
        add_segment(f"ch_{ch['id']:02d}", ch["title"])

    if "outro" in script:
        add_segment("outro", "Outro")

    return segments


def render_logo_intro(output_path: str, logo_path: str, duration: float = 3.0):
    """Render 3-second logo intro on blue background"""
    cmd = ["ffmpeg", "-y",
           "-f", "lavfi",
           "-i", f"color=#1B5299:size={VIDEO_WIDTH}x{VIDEO_HEIGHT}:duration={duration}:rate={FPS}",
           "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={duration}",
           "-c:v", "libx264", "-c:a", "aac",
           "-t", str(duration),
           output_path]

    # Add logo if exists
    if logo_path and Path(logo_path).exists():
        cmd = ["ffmpeg", "-y",
               "-f", "lavfi",
               "-i", f"color=#1B5299:size={VIDEO_WIDTH}x{VIDEO_HEIGHT}:duration={duration}:rate={FPS}",
               "-i", logo_path,
               "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={duration}",
               "-filter_complex",
               f"[0:v][1:v]overlay=(W-w)/2:(H-h)/2:enable='between(t,0.5,{duration})'[v]",
               "-map", "[v]", "-map", "2:a",
               "-c:v", "libx264", "-c:a", "aac",
               "-t", str(duration),
               output_path]

    subprocess.run(cmd, check=True, capture_output=True)


def render_segment(seg: dict, output_path: str):
    """Render single segment: image + audio with Ken Burns pan"""
    image = seg["image"]
    audio = seg["audio"]
    duration = seg["duration"]

    inputs = []
    outputs = []

    if not image:
        print(f"   Warning: No image for {seg['id']} - using solid color")
        inputs += ["-f", "lavfi", "-i",
                    f"color=#F5F0E8:size={VIDEO_WIDTH}x{VIDEO_HEIGHT}:duration={duration}:rate={FPS}"]
        outputs += ["-map", "0:v"]
    else:
        zoom_end = 1.05
        inputs += ["-loop", "1", "-i", image]
        filter_complex = (
            f"[0:v]scale={VIDEO_WIDTH*2}:{VIDEO_HEIGHT*2},"
            f"zoompan=z='min(zoom+0.0003,{zoom_end})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={int(duration*FPS)}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={FPS}[v]"
        )
        outputs += ["-filter_complex", filter_complex, "-map", "[v]"]

    # Add audio input
    if audio and Path(audio).exists():
        inputs += ["-i", audio]
    else:
        inputs += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    outputs += ["-map", "1:a"]

    outputs += [
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac", "-ar", "44100", "-b:a", "192k", "-ac", "2",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        output_path
    ]

    cmd = ["ffmpeg", "-y"] + inputs + outputs
    subprocess.run(cmd, check=True, capture_output=True)


def concatenate_segments(segment_files: list, output_path: str, srt_path: str = None):
    """Concatenate all segment videos and burn subtitles"""
    # Create concat file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for sf in segment_files:
            f.write(f"file '{sf}'\n")
        concat_file = f.name

    intermediate = output_path.replace(".mp4", "_nosubs.mp4")

    # Concatenate
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        intermediate
    ]
    subprocess.run(cmd_concat, check=True, capture_output=True)
    os.unlink(concat_file)

    # Burn subtitles
    if srt_path and Path(srt_path).exists():
        srt_for_ffmpeg = os.path.relpath(srt_path).replace("\\", "/")
        subtitle_filter = (
            f"subtitles={srt_for_ffmpeg}"
            f":force_style='FontSize=22,PrimaryColour=&HFFFFFF&,"
            f"OutlineColour=&H000000&,Outline=2,Shadow=1,"
            f"Alignment=2,MarginV=60'"
        )
        cmd_subs = [
            "ffmpeg", "-y",
            "-i", intermediate,
            "-vf", subtitle_filter,
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "copy",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        subprocess.run(cmd_subs, check=True, capture_output=True)
        os.unlink(intermediate)
        print("   ✅ Subtitles burned in")
    else:
        os.rename(intermediate, output_path)
        print("   ⚠️  No subtitles (run generate_subtitles.py first)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", default="output/script.json")
    parser.add_argument("--output", default="output/final/video_final.mp4")
    parser.add_argument("--no-logo", action="store_true")
    args = parser.parse_args()

    check_ffmpeg()

    with open(args.script, encoding="utf-8") as f:
        script = json.load(f)

    audio_map, image_map = load_manifests()
    segments = build_segment_list(script, audio_map, image_map)

    output_dir = ROOT / "output/final"
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = output_dir / "tmp"
    tmp_dir.mkdir(exist_ok=True)

    print(f"\n🎬 Rendering {len(segments)} segments...")

    segment_files = []

    # Logo intro (3 seconds)
    if not args.no_logo:
        logo_path = str(ROOT / "assets/logo/logo.png")
        logo_video = str(tmp_dir / "logo_intro.mp4")
        print("   [0/N] Logo intro...")
        try:
            render_logo_intro(logo_video, logo_path, duration=2.5)
            segment_files.append(logo_video)
        except Exception as e:
            print(f"   ⚠️  Logo intro failed: {e}")

    for i, seg in enumerate(segments):
        print(f"   [{i+1}/{len(segments)}] {seg['id']} ({seg['duration']:.1f}s)")
        seg_video = str(tmp_dir / f"seg_{i+1:02d}_{seg['id']}.mp4")
        try:
            render_segment(seg, seg_video)
            segment_files.append(seg_video)
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Render failed: {e.stderr.decode()[-200:]}")

    print(f"\n🔗 Concatenating {len(segment_files)} clips...")

    srt_path = str(ROOT / "output/subtitles/subtitles.srt")
    output_path = str(ROOT / args.output)

    concatenate_segments(segment_files, output_path, srt_path)

    # Cleanup tmp
    for f in tmp_dir.glob("*.mp4"):
        f.unlink()

    # Final stats
    output = Path(output_path)
    if output.exists():
        size_mb = output.stat().st_size / 1_048_576
        print(f"\n🎉 Video Complete!")
        print(f"   Output : {output_path}")
        print(f"   Size   : {size_mb:.1f} MB")
    else:
        print("❌ Output file not found — check FFmpeg errors above")


if __name__ == "__main__":
    main()
