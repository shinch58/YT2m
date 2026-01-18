import os
import logging
import subprocess
import paramiko
import time
import json
import requests
from urllib.parse import urlparse

# ===== 專案資料夾路徑 =====
script_dir = os.path.dirname(os.path.abspath(__file__))  # scripts 目錄
root_dir = os.path.dirname(script_dir)  # 專案根目錄

output_dir = os.path.join(root_dir, 'output')
log_dir = os.path.join(root_dir, 'log')
cookies_path = os.path.join(root_dir, 'cookies.txt')  # 臨時 cookies 檔案

os.makedirs(output_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

print(f"📁 專案根目錄: {root_dir}")
print(f"📁 腳本目錄: {script_dir}")

# ===== 日誌設置 =====
logging.basicConfig(
    filename=os.path.join(log_dir, 'log.txt'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ===== 從環境變數載入配置 =====
YOUTUBE_API_KEY = os.getenv('YT_API_KEY', '')
cookies_content = os.getenv('YT_COOKIES', '')

# 寫入臨時 cookies.txt（支援多行）
if cookies_content:
    with open(cookies_path, 'w', encoding='utf-8') as f:
        f.write(cookies_content)
    print(f"✅ 已從環境變數載入 Cookies: {cookies_path}")
else:
    print("⚠️ 未找到 YT_COOKIES 環境變數")

SF_L = os.getenv('SF_L', '')
if not SF_L:
    print("❌ 缺少 SF_L 環境變數，請在 GitHub Secrets 設定")
    logging.error("缺少 SF_L 環境變數")
    exit(1)

parsed_url = urlparse(SF_L)
SFTP_HOST = parsed_url.hostname
SFTP_PORT = parsed_url.port or 22
SFTP_USER = parsed_url.username
SFTP_PASSWORD = parsed_url.password
SFTP_REMOTE_DIR = parsed_url.path or "/"

print(f"✅ 配置載入完成 (SFTP: {SFTP_HOST}:{SFTP_PORT})")

# ===== 解析策略設置 =====
USE_API_CHECK = False  # 是否使用 API 檢查
FORCE_PARSE = False  # 強制解析
SKIP_NON_LIVE = True  # 跳過非直播內容

# ===== 地區繞過設置 =====
PROXY = None
GEO_BYPASS = True
GEO_BYPASS_COUNTRY = "TW"
USE_EMBED_URL = True
IGNORE_IP_RANGE = True
USE_IPV6 = False

# ===== yt_info.txt 路徑 =====
yt_info_path = os.path.join(root_dir, 'yt_info.txt')

# ===== 從頻道 URL 找到直播 URL =====
def find_live_url(channel_url):
    """嘗試從頻道 URL 找到正在直播的影片 URL"""
    print(f"🔍 嘗試從頻道找到直播...")
    
    live_urls = []
    
    if '/channel/' in channel_url or '/@' in channel_url or '/c/' in channel_url:
        base_url = channel_url.rstrip('/')
        live_urls.append(f"{base_url}/live")
    
    if '/channel/' in channel_url:
        channel_id = channel_url.split('/channel/')[-1].split('/')[0]
        live_urls.append(f"https://www.youtube.com/channel/{channel_id}/streams")
    
    for test_url in live_urls:
        print(f"   測試: {test_url}")
        cmd = ["yt-dlp", "--dump-json", "--playlist-items", "1"]
        
        if os.path.exists(cookies_path):
            cmd.extend(["--cookies", cookies_path])
        
        cmd.append(test_url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=True)
            info = json.loads(result.stdout)
            
            is_live = info.get('is_live', False)
            live_status = info.get('live_status', 'not_live')
            video_id = info.get('id', '')
            
            if is_live or live_status == 'is_live':
                live_video_url = f"https://www.youtube.com/watch?v={video_id}"
                print(f"   ✅ 找到直播: {live_video_url}")
                logging.info(f"找到直播 URL: {channel_url} → {live_video_url}")
                return live_video_url, True
            else:
                print(f"   ⚠️ 非直播狀態: {live_status}")
                
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ 檢查超時")
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"   ❌ 檢查失敗")
    
    print(f"   ℹ️ 未找到正在直播的影片")
    return channel_url, False

# ===== 使用 YouTube API 檢查直播狀態 =====
def check_live_with_api(youtube_url):
    """使用 YouTube Data API v3 檢查頻道是否正在直播"""
    if not USE_API_CHECK or not YOUTUBE_API_KEY:
        return True, youtube_url
        
    # extract_id_from_url 函數需自行實作或移除，此處假設存在
    video_id = youtube_url.split('v=')[-1].split('&')[0] if 'v=' in youtube_url else ''
    id_type = 'video' if video_id else 'channel'
    
    try:
        if id_type == 'video':
            api_url = f"https://www.googleapis.com/youtube/v3/videos"
            params = {
                'part': 'snippet,liveStreamingDetails',
                'id': video_id,
                'key': YOUTUBE_API_KEY
            }
            response = requests.get(api_url, params=params, timeout=10)
            data = response.json()
            
            if 'items' in data and len(data['items']) > 0:
                item = data['items'][0]
                snippet = item.get('snippet', {})
                is_live = snippet.get('liveBroadcastContent') == 'live'
                
                if is_live:
                    print(f"✅ API 確認為直播中")
                    logging.info(f"API 確認直播: {youtube_url}")
                    return True, youtube_url
                else:
                    print(f"⚠️ API 顯示非直播狀態")
                    return False, youtube_url
        
        elif id_type == 'channel':
            api_url = f"https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'channelId': video_id,
                'eventType': 'live',
                'type': 'video',
                'key': YOUTUBE_API_KEY
            }
            response = requests.get(api_url, params=params, timeout=10)
            data = response.json()
            
            if 'items' in data and len(data['items']) > 0:
                live_video_id = data['items'][0]['id']['videoId']
                live_url = f"https://www.youtube.com/watch?v={live_video_id}"
                print(f"✅ API 找到直播影片: {live_video_id}")
                return True, live_url
                
    except Exception as e:
        print(f"⚠️ API 請求失敗: {e}")
        logging.error(f"API 請求失敗: {youtube_url} → {e}")
    
    return True, youtube_url

# ===== 使用 yt-dlp 驗證直播狀態 =====
def check_if_live_with_ytdlp(youtube_url):
    """使用 yt-dlp 檢查是否為直播"""
    cmd = ["yt-dlp", "--dump-json", "--playlist-items", "1", "--no-warnings"]
    
    if os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])
    
    if PROXY:
        cmd.extend(["--proxy", PROXY])
    
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
        
        if is_live and live_status == 'is_live':
            print(f"   ✅ 確認為直播中")
            return True
        return False
            
    except Exception as e:
        print(f"   ❌ 檢查失敗")
        return False

