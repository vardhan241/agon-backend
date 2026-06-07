import cv2
import numpy as np
import re

reader = None

def get_reader():
    global reader
    if reader is None:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
    return reader

def detect_plate_region(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = w / h
        if 2.5 < aspect_ratio < 6.0 and w > 100:
            return img[y:y+h, x:x+w]
    return img

def clean_plate_text(texts):
    text = ''.join(texts).upper()
    text = re.sub(r'[^A-Z0-9]', '', text)
    text = text.replace('O', '0')
    text = text.replace('I', '1')
    text = text.replace('Q', '0')
    text = text.replace('S', '5')
    text = text.replace('B', '8')
    text = text.replace('Z', '2')
    match = re.search(r'[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{3,4}', text)
    if match:
        return match.group(0)
    return text

def extract_plate(image):
    try:
        if image is None:
            return ''
        ocr = get_reader()
        plate_img = detect_plate_region(image)
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        candidates = []
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        candidates.append(otsu)
        candidates.append(cv2.bitwise_not(otsu))
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        candidates.append(adaptive)
        candidates.append(gray)
        best_result = ''
        best_conf = 0
        for candidate in candidates:
            results = ocr.readtext(candidate, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', detail=1, paragraph=False)
            for (_, text, conf) in results:
                cleaned = clean_plate_text([text])
                if conf > best_conf and len(cleaned) >= 6:
                    best_conf = conf
                    best_result = cleaned
        print(f'[OCR] Result: {best_result} | Conf: {best_conf:.2f}')
        return best_result if best_result else ''
    except Exception as e:
        print(f'[OCR ERROR] {e}')
        return ''