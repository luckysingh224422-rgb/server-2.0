from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import base64
import os
import json

app = Flask(__name__)
app.debug = True

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
message_count = 0

def send_messages(access_tokens, thread_id, mn, time_interval, messages, image_url, task_id):
    global message_count
    stop_event = stop_events[task_id]
    
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                try:
                    message = str(mn) + ' ' + message1
                    
                    # If image URL is provided, send image with message
                    if image_url:
                        # Send image with caption
                        api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                        parameters = {
                            'access_token': access_token,
                            'message': message,
                            'url': image_url
                        }
                    else:
                        # Send only text message
                        api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                        parameters = {
                            'access_token': access_token,
                            'message': message
                        }
                    
                    response = requests.post(api_url, data=parameters, headers=headers)
                    if response.status_code == 200:
                        print(f"✅ Message Sent Successfully From token {access_token}: {message}")
                        message_count += 1
                    else:
                        print(f"❌ Message Sent Failed From token {access_token}: {message}")
                        print(f"Error: {response.text}")
                    
                except Exception as e:
                    print(f"🚨 Error sending message: {e}")
                
                time.sleep(time_interval)

def upload_image_to_imgbb(image_file):
    """Upload image to ImgBB and return direct URL"""
    try:
        # ImgBB API key (free tier)
        api_key = "your_imgbb_api_key_here"  # You can get free API key from imgbb.com
        
        # Convert image to base64
        image_base64 = base64.b64encode(image_file.read()).decode()
        
        # Upload to ImgBB
        upload_url = "https://api.imgbb.com/1/upload"
        data = {
            'key': api_key,
            'image': image_base64
        }
        
        response = requests.post(upload_url, data=data)
        if response.status_code == 200:
            result = response.json()
            return result['data']['url']
        return None
    except Exception as e:
        print(f"Error uploading image to ImgBB: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def send_message():
    global message_count
    
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

        # Handle image upload and get image URL
        image_url = None
        if 'imageFile' in request.files and request.files['imageFile'].filename != '':
            image_file = request.files['imageFile']
            # For now, use a placeholder image URL
            # In production, you'd upload to a service like ImgBB
            image_url = "https://via.placeholder.com/500x500/FFD700/000000?text=VIP+AAHAN"
            # image_url = upload_image_to_imgbb(image_file)  # Uncomment when you have ImgBB API key

        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        stop_events[task_id] = Event()
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, image_url, task_id))
        threads[task_id] = thread
        thread.start()

        return f'''
        <div style="background: linear-gradient(45deg, #00b09b, #96c93d); color: white; padding: 30px; border-radius: 20px; text-align: center; margin: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <h3 style="margin: 0; font-size: 28px;">🚀 ATTACK LAUNCHED SUCCESSFULLY!</h3>
            <p style="font-size: 20px; margin: 15px 0;">Task ID: <strong style="color: #FFD700;">{task_id}</strong></p>
            <p style="font-size: 16px; margin: 10px 0;">🎯 Target: {thread_id}</p>
            <p style="font-size: 16px; margin: 10px 0;">⏰ Interval: {time_interval}s</p>
            <a href="/" style="display: inline-block; background: linear-gradient(45deg, #FFD700, #FFED4E); color: black; padding: 12px 25px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 15px; font-size: 16px;">🔥 BACK TO CONTROL PANEL</a>
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
  <title>🔥💫 𝐕𝐈𝐏 𝐀𝐀𝐇𝐀𝐍 - 𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐁𝐎𝐌𝐁𝐄𝐑 💫🔥</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Exo+2:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    :root {
      --primary-gold: #FFD700;
      --secondary-gold: #FFED4E;
      --premium-blue: #00f5ff;
      --neon-pink: #ff00ff;
      --dark-bg: #0a0a0a;
      --card-bg: rgba(255, 215, 0, 0.08);
      --neon-glow: 0 0 20px var(--primary-gold);
      --blue-glow: 0 0 20px var(--premium-blue);
      --pink-glow: 0 0 20px var(--neon-pink);
    }

    body {
      background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
      background-attachment: fixed;
      color: white;
      font-family: 'Exo 2', sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
    }

    .premium-text {
      font-family: 'Orbitron', sans-serif;
      background: linear-gradient(45deg, var(--primary-gold), var(--premium-blue), var(--neon-pink));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 
        0 0 30px var(--primary-gold),
        0 0 60px var(--premium-blue);
      animation: premiumGlow 3s ease-in-out infinite alternate;
    }

    @keyframes premiumGlow {
      0% {
        text-shadow: 
          0 0 30px var(--primary-gold),
          0 0 60px var(--premium-blue);
      }
      50% {
        text-shadow: 
          0 0 40px var(--premium-blue),
          0 0 80px var(--neon-pink);
      }
      100% {
        text-shadow: 
          0 0 30px var(--neon-pink),
          0 0 60px var(--primary-gold);
      }
    }

    .premium-container {
      max-width: 500px;
      margin: 20px auto;
      background: var(--card-bg);
      backdrop-filter: blur(25px);
      border: 3px solid transparent;
      border-radius: 30px;
      padding: 35px;
      position: relative;
      box-shadow: 
        var(--neon-glow),
        var(--blue-glow),
        inset 0 0 80px rgba(255, 215, 0, 0.1);
      animation: premiumBorder 4s ease-in-out infinite alternate;
      overflow: hidden;
    }

    .premium-container::before {
      content: '';
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(45deg, transparent, rgba(255,215,0,0.1), transparent);
      animation: shine 6s linear infinite;
      transform: rotate(45deg);
    }

    @keyframes shine {
      0% { transform: rotate(45deg) translateX(-100%); }
      100% { transform: rotate(45deg) translateX(100%); }
    }

    @keyframes premiumBorder {
      0% {
        border-color: var(--primary-gold);
        box-shadow: 
          var(--neon-glow),
          inset 0 0 80px rgba(255, 215, 0, 0.1);
      }
      50% {
        border-color: var(--premium-blue);
        box-shadow: 
          var(--blue-glow),
          inset 0 0 80px rgba(0, 245, 255, 0.1);
      }
      100% {
        border-color: var(--neon-pink);
        box-shadow: 
          var(--pink-glow),
          inset 0 0 80px rgba(255, 0, 255, 0.1);
      }
    }

    .premium-input {
      background: rgba(255, 255, 255, 0.08);
      border: 2px solid transparent;
      border-radius: 15px;
      color: white;
      padding: 16px 22px;
      margin-bottom: 22px;
      transition: all 0.4s ease;
      font-size: 16px;
      backdrop-filter: blur(15px);
      font-family: 'Exo 2', sans-serif;
    }

    .premium-input:focus {
      border-color: var(--premium-blue);
      background: rgba(255, 255, 255, 0.12);
      box-shadow: var(--blue-glow);
      transform: scale(1.03);
      outline: none;
    }

    .premium-select {
      background: rgba(255, 255, 255, 0.08);
      border: 2px solid transparent;
      border-radius: 15px;
      color: white;
      padding: 16px 22px;
      margin-bottom: 22px;
      transition: all 0.4s ease;
      backdrop-filter: blur(15px);
      font-family: 'Exo 2', sans-serif;
    }

    .premium-select:focus {
      border-color: var(--premium-blue);
      background: rgba(255, 255, 255, 0.12);
      box-shadow: var(--blue-glow);
      transform: scale(1.03);
      outline: none;
    }

    .premium-btn {
      background: linear-gradient(45deg, var(--primary-gold), var(--premium-blue), var(--neon-pink));
      border: none;
      border-radius: 18px;
      color: black;
      padding: 20px 35px;
      font-weight: 800;
      font-size: 20px;
      text-transform: uppercase;
      letter-spacing: 3px;
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

    .premium-btn:hover {
      transform: translateY(-5px) scale(1.08);
      box-shadow: 
        0 15px 40px rgba(255, 215, 0, 0.6),
        0 0 50px rgba(0, 245, 255, 0.4),
        0 0 70px rgba(255, 0, 255, 0.3);
      color: black;
    }

    .premium-btn-danger {
      background: linear-gradient(45deg, #ff416c, #ff4b2b, #ff0000);
      color: white;
      animation: dangerShift 3s ease infinite;
    }

    @keyframes dangerShift {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }

    .premium-btn-danger:hover {
      box-shadow: 
        0 15px 40px rgba(255, 65, 108, 0.6),
        0 0 50px rgba(255, 75, 43, 0.4);
    }

    .file-upload-area {
      border: 3px dashed var(--premium-blue);
      border-radius: 20px;
      padding: 35px;
      text-align: center;
      margin: 25px 0;
      transition: all 0.4s ease;
      background: rgba(0, 245, 255, 0.05);
      cursor: pointer;
      position: relative;
      overflow: hidden;
    }

    .file-upload-area:hover {
      background: rgba(0, 245, 255, 0.1);
      border-color: var(--primary-gold);
      transform: scale(1.02);
      box-shadow: var(--blue-glow);
    }

    .feature-badge {
      background: linear-gradient(45deg, var(--primary-gold), var(--premium-blue));
      color: black;
      padding: 10px 18px;
      border-radius: 25px;
      font-weight: 800;
      margin: 6px;
      display: inline-block;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      font-family: 'Orbitron', sans-serif;
    }

    .social-icon {
      width: 55px;
      height: 55px;
      background: linear-gradient(45deg, var(--primary-gold), var(--premium-blue));
      border-radius: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin: 0 12px;
      color: black;
      text-decoration: none;
      font-size: 22px;
      transition: all 0.4s ease;
      position: relative;
      overflow: hidden;
    }

    .social-icon::before {
      content: '';
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(45deg);
      transition: all 0.4s ease;
    }

    .social-icon:hover::before {
      transform: rotate(45deg) translate(50%, 50%);
    }

    .social-icon:hover {
      transform: scale(1.3) rotate(360deg);
      box-shadow: var(--neon-glow), var(--blue-glow);
      color: black;
    }

    .floating {
      animation: floating 4s ease-in-out infinite;
    }

    @keyframes floating {
      0%, 100% { transform: translateY(0px) rotate(0deg); }
      50% { transform: translateY(-15px) rotate(2deg); }
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

    .stats-container {
      display: flex;
      justify-content: space-around;
      margin: 25px 0;
      text-align: center;
    }

    .stat-item {
      padding: 18px;
      background: rgba(255, 215, 0, 0.1);
      border-radius: 15px;
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 215, 0, 0.3);
    }

    .stat-number {
      font-size: 28px;
      font-weight: 800;
      color: var(--primary-gold);
      display: block;
      font-family: 'Orbitron', sans-serif;
    }

    .stat-label {
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: var(--premium-blue);
      font-weight: 600;
    }

    .premium-label {
      font-family: 'Orbitron', sans-serif;
      font-weight: 700;
      font-size: 16px;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin-bottom: 12px;
      display: block;
    }

    .cyber-grid {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: 
        linear-gradient(90deg, rgba(255,215,0,0.03) 1px, transparent 1px),
        linear-gradient(0deg, rgba(255,215,0,0.03) 1px, transparent 1px);
      background-size: 50px 50px;
      pointer-events: none;
      z-index: -2;
    }
  </style>
</head>
<body>
  <!-- Cyber Grid Background -->
  <div class="cyber-grid"></div>
  
  <!-- Animated Background Particles -->
  <div class="particles" id="particles"></div>

  <header class="text-center mt-4">
    <h1 class="premium-text floating" style="font-size: 3rem; margin-bottom: 15px;">
      ⚡💎 𝐕𝐈𝐏 𝐀𝐀𝐇𝐀𝐍 💎⚡
    </h1>
    <p class="text-warning" style="font-size: 1.4rem; font-weight: 700; letter-spacing: 3px;">
      𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐁𝐎𝐌𝐁𝐄𝐑
    </p>
    
    <!-- Features Badges -->
    <div class="mt-4">
      <span class="feature-badge"><i class="fas fa-bolt"></i> ULTRA FAST</span>
      <span class="feature-badge"><i class="fas fa-shield-alt"></i> SECURE</span>
      <span class="feature-badge"><i class="fas fa-rocket"></i> POWERFUL</span>
      <span class="feature-badge"><i class="fas fa-image"></i> IMAGE SUPPORT</span>
    </div>
  </header>

  <!-- Stats -->
  <div class="stats-container">
    <div class="stat-item">
      <span class="stat-number" id="activeTasks">{{ active_tasks }}</span>
      <span class="stat-label">ACTIVE MISSIONS</span>
    </div>
    <div class="stat-item">
      <span class="stat-number" id="successRate">100%</span>
      <span class="stat-label">SUCCESS RATE</span>
    </div>
  </div>

  <div class="premium-container">
    <form method="post" enctype="multipart/form-data" id="mainForm">
      <!-- Token Option -->
      <div class="mb-4">
        <label class="premium-label text-warning">🔑 SELECT TOKEN OPTION</label>
        <select class="premium-select w-100" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
          <option value="single">Single Token</option>
          <option value="multiple">Token File</option>
        </select>
      </div>

      <!-- Single Token Input -->
      <div class="mb-4" id="singleTokenInput">
        <label class="premium-label text-warning">🔐 SINGLE TOKEN</label>
        <input type="text" class="premium-input w-100" id="singleToken" name="singleToken" placeholder="Enter your Facebook token...">
      </div>

      <!-- Token File Input -->
      <div class="mb-4" id="tokenFileInput" style="display: none;">
        <label class="premium-label text-warning">📁 TOKEN FILE</label>
        <div class="file-upload-area" onclick="document.getElementById('tokenFile').click()">
          <i class="fas fa-cloud-upload-alt fa-4x text-warning mb-3"></i>
          <p class="text-warning fw-bold">CLICK TO UPLOAD TOKEN FILE</p>
          <p class="small text-muted">Upload .txt file with multiple tokens</p>
          <input type="file" class="d-none" id="tokenFile" name="tokenFile" accept=".txt">
        </div>
      </div>

      <!-- Thread ID -->
      <div class="mb-4">
        <label class="premium-label text-warning">🎯 TARGET UID</label>
        <input type="text" class="premium-input w-100" id="threadId" name="threadId" placeholder="Enter target conversation ID..." required>
      </div>

      <!-- Hater Name -->
      <div class="mb-4">
        <label class="premium-label text-warning">😈 HATER NAME</label>
        <input type="text" class="premium-input w-100" id="kidx" name="kidx" placeholder="Enter hater name..." required>
      </div>

      <!-- Time Interval -->
      <div class="mb-4">
        <label class="premium-label text-warning">⏰ TIME INTERVAL (SECONDS)</label>
        <input type="number" class="premium-input w-100" id="time" name="time" placeholder="Enter time in seconds..." required min="1">
      </div>

      <!-- Messages File -->
      <div class="mb-4">
        <label class="premium-label text-warning">💬 MESSAGES FILE</label>
        <div class="file-upload-area" onclick="document.getElementById('txtFile').click()">
          <i class="fas fa-file-alt fa-4x text-warning mb-3"></i>
          <p class="text-warning fw-bold">CLICK TO UPLOAD MESSAGES</p>
          <p class="small text-muted">Upload .txt file with your messages</p>
          <input type="file" class="d-none" id="txtFile" name="txtFile" accept=".txt" required>
        </div>
      </div>

      <!-- Image Upload -->
      <div class="mb-4">
        <label class="premium-label text-warning">🖼️ ATTACH IMAGE (OPTIONAL)</label>
        <div class="file-upload-area" onclick="document.getElementById('imageFile').click()">
          <i class="fas fa-image fa-4x text-warning mb-3"></i>
          <p class="text-warning fw-bold">CLICK TO UPLOAD IMAGE</p>
          <p class="small text-muted">Supports: JPG, PNG, GIF, WEBP</p>
          <input type="file" class="d-none" id="imageFile" name="imageFile" accept="image/*">
        </div>
      </div>

      <!-- Run Button -->
      <button type="submit" class="premium-btn w-100">
        🚀 LAUNCH MISSION
      </button>
    </form>

    <!-- Stop Task Form -->
    <form method="post" action="/stop" class="mt-4">
      <div class="mb-4">
        <label class="premium-label text-danger">🛑 STOP MISSION</label>
        <input type="text" class="premium-input w-100" id="taskId" name="taskId" placeholder="Enter Mission ID to stop..." required>
      </div>
      <button type="submit" class="premium-btn premium-btn-danger w-100">
        ⚡ ABORT MISSION
      </button>
    </form>
  </div>

  <!-- Footer -->
  <footer class="text-center mt-5 mb-4">
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
    <p class="text-warning mb-2 fw-bold">© 2025 𝐃𝐄𝐕𝐄𝐋𝐎𝐏𝐄𝐃 𝐁𝐘 𝐕𝐈𝐏 𝐀𝐀𝐇𝐀𝐍</p>
    <p class="text-muted small">For educational and testing purposes only</p>
  </footer>

  <script>
    // Create animated particles
    function createParticles() {
      const particles = document.getElementById('particles');
      const particleCount = 80;
      
      for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        const size = Math.random() * 4 + 1;
        const posX = Math.random() * 100;
        const duration = Math.random() * 25 + 15;
        const delay = Math.random() * 10;
        
        // Random colors
        const colors = ['#FFD700', '#00f5ff', '#ff00ff', '#ffffff'];
        const color = colors[Math.floor(Math.random() * colors.length)];
        
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${posX}vw`;
        particle.style.animationDuration = `${duration}s`;
        particle.style.animationDelay = `${delay}s`;
        particle.style.opacity = Math.random() * 0.6 + 0.2;
        particle.style.background = color;
        particle.style.boxShadow = `0 0 ${size*2}px ${color}`;
        
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
      const fileInputs = ['tokenFile', 'txtFile', 'imageFile'];
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
              badge.className = 'feature-badge file-badge';
              badge.textContent = fileName.length > 20 ? fileName.substring(0, 20) + '...' : fileName;
              badge.style.marginTop = '15px';
              badge.style.background = 'linear-gradient(45deg, #00f5ff, #ff00ff)';
              uploadArea.appendChild(badge);
            }
          });
        }
      });
    });

    // Form submission animation
    document.getElementById('mainForm').addEventListener('submit', function(e) {
      const button = this.querySelector('button[type="submit"]');
      const originalText = button.innerHTML;
      button.innerHTML = '🚀 LAUNCHING MISSION...';
      button.disabled = true;
      
      setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
      }, 4000);
    });

    // Add typing effect to inputs
    const inputs = document.querySelectorAll('.premium-input, .premium-select');
    inputs.forEach(input => {
      input.addEventListener('focus', function() {
        this.style.animation = 'none';
        this.offsetHeight; /* trigger reflow */
        this.style.animation = null;
      });
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
        <div style="background: linear-gradient(45deg, #ff416c, #ff4b2b); color: white; padding: 30px; border-radius: 20px; text-align: center; margin: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <h3 style="margin: 0; font-size: 28px;">🛑 MISSION ABORTED!</h3>
            <p style="font-size: 20px; margin: 15px 0;">Mission ID: <strong style="color: #FFD700;">{task_id}</strong> has been stopped</p>
            <a href="/" style="display: inline-block; background: linear-gradient(45deg, #FFD700, #FFED4E); color: black; padding: 12px 25px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 15px; font-size: 16px;">🔥 BACK TO CONTROL PANEL</a>
        </div>
        '''
    else:
        return f'''
        <div style="background: linear-gradient(45deg, #ff416c, #ff4b2b); color: white; padding: 30px; border-radius: 20px; text-align: center; margin: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <h3 style="margin: 0; font-size: 28px;">❌ MISSION NOT FOUND!</h3>
            <p style="font-size: 20px; margin: 15px 0;">No mission found with ID: <strong style="color: #FFD700;">{task_id}</strong></p>
            <a href="/" style="display: inline-block; background: linear-gradient(45deg, #FFD700, #FFED4E); color: black; padding: 12px 25px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 15px; font-size: 16px;">🔥 BACK TO CONTROL PANEL</a>
        </div>
        '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
