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
            if "/@" in line:  # 如果是 YouTube 頻道連結
                video_id = get_live_video_id(line.strip())  # 轉換為 video ID
                if video_id:
                    line = f"https://www.youtube.com/watch?v={video_id}\n"
            new_lines.append(line)

    with open(TMP_INFO_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"✅ 轉換完成，儲存至 {TMP_INFO_PATH}")


def grab_m3u8(youtube_url):
    """使用 YouTube HLS API 解析 M3U8 連結"""
    if "watch?v=" in youtube_url:
        video_id = youtube_url.split("watch?v=")[-1]
        hls_url = f"https://manifest.googlevideo.com/api/manifest/hls_variant/id/{video_id}"
        return hls_url
    else:
        print(f"⚠️ 錯誤的 YouTube 連結: {youtube_url}")
        return None
