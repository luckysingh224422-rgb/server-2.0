from flask import Flask, request, render_template_string
import requests
from threading import Thread, Event
import time
import secrets
import os
import random

app = Flask(__name__)

# Global variables to manage tasks
stop_events = {}
threads = {}

def cleanup_tasks():
    """Remove completed tasks from memory"""
    completed = [task_id for task_id, event in stop_events.items() if event.is_set()]
    for task_id in completed:
        if task_id in stop_events:
            del stop_events[task_id]
        if task_id in threads:
            del threads[task_id]

def send_messages(access_tokens, group_id, prefix, delay, messages, task_id):
    stop_event = stop_events[task_id]
    message_index = 0
    
    print(f"🚀 Starting message sending...")
    print(f"📝 Total messages: {len(messages)}")
    print(f"🔑 Total tokens: {len(access_tokens)}")
    print(f"🎯 Target group: {group_id}")
    
    while not stop_event.is_set():
        try:
            # Get current message
            message = messages[message_index % len(messages)]
            full_message = f"{prefix} {message}".strip() if prefix else message
            
            print(f"📨 Sending message: {full_message[:50]}...")
            
            # Shuffle tokens for random order
            shuffled_tokens = [t.strip() for t in access_tokens if t.strip()]
            random.shuffle(shuffled_tokens)
            
            for token in shuffled_tokens:
                if stop_event.is_set():
                    break
                
                short_token = token[:15] + "..." if len(token) > 15 else token
                
                try:
                    # Facebook Graph API endpoint
                    url = f'https://graph.facebook.com/v19.0/{group_id}/feed'
                    
                    payload = {
                        'message': full_message,
                        'access_token': token
                    }
                    
                    # Send request
                    response = requests.post(
                        url,
                        data=payload,
                        timeout=30
                    )
                    
                    # Check response
                    if response.status_code == 200:
                        result = response.json()
                        post_id = result.get('id', 'Unknown')
                        print(f"✅ SUCCESS! Post ID: {post_id} | Token: {short_token}")
                    else:
                        error_data = response.json().get('error', {})
                        error_msg = error_data.get('message', 'Unknown error')
                        error_type = error_data.get('type', 'Unknown')
                        print(f"❌ FAILED! Error: {error_type} - {error_msg} | Token: {short_token}")
                        
                except requests.exceptions.Timeout:
                    print(f"⏰ Timeout for token: {short_token}")
                except requests.exceptions.ConnectionError:
                    print(f"🔌 Connection error for token: {short_token}")
                except Exception as e:
                    print(f"⚠️ Request error: {str(e)} | Token: {short_token}")
                
                # Delay between tokens
                if not stop_event.is_set() and len(shuffled_tokens) > 1:
                    time.sleep(max(delay, 5))
            
            # Move to next message
            message_index += 1
            
            # Additional delay between message cycles
            if not stop_event.is_set():
                print(f"💤 Waiting {delay} seconds before next cycle...")
                time.sleep(delay)
                    
        except Exception as e:
            print(f"🔴 Critical error: {str(e)}")
            time.sleep(10)
    
    print(f"🛑 Task {task_id} stopped")

def extract_tokens_from_text(text):
    """Extract tokens from text content"""
    tokens = []
    try:
        # Look for Facebook token patterns
        import re
        patterns = [
            r'EAAB\w+',
            r'EAA\w+', 
            r'[A-Za-z0-9]{50,}'
        ]
        
        for pattern in patterns:
            found_tokens = re.findall(pattern, text)
            tokens.extend(found_tokens)
        
        # Remove duplicates
        tokens = list(set(tokens))
        print(f"🔍 Found {len(tokens)} tokens")
        
    except Exception as e:
        print(f"Error extracting tokens: {e}")
    
    return tokens

