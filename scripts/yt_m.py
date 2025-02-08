import os
import subprocess

# 設定目錄與檔案
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INFO_FILE = os.path.join(BASE_DIR, "yt_info.txt")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FALLBACK_M3U8 = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"

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
    """使用 yt-dlp 取得 M3U8 連結，並顯示錯誤資訊"""
    try:
        print(f"🔍 嘗試解析 M3U8: {url}")
        result = subprocess.run(["yt-dlp", "-g", url], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"⚠️ yt-dlp 執行失敗，錯誤訊息: {result.stderr}")
        return result.stdout.strip() if "m3u8" in result.stdout else FALLBACK_M3U8
    except Exception as e:
        print(f"⚠️ yt-dlp 執行異常: {e}")
        return FALLBACK_M3U8

def main():
    channels = read_yt_info()
    if not channels:
        print("❌ 錯誤: 沒有有效的 YouTube 直播 URL")
        return

    for idx, (channel_name, url) in enumerate(channels, start=1):
        filename = os.path.join(OUTPUT_DIR, f"y{idx:02d}.m3u8")
        m3u8_url = get_m3u8(url)

        content = f"#EXTM3U\n#EXTINF:-1 ,{channel_name}\n{m3u8_url}"
        with open(filename, "w", encoding="utf-8") as output_file:
            output_file.write(content)

        print(f"✅ 生成 {filename}")

if __name__ == "__main__":
    main()
