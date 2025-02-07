import os
import re
import requests
from bs4 import BeautifulSoup

# 設定輸出目錄
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 讀取 yt_info.txt
YT_INFO_FILE = "yt_info.txt"

def get_m3u8_url(youtube_url):
    """透過解析 YouTube 頁面 HTML 來獲取 M3U8 連結"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(youtube_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ 無法請求 {youtube_url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    scripts = soup.find_all("script")

    for script in scripts:
        if script.string and "hlsManifestUrl" in script.string:
            match = re.search(r'"hlsManifestUrl":"(https:[^"]+)"', script.string)
            if match:
                return match.group(1).replace("\\u0026", "&")

    print(f"❌ 解析失敗: {youtube_url}")
    return None

def parse_yt_info():
    """解析 yt_info.txt 並生成 M3U8 檔案"""
    with open(YT_INFO_FILE, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]

    channels = []
    for i in range(2, len(lines), 2):  # 每兩行為一組 (標題 + 連結)
        if i + 1 < len(lines):
            meta, url = lines[i], lines[i + 1]
            name = meta.split("|")[0].strip()
            channels.append((name, url))

    for idx, (name, url) in enumerate(channels):
        print(f"🔍 解析: {name} ({url})")
        m3u8_url = get_m3u8_url(url)
        if m3u8_url:
            m3u8_content = f"EXTM3U\n#EXTINF:-1 ,{name}\n{m3u8_url}\n"
            output_file = os.path.join(OUTPUT_DIR, f"y{idx+1:02d}.m3u8")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(m3u8_content)
            print(f"✅  已生成 {output_file}")
        else:
            print(f"❌  解析 {name} 失敗")

if __name__ == "__main__":
    parse_yt_info()
