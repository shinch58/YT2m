import os
import subprocess

# 設定檔案路徑
yt_info_path = "yt_info.txt"
output_dir = "output"
cookies_path = "cookies.txt"  # 與 go.sh 同目錄

# 確保輸出目錄存在
os.makedirs(output_dir, exist_ok=True)

def grab(youtube_url):
    """使用 yt-dlp 解析 M3U8 連結"""
    yt_dlp_cmd = f"yt-dlp --cookies {cookies_path} --sleep-requests 2 --limit-rate 500K -g {youtube_url}"
    try:
        result = subprocess.run(yt_dlp_cmd, shell=True, capture_output=True, text=True, check=True)
        m3u8_url = result.stdout.strip()
        if m3u8_url.startswith("http"):
            return m3u8_url
    except subprocess.CalledProcessError as e:
        print(f"⚠️ yt-dlp 解析失敗，錯誤訊息: {e.stderr}")
    return "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"  # 預設 M3U8

def process_yt_info():
    """解析 yt_info.txt 並生成 M3U8 檔案"""
    with open(yt_info_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 1
    channel_name = None

    for line in lines:
        line = line.strip()
        if line.startswith("~~") or not line:
            continue
        if "|" in line:  # 頻道資訊行
            parts = line.split("|")
            channel_name = parts[0].strip() if len(parts) > 0 else f"Channel {i}"
        else:  # YouTube 連結行
            youtube_url = line
            print(f"🔍 嘗試解析 M3U8: {youtube_url}")
            m3u8_url = grab(youtube_url)

            # 生成正確的 M3U8 文件內容
            m3u8_content = f"#EXTM3U\n#EXTINF:-1,{channel_name}\n{m3u8_url}\n"

            output_path = os.path.join(output_dir, f"y{i:02d}.m3u8")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(m3u8_content)

            print(f"✅ 生成 {output_path}")
            i += 1

if __name__ == "__main__":
    process_yt_info()
