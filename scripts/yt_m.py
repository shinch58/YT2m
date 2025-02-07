#! /usr/bin/python3

import requests
import os
import re

INPUT_FILE = "yt_info.txt"
OUTPUT_DIR = "output"
PLACEHOLDER_URL = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"

def extract_m3u8(url):
    """ 從 YouTube 直播頁面提取 .m3u8 連結 """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ 無法請求 {url}: {e}")
        return None

    matches = re.findall(r'https://[^\s]+\.m3u8', response.text)
    return matches[0] if matches else None

def process_channels():
    """ 解析 yt_info.txt 並生成 M3U8 清單 """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        lines = file.readlines()

    for idx, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("~~"):
            continue

        parts = line.split("|")
        if len(parts) < 2:
            print(f"❌ 格式錯誤: {line}")
            continue

        name = parts[0].strip()
        url = parts[1].strip()

        print(f"🔍 解析: {name} ({url})")
        m3u8_url = extract_m3u8(url)

        if not m3u8_url:
            print(f"❌  解析 {name} 失敗，使用預設 M3U8")
            m3u8_url = PLACEHOLDER_URL

        output_file = os.path.join(OUTPUT_DIR, f"y{idx:02d}.m3u8")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"#EXTINF:-1 ,{name}\n")
            f.write(f"{m3u8_url}\n")

        print(f"✅ 已生成 {output_file} ({name})")

if __name__ == "__main__":
    process_channels()
