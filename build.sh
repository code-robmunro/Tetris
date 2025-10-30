#!/bin/bash
set -e  # exit immediately if a command fails

# Step 1: Build pygbag output only
python -m pygbag --build main.py

# Step 2: Copy APK to current directory
cp -r build/web/tetris.apk .

# Step 3: Increment version number in index.html
perl -pe 's/(v=)(\d+)/$1.($2+1)/eg' -i index.html

echo "✅ Build complete. Version number incremented."