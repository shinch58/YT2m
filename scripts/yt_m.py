import os
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YT_INFO_PATH = os.path.join(BASE_DIR, "../yt_info.txt")
TMP_INFO_PATH = os.path.join(BASE_DIR, "../tmp_inf.txt")
OUTPUT_DIR = os.path.join(BASE_DIR, "../output/")

def grab_m3u8(youtube_url):
    """取得 YouTube HLS M3U8 連結"""
    if "watch?v=" in youtube_url:
        video_id = youtube_url.split("watch?v=")[-1]
        return f"https://manifest.googlevideo.com/api/manifest/hls_variant/id/{video_id}"
    return None

def generate_m3u8():
    """根據 tmp_inf.txt 生成 M3U8"""
    if not os.path.exists(TMP_INFO_PATH):
        print(f"❌ 找不到 {TMP_INFO_PATH}")
        return

    with open(TMP_INFO_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        print("❌ tmp_inf.txt 內容為空，無法生成 M3U8")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    index = 1
    updated = False
    for i in range(0, len(lines), 2):
        if i + 1 >= len(lines):
            continue

        metadata = lines[i].strip()
        youtube_url = lines[i + 1].strip()
        hls_url = grab_m3u8(youtube_url)

        if not hls_url:
            print(f"⚠️ 無法解析 M3U8: {youtube_url}")
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
        updated = True
        index += 1

    if not updated:
        print("ℹ️ 沒有新的 M3U8 生成")


if __name__ == "__main__":
    generate_m3u8()
