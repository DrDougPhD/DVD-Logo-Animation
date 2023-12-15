#!/usr/bin/env bash

ffmpeg -framerate 60 -f image2 -i ./output/%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p ./output/dvd.webm