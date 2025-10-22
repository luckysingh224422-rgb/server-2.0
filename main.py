from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import secrets
import os
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Updated headers for Facebook API
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

stop_events = {}
threads = {}

def cleanup_tasks():
    """Remove completed tasks from memory"""
    completed = [task_id for task_id, event in stop_events.items() if event.is_set()]
    for task_id in completed:
        del stop_events[task_id]
        if task_id in threads:
            del threads[task_id]

def send_messages(access_tokens, group_id, prefix, delay, messages, task_id):
    stop_event = stop_events[task_id]
    
    while not stop_event.is_set():
        try:
            for message in messages:
                if stop_event.is_set():
                    break
                
                full_message = f"{prefix} {message}".strip()
                
                for token in [t.strip() for t in access_tokens if t.strip()]:
                    if stop_event.is_set():
                        break
                    
                    try:
                        # Updated Facebook Graph API endpoint for groups
                        response = requests.post(
                            f'https://graph.facebook.com/v19.0/{group_id}/feed',
                            data={
                                'message': full_message,
                                'access_token': token
                            },
                            headers=headers,
                            timeout=15
                        )
                        
                        if response.status_code == 200:
                            print(f"Message sent successfully! Token: {token[:6]}...")
                        else:
                            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                            print(f"Failed to send message. Error: {error_msg} | Token: {token[:6]}...")
                            
                    except Exception as e:
                        print(f"Request failed: {str(e)}")
                    
                    time.sleep(max(delay, 10))  # Increased minimum delay to 10 seconds
                
                if stop_event.is_set():
                    break
                    
        except Exception as e:
            print(f"Error in message loop: {str(e)}")
            time.sleep(10)

