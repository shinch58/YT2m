import os
import subprocess

# 設定目錄
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
output_dir = os.path.join(parent_dir, "output")

# 確保 output 目錄存在
os.makedirs(output_dir, exist_ok=True)

# 讀取 yt_info.txt
yt_info_path = os.path.join(parent_dir, "yt_info.txt")
with open(yt_info_path, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

# 過濾 YouTube 直播連結
yt_links = [line for line in lines if line.startswith("https://www.youtube.com/watch")]

# 解析 YouTube 連結
for index, url in enumerate(yt_links, start=1):
    print(f"🔍 解析: {url}")
    try:
        result = subprocess.run(
            ["yt-dlp", "-g", "--live-from-start", url],
            capture_output=True, text=True, timeout=30
        )
        m3u8_url = result.stdout.strip()
        if not m3u8_url:
            raise ValueError("未取得 M3U8")

        # 生成對應的 M3U8 檔案
        m3u8_filename = os.path.join(output_dir, f"y{index:02}.m3u8")
        with open(m3u8_filename, "w", encoding="utf-8") as m3u8_file:
            m3u8_file.write(f"EXTM3U\n#EXTINF:-1 ,{url}\n{m3u8_url}\n")

        print(f"✅  已生成 {m3u8_filename}")
    except Exception as e:
        print(f"❌  解析 {url} 失敗: {e}")
