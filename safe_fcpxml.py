import csv
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from urllib.parse import quote


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v"}
FPS = 25
WIDTH = 1920
HEIGHT = 1080


def _slug(text: str, fallback: str = "media") -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:90] or fallback


def _file_uri(path: str) -> str:
    return "file://" + quote(str(Path(path).resolve()), safe="/:")


def _uid(path: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, _file_uri(path))).upper()


def _run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Command failed")
    return result


def media_files(media_dir: str):
    """Return images and videos, sorted by filename."""
    if not os.path.isdir(media_dir):
        return []
    allowed = IMAGE_EXTS | VIDEO_EXTS
    return sorted(
        f for f in os.listdir(media_dir)
        if not f.startswith(".") and Path(f).suffix.lower() in allowed
    )


def rename_media_batch(media_dir: str, rows: list, prefix: bool = True):
    """Rename rows of {'File Name': old, 'New Name': stem_or_name}. Returns a manifest path."""
    if not os.access(media_dir, os.W_OK):
        raise PermissionError(
            f"Cannot rename files in {media_dir}. Restart the app with write access "
            "to this media folder, or move/copy the media into a writable folder."
        )

    manifest_rows = []
    temp_pairs = []
    for idx, row in enumerate(rows, start=1):
        old_name = row.get("File Name", "")
        new_name = row.get("New Name", "")
        src = Path(media_dir) / old_name
        if not src.exists():
            manifest_rows.append([old_name, "", "skipped - missing source"])
            continue
        stem = _slug(Path(new_name).stem or new_name or src.stem)
        if prefix:
            stem = f"{idx:02d}_{stem}"
        dst = src.with_name(stem + src.suffix)
        suffix = 2
        while dst.exists():
            dst = src.with_name(f"{stem}_{suffix}{src.suffix}")
            suffix += 1
        tmp = src.with_name(src.name + ".renaming_tmp")
        src.rename(tmp)
        temp_pairs.append((tmp, dst, src.name))
    for tmp, dst, old_name in temp_pairs:
        tmp.rename(dst)
        manifest_rows.append([old_name, dst.name, "renamed"])

    out_dir = Path(media_dir) / "rename_manifests"
    out_dir.mkdir(exist_ok=True)
    manifest = out_dir / f"rename_manifest_{int(time.time())}.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["old_filename", "new_filename", "status"])
        writer.writerows(manifest_rows)
    return str(manifest)


def _video_frames(path: str) -> int:
    try:
        raw = subprocess.check_output(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=nb_frames,duration",
                "-of", "default=nw=1", path,
            ],
            text=True,
        )
        nb_frames = None
        duration = None
        for line in raw.splitlines():
            if line.startswith("nb_frames=") and line.split("=", 1)[1] != "N/A":
                nb_frames = int(line.split("=", 1)[1])
            if line.startswith("duration=") and line.split("=", 1)[1] != "N/A":
                duration = float(line.split("=", 1)[1])
        if nb_frames:
            return max(1, nb_frames)
        if duration:
            return max(1, round(duration * FPS))
    except Exception:
        pass
    return 5 * FPS


def _still_proxy(media_dir: str, filename: str, seconds: float):
    src = Path(media_dir) / filename
    out_dir = Path(media_dir) / "fcp_photo_video_proxies"
    out_dir.mkdir(exist_ok=True)
    dst = out_dir / f"{src.stem}_still_proxy.mp4"
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return str(dst)
    _run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-t", str(seconds), "-i", str(src),
            "-vf",
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS},format=yuv420p",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-movflags", "+faststart", str(dst),
        ]
    )
    return str(dst)


def generate_final_cut_safe_xml(media_dir: str, clips: list, project_name: str = "Safe Source Timeline"):
    """
    Generate the Final Cut XML pattern that avoided crashes:
    - video assets only
    - still images converted to short MP4 proxies
    - direct src attribute on asset
    - no media-rep, no colorSpace, no notes, minimal asset-clip syntax
    """
    assets = []
    spine = []
    manifest_rows = []
    current_frame = 0

    for idx, clip in enumerate(clips, start=2):
        filename = clip.get("File Name", "")
        source_path = Path(media_dir) / filename
        if not source_path.exists():
            raise FileNotFoundError(f"Missing source file: {filename}")

        duration_text = clip.get("Duration", "00:00:05")
        try:
            h, m, s = duration_text.split(":")
            duration_sec = int(h) * 3600 + int(m) * 60 + float(s)
        except Exception:
            duration_sec = 5.0

        if source_path.suffix.lower() in IMAGE_EXTS:
            media_path = Path(_still_proxy(media_dir, filename, duration_sec))
            source_label = f"{filename} -> {media_path.name}"
        else:
            media_path = source_path
            source_label = filename

        source_frames = _video_frames(str(media_path))
        duration_frames = min(max(1, round(duration_sec * FPS)), max(1, source_frames - 1))
        asset_id = f"r{idx}"
        asset_name = media_path.stem.replace("&", "and")
        assets.append(
            f'    <asset id="{asset_id}" name="{asset_name}" uid="{_uid(str(media_path))}" '
            f'src="{_file_uri(str(media_path))}" start="0s" duration="{source_frames}/{FPS}s" '
            f'hasVideo="1" format="r1"/>'
        )
        spine.append(
            f'            <asset-clip name="{asset_name}" ref="{asset_id}" '
            f'offset="{current_frame}/{FPS}s" start="0s" duration="{duration_frames}/{FPS}s"/>'
        )
        manifest_rows.append([current_frame / FPS, duration_frames / FPS, source_label])
        current_frame += duration_frames

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.6">
  <resources>
    <format id="r1" name="FFVideoFormat1080p25" frameDuration="1/25s" width="{WIDTH}" height="{HEIGHT}"/>
{chr(10).join(assets)}
  </resources>
  <library>
    <event name="{project_name}">
      <project name="{project_name}">
        <sequence format="r1" duration="{current_frame}/{FPS}s" tcStart="0s" tcFormat="NDF">
          <spine>
{chr(10).join(spine)}
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
'''
    out_dir = Path(media_dir) / "nle_exports"
    out_dir.mkdir(exist_ok=True)
    base = _slug(project_name, "safe_timeline")
    xml_path = out_dir / f"{base}_final_cut_safe.fcpxml"
    manifest_path = out_dir / f"{base}_manifest.csv"
    xml_path.write_text(xml, encoding="utf-8")
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timeline_start_seconds", "duration_seconds", "source"])
        writer.writerows(manifest_rows)
    return str(xml_path), str(manifest_path)
