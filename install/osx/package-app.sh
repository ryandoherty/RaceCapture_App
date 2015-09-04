#!/bin/bash

set -x  # verbose
if [ "X$1" == "X" ]; then
	echo "Usage: $(basename $0) path/to/your/app"
	exit 1
fi

set -e  # exit on error

SCRIPT_PATH="${BASH_SOURCE[0]}";
if([ -h "${SCRIPT_PATH}" ]) then
  while([ -h "${SCRIPT_PATH}" ]) do SCRIPT_PATH=`readlink "${SCRIPT_PATH}"`; done
fi
SCRIPT_PATH=$(python -c "import os; print os.path.realpath(os.path.dirname('${SCRIPT_PATH}'))")
KIVY_APP="${SCRIPT_PATH}/Kivy.App"

echo "${SCRIPT_PATH}"
echo "${KIVY_APP}"

if [ ! -f "${KIVY_APP}" ]; then
	echo "No Kivy.app generated, use create-osx-bundle.sh first."
fi

echo "-- Get the name of your app"
APPNAME="RaceCapture"
APPPATH="${SCRIPT_PATH}/${APPNAME}.app"
echo "Hello, ${APPNAME}"

echo "-- Duplicate the Kivy.app to ${APPNAME}.app"
cp -R ${SCRIPT_PATH}/Kivy.App/ ${APPPATH}

echo "-- Copy your application"
rsync -av --exclude-from=exclude.txt $1 ${APPPATH}/Contents/Resources/yourapp
#cp -R $1 ${APPPATH}/Contents/Resources/yourapp

echo "-- Optimize all python files"
source ${APPPATH}/Contents/Resources/venv/bin/activate
python -OO -m compileall ${APPPATH}

echo "-- Remove all py/pyc"
find -E ${APPPATH} -regex ".*pyc?$" -exec rm {} \;