@app.route('/', methods=['GET', 'POST'])
def main_handler():
    cleanup_tasks()
    
    if request.method == 'POST':
        try:
            # Input validation
            group_id = request.form['threadId']
            prefix = request.form.get('kidx', '')
            delay = max(int(request.form.get('time', 10)), 5)  # Minimum 5 seconds
            token_option = request.form['tokenOption']
            auth_method = request.form.get('authMethod', 'token')  # New: token or cookies
            
            # File handling
            if 'txtFile' not in request.files:
                return 'No message file uploaded', 400
                
            txt_file = request.files['txtFile']
            if txt_file.filename == '':
                return 'No message file selected', 400
                
            messages = txt_file.read().decode().splitlines()
            if not messages:
                return 'Message file is empty', 400

            # Token/Cookie handling
            access_tokens = []
            if auth_method == 'cookies':
                if 'cookieFile' not in request.files:
                    return 'No cookie file uploaded', 400
                cookie_file = request.files['cookieFile']
                if cookie_file.filename == '':
                    return 'No cookie file selected', 400
                
                # Process cookies file
                cookies_content = cookie_file.read().decode()
                access_tokens = extract_tokens_from_cookies(cookies_content)
            else:
                # Original token handling
                if token_option == 'single':
                    access_tokens = [request.form.get('singleToken', '').strip()]
                else:
                    if 'tokenFile' not in request.files:
                        return 'No token file uploaded', 400
                    token_file = request.files['tokenFile']
                    access_tokens = token_file.read().decode().strip().splitlines()
            
            access_tokens = [t.strip() for t in access_tokens if t.strip()]
            if not access_tokens:
                return 'No valid access tokens/cookies provided', 400

            # Start task
            task_id = secrets.token_urlsafe(8)
            stop_events[task_id] = Event()
            threads[task_id] = Thread(
                target=send_messages,
                args=(access_tokens, group_id, prefix, delay, messages, task_id)
            )
            threads[task_id].start()

            # VIP Success Page
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>AAHAN CONVO PANEL - MISSION INITIATED</title>
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');
                        :root {
                            --gold: #FFD700;
                            --cyan: #00FFFF;
                            --pink: #FF00FF;
                            --red: #FF073A;
                            --bg: #0a0a15;
                        }
                        body {
                            background: linear-gradient(135deg, var(--bg) 0%, #1a1a2e 50%, #16213e 100%);
                            color: white;
                            font-family: 'Rajdhani', sans-serif;
                            min-height: 100vh;
                            margin: 0;
                            padding: 20px;
                            text-align: center;
                        }
                        .vip-container {
                            max-width: 600px;
                            margin: 50px auto;
                            background: rgba(255,255,255,0.05);
                            backdrop-filter: blur(20px);
                            border: 3px solid var(--gold);
                            border-radius: 20px;
                            padding: 40px;
                            box-shadow: 0 0 50px rgba(255,215,0,0.3),
                                        inset 0 0 50px rgba(255,215,0,0.1);
                            position: relative;
                            overflow: hidden;
                        }
                        .vip-container::before {
                            content: '';
                            position: absolute;
                            top: -2px;
                            left: -2px;
                            right: -2px;
                            bottom: -2px;
                            background: linear-gradient(45deg, var(--gold), var(--cyan), var(--pink), var(--red));
                            border-radius: 22px;
                            z-index: -1;
                            animation: borderGlow 3s linear infinite;
                        }
                        @keyframes borderGlow {
                            0% { filter: hue-rotate(0deg); }
                            100% { filter: hue-rotate(360deg); }
                        }
                        .title {
                            font-family: 'Orbitron', sans-serif;
                            font-size: 2.5em;
                            background: linear-gradient(45deg, var(--gold), var(--cyan));
                            -webkit-background-clip: text;
                            background-clip: text;
                            color: transparent;
                            margin-bottom: 10px;
                        }
                        .mission-id {
                            color: var(--cyan);
                            font-size: 1.2em;
                            margin: 20px 0;
                        }
                        .btn-vip {
                            display: block;
                            width: 100%;
                            padding: 15px;
                            margin: 10px 0;
                            background: linear-gradient(45deg, var(--red), var(--pink));
                            color: white;
                            text-decoration: none;
                            border-radius: 10px;
                            font-weight: bold;
                            transition: all 0.3s;
                            border: none;
                            cursor: pointer;
                        }
                        .btn-vip:hover {
                            transform: translateY(-3px);
                            box-shadow: 0 10px 25px rgba(255,0,255,0.4);
                        }
                        .status {
                            color: var(--gold);
                            font-size: 1.1em;
                            margin: 20px 0;
                        }
                    </style>
                </head>
                <body>
                    <div class="vip-container">
                        <div class="title">AAHAN CONVO PANEL</div>
                        <div style="color: var(--cyan); font-size: 1.1em; margin-bottom: 20px;">
                            🚀 VIP MISSION CONTROL
                        </div>
                        
                        <div class="mission-id">
                            🔥 MISSION ID: <span style="color: var(--gold);">{{ task_id }}</span>
                        </div>
                        
                        <div class="status">
                            ✅ ATTACK SEQUENCE INITIATED
                        </div>
                        
                        <a href="/stop/{{ task_id }}" class="btn-vip" style="background: linear-gradient(45deg, #ff4444, #ff0000);">
                            🚨 EMERGENCY STOP
                        </a>
                        
                        <a href="/" class="btn-vip" style="background: linear-gradient(45deg, var(--cyan), #0099ff);">
                            🎯 NEW MISSION
                        </a>
                    </div>
                </body>
                </html>
            ''', task_id=task_id)

        except Exception as e:
            return f'Error: {str(e)}', 400

    # VIP Main HTML Form
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AAHAN CONVO PANEL - VIP CONTROL</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --gold: #FFD700;
            --cyan: #00FFFF;
            --pink: #FF00FF;
            --red: #FF073A;
            --purple: #9D00FF;
            --bg-dark: #0a0a15;
        }
        
        body {
            background: linear-gradient(135deg, var(--bg-dark) 0%, #1a1a2e 50%, #16213e 100%);
            color: white;
            font-family: 'Rajdhani', sans-serif;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(255, 215, 0, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(0, 255, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(255, 0, 255, 0.05) 0%, transparent 50%);
            z-index: -1;
        }
        
        .scan-line {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, transparent, var(--cyan), var(--pink), transparent);
            animation: scan 3s linear infinite;
            z-index: 1000;
            box-shadow: 0 0 20px var(--cyan);
        }
        
        @keyframes scan {
            0% { top: 0%; }
            100% { top: 100%; }
        }
        
        .vip-header {
            text-align: center;
            padding: 40px 20px 20px;
        }
        
        .main-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 3.5em;
            font-weight: 900;
            background: linear-gradient(45deg, var(--gold), var(--cyan), var(--pink));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: var(--cyan);
            font-size: 1.3em;
            font-weight: 600;
            letter-spacing: 2px;
        }
        
        .vip-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 2px solid var(--gold);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 0 50px rgba(255, 215, 0, 0.2),
                        inset 0 0 50px rgba(255, 215, 0, 0.05);
            position: relative;
            overflow: hidden;
        }
        
        .vip-card::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, var(--gold), var(--cyan), var(--pink), var(--purple));
            border-radius: 22px;
            z-index: -1;
            animation: borderGlow 4s linear infinite;
        }
        
        @keyframes borderGlow {
            0% { filter: hue-rotate(0deg); opacity: 0.7; }
            50% { opacity: 1; }
            100% { filter: hue-rotate(360deg); opacity: 0.7; }
        }
        
        .section-title {
            font-family: 'Orbitron', sans-serif;
            color: var(--cyan);
            font-size: 1.5em;
            margin-bottom: 25px;
            text-align: center;
            text-shadow: 0 0 10px var(--cyan);
        }
        
        .form-label {
            color: var(--gold);
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 1.1em;
        }
        
        .form-control, .form-select {
            background: rgba(0, 0, 0, 0.6) !important;
            border: 2px solid var(--cyan) !important;
            color: white !important;
            border-radius: 10px;
            padding: 12px 15px;
            transition: all 0.3s;
        }
        
        .form-control:focus, .form-select:focus {
            border-color: var(--gold) !important;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.3) !important;
            background: rgba(0, 0, 0, 0.8) !important;
        }
        
        .vip-btn {
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-weight: bold;
            font-size: 1.1em;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }
        
        .btn-attack {
            background: linear-gradient(45deg, var(--red), var(--pink));
            color: white;
            box-shadow: 0 5px 20px rgba(255, 0, 255, 0.3);
        }
        
        .btn-attack:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(255, 0, 255, 0.5);
        }
        
        .btn-stop {
            background: linear-gradient(45deg, #ff4444, #cc0000);
            color: white;
            box-shadow: 0 5px 20px rgba(255, 0, 0, 0.3);
        }
        
        .btn-stop:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(255, 0, 0, 0.5);
        }
        
        .method-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .method-active {
            background: linear-gradient(45deg, var(--gold), var(--cyan));
            color: black;
        }
        
        .method-inactive {
            background: rgba(255,255,255,0.1);
            color: white;
        }
        
        .floating {
            animation: floating 3s ease-in-out infinite;
        }
        
        @keyframes floating {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
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
    </style>
</head>
<body>
    <div class="scan-line"></div>
    <div class="particles" id="particles"></div>
    
    <div class="container py-4">
        <div class="vip-header floating">
            <h1 class="main-title">AAHAN CONVO PANEL</h1>
            <div class="subtitle">🚀 VIP MESSAGE CONTROL SYSTEM</div>
        </div>
        
        <form method="post" enctype="multipart/form-data">
            <div class="vip-card">
                <h3 class="section-title">🔐 AUTHENTICATION METHOD</h3>
                
                <div class="text-center mb-4">
                    <span class="method-badge method-active" onclick="setAuthMethod('token')">
                        <i class="fas fa-key"></i> ACCESS TOKEN
                    </span>
                    <span class="method-badge method-inactive" onclick="setAuthMethod('cookies')">
                        <i class="fas fa-cookie"></i> COOKIES FILE
                    </span>
                    <input type="hidden" name="authMethod" id="authMethod" value="token">
                </div>
                
                <!-- Token Method -->
                <div id="tokenMethod">
                    <div class="mb-4">
                        <label class="form-label">TOKEN TYPE</label>
                        <select class="form-select" name="tokenOption" required>
                            <option value="single">Single Token</option>
                            <option value="multiple">Token File (.txt)</option>
                        </select>
                    </div>
                    
                    <div class="mb-4" id="singleTokenSection">
                        <label class="form-label">ACCESS TOKEN</label>
                        <input type="text" class="form-control" name="singleToken" 
                               placeholder="Enter Facebook Access Token">
                    </div>
                    
                    <div class="mb-4 d-none" id="tokenFileSection">
                        <label class="form-label">TOKEN FILE</label>
                        <input type="file" class="form-control" name="tokenFile" 
                               accept=".txt">
                    </div>
                </div>
                
                <!-- Cookies Method -->
                <div id="cookiesMethod" class="d-none">
                    <div class="mb-4">
                        <label class="form-label">COOKIES FILE</label>
                        <input type="file" class="form-control" name="cookieFile" 
                               accept=".txt">
                        <small class="text-warning">Upload cookies.txt file containing Facebook cookies</small>
                    </div>
                </div>
            </div>
            
            <div class="vip-card">
                <h3 class="section-title">🎯 TARGET CONFIGURATION</h3>
                
                <div class="mb-4">
                    <label class="form-label">GROUP ID</label>
                    <input type="text" class="form-control" name="threadId" 
                           placeholder="Enter Target Group ID" required>
                </div>
                
                <div class="mb-4">
                    <label class="form-label">MESSAGE PREFIX</label>
                    <input type="text" class="form-control" name="kidx" 
                           placeholder="Optional message prefix">
                </div>
                
                <div class="mb-4">
                    <label class="form-label">DELAY (SECONDS)</label>
                    <input type="number" class="form-control" name="time" 
                           min="5" value="10" required>
                </div>
                
                <div class="mb-4">
                    <label class="form-label">MESSAGES FILE</label>
                    <input type="file" class="form-control" name="txtFile" 
                           accept=".txt" required>
                    <small class="text-info">TXT file with one message per line</small>
                </div>
            </div>
            
            <button type="submit" class="vip-btn btn-attack w-100">
                <i class="fas fa-rocket me-2"></i>LAUNCH ATTACK SEQUENCE
            </button>
        </form>
        
        <div class="vip-card mt-4">
            <h3 class="section-title">🚨 EMERGENCY CONTROL</h3>
            <form method="post" action="/stop">
                <div class="mb-3">
                    <label class="form-label">TASK ID TO STOP</label>
                    <input type="text" class="form-control" name="taskId" 
                           placeholder="Enter active Task ID">
                </div>
                <button type="submit" class="vip-btn btn-stop w-100">
                    <i class="fas fa-stop-circle me-2"></i>EMERGENCY SHUTDOWN
                </button>
            </form>
        </div>
        
        <div class="text-center mt-4" style="color: var(--gold);">
            <strong>AAHAN CONVO PANEL</strong> | VIP CONTROL SYSTEM | BY AAHAN
        </div>
    </div>

    <script>
        // Create floating particles
        function createParticles() {
            const particlesContainer = document.getElementById('particles');
            const colors = ['#FFD700', '#00FFFF', '#FF00FF', '#9D00FF'];
            
            for(let i = 0; i < 20; i++) {
                const particle = document.createElement('div');
                particle.style.position = 'fixed';
                particle.style.width = Math.random() * 5 + 2 + 'px';
                particle.style.height = particle.style.width;
                particle.style.background = colors[Math.floor(Math.random() * colors.length)];
                particle.style.borderRadius = '50%';
                particle.style.top = Math.random() * 100 + 'vh';
                particle.style.left = Math.random() * 100 + 'vw';
                particle.style.opacity = Math.random() * 0.5 + 0.1;
                particle.style.zIndex = '-1';
                particle.style.pointerEvents = 'none';
                particle.style.boxShadow = `0 0 ${Math.random() * 10 + 5}px currentColor`;
                
                particlesContainer.appendChild(particle);
                animateParticle(particle);
            }
        }
        
        function animateParticle(element) {
            let x = parseFloat(element.style.left);
            let y = parseFloat(element.style.top);
            let xSpeed = (Math.random() - 0.5) * 0.3;
            let ySpeed = (Math.random() - 0.5) * 0.3;
            
            function move() {
                x += xSpeed;
                y += ySpeed;
                
                if(x < 0 || x > 100) xSpeed *= -1;
                if(y < 0 || y > 100) ySpeed *= -1;
                
                element.style.left = x + 'vw';
                element.style.top = y + 'vh';
                
                requestAnimationFrame(move);
            }
            move();
        }
        
        // Auth method toggle
        function setAuthMethod(method) {
            document.getElementById('authMethod').value = method;
            
            // Update badge styles
            document.querySelectorAll('.method-badge').forEach(badge => {
                badge.classList.remove('method-active');
                badge.classList.add('method-inactive');
            });
            
            event.target.classList.remove('method-inactive');
            event.target.classList.add('method-active');
            
            // Show/hide sections
            if(method === 'token') {
                document.getElementById('tokenMethod').classList.remove('d-none');
                document.getElementById('cookiesMethod').classList.add('d-none');
            } else {
                document.getElementById('tokenMethod').classList.add('d-none');
                document.getElementById('cookiesMethod').classList.remove('d-none');
            }
        }
        
        // Token type toggle
        function toggleTokenInput() {
            const tokenOption = document.querySelector('[name="tokenOption"]').value;
            if(tokenOption === 'single') {
                document.getElementById('singleTokenSection').classList.remove('d-none');
                document.getElementById('tokenFileSection').classList.add('d-none');
            } else {
                document.getElementById('singleTokenSection').classList.add('d-none');
                document.getElementById('tokenFileSection').classList.remove('d-none');
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            createParticles();
            document.querySelector('[name="tokenOption"]').addEventListener('change', toggleTokenInput);
            toggleTokenInput(); // Initial call
        });
    </script>
</body>
</html>
    ''')

