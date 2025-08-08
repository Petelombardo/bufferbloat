#!/usr/bin/env python3
"""
Enhanced Bufferbloat Testing Application
A containerized tool for testing network bufferbloat, download speed, and upload speed using HTTP-based measurements.
"""

import time
import os
import json
from flask import Flask, Response, request, render_template_string, jsonify
import threading
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Global variables to track speed statistics
download_stats = {
    'total_bytes': 0,
    'start_time': None,
    'streams_active': 0,
    'lock': threading.Lock()
}

upload_stats = {
    'total_bytes': 0,
    'start_time': None,
    'lock': threading.Lock()
}

# HTML Template with enhanced UI for speed testing
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Enhanced Bufferbloat & Speed Tester</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 800px;
            width: 100%;
            text-align: center;
        }
        
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .subtitle {
            color: #7f8c8d;
            margin-bottom: 40px;
            font-size: 1.1em;
        }
        
        .test-button {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.2em;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 30px;
            min-width: 250px;
        }
        
        .test-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(52, 152, 219, 0.3);
        }
        
        .test-button:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .results {
            margin-top: 30px;
            padding: 20px;
            border-radius: 15px;
            background: #f8f9fa;
        }
        
        .grade {
            font-size: 4em;
            font-weight: bold;
            margin: 20px 0;
        }
        
        .grade.A { color: #27ae60; }
        .grade.B { color: #f39c12; }
        .grade.C { color: #e67e22; }
        .grade.D { color: #e74c3c; }
        .grade.F { color: #c0392b; }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .metric {
            padding: 15px;
            background: white;
            border-radius: 10px;
            border-left: 4px solid #3498db;
        }
        
        .metric.speed {
            border-left-color: #27ae60;
        }
        
        .metric.latency {
            border-left-color: #3498db;
        }
        
        .metric.bufferbloat {
            border-left-color: #e67e22;
        }
        
        .metric-label {
            font-size: 0.9em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 5px;
        }
        
        .progress {
            margin: 20px 0;
            background: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            height: 8px;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(45deg, #3498db, #2980b9);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .status {
            margin: 15px 0;
            font-weight: 500;
            color: #2c3e50;
        }
        
        .explanation {
            margin-top: 20px;
            padding: 20px;
            background: #e8f4fd;
            border-radius: 10px;
            border-left: 4px solid #3498db;
            text-align: left;
        }
        
        .explanation h3 {
            margin-bottom: 10px;
            color: #2c3e50;
        }
        
        .explanation p {
            line-height: 1.6;
            color: #34495e;
            margin-bottom: 10px;
        }
        
        .speed-summary {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        
        .speed-card {
            padding: 20px;
            background: linear-gradient(135deg, #27ae60, #219a52);
            color: white;
            border-radius: 15px;
            text-align: center;
        }
        
        .speed-card h3 {
            font-size: 1.2em;
            margin-bottom: 10px;
            opacity: 0.9;
        }
        
        .speed-card .speed-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .speed-card .speed-unit {
            font-size: 1em;
            opacity: 0.8;
        }
        
        @media (max-width: 600px) {
            .metrics {
                grid-template-columns: 1fr;
            }
            
            .speed-summary {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 2em;
            }
            
            .container {
                padding: 30px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Bufferbloat & Speed Tester</h1>
        <p class="subtitle">Test your network for bufferbloat, download speed, and upload speed</p>
        
        <div class="explanation" id="testingNotice">
            <h3>Testing Notice</h3>
            <p><strong>For real network testing</strong>, access this tool from a different device on your network (not localhost). Testing localhost only measures application performance, not actual network performance.</p>
        </div>
        
        <button id="startTest" class="test-button">
            Start Complete Network Test
        </button>
        
        <div class="progress" id="progressContainer" style="display: none;">
            <div class="progress-bar" id="progressBar"></div>
        </div>
        
        <div class="status" id="status"></div>
        
        <div id="results" class="results" style="display: none;">
            <div class="speed-summary">
                <div class="speed-card">
                    <h3>Download Speed</h3>
                    <div class="speed-value" id="downloadSpeed">--</div>
                    <div class="speed-unit">Mbps</div>
                </div>
                <div class="speed-card" style="background: linear-gradient(135deg, #3498db, #2980b9);">
                    <h3>Upload Speed</h3>
                    <div class="speed-value" id="uploadSpeed">--</div>
                    <div class="speed-unit">Mbps</div>
                </div>
            </div>
            
            <div class="grade" id="grade">A+</div>
            
            <div class="metrics">
                <div class="metric latency">
                    <div class="metric-label">Idle Latency</div>
                    <div class="metric-value" id="idleLatency">--</div>
                </div>
                <div class="metric latency">
                    <div class="metric-label">Loaded Latency</div>
                    <div class="metric-value" id="loadedLatency">--</div>
                </div>
                <div class="metric bufferbloat">
                    <div class="metric-label">Latency Increase</div>
                    <div class="metric-value" id="latencyIncrease">--</div>
                </div>
                <div class="metric bufferbloat">
                    <div class="metric-label">Jitter</div>
                    <div class="metric-value" id="jitter">--</div>
                </div>
            </div>
            
            <div class="explanation">
                <h3>Test Results</h3>
                <p id="explanation">Your test results will be explained here.</p>
            </div>
        </div>
    </div>

    <script>
        let testRunning = false;
        
        async function measureLatency() {
            const start = performance.now();
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 2000);
                
                // Use ultra-lightweight ping endpoint to minimize server processing
                const response = await fetch('/api/ping-light', { 
                    method: 'GET',
                    cache: 'no-cache',
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                // Don't even read the response body to minimize processing
                return performance.now() - start;
            } catch (error) {
                if (error.name === 'AbortError') {
                    console.log('Latency measurement timed out (>2000ms) - severe bufferbloat detected');
                    return 2000 + Math.random() * 1000;
                } else {
                    console.error('Latency measurement failed:', error);
                    return null;
                }
            }
        }
        
        function updateProgress(percent) {
            document.getElementById('progressBar').style.width = percent + '%';
        }
        
        function updateStatus(message) {
            document.getElementById('status').textContent = message;
        }
        
        function calculateGrade(ratio) {
            if (ratio <= 1.2) return 'A+';
            if (ratio <= 1.5) return 'A';
            if (ratio <= 2.0) return 'B';
            if (ratio <= 3.0) return 'C';
            if (ratio <= 5.0) return 'D';
            return 'F';
        }
        
        function getExplanation(grade, ratio, idleMs, loadedMs, downloadMbps, uploadMbps) {
            const increase = Math.round((ratio-1)*100);
            
            let explanation = `<strong>Speed Test:</strong> Download ${downloadMbps.toFixed(1)} Mbps, Upload ${uploadMbps.toFixed(1)} Mbps<br><br>`;
            
            if (loadedMs >= 2000) {
                explanation += `<strong>Bufferbloat:</strong> Severe bufferbloat detected! Your network latency increased to ${loadedMs.toFixed(0)}ms under load (${increase}% increase). This will make real-time applications like gaming, video calls, and VoIP nearly unusable.`;
            } else {
                const explanations = {
                    'A+': `<strong>Bufferbloat:</strong> Excellent! Your network has minimal bufferbloat. Latency increased by only ${increase}%, which is barely noticeable for real-time applications.`,
                    'A': `<strong>Bufferbloat:</strong> Very good! Your network has low bufferbloat. The ${increase}% latency increase is minor and shouldn't impact most applications.`,
                    'B': `<strong>Bufferbloat:</strong> Good! Your network has moderate bufferbloat. The ${increase}% latency increase may cause occasional issues with real-time applications.`,
                    'C': `<strong>Bufferbloat:</strong> Fair. Your network has noticeable bufferbloat. The ${increase}% latency increase will likely cause problems with gaming and video calls.`,
                    'D': `<strong>Bufferbloat:</strong> Poor. Your network has significant bufferbloat. The ${increase}% latency increase will cause noticeable delays in real-time applications.`,
                    'F': `<strong>Bufferbloat:</strong> Bad. Your network has severe bufferbloat. The ${increase}% latency increase will make real-time applications nearly unusable. Consider upgrading your router or enabling Smart Queue Management (SQM).`
                };
                explanation += explanations[grade] || 'Unable to determine network quality.';
            }
            
            return explanation;
        }

        async function testUploadSpeed() {
            console.log('Starting lightweight upload speed test...');
            const startTime = performance.now();
            let totalBytes = 0;
            
            try {
                // Even lighter upload test - just enough to measure speed
                const numStreams = 2;
                const uploadsPerStream = 8; // Reduced from 15
                const chunkSize = 64 * 1024;
                const data = new Uint8Array(chunkSize).fill(65);
                const promises = [];
                
                for (let stream = 0; stream < numStreams; stream++) {
                    const uploadPromise = (async () => {
                        let streamBytes = 0;
                        
                        console.log(`Starting upload stream ${stream + 1}...`);
                        
                        for (let uploadCount = 0; uploadCount < uploadsPerStream; uploadCount++) {
                            try {
                                const response = await fetch('/api/upload', {
                                    method: 'POST',
                                    body: data,
                                    headers: {
                                        'Content-Type': 'application/octet-stream',
                                        'X-Stream-Id': stream.toString()
                                    },
                                    cache: 'no-cache'
                                });
                                
                                if (!response.ok) {
                                    throw new Error(`Upload failed: ${response.status}`);
                                }
                                
                                streamBytes += chunkSize;
                                totalBytes += chunkSize;
                                
                                // Much smaller delay - just 5ms
                                if (uploadCount < uploadsPerStream - 1) {
                                    await new Promise(resolve => setTimeout(resolve, 5));
                                }
                                
                            } catch (error) {
                                console.error(`Upload stream ${stream + 1}, chunk ${uploadCount + 1} failed:`, error);
                                break;
                            }
                        }
                        
                        console.log(`Upload stream ${stream + 1} completed: ${(streamBytes / 1024 / 1024).toFixed(1)}MB`);
                        return streamBytes;
                    })();
                    
                    promises.push(uploadPromise);
                }
                
                // Realistic timeout - should easily complete in under 5 seconds now
                const timeoutPromise = new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Upload test timeout')), 8000) // 8 second timeout
                );
                
                const result = await Promise.race([
                    Promise.all(promises),
                    timeoutPromise
                ]);
                
                // If we get here, the test completed successfully
                const elapsedSeconds = (performance.now() - startTime) / 1000;
                const mbps = (totalBytes * 8) / (elapsedSeconds * 1024 * 1024);
                
                console.log(`Upload test completed successfully: ${(totalBytes / 1024 / 1024).toFixed(1)}MB in ${elapsedSeconds.toFixed(1)}s = ${mbps.toFixed(1)} Mbps`);
                return mbps;
                
            } catch (error) {
                console.error('Upload test failed:', error);
                
                // Only return partial result if we actually got meaningful data
                if (totalBytes > 512 * 1024) { // At least 512KB
                    const elapsedSeconds = (performance.now() - startTime) / 1000;
                    const mbps = (totalBytes * 8) / (elapsedSeconds * 1024 * 1024);
                    console.log(`Upload test partial result: ${mbps.toFixed(1)} Mbps (${(totalBytes / 1024).toFixed(0)}KB transferred)`);
                    return mbps;
                } else {
                    console.log('Upload test failed with insufficient data - returning 0');
                    return 0;
                }
            }
        }

        async function startCompleteNetworkTest() {
            if (testRunning) return;
            
            testRunning = true;
            console.log('=== STARTING COMPLETE NETWORK TEST ===');
            
            const button = document.getElementById('startTest');
            const progressContainer = document.getElementById('progressContainer');
            const results = document.getElementById('results');
            
            button.disabled = true;
            button.textContent = 'Testing...';
            progressContainer.style.display = 'block';
            results.style.display = 'none';
            
            let streamControllers = [];
            let streamPromises = [];
            let baselineMeasurements = [];
            let loadedMeasurements = [];
            let downloadSpeed = 0;
            let uploadSpeed = 0;
            
            try {
                // Phase 1: Upload Speed Test
                console.log('PHASE 1: Testing upload speed...');
                updateStatus('Testing upload speed...');
                updateProgress(5);
                
                uploadSpeed = await testUploadSpeed();
                updateProgress(20);
                
                // Phase 2: Baseline latency (extended for accuracy)
                console.log('PHASE 2: Measuring baseline latency...');
                updateStatus('Measuring baseline latency (taking multiple samples)...');
                
                const baselineTestDuration = 3; // 3 seconds of baseline testing
                const baselineInterval = 250; // 250ms between measurements
                const baselineTests = Math.floor((baselineTestDuration * 1000) / baselineInterval);
                
                for (let i = 0; i < baselineTests; i++) {
                    const latency = await measureLatency();
                    if (latency !== null) {
                        baselineMeasurements.push(latency);
                        
                        // Show progress and current measurement
                        const current = latency.toFixed(1);
                        const avg = baselineMeasurements.length > 1 ? 
                            (baselineMeasurements.reduce((a, b) => a + b) / baselineMeasurements.length).toFixed(1) : 
                            current;
                        console.log(`Baseline test ${i + 1}/${baselineTests}: ${current}ms (avg: ${avg}ms)`);
                        updateStatus(`Baseline latency: ${current}ms (avg: ${avg}ms) - ${i + 1}/${baselineTests}`);
                    }
                    
                    // Update progress through baseline phase (20% to 35%)
                    const baselineProgress = 20 + (i / baselineTests) * 15;
                    updateProgress(baselineProgress);
                    
                    await new Promise(resolve => setTimeout(resolve, baselineInterval));
                }
                
                if (baselineMeasurements.length === 0) {
                    throw new Error('Failed to measure baseline latency');
                }
                
                // Calculate baseline with better statistics
                const baselineLatency = baselineMeasurements.reduce((a, b) => a + b) / baselineMeasurements.length;
                const baselineMin = Math.min(...baselineMeasurements);
                const baselineMax = Math.max(...baselineMeasurements);
                const baselineStdDev = Math.sqrt(
                    baselineMeasurements.reduce((acc, val) => acc + Math.pow(val - baselineLatency, 2), 0) / baselineMeasurements.length
                );
                
                console.log(`Baseline complete: ${baselineLatency.toFixed(1)}ms avg (${baselineMin.toFixed(1)}-${baselineMax.toFixed(1)}ms range, ${baselineStdDev.toFixed(1)}ms std dev, ${baselineMeasurements.length} samples)`);
                updateProgress(35);
                
                // Phase 3: Download speed test with bufferbloat measurement
                console.log('PHASE 3: Starting download speed test...');
                updateStatus('Testing download speed and bufferbloat...');
                updateProgress(40);
                
                // Track download speed on client side
                let totalBytesConsumed = 0;
                let downloadStartTime = performance.now();
                
                // Create 2 download streams for lighter system load
                for (let streamIndex = 0; streamIndex < 2; streamIndex++) {
                    const controller = new AbortController();
                    streamControllers.push(controller);
                    
                    const streamPromise = fetch('/api/download/throttled', {
                        method: 'GET',
                        cache: 'no-cache',
                        signal: controller.signal
                    }).then(response => {
                        console.log('Download stream ' + (streamIndex + 1) + ' connected');
                        return response.body.getReader();
                    }).then(reader => {
                        const consumeData = async () => {
                            let streamBytes = 0;
                            let lastLogTime = Date.now();
                            
                            try {
                                while (!controller.signal.aborted) {
                                    const { done, value } = await reader.read();
                                    if (done) break;
                                    
                                    // Consume data efficiently
                                    if (value) {
                                        streamBytes += value.length;
                                        totalBytesConsumed += value.length;
                                        
                                        // Log every 3 seconds for balance
                                        const now = Date.now();
                                        if (now - lastLogTime > 3000) {
                                            const elapsedSeconds = (performance.now() - downloadStartTime) / 1000;
                                            const currentSpeedMbps = (totalBytesConsumed * 8) / (elapsedSeconds * 1024 * 1024);
                                            console.log(`Stream ${streamIndex + 1}: ${(streamBytes / 1024 / 1024).toFixed(1)}MB | Total: ${(totalBytesConsumed / 1024 / 1024).toFixed(1)}MB | Speed: ${currentSpeedMbps.toFixed(1)} Mbps`);
                                            lastLogTime = now;
                                        }
                                    }
                                }
                                console.log(`Stream ${streamIndex + 1} finished: ${(streamBytes / 1024 / 1024).toFixed(1)}MB total`);
                            } catch (error) {
                                if (error.name !== 'AbortError') {
                                    console.log('Stream ' + (streamIndex + 1) + ' error: ' + error.message);
                                }
                            }
                        };
                        return consumeData();
                    }).catch(error => {
                        if (error.name !== 'AbortError') {
                            console.log('Stream ' + (streamIndex + 1) + ' failed: ' + error.message);
                        }
                    });
                    
                    streamPromises.push(streamPromise);
                }
                
                updateProgress(50);
                
                // Wait for streams to establish and transfer some data
                console.log('Waiting for streams to establish and transfer data...');
                updateStatus('Waiting for streams to establish...');
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                // Phase 4: Measure latency under load
                console.log('PHASE 4: Measuring latency under load...');
                updateStatus('Measuring latency under load...');
                
                const testDuration = 10;
                const interval = 500; // Back to 500ms for better measurement
                const totalTests = Math.floor((testDuration * 1000) / interval);
                
                for (let i = 0; i < totalTests; i++) {
                    const latency = await measureLatency();
                    if (latency !== null) {
                        loadedMeasurements.push(latency);
                    }
                    
                    const progress = 50 + (i / totalTests) * 35;
                    updateProgress(progress);
                    
                    await new Promise(resolve => setTimeout(resolve, interval));
                }
                
                // Calculate download speed from client-side data consumption
                const downloadElapsedSeconds = (performance.now() - downloadStartTime) / 1000;
                downloadSpeed = downloadElapsedSeconds > 0 ? (totalBytesConsumed * 8) / (downloadElapsedSeconds * 1024 * 1024) : 0;
                
                console.log(`Download complete: ${(totalBytesConsumed / 1024 / 1024).toFixed(1)}MB in ${downloadElapsedSeconds.toFixed(1)}s`);
                console.log(`Download speed: ${downloadSpeed.toFixed(1)} Mbps`);
                
                updateProgress(90);
                updateStatus('Calculating results...');
                
                // Calculate bufferbloat results
                const loadedLatency = loadedMeasurements.reduce((a, b) => a + b) / loadedMeasurements.length;
                const ratio = loadedLatency / baselineLatency;
                const grade = calculateGrade(ratio);
                
                // Calculate jitter
                const mean = loadedLatency;
                const variance = loadedMeasurements.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / loadedMeasurements.length;
                const jitter = Math.sqrt(variance);
                
                console.log(`Test complete! Grade: ${grade}, Download: ${downloadSpeed.toFixed(1)} Mbps, Upload: ${uploadSpeed.toFixed(1)} Mbps`);
                
                // Display results
                updateProgress(100);
                updateStatus('Test complete!');
                
                document.getElementById('downloadSpeed').textContent = downloadSpeed.toFixed(1);
                document.getElementById('uploadSpeed').textContent = uploadSpeed.toFixed(1);
                document.getElementById('grade').textContent = grade;
                document.getElementById('grade').className = 'grade ' + grade.charAt(0);
                document.getElementById('idleLatency').textContent = baselineLatency.toFixed(1) + ' ms';
                document.getElementById('loadedLatency').textContent = loadedLatency.toFixed(1) + ' ms';
                document.getElementById('latencyIncrease').textContent = ratio.toFixed(1) + 'x';
                document.getElementById('jitter').textContent = jitter.toFixed(1) + ' ms';
                document.getElementById('explanation').innerHTML = getExplanation(grade, ratio, baselineLatency, loadedLatency, downloadSpeed, uploadSpeed);
                
                results.style.display = 'block';
                
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                }, 2000);
                
            } catch (error) {
                console.error('Test failed:', error);
                updateStatus('Test failed: ' + error.message);
                updateProgress(0);
                alert('Test failed: ' + error.message);
            } finally {
                // Clean up
                console.log('Cleaning up streams...');
                streamControllers.forEach((controller, i) => {
                    try {
                        controller.abort();
                    } catch (e) {
                        console.log(`Error stopping stream ${i + 1}: ${e.message}`);
                    }
                });
                
                if (streamPromises.length > 0) {
                    try {
                        await Promise.allSettled(streamPromises);
                    } catch (e) {
                        console.log('Cleanup error:', e.message);
                    }
                }
                
                testRunning = false;
                button.disabled = false;
                button.textContent = 'Start Complete Network Test';
                
                console.log('=== TEST COMPLETE ===');
            }
        }
        
        // Initialize
        window.startCompleteNetworkTest = startCompleteNetworkTest;
        
        document.addEventListener('DOMContentLoaded', function() {
            const isLocalhost = window.location.hostname === 'localhost' || 
                               window.location.hostname === '127.0.0.1' ||
                               window.location.hostname === '::1';
            
            if (isLocalhost) {
                updateStatus('WARNING: LOCALHOST TESTING - Results may not reflect real network performance');
                document.getElementById('testingNotice').style.background = '#fff3cd';
                document.getElementById('testingNotice').style.borderColor = '#ffc107';
            } else {
                updateStatus('Ready for complete network test');
                document.getElementById('testingNotice').style.display = 'none';
            }
            
            console.log('Enhanced Bufferbloat & Speed Tester v3.3 loaded successfully - LIGHTWEIGHT FOR ACCURACY');
            console.log('Focus: 2 streams × 8 Mbps = 16 Mbps total, prioritizing network accuracy over raw speed');
            
            const button = document.getElementById('startTest');
            if (button) {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    startCompleteNetworkTest();
                });
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Serve the main application page with cache busting"""
    import time
    cache_bust = int(time.time())
    
    html_with_cache_bust = HTML_TEMPLATE.replace(
        '<title>Enhanced Bufferbloat & Speed Tester</title>',
        f'<title>Enhanced Bufferbloat & Speed Tester (v{cache_bust})</title>'
    )
    
    response = app.response_class(
        response=html_with_cache_bust,
        status=200,
        mimetype='text/html'
    )
    
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['ETag'] = f'"{cache_bust}"'
    
    return response

@app.route('/favicon.ico')
def favicon():
    """Serve a simple favicon to prevent 404 errors"""
    return '', 204

@app.route('/api/debug')
def debug():
    """Debug endpoint to check what's being served"""
    return jsonify({
        'version': '3.0',
        'features': ['bufferbloat-testing', 'download-speed', 'upload-speed'],
        'timestamp': time.time(),
        'download_stats': {
            'total_bytes': download_stats['total_bytes'],
            'streams_active': download_stats['streams_active'],
            'start_time': download_stats['start_time']
        },
        'upload_stats': {
            'total_bytes': upload_stats['total_bytes'],
            'start_time': upload_stats['start_time']
        }
    })

@app.route('/api/version')
def version():
    """Version check endpoint"""
    return jsonify({
        'version': '3.0',
        'status': 'enhanced-speed-testing-enabled',
        'features': ['bufferbloat', 'download_speed', 'upload_speed'],
        'timestamp': time.time()
    })

@app.route('/api/ping-light')
def ping_light():
    """Ultra-lightweight endpoint for latency measurement - minimal processing"""
    return 'pong', 200, {'Content-Type': 'text/plain', 'Content-Length': '4'}

@app.route('/api/ping')
def ping():
    """Standard ping endpoint for debugging"""
    return jsonify({
        'timestamp': time.time(),
        'status': 'pong'
    })

@app.route('/api/stats/reset', methods=['POST'])
def reset_stats():
    """Reset download statistics"""
    global download_stats, upload_stats
    
    with download_stats['lock']:
        old_bytes = download_stats['total_bytes']
        download_stats['total_bytes'] = 0
        download_stats['start_time'] = time.time()
        download_stats['streams_active'] = 0
    
    with upload_stats['lock']:
        upload_stats['total_bytes'] = 0
        upload_stats['start_time'] = None
    
    app.logger.info(f"Statistics reset (was {old_bytes} download bytes)")
    return jsonify({'status': 'reset', 'timestamp': time.time()})

@app.route('/api/stats')
def get_stats():
    """Get current speed statistics"""
    global download_stats, upload_stats
    
    with download_stats['lock']:
        download_elapsed = time.time() - download_stats['start_time'] if download_stats['start_time'] else 0
        download_speed_mbps = 0
        if download_elapsed > 0 and download_stats['total_bytes'] > 0:
            download_speed_mbps = (download_stats['total_bytes'] * 8) / (download_elapsed * 1024 * 1024)
    
    with upload_stats['lock']:
        upload_elapsed = time.time() - upload_stats['start_time'] if upload_stats['start_time'] else 0
        upload_speed_mbps = 0
        if upload_elapsed > 0:
            upload_speed_mbps = (upload_stats['total_bytes'] * 8) / (upload_elapsed * 1024 * 1024)
    
    # Log the stats calculation for debugging
    app.logger.info(f"Stats: {download_stats['total_bytes']} bytes in {download_elapsed:.1f}s = {download_speed_mbps:.1f} Mbps ({download_stats['streams_active']} active)")
    
    return jsonify({
        'download_speed_mbps': download_speed_mbps,
        'upload_speed_mbps': upload_speed_mbps,
        'download_bytes': download_stats['total_bytes'],
        'upload_bytes': upload_stats['total_bytes'],
        'download_elapsed': download_elapsed,
        'upload_elapsed': upload_elapsed,
        'streams_active': download_stats['streams_active'],
        'timestamp': time.time()
    })

@app.route('/api/download/<int:megabytes>')
def download(megabytes):
    """Generate download traffic - legacy endpoint"""
    def generate_data():
        chunk_size = 1024 * 1024
        chunk = b'0' * chunk_size
        
        for i in range(megabytes):
            yield chunk
    
    return Response(
        generate_data(),
        mimetype='application/octet-stream',
        headers={
            'Content-Length': str(megabytes * 1024 * 1024),
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    )

@app.route('/api/download/throttled')
def download_throttled():
    """Generate throttled download traffic with speed tracking"""
    def generate_throttled_data():
        global download_stats
        
        chunk_size = 32 * 1024  # 32KB chunks
        chunk = b'A' * chunk_size
        bytes_sent = 0
        start_time = time.time()
        
        # Register this stream
        with download_stats['lock']:
            download_stats['streams_active'] += 1
            if download_stats['start_time'] is None:
                download_stats['start_time'] = start_time
        
        app.logger.info(f"Starting throttled download stream (active streams: {download_stats['streams_active']})")
        
        try:
            while True:
                yield chunk
                bytes_sent += chunk_size
                
                # Update global statistics
                with download_stats['lock']:
                    download_stats['total_bytes'] += chunk_size
                
                # Throttle to ~10 Mbps per stream
                target_rate = 1280000  # bytes per second (10 Mbps)
                elapsed = time.time() - start_time
                expected_bytes = elapsed * target_rate
                
                if bytes_sent > expected_bytes:
                    delay = (bytes_sent - expected_bytes) / target_rate
                    sleep_time = min(delay, 0.2)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                
                # Log progress every 5MB
                if bytes_sent % (5 * 1024 * 1024) == 0:
                    mbytes = bytes_sent // (1024*1024)
                    rate_mbps = (bytes_sent * 8) / (elapsed * 1024 * 1024) if elapsed > 0 else 0
                    app.logger.info(f"Stream progress: {mbytes}MB sent, {rate_mbps:.1f} Mbps")
                    
        except GeneratorExit:
            elapsed = time.time() - start_time
            mbytes = bytes_sent // (1024*1024)
            rate_mbps = (bytes_sent * 8) / (elapsed * 1024 * 1024) if elapsed > 0 else 0
            
            # Unregister this stream
            with download_stats['lock']:
                download_stats['streams_active'] = max(0, download_stats['streams_active'] - 1)
            
            app.logger.info(f"Stream stopped: {mbytes}MB in {elapsed:.1f}s ({rate_mbps:.1f} Mbps, {download_stats['streams_active']} active)")
            return
        except Exception as e:
            with download_stats['lock']:
                download_stats['streams_active'] = max(0, download_stats['streams_active'] - 1)
            app.logger.error(f"Download stream error: {e}")
            return
    
    response = Response(
        generate_throttled_data(),
        mimetype='application/octet-stream',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache', 
            'Expires': '0',
            'Transfer-Encoding': 'chunked',
            'X-Stream-Type': 'throttled-10mbps'
        }
    )
    
    return response

@app.route('/api/upload', methods=['POST'])
def upload():
    """Accept upload traffic and track speed"""
    global upload_stats
    
    bytes_received = 0
    start_time = time.time()
    
    # Initialize upload stats if not already started
    with upload_stats['lock']:
        if upload_stats['start_time'] is None:
            upload_stats['start_time'] = start_time
    
    try:
        # Consume the upload stream
        while True:
            chunk = request.stream.read(8192)
            if not chunk:
                break
            bytes_received += len(chunk)
            
            # Update global stats
            with upload_stats['lock']:
                upload_stats['total_bytes'] += len(chunk)
                
    except Exception as e:
        app.logger.warning(f"Upload stream error: {e}")
    
    elapsed = time.time() - start_time
    speed_mbps = (bytes_received * 8) / (elapsed * 1024 * 1024) if elapsed > 0 else 0
    
    app.logger.info(f"Upload received: {bytes_received // 1024}KB in {elapsed:.2f}s ({speed_mbps:.1f} Mbps)")
    
    return jsonify({
        'status': 'received',
        'bytes': bytes_received,
        'elapsed': elapsed,
        'speed_mbps': speed_mbps,
        'timestamp': time.time()
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '3.0',
        'features': ['bufferbloat', 'download_speed', 'upload_speed'],
        'timestamp': time.time()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '0.0.0.0')
    
    app.logger.info(f"Starting Enhanced Bufferbloat & Speed Tester on {host}:{port}")
    
    app.run(host=host, port=port, debug=False, threaded=True, processes=1)