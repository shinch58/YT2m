#!/bin/bash

echo "🚀 運行 yt_m.py 解析 YouTube 直播 M3U8"
python3 yt_m.py

echo "📂 檢查輸出目錄變更"
if git status --porcelain | grep "output/"; then
    git add output/
    git commit -m "🔄 更新 M3U8 直播連結"
    git push
    echo "✅ 變更已提交"
else
    echo "⚠️ 無變更，跳過提交"
fi
