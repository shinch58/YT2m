#!/bin/bash

echo "🚀 運行 yt_m.py 解析 YouTube 直播 M3U8"
python3 scripts/yt_m.py

echo "📂 檢查輸出目錄變更"
git add output/
git diff --cached --quiet || {
    echo "🔄 提交並推送變更"
    git commit -m "🔄 更新 M3U8 清單"
    git push
    echo "✅ 更新完成"
} || echo "⚠️ 無變更，跳過提交"
