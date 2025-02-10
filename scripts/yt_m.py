import re
import requests
import json

def get_video_id(channel_url):
    """ 從 YouTube 頻道 URL 取得直播影片 ID """
    api_url = f"https://www.googleapis.com/youtube/v3/search?part=id&channelId={channel_url}&eventType=live&type=video&key=YOUR_YOUTUBE_API_KEY"
    response = requests.get(api_url)
    data = response.json()
    
    if "items" in data and len(data["items"]) > 0:
        return data["items"][0]["id"]["videoId"]
    return None

def extract_full_m3u8(video_url):
    """ 解析 YouTube 直播頁面 HTML 以獲取完整 M3U8 連結 """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    html = requests.get(video_url, headers=headers).text
    match = re.search(r'(https://manifest\.googlevideo\.com/[^"]+index\.m3u8)', html)
    return match.group(1) if match else None

def main():
    """ 主程式 """
    channels = [
        "https://www.youtube.com/@bdtvbest/live",
        "https://www.youtube.com/@chengsin94/live"
    ]

    results = []
    for channel_url in channels:
        print(f"🔍 解析 {channel_url} ...")
        
        video_id = get_video_id(channel_url)
        if not video_id:
            print(f"❌ 無法找到直播影片: {channel_url}")
            continue
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        m3u8_url = extract_full_m3u8(video_url)

        if m3u8_url:
            print(f"✅ 找到 M3U8: {m3u8_url}")
            results.append({"channel": channel_url, "m3u8": m3u8_url})
        else:
            print(f"❌ 未找到 M3U8: {video_url}")

    with open("m3u8_list.json", "w") as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    main()
