#!/usr/bin/python3

import os
import sys
import requests

# 確定運行環境
windows = 'win' in sys.platform

# 確定 yt_info.txt 的完整路徑
script_dir = os.path.dirname(os.path.abspath(__file__))  # 取得當前腳本目錄
yt_info_path = os.path.join(script_dir, "../yt_info.txt")

# Debug: 確保找到 yt_info.txt
print(f"Trying to read: {yt_info_path}")
if not os.path.exists(yt_info_path):
    print("Error: yt_info.txt not found!")
    sys.exit(1)

# 設定輸出目錄
output_dir = os.path.join(script_dir, "../output/")
os.makedirs(output_dir, exist_ok=True)  # 確保 output 目錄存在
print(f"Output directory: {output_dir}")

def grab(url, output_file):
    """從 URL 擷取 M3U8 連結"""
    try:
        response = requests.get(url, timeout=15).text
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        output_file.write('https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u\n')
        return

    if '.m3u8' not in response:
        print(f"Warning: No M3U8 found in {url}, using fallback link.")
        output_file.write('https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u\n')
        return

    end = response.find('.m3u8') + 5
    tuner = 100
    while True:
        if 'https://' in response[end - tuner:end]:
            link = response[end - tuner:end]
            start = link.find('https://')
            end = link.find('.m3u8') + 5
            final_link = link[start:end]
            print(f"Extracted M3U8 link: {final_link}")
            output_file.write(f"{final_link}\n")
            return
        else:
            tuner += 5

# 開始處理 yt_info.txt
counter = 1
with open(yt_info_path, 'r') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('~~'):
            continue

        if not line.startswith('https:'):
            # 解析頻道資訊
            line_parts = line.split('|')
            if len(line_parts) < 4:
                print(f"Warning: Skipping invalid line: {line}")
                continue
            
            ch_name = line_parts[0].strip()
            grp_title = line_parts[1].strip().title()
            tvg_logo = line_parts[2].strip()
            tvg_id = line_parts[3].strip()
            
            output_filename = f"y{counter:02}.m3u8"
            output_filepath = os.path.join(output_dir, output_filename)
            
            # Debug: 顯示 M3U8 生成路徑
            print(f"Creating {output_filepath}")

            with open(output_filepath, 'w') as output_file:
                output_file.write('#EXTM3U x-tvg-url="https://github.com/botallen/epg/releases/download/latest/epg.xml"\n')
                output_file.write(f'#EXTINF:-1 group-title="{grp_title}" tvg-logo="{tvg_logo}" tvg-id="{tvg_id}", {ch_name}\n')

            counter += 1
        else:
            # 處理 URL
            with open(output_filepath, 'a') as output_file:
                grab(line, output_file)

# 清理暫存文件
temp_file = os.path.join(script_dir, 'temp.txt')
if os.path.exists(temp_file):
    os.remove(temp_file)
    print("Temporary file removed.")
