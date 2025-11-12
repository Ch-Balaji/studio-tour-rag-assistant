#!/bin/bash

# Frontend Setup Script for Azure VM
# This script will be executed on the remote server

echo "=== Frontend Setup Script ==="
echo "Starting at: $(date)"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "📦 Installing git..."
    sudo apt-get update
    sudo apt-get install -y git
else
    echo "✅ Git is already installed: $(git --version)"
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js 18.x..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    echo "✅ Node.js is already installed: $(node --version)"
fi

# Check npm version
echo "✅ npm version: $(npm --version)"

# Clone or update the repository
if [ ! -d "$HOME/FF918" ]; then
    echo "📥 Cloning repository..."
    cd $HOME
    git clone https://github.com/WarnerBrosDiscovery/FF918.git
    cd FF918
else
    echo "📥 Updating existing repository..."
    cd $HOME/FF918
    git pull origin main
fi

# Navigate to frontend folder
cd frontend

# Install dependencies
echo "📦 Installing frontend dependencies..."
npm install

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "📦 Installing PM2 globally..."
    sudo npm install -g pm2
else
    echo "✅ PM2 is already installed"
fi

# Build the frontend
echo "🔨 Building the frontend application..."
npm run build

# Check if frontend is already running
if pm2 list | grep -q "harry-potter-frontend"; then
    echo "🔄 Restarting existing frontend application..."
    pm2 restart harry-potter-frontend
else
    echo "🚀 Starting frontend application with PM2..."
    pm2 start npm --name "harry-potter-frontend" -- start
fi

# Save PM2 configuration
pm2 save

# Setup PM2 to start on system boot (only if not already done)
if [ ! -f "/etc/systemd/system/pm2-azureuser.service" ]; then
    echo "⚙️  Setting up PM2 startup script..."
    pm2 startup systemd -u azureuser --hp /home/azureuser | tail -n 1 | sudo bash
fi

# Show status
echo ""
echo "=== Setup Complete! ==="
echo "✅ Frontend is running at: http://20.163.185.178:3000"
echo ""
echo "📊 PM2 Status:"
pm2 status

echo ""
echo "📝 Useful commands:"
echo "  - View logs: pm2 logs harry-potter-frontend"
echo "  - Stop frontend: pm2 stop harry-potter-frontend"
echo "  - Restart frontend: pm2 restart harry-potter-frontend"
echo "  - Monitor: pm2 monit"
echo "  - View all processes: pm2 list"
echo ""
echo "Completed at: $(date)"

