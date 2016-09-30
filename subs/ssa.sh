#!/bin/bash -e

#$1 is input file
#$2 is track #
#$3 is output filename

tmpnm=`uuidgen`

mkvextract tracks "$1" $2:$tmpnm_subs.ass

#Surprised? Me too. Turns out ffmpeg is the only tool in existance to do this.
#Everone online just says "ssa is better than srt, don't bother", yet ssa support is in far, far fewer players than SRT.
ffmpeg -i "$tmpnm_subs.ass" -map 0:0  -c:s:0 srt $tmpnm_subs_tmp.srt

nme="$1"
mv $tmpnm_subs_tmp.srt $3

rm $tmpnm_subs.ass


