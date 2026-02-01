import cv2
import numpy as np
import os
from PIL import Image

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

def preprocess_image_simple(image_path):
    """Simple and fast preprocessing"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Simple upscaling (3x only)
    height, width = gray.shape
    upscaled = cv2.resize(gray, (width * 3, height * 3), interpolation=cv2.INTER_LINEAR)
    
    # Simple thresholding
    _, thresh = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def recognize_handwriting(image_path):
    """Simple handwriting recognition using EasyOCR with aggressive preprocessing"""
    
    if not os.path.exists(image_path):
        return {"error": f"File not found: {image_path}"}
    
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
        return {"error": "Invalid file format. Use JPG, PNG, BMP, or TIFF"}
    
    if not EASYOCR_AVAILABLE:
        return {"error": "EasyOCR not available. Install: pip install easyocr"}
    
    try:
        # Simple preprocessing
        processed_img = preprocess_image_simple(image_path)
        if processed_img is None:
            return {"error": "Could not load image"}
        
        # Initialize EasyOCR
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        
        # Simple OCR call
        results = reader.readtext(processed_img, detail=1)
        
        ocr_results = []
        for bbox, text, confidence in results:
            if confidence > 0.3 and text.strip():  # Normal threshold
                ocr_results.append({
                    "text": text.strip(),
                    "confidence": round(confidence, 2),
                    "engine": "easyocr"
                })
        
        return {
            "texts": ocr_results,
            "engines_used": ["EasyOCR"],
            "total_results": len(ocr_results)
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"🔍 Simple OCR Analysis: {image_path}")
        result = recognize_handwriting(image_path)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"\n📝 Detected Text:")
            if result["texts"]:
                for i, item in enumerate(result["texts"], 1):
                    print(f"  {i}. '{item['text']}' (confidence: {item['confidence']})")
            else:
                print("  No text detected")
    else:
        print("Usage: python simple_ocr.py image.jpg")