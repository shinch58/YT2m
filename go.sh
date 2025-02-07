#!/bin/bash

echo "🔵 go.sh: 開始執行..."
echo "🔵 當前目錄: $(pwd)"
echo "🔵 顯示檔案列表:"
ls -lh

# 安裝 Python 依賴
python3 -m pip install requests
# 安裝 yt-dlp（確保 GitHub Actions 可以解析 YouTube 直播）
python3 -m pip install yt-dlp

# 切換到 scripts 目錄
cd "$(dirname "$0")/scripts/"
echo "🔵 進入 scripts 目錄: $(pwd)"
ls -lh  # 確保 yt_m.py 存在

# 執行 yt_m.py
python3 yt_m.py

echo "🟢 go.sh: 執行完成"
