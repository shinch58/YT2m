import os
import re
import requests
import paramiko

# GitHub Actions 變數 (三組 API 金鑰)
YOUTUBE_API_KEYS = [
    os.getenv("Y_1", ""),
    os.getenv("Y_2", ""),
    os.getenv("Y_3", "")
]

# 檔案路徑
yt_info_path = "yt_info.txt"
output_dir = "output"

# SFTP 設定
SFTP_HOST = os.getenv("SFTP_HOST", "your_sftp_server.com")
SFTP_PORT = int(os.getenv("SFTP_PORT", 22))
SFTP_USER = os.getenv("SFTP_USER", "your_username")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD", "your_password")
SFTP_REMOTE_DIR = os.getenv("SFTP_REMOTE_DIR", "/remote/path/")

# 確保輸出目錄存在
os.makedirs(output_dir, exist_ok=True)

def extract_video_id(url):
    """從 YouTube 連結提取影片 ID"""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def grab(youtube_url):
    """使用三組 YouTube API 金鑰或 HTTP 解析 M3U8 連結"""
    video_id = extract_video_id(youtube_url)
    if not video_id:
        print(f"⚠️ 無效的 YouTube 連結: {youtube_url}")
        return "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/no_s.m3u8"

    # 1️⃣ 嘗試使用 YouTube API (輪流使用三組金鑰)
    for api_key in YOUTUBE_API_KEYS:
        if api_key:
            api_url = f"https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={video_id}&key={api_key}"
            try:
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                data = response.json()

                if "items" in data and data["items"]:
                    hls_url = data["items"][0].get("liveStreamingDetails", {}).get("hlsManifestUrl")
                    if hls_url:
                        print(f"✅ API 解析成功: {hls_url}")
                        return hls_url
            except requests.RequestException:
                print("⚠️ API 解析失敗，嘗試下一組金鑰...")

    # 2️⃣ 如果 API 失敗，改用 HTTP 解析 HTML
    try:
        print(f"🔍 嘗試透過 HTTP 解析 M3U8: {youtube_url}")
        response = requests.get(youtube_url, timeout=10)
        response.raise_for_status()
        m3u8_matches = re.findall(r"https://[^\"']+\.m3u8", response.text)
        if m3u8_matches:
            return m3u8_matches[0]
    except requests.RequestException as e:
        print(f"⚠️ HTTP 解析失敗: {e}")

    return "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/no_s.m3u8"

def process_yt_info():
    """解析 yt_info.txt 並生成 M3U8 和 PHP 檔案"""
    with open(yt_info_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 1
    for line in lines:
        line = line.strip()
        if line.startswith("~~") or not line:
            continue
        if "|" in line:  # 頻道資訊行
            parts = line.split("|")
            channel_name = parts[0].strip() if len(parts) > 0 else f"Channel {i}"
        else:  # YouTube 連結行
            youtube_url = line
            m3u8_url = grab(youtube_url)

            # 生成 M3U8 文件
            m3u8_content = f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\n{m3u8_url}\n"
            output_m3u8 = os.path.join(output_dir, f"y{i:02d}.m3u8")
            with open(output_m3u8, "w", encoding="utf-8") as f:
                f.write(m3u8_content)

            # 生成 PHP 文件
            php_content = f"""<?php
    header('Location: {m3u8_url}');
?>"""
            output_php = os.path.join(output_dir, f"y{i:02d}.php")
            with open(output_php, "w", encoding="utf-8") as f:
                f.write(php_content)

            print(f"✅ 生成 {output_m3u8} 和 {output_php}")
            i += 1

def upload_files():
    """使用 SFTP 上傳 M3U8 檔案"""
    print("🚀 啟動 SFTP 上傳程序...")
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)

        print(f"✅ 成功連接到 SFTP：{SFTP_HOST}")

        # 確保遠端目錄存在
        try:
            sftp.chdir(SFTP_REMOTE_DIR)
        except IOError:
            print(f"📁 遠端目錄 {SFTP_REMOTE_DIR} 不存在，正在創建...")
            sftp.mkdir(SFTP_REMOTE_DIR)
            sftp.chdir(SFTP_REMOTE_DIR)

        # 上傳所有檔案
        for file in os.listdir(output_dir):
            local_path = os.path.join(output_dir, file)
            remote_path = os.path.join(SFTP_REMOTE_DIR, file)
            if os.path.isfile(local_path):
                print(f"⬆️ 上傳 {local_path} → {remote_path}")
                sftp.put(local_path, remote_path)

        sftp.close()
        transport.close()
        print("✅ SFTP 上傳完成！")

    except Exception as e:
        print(f"❌ SFTP 上傳失敗: {e}")

if __name__ == "__main__":
    process_yt_info()
    upload_files()
