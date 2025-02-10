#!/bin/bash

set -e

echo "🚀 開始執行 go.sh"

# 執行 yt_m.py 解析 M3U8
python3 scripts/yt_m.py

# 確保 Git 設置正確
git config --global user.name "github-actions"
git config --global user.email "github-actions@github.com"

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
