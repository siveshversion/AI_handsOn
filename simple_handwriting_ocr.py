import cv2
import numpy as np
import os
import sys

# Python 3.14.2 compatible imports
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("EasyOCR not available. Install with: pip install easyocr")

def recognize_handwriting(image_path):
    """Main function to recognize handwriting from image path"""
    
    # Check if file exists
    if not os.path.exists(image_path):
        return {"error": f"File not found: {image_path}"}
    
    # Check file extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
        return {"error": "Invalid file format. Use JPG, PNG, BMP, or TIFF"}
    
    try:
        # Read and preprocess image
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "Could not load image"}
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Resize image to improve small text recognition (scale up by 2x)
        height, width = gray.shape
        gray = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive threshold for better text extraction
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Morphological operations to clean up small text
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Invert if needed (text should be black on white)
        if np.mean(cleaned) < 127:
            cleaned = cv2.bitwise_not(cleaned)
        
        results = {"preprocessing": "completed", "texts": []}
        
        # Try OCR if available
        if EASYOCR_AVAILABLE:
            reader = easyocr.Reader(['en'])
            
            # Try multiple approaches for better small text recognition
            ocr_results = []
            
            # 1. Original image
            try:
                ocr_original = reader.readtext(image_path, detail=1, width_ths=0.4, height_ths=0.4)
                ocr_results.extend(ocr_original)
            except:
                pass
            
            # 2. Processed image with better settings for small text
            try:
                ocr_processed = reader.readtext(cleaned, detail=1, width_ths=0.3, height_ths=0.3, paragraph=False)
                ocr_results.extend(ocr_processed)
            except:
                pass
            
            # 3. Further upscaled version for very small text
            try:
                upscaled = cv2.resize(cleaned, (width * 4, height * 4), interpolation=cv2.INTER_CUBIC)
                ocr_upscaled = reader.readtext(upscaled, detail=1, width_ths=0.2, height_ths=0.2)
                ocr_results.extend(ocr_upscaled)
            except:
                pass
            
            # Collect results with lower confidence threshold for small text
            for bbox, text, confidence in ocr_results:
                if confidence > 0.2 and len(text.strip()) > 0:  # Lower threshold for small text
                    results["texts"].append({
                        "text": text.strip(),
                        "confidence": round(confidence, 2)
                    })
            
            # Remove duplicates and sort by confidence
            seen = set()
            unique_texts = []
            for item in sorted(results["texts"], key=lambda x: x["confidence"], reverse=True):
                text_lower = item["text"].lower()
                if text_lower not in seen:
                    seen.add(text_lower)
                    unique_texts.append(item)
            results["texts"] = unique_texts
            
        else:
            results["error"] = "EasyOCR not available. Install with: pip install easyocr"
        
        return results
        
    except Exception as e:
        return {"error": str(e)}

# Simple usage function
def ocr_from_path(file_path):
    """Simple wrapper for command line usage"""
    print(f"🔍 Analyzing: {file_path}")
    result = recognize_handwriting(file_path)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print("\n📝 Detected Text:")
    if result["texts"]:
        for i, item in enumerate(result["texts"], 1):
            print(f"  {i}. '{item['text']}' (confidence: {item['confidence']})")
    else:
        print("  No text detected")
    
    return result

# Usage examples
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Command line usage: python simple_handwriting_ocr.py image.jpg
        image_path = sys.argv[1]
        ocr_from_path(image_path)
    else:
        # Default usage
        image_path = 'my_handwriting.jpg'
        if os.path.exists(image_path):
            ocr_from_path(image_path)
        else:
            print(f"❌ Default image '{image_path}' not found!")
            print("Usage: python simple_handwriting_ocr.py <image_path>")
            print("Example: python simple_handwriting_ocr.py my_image.jpg")