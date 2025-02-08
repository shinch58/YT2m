#!/bin/sh
set -e  # 遇到錯誤時立即中止

echo "🚀 開始執行 go.sh"
echo "📂 當前目錄: $(pwd)"
ls -la

# 安裝依賴
echo "📦 安裝 yt-dlp 和 pip3"
sudo apt-get update
sudo apt-get install -y yt-dlp
sudo apt-get install -y python3-pip
pip3 install requests

# 確保 yt_info.txt 存在
if [ ! -f "$(dirname "$0")/yt_info.txt" ]; then
    echo "❌ 找不到 yt_info.txt，請確認檔案是否存在！"
    exit 1
fi

# 執行 Python 腳本
echo "🐍 執行 yt_m.py"
python3 "$(dirname "$0")/yt_m.py"
echo "✅ yt_m.py 執行完成"

# 確保 output/ 目錄下有 M3U8 檔案
echo "📂 檢查 output/ 目錄內容"
ls -la "$(dirname "$0")/output"
