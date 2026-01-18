#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import hashlib
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INFO_FILE = os.path.join(BASE_DIR, "yt_info.txt")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"
}

NO_STREAM = "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"
MAX_HEIGHT = 720   # 🔒 鎖定最高 720p

# ---------- 工具 ----------

def sha1(data):
    return hashlib.sha1(data.encode("utf-8")).hexdigest()

def safe_get(url, timeout=10):
    return requests.get(url, headers=HEADERS, timeout=timeout)

def safe_head(url, timeout=5):
    return requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)

# ---------- HTML 直抓 m3u8 ----------

def grab_html_m3u8(youtube_url):
    try:
        html = safe_get(youtube_url).text
    except Exception:
        return None

    m = re.search(r'https://manifest\.googlevideo\.com/[^"]+\.m3u8[^"]*', html)
    if m:
        return m.group(0)
    return None

# ---------- master.m3u8 → 選最高 ≤720p ----------

def select_720p_from_master(master_url):
    try:
        txt = safe_get(master_url).text
    except Exception:
        return None

    streams = []
    lines = txt.splitlines()

    for i in range(len(lines)):
        if lines[i].startswith("#EXT-X-STREAM-INF"):
            m = re.search(r"RESOLUTION=\d+x(\d+)", lines[i])
            if not m:
                continue
            h = int(m.group(1))
            if h <= MAX_HEIGHT:
                streams.append((h, lines[i + 1]))

    if not streams:
        return None

    streams.sort(reverse=True, key=lambda x: x[0])
    return streams[0][1]

# ---------- 檔案處理 ----------

def write_if_changed(path, content):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            old = f.read()
        if sha1(old) == sha1(content):
            return False

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True

def build_m3u8(target_url):
    return "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1500000\n" + target_url + "\n"

def build_php(target_url):
    return "<?php\nheader(\"Location: {}\");\nexit;\n?>".format(target_url)

# ---------- 主流程 ----------

def main():
    print(datetime.now().strftime("%Y.%m.%d"))
    print("🚀 yt_m.py start (HTML first)")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(INFO_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    idx = 0
    i = 2
    while i < len(lines):
        if "|" in lines[i]:
            name = lines[i].split("|")[0].strip()
            url = lines[i + 1].strip()
            idx += 1

            print(f"📺 {name}")
            print("🌐 HTML 直抓")

            final_m3u8 = NO_STREAM

            master = grab_html_m3u8(url)
            if master:
                stream_720 = select_720p_from_master(master)
                if stream_720:
                    # 驗證是否還活著
                    try:
                        r = safe_head(stream_720)
                        if r.status_code == 200:
                            final_m3u8 = stream_720
                            print("✅ HTML 直接命中 m3u8 (720p)")
                        else:
                            print("⚠️ m3u8 已失效，使用 fallback")
                    except Exception:
                        pass

            out_m3u8 = os.path.join(OUTPUT_DIR, "y{:02d}.m3u8".format(idx))
            out_php = os.path.join(OUTPUT_DIR, "y{:02d}.php".format(idx))

            changed = False
            changed |= write_if_changed(out_m3u8, build_m3u8(final_m3u8))
            changed |= write_if_changed(out_php, build_php(final_m3u8))

            if not changed:
                print("ℹ️ 無變更，跳過寫入")

            time.sleep(1)
            i += 2
        else:
            i += 1

    print("🎉 done")

if __name__ == "__main__":
    main()
