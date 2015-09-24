#!/bin/bash
set -e
rm -rf bin
cp install/defaulttheme-0.png .buildozer/android/platform/python-for-android/dist/racecapture/private/lib/python2.7/site-packages/kivy/data/images/defaulttheme-0.png
cp install/defaulttheme-0.png .buildozer/android/platform/python-for-android/dist/racecapture/python-install/lib/python2.7/site-packages/kivy/data/images/defaulttheme-0.png
buildozer -v android release
APK=$(ls bin/*.apk)
RELEASE_APK="${APK/unsigned/signed}"
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore $1 -storepass $2 $APK rcpmobile
ZA=`find ~/.buildozer/ -name zipalign -print -quit`
$ZA -f 4 $APK $RELEASE_APK
