import os
import requests
import re
import paramiko

# 設定檔案路徑
yt_info_path = "yt_info.txt"   # 原始 YouTube 頻道清單
tmp_info_path = "tmp_inf.txt"  # 轉換後的清單
output_dir = "output"          # M3U8 生成目錄

# SFTP 設定（從 GitHub Actions 變數讀取）
SFTP_HOST = os.getenv("SFTP_HOST", "your_sftp_server.com")
SFTP_PORT = int(os.getenv("SFTP_PORT", 22))
SFTP_USER = os.getenv("SFTP_USER", "your_username")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD", "your_password")
SFTP_REMOTE_DIR = os.getenv("SFTP_REMOTE_DIR", "/remote/path/")

# 確保輸出目錄存在
os.makedirs(output_dir, exist_ok=True)

def get_watch_url(youtube_url):
    """將 @handle/live 轉換為 /watch?v= 連結"""
    match = re.search(r"youtube\.com/@([\w-]+)/live", youtube_url)
    if not match:
        return youtube_url  # 不是 @handle/live 格式，直接返回

    handle = match.group(1)
    channel_url = f"https://www.youtube.com/@{handle}"

    # 嘗試獲取頻道頁面 HTML
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(channel_url, headers=headers)

    # 解析直播影片 ID
    match = re.search(r'"videoId":"([\w-]+)"', response.text)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"

    return youtube_url  # 如果找不到 videoId，則返回原網址

def convert_live_links():
    """轉換 yt_info.txt 內的 @handle/live 連結，存入 tmp_inf.txt"""
    with open(yt_info_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith("http") and "youtube.com" in line:
            converted_url = get_watch_url(line)
            new_lines.append(converted_url + "\n")
        else:
            new_lines.append(line + "\n")

    with open(tmp_info_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("✅ 轉換完成，儲存至 tmp_inf.txt")

def grab(youtube_url):
    """解析 YouTube M3U8 連結（使用備用 M3U8）"""
    print(f"🔍 嘗試解析 M3U8: {youtube_url}")
    
    # 這裡可以改成 YouTube API 解析 M3U8
    # 目前使用預設的無訊號 M3U8
    return "https://raw.githubusercontent.com/shinch58/YT2m/main/assets/no_s.m3u8"

def process_yt_info():
    """解析 tmp_inf.txt 並生成 M3U8 和 PHP 檔案"""
    with open(tmp_info_path, "r", encoding="utf-8") as f:
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
    convert_live_links()  # 轉換 @handle/live 連結
    process_yt_info()  # 解析 tmp_inf.txt
    upload_files()  # 上傳到 SFTP（可選）
