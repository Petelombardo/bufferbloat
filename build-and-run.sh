#!/bin/bash

# Build and Run Script for Bufferbloat Tester
# This script builds the Docker image and runs the container

set -e  # Exit on any error

echo "🔧 Building Bufferbloat Tester..."

# Build the Docker image
docker build -t bufferbloat-tester .

echo "✅ Build complete!"

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "bufferbloat-tester"; then
    echo "🔄 Stopping existing container..."
    docker stop bufferbloat-tester >/dev/null 2>&1 || true
    docker rm bufferbloat-tester >/dev/null 2>&1 || true
fi

# Run the new container
echo "🚀 Starting Bufferbloat Tester..."
docker run -d \
    --name bufferbloat-tester \
    -p 8080:8080 \
    --restart unless-stopped \
    bufferbloat-tester

echo "⏳ Waiting for container to start..."
sleep 3

# Check if container is running
if docker ps --format 'table {{.Names}}' | grep -q "bufferbloat-tester"; then
    echo "✅ Bufferbloat Tester is running!"
    echo ""
    echo "🌐 Access the web interface at:"
    echo "   http://localhost:8080 (for localhost testing only)"
    echo ""
    
    # Try to get the local IP address
    LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "your-server-ip")
    if [ "$LOCAL_IP" != "your-server-ip" ]; then
        echo "🔗 For REAL bufferbloat testing, access from other devices at:"
        echo "   http://$LOCAL_IP:8080"
        echo ""
        echo "⚠️  IMPORTANT: Testing localhost won't detect network bufferbloat!"
        echo "   Deploy on one device, test from another device on your network."
        echo ""
    fi
    
    echo "📊 Quick commands:"
    echo "   View logs:    docker logs -f bufferbloat-tester"
    echo "   Stop:         docker stop bufferbloat-tester"
    echo "   Restart:      docker restart bufferbloat-tester"
    echo ""
    
    # Open browser on macOS/Linux (optional)
    if command -v open >/dev/null 2>&1; then
        echo "🔍 Opening browser..."
        open http://localhost:8080
    elif command -v xdg-open >/dev/null 2>&1; then
        echo "🔍 Opening browser..."
        xdg-open http://localhost:8080
    fi
    
else
    echo "❌ Failed to start container. Checking logs..."
    docker logs bufferbloat-tester
    exit 1
fi
