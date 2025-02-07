import os
import sys
import requests
import subprocess

def grab(url, output_file):
    """使用 yt-dlp 解析 YouTube 直播的 M3U8 連結"""
    try:
        # 用 yt-dlp 取得 M3U8 連結
        result = subprocess.run(
            ["yt-dlp", "-g", url],
            capture_output=True, text=True, timeout=30
        )
        m3u8_url = result.stdout.strip()

        # Debug: 顯示取得的 M3U8 連結
        print(f"Extracted M3U8: {m3u8_url}")

        if "m3u8" in m3u8_url:
            output_file.write(f"{m3u8_url}\n")
        else:
            raise ValueError("No M3U8 found")
    except Exception as e:
        print(f"Error extracting M3U8 from {url}: {e}")
        output_file.write('https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u\n')
