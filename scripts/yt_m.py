import os
import subprocess
import time
import json
import logging
import paramiko
import requests
from urllib.parse import urlparse

# ========= Paths =========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
LOG_DIR = os.path.join(ROOT_DIR, "log")
COOKIES_PATH = os.path.join(ROOT_DIR, "cookies.txt")
YT_INFO = os.path.join(ROOT_DIR, "yt_info.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "log.txt"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# ========= ENV =========
SF_L = os.getenv("SF_L", "")
YT_API_KEY = os.getenv("YT_API_KEY", "")

if not SF_L:
    print("❌ SF_L missing")
    exit(1)

p = urlparse(SF_L)
SFTP_HOST = p.hostname
SFTP_PORT = p.port or 22
SFTP_USER = p.username
SFTP_PASS = p.password
SFTP_DIR = p.path or "/"

# ========= Config =========
USE_API_CHECK = False
GEO_BYPASS = True
GEO_COUNTRY = "TW"
NO_STREAM = "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"

# ========= yt-dlp helpers =========
def is_live_ytdlp(url):
    try:
        r = subprocess.run(
            ["yt-dlp", "--dump-json", url],
            capture_output=True,
            text=True,
            timeout=30
        )
        info = json.loads(r.stdout)
        return info.get("is_live", False)
    except:
        return False

def grab_m3u8(url):
    strategies = [
        "youtube:player_client=android",
        "youtube:player_client=android_embedded",
        "youtube:player_client=ios",
        "youtube:player_client=web_embedded",
    ]

    for s in strategies:
        print("策略:", s)
        cmd = [
            "yt-dlp",
            "-f", "best[protocol=m3u8][height<=720]/best[protocol=m3u8]",
            "-g",
            "--extractor-args", s,
        ]

        if os.path.exists(COOKIES_PATH):
            cmd += ["--cookies", COOKIES_PATH]

        if GEO_BYPASS:
            cmd += ["--geo-bypass", "--geo-bypass-country", GEO_COUNTRY]

        cmd.append(url)

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            m3u8 = r.stdout.strip()
            if "m3u8" in m3u8 and "googlevideo.com" in m3u8:
                return m3u8
        except:
            pass

        time.sleep(1)

    return NO_STREAM

# ========= Process =========
def process():
    with open(YT_INFO, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    items = lines[2:]
    idx = 1
    i = 0

    while i + 1 < len(items):
        name = items[i].split("|")[0].strip()
        url = items[i + 1]

        print(f"📺 {name}")
        m3u8 = grab_m3u8(url)

        with open(os.path.join(OUTPUT_DIR, f"y{idx:02d}.m3u8"), "w") as f:
            f.write("#EXTM3U\n")
            f.write("#EXT-X-STREAM-INF:BANDWIDTH=1280000\n")
            f.write(m3u8 + "\n")

        with open(os.path.join(OUTPUT_DIR, f"y{idx:02d}.php"), "w") as f:
            f.write("<?php\n")
            f.write(f"header('Location: {m3u8}');\n")
            f.write("?>")

        idx += 1
        i += 2
        time.sleep(2)

# ========= SFTP =========
def upload():
    t = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    t.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(t)

    try:
        sftp.chdir(SFTP_DIR)
    except:
        sftp.mkdir(SFTP_DIR)
        sftp.chdir(SFTP_DIR)

    for f in os.listdir(OUTPUT_DIR):
        sftp.put(
            os.path.join(OUTPUT_DIR, f),
            os.path.join(SFTP_DIR, f)
        )

    sftp.close()
    t.close()

# ========= Main =========
if __name__ == "__main__":
    print("🚀 yt_m.py start")
    subprocess.run(["yt-dlp", "--version"])
    process()
    upload()
    print("🎉 done")
