import os
import subprocess

# 預設 M3U8 連結（解析失敗時使用）
FALLBACK_M3U8 = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"

# 讀取頻道資訊檔案
INFO_FILE = os.path.join(os.path.dirname(__file__), "../yt_info.txt")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../output")

# 確保 output 目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_m3u8(url):
    """使用 yt-dlp 解析 M3U8 連結，透過 stdin 傳遞 cookies"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--cookies-from-file", "-", "-g", url],
            input=os.getenv("YT_COOKIES"),  # 直接讀取環境變數
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip() if "m3u8" in result.stdout else FALLBACK_M3U8
    except Exception as e:
        print(f"⚠️ yt-dlp 執行失敗，錯誤訊息: {e}")
        return FALLBACK_M3U8

# 解析 yt_info.txt
with open(INFO_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

channels = []
current_channel = None

for line in lines:
    line = line.strip()
    if not line or line.startswith("~~"):
        continue  # 跳過空行或註解

    if "|" in line:
        if current_channel:
            channels.append(current_channel)
        current_channel = {"info": line, "url": None}
    else:
        if current_channel:
            current_channel["url"] = line
            channels.append(current_channel)
            current_channel = None

# 生成 M3U8 檔案
for index, channel in enumerate(channels):
    if not channel["url"]:
        continue  # 跳過沒有 URL 的頻道

    m3u8_link = get_m3u8(channel["url"])
    output_file = os.path.join(OUTPUT_DIR, f"y{index+1:02}.m3u8")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"#EXTINF:-1,{channel['info'].split('|')[0].strip()}\n")
        f.write(m3u8_link + "\n")

    print(f"✅ 生成 {output_file}")