# ===== yt-dlp 解析 m3u8 =====
def grab(youtube_url, max_retries=3):
    """使用 yt-dlp 取得直播 m3u8 URL"""
    
    is_live, corrected_url = check_live_with_api(youtube_url)
    
    if not is_live and not FORCE_PARSE:
        if not check_if_live_with_ytdlp(youtube_url):
            logging.warning(f"跳過非直播 URL: {youtube_url}")
            return "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"
    
    youtube_url = corrected_url
    
    strategies = [
        {"name": "Android + Cookies", "args": ["--extractor-args", "youtube:player_client=android"], "use_cookies": True, "use_geo_bypass": True},
        {"name": "Android Embedded", "args": ["--extractor-args", "youtube:player_client=android_embedded"], "use_cookies": True, "use_geo_bypass": True},
        {"name": "iOS", "args": ["--extractor-args", "youtube:player_client=ios"], "use_cookies": True, "use_geo_bypass": True},
        {"name": "Web Embed", "args": ["--extractor-args", "youtube:player_client=web_embedded"], "use_cookies": True, "use_geo_bypass": True},
        {"name": "TV Client", "args": ["--extractor-args", "youtube:player_client=tv_embedded"], "use_cookies": True, "use_geo_bypass": True},
    ]
    
    for strategy in strategies:
        print(f"
🔧 策略: {strategy['name']}")
        
        cmd = [
            "yt-dlp", "-f", "best[height<=720]/best", "-g",
            "--no-check-certificate"
        ]
        cmd.extend(strategy["args"])
        
        if strategy["use_cookies"] and os.path.exists(cookies_path):
            cmd.extend(["--cookies", cookies_path])
        
        if strategy.get("use_geo_bypass", False) and GEO_BYPASS:
            cmd.append("--geo-bypass")
            if GEO_BYPASS_COUNTRY:
                cmd.extend(["--geo-bypass-country", GEO_BYPASS_COUNTRY])
        
        if PROXY:
            cmd.extend(["--proxy", PROXY])
        
        cmd.append(youtube_url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=45)
            m3u8_url = result.stdout.strip()
            
            if m3u8_url and ("googlevideo.com" in m3u8_url or "m3u8" in m3u8_url.lower()):
                print(f"   ✅ 解析成功！")
                logging.info(f"策略 {strategy['name']} 成功: {youtube_url}")
                return m3u8_url
                
        except Exception as e:
            print(f"   ❌ 解析失敗")
        
        time.sleep(2)
    
    logging.error(f"所有策略失敗: {youtube_url}")
    return "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"

# ===== 解析 yt_info.txt =====
def process_yt_info():
    if not os.path.exists(yt_info_path):
        print(f"❌ 未找到 {yt_info_path}")
        return
        
    try:
        with open(yt_info_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        logging.info(f"讀取 yt_info.txt 成功，共 {len(lines)} 行")

        i = 1
        entries = lines[2:]  # 跳過前兩行
        for j in range(0, len(entries), 2):
            if j + 1 >= len(entries):
                continue
            info_line = entries[j]
            youtube_url = entries[j + 1]
            channel_name = info_line.split("|")[0].strip() or f"Channel{i:02d}"

            print(f"
{'='*60}")
            print(f"🔍 處理頻道 {i}: {channel_name}")
            print(f"📺 YouTube URL: {youtube_url}")
            
            m3u8_url = grab(youtube_url)

            # 儲存 .m3u8
            output_m3u8 = os.path.join(output_dir, f"y{i:02d}.m3u8")
            with open(output_m3u8, "w", encoding="utf-8") as f:
                f.write(f"#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=1280000
{m3u8_url}
")
            logging.info(f"生成 m3u8: {output_m3u8}")

            # 儲存 .php
            output_php = os.path.join(output_dir, f"y{i:02d}.php")
            with open(output_php, "w", encoding="utf-8") as f:
                f.write(f"<?php
header('Location: {m3u8_url}');
?>")
            logging.info(f"生成 php: {output_php}")

            print(f"✅ 完成: y{i:02d}.m3u8 和 y{i:02d}.php")
            i += 1
            time.sleep(3)

    except Exception as e:
        logging.error(f"處理 yt_info.txt 失敗: {e}")
        print(f"❌ 處理 yt_info.txt 失敗: {e}")

# ===== SFTP 上傳 =====
def upload_files():
    print("
" + "="*60)
    print("🚀 啟動 SFTP 上傳...")
    print("="*60)
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        print(f"✅ SFTP 連線成功: {SFTP_HOST}")

        try:
            sftp.chdir(SFTP_REMOTE_DIR)
        except IOError:
            print(f"📁 創建遠端目錄: {SFTP_REMOTE_DIR}")
            sftp.mkdir(SFTP_REMOTE_DIR)
            sftp.chdir(SFTP_REMOTE_DIR)

        uploaded_count = 0
        for file in os.listdir(output_dir):
            local_path = os.path.join(output_dir, file)
            remote_path = os.path.join(SFTP_REMOTE_DIR, file)
            if os.path.isfile(local_path):
                print(f"⬆️ 上傳 {file}")
                sftp.put(local_path, remote_path)
                uploaded_count += 1

        sftp.close()
        transport.close()
        print(f"✅ 上傳完成！共 {uploaded_count} 個檔案")
        logging.info(f"SFTP 上傳完成，共 {uploaded_count} 個檔案")
        
    except Exception as e:
        print(f"❌ SFTP 上傳失敗: {e}")
        logging.error(f"SFTP 上傳失敗: {e}")

# ===== 主程式入口 =====
if __name__ == "__main__":
    print("="*60)
    print("🎬 YouTube 直播 M3U8 解析器 (GitHub Actions 版)")
    print("="*60)
    
    # 檢查 yt-dlp
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
        print(f"✅ yt-dlp 版本: {result.stdout.strip()}")
    except:
        print("❌ 未安裝 yt-dlp，請在 workflow 安裝")
        exit(1)
    
    print(f"🔑 API Key: {'✅' if YOUTUBE_API_KEY else '❌'}")
    print(f"🍪 Cookies: {'✅' if os.path.exists(cookies_path) else '❌'}")
    print(f"🌐 SFTP: ✅")
    
    start_time = time.time()
    
    process_yt_info()
    upload_files()
    
    elapsed_time = time.time() - start_time
    print(f"
⏱️ 總執行時間: {elapsed_time:.2f} 秒")
    logging.info(f"執行完成，總時間: {elapsed_time:.2f} 秒")
