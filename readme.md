# Bufferbloat Tester

A simple web-based tool to test for bufferbloat on your network. This application measures your connection speed and then tests for latency increases under load to detect buffer bloat issues.

## Features

- **Speed Testing**: Measures upload and download speeds via HTTP
- **Bufferbloat Detection**: Tests latency increase under network load
- **WebRTC Data Channels**: Uses UDP-like transmission for accurate packet loss measurement
- **Simple Scoring**: Provides an easy-to-understand score and metrics
- **Docker Deployment**: Fully containerized with configurable environment variables
- **No Client Installation**: Runs entirely in the browser

## How It Works

1. **Speed Test**: Measures your baseline upload/download speeds
2. **Baseline Latency**: Establishes normal latency via WebRTC data channels
3. **Load Test**: Saturates the connection at 80% of download speed while measuring latency
4. **Analysis**: Compares loaded vs. baseline latency to detect bufferbloat

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bufferbloat-tester
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   Open your browser to `http://localhost:3000` (or your configured URL)

## HTTP vs UDP Traffic Separation

This application supports different hostnames/IPs for HTTP and UDP traffic, which is common in production deployments:

- **HTTP Traffic**: Web interface, speed tests, WebRTC signaling → Goes through reverse proxy
- **UDP Traffic**: WebRTC data channels for bufferbloat testing → Direct to server

### Why Separate Them?

1. **Reverse Proxy Limitations**: nginx/Apache can't proxy UDP traffic
2. **Performance**: Direct UDP connection reduces latency for accurate measurements  
3. **Firewall**: Different rules for web traffic vs. testing traffic
4. **Load Balancing**: Web traffic can be load balanced, UDP testing should be direct

### Configuration Example

```env
# Web traffic through reverse proxy
PUBLIC_HTTP_URL=https://bufferbloat.example.com
PUBLIC_HTTPS_URL=https://bufferbloat.example.com

# Direct connection for UDP testing  
WEBRTC_UDP_HOSTNAME=server.example.com
# OR direct IP:
# WEBRTC_UDP_IP=203.0.113.10
```

The application automatically handles the routing - users connect via the public URLs but WebRTC data channels use the direct UDP endpoint.

## Configuration

All configuration is done via environment variables in the `.env` file:

### Container Configuration
- `LISTEN_PORT`: Port for the application to listen on inside Docker container (default: 8080)
- `PUBLIC_URL`: Public URL for the application as accessed by users (no port needed if using standard 80/443)

### WebRTC Configuration
- `WEBRTC_UDP_HOSTNAME`: Hostname for direct UDP connections (can differ from HTTP hostname)
- `WEBRTC_UDP_IP`: Alternative - direct IP address for UDP connections  
- `WEBRTC_UDP_PORT_MIN`: Start of UDP port range (default: 10000)
- `WEBRTC_UDP_PORT_MAX`: End of UDP port range (default: 10100)

### Test Parameters
- `DEFAULT_TEST_DURATION`: Duration of bufferbloat test in seconds (default: 30)
- `DEFAULT_PACKET_SIZE`: Size of test packets in bytes (default: 1024)
- `DEFAULT_PACKET_RATE`: Rate of test packets per second (default: 100)

### Example .env Configuration

**Basic configuration (same hostname for HTTP and UDP):**
```env
LISTEN_PORT=8080
PUBLIC_URL=https://bufferbloat.yourdomain.com
WEBRTC_UDP_HOSTNAME=bufferbloat.yourdomain.com
WEBRTC_UDP_PORT_MIN=10000
WEBRTC_UDP_PORT_MAX=10100
```

**Advanced configuration (separate hostnames for HTTP vs UDP):**
```env
# Container listens on port 8080, reverse proxy forwards from 443→8080
LISTEN_PORT=8080
PUBLIC_URL=https://bufferbloat.example.com

# UDP traffic goes directly to server (bypassing reverse proxy)
WEBRTC_UDP_HOSTNAME=direct.example.com
# OR use direct IP address:
# WEBRTC_UDP_IP=203.0.113.10

WEBRTC_UDP_PORT_MIN=10000
WEBRTC_UDP_PORT_MAX=10100
NODE_ENV=production
LOG_LEVEL=info
```

## Nginx Reverse Proxy Setup

If you're using nginx as a reverse proxy, here's a sample configuration:

```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name bufferbloat.yourdomain.com;

    # SSL configuration (if using HTTPS)
    # ssl_certificate /path/to/cert.pem;
    # ssl_certificate_key /path/to/key.pem;

    location / {
        # Forward to container on port 8080
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support for Socket.IO
    location /socket.io/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Firewall Configuration

Make sure the following ports are open:

- **Reverse Proxy Ports** (80, 443): For web interface access
- **Container Port** (default 8080): For reverse proxy → container communication  
- **UDP Port Range** (default 10000-10100): For WebRTC data channels

Example iptables rules:
```bash
# Allow web traffic to reverse proxy
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow reverse proxy to reach container (if on same host)
iptables -A INPUT -p tcp --dport 8080 -s 127.0.0.1 -j ACCEPT

# Allow WebRTC UDP traffic (direct to server)
iptables -A INPUT -p udp --dport 10000:10100 -j ACCEPT
```

## Understanding the Results

### Speed Test
- **Download Speed**: Your connection's download capacity
- **Upload Speed**: Your connection's upload capacity  
- **Test Target**: 80% of download speed (used for load testing)

### Bufferbloat Test
- **Baseline Latency**: Normal latency when network is idle
- **Loaded Latency**: Latency when network is under 80% load
- **Latency Increase**: The difference (this is bufferbloat)
- **Packet Loss**: Percentage of packets lost during test
- **Jitter**: Variation in packet delivery times

### Scoring
- **Excellent (90-100)**: No significant bufferbloat detected
- **Good (70-89)**: Minor bufferbloat, network performs well under load
- **Fair (50-69)**: Moderate bufferbloat, consider equipment upgrade
- **Poor (0-49)**: Severe bufferbloat, significant buffer issues detected

## Troubleshooting

### WebRTC Connection Issues
- Ensure UDP ports are open in firewall
- Check that Docker port mapping matches your environment configuration
- For internal networks, the default direct connection should work
- If behind NAT, you may need STUN/TURN servers (not implemented in this simple version)

### Speed Test Issues
- Verify the application can reach the configured public URLs
- Check that your reverse proxy is correctly forwarding requests
- Ensure sufficient bandwidth between client and server

### Docker Issues
- Check logs: `docker-compose logs bufferbloat-tester`
- Verify environment variables: `docker-compose config`
- Ensure ports aren't already in use: `netstat -tlnp | grep :3000`

## Development

To run in development mode:

```bash
# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Run in development mode
npm run dev
```

## License

MIT License - see LICENSE file for details.

## Contributing

Pull requests welcome! Please ensure:
- Code follows existing style
- All environment variables are configurable
- Docker deployment works
- Documentation is updated