#!/usr/bin/env bash

INSTALL_DIR="$1"
cd "$INSTALL_DIR"
echo "INSTALL DIR: $INSTALL_DIR \n"
pip install -r "$INSTALL_DIR/ios_requirements.txt" --force-reinstall --target "$INSTALL_DIR"
