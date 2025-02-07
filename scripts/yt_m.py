#!/usr/bin/python3

import requests
import os
import re

# 設定檔與輸出目錄
YT_INFO_PATH = "yt_info.txt"
OUTPUT_DIR = "output"
PLACEHOLDER_URL = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"

# 確保輸出目錄存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 解析 YouTube 頁面，擷取 `.m3u8` 連結
def grab_m3u8(youtube_url):
    try:
        response = requests.get(youtube_url, timeout=15).text
        match = re.search(r'(https?://[^"]+\.m3u8)', response)
        return match.group(1) if match else PLACEHOLDER_URL
    except Exception as e:
        print(f"❌ 解析失敗: {youtube_url}, 錯誤: {e}")
        return PLACEHOLDER_URL

# 讀取 yt_info.txt 並解析頻道資訊
with open(YT_INFO_PATH, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip() and not line.startswith("~~")]

m3u8_files = {}  # 用來追蹤頻道名稱對應的 m3u8 檔案

for i in range(len(lines)):
    line = lines[i]

    if not line.startswith("https"):
        ch_name, grp_title, tvg_logo, tvg_id = map(str.strip, line.split("|"))
        output_filename = f"y{i//2 + 1:02}.m3u8"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        m3u8_files[output_path] = f"#EXTM3U\n#EXTINF:-1 group-title=\"{grp_title}\" tvg-logo=\"{tvg_logo}\" tvg-id=\"{tvg_id}\", {ch_name}\n"
    else:
        m3u8_url = grab_m3u8(line)
        output_path = list(m3u8_files.keys())[-1]
        m3u8_files[output_path] += f"{m3u8_url}\n"

# 寫入 `.m3u8` 檔案，確保覆蓋舊的
for path, content in m3u8_files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        print(f"✅ 已生成 {path}")

print("✅ M3U8 解析完成")
