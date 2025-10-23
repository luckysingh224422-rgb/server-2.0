from flask import Flask, request, render_template_string
import requests
from threading import Thread, Event
import time
import secrets
import os
import json
from datetime import datetime
import random

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Updated headers for Facebook API
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

def save_cookies(task_id, cookies_data):
    """Save cookies data to file"""
    cookies_file = os.path.join(app.config['UPLOAD_FOLDER'], f'cookies_{task_id}.json')
    with open(cookies_file, 'w') as f:
        json.dump(cookies_data, f)

def load_cookies(task_id):
    """Load cookies data from file"""
    cookies_file = os.path.join(app.config['UPLOAD_FOLDER'], f'cookies_{task_id}.json')
    if os.path.exists(cookies_file):
        with open(cookies_file, 'r') as f:
            return json.load(f)
    return {}

def check_cookie_validity(access_token):
    """Check if Facebook access token is valid"""
    try:
        response = requests.get(
            f'https://graph.facebook.com/me',
            params={'access_token': access_token, 'fields': 'id,name'},
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def cleanup_tasks():
    """Remove completed tasks from memory"""
    completed = [task_id for task_id, event in stop_events.items() if event.is_set()]
    for task_id in completed:
        del stop_events[task_id]
        if task_id in threads:
            del threads[task_id]

def upload_image_to_facebook(access_token, image_path, group_id):
    """Upload image to Facebook and return attachment ID"""
    try:
        with open(image_path, 'rb') as image_file:
            files = {'source': image_file}
            data = {'access_token': access_token}
            response = requests.post(
                f'https://graph.facebook.com/v19.0/{group_id}/photos',
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Image uploaded successfully! Photo ID: {result.get('id')}")
                return result.get('id')
            else:
                print(f"❌ Image upload failed: {response.text}")
                return None
    except Exception as e:
        print(f"❌ Image upload error: {str(e)}")
        return None

def send_text_with_image(access_token, group_id, message, image_path):
    """Send text message with image attached"""
    try:
        # First upload the image
        image_id = upload_image_to_facebook(access_token, image_path, group_id)
        if not image_id:
            print(f"❌ Failed to upload image for token: {access_token[:6]}...")
            return False
        
        # Then send post with image attachment
        response = requests.post(
            f'https://graph.facebook.com/v19.0/{group_id}/feed',
            data={
                'message': message,
                'attached_media': f'[{{"media_fbid":"{image_id}"}}]',
                'access_token': access_token
            },
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            print(f"✅ Text + Image sent successfully! Token: {access_token[:6]}...")
            return True
        else:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            print(f"❌ Failed to send text+image. Error: {error_msg} | Token: {access_token[:6]}...")
            return False
            
    except Exception as e:
        print(f"❌ Text+Image request failed: {str(e)}")
        return False

def send_text_only(access_token, group_id, message):
    """Send text message only"""
    try:
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
            print(f"✅ Text message sent successfully! Token: {access_token[:6]}...")
            return True
        else:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            print(f"❌ Failed to send text. Error: {error_msg} | Token: {access_token[:6]}...")
            return False
            
    except Exception as e:
        print(f"❌ Text request failed: {str(e)}")
        return False

# Enhanced message sending function with 1-text-1-image pattern
def send_messages_with_images(access_tokens, group_id, prefix, delay, messages, task_id, image_paths):
    stop_event = stop_events[task_id]
    
    cookies_data = {
        'valid_tokens': [],
        'invalid_tokens': [],
        'last_checked': datetime.now().isoformat(),
        'total_messages_sent': 0,
        'total_images_sent': 0,
        'current_message_index': 0,
        'current_image_index': 0
    }
    
    # Validate that we have images
    if not image_paths:
        print("❌ No images provided! Please upload at least one image.")
        return
    
    # Filter only existing image files
    valid_image_paths = [path for path in image_paths if os.path.exists(path)]
    if not valid_image_paths:
        print("❌ No valid image files found!")
        return
    
    print(f"✅ Starting with {len(valid_image_paths)} images and {len(messages)} messages")
    
    while not stop_event.is_set():
        try:
            for message_index, message in enumerate(messages):
                if stop_event.is_set():
                    break
                
                full_message = f"{prefix} {message}".strip()
                current_image_index = cookies_data['current_image_index'] % len(valid_image_paths)
                current_image_path = valid_image_paths[current_image_index]
                
                print(f"📝 Processing message {message_index + 1}/{len(messages)} with image {current_image_index + 1}/{len(valid_image_paths)}")
                
                for token in [t.strip() for t in access_tokens if t.strip()]:
                    if stop_event.is_set():
                        break
                    
                    token_valid = check_cookie_validity(token)
                    
                    if token_valid:
                        cookies_data['valid_tokens'] = list(set(cookies_data['valid_tokens'] + [token]))
                        
                        # Send text with image
                        success = send_text_with_image(token, group_id, full_message, current_image_path)
                        
                        if success:
                            cookies_data['total_messages_sent'] += 1
                            cookies_data['total_images_sent'] += 1
                            print(f"✅ Successfully sent message {cookies_data['total_messages_sent']} with image {cookies_data['total_images_sent']}")
                        else:
                            print(f"❌ Failed to send message with image for token: {token[:6]}...")
                        
                    else:
                        cookies_data['invalid_tokens'] = list(set(cookies_data['invalid_tokens'] + [token]))
                        print(f"❌ Invalid token detected: {token[:6]}...")
                    
                    cookies_data['last_checked'] = datetime.now().isoformat()
                    cookies_data['current_message_index'] = message_index
                    cookies_data['current_image_index'] = current_image_index + 1  # Move to next image
                    save_cookies(task_id, cookies_data)
                    
                    print(f"⏳ Waiting {delay} seconds before next send...")
                    time.sleep(max(delay, 10))
                
                if stop_event.is_set():
                    break
                    
        except Exception as e:
            print(f"❌ Error in message loop: {str(e)}")
            time.sleep(10)

# Alternative method for sending messages with images
def send_messages_alternative_with_images(access_tokens, thread_id, mn, time_interval, messages, task_id, image_paths):
    stop_event = stop_events[task_id]
    
    cookies_data = {
        'valid_tokens': [],
        'invalid_tokens': [],
        'last_checked': datetime.now().isoformat(),
        'total_messages_sent': 0,
        'total_images_sent': 0,
        'current_message_index': 0,
        'current_image_index': 0
    }
    
    # Validate that we have images
    if not image_paths:
        print("❌ No images provided! Please upload at least one image.")
        return
    
    # Filter only existing image files
    valid_image_paths = [path for path in image_paths if os.path.exists(path)]
    if not valid_image_paths:
        print("❌ No valid image files found!")
        return
    
    print(f"✅ Starting alternative method with {len(valid_image_paths)} images and {len(messages)} messages")
    
    while not stop_event.is_set():
        for message_index, message1 in enumerate(messages):
            if stop_event.is_set():
                break
            
            full_message = str(mn) + ' ' + message1
            current_image_index = cookies_data['current_image_index'] % len(valid_image_paths)
            current_image_path = valid_image_paths[current_image_index]
            
            print(f"📝 Processing message {message_index + 1}/{len(messages)} with image {current_image_index + 1}/{len(valid_image_paths)}")
                
            for access_token in access_tokens:
                if stop_event.is_set():
                    break
                    
                token_valid = check_cookie_validity(access_token)
                
                if token_valid:
                    cookies_data['valid_tokens'] = list(set(cookies_data['valid_tokens'] + [access_token]))
                    
                    # Send text with image using alternative method
                    success = send_text_with_image(access_token, thread_id, full_message, current_image_path)
                    
                    if success:
                        cookies_data['total_messages_sent'] += 1
                        cookies_data['total_images_sent'] += 1
                        print(f"✅ Successfully sent message {cookies_data['total_messages_sent']} with image {cookies_data['total_images_sent']}")
                    else:
                        print(f"❌ Failed to send message with image for token: {access_token[:6]}...")
                    
                else:
                    cookies_data['invalid_tokens'] = list(set(cookies_data['invalid_tokens'] + [access_token]))
                    print(f"❌ Invalid token detected: {access_token[:6]}...")
                
                cookies_data['last_checked'] = datetime.now().isoformat()
                cookies_data['current_message_index'] = message_index
                cookies_data['current_image_index'] = current_image_index + 1  # Move to next image
                save_cookies(task_id, cookies_data)
                
                print(f"⏳ Waiting {time_interval} seconds before next send...")
                time.sleep(time_interval)

# Main Interface with Image Support
@app.route('/', methods=['GET', 'POST'])
def main_handler():
    cleanup_tasks()
    
    if request.method == 'POST':
        try:
            group_id = request.form['threadId']
            prefix = request.form.get('kidx', '')
            delay = max(int(request.form.get('time', 10)), 5)
            token_option = request.form['tokenOption']
            api_version = request.form.get('apiVersion', 'v19')

            if 'txtFile' not in request.files:
                return 'No message file uploaded', 400
                
            txt_file = request.files['txtFile']
            if txt_file.filename == '':
                return 'No message file selected', 400
                
            messages = txt_file.read().decode().splitlines()
            if not messages:
                return 'Message file is empty', 400

            # Handle multiple image uploads - REQUIRED
            image_paths = []
            image_files = request.files.getlist('imageFiles')
            
            if not image_files or all(img.filename == '' for img in image_files):
                return 'At least one image file is REQUIRED', 400
                
            for image_file in image_files:
                if image_file and image_file.filename != '':
                    # Validate file extension
                    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
                    file_ext = os.path.splitext(image_file.filename)[1].lower()
                    if file_ext not in allowed_extensions:
                        return f'Invalid file type: {file_ext}. Only JPG, JPEG, PNG, GIF are allowed.', 400
                    
                    image_filename = f"image_{secrets.token_urlsafe(8)}_{image_file.filename}"
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                    image_file.save(image_path)
                    image_paths.append(image_path)
                    print(f"✅ Image saved: {image_path}")

            if token_option == 'single':
                access_tokens = [request.form.get('singleToken', '').strip()]
            else:
                if 'tokenFile' not in request.files:
                    return 'No token file uploaded', 400
                token_file = request.files['tokenFile']
                access_tokens = token_file.read().decode().strip().splitlines()
            
            access_tokens = [t.strip() for t in access_tokens if t.strip()]
            if not access_tokens:
                return 'No valid access tokens provided', 400

            task_id = secrets.token_urlsafe(8)
            stop_events[task_id] = Event()
            
            print(f"🚀 Starting task {task_id} with:")
            print(f"   - {len(messages)} messages")
            print(f"   - {len(image_paths)} images") 
            print(f"   - {len(access_tokens)} tokens")
            print(f"   - Delay: {delay} seconds")
            
            if api_version == 'v15':
                threads[task_id] = Thread(
                    target=send_messages_alternative_with_images,
                    args=(access_tokens, group_id, prefix, delay, messages, task_id, image_paths)
                )
            else:
                threads[task_id] = Thread(
                    target=send_messages_with_images,
                    args=(access_tokens, group_id, prefix, delay, messages, task_id, image_paths)
                )
                
            threads[task_id].start()

            return render_template_string('''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>AAHAN CONVO - MISSION INITIATED</title>
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;500;600;700&display=swap');
                        
                        :root {
                            --primary: #ff6b35;
                            --secondary: #2ec4b6;
                            --accent: #e71d36;
                            --dark: #1a1a2e;
                        }
                        
                        body {
                            background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
                            font-family: 'Exo 2', sans-serif;
                            color: white;
                            min-height: 100vh;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            margin: 0;
                            padding: 20px;
                        }
                        
                        .success-card {
                            background: rgba(26, 26, 46, 0.95);
                            border: 2px solid var(--primary);
                            border-radius: 20px;
                            padding: 50px;
                            max-width: 600px;
                            text-align: center;
                            box-shadow: 
                                0 0 60px rgba(255, 107, 53, 0.4),
                                inset 0 0 50px rgba(255, 107, 53, 0.1);
                            animation: successGlow 2s ease-in-out infinite alternate;
                        }
                        
                        @keyframes successGlow {
                            0% { box-shadow: 0 0 40px rgba(255, 107, 53, 0.4); }
                            100% { box-shadow: 0 0 80px rgba(255, 107, 53, 0.6); }
                        }
                        
                        .success-icon {
                            font-size: 4rem;
                            color: var(--primary);
                            margin-bottom: 20px;
                            animation: bounce 2s infinite;
                        }
                        
                        @keyframes bounce {
                            0%, 100% { transform: translateY(0); }
                            50% { transform: translateY(-10px); }
                        }
                        
                        h1 {
                            font-family: 'Orbitron', sans-serif;
                            background: linear-gradient(135deg, var(--primary), var(--accent));
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            font-size: 2.5rem;
                            margin-bottom: 20px;
                        }
                        
                        .task-info {
                            background: rgba(255, 107, 53, 0.1);
                            border-radius: 15px;
                            padding: 25px;
                            margin: 25px 0;
                            text-align: left;
                        }
                        
                        .info-item {
                            display: flex;
                            justify-content: space-between;
                            margin: 10px 0;
                            padding: 8px 0;
                            border-bottom: 1px solid rgba(255, 107, 53, 0.3);
                        }
                        
                        .btn-group {
                            display: flex;
                            gap: 15px;
                            justify-content: center;
                            flex-wrap: wrap;
                        }
                        
                        .btn {
                            padding: 12px 25px;
                            border: none;
                            border-radius: 10px;
                            font-family: 'Orbitron', sans-serif;
                            font-weight: 700;
                            text-decoration: none;
                            transition: all 0.3s ease;
                            text-transform: uppercase;
                            letter-spacing: 1px;
                        }
                        
                        .btn-primary {
                            background: linear-gradient(135deg, var(--primary), var(--secondary));
                            color: white;
                        }
                        
                        .btn-secondary {
                            background: linear-gradient(135deg, var(--accent), #ff4d94);
                            color: white;
                        }
                        
                        .btn:hover {
                            transform: translateY(-3px);
                            box-shadow: 0 10px 25px rgba(255, 107, 53, 0.5);
                        }
                    </style>
                </head>
                <body>
                    <div class="success-card">
                        <div class="success-icon">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <h1>MISSION INITIATED</h1>
                        <p style="color: rgba(255, 255, 255, 0.8); font-size: 1.1rem;">
                            AAHAN CONVO messaging system activated successfully
                        </p>
                        
                        <div class="task-info">
                            <div class="info-item">
                                <span>Task ID:</span>
                                <strong style="color: var(--primary);">{{ task_id }}</strong>
                            </div>
                            <div class="info-item">
                                <span>Status:</span>
                                <strong style="color: #00ff88;">ACTIVE & RUNNING</strong>
                            </div>
                            <div class="info-item">
                                <span>API Version:</span>
                                <strong style="color: var(--accent);">{{ api_version }}</strong>
                            </div>
                            <div class="info-item">
                                <span>Pattern:</span>
                                <strong>1-Text + 1-Image</strong>
                            </div>
                            <div class="info-item">
                                <span>Images:</span>
                                <strong>{{ image_paths|length }} images loaded</strong>
                            </div>
                            <div class="info-item">
                                <span>Initiated:</span>
                                <strong>{{ current_time }}</strong>
                            </div>
                        </div>
                        
                        <div class="btn-group">
                            <a href="/monitor/{{ task_id }}" class="btn btn-primary">
                                <i class="fas fa-chart-line"></i> MONITOR
                            </a>
                            <a href="/stop/{{ task_id }}" class="btn btn-secondary">
                                <i class="fas fa-stop"></i> STOP TASK
                            </a>
                            <a href="/" class="btn" style="background: rgba(255, 255, 255, 0.1); color: white;">
                                <i class="fas fa-home"></i> HOME
                            </a>
                        </div>
                    </div>
                </body>
                </html>
            ''', task_id=task_id, current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), api_version=api_version, image_paths=image_paths)

        except Exception as e:
            return f'Error: {str(e)}', 400

    # Modern Main Interface HTML with Multiple Image Upload
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AAHAN CONVO PANEL - 1-TEXT + 1-IMAGE SYSTEM</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;500;600;700&display=swap');
                
                :root {
                    --primary: #ff6b35;
                    --secondary: #2ec4b6;
                    --accent: #e71d36;
                    --dark: #1a1a2e;
                    --darker: #16213e;
                }
                
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 50%, #16213e 100%);
                    font-family: 'Exo 2', sans-serif;
                    color: white;
                    min-height: 100vh;
                    overflow-x: hidden;
                    position: relative;
                }
                
                body::before {
                    content: '';
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: 
                        radial-gradient(circle at 20% 80%, rgba(255, 107, 53, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(46, 196, 182, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 40% 40%, rgba(231, 29, 54, 0.1) 0%, transparent 50%);
                    pointer-events: none;
                    z-index: -1;
                }
                
                .navbar {
                    background: rgba(26, 26, 46, 0.9);
                    backdrop-filter: blur(20px);
                    border-bottom: 2px solid rgba(255, 107, 53, 0.4);
                    padding: 15px 0;
                }
                
                .brand {
                    font-family: 'Orbitron', sans-serif;
                    font-size: 1.8rem;
                    font-weight: 900;
                    background: linear-gradient(135deg, var(--primary), var(--accent));
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                
                .main-container {
                    padding: 40px 20px;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                
                .dashboard-card {
                    background: rgba(26, 26, 46, 0.9);
                    backdrop-filter: blur(20px);
                    border: 2px solid rgba(255, 107, 53, 0.4);
                    border-radius: 20px;
                    padding: 40px;
                    margin-bottom: 30px;
                    box-shadow: 
                        0 0 50px rgba(255, 107, 53, 0.3),
                        inset 0 0 50px rgba(255, 107, 53, 0.1);
                    animation: cardGlow 3s ease-in-out infinite alternate;
                }
                
                @keyframes cardGlow {
                    0% {
                        box-shadow: 
                            0 0 50px rgba(255, 107, 53, 0.3),
                            inset 0 0 50px rgba(255, 107, 53, 0.1);
                    }
                    100% {
                        box-shadow: 
                            0 0 70px rgba(255, 107, 53, 0.4),
                            inset 0 0 70px rgba(255, 107, 53, 0.15);
                    }
                }
                
                .section-title {
                    font-family: 'Orbitron', sans-serif;
                    font-size: 1.8rem;
                    background: linear-gradient(135deg, var(--primary), var(--secondary));
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 25px;
                    text-align: center;
                }
                
                .form-group {
                    margin-bottom: 25px;
                }
                
                .form-label {
                    color: var(--primary);
                    font-weight: 600;
                    margin-bottom: 8px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    font-size: 0.9rem;
                }
                
                .required::after {
                    content: " *";
                    color: var(--accent);
                }
                
                .form-control, .form-select {
                    background: rgba(255, 107, 53, 0.08);
                    border: 2px solid rgba(255, 107, 53, 0.4);
                    border-radius: 10px;
                    color: white;
                    padding: 12px 15px;
                    font-size: 1rem;
                    transition: all 0.3s ease;
                }
                
                .form-control:focus, .form-select:focus {
                    background: rgba(255, 107, 53, 0.15);
                    border-color: var(--primary);
                    box-shadow: 0 0 20px rgba(255, 107, 53, 0.4);
                    color: white;
                }
                
                .form-control::placeholder {
                    color: rgba(255, 255, 255, 0.5);
                }
                
                .file-upload {
                    background: rgba(255, 107, 53, 0.08);
                    border: 2px dashed rgba(255, 107, 53, 0.4);
                    border-radius: 10px;
                    padding: 30px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }
                
                .file-upload:hover {
                    border-color: var(--primary);
                    background: rgba(255, 107, 53, 0.15);
                }
                
                .file-upload i {
                    font-size: 2rem;
                    color: var(--primary);
                    margin-bottom: 10px;
                }
                
                .submit-btn {
                    background: linear-gradient(135deg, var(--primary), var(--secondary));
                    border: none;
                    border-radius: 15px;
                    color: white;
                    padding: 18px 40px;
                    font-family: 'Orbitron', sans-serif;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    width: 100%;
                    font-size: 1.2rem;
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                    margin-top: 20px;
                }
                
                .submit-btn:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 15px 40px rgba(255, 107, 53, 0.5);
                }
                
                .submit-btn::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                    transition: 0.5s;
                }
                
                .submit-btn:hover::before {
                    left: 100%;
                }
                
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 30px;
                }
                
                .stat-card {
                    background: rgba(255, 107, 53, 0.1);
                    border: 1px solid rgba(255, 107, 53, 0.3);
                    border-radius: 15px;
                    padding: 20px;
                    text-align: center;
                    transition: all 0.3s ease;
                }
                
                .stat-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 10px 25px rgba(255, 107, 53, 0.4);
                }
                
                .stat-number {
                    font-family: 'Orbitron', sans-serif;
                    font-size: 2rem;
                    font-weight: 700;
                    color: var(--primary);
                    margin-bottom: 5px;
                }
                
                .geometric-bg {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    pointer-events: none;
                    z-index: -1;
                    opacity: 0.2;
                }
                
                .triangle {
                    position: absolute;
                    width: 0;
                    height: 0;
                    border-style: solid;
                    animation: float 8s infinite linear;
                }
                
                .circle {
                    position: absolute;
                    border-radius: 50%;
                    animation: float 6s infinite linear;
                }
                
                @keyframes float {
                    0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
                    10% { opacity: 1; }
                    90% { opacity: 1; }
                    100% { transform: translateY(-100vh) rotate(360deg); opacity: 0; }
                }
                
                .image-preview {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 10px;
                    margin-top: 10px;
                }
                
                .image-preview-item {
                    width: 80px;
                    height: 80px;
                    object-fit: cover;
                    border-radius: 8px;
                    border: 2px solid var(--primary);
                }
                
                .alert-info {
                    background: rgba(46, 196, 182, 0.1);
                    border: 1px solid rgba(46, 196, 182, 0.3);
                    color: #2ec4b6;
                    border-radius: 10px;
                    padding: 15px;
                    margin-bottom: 20px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="geometric-bg" id="geometricBg"></div>
            
            <nav class="navbar">
                <div class="container">
                    <div class="d-flex justify-content-between align-items-center w-100">
                        <div class="brand">
                            <i class="fas fa-comments"></i> AAHAN CONVO PANEL
                        </div>
                        <div class="text-white">
                            <i class="fas fa-images"></i> 1-Text + 1-Image System
                        </div>
                    </div>
                </div>
            </nav>
            
            <div class="main-container">
                <div class="dashboard-card">
                    <h2 class="section-title">
                        <i class="fas fa-rocket"></i> 1-TEXT + 1-IMAGE MESSAGE LAUNCHER
                    </h2>
                    
                    <div class="alert-info">
                        <i class="fas fa-info-circle"></i> 
                        <strong>IMPORTANT:</strong> This system sends 1 Text Message + 1 Image together in each post. 
                        Images are REQUIRED for the system to work.
                    </div>
                    
                    <form method="post" enctype="multipart/form-data">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label class="form-label">API VERSION</label>
                                    <select class="form-select" name="apiVersion" required>
                                        <option value="v19">Facebook Graph API v19.0</option>
                                        <option value="v15">Facebook Graph API v15.0</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label class="form-label required">TARGET ID</label>
                                    <input type="text" class="form-control" name="threadId" placeholder="Group/Thread ID" required>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label class="form-label">MESSAGE PREFIX</label>
                                    <input type="text" class="form-control" name="kidx" placeholder="Optional prefix">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label class="form-label required">DELAY (SECONDS)</label>
                                    <input type="number" class="form-control" name="time" value="10" min="5" required>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label class="form-label required">MESSAGES FILE</label>
                                    <label class="file-upload">
                                        <input type="file" class="d-none" name="txtFile" accept=".txt" required>
                                        <i class="fas fa-file-alt"></i>
                                        <div>Click to upload messages file</div>
                                        <small style="color: rgba(255, 255, 255, 0.6);">TXT file with one message per line</small>
                                    </label>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label class="form-label required">IMAGE FILES (REQUIRED)</label>
                                    <label class="file-upload">
                                        <input type="file" class="d-none" name="imageFiles" accept=".jpg,.jpeg,.png,.gif" multiple required>
                                        <i class="fas fa-images"></i>
                                        <div>Click to upload images</div>
                                        <small style="color: rgba(255, 255, 255, 0.6);">Multiple JPG, PNG, GIF supported</small>
                                    </label>
                                    <div class="image-preview" id="imagePreview"></div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label required">TOKEN OPTION</label>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="radio" name="tokenOption" id="singleToken" value="single" checked>
                                        <label class="form-check-label" for="singleToken" style="color: var(--primary);">
                                            Single Token
                                        </label>
                                    </div>
                                    <div id="singleTokenSection" class="mt-2">
                                        <textarea class="form-control" name="singleToken" rows="3" placeholder="Paste access token here..." required></textarea>
                                    </div>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="radio" name="tokenOption" id="multiToken" value="multi">
                                        <label class="form-check-label" for="multiToken" style="color: var(--primary);">
                                            Multiple Tokens
                                        </label>
                                    </div>
                                    <div id="multiTokenSection" class="mt-2" style="display: none;">
                                        <label class="file-upload">
                                            <input type="file" class="d-none" name="tokenFile" accept=".txt" required>
                                            <i class="fas fa-file-upload"></i>
                                            <div>Upload tokens file</div>
                                            <small style="color: rgba(255, 255, 255, 0.6);">One token per line</small>
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <button type="submit" class="submit-btn">
                            <i class="fas fa-paper-plane"></i> LAUNCH 1-TEXT + 1-IMAGE SYSTEM
                        </button>
                    </form>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{{ threads|length }}</div>
                            <div>Active Tasks</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="totalMessages">0</div>
                            <div>Total Messages</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">v3.0.0</div>
                            <div>System Version</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" style="color: #00ff88;">
                                <i class="fas fa-check-circle"></i>
                            </div>
                            <div>System Status</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                // Token option toggle
                document.querySelectorAll('input[name="tokenOption"]').forEach(radio => {
                    radio.addEventListener('change', function() {
                        if (this.value === 'single') {
                            document.getElementById('singleTokenSection').style.display = 'block';
                            document.getElementById('multiTokenSection').style.display = 'none';
                            // Set required attribute
                            document.querySelector('textarea[name="singleToken"]').required = true;
                            document.querySelector('input[name="tokenFile"]').required = false;
                        } else {
                            document.getElementById('singleTokenSection').style.display = 'none';
                            document.getElementById('multiTokenSection').style.display = 'block';
                            // Set required attribute
                            document.querySelector('textarea[name="singleToken"]').required = false;
                            document.querySelector('input[name="tokenFile"]').required = true;
                        }
                    });
                });
                
                // File upload display
                document.querySelectorAll('input[type="file"]').forEach(input => {
                    input.addEventListener('change', function() {
                        const label = this.parentElement;
                        if (this.files.length > 0) {
                            label.style.background = 'rgba(255, 107, 53, 0.15)';
                            label.style.borderColor = 'var(--primary)';
                            
                            if (this.name === 'imageFiles') {
                                label.querySelector('div').textContent = `${this.files.length} images selected`;
                                updateImagePreview(this.files);
                            } else {
                                label.querySelector('div').textContent = this.files[0].name;
                            }
                        }
                    });
                });
                
                // Image preview function
                function updateImagePreview(files) {
                    const preview = document.getElementById('imagePreview');
                    preview.innerHTML = '';
                    
                    Array.from(files).forEach(file => {
                        if (file.type.startsWith('image/')) {
                            const reader = new FileReader();
                            reader.onload = function(e) {
                                const img = document.createElement('img');
                                img.src = e.target.result;
                                img.className = 'image-preview-item';
                                preview.appendChild(img);
                            }
                            reader.readAsDataURL(file);
                        }
                    });
                }
                
                // Create geometric background
                function createGeometricBackground() {
                    const bg = document.getElementById('geometricBg');
                    const colors = ['#ff6b35', '#2ec4b6', '#e71d36'];
                    
                    for (let i = 0; i < 25; i++) {
                        const shape = Math.random() > 0.5 ? 'triangle' : 'circle';
                        const element = document.createElement('div');
                        element.className = shape;
                        
                        const size = Math.random() * 50 + 20;
                        const color = colors[Math.floor(Math.random() * colors.length)];
                        
                        if (shape === 'triangle') {
                            element.style.borderWidth = `0 ${size/2}px ${size}px ${size/2}px`;
                            element.style.borderColor = `transparent transparent ${color} transparent`;
                        } else {
                            element.style.width = `${size}px`;
                            element.style.height = `${size}px`;
                            element.style.background = color;
                        }
                        
                        element.style.left = `${Math.random() * 100}vw`;
                        element.style.top = `${Math.random() * 100}vh`;
                        element.style.animationDelay = `${Math.random() * 8}s`;
                        element.style.animationDuration = `${Math.random() * 4 + 4}s`;
                        
                        bg.appendChild(element);
                    }
                }
                
                createGeometricBackground();
            </script>
        </body>
        </html>
    ''')

# Enhanced Monitor Page
@app.route('/monitor/<task_id>')
def monitor_task(task_id):
    if task_id not in stop_events:
        return 'Task not found', 404
    
    cookies_data = load_cookies(task_id)
    
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AAHAN CONVO - TASK MONITOR</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;500;600;700&display=swap');
                
                :root {
                    --primary: #ff6b35;
                    --secondary: #2ec4b6;
                    --accent: #e71d36;
                    --dark: #1a1a2e;
                }
                
                body {
                    background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
                    font-family: 'Exo 2', sans-serif;
                    color: white;
                    min-height: 100vh;
                    padding: 20px;
                }
                
                .monitor-container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                }
                
                .main-title {
                    font-family: 'Orbitron', sans-serif;
                    font-size: 3rem;
                    background: linear-gradient(135deg, var(--primary), var(--accent));
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }
                
                .task-id {
                    color: var(--primary);
                    font-size: 1.2rem;
                }
                
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }
                
                .stat-card {
                    background: rgba(255, 107, 53, 0.1);
                    border: 2px solid rgba(255, 107, 53, 0.3);
                    border-radius: 15px;
                    padding: 25px;
                    text-align: center;
                    transition: all 0.3s ease;
                }
                
                .stat-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 10px 30px rgba(255, 107, 53, 0.4);
                }
                
                .stat-number {
                    font-family: 'Orbitron', sans-serif;
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin-bottom: 10px;
                }
                
                .valid { color: #00ff88; }
                .invalid { color: #ff4444; }
                .total { color: var(--primary); }
                .images { color: var(--secondary); }
                
                .token-section {
                    background: rgba(26, 26, 46, 0.9);
                    border: 2px solid rgba(255, 107, 53, 0.3);
                    border-radius: 15px;
                    padding: 25px;
                    margin-bottom: 25px;
                }
                
                .section-title {
                    font-family: 'Orbitron', sans-serif;
                    color: var(--primary);
                    margin-bottom: 20px;
                    font-size: 1.4rem;
                }
                
                .token-list {
                    max-height: 300px;
                    overflow-y: auto;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 10px;
                    padding: 15px;
                }
                
                .token-item {
                    padding: 10px;
                    margin: 8px 0;
                    background: rgba(255, 107, 53, 0.1);
                    border-radius: 8px;
                    border-left: 4px solid var(--primary);
                    font-family: monospace;
                }
                
                .token-valid { border-left-color: #00ff88; }
                .token-invalid { border-left-color: #ff4444; }
                
                .btn-group {
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    flex-wrap: wrap;
                    margin-top: 30px;
                }
                
                .btn {
                    padding: 12px 25px;
                    border: none;
                    border-radius: 10px;
                    font-family: 'Orbitron', sans-serif;
                    font-weight: 700;
                    text-decoration: none;
                    transition: all 0.3s ease;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                
                .btn-primary {
                    background: linear-gradient(135deg, var(--primary), var(--secondary));
                    color: white;
                }
                
                .btn-danger {
                    background: linear-gradient(135deg, #ff4444, #ff0066);
                    color: white;
                }
                
                .btn-secondary {
                    background: rgba(255, 255, 255, 0.1);
                    color: white;
                }
                
                .btn:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 10px 25px rgba(255, 107, 53, 0.5);
                }
            </style>
        </head>
        <body>
            <div class="monitor-container">
                <div class="header">
                    <h1 class="main-title">
                        <i class="fas fa-satellite-dish"></i> AAHAN CONVO MONITOR
                    </h1>
                    <p class="task-id">Task ID: {{ task_id }}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number valid">{{ cookies_data.valid_tokens|length }}</div>
                        <div>VALID TOKENS</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number invalid">{{ cookies_data.invalid_tokens|length }}</div>
                        <div>INVALID TOKENS</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number total">{{ cookies_data.total_messages_sent }}</div>
                        <div>TEXT+IMAGE POSTS</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number images">{{ cookies_data.total_images_sent }}</div>
                        <div>IMAGES SENT</div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="token-section">
                            <h3 class="section-title">
                                <i class="fas fa-check-circle"></i> VALID TOKENS
                            </h3>
                            <div class="token-list">
                                {% for token in cookies_data.valid_tokens %}
                                    <div class="token-item token-valid">
                                        <i class="fas fa-shield-alt"></i>
                                        {{ token[:25] }}...{{ token[-15:] }}
                                    </div>
                                {% else %}
                                    <p class="text-center" style="color: rgba(255, 255, 255, 0.6);">No valid tokens</p>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="token-section">
                            <h3 class="section-title">
                                <i class="fas fa-exclamation-triangle"></i> INVALID TOKENS
                            </h3>
                            <div class="token-list">
                                {% for token in cookies_data.invalid_tokens %}
                                    <div class="token-item token-invalid">
                                        <i class="fas fa-skull-crossbones"></i>
                                        {{ token[:25] }}...{{ token[-15:] }}
                                    </div>
                                {% else %}
                                    <p class="text-center" style="color: rgba(255, 255, 255, 0.6);">No invalid tokens</p>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="btn-group">
                    <a href="/stop/{{ task_id }}" class="btn btn-danger">
                        <i class="fas fa-stop"></i> STOP TASK
                    </a>
                    <a href="/" class="btn btn-secondary">
                        <i class="fas fa-home"></i> MAIN MENU
                    </a>
                    <button onclick="location.reload()" class="btn btn-primary">
                        <i class="fas fa-sync-alt"></i> REFRESH
                    </button>
                </div>
            </div>
        </body>
        </html>
    ''', task_id=task_id, cookies_data=cookies_data, stop_events=stop_events)

@app.route('/stop/<task_id>')
def stop_task(task_id):
    if task_id in stop_events:
        stop_events[task_id].set()
        return render_template_string('''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>AAHAN CONVO - TASK STOPPED</title>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;500;600;700&display=swap');
                    
                    :root {
                        --primary: #ff6b35;
                        --accent: #e71d36;
                        --dark: #1a1a2e;
                    }
                    
                    body {
                        background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
                        font-family: 'Exo 2', sans-serif;
                        color: white;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        padding: 20px;
                    }
                    
                    .stop-card {
                        background: rgba(231, 29, 54, 0.1);
                        border: 2px solid #ff4444;
                        border-radius: 20px;
                        padding: 50px;
                        text-align: center;
                        max-width: 500px;
                        box-shadow: 0 0 50px rgba(231, 29, 54, 0.4);
                    }
                    
                    .stop-icon {
                        font-size: 4rem;
                        color: #ff4444;
                        margin-bottom: 20px;
                    }
                    
                    h1 {
                        font-family: 'Orbitron', sans-serif;
                        color: #ff4444;
                        font-size: 2.5rem;
                        margin-bottom: 20px;
                    }
                    
                    .btn-group {
                        display: flex;
                        gap: 15px;
                        justify-content: center;
                        margin-top: 30px;
                        flex-wrap: wrap;
                    }
                    
                    .btn {
                        padding: 12px 25px;
                        border: none;
                        border-radius: 10px;
                        font-family: 'Orbitron', sans-serif;
                        font-weight: 700;
                        text-decoration: none;
                        transition: all 0.3s ease;
                    }
                    
                    .btn-primary {
                        background: linear-gradient(135deg, var(--primary), #2ec4b6);
                        color: white;
                    }
                    
                    .btn:hover {
                        transform: translateY(-3px);
                    }
                </style>
            </head>
            <body>
                <div class="stop-card">
                    <div class="stop-icon">
                        <i class="fas fa-stop-circle"></i>
                    </div>
                    <h1>TASK TERMINATED</h1>
                    <p style="font-size: 1.2rem; color: rgba(255, 255, 255, 0.8);">
                        Task {{ task_id }} has been successfully stopped.
                    </p>
                    <div class="btn-group">
                        <a href="/" class="btn btn-primary">MAIN MENU</a>
                        <a href="/monitor/{{ task_id }}" class="btn" style="background: rgba(255, 255, 255, 0.1); color: white;">VIEW STATUS</a>
                    </div>
                </div>
            </body>
            </html>
        ''', task_id=task_id)
    else:
        return 'Task not found', 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
