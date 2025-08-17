require('dotenv').config();
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const path = require('path');
const crypto = require('crypto');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Configuration from environment
const config = {
  listenPort: parseInt(process.env.LISTEN_PORT) || 8081,
  publicUrl: process.env.PUBLIC_URL || `http://localhost:${process.env.LISTEN_PORT || 8081}`,
  maxDownloadMbps: process.env.MAX_DOWNLOAD_MBPS ? parseFloat(process.env.MAX_DOWNLOAD_MBPS) : null,
  maxUploadMbps: process.env.MAX_UPLOAD_MBPS ? parseFloat(process.env.MAX_UPLOAD_MBPS) : null,
  testDuration: parseInt(process.env.DEFAULT_TEST_DURATION) || 30,
  packetSize: parseInt(process.env.DEFAULT_PACKET_SIZE) || 1024,
  packetRate: parseInt(process.env.DEFAULT_PACKET_RATE) || 100
};

console.log('Starting Bufferbloat Tester with config:', config);

app.use(cors());
app.use(express.static(path.join(__dirname, 'public')));

// JSON parser for specific routes only
app.use('/api/config', express.json());

// Raw body parser only for load testing
app.use('/api/load-chunk', express.raw({ limit: '100mb', type: 'application/octet-stream' }));

// Speed test endpoints
app.get('/api/config', (req, res) => {
  res.json({
    publicUrl: config.publicUrl,
    maxDownloadMbps: config.maxDownloadMbps,
    maxUploadMbps: config.maxUploadMbps,
    testDuration: config.testDuration,
    packetSize: config.packetSize,
    packetRate: config.packetRate
  });
});

// Download speed test - serve random data with optional bandwidth limiting
app.get('/api/download/:size', (req, res) => {
  const requestedSize = Math.min(parseInt(req.params.size) || 1024, 100 * 1024 * 1024); // Max 100MB
  
  res.setHeader('Content-Type', 'application/octet-stream');
  res.setHeader('Cache-Control', 'no-cache');
  
  if (config.maxDownloadMbps) {
    // Bandwidth-limited download
    const maxBytesPerSecond = (config.maxDownloadMbps * 1024 * 1024) / 8; // Convert Mbps to bytes/sec
    const chunkSize = Math.min(256 * 1024, requestedSize); // 256KB chunks or smaller
    const chunkDelayMs = (chunkSize / maxBytesPerSecond) * 1000; // Time between chunks
    
    console.log(`Bandwidth-limited download: ${config.maxDownloadMbps} Mbps max, ${chunkSize} byte chunks, ${chunkDelayMs.toFixed(1)}ms delay`);
    
    let sentBytes = 0;
    const startTime = Date.now();
    
    res.setHeader('Content-Length', requestedSize);
    
    const sendChunk = () => {
      if (sentBytes >= requestedSize) {
        res.end();
        const actualDuration = (Date.now() - startTime) / 1000;
        const actualMbps = (requestedSize * 8) / (actualDuration * 1000000);
        console.log(`Download completed: ${requestedSize} bytes in ${actualDuration.toFixed(1)}s = ${actualMbps.toFixed(2)} Mbps`);
        return;
      }
      
      const remainingBytes = requestedSize - sentBytes;
      const currentChunkSize = Math.min(chunkSize, remainingBytes);
      const chunk = crypto.randomBytes(currentChunkSize);
      
      res.write(chunk);
      sentBytes += currentChunkSize;
      
      setTimeout(sendChunk, chunkDelayMs);
    };
    
    sendChunk();
    
  } else {
    // Unlimited download (original behavior)
    const data = crypto.randomBytes(requestedSize);
    res.setHeader('Content-Length', requestedSize);
    res.send(data);
  }
});

