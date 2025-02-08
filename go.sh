#!/bin/sh

# 安裝依賴
sudo apt-get update
sudo apt-get install -y yt-dlp
sudo apt-get install -y python3-pip
pip3 install requests

# 確保 output 目錄存在，並清空內容
mkdir -p output
rm -rf output/*

# 執行 Python 腳本
python3 "$(dirname "$0")/scripts/yt_m.py"

# 提交變更
git add output/
git commit -m "Update M3U8 files" || echo "No changes to commit"
git push
