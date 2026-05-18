import os
import yt_dlp
from pathlib import Path

COOKIES_FILE = os.getenv("COOKIES_FILE", "cookies.txt")


def detect_platform(url: str) -> str:
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    elif "instagram.com" in url_lower:
        return "instagram"
    elif "tiktok.com" in url_lower:
        return "tiktok"
    elif "pinterest.com" in url_lower or "pin.it" in url_lower:
        return "pinterest"
    return "unknown"


def get_format(platform: str, media_type: str, quality: str) -> str:
    if media_type == "audio":
        return "bestaudio/best"

    quality_map = {
        "360":  "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best[height<=360]",
        "720":  "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
        "1080": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]",
        "best": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
    }

    if platform == "youtube":
        return quality_map.get(quality, quality_map["720"])

    return "best[ext=mp4]/best"


def get_ydl_opts(platform: str, media_type: str, quality: str, output_dir: str) -> dict:
    output_template = os.path.join(output_dir, "%(title).50s.%(ext)s")
    fmt = get_format(platform, media_type, quality)

    common = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "max_filesize": 50 * 1024 * 1024,
    }

    if media_type == "audio":
        return {
            **common,
            "format": fmt,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

    opts = {
        **common,
        "format": fmt,
        "merge_output_format": "mp4",
    }

    if platform == "instagram":
        opts["http_headers"] = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
        }

    return opts


def download_media(url: str, platform: str, media_type: str, quality: str, output_dir: str) -> str | None:
    opts = get_ydl_opts(platform, media_type, quality, output_dir)

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.extract_info(url, download=True)

    files = list(Path(output_dir).iterdir())
    if not files:
        return None
    return str(max(files, key=lambda f: f.stat().st_size))


def get_playlist_info(url: str) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        entries = info.get("entries", [])
        return {
            "title": info.get("title", "Playlist"),
            "count": len(entries),
            "entries": entries,
        }


def download_playlist(url: str, output_dir: str) -> list[str]:
    output_template = os.path.join(output_dir, "%(playlist_index)s_%(title).40s.%(ext)s")

    opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best",
        "merge_output_format": "mp4",
        "max_filesize": 50 * 1024 * 1024,
        "ignoreerrors": True,  # Xatolikda keyingisiga o'tadi
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.extract_info(url, download=True)

    files = sorted(Path(output_dir).iterdir(), key=lambda f: f.name)
    return [str(f) for f in files if f.is_file()]
