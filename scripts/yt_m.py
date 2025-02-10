import os
import re
import json
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YT_INFO_PATH = os.path.join(BASE_DIR, "../yt_info.txt")
TMP_INFO_PATH = os.path.join(BASE_DIR, "../tmp_inf.txt")
OUTPUT_DIR = os.path.join(BASE_DIR, "../output/")

YT_API_KEYS = [os.getenv("Y_1"), os.getenv("Y_2"), os.getenv("Y_3")]
YT_API_KEYS = [key for key in YT_API_KEYS if key]
API_INDEX = 0


def switch_api_key():
    """輪替 YouTube API 金鑰"""
    global API_INDEX
    API_INDEX = (API_INDEX + 1) % len(YT_API_KEYS)


def get_live_video_id(channel_url):
    """取得 YouTube 直播影片 ID"""
    if not YT_API_KEYS:
        print("❌ 未設置 YouTube API 金鑰，跳過 API 解析")
        return None

    global API_INDEX
    channel_name = channel_url.split("/@")[-1].replace("/live", "")
    url = f"https://www.googleapis.com/youtube/v3/search?part=id&channelId={channel_name}&eventType=live&type=video&key={YT_API_KEYS[API_INDEX]}"

    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if "items" in data and data["items"]:
            video_id = data["items"][0]["id"]["videoId"]
            return video_id
        else:
            switch_api_key()
            return None
    except:
        switch_api_key()
        return None


def convert_yt_info():
    """轉換 yt_info.txt 為 tmp_inf.txt"""
    with open(YT_INFO_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("~~"):
            continue
        if "|" in line:
            new_lines.append(line + "\n")
        else:
            if "/@" in line:
                video_id = get_live_video_id(line)
                if video_id:
                    line = f"https://www.youtube.com/watch?v={video_id}"
            new_lines.append(line + "\n")

    with open(TMP_INFO_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"✅ 轉換完成，儲存至 {TMP_INFO_PATH}")


def grab_m3u8(youtube_url):
    """取得 YouTube HLS M3U8"""
    if "watch?v=" in youtube_url:
        video_id = youtube_url.split("watch?v=")[-1]
        return f"https://manifest.googlevideo.com/api/manifest/hls_variant/id/{video_id}"
    return None


def generate_m3u8():
    """根據 tmp_inf.txt 生成 M3U8"""
    with open(TMP_INFO_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    index = 1
    for i in range(0, len(lines), 2):
        if i + 1 >= len(lines):
            continue

        metadata = lines[i].strip()
        youtube_url = lines[i + 1].strip()
        hls_url = grab_m3u8(youtube_url)

        if not hls_url:
            continue

        m3u8_filename = f"y{index:02d}.m3u8"
        php_filename = f"y{index:02d}.php"
        m3u8_path = os.path.join(OUTPUT_DIR, m3u8_filename)
        php_path = os.path.join(OUTPUT_DIR, php_filename)

        with open(m3u8_path, "w", encoding="utf-8") as m3u8_file:
            m3u8_file.write("#EXTM3U\n")
            m3u8_file.write("#EXT-X-STREAM-INF:BANDWIDTH=1280000\n")
            m3u8_file.write(hls_url + "\n")

        with open(php_path, "w", encoding="utf-8") as php_file:
            php_file.write(f"<?php\n")
            php_file.write(f"    header('Location: {hls_url}');\n")
            php_file.write("?>\n")

        print(f"✅ 生成 {m3u8_filename} 和 {php_filename}")
        index += 1


if __name__ == "__main__":
    convert_yt_info()
    generate_m3u8()
