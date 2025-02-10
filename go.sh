#!/bin/bash

set -e  # 遇到錯誤立即停止腳本
export TZ=Asia/Taipei  # 設置時區為台灣時間

echo "🚀 開始執行 go.sh"

# 確保 Python 依賴已安裝
pip install -U requests paramiko  # 確保 Python 依賴可用

# 執行 yt_m.py 解析 M3U8
echo "🔍 開始執行 yt_m.py"
python3 scripts/yt_m.py

# 檢查 Git 設置是否已配置
git config --global user.name "github-actions[bot]"
git config --global user.email "github-actions[bot]@users.noreply.github.com"

# 檢查 output 目錄是否有變更
if [[ -n "$(git status --porcelain output/)" ]]; then
    echo "📂 偵測到 output 變更，開始提交..."
    git add output/
    git commit -m "🔄 更新 M3U8 文件 $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
    echo "✅ 變更已提交至 GitHub"
else
    echo "ℹ️ output 目錄沒有變更，不進行提交"
fi

# 記錄時間戳記
echo "$(date '+%m/%d/%Y %H:%M:%S %Z')" > scripts/timestamp.txt
echo "✅ go.sh 執行完成"
