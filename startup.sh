#!/bin/bash
# ffmpeg o'rnatish
apt-get update -qq && apt-get install -y ffmpeg

# Botni ishga tushirish
python bot.py
