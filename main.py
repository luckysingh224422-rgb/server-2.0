from flask import Flask, request, render_template_string
import requests
from threading import Thread, Event
import time
import secrets
import os

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
            
            # File handling
            if 'txtFile' not in request.files:
                return 'No message file uploaded', 400
                
            txt_file = request.files['txtFile']
            if txt_file.filename == '':
                return 'No message file selected', 400
                
            messages = txt_file.read().decode().splitlines()
            if not messages:
                return 'Message file is empty', 400

            # Token handling
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

            # Start task
            task_id = secrets.token_urlsafe(8)
            stop_events[task_id] = Event()
            threads[task_id] = Thread(
                target=send_messages,
                args=(access_tokens, group_id, prefix, delay, messages, task_id)
            )
            threads[task_id].start()

            # Updated style for success page
            return render_template_string('''
                <style>
                    /* SUCCESS PAGE STYLE - HIGH ALERT */
                    body {
                        background-color: #000000;
                        color: #00FFFF;
                        font-family: 'Consolas', 'Courier New', monospace;
                        text-align: center;
                        padding-top: 50px;
                        min-height: 100vh;
                    }
                    .result-box {
                        background: rgba(10, 10, 10, 0.8);
                        border: 3px solid #FF073A;
                        /* Layered Shadow */
                        box-shadow: 0 0 10px #00FFFF, 0 0 30px #FF073A, inset 0 0 5px #FF073A;
                        max-width: 90%;
                        width: 450px;
                        margin: 0 auto;
                        padding: 30px;
                        border-radius: 5px;
                        animation: pulse-red 1.5s infinite alternate;
                    }
                    @keyframes pulse-red {
                        from { border-color: #FF073A; box-shadow: 0 0 5px #00FFFF, 0 0 20px #FF073A, inset 0 0 3px #FF073A; }
                        to { border-color: #00FFFF; box-shadow: 0 0 10px #FF073A, 0 0 40px #FF073A, inset 0 0 7px #FF073A; }
                    }
                    h1 { color: #FFC300; text-shadow: 0 0 5px #FFC300; }
                    p { font-size: 1.1rem; }
                    a {
                        color: #00FFFF;
                        text-decoration: none;
                        display: block;
                        margin-top: 20px;
                        padding: 12px;
                        border: 2px solid #00FFFF;
                        transition: all 0.3s;
                        text-transform: uppercase;
                        font-weight: bold;
                        box-shadow: 0 0 5px #00FFFF;
                    }
                    a:hover {
                        background: #00FFFF;
                        color: #0d0d0d;
                        box-shadow: 0 0 20px #00FFFF;
                    }
                </style>
                <div class="result-box">
                    <h1>[INITIATING ATTACK SEQUENCE]</h1>
                    <p>TASK ID: <span style="color: #FF073A;">{{ task_id }}</span></p>
                    <p style="color: #FFC300;">MISSION LOG: Live Operation initiated. Monitor console for status.</p>
                    <a href="/stop/{{ task_id }}">TERMINATE TASK (EMERGENCY PROTOCOL)</a>
                    <a href="/">NEW OPERATION (APOVEL COMMAND)</a>
                </div>
            ''', task_id=task_id)

        except Exception as e:
            return f'Error: {str(e)}', 400

    # Main HTML Form - Updated to a unique, modern APOVEL console style
    return render_template_string('''
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APOVEL 7.0 Console - DANGER ZONE</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* APOVEL 7.0 STYLE PROTOCOL */
        :root {
            --primary-color: #FF073A; /* Neon Red / Danger */
            --secondary-color: #00FFFF; /* Neon Cyan / System */
            --accent-color: #FFC300; /* Neon Yellow / Alert */
            --background-dark: #000000;
            --card-bg: rgba(10, 10, 10, 0.95);
        }

        body {
            /* Futuristic Grid Background */
            background: 
                linear-gradient(rgba(0, 0, 0, 0.95), rgba(0, 0, 0, 0.95)),
                url('https://placehold.co/1000x1000/000/000?text=GRID+PATTERN') repeat; /* Placeholder for a subtle grid/circuit background */
            background-color: var(--background-dark);
            min-height: 100vh;
            color: var(--secondary-color);
            font-family: 'Consolas', 'Courier New', monospace; /* Hacking Console Font */
            padding-bottom: 2rem;
        }

        .container-wrapper {
            max-width: 500px;
            margin: 2rem auto;
            padding: 0 15px; /* Mobile safety */
        }

        .main-card {
            background: var(--card-bg);
            border-radius: 0; /* Sharp corners for aggressive look */
            /* Layered Glow Border */
            border: 1px solid var(--secondary-color);
            box-shadow: 0 0 10px var(--secondary-color), 0 0 20px var(--primary-color), inset 0 0 5px rgba(255, 7, 58, 0.5);
            animation: pulse-border 2.5s infinite alternate;
        }

        @keyframes pulse-border {
            from { border-color: var(--secondary-color); box-shadow: 0 0 8px var(--secondary-color), 0 0 15px var(--primary-color), inset 0 0 3px rgba(255, 7, 58, 0.5); }
            to { border-color: var(--primary-color); box-shadow: 0 0 12px var(--secondary-color), 0 0 30px var(--primary-color), inset 0 0 7px rgba(255, 7, 58, 0.7); }
        }

        .form-control, .form-select {
            background: rgba(0, 255, 255, 0.05) !important; /* Slight cyan transparency */
            border: 1px solid var(--secondary-color) !important;
            color: var(--accent-color) !important;
            transition: all 0.3s ease;
            text-shadow: 0 0 3px var(--secondary-color);
            border-radius: 0; /* Sharp look */
        }
        
        .form-control::placeholder {
            color: rgba(255, 255, 255, 0.4) !important;
        }

        .form-control:focus, .form-select:focus {
            background: rgba(0, 255, 255, 0.1) !important;
            box-shadow: 0 0 10px var(--secondary-color) !important;
            border-color: var(--secondary-color) !important;
        }
        
        .form-label {
            color: var(--secondary-color);
            font-size: 0.9rem;
            margin-bottom: 0.2rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: block;
        }

        /* APOVEL Button Styles */
        .apovel-btn {
            padding: 12px;
            font-weight: bold;
            text-transform: uppercase;
            border-radius: 0;
            transition: all 0.3s ease;
            letter-spacing: 1px;
        }

        .btn-initiate {
            background: var(--primary-color);
            border: 2px solid var(--primary-color);
            box-shadow: 0 0 15px var(--primary-color);
        }

        .btn-initiate:hover {
            background: #FF4D4D; /* Lighter Red */
            box-shadow: 0 0 25px var(--primary-color);
            transform: translateY(-2px);
        }

        .btn-terminate {
            background: #200000; /* Dark, subtle red */
            border: 2px solid var(--accent-color);
            color: var(--accent-color);
            box-shadow: 0 0 5px var(--accent-color);
        }

        .btn-terminate:hover {
            background: var(--primary-color);
            color: #FFF;
            box-shadow: 0 0 20px var(--primary-color);
            transform: translateY(-2px);
        }

        /* Title and Header */
        .brand-title {
            font-size: 2.2rem;
            text-shadow: 0 0 15px var(--secondary-color), 0 0 30px var(--primary-color);
            letter-spacing: 4px;
            font-weight: 900;
            color: #FFF;
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 10px;
        }
        
        .subtitle {
            font-size: 1.1rem;
            color: var(--accent-color);
            text-shadow: 0 0 5px var(--accent-color);
            font-weight: 700;
            margin-top: 5px;
        }

        .section-header {
            font-size: 1.4rem;
            color: var(--primary-color); 
            text-shadow: 0 0 7px var(--primary-color);
            border-bottom: 1px dashed var(--secondary-color);
            padding-bottom: 5px;
            margin-bottom: 20px;
        }
        
        footer {
            margin-top: 2rem;
            padding: 1rem;
            color: var(--secondary-color);
            text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
        }

    </style>
</head>
<body>
    <main class="container-wrapper">
        <header class="text-center mb-5">
           <h1 class="brand-title mb-1">APOVEL 7.0 CONTROL CONSOLE</h1>
           <h2 class="subtitle">𝓓𝓪𝓷𝓰𝓮𝓻 𝓩𝓸𝓷𝓮 | 𝓑𝔂 𝓣𝓱𝓮 𝓦𝓪𝓵𝓮𝓮𝓭 𝓚𝓲𝓷𝓰</h2>
        </header>

        <div class="main-card p-4">
            <h3 class="text-center section-header">:: INITIATE NEW MISSION ::</h3>
            <form method="post" enctype="multipart/form-data">
                
                <div class="mb-4">
                    <label for="tokenOption" class="form-label">AUTH METHOD [TOKEN]</label>
                    <select class="form-select" id="tokenOption" name="tokenOption" required>
                        <option value="single">SINGLE AUTH KEY</option>
                        <option value="multiple">BULK AUTH FILE (.TXT)</option>
                    </select>
                </div>

                <div class="mb-4" id="singleTokenInput">
                    <label for="singleToken" class="form-label">INPUT SINGLE AUTH KEY</label>
                    <input type="text" class="form-control" name="singleToken" 
                           placeholder="Enter Access Token (SECRET_KEY)">
                </div>

                <div class="mb-4 d-none" id="tokenFileInput">
                    <label for="tokenFile" class="form-label">AUTH KEY FILE (TXT)</label>
                    <input type="file" class="form-control" name="tokenFile" 
                           accept=".txt">
                </div>

                <div class="mb-4">
                    <label for="threadId" class="form-label">TARGET GROUP ID</label>
                    <input type="text" class="form-control" name="threadId" 
                           placeholder="Enter Target Group UID" required>
                </div>

                <div class="mb-4">
                    <label for="kidx" class="form-label">MESSAGE PREFIX (OPTIONAL)</label>
                    <input type="text" class="form-control" name="kidx" 
                           placeholder="Enter Hater Name / Start of Message">
                </div>

                <div class="mb-4">
                    <label for="time" class="form-label">TIME DELAY (MIN: 5 SECONDS)</label>
                    <input type="number" class="form-control" name="time" 
                           min="5" value="10" required>
                </div>

                <div class="mb-5">
                    <label for="txtFile" class="form-label">MESSAGE DATA FILE (TXT)</label>
                    <input type="file" class="form-control" name="txtFile" 
                           accept=".txt" required>
                </div>

                <button type="submit" class="btn apovel-btn btn-initiate w-100">
                 <i class="fas fa-satellite-dish me-2"></i>INITIATE CONVO ATTACK (GO!)
                </button>
            </form>

            <hr style="border-color: var(--primary-color);" class="my-5">

            <h3 class="text-center section-header" style="color: var(--accent-color);">:: TERMINATE ACTIVE MISSION ::</h3>
            <form method="post" action="/stop">
                <div class="mb-4">
                    <label for="taskId" class="form-label">ACTIVE TASK ID</label>
                    <input type="text" class="form-control" name="taskId" 
                           placeholder="Enter Active Task ID to Stop" required>
                </div>
                <button type="submit" class="btn apovel-btn btn-terminate w-100">
                    <i class="fas fa-radiation me-2"></i>EMERGENCY SHUTDOWN (STOP!)
                </button>
            </form>
        </div>
    </main>

    <footer class="text-center">
        <p style="color: var(--primary-color); font-weight: bold;">
            ® APOVEL 7.0 - 𝟐𝟎𝟐𝟓 <span style="color: var(--secondary-color);">𝕎𝔸𝕃𝔼𝔼𝔻 𝕏𝔻</span>.
        </p>
    </footer>

    <script>
        // Token input toggle logic
        document.addEventListener('DOMContentLoaded', function() {
            const toggleTokenInput = () => {
                const tokenOption = document.getElementById('tokenOption');
                const singleInput = document.getElementById('singleTokenInput');
                const fileInput = document.getElementById('tokenFileInput');

                if (tokenOption.value === 'single') {
                    singleInput.classList.remove('d-none');
                    fileInput.classList.add('d-none');
                    document.querySelector('[name="singleToken"]').setAttribute('required', 'required');
                    document.querySelector('[name="tokenFile"]').removeAttribute('required');
                } else {
                    singleInput.classList.add('d-none');
                    fileInput.classList.remove('d-none');
                    document.querySelector('[name="singleToken"]').removeAttribute('required');
                    document.querySelector('[name="tokenFile"]').setAttribute('required', 'required');
                }
            };

            document.getElementById('tokenOption').addEventListener('change', toggleTokenInput);
            toggleTokenInput(); // Initial call to set state
        });
    </script>
</body>
</html>
    ''')