@app.route('/', methods=['GET', 'POST'])
def main_handler():
    cleanup_tasks()
    
    if request.method == 'POST':
        try:
            # Get form data
            group_id = request.form['threadId'].strip()
            prefix = request.form.get('kidx', '').strip()
            delay = max(int(request.form.get('time', 10)), 5)
            
            # Validate group ID
            if not group_id:
                return '❌ Group ID is required', 400
            
            # Handle message file
            if 'txtFile' not in request.files:
                return '❌ No message file uploaded', 400
                
            txt_file = request.files['txtFile']
            if txt_file.filename == '':
                return '❌ No message file selected', 400
            
            # Read messages
            messages_content = txt_file.read().decode('utf-8', errors='ignore')
            messages = [line.strip() for line in messages_content.splitlines() if line.strip()]
            
            if not messages:
                return '❌ Message file is empty', 400
            
            # Handle tokens
            access_tokens = []
            token_option = request.form.get('tokenOption', 'single')
            
            if token_option == 'single':
                single_token = request.form.get('singleToken', '').strip()
                if single_token:
                    access_tokens = [single_token]
            else:
                if 'tokenFile' not in request.files:
                    return '❌ No token file uploaded', 400
                token_file = request.files['tokenFile']
                if token_file.filename == '':
                    return '❌ No token file selected', 400
                
                token_content = token_file.read().decode('utf-8', errors='ignore')
                access_tokens = [line.strip() for line in token_content.splitlines() if line.strip()]
            
            # Clean tokens
            access_tokens = [t for t in access_tokens if t]
            if not access_tokens:
                return '❌ No valid tokens provided', 400
            
            print(f"🎯 Starting with {len(access_tokens)} tokens and {len(messages)} messages")
            
            # Create and start task
            task_id = secrets.token_urlsafe(6)
            stop_events[task_id] = Event()
            
            thread = Thread(
                target=send_messages,
                args=(access_tokens, group_id, prefix, delay, messages, task_id)
            )
            thread.daemon = True
            thread.start()
            
            threads[task_id] = thread
            
            # Success page
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Success - Message Sender</title>
                <meta http-equiv="refresh" content="2;url=/status/{task_id}" />
                <style>
                    body {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        color: white;
                    }}
                    .container {{
                        background: rgba(255,255,255,0.1);
                        padding: 40px;
                        border-radius: 10px;
                        text-align: center;
                        backdrop-filter: blur(10px);
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>✅ Message Sending Started!</h2>
                    <p>Task ID: <strong>{task_id}</strong></p>
                    <p>Redirecting to status page...</p>
                </div>
            </body>
            </html>
            '''
            
        except Exception as e:
            return f'❌ Error: {str(e)}', 400

    # Main form
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Facebook Message Sender</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        input, select, textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        input:focus, select:focus {
            border-color: #667eea;
            outline: none;
        }
        .btn {
            background: #667eea;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            font-size: 18px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
        }
        .btn:hover {
            background: #764ba2;
        }
        .btn-stop {
            background: #ff4444;
        }
        .btn-stop:hover {
            background: #cc0000;
        }
        .section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .token-option {
            display: none;
        }
        .active {
            display: block;
        }
        .tab {
            padding: 10px 20px;
            background: #ddd;
            border: none;
            cursor: pointer;
            margin-right: 5px;
        }
        .tab.active {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📨 Facebook Message Sender</h1>
        
        <form method="post" enctype="multipart/form-data">
            <div class="section">
                <h3>🔑 Authentication</h3>
                
                <div class="form-group">
                    <label>Token Type:</label>
                    <div>
                        <button type="button" class="tab active" onclick="showTokenOption('single')">Single Token</button>
                        <button type="button" class="tab" onclick="showTokenOption('multiple')">Token File</button>
                    </div>
                </div>
                
                <div id="singleToken" class="token-option active">
                    <div class="form-group">
                        <label>Access Token:</label>
                        <input type="text" name="singleToken" placeholder="Enter Facebook access token">
                    </div>
                </div>
                
                <div id="multipleToken" class="token-option">
                    <div class="form-group">
                        <label>Token File (txt):</label>
                        <input type="file" name="tokenFile" accept=".txt">
                    </div>
                </div>
                <input type="hidden" name="tokenOption" id="tokenOption" value="single">
            </div>
            
            <div class="section">
                <h3>🎯 Target</h3>
                <div class="form-group">
                    <label>Group ID:</label>
                    <input type="text" name="threadId" placeholder="Enter Facebook Group ID" required>
                </div>
                
                <div class="form-group">
                    <label>Message Prefix (optional):</label>
                    <input type="text" name="kidx" placeholder="Prefix for all messages">
                </div>
                
                <div class="form-group">
                    <label>Delay (seconds):</label>
                    <input type="number" name="time" value="10" min="5" required>
                </div>
            </div>
            
            <div class="section">
                <h3>📝 Messages</h3>
                <div class="form-group">
                    <label>Messages File (txt):</label>
                    <input type="file" name="txtFile" accept=".txt" required>
                    <small>One message per line</small>
                </div>
            </div>
            
            <button type="submit" class="btn">🚀 Start Sending Messages</button>
        </form>
        
        <div class="section">
            <h3>🛑 Stop Task</h3>
            <form method="post" action="/stop">
                <div class="form-group">
                    <label>Task ID:</label>
                    <input type="text" name="taskId" placeholder="Enter Task ID to stop">
                </div>
                <button type="submit" class="btn btn-stop">🛑 Stop Task</button>
            </form>
        </div>
    </div>

    <script>
        function showTokenOption(option) {
            // Update tabs
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
            
            // Show/hide sections
            document.getElementById('singleToken').classList.toggle('active', option === 'single');
            document.getElementById('multipleToken').classList.toggle('active', option === 'multiple');
            document.getElementById('tokenOption').value = option;
        }
    </script>
</body>
</html>
    '''

@app.route('/status/<task_id>')
def status_page(task_id):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Status - {task_id}</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: Arial, sans-serif;
                padding: 20px;
                color: white;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 10px;
                backdrop-filter: blur(10px);
            }}
            .btn {{
                display: inline-block;
                background: #ff4444;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                margin: 10px 5px;
            }}
            .btn:hover {{
                background: #cc0000;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Task Status</h1>
            <p><strong>Task ID:</strong> {task_id}</p>
            <p><strong>Status:</strong> {"🟢 Running" if task_id in stop_events and not stop_events[task_id].is_set() else "🔴 Stopped"}</p>
            <p>🔍 Check console for detailed sending status...</p>
            <br>
            <a href="/stop/{task_id}" class="btn">🛑 Stop This Task</a>
            <a href="/" class="btn" style="background: #667eea;">🏠 Back to Home</a>
        </div>
    </body>
    </html>
    '''

@app.route('/stop/<task_id>')
def stop_task(task_id):
    cleanup_tasks()
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Stopped - {task_id}</title>
            <style>
                body {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    color: white;
                }}
                .container {{
                    background: rgba(255,255,255,0.1);
                    padding: 40px;
                    border-radius: 10px;
                    text-align: center;
                    backdrop-filter: blur(10px);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🛑 Task Stopped</h2>
                <p>Task <strong>{task_id}</strong> has been stopped.</p>
                <a href="/" style="color: white; text-decoration: underline;">← Back to Home</a>
            </div>
        </body>
        </html>
        '''
    else:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    color: white;
                }
                .container {
                    background: rgba(255,255,255,0.1);
                    padding: 40px;
                    border-radius: 10px;
                    text-align: center;
                    backdrop-filter: blur(10px);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>❌ Task Not Found</h2>
                <p>The specified task was not found or already stopped.</p>
                <a href="/" style="color: white; text-decoration: underline;">← Back to Home</a>
            </div>
        </body>
        </html>
        ''', 404

@app.route('/stop', methods=['POST'])
def stop_task_form():
    task_id = request.form.get('taskId', '').strip()
    if task_id and task_id in stop_events:
        stop_events[task_id].set()
        return f"✅ Task {task_id} stopped successfully!"
    return "❌ Task not found or already stopped!", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("🚀 Facebook Message Sender Started!")
    print(f"📧 Access at: http://localhost:{port}")
    print("🔧 Ready to send messages...")
    app.run(host='0.0.0.0', port=port, debug=False)
