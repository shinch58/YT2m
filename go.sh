#!/bin/sh

echo "🚀 開始執行 go.sh"

# 確保 YT_COOKIES 存在
if [ -z "$YT_COOKIES" ]; then
  echo "❌ 環境變數 YT_COOKIES 未設置，無法解析 YouTube 直播"
  exit 1
fi

# 執行 Python 腳本
python3 "$(dirname "$0")/scripts/yt_m.py"

echo "✅ yt_m.py 執行完成"