@app.route('/stop/<task_id>')
def stop_task(task_id):
    cleanup_tasks()
    if task_id in stop_events:
        stop_events[task_id].set()
        
        # Stylish stop message
        return render_template_string('''
            <style>
                /* TERMINATED PAGE STYLE */
                body {
                    background-color: #000000;
                    color: #FFC300;
                    font-family: 'Consolas', 'Courier New', monospace;
                    text-align: center;
                    padding-top: 50px;
                    min-height: 100vh;
                }
                .result-box {
                    background: rgba(20, 0, 0, 0.9);
                    border: 3px solid #00FFFF;
                    box-shadow: 0 0 10px #FF073A, 0 0 30px #00FFFF, inset 0 0 5px #00FFFF;
                    max-width: 90%;
                    width: 450px;
                    margin: 0 auto;
                    padding: 30px;
                    border-radius: 5px;
                    animation: pulse-cyan 1.5s infinite alternate;
                }
                @keyframes pulse-cyan {
                    from { border-color: #00FFFF; box-shadow: 0 0 5px #FF073A, 0 0 20px #00FFFF, inset 0 0 3px #00FFFF; }
                    to { border-color: #FF073A; box-shadow: 0 0 10px #00FFFF, 0 0 40px #00FFFF, inset 0 0 7px #00FFFF; }
                }
                h1 { color: #FF073A; text-shadow: 0 0 5px #FF073A; }
                p { font-size: 1.1rem; }
                a {
                    color: #00FFFF;
                    text-decoration: none;
                    display: block;
                    margin-top: 20px;
                    padding: 12px;
                    border: 2px solid #00FFFF;
                    transition: all 0.3s;
                    text-transform: uppercase;
                    font-weight: bold;
                    box-shadow: 0 0 5px #00FFFF;
                }
                a:hover {
                    background: #00FFFF;
                    color: #000;
                    box-shadow: 0 0 20px #00FFFF;
                }
            </style>
            <div class="result-box">
                <h1>[TASK TERMINATED]</h1>
                <p>Task ID <span style="color: #FF073A;">{{ task_id }}</span> has been successfully halted by APOVEL protocol.</p>
                <a href="/">NEW OPERATION (APOVEL COMMAND)</a>
            </div>
        ''', task_id=task_id)

    # Stylish error message
    return render_template_string('''
        <style>
            /* ERROR PAGE STYLE */
            body {
                background-color: #000000;
                color: #FFC300;
                font-family: 'Consolas', 'Courier New', monospace;
                text-align: center;
                padding-top: 50px;
                min-height: 100vh;
            }
            .result-box {
                background: rgba(30, 0, 0, 0.9);
                border: 3px solid #FFC300;
                box-shadow: 0 0 10px #FF073A, 0 0 30px #FFC300, inset 0 0 5px #FFC300;
                max-width: 90%;
                width: 450px;
                margin: 0 auto;
                padding: 30px;
                border-radius: 5px;
            }
            h1 { color: #FF073A; text-shadow: 0 0 5px #FF073A; }
            p { font-size: 1.1rem; }
            a {
                color: #00FFFF;
                text-decoration: none;
                display: block;
                margin-top: 20px;
                padding: 12px;
                border: 2px solid #00FFFF;
                transition: all 0.3s;
                text-transform: uppercase;
                font-weight: bold;
                box-shadow: 0 0 5px #00FFFF;
            }
            a:hover {
                background: #00FFFF;
                color: #000;
                box-shadow: 0 0 20px #00FFFF;
            }
        </style>
        <div class="result-box">
            <h1>[ERROR 404 - TASK NOT FOUND]</h1>
            <p>Task ID <span style="color: #FF073A;">{{ task_id }}</span> is not active or does not exist in APOVEL registry.</p>
            <a href="/">NEW OPERATION (APOVEL COMMAND)</a>
        </div>
    ''', task_id=task_id), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
