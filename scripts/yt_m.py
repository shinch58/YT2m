import os
import re
import httpx
import paramiko
import json
import subprocess
from urllib.parse import urlparse

yt_info_path = "yt_info.txt"
output_dir = "output"
cookies_path = os.path.join(os.getcwd(), "cookies.txt")
API_KEY = os.getenv("YT_API_KEY", "")
if not API_KEY:
    print("❌ 環境變數 YT_API_KEY 未設置，改用 HTML 解析")

SF_L = os.getenv("SF_L", "")
if not SF_L:
    print("❌ 環境變數 SF_L 未設置")
    exit(1)

parsed_url = urlparse(SF_L)
SFTP_HOST = parsed_url.hostname
SFTP_PORT = parsed_url.port if parsed_url.port else 22
SFTP_USER = parsed_url.username
SFTP_PASSWORD = parsed_url.password
SFTP_REMOTE_DIR = parsed_url.path if parsed_url.path else "/"

os.makedirs(output_dir, exist_ok=True)

def get_channel_id(youtube_url):
    handle = youtube_url.split("/")[-2] if "/@" in youtube_url else None
    if API_KEY and handle:
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=id&forHandle={handle}&key={API_KEY}"
            with httpx.Client(timeout=15) as client:
                res = client.get(url)
                res.raise_for_status()
                data = res.json()
                if data.get("items"):
                    print(f"✅ API 找到頻道 ID: {data['items'][0]['id']}")
                    return data["items"][0]["id"]
                print(f"⚠️ API 無法找到 {handle} 的頻道 ID，嘗試 HTML 解析")
        except Exception as e:
            print(f"⚠️ API 獲取頻道 ID 失敗: {e}")

    try:
        with httpx.Client(http2=True, follow_redirects=True, timeout=15) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "text/html",
                "Accept-Language": "en-US,en;q=0.5",
            }
            res = client.get(youtube_url, headers=headers)
            html = res.text
            patterns = [
                r'"channelId":"(UC[^"]+)"',
                r'<meta itemprop="channelId" content="(UC[^"]+)"',
                r'"externalId":"(UC[^"]+)"'
            ]
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    print(f"✅ HTML 找到頻道 ID: {match.group(1)}")
                    return match.group(1)
            print(f"⚠️ 無法從 {youtube_url} 提取頻道 ID")
            return None
    except Exception as e:
        print(f"⚠️ HTML 提取頻道 ID 失敗: {e}")
        return None

def get_live_video_id(channel_id):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&eventType=live&type=video&key={API_KEY}"
        with httpx.Client(timeout=15) as client:
            res = client.get(url)
            res.raise_for_status()
            data = res.json()
            if data.get("items"):
                video_id = data["items"][0]["id"]["videoId"]
                print(f"✅ 找到直播 videoId: {video_id}")
                return f"https://www.youtube.com/watch?v={video_id}"
            print(f"⚠️ 頻道 {channel_id} 目前無直播 (API 返回空結果)")
            return None
    except Exception as e:
        print(f"⚠️ API 請求失敗: {e}")
        return None

def grab_by_ytdlp(youtube_url):
    """使用 yt-dlp 嘗試抓取 720p 以下的 m3u8 串流"""

    yt_header_auth = os.getenv("YT_HEADER_AUTH", "")
    headers = []
    if yt_header_auth:
        try:
            key, value = yt_header_auth.split(":", 1)
            headers = ["--add-header", f"{key.strip()}:{value.strip()}"]
            print("🛡️ 使用 Authorization header 傳入 yt-dlp")
        except Exception as e:
            print(f"⚠️ YT_HEADER_AUTH 格式錯誤: {e}")

    if not headers and not os.path.exists(cookies_path):
        print("⚠️ 未設置 Authorization header，也找不到 cookies.txt，yt-dlp 可能會失敗")

    cmd = [
        "yt-dlp",
        "-f", "best[ext=m3u8][height<=720]",
        *headers
    ]

    if not headers:
        cmd += ["--cookies", cookies_path]

    cmd.append(youtube_url)

    try:
        print("⚙️ 執行 yt-dlp:", " ".join(cmd))
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        if result.returncode == 0:
            m3u8_url = result.stdout.strip()
            if ".m3u8" in m3u8_url:
                print(f"✅ yt-dlp 成功取得 .m3u8: {m3u8_url}")
                return m3u8_url
            else:
                print("⚠️ yt-dlp 回傳非 .m3u8 連結")
        else:
            print(f"⚠️ yt-dlp 解析失敗: {result.stderr}")
    except Exception as e:
        print(f"⚠️ 執行 yt-dlp 發生錯誤: {e}")
    return None

def grab(youtube_url):
    with httpx.Client(http2=True, follow_redirects=True, timeout=15) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html",
            "Accept-Language": "en-US,en;q=0.5",
        }

        cookies = {}
        if os.path.exists(cookies_path):
            try:
                with open(cookies_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.startswith('#') and '\t' in line:
                            parts = line.strip().split('\t')
                            if len(parts) >= 6:
                                cookies[parts[5]] = parts[6]
            except Exception as e:
                print(f"⚠️ Cookie 讀取失敗: {e}")

        try:
            res = client.get(youtube_url, headers=headers, cookies=cookies)
            html = res.text

            if 'noindex' in html:
                print(f"⚠️ 頻道 {youtube_url} 目前未開啟直播")
                return None

            player_response_match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', html, re.DOTALL)
            if player_response_match:
                player_response = json.loads(player_response_match.group(1))
                streaming_data = player_response.get("streamingData", {})
                hls_formats = streaming_data.get("hlsManifestUrl", "")
                if hls_formats:
                    print(f"✅ 找到 .m3u8 連結: {hls_formats}")
                    return hls_formats

            m3u8_matches = re.findall(r'(https://[^"]+\.m3u8[^"]*)', html)
            for url in m3u8_matches:
                if "googlevideo.com" in url:
                    print(f"✅ 找到 .m3u8 連結: {url}")
                    return url

            print("⚠️ 未找到有效的 .m3u8 連結，嘗試 yt-dlp 備援解析")
            return grab_by_ytdlp(youtube_url) or "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"

        except Exception as e:
            print(f"⚠️ 抓取頁面失敗: {e}")
            return grab_by_ytdlp(youtube_url) or "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"

def process_yt_info():
    with open(yt_info_path, "r", encoding="utf-8") as f:
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

            channel_id = get_channel_id(youtube_url)
            if not channel_id:
                print(f"⚠️ 跳過 {youtube_url}，無法獲取頻道 ID")
                continue

            if API_KEY:
                live_url = get_live_video_id(channel_id)
                if not live_url:
                    print(f"⚠️ 頻道 {youtube_url} 無直播，跳過")
                    continue
            else:
                live_url = youtube_url

            m3u8_url = grab(live_url)
            if m3u8_url is None:
                continue

            m3u8_content = f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\n{m3u8_url}\n"
            output_m3u8 = os.path.join(output_dir, f"y{i:02d}.m3u8")
            with open(output_m3u8, "w", encoding="utf-8") as f:
                f.write(m3u8_content)

            php_content = f"""<?php
header('Location: {m3u8_url}');
?>"""
            output_php = os.path.join(output_dir, f"y{i:02d}.php")
            with open(output_php, "w", encoding="utf-8") as f:
                f.write(php_content)

            print(f"✅ 生成 {output_m3u8} 和 {output_php}")
            i += 1

def upload_files():
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
    process_yt_info()
    upload_files()
