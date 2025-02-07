#!/bin/bash

echo "🔵 go.sh: 開始執行..."
echo "🔵 當前目錄: $(pwd)"
echo "🔵 顯示檔案列表:"
ls -lh

# 安裝 Python 依賴
python3 -m pip install -q requests yt-dlp

# 確保 `yt_m.py` 存在並可執行
if [[ ! -f scripts/yt_m.py ]]; then
    echo "❌ 錯誤: 找不到 scripts/yt_m.py"
    exit 1
fi

# 執行 yt_m.py
echo "🔵 執行 yt_m.py..."
python3 scripts/yt_m.py || { echo "❌ yt_m.py 執行失敗"; exit 1; }

# 確保 output/ 目錄存在
if [[ ! -d output ]]; then
    echo "❌ 錯誤: output/ 目錄未創建"
    exit 1
fi

# 顯示 output/ 內容
echo "🔵 確認 output/ 目錄內容:"
ls -lh output/

echo "🟢 go.sh: 執行完成"
