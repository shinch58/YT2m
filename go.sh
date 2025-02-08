#!/bin/sh

echo "🚀 開始執行 go.sh"

# 測試是否成功讀取 YT_COOKIES
if [ -z "$YT_COOKIES" ]; then
  echo "❌ 環境變數 YT_COOKIES 未設置"
  exit 1
else
  echo "✅ YT_COOKIES 已成功讀取"
  echo "$YT_COOKIES" > cookies.txt  # 儲存 cookies.txt
fi

# 安裝必要套件
echo "📦 安裝 yt-dlp 和 pip3"
sudo apt update
sudo apt install -y yt-dlp python3-pip

# 測試 yt-dlp 是否能解析 M3U8
echo "🔍 測試 yt-dlp 解析 YouTube 直播"
yt-dlp --cookies cookies.txt -g "https://www.youtube.com/watch?v=ylYJSBUgaMA"

# 執行 Python 腳本
echo "🐍 執行 scripts/yt_m.py"
python3 "$(dirname "$0")/scripts/yt_m.py"

echo "✅ yt_m.py 執行完成"

# 檢查 output 目錄變更並提交
echo "📂 檢查 output/ 目錄變更"
git add output/
git status

if git diff --cached --quiet; then
  echo "⚠️ 沒有變更，不提交"
else
  git config --global user.name "github-actions[bot]"
  git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"
  git commit -m "📺 更新 M3U8 清單"
  git push origin main
  echo "✅ 變更已提交"
fi
