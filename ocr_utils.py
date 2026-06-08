import re

def extract_plate(image):
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(image)
        full_text = ' '.join([r[1] for r in results]).upper()
        full_text = re.sub(r'[^A-Z0-9]', '', full_text)
        print(f'[OCR] Raw: {full_text}')
        match = re.search(r'[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{3,4}', full_text)
        if match:
            return match.group(0)
        return full_text[:10] if len(full_text) >= 6 else None
    except Exception as e:
        print(f'[OCR ERROR] {e}')
        return None
