#!/usr/bin/env bash

ffmpeg -framerate ${1} -f image2 -i "${2}" -c:v libvpx-vp9 -pix_fmt yuva420p ./output/dvd.webm