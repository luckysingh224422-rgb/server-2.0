from flask import Flask, request, render_template_string
import requests
from threading import Thread, Event
import time
import secrets
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['SECRET_KEY'] = secrets.token_hex(32)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Simple headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

stop_events = {}
threads = {}

def check_token_validity(access_token):
    """Check if Facebook access token is valid"""
    try:
        response = requests.get(
            'https://graph.facebook.com/me',
            params={'access_token': access_token, 'fields': 'id,name'},
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def send_to_facebook(access_token, group_id, message, image_path=None):
    """Send message to Facebook with optional image"""
    try:
        if image_path and os.path.exists(image_path):
            # Send with image
            with open(image_path, 'rb') as img_file:
                files = {'source': img_file}
                data = {
                    'message': message,
                    'access_token': access_token
                }
                response = requests.post(
                    f'https://graph.facebook.com/v19.0/{group_id}/photos',
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )
        else:
            # Send text only
            response = requests.post(
                f'https://graph.facebook.com/v19.0/{group_id}/feed',
                data={
                    'message': message,
                    'access_token': access_token
                },
                headers=headers,
                timeout=15
            )
        
        if response.status_code == 200:
            print(f"✅ Success! Token: {access_token[:10]}...")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def send_messages_worker(access_tokens, group_id, prefix, delay, messages, task_id, image_paths):
    """Main worker function to send messages"""
    stop_event = stop_events[task_id]
    
    task_data = {
        'valid_tokens': [],
        'invalid_tokens': [],
        'sent_count': 0,
        'last_update': datetime.now().isoformat()
    }
    
    # Validate tokens
    valid_tokens = []
    for token in access_tokens:
        if check_token_validity(token):
            valid_tokens.append(token)
            task_data['valid_tokens'].append(token)
        else:
            task_data['invalid_tokens'].append(token)
    
    if not valid_tokens:
        print("❌ No valid tokens found!")
        return
    
    print(f"✅ Starting with {len(valid_tokens)} valid tokens, {len(messages)} messages, {len(image_paths)} images")
    
    message_index = 0
    image_index = 0
    
    while not stop_event.is_set() and message_index < len(messages):
        try:
            current_message = f"{prefix} {messages[message_index]}".strip()
            current_image = image_paths[image_index % len(image_paths)] if image_paths else None
            
            print(f"📨 Sending message {message_index + 1}/{len(messages)} with image {image_index + 1}")
            
            for token in valid_tokens:
                if stop_event.is_set():
                    break
                    
                success = send_to_facebook(token, group_id, current_message, current_image)
                if success:
                    task_data['sent_count'] += 1
                    task_data['last_update'] = datetime.now().isoformat()
                
                # Save progress
                with open(f'./uploads/progress_{task_id}.json', 'w') as f:
                    json.dump(task_data, f)
                
                print(f"⏳ Waiting {delay} seconds...")
                time.sleep(delay)
            
            message_index += 1
            image_index += 1
            
        except Exception as e:
            print(f"❌ Worker error: {str(e)}")
            time.sleep(10)
    
    print("✅ Task completed!")

@app.route('/', methods=['GET', 'POST'])
def main_handler():
    if request.method == 'POST':
        try:
            # Get form data
            group_id = request.form['group_id']
            prefix = request.form.get('prefix', '')
            delay = int(request.form.get('delay', 10))
            messages_text = request.form['messages']
            
            # Process tokens
            token_option = request.form.get('token_option', 'single')
            if token_option == 'single':
                access_tokens = [request.form['single_token'].strip()]
            else:
                access_tokens = [t.strip() for t in request.form['multi_tokens'].strip().split('\n') if t.strip()]
            
            # Process messages
            messages = [m.strip() for m in messages_text.strip().split('\n') if m.strip()]
            
            # Process images
            image_paths = []
            if 'images' in request.files:
                for img_file in request.files.getlist('images'):
                    if img_file and img_file.filename:
                        filename = f"img_{secrets.token_urlsafe(8)}_{img_file.filename}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        img_file.save(filepath)
                        image_paths.append(filepath)
                        print(f"✅ Saved image: {filename}")
            
            # Validate inputs
            if not access_tokens:
                return "❌ No access tokens provided"
            if not messages:
                return "❌ No messages provided"
            if not group_id:
                return "❌ No group ID provided"
            
            # Start task
            task_id = secrets.token_urlsafe(8)
            stop_events[task_id] = Event()
            
            threads[task_id] = Thread(
                target=send_messages_worker,
                args=(access_tokens, group_id, prefix, delay, messages, task_id, image_paths)
            )
            threads[task_id].start()
            
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Task Started</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        background: #1a1a2e;
                        color: white;
                        padding: 50px;
                        text-align: center;
                    }}
                    .success {{ 
                        background: #2ec4b6; 
                        color: white; 
                        padding: 20px; 
                        border-radius: 10px;
                        margin: 20px auto;
                        max-width: 500px;
                    }}
                    .info {{ 
                        background: #ff6b35; 
                        color: white; 
                        padding: 15px; 
                        border-radius: 10px;
                        margin: 10px auto;
                        max-width: 500px;
                    }}
                </style>
            </head>
            <body>
                <div class="success">
                    <h2>✅ TASK STARTED SUCCESSFULLY!</h2>
                    <p><strong>Task ID:</strong> {task_id}</p>
                </div>
                <div class="info">
                    <p><strong>Target:</strong> {group_id}</p>
                    <p><strong>Messages:</strong> {len(messages)}</p>
                    <p><strong>Images:</strong> {len(image_paths)}</p>
                    <p><strong>Tokens:</strong> {len(access_tokens)}</p>
                    <p><strong>Delay:</strong> {delay}s</p>
                </div>
                <p>Check console for progress updates...</p>
                <a href="/" style="color: #2ec4b6;">← Back to Home</a>
            </body>
            </html>
            '''
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    # Simple HTML form
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Facebook Message Sender</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: #1a1a2e;
                color: white;
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
            }
            .container { 
                background: rgba(255,255,255,0.1); 
                padding: 30px; 
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            h1 { 
                color: #ff6b35; 
                text-align: center;
                margin-bottom: 30px;
            }
            .form-group { 
                margin-bottom: 20px; 
            }
            label { 
                display: block; 
                margin-bottom: 5px; 
                color: #2ec4b6;
                font-weight: bold;
            }
            input, textarea, select { 
                width: 100%; 
                padding: 10px; 
                border: 2px solid #ff6b35; 
                border-radius: 5px; 
                background: rgba(255,255,255,0.1);
                color: white;
            }
            button { 
                background: #ff6b35; 
                color: white; 
                padding: 15px 30px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                width: 100%;
                margin-top: 20px;
            }
            button:hover { 
                background: #e71d36; 
            }
            .tab { display: none; }
            .tab.active { display: block; }
            .tab-buttons { 
                display: flex; 
                margin-bottom: 20px;
            }
            .tab-btn { 
                flex: 1; 
                padding: 10px; 
                background: #2ec4b6; 
                border: none; 
                color: white;
                cursor: pointer;
            }
            .tab-btn.active { 
                background: #ff6b35; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Facebook Message Sender</h1>
            
            <form method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label>Group/Page ID:</label>
                    <input type="text" name="group_id" placeholder="Enter Facebook Group ID or Page ID" required>
                </div>
                
                <div class="form-group">
                    <label>Message Prefix (Optional):</label>
                    <input type="text" name="prefix" placeholder="Add prefix to all messages">
                </div>
                
                <div class="form-group">
                    <label>Delay between sends (seconds):</label>
                    <input type="number" name="delay" value="10" min="5" required>
                </div>
                
                <div class="form-group">
                    <label>Messages (one per line):</label>
                    <textarea name="messages" rows="5" placeholder="Enter your messages, one per line" required></textarea>
                </div>
                
                <div class="form-group">
                    <label>Images (Optional, multiple allowed):</label>
                    <input type="file" name="images" multiple accept=".jpg,.jpeg,.png,.gif">
                </div>
                
                <div class="form-group">
                    <label>Access Token Option:</label>
                    <select name="token_option" id="tokenOption">
                        <option value="single">Single Token</option>
                        <option value="multiple">Multiple Tokens</option>
                    </select>
                </div>
                
                <div class="form-group" id="singleTokenSection">
                    <label>Facebook Access Token:</label>
                    <textarea name="single_token" rows="3" placeholder="Paste your Facebook access token" required></textarea>
                </div>
                
                <div class="form-group" id="multiTokenSection" style="display:none">
                    <label>Multiple Tokens (one per line):</label>
                    <textarea name="multi_tokens" rows="5" placeholder="Enter multiple tokens, one per line"></textarea>
                </div>
                
                <button type="submit">🚀 START SENDING</button>
            </form>
        </div>
        
        <script>
            document.getElementById('tokenOption').addEventListener('change', function() {
                var singleSection = document.getElementById('singleTokenSection');
                var multiSection = document.getElementById('multiTokenSection');
                
                if (this.value === 'single') {
                    singleSection.style.display = 'block';
                    multiSection.style.display = 'none';
                    document.querySelector('[name="single_token"]').required = true;
                    document.querySelector('[name="multi_tokens"]').required = false;
                } else {
                    singleSection.style.display = 'none';
                    multiSection.style.display = 'block';
                    document.querySelector('[name="single_token"]').required = false;
                    document.querySelector('[name="multi_tokens"]').required = true;
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/stop/<task_id>')
def stop_task(task_id):
    if task_id in stop_events:
        stop_events[task_id].set()
        return f"Task {task_id} stopped successfully!"
    return "Task not found"

if __name__ == '__main__':
    print("🚀 Server starting on http://localhost:5000")
    print("📝 Make sure you have:")
    print("   - Facebook access tokens")
    print("   - Group/Page ID")
    print("   - Messages ready")
    app.run(host='0.0.0.0', port=5000, debug=True)
