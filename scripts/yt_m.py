import os
import subprocess

YT_INFO_FILE = "yt_info.txt"
OUTPUT_DIR = "output/"
FALLBACK_M3U8 = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"

# 確保 output 目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 測試是否能讀取 YT_COOKIES
if "YT_COOKIES" not in os.environ or not os.environ["YT_COOKIES"]:
    print("❌ 環境變數 YT_COOKIES 未設置")
else:
    print("✅ 成功讀取 YT_COOKIES")
    with open("cookies.txt", "w") as f:
        f.write(os.getenv("YT_COOKIES"))

def get_m3u8(url):
    """使用 yt-dlp 解析 M3U8"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--cookies", "cookies.txt", "-g", url],
            capture_output=True, text=True, timeout=30
        )
        if "m3u8" in result.stdout:
            print(f"✅ 成功解析 M3U8: {result.stdout.strip()}")
            return result.stdout.strip()
        else:
            print("⚠️ yt-dlp 解析失敗，使用預設 M3U8")
            return FALLBACK_M3U8
    except Exception as e:
        print(f"⚠️ yt-dlp 發生錯誤: {e}")
        return FALLBACK_M3U8

# 讀取 yt_info.txt 解析直播網址
with open(YT_INFO_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

index = 1
for i in range(len(lines)):
    if lines[i].startswith("http"):
        channel_name = lines[i - 1].split("|")[0].strip()
        yt_url = lines[i].strip()
        m3u8_url = get_m3u8(yt_url)

        # 生成 M3U8 檔案
        output_file = os.path.join(OUTPUT_DIR, f"y{index:02}.m3u8")
        with open(output_file, "w", encoding="utf-8") as out:
            out.write("#EXTM3U\n")
            out.write(f"#EXTINF:-1,{channel_name}\n")
            out.write(f"{m3u8_url}\n")
        
        print(f"✅ 生成 {output_file}")
        index += 1
