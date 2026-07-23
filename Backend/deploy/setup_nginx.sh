#!/bin/bash

# Copy config to Nginx directory
echo "Configuring Nginx..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
sudo cp "$SCRIPT_DIR/nginx_config" /etc/nginx/sites-available/sinewave_bot

# Enable the site
sudo ln -sf /etc/nginx/sites-available/sinewave_bot /etc/nginx/sites-enabled/

# Remove default site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default
fi

# Test configuration
echo "Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    # Restart Nginx
    echo "Restarting Nginx..."
    sudo systemctl restart nginx
    echo "Nginx configured successfully! Application should be accessible on port 80."
else
    echo "Nginx configuration failed."
    exit 1
fi
