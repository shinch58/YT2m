#! /usr/bin/python3

import requests
import os
import sys

windows = False
if 'win' in sys.platform:
    windows = True

def grab(url, output_file):
    response = requests.get(url, timeout=15).text
    if '.m3u8' not in response:
        if '.m3u8' not in response:
            if windows:
                output_file.write('https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u\n')
                return
            os.system(f'curl "{url}" > temp.txt')
            response = ''.join(open('temp.txt').readlines())
            if '.m3u8' not in response:
                output_file.write('https://raw.githubusercontent.com/shinch58/YT2m/main/assets/moose_na.m3u\n')
                return
    end = response.find('.m3u8') + 5
    tuner = 100
    while True:
        if 'https://' in response[end-tuner:end]:
            link = response[end-tuner:end]
            start = link.find('https://')
            end = link.find('.m3u8') + 5
            break
        else:
            tuner += 5
    output_file.write(f"{link[start:end]}\n")

# 計數器
counter = 1

# 設置文件生成的目標目錄
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')

# 確保目標目錄存在
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

with open('../yt_info.txt') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('~~'):
            continue
        if not line.startswith('https:'):
            line = line.split('|')
            ch_name = line[0].strip()
            grp_title = line[1].strip().title()
            tvg_logo = line[2].strip()
            tvg_id = line[3].strip()
            output_filename = f"y{counter:02}.m3u8"
            output_filepath = os.path.join(output_dir, output_filename)
            with open(output_filepath, 'w') as output_file:
                output_file.write('#EXTM3U x-tvg-url="https://github.com/botallen/epg/releases/download/latest/epg.xml"\n')
                output_file.write(f'#EXTINF:-1 group-title="{grp_title}" tvg-logo="{tvg_logo}" tvg-id="{tvg_id}", {ch_name}\n')
            counter += 1
        else:
            with open(output_filepath, 'a') as output_file:
                grab(line, output_file)

if 'temp.txt' in os.listdir():
    os.system('rm temp.txt')
