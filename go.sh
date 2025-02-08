#!/bin/sh
set -e  # 遇到錯誤時立即終止

echo "🚀 開始執行 go.sh"
echo "📂 當前目錄: $(pwd)"
ls -la

# 安裝依賴
echo "📦 安裝 yt-dlp 和 pip3"
sudo apt-get update
sudo apt-get install -y yt-dlp
pip3 install -U yt-dlp==2025.01.26
sudo apt-get install -y python3-pip
pip3 install requests

# 測試 yt-dlp 是否可用
echo "🔍 測試 yt-dlp 是否可用"
yt-dlp --version
yt-dlp -g "https://www.youtube.com/watch?v=dQw4w9WgXcQ" || echo "⚠️ yt-dlp 解析失敗"

# 確保 yt_info.txt 存在
if [ ! -f "$(pwd)/yt_info.txt" ]; then
    echo "❌ 找不到 yt_info.txt，請確認檔案是否存在！"
    exit 1
fi

# 執行 Python 腳本
echo "🐍 執行 scripts/yt_m.py"
python3 "$(pwd)/scripts/yt_m.py"
echo "✅ yt_m.py 執行完成"

# 確保 output/ 目錄下有 M3U8 檔案
echo "📂 檢查 output/ 目錄內容"
ls -la "$(pwd)/output"
