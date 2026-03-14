#!/usr/bin/env python3
"""
Fetch YouTube subtitle/transcript using yt-dlp.
Usage: python fetch_transcript.py <youtube_url_or_id> [--output-dir <dir>] [--proxy <url>] [--cookies <path>]
"""

import sys
import re
import json
import argparse
import tempfile
import os
from datetime import datetime


def install_if_missing(package, import_name=None):
    import importlib, subprocess
    import_name = import_name or package
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"Installing {package}...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])


install_if_missing("yt-dlp", "yt_dlp")

import yt_dlp
from yt_dlp.utils import DownloadError


def exit_error(error_type: str, message: str, hints: list = None):
    result = {
        "error": True,
        "error_type": error_type,
        "message": message,
        "hints": hints or [],
    }
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
    sys.exit(1)


def extract_video_id(url_or_id: str) -> str:
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
        r"^([A-Za-z0-9_-]{11})$",
    ]
    for pattern in patterns:
        m = re.search(pattern, url_or_id)
        if m:
            return m.group(1)
    raise ValueError(f"Cannot extract video ID from: {url_or_id}")


def get_subtitle_data(video_id: str, proxy: str = None, cookies: str = None) -> dict:
    """
    Use yt-dlp to fetch subtitle info and content.
    Returns dict with: title, subtitles dict, automatic_captions dict.
    """
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }
    if proxy:
        ydl_opts["proxy"] = proxy
    if cookies:
        ydl_opts["cookiefile"] = cookies

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

    return {
        "title": info.get("title", video_id),
        "subtitles": info.get("subtitles", {}),
        "automatic_captions": info.get("automatic_captions", {}),
    }


def pick_best_subtitle(subtitles: dict, auto_captions: dict) -> tuple:
    """
    Returns (url, lang_code, is_foreign, is_auto).
    Priority: manual zh-TW > zh-Hant > zh > zh-CN > any manual > auto zh > any auto
    """
    preferred_zh = ["zh-TW", "zh-Hant", "zh", "zh-CN", "zh-Hans"]

    def best_format_url(formats: list) -> str:
        # Prefer json3 > srv3 > vtt > ttml
        for fmt in ["json3", "srv3", "vtt", "ttml"]:
            for f in formats:
                if f.get("ext") == fmt:
                    return f.get("url")
        return formats[0].get("url") if formats else None

    # Manual subtitles first
    for lang in preferred_zh:
        if lang in subtitles:
            url = best_format_url(subtitles[lang])
            if url:
                return url, lang, False, False

    # Any other manual subtitle
    for lang, fmts in subtitles.items():
        if lang == "live_chat":
            continue
        url = best_format_url(fmts)
        if url:
            return url, lang, True, False

    # Auto-generated Chinese
    for lang in preferred_zh:
        if lang in auto_captions:
            url = best_format_url(auto_captions[lang])
            if url:
                return url, lang, False, True

    # Any auto caption
    for lang, fmts in auto_captions.items():
        if lang == "live_chat":
            continue
        url = best_format_url(fmts)
        if url:
            return url, lang, True, True

    return None, None, False, False


