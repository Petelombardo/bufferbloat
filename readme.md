# 📡 Bufferbloat Network Tester

A containerized web application for testing network bufferbloat using HTTP-based latency measurements. This tool helps identify if your network equipment is causing unnecessary delays during high bandwidth usage.

## What is Bufferbloat?

Bufferbloat occurs when network equipment (routers, modems) buffer too much data, causing high latency and jitter during periods of network congestion. This can make your internet feel sluggish for real-time applications like:

- Video calls (Zoom, Teams, etc.)
- Online gaming
- VoIP phone calls
- Live streaming

## How It Works

This tool measures bufferbloat by:

1. **Measuring baseline latency** when your network is idle
2. **Generating sustained, throttled network load** with multiple continuous download streams (~10 Mbps each)
3. **Measuring latency under load** during the bandwidth test  
4. **Calculating a bufferbloat score** based on latency increase

The scoring system:
- **A+/A**: Excellent - minimal bufferbloat
- **B**: Good - slight increase acceptable 
- **C**: Fair - noticeable but manageable
- **D/F**: Poor - significant bufferbloat problems

## Quick Start

### Prerequisites
- Docker installed on your system
- A device connected to the network you want to test

### ⚠️ Important: Testing Real Networks vs Localhost

**For REAL bufferbloat testing:** Deploy the container on one device and access it from another device on your network. Testing `localhost` only measures application performance, not network bufferbloat.

**Example Setup:**
- Deploy container on: Raspberry Pi with Ethernet connection
- Test from: WiFi laptop accessing `http://pi-ip:8080`

### Option 1: Docker Run (Simplest)

```bash
# Build the container
docker build -t bufferbloat-tester .

# Run the container
docker run -d -p 8080:8080 --name bufferbloat-tester bufferbloat-tester

# Access the web interface
open http://localhost:8080
```

### Option 2: Docker Compose (Recommended)

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Option 3: Production Setup with Nginx

```bash
# Run with nginx proxy (optional)
docker-compose --profile production up -d
```

## Usage

1. **Open your browser** and navigate to `http://your-server-ip:8080`
2. **Click "Start Network Test"** to begin the bufferbloat measurement
3. **Wait 20-30 seconds** for the test to complete
4. **Review your results** and bufferbloat grade

### Understanding Your Results

- **Idle Latency**: Your network's baseline response time
- **Loaded Latency**: Response time when bandwidth is saturated  
- **Latency Increase**: How much latency increased (lower is better)
- **Jitter**: Variability in response times (lower is better)

## Deployment Options

### Testing Your Home WiFi (Recommended Setup)

Deploy on a wired device and test from WiFi devices:

```bash
# On your Pi/server connected via Ethernet
git clone <this-repo>
cd bufferbloat-tester
docker-compose up -d

# Test from WiFi devices by visiting:
# http://your-pi-ip:8080
# NOT http://localhost:8080 (this won't test network bufferbloat)
```

**Why this setup?** The test traffic must pass through your router's WiFi and buffering mechanisms. Testing localhost bypasses the network entirely.

### Corporate Network Testing

Deploy on a server within your corporate LAN to test from various network segments.

### Cloud Testing

Deploy on a cloud instance to test the performance of your internet connection from different geographic locations.

## Configuration

### Environment Variables

- `HOST`: Bind address (default: 0.0.0.0)
- `PORT`: Port to listen on (default: 8080)

### Customizing Test Parameters

Edit `app.py` to adjust:
- **Number of concurrent streams** (default: 6)
- **Test duration** (default: 15 seconds)  
- **Download size per stream** (default: 50MB)
- **Measurement interval** (default: 300ms)

## API Endpoints

- `GET /` - Web interface
- `GET /api/ping` - Latency measurement endpoint
- `GET /api/download/<megabytes>` - Download test endpoint
- `POST /api/upload` - Upload test endpoint
- `GET /health` - Health check

## Troubleshooting

### "I Got Grade F But I'm Testing Localhost"

**This is expected!** Testing `localhost` or `127.0.0.1` measures application performance, not network bufferbloat. The Flask app can get overwhelmed by concurrent requests, simulating bufferbloat symptoms.

**Solution:** Deploy on one device, test from another:
```bash
# Find your server's IP address
ip addr show | grep inet

# Access from other devices using the real IP
http://192.168.1.100:8080  # Not localhost:8080
```

### Test Always Shows "A+" Grade

- **Check if you're testing the right link**: Make sure the test traffic goes through the network segment you want to test
- **Increase load**: Try testing from multiple devices simultaneously
- **Check bandwidth**: Ensure your test is actually saturating the connection

### Test Fails or Times Out

- **Firewall issues**: Ensure port 8080 is accessible
- **Resource limits**: The container needs sufficient CPU/memory for multiple streams
- **Network isolation**: Ensure containers can reach each other

### Inconsistent Results

- **Background traffic**: Pause other network activity during testing
- **WiFi interference**: Test when the network is quiet
- **Multiple tests**: Run several tests and average the results

## Technical Details

### Why HTTP Instead of Ping?

Browsers cannot send raw ICMP ping packets due to security restrictions. This tool uses HTTP requests to measure latency, which adds some overhead but still effectively detects bufferbloat.

### Accuracy Considerations

- HTTP-based measurements include TCP handshake overhead
- Results may vary compared to native ping/netperf tools
- The tool is optimized for detecting relative latency increases under load

### Security

- Runs as non-root user inside container
- No data is stored or logged permanently  
- All test traffic is discarded immediately

## Contributing

Contributions welcome! Areas for improvement:

- Additional test protocols (WebSocket, WebRTC)
- Historical data storage and graphing
- Mobile-optimized interface
- Integration with network monitoring tools

## License

MIT License - feel free to modify and distribute.

## Credits

Inspired by the excellent work of:
- [Bufferbloat.net project](https://www.bufferbloat.net/)
- [Flent network tester](https://flent.org/)
- [Waveform bufferbloat test](https://www.waveform.com/tools/bufferbloat)
