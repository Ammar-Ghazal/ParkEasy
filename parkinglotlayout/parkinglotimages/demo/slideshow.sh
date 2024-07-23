#!/bin/bash

# Directory containing images
IMAGE_DIR="."

# Duration of each image display in seconds
DISPLAY_DURATION=22

# Fade transition duration in milliseconds
FADE_DURATION=100

# Run the slideshow
feh --fullscreen --slideshow-delay $DISPLAY_DURATION --cycle-once --randomize --auto-zoom --borderless --reload $FADE_DURATION "$IMAGE_DIR"
