#!/bin/bash
set -e
rm -rf bin
buildozer -v android release
APK=$(ls bin/*.apk)
RELEASE_APK="${APK/unsigned/signed}"
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore $1 -storepass $2 $APK rcpmobile
~/.buildozer/android/platform/android-sdk-21/build-tools/19.1.0/zipalign -f 4 $APK $RELEASE_APK
