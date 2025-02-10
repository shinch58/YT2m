import os
import requests
import json
import paramiko

YT_INFO_PATH = "yt_info.txt"
TMP_INFO_PATH = "tmp_inf.txt"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

API_KEYS = [os.getenv("Y_1"), os.getenv("Y_2"), os.getenv("Y_3")]
api_index = 0  


def get_live_video_id(channel_url):
    """使用 YouTube API 取得 Live Video ID"""
    global api_index
    api_key = API_KEYS[api_index]
    api_index = (api_index + 1) % len(API_KEYS)

    channel_id = channel_url.split("/")[-1]  
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&eventType=live&type=video&key={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "items" in data and data["items"]:
            return data["items"][0]["id"]["videoId"]  
    print(f"⚠️ 無法解析: {channel_url}")
    return None


def convert_yt_info():
    """將 `yt_info.txt` 轉換為 `tmp_inf.txt`，將 @channel 轉換為 Video ID"""
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
    print(f"✅ `yt_info.txt` 轉換完成，儲存至 `{TMP_INFO_PATH}`")


def grab_m3u8(video_url):
    """獲取 YouTube 直播 M3U8 連結"""
    video_id = video_url.split("v=")[-1]
    return f"https://manifest.googlevideo.com/api/manifest/hls_variant/id/{video_id}"


def process_yt_info():
    """解析 `tmp_inf.txt`，並生成 M3U8 & PHP 檔案"""
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
            print(f"🔍 解析 M3U8: {youtube_url}")
            m3u8_url = grab_m3u8(youtube_url)

            output_m3u8 = os.path.join(OUTPUT_DIR, f"y{i:02d}.m3u8")
            with open(output_m3u8, "w", encoding="utf-8") as f:
                f.write(f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\n{m3u8_url}\n")

            output_php = os.path.join(OUTPUT_DIR, f"y{i:02d}.php")
            with open(output_php, "w", encoding="utf-8") as f:
                f.write(f"<?php\nheader('Location: {m3u8_url}');\n?>")

            print(f"✅ 生成 {output_m3u8} 和 {output_php}")
            i += 1


if __name__ == "__main__":
    convert_yt_info()  
    process_yt_info()
