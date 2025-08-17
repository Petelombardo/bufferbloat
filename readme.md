# 🌐 Bufferbloat Network Quality Test

A comprehensive network quality testing tool that measures **bufferbloat** - the hidden performance killer that affects real-world internet experience even when you have plenty of bandwidth.

![Network Quality Test Interface](https://img.shields.io/badge/Grade-A+-brightgreen) ![Node.js](https://img.shields.io/badge/Node.js-18+-green) ![License](https://img.shields.io/badge/License-MIT-blue)

## 🎯 What is Bufferbloat?

**Bufferbloat** occurs when network equipment (routers, modems, ISP infrastructure) buffers too much data, causing latency spikes under load. You might have fast internet speeds but still experience:

- 🎮 **Gaming lag** during downloads/uploads
- 📹 **Video call stuttering** when others use the network  
- 🌐 **Slow web browsing** despite high bandwidth
- 📱 **Poor responsiveness** on mobile devices

Unlike simple speed tests, this tool measures how your **latency changes under load** to detect bufferbloat and provide an overall network quality grade.

## ✨ Features

### 🔍 **Comprehensive Testing**
- **Upload & Download Speed Tests** - Measure raw bandwidth
- **Baseline Latency Measurement** - Establish unloaded performance
- **Bufferbloat Detection** - Test latency under realistic load conditions
- **Jitter Analysis** - Measure latency variation for consistency

### 📊 **Smart Grading System**
- **A+ to F grades** based on real-world performance impact
- **Separate analysis** for upload and download directions
- **Data quality validation** ensures reliable measurements
- **Severity classification** from Minimal to Severe bufferbloat

### 🛠 **Advanced Features**
- **Environment detection** - Optimized for localhost and remote testing
- **Bandwidth limiting** - Server-side throttling for controlled testing
- **WebSocket + HTTP measurement** - Dual protocols for reliability
- **Real-time progress** with detailed status updates

## 🚀 Quick Start

### Prerequisites
- **Node.js 18+**
- **npm** or **yarn**

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/bufferbloat-test.git
cd bufferbloat-test

# Install dependencies
npm install

# Start the server
npm start
```

### Using Docker

```bash
# Build the container
docker build -t bufferbloat-test .

# Run with default settings
docker run -p 8081:8081 bufferbloat-test

# Run with custom configuration
docker run -p 8081:8081 -e MAX_DOWNLOAD_MBPS=100 -e MAX_UPLOAD_MBPS=50 bufferbloat-test
```

### Access the Test

Open your browser to: **http://localhost:8081**

## ⚙️ Configuration

Configure the server using environment variables:

```bash
# Server settings
LISTEN_PORT=8081                    # Port to listen on
PUBLIC_URL=http://localhost:8081    # Public URL for the service

# Bandwidth limiting (optional)
MAX_DOWNLOAD_MBPS=100              # Limit download test speed
MAX_UPLOAD_MBPS=50                 # Limit upload test speed

# Test parameters (optional)
DEFAULT_TEST_DURATION=30           # Default test duration in seconds
DEFAULT_PACKET_SIZE=1024          # Default packet size in bytes
DEFAULT_PACKET_RATE=100           # Default packet rate per second
```

### Example with bandwidth limits:
```bash
# Simulate a 100/50 Mbps connection
MAX_DOWNLOAD_MBPS=100 MAX_UPLOAD_MBPS=50 npm start
```

## 📈 Understanding Your Results

### 🏆 **Grade Scale**
| Grade | Description | Characteristics |
|-------|-------------|----------------|
| **A+** | Excellent | < 3ms jitter, < 10ms latency increase |
| **A**  | Very Good | < 8ms jitter, < 25ms latency increase |
| **B+** | Good+ | < 15ms jitter, < 50ms latency increase |
| **B**  | Good | < 25ms jitter, < 100ms latency increase |
| **C**  | Fair | < 40ms jitter, < 200ms latency increase |
| **D**  | Poor | < 80ms jitter, < 500ms latency increase |
| **F**  | Failed | Severe bufferbloat or test failure |

### 📊 **Key Metrics**

**Jitter** - Latency variation during the test
- Lower is better (< 5ms is excellent)
- High jitter indicates unstable connections

**Latency Increase** - How much latency rises under load  
- Lower is better (< 20ms is excellent)
- High increase indicates bufferbloat

**Bufferbloat Severity** - Overall impact assessment
- Minimal, Low, Moderate, High, Severe

### 🎯 **What Good Results Look Like**
```
📤 Upload: A+ (95/100)
- Jitter: 2.1ms  
- Latency Increase: 8.3ms
- Bufferbloat: Minimal

📥 Download: A (87/100)  
- Jitter: 4.7ms
- Latency Increase: 15.2ms  
- Bufferbloat: Low
```

## 🔧 API Endpoints

### Testing Endpoints
```
GET  /api/config          # Get server configuration
GET  /api/download/:size  # Download speed test  
POST /api/upload          # Upload speed test
GET  /api/ping           # Latency measurement
POST /api/load-chunk     # Load generation
GET  /api/health         # Health check
```

### WebSocket Events
```
ping/pong                # Real-time latency measurement
start-bufferbloat-test   # Begin bufferbloat testing
load-data/load-response  # Load generation with timing
test-complete           # Test completion notification
```

## 🏗️ Technical Architecture

### **Measurement Strategy**
1. **Speed Tests** - Establish baseline bandwidth capabilities
2. **Baseline Latency** - Measure unloaded network performance  
3. **Load Generation** - Create realistic traffic patterns
4. **Under-Load Measurement** - Monitor latency during saturation

### **Dual Protocol Approach**
- **WebSocket** - Low-latency real-time measurement
- **HTTP** - Reliable fallback for congested networks
- **Auto-switching** - Uses HTTP when WebSocket is blocked

### **Environment Optimization**
- **Localhost Detection** - Reduced load for local testing
- **Adaptive Parameters** - Chunk sizes and intervals adjust automatically
- **Quality Validation** - Ensures sufficient samples for reliability

## 🐛 Troubleshooting

### **Common Issues**

**"Only 1 ping sample" / F grades with good network**
- The upload load is too aggressive
- Try the HTTP-based upload test function
- Reduce chunk sizes for localhost testing

**"No latency measurements received"**
- Check firewall settings for WebSocket connections
- Verify server is accessible on the configured port
- Try browser developer tools to check for errors

**Tests timing out**
- Increase timeout values in server configuration
- Check for network connectivity issues
- Reduce test duration for slower connections

**Inconsistent results**
- Run multiple tests to average results
- Check for background network activity
- Ensure stable network conditions during testing

### **Debug Mode**

Enable verbose logging by opening browser developer console:
```javascript
// View detailed test progress
console.log(testResults);

// Monitor network requests
// Check Network tab in DevTools
```

## 📝 Development

### **Adding New Tests**
```javascript
// Template for new test functions
async function runCustomTest(parameters) {
    return new Promise((resolve) => {
        // Test implementation
        resolve({
            avgLatency: 0,
            pingCount: 0, 
            jitter: 0,
            dataQuality: 'good'
        });
    });
}
```

### **Customizing Grading**
Modify the `calculateGrade()` function in `index.html` to adjust:
- Jitter thresholds
- Latency increase thresholds  
- Grade boundaries
- Data quality requirements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the work of Jim Gettys and others on bufferbloat research
- Built with modern web standards for accurate network measurement
- Thanks to the open source community for networking tools and libraries

---

**Ready to test your network quality?** 🚀  
**[Run the test now →](http://localhost:8081)**