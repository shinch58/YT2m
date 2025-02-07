#!/bin/bash

# 打印腳本所在的目錄
echo $(dirname $0)

# 安裝所需的 Python 模組（如果還未安裝）
python3 -m pip install requests

# 切換到腳本所在目錄
cd $(dirname $0)/scripts/

# 運行 yt_m3ugrabber.py 腳本
python3 yt_m3ugrabber.py

echo "m3u8 grabbed and saved to parent directory"