// Upload speed test - receive streaming data with optional bandwidth limiting
app.post('/api/upload', (req, res) => {
  let dataReceived = 0;
  const startTime = Date.now();
  
  console.log('Upload test started');
  
  // Timeout after 30 seconds
  const timeout = setTimeout(() => {
    console.error('Upload test timeout');
    if (!res.headersSent) {
      res.status(408).json({ error: 'Upload test timeout' });
    }
  }, 30000);
  
  if (config.maxUploadMbps) {
    // Bandwidth-limited upload - throttle the server's data consumption
    const maxBytesPerSecond = (config.maxUploadMbps * 1024 * 1024) / 8;
    const chunkSize = 64 * 1024; // 64KB processing chunks
    const chunkDelayMs = (chunkSize / maxBytesPerSecond) * 1000;
    
    console.log(`Upload bandwidth limited to ${config.maxUploadMbps} Mbps, processing ${chunkSize} byte chunks with ${chunkDelayMs.toFixed(1)}ms delay`);
    
    let buffer = Buffer.alloc(0);
    let processing = false;
    
    const processBuffer = () => {
      if (processing || buffer.length === 0) return;
      processing = true;
      
      const currentChunk = buffer.slice(0, Math.min(chunkSize, buffer.length));
      buffer = buffer.slice(currentChunk.length);
      dataReceived += currentChunk.length;
      
      setTimeout(() => {
        processing = false;
        if (buffer.length > 0) {
          processBuffer();
        }
      }, chunkDelayMs);
    };
    
    req.on('data', chunk => {
      buffer = Buffer.concat([buffer, chunk]);
      processBuffer();
    });
    
    req.on('end', () => {
      // Process any remaining buffer
      const finalProcess = () => {
        if (buffer.length > 0) {
          dataReceived += buffer.length;
          buffer = Buffer.alloc(0);
        }
        
        clearTimeout(timeout);
        const duration = Date.now() - startTime;
        const speedMbps = (dataReceived * 8) / (duration * 1000);
        
        console.log(`Upload test completed (limited): ${dataReceived} bytes in ${duration}ms = ${speedMbps.toFixed(2)} Mbps`);
        
        if (!res.headersSent) {
          res.json({
            bytesReceived: dataReceived,
            durationMs: duration,
            speedMbps: speedMbps,
            limited: true,
            maxConfiguredMbps: config.maxUploadMbps
          });
        }
      };
      
      // Wait for buffer to be fully processed
      const waitForBuffer = () => {
        if (buffer.length === 0 && !processing) {
          finalProcess();
        } else {
          setTimeout(waitForBuffer, 50);
        }
      };
      waitForBuffer();
    });
    
  } else {
    // Unlimited upload (original behavior)
    req.on('data', chunk => {
      dataReceived += chunk.length;
    });
    
    req.on('end', () => {
      clearTimeout(timeout);
      
      const duration = Date.now() - startTime;
      const speedMbps = (dataReceived * 8) / (duration * 1000);
      
      console.log(`Upload test completed: ${dataReceived} bytes in ${duration}ms = ${speedMbps.toFixed(2)} Mbps`);
      
      if (!res.headersSent) {
        res.json({
          bytesReceived: dataReceived,
          durationMs: duration,
          speedMbps: speedMbps,
          limited: false
        });
      }
    });
  }
  
  req.on('error', (error) => {
    clearTimeout(timeout);
    console.error('Upload test error:', error);
    if (!res.headersSent) {
      res.status(500).json({ error: 'Upload test failed' });
    }
  });
});

// Load generation endpoint for bufferbloat testing
app.post('/api/load-chunk', (req, res) => {
  const receivedSize = req.body ? req.body.length : 0;
  const timestamp = Date.now();
  
  // Send back a small response with timestamp
  res.json({
    timestamp: timestamp,
    receivedSize: receivedSize,
    responseTime: timestamp
  });
});

// Latency test endpoint (small, fast responses)
app.get('/api/ping', (req, res) => {
  const timestamp = req.query.timestamp ? parseInt(req.query.timestamp) : Date.now();
  const serverTime = Date.now();
  
  res.json({
    clientTimestamp: timestamp,
    serverTimestamp: serverTime,
    responseTime: serverTime
  });
});

// WebSocket-based real-time testing
const activeConnections = new Map();

io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);
  activeConnections.set(socket.id, {
    socket: socket,
    connectedAt: Date.now()
  });
  
  // Real-time ping-pong for latency measurement
  socket.on('ping', (data) => {
    const serverTimestamp = Date.now();
    socket.emit('pong', {
      ...data,
      serverTimestamp: serverTimestamp,
      responseTime: serverTimestamp
    });
  });
  
  // Start bufferbloat test
  socket.on('start-bufferbloat-test', (testConfig) => {
    console.log('Starting bufferbloat test for client:', socket.id);
    
    const connection = activeConnections.get(socket.id);
    if (connection) {
      connection.testStarted = Date.now();
      connection.testConfig = testConfig;
      
      // Confirm test started
      socket.emit('test-started', {
        serverTime: Date.now(),
        testId: socket.id
      });
    }
  });
  
  // Handle load test data
  socket.on('load-data', (data) => {
    const serverTime = Date.now();
    
    // Echo back with server timestamp for latency calculation
    socket.emit('load-response', {
      clientTimestamp: data.timestamp || serverTime,
      serverTimestamp: serverTime,
      sequence: data.sequence || 0,
      size: data.size || 0
    });
  });
  
  // Handle test completion
  socket.on('test-complete', (results) => {
    console.log('Test completed for client:', socket.id, 'Results:', results);
    
    // Store results or process them
    const connection = activeConnections.get(socket.id);
    if (connection) {
      connection.testCompleted = Date.now();
      connection.results = results;
    }
  });
  
  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
    activeConnections.delete(socket.id);
  });
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: Date.now(),
    connections: activeConnections.size,
    config: config
  });
});

server.listen(config.listenPort, () => {
  console.log(`Bufferbloat Tester running on port ${config.listenPort}`);
  console.log(`Public URL: ${config.publicUrl}`);
  console.log(`WebSocket endpoint available for real-time testing`);
  
  if (config.maxDownloadMbps || config.maxUploadMbps) {
    console.log('Bandwidth limits configured:');
    if (config.maxDownloadMbps) {
      console.log(`  - Max Download: ${config.maxDownloadMbps} Mbps`);
    }
    if (config.maxUploadMbps) {
      console.log(`  - Max Upload: ${config.maxUploadMbps} Mbps`);
    }
  } else {
    console.log('No bandwidth limits configured - tests will use full available bandwidth');
  }
});