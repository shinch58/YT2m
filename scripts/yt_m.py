import os
import requests
import json
import paramiko

# 設定檔案路徑
YT_INFO_PATH = "yt_info.txt"
TMP_INFO_PATH = "tmp_inf.txt"
OUTPUT_DIR = "output"

# 確保輸出目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# YouTube API 金鑰 (Y_1, Y_2, Y_3 互調用)
API_KEYS = [os.getenv("Y_1"), os.getenv("Y_2"), os.getenv("Y_3")]
api_index = 0  # 追蹤目前使用的 API 金鑰


def get_live_video_id(channel_url):
    """使用 YouTube API 解析 live 視頻 ID"""
    global api_index
    api_key = API_KEYS[api_index]
    api_index = (api_index + 1) % len(API_KEYS)  # 輪替 API 金鑰

    channel_id = channel_url.split("/")[-1]  # 提取 @channel_id
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&eventType=live&type=video&key={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "items" in data and data["items"]:
            return data["items"][0]["id"]["videoId"]  # 回傳影片 ID
    print(f"⚠️ API 無法取得直播 ID: {channel_url}")
    return None


def convert_yt_info():
    """轉換 yt_info.txt -> tmp_inf.txt（將 @channel 轉換為 video ID）"""
    with open(YT_INFO_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("~~") or not line.strip():
            new_lines.append(line)
            continue
        if "|" in line:
            new_lines.append(line)
        else:
            if "/@" in line:
                video_id = get_live_video_id(line.strip())
                if video_id:
                    line = f"https://www.youtube.com/watch?v={video_id}\n"
            new_lines.append(line)

    with open(TMP_INFO_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"✅ 轉換完成，儲存至 {TMP_INFO_PATH}")


def grab_m3u8(youtube_url):
    """使用 YouTube HLS API 解析 M3U8 連結"""
    video_id = youtube_url.split("v=")[-1]
    hls_url = f"https://manifest.googlevideo.com/api/manifest/hls_variant/id/{video_id}"
    return hls_url


def process_yt_info():
    """解析 tmp_inf.txt 並生成 M3U8 和 PHP 檔案"""
    with open(TMP_INFO_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 1
    for line in lines:
        line = line.strip()
        if line.startswith("~~") or not line:
            continue
        if "|" in line:
            channel_name = line.split("|")[0].strip()
        else:
            youtube_url = line
            print(f"🔍 嘗試解析 M3U8: {youtube_url}")
            m3u8_url = grab_m3u8(youtube_url)

            # 生成 M3U8 檔案
            m3u8_content = f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\n{m3u8_url}\n"
            output_m3u8 = os.path.join(OUTPUT_DIR, f"y{i:02d}.m3u8")
            with open(output_m3u8, "w", encoding="utf-8") as f:
                f.write(m3u8_content)

            # 生成 PHP 檔案
            php_content = f"""<?php
    header('Location: {m3u8_url}');
?>"""
            output_php = os.path.join(OUTPUT_DIR, f"y{i:02d}.php")
            with open(output_php, "w", encoding="utf-8") as f:
                f.write(php_content)

            print(f"✅ 生成 {output_m3u8} 和 {output_php}")
            i += 1


def upload_files():
    """使用 SFTP 上傳 M3U8 檔案"""
    print("🚀 啟動 SFTP 上傳程序...")
    try:
        transport = paramiko.Transport((os.getenv("SFTP_HOST"), int(os.getenv("SFTP_PORT"))))
        transport.connect(username=os.getenv("SFTP_USER"), password=os.getenv("SFTP_PASSWORD"))
        sftp = paramiko.SFTPClient.from_transport(transport)

        # 上傳檔案
        for file in os.listdir(OUTPUT_DIR):
            local_path = os.path.join(OUTPUT_DIR, file)
            remote_path = os.path.join(os.getenv("SFTP_REMOTE_DIR"), file)
            if os.path.isfile(local_path):
                sftp.put(local_path, remote_path)

        sftp.close()
        transport.close()
        print("✅ SFTP 上傳完成！")

    except Exception as e:
        print(f"❌ SFTP 上傳失敗: {e}")


if __name__ == "__main__":
    convert_yt_info()
    process_yt_info()
    upload_files()
