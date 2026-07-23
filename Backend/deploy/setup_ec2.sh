#!/bin/bash

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python, git, tmux, nginx, and certbot
echo "Installing dependencies..."
sudo apt install -y python3-pip python3-venv git tmux nginx certbot python3-certbot-nginx

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

echo "----------------------------------------------------------------"
echo "System setup complete."
echo "NEXT STEPS:"
echo "1. Clone your repository: git clone https://github.com/tdlsoft/sinewave-bot-backend.git"
echo "2. Navigate into the folder: cd sinewave-bot-backend"
echo "3. Run the deployment guide steps to configure Nginx and SSL."
echo "----------------------------------------------------------------"
