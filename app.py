from flask import Flask, request, render_template_string
import requests
import time
import secrets
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['SECRET_KEY'] = 'your-secret-key-here'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables to track tasks
active_tasks = {}

def check_facebook_token(token):
    """Check if Facebook token is valid"""
    try:
        url = f"https://graph.facebook.com/v19.0/me?access_token={token}"
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except:
        return False

def send_facebook_post(token, group_id, message, image_path=None):
    """Send post to Facebook group/page"""
    try:
        if image_path and os.path.exists(image_path):
            # Send with image
            print(f"📸 Sending with image: {image_path}")
            with open(image_path, 'rb') as img:
                files = {'source': img}
                data = {
                    'message': message,
                    'access_token': token
                }
                response = requests.post(
                    f'https://graph.facebook.com/v19.0/{group_id}/photos',
                    files=files,
                    data=data,
                    timeout=30
                )
        else:
            # Send text only
            print(f"📝 Sending text only")
            response = requests.post(
                f'https://graph.facebook.com/v19.0/{group_id}/feed',
                data={
                    'message': message,
                    'access_token': token
                },
                timeout=15
            )
        
        print(f"📤 Response: {response.status_code}")
        if response.status_code == 200:
            print("✅ Post successful!")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"🔥 Error: {str(e)}")
        return False

