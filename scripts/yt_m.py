import os
import requests
import json

# 設定檔案路徑
yt_info_path = "tmp_inf.txt"
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# 讀取 API 金鑰（使用 GitHub Actions 設定的三組 API 金鑰）
API_KEYS = [
    os.getenv("Y_1"),
    os.getenv("Y_2"),
    os.getenv("Y_3")
]

def get_video_id(channel_url, api_key):
    """使用 YouTube Data API 解析頻道的直播 ID"""
    channel_id = channel_url.split("/")[-1]  # 取得 @名稱
    api_url = f"https://www.googleapis.com/youtube/v3/search?part=id&channelId={channel_id}&eventType=live&type=video&key={api_key}"
    
    try:
        response = requests.get(api_url)
        data = response.json()

        # 記錄 API 回應
        print(f"🔍 API 回應: {json.dumps(data, indent=2)}")

        if "items" in data and len(data["items"]) > 0:
            video_id = data["items"][0]["id"]["videoId"]
            print(f"✅ 解析成功: {channel_url} → https://www.youtube.com/watch?v={video_id}")
            return video_id
        else:
            print(f"⚠️ API 無法取得直播 ID: {channel_url}")
            return None
    except Exception as e:
        print(f"❌ API 請求錯誤: {e}")
        return None

def convert_yt_info():
    """將 `tmp_inf.txt` 內的頻道連結轉換為影片 ID"""
    tmp_info_path = "tmp_inf.txt"
    with open(tmp_info_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    converted_lines = []
    api_key_index = 0  # 輪流使用 API 金鑰

    for line in lines:
        line = line.strip()
        if line.startswith("~~") or not line:
            converted_lines.append(line)
            continue

        if "|" in line:  # 頻道資訊行
            converted_lines.append(line)
        else:  # YouTube 頻道網址
            api_key = API_KEYS[api_key_index % len(API_KEYS)]
            api_key_index += 1

            print(f"🔑 使用 API 金鑰: (隱藏)")
            video_id = get_video_id(line, api_key)

            if video_id:
                new_line = f"https://www.youtube.com/watch?v={video_id}"
            else:
                new_line = line  # 保留原始網址（解析失敗）

            converted_lines.append(new_line)

    # 存入 `tmp_inf.txt`
    with open(tmp_info_path, "w", encoding="utf-8") as f:
        f.write("\n".join(converted_lines) + "\n")

    print("✅ 轉換完成，儲存至 tmp_inf.txt")

if __name__ == "__main__":
    convert_yt_info()
