#!/bin/bash

# Update and install unzip/wget if missing
sudo apt update
sudo apt install -y wget unzip

# Download Ngrok
echo "Downloading Ngrok..."
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz

# Unzip
echo "Installing..."
sudo tar xvzf ngrok-v3-stable-linux-amd64.tgz -C /usr/local/bin

# Clean up
rm ngrok-v3-stable-linux-amd64.tgz

echo "Ngrok installed successfully!"
echo "--------------------------------------------------------"
echo "To expose your bot (running on port 8000), run:"
echo "ngrok http 8000"
echo "--------------------------------------------------------"
echo "Note: If you have an Ngrok auth token, run this first:"
echo "ngrok config add-authtoken <YOUR_TOKEN>"
