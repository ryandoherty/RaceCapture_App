#!/usr/bin/env bash

INSTALL_DIR="$1"

pip install -r "$INSTALL_DIR/install/ios/ios_requirements.txt" --force-reinstall --target "$INSTALL_DIR"
