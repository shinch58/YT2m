import os
import logging
import subprocess
import paramiko
import time
import json
import requests
from urllib.parse import urlparse

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
output_dir = os.path.join(root_dir, 'output')
log_dir = os.path.join(root_dir, 'log')
cookies_path = os.path.join(root_dir, 'cookies.txt')

os.makedirs(output_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

print("專案根目錄: " + root_dir)
print("腳本目錄: " + script_dir)

logging.basicConfig(filename=os.path.join(log_dir, 'log.txt'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

YOUTUBE_API_KEY = os.getenv('YT_API_KEY', '')
cookies_content = os.getenv('YT_COOKIES', '')

if cookies_content:
    with open(cookies_path, 'w', encoding='utf-8') as f:
        f.write(cookies_content)
    print("已載入 Cookies")

SF_L = os.getenv('SF_L', '')
if not SF_L:
    print("缺少 SF_L")
    exit(1)

parsed_url = urlparse(SF_L)
SFTP_HOST = parsed_url.hostname
SFTP_PORT = parsed_url.port or 22
SFTP_USER = parsed_url.username
SFTP_PASSWORD = parsed_url.password
SFTP_REMOTE_DIR = parsed_url.path or "/"

print("配置完成")

USE_API_CHECK = False
FORCE_PARSE = False
GEO_BYPASS = True
GEO_BYPASS_COUNTRY = "TW"
yt_info_path = os.path.join(root_dir, 'yt_info.txt')

def extract_id_from_url(url):
    if 'v=' in url:
        return url.split('v=')[-1].split('&')[0], 'video'
    elif '/channel/' in url:
        return url.split('/channel/')[-1].split('/')[0], 'channel'
    return '', 'unknown'

def check_live_with_api(youtube_url):
    if not USE_API_CHECK or not YOUTUBE_API_KEY:
        return True, youtube_url
    video_id, id_type = extract_id_from_url(youtube_url)
    try:
        if id_type == 'video':
            api_url = "https://www.googleapis.com/youtube/v3/videos"
            params = {'part': 'snippet,liveStreamingDetails', 'id': video_id, 'key': YOUTUBE_API_KEY}
            response = requests.get(api_url, params=params, timeout=10)
            data = response.json()
            if 'items' in data and data['items']:
                snippet = data['items'][0].get('snippet', {})
                if snippet.get('liveBroadcastContent') == 'live':
                    print("API確認直播")
                    return True, youtube_url
        elif id_type == 'channel':
            api_url = "https://www.googleapis.com/youtube/v3/search"
            params = {'part': 'snippet', 'channelId': video_id, 'eventType': 'live', 'type': 'video', 'key': YOUTUBE_API_KEY}
            response = requests.get(api_url, params=params, timeout=10)
            data = response.json()
            if 'items' in data and data['items']:
                live_video_id = data['items'][0]['id']['videoId']
                live_url = "https://www.youtube.com/watch?v=" + live_video_id
                print("API找到直播")
                return True, live_url
    except:
        pass
    return True, youtube_url

def check_if_live_with_ytdlp(youtube_url):
    cmd = ["yt-dlp", "--dump-json", "--playlist-items", "1", "--no-warnings"]
    if os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])
    if GEO_BYPASS:
        cmd.append("--geo-bypass")
        cmd.extend(["--geo-bypass-country", GEO_BYPASS_COUNTRY])
    cmd.append(youtube_url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        info = json.loads(result.stdout)
        return info.get('is_live', False) and info.get('live_status', '') == 'is_live'
    except:
        return False

def grab(youtube_url):
    is_live, corrected_url = check_live_with_api(youtube_url)
    if not is_live and not FORCE_PARSE:
        if not check_if_live_with_ytdlp(youtube_url):
            return "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"
    youtube_url = corrected_url
    strategies = [
        {"name": "Android", "args": ["--extractor-args", "youtube:player_client=android"], "use_cookies": True},
        {"name": "AndroidE", "args": ["--extractor-args", "youtube:player_client=android_embedded"], "use_cookies": True},
        {"name": "iOS", "args": ["--extractor-args", "youtube:player_client=ios"], "use_cookies": True},
        {"name": "Web", "args": ["--extractor-args", "youtube:player_client=web_embedded"], "use_cookies": True}
    ]
    for strategy in strategies:
        print("策略: " + strategy['name'])
        cmd = ["yt-dlp", "-f", "best[height<=720]/best", "-g", "--no-check-certificate"]
        cmd.extend(strategy["args"])
        if strategy["use_cookies"] and os.path.exists(cookies_path):
            cmd.extend(["--cookies", cookies_path])
        if GEO_BYPASS:
            cmd.append("--geo-bypass")
            cmd.extend(["--geo-bypass-country", GEO_BYPASS_COUNTRY])
        cmd.append(youtube_url)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=45)
            m3u8_url = result.stdout.strip()
            if m3u8_url and ("googlevideo.com" in m3u8_url or "m3u8" in m3u8_url.lower()):
                print("解析成功")
                return m3u8_url
        except:
            pass
        time.sleep(1)
    return "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"

def process_yt_info():
    if not os.path.exists(yt_info_path):
        print("未找到yt_info.txt")
        return
    try:
        with open(yt_info_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        i = 1
        entries = lines[2:]
        j = 0
        while j < len(entries) - 1:
            info_line = entries[j]
            youtube_url = entries[j + 1]
            channel_name = info_line.split("|")[0].strip() or ("Channel%02d" % i)
            print("頻道 " + str(i) + ": " + channel_name)
            print("URL: " + youtube_url)
            m3u8_url = grab(youtube_url)
            output_m3u8 = os.path.join(output_dir, "y%02d.m3u8" % i)
            with open(output_m3u8, "w", encoding="utf-8") as f:
                f.write("#EXTM3U
")
                f.write("#EXT-X-STREAM-INF:BANDWIDTH=1280000
")
                f.write(m3u8_url)
                f.write("
")
            output_php = os.path.join(output_dir, "y%02d.php" % i)
            with open(output_php, "w", encoding="utf-8") as f:
                f.write("<?php
")
                f.write("header('Location: ")
                f.write(m3u8_url)
                f.write("');
")
                f.write("?>")
            print("完成 y%02d" % i)
            i += 1
            j += 2
            time.sleep(2)
    except Exception as e:
        print("處理失敗: " + str(e))

def upload_files():
    print("SFTP上傳")
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        print("SFTP連線成功")
        try:
            sftp.chdir(SFTP_REMOTE_DIR)
        except:
            sftp.mkdir(SFTP_REMOTE_DIR)
            sftp.chdir(SFTP_REMOTE_DIR)
        count = 0
        for file in os.listdir(output_dir):
            local_path = os.path.join(output_dir, file)
            if os.path.isfile(local_path):
                remote_path = os.path.join(SFTP_REMOTE_DIR, file)
                print("上傳 " + file)
                sftp.put(local_path, remote_path)
                count += 1
        sftp.close()
        transport.close()
        print("上傳完成: " + str(count))
    except Exception as e:
        print("SFTP失敗: " + str(e))

if __name__ == "__main__":
    print("YouTube M3U8解析器")
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
        print("yt-dlp: " + result.stdout.strip())
    except:
        print("無yt-dlp")
        exit(1)
    print("開始執行")
    start_time = time.time()
    process_yt_info()
    upload_files()
    print("完成: " + str(round(time.time() - start_time, 2)) + "秒")
