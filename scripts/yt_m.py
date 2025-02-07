import os
import requests

INPUT_FILE = "yt_info.txt"
OUTPUT_DIR = "output"
DEFAULT_M3U8 = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"

def grab(url):
    """嘗試解析 YouTube 直播 M3U8 連結"""
    try:
        response = requests.get(url, timeout=15).text
        if '.m3u8' not in response:
            return None
        
        start = response.find("https://")
        end = response.find(".m3u8") + 5
        if start != -1 and end != -1:
            return response[start:end]
    except Exception as e:
        print(f"❌ 解析失敗: {url}, 錯誤: {e}")
    return None

def process_channels():
    """讀取 yt_info.txt，解析 M3U8，並生成 M3U8 檔案"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("~~")]

    existing_files = sorted(
        [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".m3u8")]
    )

    for index, line in enumerate(lines):
        parts = line.split("|")
        if len(parts) < 2:
            print(f"❌ 格式錯誤: {line}")
            continue

        channel_name = parts[0].strip()
        youtube_url = parts[1].strip()

        print(f"🔍 解析: {channel_name} ({youtube_url})")

        m3u8_link = grab(youtube_url) or DEFAULT_M3U8
        m3u8_content = f"#EXTM3U\n#EXTINF:-1,{channel_name}\n{m3u8_link}\n"

        filename = f"y{index + 1:02}.m3u8"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as m3u8_file:
            m3u8_file.write(m3u8_content)
        
        print(f"✅ 已生成 {filename} ({channel_name})")

if __name__ == "__main__":
    process_channels()
