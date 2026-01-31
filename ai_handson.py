from flask import Flask, request, render_template_string, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
import os
from datetime import datetime

try:
    from trocr_ocr import recognize_handwriting
    OCR_AVAILABLE = True
except ImportError:
    try:
        from enhanced_ocr import recognize_handwriting
        OCR_AVAILABLE = True
    except ImportError:
        OCR_AVAILABLE = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hands-on-session'
socketio = SocketIO(app, cors_allowed_origins="*")
app.config['UPLOAD_FOLDER'] = os.path.abspath('uploads')
app.config['MAX_CONTENT_LENGTH'] = 54 * 1024 * 1024

live_users = 0
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>Hands-On Session Portal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 30px; margin-bottom: 30px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .header h1 { color: #333; margin-bottom: 10px; font-size: 2.5em; }
        .stats { display: flex; justify-content: center; gap: 20px; margin: 20px 0; }
        .stat-box { background: #4CAF50; color: white; padding: 15px 25px; border-radius: 10px; text-align: center; min-width: 120px; }
        .stat-number { font-size: 2em; font-weight: bold; }
        .stat-label { font-size: 0.9em; opacity: 0.9; }
        .main-content { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        .upload-section, .files-section { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .form-group { margin-bottom: 20px; }
        .form-input { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 1em; }
        .upload-area { border: 3px dashed #ddd; border-radius: 10px; padding: 30px; text-align: center; margin-top: 15px; cursor: pointer; }
        .file-input { display: none; }
        .upload-btn { background: #667eea; color: white; padding: 12px 25px; border: none; border-radius: 8px; font-size: 1em; cursor: pointer; width: 100%; margin-top: 15px; }
        .upload-btn:disabled { background: #ccc; cursor: not-allowed; }
        .progress-container { display: none; margin-top: 15px; }
        .progress-bar { width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); width: 0%; transition: width 0.3s; border-radius: 10px; }
        .spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid #f3f3f3; border-top: 2px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 8px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .download-btn { background: #28a745; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; font-size: 0.9em; margin-left: 5px; }
        .download-btn:disabled { background: #ccc; cursor: not-allowed; }
        .file-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; border: 1px solid #eee; border-radius: 8px; margin-bottom: 10px; }
        .file-info { flex: 1; }
        .file-name { font-weight: 500; color: #333; }
        .file-path { font-size: 0.85em; color: #666; margin-top: 2px; }
        .message { margin-top: 20px; padding: 15px; border-radius: 8px; background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .ocr-result { margin-top: 15px; padding: 15px; border-radius: 8px; background: #f8f9fa; border: 2px solid #007bff; display: none; position: relative; }
        .ocr-text { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-family: monospace; resize: vertical; min-height: 80px; }
        .close-btn { position: absolute; top: 10px; right: 15px; background: #dc3545; color: white; border: none; border-radius: 50%; width: 25px; height: 25px; cursor: pointer; font-size: 16px; line-height: 1; }
        .close-btn:hover { background: #c82333; }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Hands-On Session Portal</h1>
            <p>Upload your files organized by student folders</p>
            <div class="stats">
                <div class="stat-box pulse">
                    <div class="stat-number" id="userCount">0</div>
                    <div class="stat-label">Live Users</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{{ file_count }}</div>
                    <div class="stat-label">Files</div>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="upload-section">
                <h3>📤 Upload Files</h3>
                <form method="post" enctype="multipart/form-data" id="uploadForm">
                    <div class="form-group">
                        <label>🎓 Roll Number / Student ID:</label>
                        <input type="text" name="roll_no" class="form-input" placeholder="Enter your roll number" required>
                    </div>
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <h4>📁 Drop your files here or click to browse</h4>
                        <p>Maximum file size: 54MB</p>
                        <input type="file" name="file" id="fileInput" class="file-input" required>
                    </div>
                    <button type="submit" class="upload-btn" id="uploadBtn">🚀 Upload File</button>
                    
                    <div class="progress-container" id="progressContainer">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill"></div>
                        </div>
                        <p style="text-align: center; margin-top: 10px; color: #667eea;">
                            <span class="spinner"></span>
                            <span id="progressText">Uploading...</span>
                        </p>
                    </div>
                </form>
                {% if message %}
                    <div class="message">{{ message|safe }}</div>
                {% endif %}
            </div>
            
            <div class="files-section">
                <h3>📋 Student Files</h3>
                
                <div class="ocr-result" id="ocrResult">
                    <button class="close-btn" onclick="closeOcrResult()" title="Close">&times;</button>
                    <h4>📝 OCR Results - Select All (Ctrl+A) and Copy (Ctrl+C):</h4>
                    <textarea class="ocr-text" id="ocrText" readonly></textarea>
                </div>
                
                <div class="file-list">
                    {% for file in files %}
                    {% if '.' in file.split('/')[-1] %}
                    <div class="file-item">
                        <div class="file-info">
                            <div class="file-name">{{ file.split('/')[-1] }}</div>
                            <div class="file-path">📁 {{ file }}</div>
                        </div>
                        <button class="download-btn" onclick="downloadFile('{{ file }}')">⬇️ Download</button>
                        {% if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')) %}
                        <button class="download-btn" onclick="analyzeHandwriting('{{ file }}')" style="background: #17a2b8;">🔍 OCR</button>
                        {% endif %}
                    </div>
                    {% endif %}
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        socket.on('user_count', function(data) {
            document.getElementById('userCount').textContent = data.count;
        });
        socket.on('connect', function() {
            socket.emit('user_connected');
        });
        
        function downloadFile(filename) {
            window.location.href = '/download/' + encodeURIComponent(filename);
        }
        
        function closeOcrResult() {
            document.getElementById('ocrResult').style.display = 'none';
        }
        
        document.getElementById('uploadForm').addEventListener('submit', function() {
            const btn = document.getElementById('uploadBtn');
            const progressContainer = document.getElementById('progressContainer');
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            
            document.body.style.pointerEvents = 'none';
            btn.style.pointerEvents = 'auto';
            
            btn.innerHTML = '🔄 Uploading...';
            btn.disabled = true;
            progressContainer.style.display = 'block';
            
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress > 90) progress = 90;
                
                progressFill.style.width = progress + '%';
                progressText.textContent = 'Uploading... ' + Math.round(progress) + '%';
                
                if (progress >= 90) {
                    clearInterval(interval);
                    progressText.textContent = 'Processing...';
                }
            }, 200);
        });
        
        function analyzeHandwriting(filename) {
            const btn = event.target;
            const originalText = btn.innerHTML;
            
            const allOcrBtns = document.querySelectorAll('button[onclick*="analyzeHandwriting"]');
            allOcrBtns.forEach(b => b.disabled = true);
            
            let progress = 0;
            const updateProgress = () => {
                progress += Math.random() * 20;
                if (progress > 95) progress = 95;
                btn.innerHTML = '🔄 Analyzing... ' + Math.round(progress) + '%';
            };
            
            const interval = setInterval(updateProgress, 300);
            
            fetch('/ocr/' + encodeURIComponent(filename))
                .then(response => response.json())
                .then(data => {
                    clearInterval(interval);
                    btn.innerHTML = originalText;
                    allOcrBtns.forEach(b => b.disabled = false);
                    
                    if (data && data.error) {
                        alert('❌ OCR Error: ' + data.error);
                        return;
                    }
                    
                    let message = '📝 Handwriting Analysis Results:\\n\\n';
                    if (data && data.texts && Array.isArray(data.texts) && data.texts.length > 0) {
                        data.texts.forEach((item, i) => {
                            if (item && item.text) {
                                message += (i + 1) + '. "' + item.text + '" (confidence: ' + (item.confidence || 'N/A') + ')\\n';
                            }
                        });
                        
                        const clipboardText = data.texts.filter(item => item && item.text).map(item => item.text).join('\\n');
                        if (clipboardText) {
                            document.getElementById('ocrResult').style.display = 'block';
                            document.getElementById('ocrText').value = clipboardText;
                            document.getElementById('ocrText').select();
                            message += '\\n📋 Results displayed below - Select text and copy!';
                        }
                        alert(message);
                    } else {
                        message += 'No text detected. Try:\\n• Better lighting\\n• Darker pen/pencil\\n• Clearer writing';
                        alert(message);
                    }
                })
                .catch(error => {
                    clearInterval(interval);
                    btn.innerHTML = originalText;
                    allOcrBtns.forEach(b => b.disabled = false);
                    alert('❌ Error: ' + (error.message || 'Unknown error'));
                });
        }
    </script>
</body>
</html>'''

def get_all_files():
    all_files = []
    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), app.config['UPLOAD_FOLDER'])
            all_files.append(rel_path.replace('\\', '/'))
    return all_files

def handle_duplicate_file(filepath, filename):
    if os.path.exists(filepath):
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%H%M%S')
        new_filename = f"{name}_v{timestamp}{ext}"
        return os.path.join(os.path.dirname(filepath), new_filename), new_filename
    return filepath, filename

@app.route('/ocr/<path:filename>')
def ocr_file(filename):
    if not OCR_AVAILABLE:
        return jsonify({"error": "OCR not available. Install: pip install opencv-python easyocr"})
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"})
    
    try:
        result = recognize_handwriting(file_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@socketio.on('user_connected')
def handle_user_connected():
    global live_users
    live_users += 1
    emit('user_count', {'count': live_users}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global live_users
    live_users = max(0, live_users - 1)
    emit('user_count', {'count': live_users}, broadcast=True)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    files = get_all_files()
    file_count = len(files)
    
    if request.method == 'POST':
        roll_no = request.form.get('roll_no', '').strip()
        file = request.files.get('file')
        
        if not roll_no:
            return render_template_string(HTML_TEMPLATE, message='❌ Please enter your roll number!', files=files, file_count=file_count)
        
        if not any(char.isdigit() for char in roll_no):
            return render_template_string(HTML_TEMPLATE, message='❌ Roll number must contain numbers!', files=files, file_count=file_count)
        
        if not file or not file.filename:
            return render_template_string(HTML_TEMPLATE, message='❌ Please select a file!', files=files, file_count=file_count)
        
        student_folder = os.path.join(app.config['UPLOAD_FOLDER'], roll_no)
        os.makedirs(student_folder, exist_ok=True)
        
        filename = file.filename
        filepath = os.path.join(student_folder, filename)
        final_filepath, final_filename = handle_duplicate_file(filepath, filename)
        file.save(final_filepath)
        
        files = get_all_files()
        file_count = len(files)
        
        return render_template_string(HTML_TEMPLATE, 
                                    message=f'✅ File <strong>{filename}</strong> uploaded successfully!<br>👤 Student: <strong>{roll_no}</strong>',
                                    files=files, file_count=file_count)
    
    return render_template_string(HTML_TEMPLATE, files=files, file_count=file_count)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)