def start_sending_task(task_data):
    """Start sending messages in background"""
    task_id = task_data['task_id']
    
    try:
        print(f"🚀 Starting task {task_id}")
        print(f"📋 Target: {task_data['group_id']}")
        print(f"💬 Messages: {len(task_data['messages'])}")
        print(f"🖼️ Images: {len(task_data['image_paths'])}")
        print(f"🔑 Tokens: {len(task_data['valid_tokens'])}")
        
        message_count = 0
        image_count = 0
        
        while message_count < len(task_data['messages']) and active_tasks[task_id]['running']:
            current_message = task_data['messages'][message_count]
            full_message = f"{task_data['prefix']} {current_message}".strip()
            
            # Get current image (cycle through available images)
            current_image = None
            if task_data['image_paths']:
                current_image = task_data['image_paths'][image_count % len(task_data['image_paths'])]
            
            print(f"\n📨 Sending {message_count + 1}/{len(task_data['messages'])}")
            print(f"📝 Message: {full_message[:50]}...")
            print(f"🖼️ Image: {current_image}")
            
            # Send with each valid token
            for token in task_data['valid_tokens']:
                if not active_tasks[task_id]['running']:
                    break
                    
                success = send_facebook_post(token, task_data['group_id'], full_message, current_image)
                if success:
                    active_tasks[task_id]['stats']['success'] += 1
                else:
                    active_tasks[task_id]['stats']['failed'] += 1
                
                # Update last activity
                active_tasks[task_id]['last_activity'] = datetime.now().isoformat()
                
                # Wait before next send
                if active_tasks[task_id]['running']:
                    print(f"⏳ Waiting {task_data['delay']} seconds...")
                    time.sleep(task_data['delay'])
            
            message_count += 1
            image_count += 1
        
        print(f"✅ Task {task_id} completed!")
        active_tasks[task_id]['running'] = False
        active_tasks[task_id]['completed'] = True
        
    except Exception as e:
        print(f"🔥 Task error: {str(e)}")
        active_tasks[task_id]['running'] = False
        active_tasks[task_id]['error'] = str(e)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            # Get form data
            group_id = request.form.get('group_id', '').strip()
            prefix = request.form.get('prefix', '').strip()
            delay = int(request.form.get('delay', 10))
            
            # Get messages
            messages_text = request.form.get('messages', '')
            messages = [m.strip() for m in messages_text.split('\n') if m.strip()]
            
            # Get tokens
            token_text = request.form.get('tokens', '')
            tokens = [t.strip() for t in token_text.split('\n') if t.strip()]
            
            # Validate inputs
            if not group_id:
                return "❌ Group ID is required"
            if not messages:
                return "❌ Messages are required"
            if not tokens:
                return "❌ Access tokens are required"
            
            # Validate tokens
            valid_tokens = []
            invalid_tokens = []
            
            print("🔍 Validating tokens...")
            for token in tokens:
                if check_facebook_token(token):
                    valid_tokens.append(token)
                    print(f"✅ Valid token: {token[:20]}...")
                else:
                    invalid_tokens.append(token)
                    print(f"❌ Invalid token: {token[:20]}...")
            
            if not valid_tokens:
                return "❌ No valid tokens found. Please check your access tokens."
            
            # Handle image uploads
            image_paths = []
            if 'images' in request.files:
                for img_file in request.files.getlist('images'):
                    if img_file and img_file.filename:
                        # Save image
                        filename = f"{secrets.token_hex(8)}_{img_file.filename}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        img_file.save(filepath)
                        image_paths.append(filepath)
                        print(f"✅ Image saved: {filename}")
            
            # Create task
            task_id = secrets.token_hex(8)
            task_data = {
                'task_id': task_id,
                'group_id': group_id,
                'prefix': prefix,
                'delay': delay,
                'messages': messages,
                'image_paths': image_paths,
                'valid_tokens': valid_tokens,
                'invalid_tokens': invalid_tokens,
                'start_time': datetime.now().isoformat()
            }
            
            # Start task
            active_tasks[task_id] = {
                'running': True,
                'completed': False,
                'stats': {'success': 0, 'failed': 0},
                'last_activity': datetime.now().isoformat(),
                'error': None
            }
            
            # Start background thread
            import threading
            thread = threading.Thread(target=start_sending_task, args=(task_data,))
            thread.daemon = True
            thread.start()
            
            # Success response
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Task Started</title>
                <meta http-equiv="refresh" content="2;url=/status/{task_id}">
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 50px;
                        text-align: center;
                    }}
                    .success {{ 
                        background: rgba(255,255,255,0.1); 
                        padding: 30px; 
                        border-radius: 15px;
                        backdrop-filter: blur(10px);
                        margin: 20px auto;
                        max-width: 500px;
                    }}
                    .loading {{
                        font-size: 18px;
                        margin: 20px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="success">
                    <h2>🚀 TASK STARTED SUCCESSFULLY!</h2>
                    <div class="loading">
                        <p>📋 Task ID: <strong>{task_id}</strong></p>
                        <p>⏳ Redirecting to status page...</p>
                    </div>
                </div>
            </body>
            </html>
            '''
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    # Main form
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Facebook Auto Poster</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: rgba(255,255,255,0.95);
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            h1 {
                text-align: center;
                color: #764ba2;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .form-group {
                margin-bottom: 25px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #555;
            }
            input, textarea, select {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input:focus, textarea:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            textarea {
                min-height: 100px;
                resize: vertical;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                transition: transform 0.2s;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 30px;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }
            .instructions {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                border-left: 4px solid #667eea;
            }
            .instructions h3 {
                color: #764ba2;
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Facebook Auto Poster</h1>
            
            <div class="instructions">
                <h3>📋 How to Use:</h3>
                <p>1. Get Facebook Access Token from developers.facebook.com</p>
                <p>2. Enter Group/Page ID where you want to post</p>
                <p>3. Add your messages (one per line)</p>
                <p>4. Upload images (optional)</p>
                <p>5. Set delay between posts</p>
                <p>6. Click START POSTING!</p>
            </div>
            
            <form method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label>🔑 Facebook Group/Page ID:</label>
                    <input type="text" name="group_id" placeholder="e.g., 123456789012345" required>
                </div>
                
                <div class="form-group">
                    <label>📝 Message Prefix (Optional):</label>
                    <input type="text" name="prefix" placeholder="Add prefix to all messages">
                </div>
                
                <div class="form-group">
                    <label>⏰ Delay between posts (seconds):</label>
                    <input type="number" name="delay" value="10" min="5" required>
                </div>
                
                <div class="form-group">
                    <label>💬 Messages (one per line):</label>
                    <textarea name="messages" placeholder="Enter your messages here, one message per line&#10;Example:&#10;Hello world!&#10;This is test message&#10;Another message" required></textarea>
                </div>
                
                <div class="form-group">
                    <label>🖼️ Images (Optional, multiple allowed):</label>
                    <input type="file" name="images" multiple accept="image/*">
                </div>
                
                <div class="form-group">
                    <label>🔐 Facebook Access Tokens (one per line):</label>
                    <textarea name="tokens" placeholder="Paste your Facebook access tokens here, one token per line&#10;Example:&#10;EAABwzLixnjYBO...&#10;EAABwzLixnjYBO..." required></textarea>
                </div>
                
                <button type="submit" class="btn">🚀 START POSTING</button>
            </form>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>📊 Active Tasks</h3>
                    <p>''' + str(len([t for t in active_tasks.values() if t['running']])) + '''</p>
                </div>
                <div class="stat-card">
                    <h3>✅ Completed</h3>
                    <p>''' + str(len([t for t in active_tasks.values() if t['completed']])) + '''</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/status/<task_id>')
def task_status(task_id):
    if task_id not in active_tasks:
        return "Task not found"
    
    task = active_tasks[task_id]
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Task Status</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 50px;
                text-align: center;
            }
            .status-card { 
                background: rgba(255,255,255,0.1); 
                padding: 30px; 
                border-radius: 15px;
                backdrop-filter: blur(10px);
                margin: 20px auto;
                max-width: 600px;
            }
            .running { color: #4CAF50; }
            .stopped { color: #f44336; }
            .stats { 
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin: 20px 0;
            }
            .stat { 
                background: rgba(255,255,255,0.2);
                padding: 15px;
                border-radius: 10px;
            }
        </style>
    </head>
    <body>
        <div class="status-card">
            <h2>📊 Task Status: {task_id}</h2>
            <p><strong>Status:</strong> <span class="{'running' if task['running'] else 'stopped'}">{'🟢 RUNNING' if task['running'] else '🔴 STOPPED'}</span></p>
            
            <div class="stats">
                <div class="stat">
                    <h3>✅ Successful</h3>
                    <p>{task['stats']['success']}</p>
                </div>
                <div class="stat">
                    <h3>❌ Failed</h3>
                    <p>{task['stats']['failed']}</p>
                </div>
            </div>
            
            <p><strong>Last Activity:</strong> {task['last_activity']}</p>
            
            {f"<p><strong>Error:</strong> {task['error']}</p>" if task['error'] else ""}
            
            <div style="margin-top: 20px;">
                <a href="/" style="color: #4CAF50; text-decoration: none;">← Back to Home</a> | 
                <a href="/stop/{task_id}" style="color: #f44336; text-decoration: none;">🛑 Stop Task</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/stop/<task_id>')
def stop_task(task_id):
    if task_id in active_tasks:
        active_tasks[task_id]['running'] = False
        return f"Task {task_id} stopped successfully!"
    return "Task not found"

if __name__ == '__main__':
    print("🚀 Facebook Auto Poster Starting...")
    print("📍 Server running on: http://localhost:5000")
    print("📝 Make sure you have:")
    print("   - Facebook access tokens with required permissions")
    print("   - Group/Page ID where you have posting permissions")
    print("   - Stable internet connection")
    app.run(host='0.0.0.0', port=5000, debug=True)
