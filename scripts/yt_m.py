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

logging.basicConfig(
    filename=os.path.join(log_dir, 'log.txt'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

YOUTUBE_API_KEY = os.getenv('YT_API_KEY', '')
cookies_content = os.getenv('YT_COOKIES', '')

if cookies_content:
    with open(cookies_path, 'w', encoding='utf-8') as f:
        f.write(cookies_content)
    print("已載入 Cookies: " + cookies_path)
else:
    print("無 YT_COOKIES 環境變數")

SF_L = os.getenv('SF_L', '')
if not SF_L:
    print("缺少 SF_L 環境變數")
    logging.error("缺少 SF_L 環境變數")
    exit(1)

parsed_url = urlparse(SF_L)
SFTP_HOST = parsed_url.hostname
SFTP_PORT = parsed_url.port or 22
SFTP_USER = parsed_url.username
SFTP_PASSWORD = parsed_url.password
SFTP_REMOTE_DIR = parsed_url.path or "/"

print("配置載入完成 SFTP: " + SFTP_HOST + ":" + str(SFTP_PORT))

USE_API_CHECK = False
FORCE_PARSE = False
SKIP_NON_LIVE = True
PROXY = None
GEO_BYPASS = True
GEO_BYPASS_COUNTRY = "TW"
USE_IPV6 = False

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
            params = {
                'part': 'snippet,liveStreamingDetails',
                'id': video_id,
                'key': YOUTUBE_API_KEY
            }
            response = requests.get(api_url, params=params, timeout=10)
            data = response.json()
            
            if 'items' in data and data['items']:
                snippet = data['items'][0].get('snippet', {})
                is_live = snippet.get('liveBroadcastContent') == 'live'
                if is_live:
                    print("API 確認直播中")
                    return True, youtube_url
        
        elif id_type == 'channel':
            api_url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'channelId': video_id,
                'eventType': 'live',
                'type': 'video',
                'key': YOUTUBE_API_KEY
            }
            response = requests.get(api_url, params=params, timeout=10)
            data = response.json()
            
            if 'items' in data and data['items']:
                live_video_id = data['items'][0]['id']['videoId']
                live_url = "https://www.youtube.com/watch?v=" + live_video_id
                print("API 找到直播: " + live_video_id)
                return True, live_url
                
    except Exception as e:
        print("API 失敗: " + str(e))
    
    return True, youtube_url

def check_if_live_with_ytdlp(youtube_url):
    cmd = ["yt-dlp", "--dump-json", "--playlist-items", "1", "--no-warnings"]
    
    if os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])
    
    if GEO_BYPASS:
        cmd.append("--geo-bypass")
        if GEO_BYPASS_COUNTRY:
            cmd.extend(["--geo-bypass-country", GEO_BYPASS_COUNTRY])
    
    cmd.append(youtube_url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        info = json.loads(result.stdout)
        is_live = info.get('is_live', False)
        live_status = info.get('live_status', 'not_live')
        return is_live and live_status == 'is_live'
    except:
        return False

def grab(youtube_url):
    is_live, corrected_url = check_live_with_api(youtube_url)
    
    if not is_live and not FORCE_PARSE:
        if not check_if_live_with_ytdlp(youtube_url):
            logging.warning("跳過非直播: " + youtube_url)
            return "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"
    
    youtube_url = corrected_url
    
    strategies = [
        {"name": "Android", "args": ["--extractor-args", "youtube:player_client=android"], "use_cookies": True},
        {"name": "AndroidE", "args": ["--extractor-args", "youtube:player_client=android_embedded"], "use_cookies": True},
        {"name": "iOS", "args": ["--extractor-args", "youtube:player_client=ios"], "use_cookies": True},
        {"name": "Web", "args": ["--extractor-args", "youtube:player_client=web_embedded"], "use_cookies": True},
    ]
    
    for strategy in strategies:
        print("策略: " + strategy['name'])
        
        cmd = [
            "yt-dlp", "-f", "best[height<=720]/best", "-g",
            "--no-check-certificate"
        ]
        cmd.extend(strategy["args"])
        
        if strategy["use_cookies"] and os.path.exists(cookies_path):
            cmd.extend(["--cookies", cookies_path])
        
        if GEO_BYPASS:
            cmd.append("--geo-bypass")
            if GEO_BYPASS_COUNTRY:
                cmd.extend(["--geo-bypass-country", GEO_BYPASS_COUNTRY])
        
        cmd.append(youtube_url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=45)
            m3u8_url = result.stdout.strip()
            
            if m3u8_url and ("googlevideo.com" in m3u8_url or "m3u8" in m3u8_url.lower()):
                print("解析成功")
                logging.info("策略成功: " + strategy['name'])
                return m3u8_url
                
        except Exception as e:
            print("策略失敗")
        
        time.sleep(1)
    
    logging.error("所有策略失敗")
    return "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"

def process_yt_info():
    if not os.path.exists(yt_info_path):
        print("未找到 yt_info.txt")
        return
        
    try:
        with open(yt_info_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        logging.info("讀取 yt_info.txt 成功")

        i = 1
        entries = lines[2:]
        for j in range(0, len(entries), 2):
            if j + 1 >= len(entries):
                continue
            info_line = entries[j]
            youtube_url = entries[j + 1]
            channel_name = info_line.split("|")[0].strip() or "Channel%02d" % i

            print("處理頻道 " + str(i) + ": " + channel_name)
            print("YouTube URL: " + youtube_url)
            
            m3u8_url = grab(youtube_url)

            output_m3u8 = os.path.join(output_dir, "y%02d.m3u8" % i)
            with open(output_m3u8, "w", encoding="utf-8") as f:
                f.write("#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=1280000
" + m3u8_url + "
")
            logging.info("生成 m3u8: y%02d.m3u8" % i)

            output_php = os.path.join(output_dir, "y%02d.php" % i)
            with open(output_php, "w", encoding="utf-8") as f:
                f.write("<?php
header('Location: " + m3u8_url + "');
?>")
            logging.info("生成 php: y%02d.php" % i)

            print("完成: y%02d.m3u8 和 y%02d.php" % (i, i))
            i += 1
            time.sleep(2)

    except Exception as e:
        logging.error("處理 yt_info.txt 失敗: " + str(e))
        print("處理失敗: " + str(e))

def upload_files():
    print("啟動 SFTP 上傳")
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        print("SFTP 連線成功: " + SFTP_HOST)

        try:
            sftp.chdir(SFTP_REMOTE_DIR)
        except IOError:
            print("創建遠端目錄")
            sftp.mkdir(SFTP_REMOTE_DIR)
            sftp.chdir(SFTP_REMOTE_DIR)

        uploaded_count = 0
        for file in os.listdir(output_dir):
            local_path = os.path.join(output_dir, file)
            if os.path.isfile(local_path):
                remote_path = os.path.join(SFTP_REMOTE_DIR, file)
                print("上傳 " + file)
                sftp.put(local_path, remote_path)
                uploaded_count += 1

        sftp.close()
        transport.close()
        print("上傳完成，共 " + str(uploaded_count) + " 個檔案")
        logging.info("SFTP 上傳完成，共 " + str(uploaded_count) + " 個檔案")
        
    except Exception as e:
        print("SFTP 上傳失敗: " + str(e))
        logging.error("SFTP 上傳失敗: " + str(e))

if __name__ == "__main__":
    print("YouTube 直播 M3U8 解析器")
    
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
        print("yt-dlp 版本: " + result.stdout.strip())
    except:
        print("未安裝 yt-dlp")
        exit(1)
    
    print("API Key: " + ("有" if YOUTUBE_API_KEY else "無"))
    print("Cookies: " + ("有" if os.path.exists(cookies_path) else "無"))
    print("SFTP: 有")
    
    start_time = time.time()
    process_yt_info()
    upload_files()
    
    elapsed_time = time.time() - start_time
    print("總執行時間: " + str(round(elapsed_time, 2)) + " 秒")
    logging.info("執行完成，總時間: " + str(elapsed_time) + " 秒")
