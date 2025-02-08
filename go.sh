#!/bin/bash

echo "🚀 開始執行 go.sh"

# 生成 cookies.txt
if [ -z "$YT_COOKIES" ]; then
    echo "❌ 環境變數 YT_COOKIES 未設置"
    exit 1
fi

echo "$YT_COOKIES" | base64 --decode > cookies.txt
echo "✅ cookies.txt 生成完成"

# 安裝依賴（確保 `yt-dlp` 和 `requests` 可用）
echo "📦 安裝 yt-dlp 和 pip3"
sudo apt update
sudo apt install -y yt-dlp python3-pip
pip3 install --user requests

# 執行 yt_m.py 解析 M3U8
echo "🐍 執行 scripts/yt_m.py"
python3 scripts/yt_m.py

# **刪除 cookies.txt**
rm -f cookies.txt
echo "✅ cookies.txt 已刪除"

echo "✅ go.sh 執行完成"
