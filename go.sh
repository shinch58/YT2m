#!/bin/bash

set -e

echo "🚀 開始執行 go.sh"

# 執行 yt_m.py
echo "🔍 解析 M3U8"
python3 scripts/yt_m.py

# 設置 Git 使用者資訊
git config --global user.name "github-actions"
git config --global user.email "github-actions@github.com"

# 檢查 output 變更
if [[ -n "$(git status --porcelain output/)" ]]; then
    echo "📂 偵測到變更，開始提交..."
    git add output/
    git commit -m "🔄 更新 M3U8 $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
    echo "✅ 已提交變更"
else
    echo "ℹ️ 沒有變更，不提交"
fi

echo "✅ go.sh 完成"
