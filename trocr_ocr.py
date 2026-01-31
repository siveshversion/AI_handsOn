import cv2
import numpy as np
import os
from PIL import Image
import torch

# Try TrOCR (best for handwriting)
try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    TROCR_AVAILABLE = True
except ImportError:
    TROCR_AVAILABLE = False

# Fallback OCR engines
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

def preprocess_for_trocr(image_path):
    """Preprocessing optimized for TrOCR handwriting recognition"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aggressive upscaling for handwriting (6x)
    height, width = gray.shape
    upscaled = cv2.resize(gray, (width * 6, height * 6), interpolation=cv2.INTER_CUBIC)
    
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(upscaled)
    
    # Slight blur to smooth handwriting
    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
    
    # Convert back to PIL Image for TrOCR
    pil_image = Image.fromarray(blurred).convert('RGB')
    
    return pil_image

def ocr_with_trocr(image):
    """OCR using TrOCR - best for handwriting with GPU support"""
    if not TROCR_AVAILABLE:
        return []
    
    try:
        # GPU diagnostics
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA device count: {torch.cuda.device_count()}")
            print(f"Current CUDA device: {torch.cuda.current_device()}")
            print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
        
        # Force GPU if available, otherwise use CPU
        if torch.cuda.is_available():
            device = "cuda:0"
            torch.cuda.set_device(0)
        else:
            device = "cpu"
            print("⚠️ GPU not available. Install CUDA toolkit and GPU-enabled PyTorch:")
            print("pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
        
        print(f"Loading TrOCR model on {device}...")
        
        # Load TrOCR model (handwritten text) with fast processor disabled for compatibility
        processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten', use_fast=False)
        model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')
        
        # Move model to GPU if available
        model = model.to(device)
        
        print(f"TrOCR model loaded successfully on {device}")
        
        # Process image
        pixel_values = processor(images=image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(device)  # Move input to GPU
        
        # Generate text
        with torch.no_grad():  # Save GPU memory
            generated_ids = model.generate(pixel_values, max_length=50)
        
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        if generated_text.strip():
            return [{
                "text": generated_text.strip(),
                "confidence": 0.85,
                "engine": f"trocr-{device}"
            }]
        
        return []
    except Exception as e:
        print(f"TrOCR error: {e}")
        return []

def ocr_with_easyocr_handwriting(image):
    """EasyOCR optimized for handwriting"""
    if not EASYOCR_AVAILABLE:
        return []
    
    try:
        reader = easyocr.Reader(['en'], gpu=True, verbose=False)  # Enable GPU for EasyOCR too
        
        # Convert PIL to numpy for EasyOCR
        if hasattr(image, 'save'):  # PIL Image
            image_np = np.array(image.convert('L'))  # Convert to grayscale numpy
        else:
            image_np = image
        
        # Very sensitive settings for handwriting
        ocr_results = reader.readtext(
            image_np, 
            detail=1, 
            width_ths=0.1,    # Very low threshold
            height_ths=0.1,   # Very low threshold
            paragraph=True,   # Try to read as phrases
            decoder='beamsearch'  # Better decoder
        )
        
        results = []
        for bbox, text, confidence in ocr_results:
            if confidence > 0.05 and text.strip():  # Very low threshold
                results.append({
                    "text": text.strip(),
                    "confidence": round(confidence, 2),
                    "engine": "easyocr"
                })
        
        return results
    except:
        return []

def ocr_with_tesseract_handwriting(image):
    """Tesseract optimized for handwriting"""
    if not TESSERACT_AVAILABLE:
        return []
    
    try:
        # Convert PIL to numpy for Tesseract
        if hasattr(image, 'save'):  # PIL Image
            image_np = np.array(image.convert('L'))
        else:
            image_np = image
        
        # Multiple Tesseract configs for handwriting
        configs = [
            '--psm 8 --oem 3',  # Single word
            '--psm 7 --oem 3',  # Single text line
            '--psm 6 --oem 3',  # Single uniform block
            '--psm 13 --oem 3'  # Raw line (no heuristics)
        ]
        
        results = []
        for config in configs:
            try:
                text = pytesseract.image_to_string(image_np, config=config).strip()
                if text and len(text) > 0:
                    results.append({
                        "text": text,
                        "confidence": 0.6,  # Default confidence
                        "engine": "tesseract"
                    })
            except:
                continue
        
        return results
    except:
        return []

def recognize_handwriting(image_path):
    """Advanced handwriting recognition using TrOCR + fallbacks"""
    
    if not os.path.exists(image_path):
        return {"error": f"File not found: {image_path}"}
    
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
        return {"error": "Invalid file format. Use JPG, PNG, BMP, or TIFF"}
    
    try:
        # Preprocess image for TrOCR
        processed_img = preprocess_for_trocr(image_path)
        if processed_img is None:
            return {"error": "Could not load image"}
        
        all_results = []
        engines_used = []
        
        # 1. Try TrOCR first (best for handwriting)
        if TROCR_AVAILABLE:
            trocr_results = ocr_with_trocr(processed_img)
            if trocr_results:
                all_results.extend(trocr_results)
                engines_used.append("TrOCR")
        
        # 2. Try EasyOCR with handwriting settings
        if EASYOCR_AVAILABLE:
            easy_results = ocr_with_easyocr_handwriting(processed_img)
            if easy_results:
                all_results.extend(easy_results)
                engines_used.append("EasyOCR")
        
        # 3. Try Tesseract as final fallback
        if TESSERACT_AVAILABLE:
            tesseract_results = ocr_with_tesseract_handwriting(processed_img)
            if tesseract_results:
                all_results.extend(tesseract_results)
                engines_used.append("Tesseract")
        
        # Remove duplicates and sort by confidence
        seen_texts = {}
        for result in all_results:
            text_clean = result["text"].lower().strip()
            if text_clean and (text_clean not in seen_texts or result["confidence"] > seen_texts[text_clean]["confidence"]):
                seen_texts[text_clean] = result
        
        final_results = list(seen_texts.values())
        final_results.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "texts": final_results,
            "engines_used": engines_used,
            "total_results": len(final_results)
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"🔍 TrOCR Handwriting Analysis: {image_path}")
        result = recognize_handwriting(image_path)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"\n📝 Detected Text using {', '.join(result['engines_used'])}:")
            if result["texts"]:
                for i, item in enumerate(result["texts"], 1):
                    print(f"  {i}. '{item['text']}' (confidence: {item['confidence']}, engine: {item['engine']})")
            else:
                print("  No text detected")
    else:
        print("Usage: python trocr_ocr.py image.jpg")