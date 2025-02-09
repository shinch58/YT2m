#!/bin/bash

set -e  # 遇到錯誤立即停止腳本

pip install -U yt-dlp

echo "🚀 開始執行 go.sh"

# 檢查 YT_COOKIES 是否存在
if [[ -z "$YT_COOKIES" ]]; then
    echo "❌ 環境變數 YT_COOKIES 未設置"
    exit 1
fi

# 解碼 YT_COOKIES 並生成 cookies.txt
echo "$YT_COOKIES" | base64 --decode | tr -d '\r' > cookies.txt
echo "✅ cookies.txt 生成完成"

# 執行 yt_m.py 解析 M3U8
echo "🔍 開始執行 yt_m.py"
python3 scripts/yt_m.py

# 刪除 cookies.txt，確保隱私安全
rm -f cookies.txt
echo "✅ cookies.txt 已刪除"

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
echo "執行時間：$(date)" >> log.txt
echo "$(date)" > timestamp.txt
echo "✅ go.sh 執行完成"
