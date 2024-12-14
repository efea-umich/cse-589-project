# Make a tar with auto-vtt/ and network-sim/, excluding any directories that start with a dot.

tar -cvf colab-upload.tar --exclude=".*" --exclude="*.tar.*" auto-vtt network-sim