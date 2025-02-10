#!/bin/bash

set -e

echo "🚀 開始執行 go.sh"

# 執行 yt_m.py
echo "🔍 解析 M3U8"
python3 scripts/yt_m.py

# 檢查 output 目錄是否有變更
git status output/
git diff output/

# 設置 Git 使用者資訊
git config --global user.name "github-actions"
git config --global user.email "github-actions@github.com"

# 強制提交變更
git add output/
git commit -m "🔄 更新 M3U8 $(date '+%Y-%m-%d %H:%M:%S')" || echo "ℹ️ 沒有變更可提交"
git push origin main || echo "ℹ️ 沒有變更，跳過推送"
git add m3u8_list.json
git commit -m "Add m3u8_list.json"
git push

echo "✅ go.sh 完成"
