#!/bin/bash -e
mkvextract tracks "$1" $2:subs_tmp.sup
xvfb-run -a bdsup2subpp -o 'out_*.sub' subs_tmp.sup
vobsub2srt --tesseract-lang eng --verbose out_subs_tmp
nme="$1"
mv out_subs_tmp.srt "${nme%.*}.$3.srt" 
#
rm out_subs_tmp.{idx,sub}
rm subs_tmp.sup
