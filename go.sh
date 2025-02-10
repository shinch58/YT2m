#!/bin/bash
set -e  # 遇到錯誤立即停止

echo "🚀 開始執行 go.sh"

# 檢查必要環境變數
if [[ -z "$Y_1" || -z "$Y_2" || -z "$Y_3" ]]; then
    echo "❌ 缺少 YouTube API 金鑰"
    exit 1
fi

# 安裝依賴
pip install -U yt-dlp requests paramiko

# 執行 yt_m.py
python3 scripts/yt_m.py

# 確保 Git 設置正確
git config --global user.name "github-actions"
git config --global user.email "github-actions@github.com"

# 檢查 output 變更並提交
if [[ -n "$(git status --porcelain output/)" ]]; then
    git add output/
    git commit -m "🔄 更新 M3U8 文件 $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
fi

echo "✅ go.sh 執行完成"
