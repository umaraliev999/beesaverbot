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


def get_ydl_opts(platform: str, media_type: str, quality: str, output_dir: str) -> dict:
    output_template = os.path.join(output_dir, "%(title).50s.%(ext)s")

    common = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "max_filesize": 50 * 1024 * 1024,
        # Bot detection bypass
        "extractor_args": {
            "youtube": {
                "skip": ["dash", "hls"],
                "player_client": ["android", "web"],
            }
        },
        "http_headers": {
            "User-Agent": "com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip",
        },
    }

    # Cookie fayli mavjud bo'lsa ishlat
    if Path(COOKIES_FILE).exists():
        common["cookiefile"] = COOKIES_FILE

    quality_formats = {
        "360":  "best[height<=360][ext=mp4]/best[height<=360]",
        "720":  "best[height<=720][ext=mp4]/best[height<=720]",
        "1080": "best[height<=1080][ext=mp4]/best[height<=1080]",
        "best": "best[height<=720][ext=mp4]/best[height<=720]",
    }

    if media_type == "audio":
        return {
            **common,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

    fmt = quality_formats.get(quality, quality_formats["720"]) if platform == "youtube" else "best[ext=mp4]/best"

    return {
        **common,
        "format": fmt,
    }


def download_media(url: str, platform: str, media_type: str, quality: str, output_dir: str):
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
    if Path(COOKIES_FILE).exists():
        opts["cookiefile"] = COOKIES_FILE

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        entries = info.get("entries", [])
        return {
            "title": info.get("title", "Playlist"),
            "count": len(entries),
            "entries": entries,
        }


def download_playlist(url: str, output_dir: str):
    output_template = os.path.join(output_dir, "%(playlist_index)s_%(title).40s.%(ext)s")
    opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "format": "best[height<=720][ext=mp4]/best[height<=720]",
        "max_filesize": 50 * 1024 * 1024,
        "ignoreerrors": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }
    if Path(COOKIES_FILE).exists():
        opts["cookiefile"] = COOKIES_FILE

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.extract_info(url, download=True)

    files = sorted(Path(output_dir).iterdir(), key=lambda f: f.name)
    return [str(f) for f in files if f.is_file()]