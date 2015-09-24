#!/bin/bash
cp install/defaulttheme-0.png .buildozer/android/platform/python-for-android/dist/racecapture/private/lib/python2.7/site-packages/kivy/data/images/defaulttheme-0.png
cp install/defaulttheme-0.png .buildozer/android/platform/python-for-android/dist/racecapture/python-install/lib/python2.7/site-packages/kivy/data/images/defaulttheme-0.png
buildozer android debug deploy run logcat
