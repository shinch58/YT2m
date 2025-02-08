#!/bin/sh

# 確保腳本報錯時立即停止
set -e

echo "🚀 開始執行 go.sh"

# 安裝依賴
sudo apt-get update
sudo apt-get install -y yt-dlp python3-pip
pip3 install requests

# 執行 Python 腳本
python3 scripts/yt_m.py

echo "✅ yt_m.py 執行完成"
