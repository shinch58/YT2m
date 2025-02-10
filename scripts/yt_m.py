import os
import re
import json
import requests
import paramiko

# 設定檔案路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
yt_info_path = os.path.join(BASE_DIR, "../yt_info.txt")
tmp_info_path = os.path.join(BASE_DIR, "../tmp_inf.txt")
output_dir = os.path.join(BASE_DIR, "../output")
log_file = os.path.join(BASE_DIR, "../output/api_log.txt")

# 讀取 GitHub Actions 設定的 API 金鑰
API_KEYS = [os.getenv("Y_1"), os.getenv("Y_2"), os.getenv("Y_3")]

def log_message(message):
    """紀錄 API 解析日誌"""
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(message + "\n")
    print(message)

def get_channel_id(custom_url, api_key):
    """透過 YouTube API 查詢 @名稱對應的 channelId"""
    api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={custom_url}&type=channel&key={api_key}"
    
    try:
        response = requests.get(api_url)
        data = response.json()
        log_message(f"🔍 API 回應: {json.dumps(data, indent=2, ensure_ascii=False)}")

        if "items" in data and len(data["items"]) > 0:
            channel_id = data["items"][0]["snippet"]["channelId"]
            log_message(f"✅ 解析 @頻道名稱成功: {custom_url} → {channel_id}")
            return channel_id
        else:
            log_message(f"⚠️ 無法取得頻道 ID: {custom_url}")
            return None
    except Exception as e:
        log_message(f"❌ API 請求錯誤: {e}")
        return None

def get_video_id(channel_url, api_key):
    """使用 YouTube API 解析頻道的直播影片 ID"""
    custom_name = channel_url.split("/")[-2]  # 取得 @名稱
    channel_id = get_channel_id(custom_name, api_key)

    if not channel_id:
        return None  # 解析失敗

    api_url = f"https://www.googleapis.com/youtube/v3/search?part=id&channelId={channel_id}&eventType=live&type=video&key={api_key}"

    try:
        response = requests.get(api_url)
        data = response.json()
        log_message(f"🔍 API 回應: {json.dumps(data, indent=2, ensure_ascii=False)}")

        if "items" in data and len(data["items"]) > 0:
            video_id = data["items"][0]["id"]["videoId"]
            log_message(f"✅ 解析直播影片成功: {channel_url} → https://www.youtube.com/watch?v={video_id}")
            return video_id
        else:
            log_message(f"⚠️ 該頻道目前沒有直播: {channel_url}")
            return None
    except Exception as e:
        log_message(f"❌ API 請求錯誤: {e}")
        return None

def convert_yt_info():
    """將 `yt_info.txt` 內的 YouTube 頻道網址轉換為影片 ID"""
    with open(yt_info_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    converted_lines = []
    api_key_index = 0  # 輪流使用 API 金鑰

    for line in lines:
        line = line.strip()
        if line.startswith("~~") or not line:
            converted_lines.append(line)
            continue

        if "|" in line:  # 頻道資訊行
            converted_lines.append(line)
        else:  # YouTube 頻道網址
            api_key = API_KEYS[api_key_index % len(API_KEYS)]
            api_key_index += 1

            if "/@" in line:  # 解析 @頻道名稱
                log_message(f"🔍 嘗試解析 @頻道名稱: {line}")
                video_id = get_video_id(line, api_key)
                new_line = f"https://www.youtube.com/watch?v={video_id}" if video_id else line
            else:
                new_line = line  # 已經是影片網址則不變

            converted_lines.append(new_line)

    # 存入 `tmp_inf.txt`
    with open(tmp_info_path, "w", encoding="utf-8") as f:
        f.write("\n".join(converted_lines) + "\n")

    log_message("✅ 轉換完成，儲存至 tmp_inf.txt")

def parse_m3u8():
    """解析 `tmp_inf.txt` 內的 YouTube 影片網址並生成 M3U8"""
    with open(tmp_info_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    os.makedirs(output_dir, exist_ok=True)

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("https://www.youtube.com/watch?v="):
            video_url = line
            log_message(f"🔍 嘗試解析 M3U8: {video_url}")
            # 模擬解析 (這裡應該使用 yt-dlp 或其他方法)
            m3u8_url = f"https://example.com/fake_m3u8_for/{video_url}"
            m3u8_filename = f"y{i+1:02d}.m3u8"
            php_filename = f"y{i+1:02d}.php"

            with open(os.path.join(output_dir, m3u8_filename), "w", encoding="utf-8") as f:
                f.write(m3u8_url)

            with open(os.path.join(output_dir, php_filename), "w", encoding="utf-8") as f:
                f.write(f"<?php echo '{m3u8_url}'; ?>")

            log_message(f"✅ 生成 {m3u8_filename} 和 {php_filename}")

def upload_sftp():
    """將解析出的 M3U8 檔案上傳至 SFTP"""
    sftp_host = os.getenv("SFTP_HOST")
    sftp_port = int(os.getenv("SFTP_PORT", 22))
    sftp_user = os.getenv("SFTP_USER")
    sftp_password = os.getenv("SFTP_PASSWORD")
    remote_dir = os.getenv("SFTP_REMOTE_DIR")

    try:
        log_message("🚀 啟動 SFTP 上傳程序...")
        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.connect(username=sftp_user, password=sftp_password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        for file in os.listdir(output_dir):
            local_path = os.path.join(output_dir, file)
            remote_path = f"{remote_dir}/{file}"
            sftp.put(local_path, remote_path)
            log_message(f"✅ 已上傳: {file}")

        sftp.close()
        transport.close()
        log_message("✅ SFTP 上傳完成")
    except Exception as e:
        log_message(f"❌ SFTP 上傳失敗: {e}")

if __name__ == "__main__":
    log_message("🔍 開始執行 yt_m.py")
    convert_yt_info()
    parse_m3u8()
    upload_sftp()
    log_message("✅ yt_m.py 執行完成")
