# Python 3.14.2 compatibility check
import sys
if sys.version_info >= (3, 14):
    # Ensure compatibility with newer Python versions
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)

from flask import Flask, request, render_template_string, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
import os
import time
from datetime import datetime

# OCR imports with error handling
try:
    from simple_handwriting_ocr import recognize_handwriting
    OCR_AVAILABLE = True
except ImportError as e:
    print(f"Advanced OCR not available: {e}")
    try:
        from fallback_ocr import recognize_handwriting
        OCR_AVAILABLE = True
        print("Using fallback OCR (basic image analysis only)")
    except ImportError:
        print("No OCR capabilities available")
        OCR_AVAILABLE = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hands-on-session'
socketio = SocketIO(app, cors_allowed_origins="*")
app.config['UPLOAD_FOLDER'] = os.path.abspath('uploads')
app.config['MAX_CONTENT_LENGTH'] = 54 * 1024 * 1024  # 54MB max file size

# Track live users
live_users = 0

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
print(f"Files will be stored in: {app.config['UPLOAD_FOLDER']}")

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Hands-On Session Portal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 30px; margin-bottom: 30px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .header h1 { color: #333; margin-bottom: 10px; font-size: 2.5em; }
        .header p { color: #666; font-size: 1.1em; }
        .stats { display: flex; justify-content: center; gap: 20px; margin: 20px 0; }
        .stat-box { background: #4CAF50; color: white; padding: 15px 25px; border-radius: 10px; text-align: center; min-width: 120px; }
        .stat-number { font-size: 2em; font-weight: bold; }
        .stat-label { font-size: 0.9em; opacity: 0.9; }
        .main-content { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        .upload-section, .files-section { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 500; color: #333; }
        .form-input { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 1em; }
        .form-input:focus { outline: none; border-color: #667eea; }
        .upload-area { border: 3px dashed #ddd; border-radius: 10px; padding: 30px; text-align: center; transition: all 0.3s; margin-top: 15px; }
        .upload-area:hover { border-color: #667eea; background: #f8f9ff; }
        .file-input { display: none; }
        .upload-btn { background: #667eea; color: white; padding: 12px 25px; border: none; border-radius: 8px; font-size: 1em; cursor: pointer; transition: all 0.3s; }
        .upload-btn:hover { background: #5a6fd8; transform: translateY(-2px); }
        .upload-btn:disabled { background: #ccc; cursor: not-allowed; transform: none; }
        .progress-container { display: none; margin-top: 15px; }
        .progress-bar { width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); width: 0%; transition: width 0.3s; border-radius: 10px; }
        .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .search-box { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 1em; margin-bottom: 20px; }
        .search-box:focus { outline: none; border-color: #667eea; }
        .file-list { max-height: 400px; overflow-y: auto; }
        .file-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; border: 1px solid #eee; border-radius: 8px; margin-bottom: 10px; transition: all 0.3s; }
        .file-item:hover { background: #f8f9ff; border-color: #667eea; }
        .file-info { flex: 1; }
        .file-name { font-weight: 500; color: #333; }
        .file-path { font-size: 0.85em; color: #666; margin-top: 2px; }
        .download-btn { background: #28a745; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; font-size: 0.9em; }
        .download-btn:hover { background: #218838; }
        .message { margin-top: 20px; padding: 15px; border-radius: 8px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
        @media (max-width: 768px) { .main-content { grid-template-columns: 1fr; } }
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
                    <div class="stat-number" id="fileCount">{{ file_count }}</div>
                    <div class="stat-label">Files</div>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="upload-section">
                <h3>📤 Upload Files</h3>
                <form method="post" enctype="multipart/form-data" id="uploadForm">
                    <div class="form-group">
                        <label for="rollNo">🎓 Roll Number / Student ID:</label>
                        <input type="text" name="roll_no" id="rollNo" class="form-input" placeholder="Enter your roll number (e.g., CS2021001)" required>
                    </div>
                    
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <h4>📁 Drop your files here or click to browse</h4>
                        <p>Maximum file size: 54MB</p>
                        <input type="file" name="file" id="fileInput" class="file-input" required>
                    </div>
                    
                    <button type="submit" class="upload-btn" id="uploadButton" style="margin-top: 15px; width: 100%;">🚀 Upload File</button>
                    
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
                    <div class="message success">{{ message|safe }}</div>
                {% endif %}
            </div>
            
            <div class="files-section">
                <h3>📋 Student Folders & Files</h3>
                <input type="text" class="search-box" id="searchBox" placeholder="🔍 Search by roll number or filename..." onkeyup="searchFiles()">
                
                <div style="margin-bottom: 20px;">
                    <h4>👥 Student Folders ({{ folders|length }})</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0;">
                        {% for folder in folders %}
                        <div class="folder-tag" onclick="filterByStudent('{{ folder.name }}')" style="background: #e3f2fd; padding: 8px 12px; border-radius: 20px; cursor: pointer; font-size: 0.9em; border: 1px solid #90caf9;">
                            📁 {{ folder.name }} ({{ folder.file_count }})
                        </div>
                        {% endfor %}
                    </div>
                </div>
                
                <div class="file-list" id="fileList">
                    {% for file in files %}
                    {% if '.' in file.split('/')[-1] %}
                    <div class="file-item" data-filename="{{ file }}" data-student="{{ file.split('/')[0] }}">
                        <div class="file-info">
                            <div class="file-name">{{ file.split('/')[-1] }}</div>
                            <div class="file-path">📁 {{ file }}</div>
                        </div>
                        <button class="download-btn" onclick="downloadFile('{{ file }}')">⬇️ Download</button>
                        {% if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')) %}
                        <button class="download-btn" onclick="analyzeHandwriting('{{ file }}')" style="background: #17a2b8; margin-left: 5px;">🔍 OCR</button>
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
        
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            const rollNo = document.getElementById('rollNo').value.trim();
            const fileInput = document.getElementById('fileInput');
            
            if (!rollNo) {
                alert('Please enter your roll number!');
                e.preventDefault();
                return false;
            }
            
            if (!/\\d/.test(rollNo)) {
                alert('Roll number must contain valid numbers!');
                e.preventDefault();
                return false;
            }
            
            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Please select a file to upload!');
                e.preventDefault();
                return false;
            }
            
            showUploadProgress();
            return true;
        });
        
        function showUploadProgress() {
            const uploadBtn = document.getElementById('uploadButton');
            const progressContainer = document.getElementById('progressContainer');
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '🔄 Uploading...';
            progressContainer.style.display = 'block';
            
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress > 90) progress = 90;
                
                progressFill.style.width = progress + '%';
                progressText.textContent = `Uploading... ${Math.round(progress)}%`;
                
                if (progress >= 90) {
                    clearInterval(interval);
                    progressText.textContent = 'Processing...';
                }
            }, 200);
        }
        
        function searchFiles() {
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const fileItems = document.querySelectorAll('.file-item');
            
            fileItems.forEach(item => {
                const filename = item.getAttribute('data-filename').toLowerCase();
                if (filename.includes(searchTerm)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        }
        
        function filterByStudent(studentId) {
            const fileItems = document.querySelectorAll('.file-item');
            document.getElementById('searchBox').value = studentId;
            
            fileItems.forEach(item => {
                const student = item.getAttribute('data-student');
                if (student === studentId) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        }
        
        function downloadFile(filename) {
            window.location.href = '/download/' + encodeURIComponent(filename);
        }
        
        function analyzeHandwriting(filename) {
            const btn = event.target;
            const originalText = btn.innerHTML;
            
            showAnalyzingProgress(btn);
            
            fetch('/ocr/' + encodeURIComponent(filename))
                .then(response => response.json())
                .then(data => {
                    hideAnalyzingProgress(btn, originalText);
                    
                    if (data.error) {
                        alert('❌ OCR Error: ' + data.error);
                        return;
                    }
                    
                    let message = '📝 Handwriting Analysis Results:\\n\\n';
                    let clipboardText = 'OCR Results:\\n';
                    
                    if (data.texts && data.texts.length > 0) {
                        data.texts.forEach((item, i) => {
                            message += `${i + 1}. "${item.text}" (confidence: ${item.confidence})\\n`;
                            clipboardText += `${item.text}\\n`;
                        });
                        
                        navigator.clipboard.writeText(clipboardText.replace(/\\n/g, '\\n')).then(() => {
                            message += '\\n✅ Results copied to clipboard!';
                            alert(message);
                        }).catch(() => {
                            message += '\\n⚠️ Could not copy to clipboard';
                            alert(message);
                        });
                    } else {
                        message += 'No text detected. Try:\\n• Better lighting\\n• Darker pen/pencil\\n• Clearer writing';
                        alert(message);
                    }
                })
                .catch(error => {
                    hideAnalyzingProgress(btn, originalText);
                    alert('❌ Error: ' + error.message);
                });
        }
        
        function showAnalyzingProgress(btn) {
            btn.disabled = true;
            btn.innerHTML = '🔄 Analyzing...';
            
            const overlay = document.createElement('div');
            overlay.id = 'analyzingOverlay';
            overlay.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.8); z-index: 1000; display: flex;
                align-items: center; justify-content: center;
            `;
            
            overlay.innerHTML = `
                <div style="background: white; padding: 30px; border-radius: 15px; text-align: center; min-width: 300px;">
                    <h3 style="margin-bottom: 20px; color: #333;">🔍 Analyzing Handwriting</h3>
                    <div style="width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; margin-bottom: 15px;">
                        <div id="analyzingProgressFill" style="height: 100%; background: linear-gradient(90deg, #17a2b8, #138496); width: 0%; transition: width 0.3s; border-radius: 10px;"></div>
                    </div>
                    <p style="color: #17a2b8; margin: 0;">
                        <span class="spinner" style="display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #17a2b8; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 10px;"></span>
                        <span id="analyzingProgressText">Preprocessing image...</span>
                    </p>
                </div>
            `;
            
            document.body.appendChild(overlay);
            
            let progress = 0;
            const steps = ['Preprocessing image...', 'Detecting text regions...', 'Recognizing characters...', 'Processing results...'];
            let stepIndex = 0;
            
            const interval = setInterval(() => {
                progress += Math.random() * 12 + 3;
                if (progress > 95) progress = 95;
                
                const progressFill = document.getElementById('analyzingProgressFill');
                const progressText = document.getElementById('analyzingProgressText');
                
                if (progressFill) {
                    progressFill.style.width = progress + '%';
                }
                
                if (progressText && progress > (stepIndex + 1) * 20) {
                    stepIndex = Math.min(stepIndex + 1, steps.length - 1);
                    progressText.textContent = steps[stepIndex];
                }
            }, 300);
            
            btn.analyzingInterval = interval;
        }
        
        function hideAnalyzingProgress(btn, originalText) {
            btn.innerHTML = originalText;
            btn.disabled = false;
            
            if (btn.analyzingInterval) {
                clearInterval(btn.analyzingInterval);
                delete btn.analyzingInterval;
            }
            
            const progressFill = document.getElementById('analyzingProgressFill');
            const progressText = document.getElementById('analyzingProgressText');
            
            if (progressFill && progressText) {
                progressFill.style.width = '100%';
                progressText.textContent = 'Analysis complete!';
                
                setTimeout(() => {
                    const overlay = document.getElementById('analyzingOverlay');
                    if (overlay) overlay.remove();
                }, 500);
            } else {
                const overlay = document.getElementById('analyzingOverlay');
                if (overlay) overlay.remove();
            }
        }
    </script>
</body>
</html>
'''

def get_all_files():
    all_files = []
    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), app.config['UPLOAD_FOLDER'])
            all_files.append(rel_path.replace('\\', '/'))
    return all_files

def get_student_folders():
    folders = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for item in os.listdir(app.config['UPLOAD_FOLDER']):
            item_path = os.path.join(app.config['UPLOAD_FOLDER'], item)
            if os.path.isdir(item_path):
                file_count = len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))])
                folders.append({'name': item, 'file_count': file_count})
    return folders

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
        return jsonify({"error": "OCR not available. Install dependencies: pip install opencv-python easyocr"})
    
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
    folders = get_student_folders()
    file_count = len(files)
    
    if request.method == 'POST':
        roll_no = request.form.get('roll_no', '').strip()
        file = request.files.get('file')
        
        if not roll_no:
            return render_template_string(HTML_TEMPLATE, 
                                        message='❌ Please enter your roll number!',
                                        files=files, folders=folders, file_count=file_count)
        
        if not any(char.isdigit() for char in roll_no):
            return render_template_string(HTML_TEMPLATE, 
                                        message='❌ Roll number must contain valid numbers!',
                                        files=files, folders=folders, file_count=file_count)
        
        if not file or not file.filename:
            return render_template_string(HTML_TEMPLATE, 
                                        message='❌ Please select a file to upload!',
                                        files=files, folders=folders, file_count=file_count)
        
        student_folder = os.path.join(app.config['UPLOAD_FOLDER'], roll_no)
        os.makedirs(student_folder, exist_ok=True)
        
        filename = file.filename
        filepath = os.path.join(student_folder, filename)
        
        final_filepath, final_filename = handle_duplicate_file(filepath, filename)
        file.save(final_filepath)
        
        files = get_all_files()
        folders = get_student_folders()
        file_count = len(files)
        
        version_msg = f' (renamed to <strong>{final_filename}</strong>)' if final_filename != filename else ''
        
        return render_template_string(HTML_TEMPLATE, 
                                    message=f'✅ File <strong>{filename}</strong> uploaded successfully!{version_msg}<br>👤 Student: <strong>{roll_no}</strong><br>📍 Saved to: {final_filepath}',
                                    files=files, folders=folders, file_count=file_count)
    
    return render_template_string(HTML_TEMPLATE, files=files, folders=folders, file_count=file_count)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)