def download_subtitle_content(url: str, proxy: str = None, cookies: str = None) -> str:
    """Download subtitle file content as text."""
    import urllib.request
    req = urllib.request.Request(url, headers={
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    })
    if proxy:
        req = urllib.request.Request(url, headers=req.headers)
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        )
    else:
        opener = urllib.request.build_opener()

    if cookies:
        from http.cookiejar import MozillaCookieJar
        jar = MozillaCookieJar(cookies)
        jar.load(ignore_discard=True, ignore_expires=True)
        opener.add_handler(urllib.request.HTTPCookieProcessor(jar))

    with opener.open(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_json3(content: str) -> list:
    """Parse yt-dlp json3 subtitle format into list of {t_sec, text}."""
    data = json.loads(content)
    entries = []
    for event in data.get("events", []):
        segs = event.get("segs", [])
        text = "".join(s.get("utf8", "") for s in segs).strip()
        if text and text != "\n":
            t_sec = event.get("tStartMs", 0) // 1000
            entries.append({"t": t_sec, "text": text})
    return entries


def parse_vtt(content: str) -> list:
    """Parse WebVTT subtitle format into list of {t_sec, text}."""
    entries = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Look for timestamp lines like: 00:00:01.000 --> 00:00:04.000
        if "-->" in line:
            time_part = line.split("-->")[0].strip()
            # Parse HH:MM:SS.mmm or MM:SS.mmm
            parts = time_part.replace(",", ".").split(":")
            try:
                if len(parts) == 3:
                    t_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                else:
                    t_sec = int(parts[0]) * 60 + float(parts[1])
            except Exception:
                t_sec = 0
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1
            text = " ".join(text_lines)
            # Remove VTT tags like <00:00:01.000><c>text</c>
            text = re.sub(r"<[^>]+>", "", text).strip()
            if text:
                entries.append({"t": int(t_sec), "text": text})
        else:
            i += 1
    return entries


def parse_subtitle(content: str, url: str) -> list:
    """Auto-detect format and parse."""
    if "json3" in url or content.strip().startswith("{"):
        return parse_json3(content)
    else:
        return parse_vtt(content)


def format_time(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def entries_to_plain(entries: list) -> str:
    return " ".join(e["text"] for e in entries if e.get("text"))


def entries_to_timestamped(entries: list) -> str:
    return "\n".join(f"[{format_time(e['t'])}] {e['text']}" for e in entries if e.get("text"))


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


IP_BLOCKED_HINTS = [
    "【方法一：等待】稍等 5～15 分鐘後重試，YouTube 的限速通常是暫時的。",
    "【方法二：使用 Proxy（最有效）】若你有 VPN 或代理軟體（Clash/v2rayN 等），找到本地 proxy port 後加上參數，例如：--proxy http://127.0.0.1:7890",
    "【方法三：使用瀏覽器 Cookies】在 Chrome 安裝「Get cookies.txt LOCALLY」擴充功能，匯出 youtube.com 的 cookies.txt 後加上：--cookies /path/to/cookies.txt",
    "【方法四：手動取得】在 YouTube 影片頁面點選「…」→「開啟逐字稿」，手動複製文字。",
]


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube subtitle with yt-dlp")
    parser.add_argument("url", help="YouTube URL or video ID")
    parser.add_argument("--output-dir", default="video")
    parser.add_argument("--proxy", default=None, help="Proxy URL, e.g. http://127.0.0.1:7890")
    parser.add_argument("--cookies", default=None, help="Path to cookies.txt exported from browser")
    args = parser.parse_args()

    # Extract video ID
    try:
        video_id = extract_video_id(args.url)
    except ValueError as e:
        exit_error("invalid_url", str(e), [
            "支援格式：https://youtube.com/watch?v=xxx、youtu.be/xxx、或直接輸入 11 碼影片 ID",
        ])

    print(f"Video ID: {video_id}", file=sys.stderr)

    # Get subtitle list and metadata via yt-dlp
    try:
        data = get_subtitle_data(video_id, proxy=args.proxy, cookies=args.cookies)
    except DownloadError as e:
        err = str(e)
        if "429" in err or "Too Many Requests" in err:
            exit_error("ip_blocked", "YouTube 封鎖了此 IP 的請求（HTTP 429），無法取得字幕。", IP_BLOCKED_HINTS)
        elif "private" in err.lower():
            exit_error("private_video", "這是私人影片，無法存取。", [])
        else:
            exit_error("fetch_error", f"無法取得影片資訊：{err}", ["請確認連結是否正確，以及網路連線是否正常。"])

    title = data["title"]
    print(f"Title: {title}", file=sys.stderr)

    # Pick best subtitle
    sub_url, lang, is_foreign, is_auto = pick_best_subtitle(data["subtitles"], data["automatic_captions"])

    if not sub_url:
        exit_error("no_transcript", "這部影片沒有任何可用的字幕或逐字稿。", [
            "影片可能尚未產生自動字幕，或創作者未上傳手動字幕。",
            "可稍後再試，YouTube 有時會延遲產生自動字幕。",
        ])

    print(f"Language: {lang} | is_foreign: {is_foreign} | is_auto: {is_auto}", file=sys.stderr)

    # Download subtitle content
    try:
        content = download_subtitle_content(sub_url, proxy=args.proxy, cookies=args.cookies)
    except Exception as e:
        err = str(e)
        if "429" in err:
            exit_error("ip_blocked", "YouTube 封鎖了此 IP 的請求（HTTP 429），無法下載字幕內容。", IP_BLOCKED_HINTS)
        else:
            exit_error("download_error", f"下載字幕失敗：{err}", ["請確認網路連線後重試。"])

    # Parse subtitle
    entries = parse_subtitle(content, sub_url)
    if not entries:
        exit_error("parse_error", "字幕內容解析失敗（可能格式不支援）。", ["請回報此問題。"])

    plain_text = entries_to_plain(entries)
    timestamped = entries_to_timestamped(entries)

    result = {
        "error": False,
        "video_id": video_id,
        "title": title,
        "language": lang,
        "is_foreign": is_foreign,
        "is_auto_generated": is_auto,
        "plain_text": plain_text,
        "timestamped": timestamped,
        "output_dir": args.output_dir,
        "safe_title": sanitize_filename(title),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()
