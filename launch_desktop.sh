#!/bin/sh
if [ -n $1 ]
then
 PTS="-- -p /dev/pts/$1"
fi
python main.py $PTS
