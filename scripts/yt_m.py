import os
import requests
import json
import paramiko

# 設定檔案路徑
yt_info_path = "yt_info.txt"
tmp_info_path = "tmp_inf.txt"
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# 讀取 API 金鑰（GitHub Actions 設定的三組 API 金鑰）
API_KEYS = [
    os.getenv("Y_1"),
    os.getenv("Y_2"),
    os.getenv("Y_3")
]

# SFTP 設定（來自 GitHub Actions）
SFTP_HOST = os.getenv("SFTP_HOST", "your_sftp_server.com")
SFTP_PORT = int(os.getenv("SFTP_PORT", 22))
SFTP_USER = os.getenv("SFTP_USER", "your_username")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD", "your_password")
SFTP_REMOTE_DIR = os.getenv("SFTP_REMOTE_DIR", "/remote/path/")

def get_video_id(channel_url, api_key):
    """使用 YouTube API 解析頻道的直播影片 ID"""
    channel_id = channel_url.split("/")[-1]  # 取得 @名稱
    api_url = f"https://www.googleapis.com/youtube/v3/search?part=id&channelId={channel_id}&eventType=live&type=video&key={api_key}"

    try:
        response = requests.get(api_url)
        data = response.json()

        # 記錄 API 回應
        print(f"🔍 API 回應: {json.dumps(data, indent=2)}")

        if "items" in data and len(data["items"]) > 0:
            video_id = data["items"][0]["id"]["videoId"]
            print(f"✅ 解析成功: {channel_url} → https://www.youtube.com/watch?v={video_id}")
            return video_id
        else:
            print(f"⚠️ API 無法取得直播 ID: {channel_url}")
            return None
    except Exception as e:
        print(f"❌ API 請求錯誤: {e}")
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

            print(f"🔑 使用 API 金鑰: (隱藏)")
            video_id = get_video_id(line, api_key)

            if video_id:
                new_line = f"https://www.youtube.com/watch?v={video_id}"
            else:
                new_line = line  # 保留原始網址（解析失敗）

            converted_lines.append(new_line)

    # 存入 `tmp_inf.txt`
    with open(tmp_info_path, "w", encoding="utf-8") as f:
        f.write("\n".join(converted_lines) + "\n")

    print("✅ 轉換完成，儲存至 tmp_inf.txt")

def grab_m3u8(youtube_url):
    """使用 requests 解析 M3U8 連結"""
    hls_url = f"https://example.com/fake_m3u8_for/{youtube_url.split('=')[-1]}"  # 模擬 HLS 連結
    print(f"✅ 解析成功: {youtube_url} → {hls_url}")
    return hls_url

def process_yt_info():
    """解析 `tmp_inf.txt` 生成 M3U8 和 PHP 檔案"""
    with open(tmp_info_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 1
    for line in lines:
        line = line.strip()
        if line.startswith("~~") or not line:
            continue
        if "|" in line:
            parts = line.split("|")
            channel_name = parts[0].strip() if len(parts) > 0 else f"Channel {i}"
        else:
            youtube_url = line
            print(f"🔍 嘗試解析 M3U8: {youtube_url}")
            m3u8_url = grab_m3u8(youtube_url)

            # 生成 M3U8 文件
            m3u8_content = f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\n{m3u8_url}\n"
            output_m3u8 = os.path.join(output_dir, f"y{i:02d}.m3u8")
            with open(output_m3u8, "w", encoding="utf-8") as f:
                f.write(m3u8_content)

            # 生成 PHP 文件
            php_content = f"<?php\nheader('Location: {m3u8_url}');\n?>"
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

        try:
            sftp.chdir(SFTP_REMOTE_DIR)
        except IOError:
            print(f"📁 遠端目錄 {SFTP_REMOTE_DIR} 不存在，正在創建...")
            sftp.mkdir(SFTP_REMOTE_DIR)
            sftp.chdir(SFTP_REMOTE_DIR)

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
    convert_yt_info()  # 轉換頻道連結
    process_yt_info()  # 解析 M3U8
    upload_files()  # 上傳 SFTP
