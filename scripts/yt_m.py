import os
import base64
import requests
import subprocess

INFO_FILE = "yt_info.txt"
OUTPUT_DIR = "output"
DEFAULT_M3U8 = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"

# 確保 output 目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_yt_info():
    """ 讀取 yt_info.txt 並解析 YouTube 連結 """
    with open(INFO_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    channels = []
    current_channel = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith("~~"):
            continue
        if "youtube.com" in line:
            if current_channel:
                current_channel["url"] = line
                channels.append(current_channel)
                current_channel = None
        else:
            parts = line.split("|")
            current_channel = {
                "name": parts[0].strip(),
                "group": parts[1].strip() if len(parts) > 1 else "",
                "logo": parts[2].strip() if len(parts) > 2 else "",
                "tvg-id": parts[3].strip() if len(parts) > 3 else "",
            }

    return channels

def get_m3u8_from_ytdlp(youtube_url):
    """ 使用 yt-dlp 解析 M3U8 連結，優先使用 cookies.txt """
    try:
        result = subprocess.run(
            ["yt-dlp", "--cookies", "cookies.txt", "-g", youtube_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            print(f"⚠️ yt-dlp 解析失敗，錯誤訊息: {result.stderr.strip()}")
            return None
    except Exception as e:
        print(f"❌ 執行 yt-dlp 失敗: {e}")
        return None

def get_m3u8_from_html(youtube_url):
    """ 從 YouTube 頁面 HTML 解析 M3U8 連結 """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(youtube_url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text

        # 嘗試提取 M3U8 連結
        for line in html.split("\n"):
            if ".m3u8" in line:
                start = line.find("https://")
                end = line.find(".m3u8") + 5
                return line[start:end]
    except Exception as e:
        print(f"❌ HTML 解析失敗: {e}")
    return None

def generate_m3u8_files():
    """ 解析 YouTube 直播並生成 M3U8 文件 """
    channels = read_yt_info()
    
    for idx, channel in enumerate(channels, start=1):
        youtube_url = channel["url"]
        print(f"🔍 嘗試解析 M3U8: {youtube_url}")

        m3u8_url = get_m3u8_from_ytdlp(youtube_url)
        if not m3u8_url:
            m3u8_url = get_m3u8_from_html(youtube_url)
        
        if not m3u8_url:
            print("⚠️ 無法解析 M3U8，使用預設: " + DEFAULT_M3U8)
            m3u8_url = DEFAULT_M3U8

        output_file = os.path.join(OUTPUT_DIR, f"y{idx:02d}.m3u8")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"#EXTINF:-1,{channel['name']}\n")
            f.write(m3u8_url + "\n")

        print(f"✅ 生成 {output_file}")

if __name__ == "__main__":
    generate_m3u8_files()
    print("✅ yt_m.py 執行完成")
