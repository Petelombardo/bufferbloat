#!/bin/bash

# Bufferbloat Tester Startup Script
# This script helps with initial setup and deployment

set -e

echo "🌐 Bufferbloat Tester Setup"
echo "=========================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo "📝 Please edit .env with your configuration before continuing"
        echo ""
        echo "Key settings to configure:"
        echo "  - LISTEN_PORT: Port for container to listen on (default: 8080)"
        echo "  - PUBLIC_URL: Your public domain/URL (no port needed for standard 80/443)"
        echo "  - WEBRTC_UDP_HOSTNAME: Hostname for direct UDP connections"
        echo "  - WEBRTC_UDP_IP: (Alternative) IP address for direct UDP connections"
        echo "  - WEBRTC_UDP_PORT_MIN/MAX: UDP port range for WebRTC"
        echo ""
        read -p "Press Enter after editing .env to continue..."
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
fi

# Source .env to check configuration
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Validate required environment variables
echo "🔍 Validating configuration..."

required_vars=("LISTEN_PORT" "PUBLIC_URL" "WEBRTC_UDP_PORT_MIN" "WEBRTC_UDP_PORT_MAX")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

# Check for UDP hostname or IP (at least one should be set)
if [ -z "${WEBRTC_UDP_HOSTNAME}" ] && [ -z "${WEBRTC_UDP_IP}" ]; then
    missing_vars+=("WEBRTC_UDP_HOSTNAME or WEBRTC_UDP_IP")
fi

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '   %s\n' "${missing_vars[@]}"
    echo "Please check your .env file"
    exit 1
fi

echo "✅ Configuration validated"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Check if ports are available
echo "🔍 Checking port availability..."

if netstat -tlnp 2>/dev/null | grep -q ":${LISTEN_PORT} "; then
    echo "⚠️  Port ${LISTEN_PORT} is already in use"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Port ${LISTEN_PORT} is available"
fi

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs
echo "✅ Logs directory created"

# Build and start the application
echo "🐳 Building Docker image..."
docker-compose build

echo "🚀 Starting Bufferbloat Tester..."
docker-compose up -d

# Wait a moment for startup
echo "⏳ Waiting for application to start..."
sleep 5

# Check if application is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Bufferbloat Tester is running!"
    echo ""
    echo "🌍 Access your application at:"
    echo "   Local: http://localhost:${LISTEN_PORT}"
    echo "   Public: ${PUBLIC_URL}"
    if [ -n "${WEBRTC_UDP_HOSTNAME}" ]; then
        echo "   UDP Endpoint: ${WEBRTC_UDP_HOSTNAME}:${WEBRTC_UDP_PORT_MIN}-${WEBRTC_UDP_PORT_MAX}"
    elif [ -n "${WEBRTC_UDP_IP}" ]; then
        echo "   UDP Endpoint: ${WEBRTC_UDP_IP}:${WEBRTC_UDP_PORT_MIN}-${WEBRTC_UDP_PORT_MAX}"
    fi
    echo ""
    echo "📊 Usage:"
    echo "   1. Open the URL in your browser"
    echo "   2. Click 'Run Speed Test' to measure your connection"
    echo "   3. Click 'Run Bufferbloat Test' to test for buffer bloat"
    echo "   4. Review your score and metrics"
    echo ""
    echo "🔧 Management commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Stop: docker-compose down"
    echo "   Restart: docker-compose restart"
    echo "   Update: git pull && docker-compose build && docker-compose up -d"
    echo ""
    echo "🔥 Firewall reminder:"
    echo "   Make sure these ports are open:"
    echo "   - TCP 80/443 (reverse proxy for public access)"
    echo "   - TCP ${LISTEN_PORT} (container port, reverse proxy access)"
    if [ -n "${WEBRTC_UDP_HOSTNAME}" ]; then
        echo "   - UDP ${WEBRTC_UDP_PORT_MIN}-${WEBRTC_UDP_PORT_MAX} (WebRTC on ${WEBRTC_UDP_HOSTNAME})"
    elif [ -n "${WEBRTC_UDP_IP}" ]; then
        echo "   - UDP ${WEBRTC_UDP_PORT_MIN}-${WEBRTC_UDP_PORT_MAX} (WebRTC on ${WEBRTC_UDP_IP})"
    else
        echo "   - UDP ${WEBRTC_UDP_PORT_MIN}-${WEBRTC_UDP_PORT_MAX} (WebRTC)"
    fi
else
    echo "❌ Application failed to start. Check logs with:"
    echo "   docker-compose logs"
    exit 1
fi