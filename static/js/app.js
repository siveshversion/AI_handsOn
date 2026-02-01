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

function deleteFile(filename) {
    if (confirm('Are you sure you want to delete "' + filename.split('/').pop() + '"?')) {
        const btn = event.target;
        const originalText = btn.innerHTML;
        
        btn.innerHTML = '🔄 Deleting...';
        btn.disabled = true;
        
        fetch('/delete/' + encodeURIComponent(filename), { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('❌ Delete Error: ' + (data.error || 'Unknown error'));
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }
            })
            .catch(error => {
                alert('❌ Error: ' + error.message);
                btn.innerHTML = originalText;
                btn.disabled = false;
            });
    }
}

function filterFiles() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const fileItems = document.querySelectorAll('.file-item');
    
    fileItems.forEach(item => {
        const filename = item.getAttribute('data-filename');
        const student = item.getAttribute('data-student');
        
        if (filename.includes(searchTerm) || student.includes(searchTerm)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

function analyzeHandwriting(filename) {
    const btn = event.target;
    const originalText = btn.innerHTML;
    
    const allOcrBtns = document.querySelectorAll('button[onclick*="analyzeHandwriting"]');
    allOcrBtns.forEach(b => b.disabled = true);
    
    let progress = 0;
    const updateProgress = () => {
        progress += Math.random() * 10;
        if (progress > 90) progress = 90;
        btn.innerHTML = '🔄 Analyzing... ' + Math.round(progress) + '%';
    };
    
    const interval = setInterval(updateProgress, 300);
    
    fetch('/ocr/' + encodeURIComponent(filename))
        .then(response => response.json())
        .then(data => {
            clearInterval(interval);
            btn.innerHTML = '✅ Complete!';
            setTimeout(() => {
                btn.innerHTML = originalText;
                allOcrBtns.forEach(b => b.disabled = false);
            }, 1000);
            
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