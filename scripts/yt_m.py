#!/usr/bin/env python3
import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

YT_INFO_FILE = "yt_info.txt"
OUTPUT_DIR = "output/"
M3U8_NOT_FOUND = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"

# 確保輸出目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 設定 Selenium 瀏覽器
chrome_options = Options()
chrome_options.add_argument("--headless")  # 無頭模式
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

def grab_m3u8(url):
    """使用 Selenium 解析 YouTube 直播頁面的 .m3u8 連結"""
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        time.sleep(5)  # 等待 JavaScript 加載

        # 取得頁面 HTML
        page_source = driver.page_source
        driver.quit()

        # 用正則表達式尋找 .m3u8 連結
        match = re.search(r'(https?://[^"]+\.m3u8)', page_source)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"❌ 解析失敗: {url}, 錯誤: {e}")
    return M3U8_NOT_FOUND

def parse_yt_info():
    """解析 yt_info.txt，返回頻道資訊列表"""
    channels = []
    with open(YT_INFO_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    i = 0
    while i < len(lines):
        if lines[i].startswith("~~") or "|" not in lines[i]:
            i += 1
            continue
        try:
            ch_name, grp_title, tvg_logo, tvg_id = [x.strip() for x in lines[i].split("|")]
            yt_url = lines[i + 1].strip()
            if yt_url.startswith("https://www.youtube.com/"):
                channels.append((ch_name, grp_title, tvg_logo, tvg_id, yt_url))
            else:
                print(f"❌ 格式錯誤: {yt_url}")
            i += 2
        except IndexError:
            print(f"❌ 資料格式錯誤，跳過: {lines[i]}")
            i += 1
    return channels

def write_m3u8(index, ch_name, grp_title, tvg_logo, tvg_id, m3u8_url):
    """生成 M3U8 檔案"""
    filename = f"{OUTPUT_DIR}y{index:02d}.m3u8"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f'#EXTINF:-1 group-title="{grp_title}" tvg-logo="{tvg_logo}" tvg-id="{tvg_id}", {ch_name}\n')
        f.write(m3u8_url + "\n")
    print(f"✅ 已生成 {filename} ({ch_name})")

def main():
    print("🚀 運行 yt_m.py 解析 YouTube 直播 M3U8")
    channels = parse_yt_info()
    
    if not channels:
        print("⚠️ 沒有可解析的頻道")
        return

    for index, (ch_name, grp_title, tvg_logo, tvg_id, yt_url) in enumerate(channels, start=1):
        print(f"🔍 解析: {ch_name} ({yt_url})")
        m3u8_url = grab_m3u8(yt_url)
        write_m3u8(index, ch_name, grp_title, tvg_logo, tvg_id, m3u8_url)
        time.sleep(2)  # 避免請求過快被 YouTube 限制

    print("✅ M3U8 解析完成")

if __name__ == "__main__":
    main()
