# scripts/yt_m.py

import os
import re
import requests
from urllib.parse import urlparse, parse_qs

yt_info_path = "yt_info.txt"
output_dir = "output"
php_template = "<?php\nheader('Location: {}');\n?>\n"

def extract_4gtv_channel_id(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    ch = query.get("ch", [None])[0]
    return int(ch) if ch and ch.isdigit() else None

def get_4gtv_m3u8(channel_id):
    api_url = "https://api.4gtv.tv/Channel/GetChannelUrl.ashx"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {
        "ChannelID": channel_id,
        "Quality": "high",
        "Mode": 2
    }
    try:
        res = requests.post(api_url, headers=headers, json=payload, timeout=10)
        res.raise_for_status()
        return res.json().get("url")
    except Exception as e:
        print(f"❌ [4gtv] API 失敗（ChannelID={channel_id}）: {e}")
        return None

def main():
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(yt_info_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    output_count = 1
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("~~"):
            i += 1
            continue

        info_parts = [p.strip() for p in line.split("|")]
        if len(info_parts) < 2:
            i += 1
            continue

        name, group, *_ = info_parts
        if i + 1 >= len(lines):
            break

        url = lines[i + 1].strip()
        i += 2

        if "4gtv.tv/channel/" not in url or group.upper() != "HTML":
            continue

        channel_id = extract_4gtv_channel_id(url)
        if not channel_id:
            print(f"⚠️ 無法從 URL 擷取 channel_id: {url}")
            continue

        m3u8_url = get_4gtv_m3u8(channel_id)
        if not m3u8_url:
            print(f"⚠️ 無法取得 4gtv 串流: {name}")
            continue

        m3u8_path = os.path.join(output_dir, f"y{output_count:02}.m3u8")
        php_path = os.path.join(output_dir, f"y{output_count:02}.php")

        with open(m3u8_path, "w", encoding="utf-8") as f:
            f.write(f"#EXTM3U\n#EXTINF:-1 tvg-name=\"{name}\" group-title=\"{group}\",{name}\n{m3u8_url}\n")

        with open(php_path, "w", encoding="utf-8") as f:
            f.write(php_template.format(m3u8_url))

        print(f"✅ [{name}] ➜ y{output_count:02}.m3u8 / .php")
        output_count += 1

if __name__ == "__main__":
    main()
