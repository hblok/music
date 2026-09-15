#!/bin/sh
# Usage: wav2flac.sh track.wav  ->  track.flac
[ -n "$1" ] || { echo "usage: $0 file.wav" >&2; exit 1; }
ffmpeg -y -loglevel error -i "$1" -vn -ar 44100 -ac 2 -c:a flac -compression_level 8 "${1%.wav}.flac"
