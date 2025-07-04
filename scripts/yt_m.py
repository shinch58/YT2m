import os
import re
import subprocess
import requests
import paramiko
from urllib.parse import urlparse, urljoin

# 設定檔案路徑
yt_info_path = "yt_info.txt"
output_dir = "output"
cookies_path = os.path.join(os.getcwd(), "cookies.txt")

# 從環境變數讀取 SFTP 連線資訊
SF_L = os.getenv("SF_L", "")
if not SF_L:
    print("❌ 環境變數 SF_L 未設置")
    exit(1)

# 解析 SFTP URL
parsed_url = urlparse(SF_L)
SFTP_HOST = parsed_url.hostname
SFTP_PORT = parsed_url.port if parsed_url.port else 22
SFTP_USER = parsed_url.username
SFTP_PASSWORD = parsed_url.password
SFTP_REMOTE_DIR = parsed_url.path if parsed_url.path else "/"

# 確保輸出目錄存在
os.makedirs(output_dir, exist_ok=True)

def get_html(url, headers=None, cookies=None):
    """先用 requests，失敗 fallback 用 cloudscraper"""
    try:
        res = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        return res.text
    except Exception as e:
        print(f"⚠️ requests 抓取失敗: {e}，fallback 用 cloudscraper")
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            res = scraper.get(url, headers=headers, cookies=cookies, timeout=10)
            return res.text
        except Exception as e2:
            print(f"❌ cloudscraper 也失敗: {e2}")
            return ""

def extract_720p_variant(master_url):
    """從 master.m3u8 內選出最高 <=720p 的 variant"""
    try:
        content = requests.get(master_url, timeout=10).text
        variants = re.findall(r'#EXT-X-STREAM-INF:.*RESOLUTION=(\d+)x(\d+).*?\n(.*)', content)
        filtered = [(int(w), int(h), url) for w, h, url in variants if int(h) <= 720]
        if not filtered:
            print("⚠️ 無 720p 以下的 variant，使用原始 m3u8")
            return master_url
        best = max(filtered, key=lambda x: x[1])
        best_url = best[2].strip()
        if not best_url.startswith("http"):
            best_url = urljoin(master_url, best_url)
        print(f"🎯 選擇 720p variant：{best_url}")
        return best_url
    except Exception as e:
        print(f"⚠️ 解析 variant 失敗: {e}")
        return master_url

def grab(youtube_url):
    """從 HTML 或 yt-dlp 取得 M3U8（最高 720p）"""
    headers = {"User-Agent": "Mozilla/5.0"}
    cookies = {}

    # 嘗試讀取 cookies
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

    # 嘗試從 HTML 擷取 m3u8
    try:
        html = get_html(youtube_url, headers=headers, cookies=cookies)
        m3u8_matches = re.findall(r'https://[^\s"\']+\.m3u8', html)
        for url in m3u8_matches:
            if "googlevideo.com" in url:
                print("✅ 成功從 HTML 取得 m3u8")
                return extract_720p_variant(url)
    except Exception as e:
        print(f"⚠️ HTML 擷取失敗: {e}")

    # fallback 使用 yt-dlp
    print(f"⚙️ 執行 yt-dlp: yt-dlp -f 'bestvideo[height<=720]+bestaudio/best[height<=720]' --cookies {cookies_path} -g {youtube_url}")
    try:
        result = subprocess.run([
            "yt-dlp",
            "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "--cookies", cookies_path,
            "-g", youtube_url
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)

        if result.returncode == 0 and result.stdout.strip():
            m3u8_url = result.stdout.strip().splitlines()[0]
            print("✅ 成功取得 m3u8（yt-dlp）")
            return m3u8_url
        else:
            print("⚠️ yt-dlp 無回傳有效 URL")
            print(result.stderr)
    except Exception as e:
        print(f"❌ yt-dlp 執行失敗: {e}")

    return "https://raw.githubusercontent.com/jz168k/YT2m/main/assets/no_s.m3u8"

def process_yt_info():
    """解析 yt_info.txt 並生成 M3U8 和 PHP 檔案"""
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
            m3u8_url = grab(youtube_url)

            m3u8_content = f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\n{m3u8_url}\n"
            output_m3u8 = os.path.join(output_dir, f"y{i:02d}.m3u8")
            with open(output_m3u8, "w", encoding="utf-8") as f:
                f.write(m3u8_content)

            php_content = f"""<?php\nheader('Location: {m3u8_url}');\n?>"""
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
    process_yt_info()
    upload_files()
