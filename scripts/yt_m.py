import os
import subprocess

# 設定目錄
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../output")
os.makedirs(OUTPUT_DIR, exist_ok=True)  # 確保 output/ 目錄存在

# YouTube 直播 URL（可自行修改）
YOUTUBE_STREAMS = [
    "https://www.youtube.com/watch?v=EXAMPLE1",
    "https://www.youtube.com/watch?v=EXAMPLE2",
]

# 替代連結（yt-dlp 失敗時使用）
FALLBACK_M3U8 = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"

def grab_m3u8(url):
    """使用 yt-dlp 擷取 YouTube 直播的 M3U8 連結"""
    try:
        result = subprocess.run(["yt-dlp", "-g", url], capture_output=True, text=True, timeout=30)
        m3u8_url = result.stdout.strip()
        return m3u8_url if "m3u8" in m3u8_url else FALLBACK_M3U8
    except Exception:
        return FALLBACK_M3U8  # 發生錯誤時使用預設連結

def main():
    for idx, url in enumerate(YOUTUBE_STREAMS, start=1):
        filename = os.path.join(OUTPUT_DIR, f"y{idx:02d}.m3u8")
        with open(filename, "w", encoding="utf-8") as output_file:
            output_file.write(grab_m3u8(url) + "\n")

if __name__ == "__main__":
    main()
