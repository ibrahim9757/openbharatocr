# Water Bill OCR Extraction Module

This Python module extracts key information from scanned water bill images using OpenCV and Tesseract OCR.  
It is designed for backend/web use and returns results as a Python dictionary, ready for API or further processing.

---

## Features

- **Robust OCR preprocessing** for improved accuracy
- Extracts:
  - Total amount due
  - Phone numbers
  - Bill number
  - Account number
  - Meter number
  - Reading and due dates
  - Raw OCR text
- Modular and easy to integrate with Flask, Django, FastAPI, etc.

---

## Requirements

- Python 3.7+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (must be installed and in your PATH)
- Python packages: `opencv-python`, `numpy`, `pytesseract`, `fuzzywuzzy`

Install dependencies:
```sh
pip install opencv-python numpy pytesseract fuzzywuzzy
```

---

## Usage

```python
import cv2
import numpy as np
from water_bill import extract_water_bill_fields

# Load image (from file, upload, etc.)
image = cv2.imread('path_to_your_bill_image.jpg')

# Extract fields
result = extract_water_bill_fields(image)

# Example output
print(result)
# {
#   "amount": 1066.18,
#   "phone_numbers": ["09273768401", "09628572182"],
#   "bill_number": "Q0Q0909069",
#   "account_number": "Q0Q0909069",
#   "meter_number": "751231",
#   "reading_date": "11/04/2024",
#   "due_date": "02/07/2024",
#   "raw_text": "...full OCR text..."
# }
```

---

## Integration Example (Flask)

```python
from flask import Flask, request, jsonify
import cv2
import numpy as np
from water_bill import extract_water_bill_fields

app = Flask(__name__)

@app.route('/extract', methods=['POST'])
def extract():
    file = request.files['image']
    npimg = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    result = extract_water_bill_fields(image)
    return jsonify(result)

if __name__ == '__main__':
    app.run()
```

---

## Notes

- For best results, use high-quality, well-lit scans or photos.
- If you encounter OCR errors, try adjusting the image preprocessing or Tesseract config.
- The module is designed for Philippine-style water bills but can be adapted for other formats.

---

---

## Changelog & Improvements

This module is a refactored and improved version of the original water bill OCR extraction script.  
**Key changes and improvements include:**

- **Flexible Regex Patterns:**  
  - Regexes now handle both numbers and letters, and search both the same and next lines for values (handles OCR quirks and line breaks).
  - More robust extraction for account number, meter number, bill number, and phone numbers.

- **Consistent Fuzzy Matching:**  
  - FuzzyWuzzy is used throughout to correct for OCR label errors and variations.

- **Improved Preprocessing:**  
  - Added morphological operations, Otsu’s thresholding, and sharpening to enhance image quality for OCR.

- **Better Date Extraction:**  
  - Supports both numeric and month-name date formats (e.g., `Apr 11, 2024` and `11/04/2024`).

- **Web/Backend Ready:**  
  - No hardcoded file paths or print statements.
  - All functions are modular and importable.
  - Main function returns a Python dictionary, ready for API or frontend use.

- **Additional Fields:**  
  - Added extraction for name, address, area code, and ID number.

- **Consistent Return Values:**  
  - Returns `None` or empty lists for missing fields, making it easier to handle in web APIs.

---

## License

MIT License