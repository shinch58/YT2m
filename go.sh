#!/bin/bash

echo "🚀 安裝 Selenium 和 ChromeDriver"
pip install selenium webdriver-manager

echo "🚀 運行 yt_m.py 解析 YouTube 直播 M3U8"
python3 scripts/yt_m.py

echo "✅ M3U8 解析完成"
