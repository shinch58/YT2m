import os
import re
import subprocess
import base64

# 設定檔案路徑
YT_INFO_FILE = "yt_info.txt"
OUTPUT_DIR = "output"
COOKIES_FILE = os.path.join(OUTPUT_DIR, "cookies.txt")

# 確保輸出目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 讀取環境變數中的 Base64 Cookies，並解碼儲存
yt_cookies_b64 = os.getenv("YT_COOKIES", "").strip()
if yt_cookies_b64:
    with open(COOKIES_FILE, "wb") as f:
        f.write(base64.b64decode(yt_cookies_b64))
    print("✅ cookies.txt 生成完成")
else:
    print("❌ 環境變數 YT_COOKIES 未設置")
    exit(1)

# 讀取 yt_info.txt
if not os.path.exists(YT_INFO_FILE):
    print(f"❌ {YT_INFO_FILE} 不存在")
    exit(1)

with open(YT_INFO_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 解析 yt_info.txt
youtube_urls = []
for line in lines:
    line = line.strip()
    if line.startswith("http"):
        youtube_urls.append(line)

# 解析 YouTube 直播 M3U8 連結
for idx, youtube_url in enumerate(youtube_urls, start=1):
    output_file = os.path.join(OUTPUT_DIR, f"y{idx:02d}.m3u8")

    print(f"🔍 嘗試解析 M3U8: {youtube_url}")

    # 執行 yt-dlp 解析 M3U8
    yt_dlp_cmd = f"yt-dlp --cookies {COOKIES_FILE} --sleep-requests 2 --limit-rate 100K -g {youtube_url}"
    result = subprocess.run(yt_dlp_cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0 and result.stdout.strip():
        m3u8_url = result.stdout.strip()
        print(f"✅ 成功解析: {m3u8_url}")
    else:
        error_msg = result.stderr.strip()
        print(f"⚠️ yt-dlp 解析失敗，錯誤訊息: {error_msg}")

        # 使用預設 M3U8 連結
        m3u8_url = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"
        print(f"⚠️ 無法解析 M3U8，使用預設: {m3u8_url}")

    # 生成 M3U8 檔案
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"#EXTINF:-1,{youtube_url}\n")
        f.write(f"{m3u8_url}\n")

    print(f"✅ 生成 {output_file}")

# 刪除 cookies.txt（增加安全性）
os.remove(COOKIES_FILE)
print("✅ cookies.txt 已刪除")

print("✅ yt_m.py 執行完成")
