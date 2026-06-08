import re
import cv2
import numpy as np
from PIL import Image
import pytesseract

def extract_plate(image):
    try:
        # Preprocess image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        pil_img = Image.fromarray(thresh)
        text = pytesseract.image_to_string(pil_img, config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        
        clean = re.sub(r'[^A-Z0-9]', '', text.upper())
        print(f'[OCR] Raw: {clean}')
        
        match = re.search(r'[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{3,4}', clean)
        if match:
            return match.group(0)
        return clean[:10] if len(clean) >= 6 else None
    except Exception as e:
        print(f'[OCR ERROR] {e}')
        return None
