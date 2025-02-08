#!/bin/bash

echo "🚀 開始執行 go.sh"

# 確保環境變數 YT_COOKIES 存在
if [[ -z "$YT_COOKIES" ]]; then
  echo "❌ 環境變數 YT_COOKIES 未設置"
  exit 1
fi

# 進入腳本目錄
cd "$(dirname "$0")"

# 檢查 output 目錄是否存在，若無則建立
mkdir -p output

# 生成 cookies.txt
echo "$YT_COOKIES" > cookies.txt
echo "✅ cookies.txt 生成完成"

# 執行 yt_m.py 解析 YouTube 直播 M3U8
python3 scripts/yt_m.py

echo "✅ go.sh 執行完成"
