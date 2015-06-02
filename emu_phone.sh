#!/bin/sh
if [ -n $1 ]
then
 PTS="-- -p /dev/pts/$1"
fi
python main.py -m screen:one,scale=.5 $PTS
