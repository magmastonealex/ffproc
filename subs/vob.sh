#!/bin/bash -e
#$1 is input file
#$2 is track #
#$3 is output filename

tmpnm=`uuidgen`

mkvextract tracks "$1" $2:$tmpnm_subs_tmp.sub
vobsub2srt --tesseract-lang eng --verbose $tmpnm_subs_tmp

mv $tmpnm_subs_tmp.srt "$3"
#
rm $tmpnm_subs_tmp.{idx,sub}


