from flask import Flask, request, render_template, send_from_directory, jsonify
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

@app.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"success": True, "message": "File deleted successfully"})
        else:
            return jsonify({"success": False, "error": "File not found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

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
            return render_template('index.html', message='❌ Please enter your roll number!', files=files, file_count=file_count)
        
        if not any(char.isdigit() for char in roll_no):
            return render_template('index.html', message='❌ Roll number must contain numbers!', files=files, file_count=file_count)
        
        if not file or not file.filename:
            return render_template('index.html', message='❌ Please select a file!', files=files, file_count=file_count)
        
        student_folder = os.path.join(app.config['UPLOAD_FOLDER'], roll_no)
        os.makedirs(student_folder, exist_ok=True)
        
        filename = file.filename
        filepath = os.path.join(student_folder, filename)
        final_filepath, final_filename = handle_duplicate_file(filepath, filename)
        file.save(final_filepath)
        
        files = get_all_files()
        file_count = len(files)
        
        return render_template('index.html', 
                             message=f'✅ File <strong>{filename}</strong> uploaded successfully!<br>👤 Student: <strong>{roll_no}</strong>',
                             files=files, file_count=file_count)
    
    return render_template('index.html', files=files, file_count=file_count)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)