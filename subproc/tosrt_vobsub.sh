#!/bin/bash -e
mkvextract tracks "$1" $2:subs_tmp.sub
bdsup2subpp -o 'out_*.sub' subs_tmp.sup
vobsub2srt --tesseract-lang eng --verbose subs_tmp
nme="$1"
mv subs_tmp.srt "${nme%.*}.$3.srt"
#
rm subs_tmp.{idx,sub}


