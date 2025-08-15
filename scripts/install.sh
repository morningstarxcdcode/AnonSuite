#!/usr/bin/env bash

# AnonSuite Installation Script

# This script will install AnonSuite and its dependencies.

ANONSUITE_ROOT="/Users/morningstar/Desktop/AnonSuite"

# Create necessary directories
mkdir -p $ANONSUITE_ROOT/log
mkdir -p $ANONSUITE_ROOT/run

# Install dependencies for Debian-based Linux. For macOS, use Homebrew.
# For example: brew install tor haproxy privoxy python
# apt-get install -y tor haproxy privoxy python3 python3-pip

# For macOS, you may need to install pip separately and then run:
# pip3 install -r $ANONSUITE_ROOT/src/wifi/wifipumpkin3/requirements.txt

# Compile Pixiewps
bash $ANONSUITE_ROOT/src/wifi/compile_pixiewps.sh

# Create symbolic links
sudo ln -sf $ANONSUITE_ROOT/src/anonsuite.py /usr/local/bin/anonsuite
sudo ln -sf $ANONSUITE_ROOT/src/anonymity/anonsuite /usr/local/bin/anonsurf

echo "AnonSuite installed successfully."
