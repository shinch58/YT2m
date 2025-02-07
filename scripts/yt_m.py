import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# 設定輸出目錄
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 設定 Selenium 瀏覽器選項
chrome_options = Options()
chrome_options.add_argument("--headless")  # 無頭模式
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

def get_m3u8_url(youtube_url):
    """使用 Selenium 爬取 YouTube 頁面，解析 M3U8 連結"""
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(youtube_url)
    time.sleep(5)  # 等待 YouTube 動態內容載入

    page_source = driver.page_source
    driver.quit()

    # 在 HTML 內查找 hlsManifestUrl
    match = re.search(r'"hlsManifestUrl":"(https:[^"]+)"', page_source)
    if match:
        return match.group(1).replace("\\u0026", "&")

    print(f"❌ 解析失敗: {youtube_url}")
    return None

def parse_yt_info():
    """解析 yt_info.txt 並生成 M3U8 檔案"""
    with open("yt_info.txt", "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]

    channels = []
    for i in range(2, len(lines), 2):
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
