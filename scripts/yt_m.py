import os
import subprocess
import time
import json
import logging
import re
import paramiko
import requests
from urllib.parse import urlparse, unquote

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
GEO_BYPASS = True
GEO_COUNTRY = "TW"
NO_STREAM = "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 Chrome/120.0",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"
}

# ========= Cookies for requests =========
def load_cookies():
    jar = requests.cookies.RequestsCookieJar()
    if not os.path.exists(COOKIES_PATH):
        return jar
    with open(COOKIES_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("#") or "\t" not in line:
                continue
            parts = line.strip().split("\t")
            if len(parts) >= 7:
                jar.set(parts[5], parts[6], domain=parts[0])
    return jar

REQ_COOKIES = load_cookies()

# ========= HTML direct grab =========
def grab_m3u8_from_html(url):
    print("🌐 HTML 直抓")
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            cookies=REQ_COOKIES,
            timeout=15
        )
        html = r.text

        # 1️⃣ 直接找 m3u8
        m = re.findall(r"https://[^\"']+\.m3u8[^\"']*", html)
        for u in m:
            u = unquote(u)
            if "googlevideo.com" in u:
                print("✅ HTML 直接命中 m3u8")
                return u

        # 2️⃣ ytInitialPlayerResponse
        m = re.search(r"ytInitialPlayerResponse\s*=\s*({.+?});", html)
        if m:
            data = json.loads(m.group(1))
            streams = (
                data.get("streamingData", {})
                    .get("hlsManifestUrl")
            )
            if streams:
                print("✅ playerResponse 命中 m3u8")
                return streams

    except Exception as e:
        logging.warning("HTML grab failed: %s", e)

    return None

# ========= yt-dlp fallback =========
def grab_m3u8_ytdlp(url):
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
                print("✅ yt-dlp 命中 m3u8")
                return m3u8
        except:
            pass

        time.sleep(1)

    return None

# ========= Main grab =========
def grab(url):
    m3u8 = grab_m3u8_from_html(url)
    if m3u8:
        return m3u8

    m3u8 = grab_m3u8_ytdlp(url)
    if m3u8:
        return m3u8

    print("⚠️ fallback no_s")
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
        m3u8 = grab(url)

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

# ========= Entry =========
if __name__ == "__main__":
    print("🚀 yt_m.py start (HTML first)")
    subprocess.run(["yt-dlp", "--version"])
    process()
    upload()
    print("🎉 done")
