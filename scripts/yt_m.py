import os
import subprocess

# 設定目錄與檔案
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # yt_m.py 的上一層
INFO_FILE = os.path.join(BASE_DIR, "yt_info.txt")  # YouTube 直播清單
OUTPUT_DIR = os.path.join(BASE_DIR, "output")  # M3U8 輸出目錄
FALLBACK_M3U8 = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"  # 預設連結

# 確保 output/ 目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_yt_info():
    """解析 yt_info.txt，獲取頻道名稱與 YouTube 直播 URL"""
    if not os.path.exists(INFO_FILE):
        print(f"❌ 錯誤: 找不到 {INFO_FILE}")
        return []

    channels = []
    with open(INFO_FILE, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]
    
    i = 2  # 跳過前兩行
    while i < len(lines) - 1:
        channel_info = lines[i]  # 頻道資訊 (格式: 頻道名稱 | YouTube | | )
        yt_url = lines[i + 1]    # YouTube 直播網址
        if "|" in channel_info and "youtube.com" in yt_url:
            channel_name = channel_info.split("|")[0].strip()  # 取得頻道名稱
            channels.append((channel_name, yt_url))
        i += 2  # 每次讀兩行

    return channels

def get_m3u8(url):
    """使用 yt-dlp 取得 M3U8 連結"""
    try:
        result = subprocess.run(["yt-dlp", "-g", url], capture_output=True, text=True, timeout=30)
        return result.stdout.strip() if "m3u8" in result.stdout else FALLBACK_M3U8
    except:
        return FALLBACK_M3U8  # 發生錯誤時使用預設連結

def main():
    channels = read_yt_info()
    if not channels:
        print("❌ 錯誤: 沒有有效的 YouTube 直播 URL，請確認 yt_info.txt 是否正確")
        return

    for idx, (channel_name, url) in enumerate(channels, start=1):
        filename = os.path.join(OUTPUT_DIR, f"y{idx:02d}.m3u8")
        m3u8_url = get_m3u8(url)

        # 生成符合格式的 M3U8 文件內容
        content = f"EXTM3U\n#EXTINF:-1 ,{channel_name}\n{m3u8_url}"

        with open(filename, "w", encoding="utf-8") as output_file:
            output_file.write(content)

        print(f"✅ 生成 {filename}")

if __name__ == "__main__":
    main()
