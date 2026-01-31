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