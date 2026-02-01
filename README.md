# AI Hands-On Portal

Flask web application for file uploads with handwriting OCR recognition using Google Gemini AI.

## Features

- 📁 Student file upload with roll number validation
- 🔍 Handwriting OCR with Google Gemini AI
- 👥 Live user count tracking
- 📋 Clipboard integration for OCR results
- 🔍 Search functionality for files and students
- 🗑️ File deletion with confirmation
- 📱 Mobile-responsive design

## Quick Start

1. **Set API key:**
   ```bash
   setx GEMINI_API_KEY "your-api-key-here"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python AI_handsOn.py
   ```

4. **Access:** http://localhost:5000

## OCR Engine

- **Google Gemini AI**: Primary OCR engine using gemini-3-pro-preview model
- **EasyOCR**: Fallback OCR engine for basic handwriting recognition
- **No GPU required**: Runs efficiently on CPU

## File Structure

```
AI_handsOn/
├── AI_handsOn.py          # Main Flask application
├── gemini_ocr.py          # Google Gemini AI OCR module
├── simple_ocr.py          # EasyOCR fallback module
├── requirements.txt       # Dependencies
├── templates/             # HTML templates
│   └── index.html         # Main web interface
├── static/                # Static assets
│   ├── css/
│   │   └── style.css      # Stylesheet
│   ├── js/
│   │   └── app.js         # JavaScript functionality
│   └── favicon.ico        # Site icon
└── uploads/               # Student file storage
```