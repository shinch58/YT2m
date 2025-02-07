#!/bin/bash

echo $(dirname $0)

# 安裝所需的 Python 模組（如果還未安裝）
python3 -m pip install requests

# 運行 yt_m.py 腳本
python3 scripts/yt_m.py
