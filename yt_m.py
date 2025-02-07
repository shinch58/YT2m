import os
import subprocess

# 設定目錄與檔案
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INFO_FILE = os.path.join(BASE_DIR, "yt_info.txt")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FALLBACK_M3U8 = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"

# 確保 output/ 目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_yt_info():
    if not os.path.exists(INFO_FILE):
        print(f"❌ 錯誤: 找不到 {INFO_FILE}")
        return []

    channels = []
    with open(INFO_FILE, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]
    
    i = 2
    while i < len(lines) - 1:
        channel_info = lines[i]
        yt_url = lines[i + 1]
        if "|" in channel_info and "youtube.com" in yt_url:
            channel_name = channel_info.split("|")[0].strip()
            channels.append((channel_name, yt_url))
        i += 2

    return channels

def get_m3u8(url):
    try:
        print(f"📡 嘗試從 {url} 獲取 M3U8 連結...")
        result = subprocess.run(["yt-dlp", "-g", url], capture_output=True, text=True, timeout=30)
        print(f"📝 yt-dlp 輸出: {result.stdout}")
        print(f"⚠️ yt-dlp 錯誤輸出: {result.stderr}")
        if "m3u8" in result.stdout:
            return result.stdout.strip()
        else:
            print("⚠️ 未找到 M3U8 連結，使用預設連結。")
            return FALLBACK_M3U8
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return FALLBACK_M3U8

def main():
    channels = read_yt_info()
    if not channels:
        print("❌ 錯誤: 沒有有效的 YouTube 直播 URL，請確認 yt_info.txt 是否正確")
        return

    for idx, (channel_name, url) in enumerate(channels, start=1):
        filename = os.path.join(OUTPUT_DIR, f"y{idx:02d}.m3u8")
        m3u8_url = get_m3u8(url)

        content = f"#EXTM3U\n#EXTINF:-1 ,{channel_name}\n{m3u8_url}"

        with open(filename, "w", encoding="
