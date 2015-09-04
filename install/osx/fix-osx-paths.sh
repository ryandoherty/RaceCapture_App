#!/usr/bin/env bash

cd /Applications/Kivy.app/Contents/Resources/venv/bin
source activate

cd ../..
osxrelocator -r . /Library/Frameworks/GStreamer.framework/ \
	@executable_path/../Frameworks/GStreamer.framework/
osxrelocator -r . /Library/Frameworks/SDL2/ \
	@executable_path/../Frameworks/SDL2/
osxrelocator -r . /Library/Frameworks/SDL2_ttf/ \
	@executable_path/../Frameworks/SDL2_ttf/
osxrelocator -r . /Library/Frameworks/SDL2_image/ \
	@executable_path/../Frameworks/SDL2_image/
osxrelocator -r . @rpath/SDL2.framework/Versions/A/SDL2 \
	@executable_path/../Frameworks/SDL2.framework/Versions/A/SDL2
osxrelocator -r . @rpath/SDL2_ttf.framework/Versions/A/SDL2_ttf \
	@executable_path/../Frameworks/SDL2_ttf.framework/Versions/A/SDL2_ttf
osxrelocator -r . @rpath/SDL2_image.framework/Versions/A/SDL2_image \
	@executable_path/../Frameworks/SDL2_image.framework/Versions/A/SDL2_image
osxrelocator -r . @rpath/SDL2_mixer.framework/Versions/A/SDL2_mixer \
	@executable_path/../Frameworks/SDL2_mixer.framework/Versions/A/SDL2_mixer
