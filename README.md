# AI Hands-On Portal

Flask web application for file uploads with handwriting OCR recognition using EasyOCR.

## Features

- 📁 Student file upload with roll number validation
- 🔍 Handwriting OCR with image preprocessing
- 👥 Live user count tracking
- 📋 Clipboard integration for OCR results
- 🔍 Search functionality for files and students
- 🗑️ File deletion with confirmation
- 📱 Mobile-responsive design

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python AI_handsOn.py
   ```

3. **Access:** http://localhost:5000

## OCR Engine

- **EasyOCR**: Lightweight OCR engine with handwriting support
- **Preprocessing**: Image upscaling and thresholding for better recognition
- **No GPU required**: Runs efficiently on CPU

## File Structure

```
AI_handsOn/
├── AI_handsOn.py          # Main Flask application
├── simple_ocr.py          # EasyOCR handwriting recognition
├── requirements.txt       # Dependencies
├── templates/             # HTML templates
│   └── index.html         # Main web interface
├── static/                # Static assets
│   ├── css/
│   │   └── style.css      # Stylesheet
│   └── js/
│       └── app.js         # JavaScript functionality
└── uploads/               # Student file storage
```