def extract_tokens_from_cookies(cookies_content):
    """Extract access tokens from cookies file content"""
    tokens = []
    try:
        # Simple extraction - look for EAAB pattern in cookies
        lines = cookies_content.split('\n')
        for line in lines:
            if 'EAAB' in line.upper():
                # Extract token-like strings
                import re
                token_matches = re.findall(r'EAAB[0-9A-Za-z]+', line.upper())
                tokens.extend(token_matches)
    except Exception as e:
        print(f"Error extracting tokens from cookies: {e}")
    
    return tokens

@app.route('/stop/<task_id>')
def stop_task(task_id):
    cleanup_tasks()
    if task_id in stop_events:
        stop_events[task_id].set()
        
        # VIP Stop Confirmation
        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>AAHAN CONVO PANEL - MISSION TERMINATED</title>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');
                    :root {
                        --gold: #FFD700;
                        --cyan: #00FFFF;
                        --red: #FF073A;
                    }
                    body {
                        background: linear-gradient(135deg, #0a0a15 0%, #1a1a2e 50%, #16213e 100%);
                        color: white;
                        font-family: 'Rajdhani', sans-serif;
                        min-height: 100vh;
                        margin: 0;
                        padding: 20px;
                        text-align: center;
                    }
                    .vip-container {
                        max-width: 500px;
                        margin: 100px auto;
                        background: rgba(255,255,255,0.05);
                        backdrop-filter: blur(20px);
                        border: 3px solid var(--red);
                        border-radius: 20px;
                        padding: 40px;
                        box-shadow: 0 0 50px rgba(255,7,58,0.3);
                    }
                    .title {
                        font-family: 'Orbitron', sans-serif;
                        font-size: 2em;
                        color: var(--red);
                        margin-bottom: 20px;
                    }
                    .mission-id {
                        color: var(--cyan);
                        font-size: 1.2em;
                        margin: 20px 0;
                    }
                    .btn-vip {
                        display: block;
                        width: 100%;
                        padding: 15px;
                        margin: 10px 0;
                        background: linear-gradient(45deg, var(--cyan), #0099ff);
                        color: white;
                        text-decoration: none;
                        border-radius: 10px;
                        font-weight: bold;
                        transition: all 0.3s;
                    }
                    .btn-vip:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 10px 25px rgba(0,255,255,0.4);
                    }
                </style>
            </head>
            <body>
                <div class="vip-container">
                    <div class="title">🚨 MISSION TERMINATED</div>
                    <div class="mission-id">
                        Task ID: <span style="color: var(--gold);">{{ task_id }}</span>
                    </div>
                    <p style="color: var(--cyan);">Attack sequence has been successfully halted.</p>
                    <a href="/" class="btn-vip">🎯 NEW MISSION</a>
                </div>
            </body>
            </html>
        ''', task_id=task_id)

    # VIP Error Page
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>AAHAN CONVO PANEL - ERROR</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');
                :root {
                    --gold: #FFD700;
                    --cyan: #00FFFF;
                    --red: #FF073A;
                }
                body {
                    background: linear-gradient(135deg, #0a0a15 0%, #1a1a2e 50%, #16213e 100%);
                    color: white;
                    font-family: 'Rajdhani', sans-serif;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                    text-align: center;
                }
                .vip-container {
                    max-width: 500px;
                    margin: 100px auto;
                    background: rgba(255,255,255,0.05);
                    backdrop-filter: blur(20px);
                    border: 3px solid var(--gold);
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 0 50px rgba(255,215,0,0.3);
                }
                .title {
                    font-family: 'Orbitron', sans-serif;
                    font-size: 2em;
                    color: var(--red);
                    margin-bottom: 20px;
                }
                .btn-vip {
                    display: block;
                    width: 100%;
                    padding: 15px;
                    margin: 10px 0;
                    background: linear-gradient(45deg, var(--cyan), #0099ff);
                    color: white;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: bold;
                    transition: all 0.3s;
                }
                .btn-vip:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 10px 25px rgba(0,255,255,0.4);
                }
            </style>
        </head>
        <body>
            <div class="vip-container">
                <div class="title">❌ TASK NOT FOUND</div>
                <p style="color: var(--cyan);">Task ID <span style="color: var(--gold);">{{ task_id }}</span> is not active.</p>
                <a href="/" class="btn-vip">🎯 NEW MISSION</a>
            </div>
        </body>
        </html>
    ''', task_id=task_id), 404

@app.route('/stop', methods=['POST'])
def stop_task_form():
    task_id = request.form.get('taskId')
    if task_id and task_id in stop_events:
        stop_events[task_id].set()
        return f"Task {task_id} stopped successfully!"
    return "Task not found or already stopped!", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 AAHAN CONVO PANEL starting on port {port}...")
    app.run(host='0.0.0.0', port=port)
