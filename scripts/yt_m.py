import os
import json
import time
import requests
import subprocess
import paramiko

# 設定檔案路徑
yt_info_path = "yt_info.txt"
tmp_info_path = "tmp_inf.txt"  # 暫存轉換後的 yt_info
output_dir = "output"
log_file = "logs.txt"

# YouTube API 金鑰
API_KEYS = [
    os.getenv("Y_1"),
    os.getenv("Y_2"),
    os.getenv("Y_3"),
]
api_index = 0  # 目前使用的 API 金鑰索引
API_URL = "https://www.googleapis.com/youtube/v3/search"

# SFTP 設定
SFTP_HOST = os.getenv("SFTP_HOST", "your_sftp_server.com")
SFTP_PORT = int(os.getenv("SFTP_PORT", 22))
SFTP_USER = os.getenv("SFTP_USER", "your_username")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD", "your_password")
SFTP_REMOTE_DIR = os.getenv("SFTP_REMOTE_DIR", "/remote/path/")

# 建立 log 記錄
def log_message(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)

# 轉換 @頻道/live → ?v=直播ID
def convert_live_links():
    global api_index
    with open(yt_info_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith("https://www.youtube.com/@") and "/live" in line:
            channel_name = line.split("@")[1].split("/")[0]
            api_key = API_KEYS[api_index]

            params = {
                "part": "snippet",
                "channelId": get_channel_id(channel_name, api_key),
                "eventType": "live",
                "type": "video",
                "key": api_key
            }

            log_message(f"🔑 使用 API 金鑰: (隱藏)")
            response = requests.get(API_URL, params=params)
            log_message(f"🔍 API 回應: {response.text}")

            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                video_id = data["items"][0]["id"]["videoId"]
                new_lines.append(f"https://www.youtube.com/watch?v={video_id}\n")
                log_message(f"✅ 解析成功: {line} → {new_lines[-1].strip()}")
            else:
                log_message(f"⚠️ API 無法取得直播 ID: {line}")
                api_index = (api_index + 1) % len(API_KEYS)  # 換下一組 API 金鑰
                new_lines.append(f"{line}\n")
        else:
            new_lines.append(f"{line}\n")

    with open(tmp_info_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    log_message("✅ 轉換完成，儲存至 tmp_inf.txt")

# 取得 YouTube 頻道 ID
def get_channel_id(channel_name, api_key):
    url = f"https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "id",
        "forUsername": channel_name,
        "key": api_key
    }
    response = requests.get(url, params=params).json()
    return response["items"][0]["id"] if "items" in response else None

# 取得 M3U8 串流連結
def get_m3u8_url(video_url):
    try:
        result = subprocess.run(
            ["yt-dlp", "-g", video_url],
            capture_output=True,
            text=True
        )
        m3u8_url = result.stdout.strip()
        return m3u8_url if m3u8_url.startswith("http") else None
    except Exception as e:
        log_message(f"❌ 解析錯誤: {e}")
        return None

# 解析 M3U8 串流
def parse_m3u8():
    with open(tmp_info_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    os.makedirs(output_dir, exist_ok=True)

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("https://www.youtube.com/watch?v="):
            m3u8_url = get_m3u8_url(line)

            if m3u8_url:
                m3u8_filename = f"y{i+1:02d}.m3u8"
                php_filename = f"y{i+1:02d}.php"

                with open(os.path.join(output_dir, m3u8_filename), "w", encoding="utf-8") as f:
                    f.write("#EXTM3U\n")
                    f.write("#EXT-X-STREAM-INF:BANDWIDTH=1280000\n")
                    f.write(m3u8_url + "\n")

                with open(os.path.join(output_dir, php_filename), "w", encoding="utf-8") as f:
                    f.write(f"<?php echo '{m3u8_url}'; ?>")

                log_message(f"✅ 生成 {m3u8_filename} 和 {php_filename}")

# SFTP 上傳檔案
def upload_files():
    log_message("🚀 啟動 SFTP 上傳程序...")
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.chdir(SFTP_REMOTE_DIR)

        for file in os.listdir(output_dir):
            local_path = os.path.join(output_dir, file)
            remote_path = os.path.join(SFTP_REMOTE_DIR, file)
            if os.path.isfile(local_path):
                sftp.put(local_path, remote_path)
                log_message(f"⬆️ 上傳 {local_path} → {remote_path}")

        sftp.close()
        transport.close()
        log_message("✅ SFTP 上傳完成！")
    except Exception as e:
        log_message(f"❌ SFTP 上傳失敗: {e}")

if __name__ == "__main__":
    convert_live_links()
    parse_m3u8()
    upload_files()
