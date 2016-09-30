#!/bin/bash -e
cd /tmp
#$1 is input file
#$2 is track #
#$3 is output filename

tmpnm=`uuidgen`

mkvextract tracks "$1" $2:$tmpnm_subs_tmp.sup
xvfb-run -a bdsup2subpp -o "$tmpnm_out_*.sub" $tmpnm_subs_tmp.sup
vobsub2srt --tesseract-lang eng --verbose $tmpnm_out_subs_tmp
mv $tmpnm_out_subs_tmp.srt "$3"

#cleanup
rm $tmpnm_out_subs_tmp.{idx,sub}
rm $tmpnm_subs_tmp.sup
