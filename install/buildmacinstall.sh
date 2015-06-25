#!/bin/bash
rm -rf dist
rm -rf build
kivy /usr/local/bin/pyinstaller -y racecapture.spec
pushd dist
cp ../defaulttheme-0.png racecapture.app/Contents/MacOS/kivy_install/data/images/
zip -r -9 racecapture.zip racecapture.app
popd
dist/racecapture/racecapture
