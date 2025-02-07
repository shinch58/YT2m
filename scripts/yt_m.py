import subprocess
import os

# 讀取 yt_info.txt
script_dir = os.path.dirname(os.path.abspath(__file__))  # 獲取 scripts 目錄
base_dir = os.path.dirname(script_dir)  # 上層目錄（YT2m 主目錄）
info_path = os.path.join(base_dir, "yt_info.txt")  # yt_info.txt 路徑
output_dir = os.path.join(base_dir, "output")  # output 目錄

os.makedirs(output_dir, exist_ok=True)  # 確保 output 資料夾存在

# 讀取並解析 yt_info.txt
with open(info_path, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f.readlines() if line.strip()]

urls = [lines[i] for i in range(1, len(lines), 2)]  # 取得所有 YouTube 連結

for idx, url in enumerate(urls, start=1):
    print(f"🔍 解析: {url}")
    try:
        result = subprocess.run(
            ["yt-dlp", "-g", "--live-from-start", url],
            capture_output=True, text=True, timeout=30
        )
        m3u8_url = result.stdout.strip()
        if not m3u8_url.startswith("http"):
            raise ValueError("❌ 解析失敗: 取得的 M3U8 連結無效")
        
        m3u8_path = os.path.join(output_dir, f"y{idx:02}.m3u8")
        with open(m3u8_path, "w", encoding="utf-8") as f:
            f.write(f"EXTM3U\n#EXTINF:-1 ,Channel {idx}\n{m3u8_url}\n")

        print(f"✅ 已生成 {m3u8_path}")

    except Exception as e:
        print(f"❌ 解析 {url} 失敗: {e}")
