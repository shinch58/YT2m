#!/bin/sh

# 安裝依賴
sudo apt-get update
sudo apt-get install -y yt-dlp
sudo apt-get install -y python3-pip
pip3 install requests

# 執行 Python 腳本
python3 scripts/yt_m.py
