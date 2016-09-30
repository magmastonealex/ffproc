#!/bin/bash -e

#$1 is input file
#$2 is track #
#$3 is output filename

tmpnm=`uuidgen`
mkvextract tracks "$1" $2:"$3"
