import os
from google import genai  # Use the new import
from PIL import Image

# Force the use of GEMINI_API_KEY
api_key = os.environ.get("GEMINI_API_KEY")

# Pass it explicitly to the client
client = genai.Client(api_key=api_key)

def recognize_handwriting(image_path):
    """Handwriting OCR using Google GenAI 2026 SDK"""
    
    if not os.path.exists(image_path):
        return {"error": f"File not found: {image_path}"}
    
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
        return {"error": "Invalid file format. Use JPG, PNG, BMP, or TIFF"}

    try:
        # Load image
        img = Image.open(image_path)
        
        # Use the modern Gemini 3 family
        response = client.models.generate_content(
            model='gemini-3-flash-preview',  # gemini-pro-vision is 404/retired
            contents=[
                "Extract all handwritten text from this image. Return only the text content.",
                img
            ]
        )

        extracted_text = response.text.strip()
        
        if extracted_text:
            return {
                "texts": [{"text": extracted_text, "confidence": 0.95, "engine": "google-genai"}],
                "engines_used": ["Google GenAI"],
                "total_results": 1
            }
        else:
            return {
                "texts": [],
                "engines_used": ["Google GenAI"],
                "total_results": 0
            }

    except Exception as e:
        return {"error": f"API Error: {str(e)}"}