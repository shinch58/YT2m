import os
import subprocess

# 設定輸出目錄
script_dir = os.path.dirname(os.path.abspath(__file__))  # 取得 yt_m.py 所在目錄
base_dir = os.path.dirname(script_dir)  # 上層目錄
output_dir = os.path.join(base_dir, "output")
os.makedirs(output_dir, exist_ok=True)  # 確保 output 資料夾存在

# 讀取 yt_info.txt
yt_info_path = os.path.join(base_dir, "yt_info.txt")
with open(yt_info_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 過濾出 YouTube 直播連結
yt_links = [line.strip() for line in lines if line.startswith("http")]

result = subprocess.run(
    ["yt-dlp", "-g", "--live-from-start", url],
    capture_output=True, text=True, timeout=30
)

# 解析每個直播連結
for index, url in enumerate(yt_links, start=1):
    try:
        # 使用 yt-dlp 解析 M3U8 連結
        result = subprocess.run(
            ["yt-dlp", "-g", url],
            capture_output=True, text=True, timeout=30
        )
        m3u8_url = result.stdout.strip()

        # 取得對應的頻道名稱
        channel_name = lines[lines.index(url) - 1].split(" | ")[0].strip()

        # 檢查是否成功獲取 M3U8 連結
        if not m3u8_url or "m3u8" not in m3u8_url:
            print(f"⚠️  無法解析 {channel_name}，使用預設 M3U8")
            m3u8_url = "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u"

        # 生成 M3U8 檔案
        m3u8_filename = f"y{index:02}.m3u8"
        with open(os.path.join(output_dir, m3u8_filename), "w", encoding="utf-8") as m3u8_file:
            m3u8_file.write(f"EXTM3U\n#EXTINF:-1 ,{channel_name}\n{m3u8_url}\n")

        print(f"✅  已生成 {m3u8_filename} ({channel_name})")

    except Exception as e:
        print(f"❌  解析 {url} 失敗: {e}")

- name: 測試 yt-dlp 解析
  run: yt-dlp -g "https://www.youtube.com/watch?v=ylYJSBUgaMA" || echo "❌ yt-dlp 無法解析"
