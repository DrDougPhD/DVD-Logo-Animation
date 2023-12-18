#!/usr/bin/env bash

ffmpeg -framerate ${1} -f image2 -i "${2}" -c:v libx264 -pix_fmt yuv420p ./output/dvd.mp4