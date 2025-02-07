#!/bin/bash

echo "🔵 go.sh: 開始執行..."
echo "🔵 當前目錄: $(pwd)"
echo "🔵 顯示檔案列表:"
ls -lh

# 安裝 Python 依賴
python3 -m pip install requests yt-dlp

# 確保 output 目錄存在
mkdir -p "$(dirname "$0")/output"
echo "✅ output 目錄已創建"

# 切換到 scripts 目錄
cd "$(dirname "$0")/scripts/" || { echo "❌ 無法進入 scripts 目錄"; exit 1; }
echo "🔵 進入 scripts 目錄: $(pwd)"
ls -lh  # 確保 yt_m.py 存在

# 執行 yt_m.py 並捕捉錯誤
echo "🔵 執行 yt_m.py..."
python3 yt_m.py 2>&1 | tee yt_m_log.txt
YT_EXIT_CODE=${PIPESTATUS[0]}

if [ $YT_EXIT_CODE -ne 0 ]; then
    echo "❌ yt_m.py 執行失敗，日誌如下："
    cat yt_m_log.txt
    exit 1
fi

# 列出 output 目錄
echo "🔵 yt_m.py 執行完畢，列出 output 目錄內容"
ls -lh "$(dirname "$0")/output" || echo "⚠️ output 目錄仍然不存在"

echo "🟢 go.sh: 執行完成"
