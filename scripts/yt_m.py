import os
import logging
import subprocess
import paramiko
import time
import json
import requests
from urllib.parse import urlparse

# ================== 基本路徑 ==================
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
output_dir = os.path.join(root_dir, "output")
log_dir = os.path.join(root_dir, "log")
cookies_path = os.path.join(root_dir, "cookies.txt")
yt_info_path = os.path.join(root_dir, "yt_info.txt")

os.makedirs(output_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

print("專案根目錄:", root_dir)
print("腳本目錄:", script_dir)

# ================== Logging ==================
logging.basicConfig(
    filename=os.path.join(log_dir, "log.txt"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ================== 環境變數 ==================
YOUTUBE_API_KEY = os.getenv("YT_API_KEY", "")
SF_L = os.getenv("SF_L", "")

if not SF_L:
    print("❌ 缺少 SF_L")
    exit(1)

parsed = urlparse(SF_L)
SFTP_HOST = parsed.hostname
SFTP_PORT = parsed.port or 22
SFTP_USER = parsed.username
SFTP_PASSWORD = parsed.password
SFTP_REMOTE_DIR = parsed.path or "/"

print("SFTP 設定完成")

# ================== 行為設定 ==================
USE_API_CHECK = False        # 你目前是關閉 API 判斷
FORCE_PARSE = False
GEO_BYPASS = True
GEO_BYPASS_COUNTRY = "TW"

NO_STREAM_M3U8 = "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"

# ================== 工具函式 ==================
def extract_id_from_url(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0], "video"
    elif "/channel/" in url:
        return url.split("/channel/")[-1].split("/")[0], "channel"
    return "", "unknown"


def check_live_with_api(youtube_url):
    if not USE_API_CHECK or not YOUTUBE_API_KEY:
        return True, youtube_url

    vid, t = extract_id_from_url(youtube_url)
    try:
        if t == "video":
            r = requests.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "snippet,liveStreamingDetails",
                    "id": vid,
                    "key": YOUTUBE_API_KEY,
                },
                timeout=10
            ).json()
            if r.get("items"):
                if r["items"][0]["snippet"].get("liveBroadcastContent") == "live":
                    return True, youtube_url

        elif t == "channel":
            r = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "channelId": vid,
                    "eventType": "live",
                    "type": "video",
                    "key": YOUTUBE_API_KEY,
                },
                timeout=10
            ).json()
            if r.get("items"):
                live_id = r["items"][0]["id"]["videoId"]
                return True, f"https://www.youtube.com/watch?v={live_id}"

    except Exception as e:
        logging.warning("API live check failed: %s", e)

    return True, youtube_url


def check_if_live_with_ytdlp(url):
    cmd = ["yt-dlp", "--dump-json", "--no-warnings"]
    if os.path.exists(cookies_path):
        cmd += ["--cookies", cookies_path]
    if GEO_BYPASS:
        cmd += ["--geo-bypass", "--geo-bypass-country", GEO_BYPASS_COUNTRY]
    cmd.append(url)

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        info = json.loads(r.stdout)
        return info.get("is_live", False)
    except:
        return False


# ================== 核心解析 ==================
def grab(youtube_url):
    is_live, corrected_url = check_live_with_api(youtube_url)

    if not is_live and not FORCE_PARSE:
        if not check_if_live_with_ytdlp(youtube_url):
            return NO_STREAM_M3U8

    youtube_url = corrected_url

    strategies = [
        ("Android", ["youtube:player_client=android"]),
        ("AndroidE", ["youtube:player_client=android_embedded"]),
        ("iOS", ["youtube:player_client=ios"]),
        ("Web", ["youtube:player_client=web_embedded"]),
    ]

    for name, extractor_args in strategies:
        print("策略:", name)

        cmd = [
            "yt-dlp",
            "-f", "best[protocol=m3u8][height<=720]/best[protocol=m3u8]",
            "-g",
            "--no-check-certificate",
            "--extractor-args", ",".join(extractor_args),
        ]

        if os.path.exists(cookies_path):
            cmd += ["--cookies", cookies_path]

        if GEO_BYPASS:
            cmd += ["--geo-bypass", "--geo-bypass-country", GEO_BYPASS_COUNTRY]

        cmd.append(youtube_url)

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            m3u8 = r.stdout.strip()
            if "m3u8" in m3u8 and "googlevideo.com" in m3u8:
                print("✅ 解析成功")
                return m3u8
        except:
            pass

        time.sleep(1)

    return NO_STREAM_M3U8


# ================== 讀取 yt_info.txt ==================
def process_yt_info():
    if not os.path.exists(yt_info_path):
        print("❌ 找不到 yt_info.txt")
        return

    with open(yt_info_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    entries = lines[2:]
    idx = 1
    i = 0

    while i + 1 < len(entries):
        info = entries[i]
        url = entries[i + 1]

        channel = info.split("|")[0].strip() or f"Channel{idx:02d}"

        print(f"📺 {channel}")
        print("URL:", url)

        m3u8 = grab(url)

        m3u8_file = os.path.join(output_dir, f"y{idx:02d}.m3u8")
        php_file = os.path.join(output_dir, f"y{idx:02d}.php")

        with open(m3u8_file, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write("#EXT-X-STREAM-INF:BANDWIDTH=1280000\n")
            f.write(m3u8 + "\n")

        with open(php_file, "w", encoding="utf-8") as f:
            f.write("<?php\n")
            f.write(f"header('Location: {m3u8}');\n")
            f.write("?>")

        print(f"✅ 完成 y{idx:02d}")
        idx += 1
        i += 2
        time.sleep(2)


# ================== SFTP ==================
def upload_files():
    print("📤 SFTP 上傳中")
    try:
        t = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        t.connect(username=SFTP_USER, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(t)

        try:
            sftp.chdir(SFTP_REMOTE_DIR)
        except:
            sftp.mkdir(SFTP_REMOTE_DIR)
            sftp.chdir(SFTP_REMOTE_DIR)

        for f in os.listdir(output_dir):
            lp = os.path.join(output_dir, f)
            if os.path.isfile(lp):
                print("上傳:", f)
                sftp.put(lp, os.path.join(SFTP_REMOTE_DIR, f))

        sftp.close()
        t.close()
        print("✅ SFTP 完成")
    except Exception as e:
        print("❌ SFTP 失敗:", e)


# ================== Main ==================
if __name__ == "__main__":
    print("YouTube M3U8 解析器啟動")

    try:
        v = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
        print("yt-dlp:", v.stdout.strip())
    except:
        print("❌ 找不到 yt-dlp")
        exit(1)

    start = time.time()
    process_yt_info()
    upload_files()
    print("🎉 完成，耗時", round(time.time() - start, 2), "秒")
