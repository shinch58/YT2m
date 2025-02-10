#!/bin/bash

set -e  # 遇到錯誤立即停止腳本

pip install -U yt-dlp

echo "🚀 開始執行 go.sh"

# 檢查 YT_COOKIE_B64 是否存在
if [[ -z "$YT_COOKIE_B64" ]]; then
    echo "❌ 環境變數 YT_COOKIE_B64 未設置"
    exit 1
fi

# 解碼 YT_COOKIE_B64 並生成 cookies.txt
echo "$YT_COOKIE_B64" | base64 --decode | tr -d '\r' > cookies.txt
echo "✅ cookies.txt 生成完成"

# 設置 YouTube API 金鑰
export YT_API_KEYS="$Y_1,$Y_2,$Y_3"
echo "✅ API 金鑰設置完成"

# 執行 yt_m.py 解析 M3U8（包含 SFTP 上傳）
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

# 設定時區
export TZ=Asia/Taipei
echo "$(date '+%m/%d/%Y %H:%M:%S %Z')" > scripts/timestamp.txt

echo "✅ go.sh 執行完成"
