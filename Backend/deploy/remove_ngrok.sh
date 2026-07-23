#!/bin/bash

# Stop Ngrok if running
pkill ngrok

# Remove binary
sudo rm /usr/local/bin/ngrok

# Remove config directory if exists
rm -rf ~/.config/ngrok

echo "Ngrok has been removed."
