import cv2
import pytesseract
import re
import numpy as np
from datetime import datetime
from fuzzywuzzy import process

# Preprocess the image to enhance bold text for OCR
def preprocess_for_bold_text(image):
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        opening = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        contrast = cv2.addWeighted(opening, 2, opening, -0.5, 0)
        _, binary = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        sharpened = cv2.filter2D(
            binary, -1, np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        )
        return sharpened
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        return image

# FuzzyWuzzy correction function
def fuzzy_correct(text, possible_corrections):
    if not text:
        return text
    best_match = process.extractOne(text, possible_corrections)
    return best_match[0] if best_match and best_match[1] > 80 else text

# Extracting the amount from the image (using various strategies)
def extract_amount(extracted_text):
    try:
        amount_keywords = [
            "Total Amount Due", "Amount Due", "Net Amount", "Amount to be Paid",
            "TOTAL AMOUNT DUE", "Amount Due Rs", "Amount Due in Rs",
            "OTAL DUE", "TOTAL"
        ]
        for keyword in amount_keywords:
            keyword_regex = rf"(?i){keyword}\s*:?\s*(\D*\d+\.?\d*)"
            match = re.search(keyword_regex, extracted_text)
            if match:
                amount = re.sub(r'[^\d.]', '', match.group(1))
                return float(amount) if amount else None
        amount_regex = r"(?i)(?:\D?)(\d{1,3}(?:[\s.,]?\d{3})*(?:[\s.,]?\d{1,2})?)"
        amounts = re.findall(amount_regex, extracted_text)
        valid_amounts = [amount.replace(' ', '').replace(',', '') for amount in amounts if amount]
        valid_amounts = [float(amount) for amount in valid_amounts if amount.replace('.', '', 1).isdigit()]
        return max(valid_amounts) if valid_amounts else None
    except Exception:
        return None

# Extracting phone numbers
def extract_phone_numbers(extracted_text):
    try:
        phone_regex = r"\b\d{10,12}\b"
        phone_numbers = re.findall(phone_regex, extracted_text)
        return phone_numbers if phone_numbers else []
    except Exception:
        return []

# Extracting bill number using regex and fuzzy correction
def extract_bill_number(extracted_text):
    try:
        bill_number_regex = r"Account\s*No\.?\s*[:\-]?\s*([\dA-Za-z]+)"
        match = re.search(bill_number_regex, extracted_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    except Exception:
        return None

# Extracting account number using regex and fuzzy correction (updated regex for new format)
def extract_account_number(extracted_text):
    try:
        account_number_regex = r"Account\s*No\.?\s*[:\-]?\s*([A-Za-z0-9]{6,})"
        match = re.search(account_number_regex, extracted_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        lines = extracted_text.splitlines()
        for i, line in enumerate(lines):
            if re.search(r"Account\s*No", line, re.IGNORECASE):
                possible = re.search(r"([A-Za-z0-9]{6,})", line)
                if possible:
                    return possible.group(1).strip()
                for j in range(1, 3):
                    if i+j < len(lines):
                        possible = re.search(r"([A-Za-z0-9]{6,})", lines[i+j])
                        if possible:
                            return possible.group(1).strip()
        return None
    except Exception:
        return None

# Extracting meter number using regex and fuzzy correction (updated regex for new format)
def extract_meter_number(extracted_text):
    try:
        meter_number_regex = r"Meter\s*No\.?\s*[:\-]?\s*([\dA-Za-z]+)"
        match = re.search(meter_number_regex, extracted_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        lines = extracted_text.splitlines()
        for i, line in enumerate(lines):
            if re.search(r"Meter\s*No", line, re.IGNORECASE):
                if i+1 < len(lines):
                    possible = re.search(r"([\dA-Za-z]+)", lines[i+1])
                    if possible:
                        return possible.group(1).strip()
        return None
    except Exception:
        return None

# Extracting ID number using regex and fuzzy correction
def extract_id_number(extracted_text):
    id_number_regex = r"(?i)(?:id no\.?|id number|tin|seq no)\s*[:\-]?\s*(\d{3}[-\d]{3,})"
    id_match = re.search(id_number_regex, extracted_text)
    return fuzzy_correct(id_match.group(1).strip(), ["id", "number", "seq"]) if id_match else "ID number not found"

# Extracting area code
def extract_area_code(extracted_text):
    area_code_regex = r"(?i)(?:area code|region code)\s*[:\-]?\s*(\d{3,5})"
    area_code_match = re.search(area_code_regex, extracted_text)
    return area_code_match.group(1).strip() if area_code_match else "Area code not found"

# Extracting name from the image (customer, owner, etc.)
def extract_name(extracted_text):
    name_regex = r"(?i)(?:name|account name|consumer name|owner name)\s*[:\-]?\s*([A-Za-z\s]+)"
    name_match = re.search(name_regex, extracted_text)
    return name_match.group(1).strip() if name_match else "Name not found"

# Extracting address from the image
def extract_address(extracted_text):
    address_regex = r"(?i)(?:address)\s*[:\-]?\s*([^\n]+)"
    address_match = re.search(address_regex, extracted_text)
    return address_match.group(1).strip() if address_match else "Address not found"

# Extracting reading and due dates
def extract_dates(extracted_text):
    try:
        full_date_regex = r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}[.,]\s+\d{4})"
        date_strs = re.findall(full_date_regex, extracted_text, re.IGNORECASE)
        parsed_dates = []
        for date_str in date_strs:
            date_str = date_str.replace('.', ',').replace('  ', ' ')
            try:
                parsed_date = datetime.strptime(date_str.strip(), "%b %d, %Y")
            except ValueError:
                try:
                    parsed_date = datetime.strptime(date_str.strip(), "%B %d, %Y")
                except ValueError:
                    continue
            parsed_dates.append(parsed_date)
        if parsed_dates:
            parsed_dates.sort()
            reading_date = parsed_dates[0].strftime("%d/%m/%Y")
            due_date = parsed_dates[-1].strftime("%d/%m/%Y")
        else:
            reading_date = None
            due_date = None
        return reading_date, due_date
    except Exception:
        return None, None

def extract_water_bill_fields(image: np.ndarray) -> dict:
    """
    Main function to extract all relevant fields from a water bill image.
    Args:
        image (np.ndarray): The image as a numpy array (BGR).
    Returns:
        dict: Extracted fields.
    """
    preprocessed = preprocess_for_bold_text(image)
    extracted_text = pytesseract.image_to_string(preprocessed, config='--psm 6')
    reading_date, due_date = extract_dates(extracted_text)
    return {
        "amount": extract_amount(extracted_text),
        "phone_numbers": extract_phone_numbers(extracted_text),
        "bill_number": extract_bill_number(extracted_text),
        "account_number": extract_account_number(extracted_text),
        "meter_number": extract_meter_number(extracted_text),
        "reading_date": reading_date,
        "due_date": due_date,
        "raw_text": extracted_text
    }






