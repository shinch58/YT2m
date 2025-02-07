#!/bin/bash

# 打印腳本所在的目錄
echo $(dirname $0)

# 安裝所需的 Python 模組（如果還未安裝）
python3 -m pip install requests yt-dlp
python3 -m pip install --upgrade yt-dlp

# 檢查並創建 output 資料夾（如果不存在）
if [ ! -d "./output" ]; then
    mkdir ./output
fi

# 運行 yt_m.py 腳本
python3 scripts/yt_m.py
