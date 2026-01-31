# AI Hands-On Portal

Flask web application for file uploads with advanced handwriting OCR recognition using TrOCR, EasyOCR, and Tesseract.

## Features

- 📁 Student file upload with roll number validation
- 🔍 Advanced handwriting OCR with multiple engines
- 👥 Live user count tracking
- 📋 Clipboard integration for OCR results
- 🚀 GPU acceleration support

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **For GPU acceleration (optional):**
   - Install [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
   - Reinstall PyTorch with CUDA:
     ```bash
     pip uninstall torch torchvision
     pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
     ```

3. **Run the application:**
   ```bash
   python AI_handsOn.py
   ```

4. **Access:** http://localhost:5000

## OCR Engines

- **TrOCR**: Transformer-based handwriting recognition (1.33GB model)
- **EasyOCR**: Multi-language text detection
- **Tesseract**: Traditional OCR engine

## GPU Setup

Set environment variable for faster downloads:
```bash

```

## File Structure

```
AI_handsOn/
├── AI_handsOn.py          # Main Flask application
├── trocr_ocr.py           # TrOCR handwriting recognition
├── enhanced_ocr.py        # Multi-engine OCR system
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