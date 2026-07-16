import os
import re
import cv2
import pytesseract
import json
from datetime import datetime

# Optional: uncomment and configure if Tesseract is installed in a non-standard Windows path
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

_tesseract_available = None

def is_tesseract_installed():
    """
    Checks if the Tesseract OCR executable is available in the system PATH.

    Saves the check result globally to avoid spawning process checks on 
    every image run.

    Returns:
    -------
    bool
        True if Tesseract is installed and accessible, False otherwise.
    """
    global _tesseract_available
    if _tesseract_available is not None:
        return _tesseract_available
    try:
        pytesseract.get_tesseract_version()
        _tesseract_available = True
    except Exception:
        _tesseract_available = False
    return _tesseract_available

def extract_dates(text):
    """
    Parses date fields from raw extracted OCR text using Regular Expressions.

    Searches specifically for labels 'DATE OF BIRTH', 'ISSUE DATE', and 
    'EXPIRY DATE' followed by dates formatted in YYYY-MM-DD pattern.

    Parameters:
    ----------
    text : str
        The raw text output returned from the OCR engine.

    Returns:
    -------
    dob : datetime.date or None
        Parsed Date of Birth, or None if matching fails or format is invalid.
    issue : datetime.date or None
        Parsed Date of Issue, or None if matching fails or format is invalid.
    expiry : datetime.date or None
        Parsed Date of Expiry, or None if matching fails or format is invalid.
    """
    # Match dates in standard YYYY-MM-DD format based on context labels
    dob_match = re.search(r'DATE\s+OF\s+BIRTH:?\s*(\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
    issue_match = re.search(r'ISSUE\s+DATE:?\s*(\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
    expiry_match = re.search(r'EXPIRY\s+DATE:?\s*(\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
    
    dob = None
    issue = None
    expiry = None
    
    if dob_match:
        try:
            dob = datetime.strptime(dob_match.group(1).strip(), "%Y-%m-%d").date()
        except ValueError:
            pass
    if issue_match:
        try:
            issue = datetime.strptime(issue_match.group(1).strip(), "%Y-%m-%d").date()
        except ValueError:
            pass
    if expiry_match:
        try:
            expiry = datetime.strptime(expiry_match.group(1).strip(), "%Y-%m-%d").date()
        except ValueError:
            pass
            
    return dob, issue, expiry

def extract_mrz(text):
    """
    Safely extracts Machine Readable Zone (MRZ) lines from text.
    If MRZ is not found or is incomplete, returns None.

    Parameters:
    ----------
    text : str
        Raw text extracted from OCR.

    Returns:
    -------
    list of str or None
        List containing the 3 MRZ lines, or None if not detected.
    """
    try:
        # Match lines of exactly 30 characters consisting of A-Z, 0-9, and '<'
        lines = [line.strip() for line in text.split('\n') if re.match(r'^[A-Z0-9<]{30}$', line.strip())]
        if len(lines) >= 3:
            # Return the last 3 lines (which correspond to the MRZ band)
            return lines[-3:]
    except Exception:
        pass
    return None

def run_ocr_pipeline(image_path, metadata_cache=None):
    """
    Runs the image loading, grayscale preprocessing, OCR, and Regex parsing.

    If Tesseract OCR is not found on the host machine, the pipeline automatically 
    falls back to a simulated OCR mode. It reads the ground truth text from the 
    provided metadata cache to ensure the rest of the application (Regex parsing 
    and Semantic checks) remains executable.

    Parameters:
    ----------
    image_path : str
        The absolute file path of the digital ID card image to process.
    metadata_cache : dict, optional
        A dictionary containing ground truth data for the images. Used for 
        fallback OCR simulation if Tesseract is missing.

    Returns:
    -------
    dob : datetime.date or None
        The parsed Date of Birth.
    issue : datetime.date or None
        The parsed Issue Date.
    expiry : datetime.date or None
        The parsed Expiry Date.
    text : str
        The raw text extracted by OCR or simulated.
    is_simulated : bool
        True if the simulated fallback mode was active, False if real Tesseract ran.
    """
    # 1. Load the image and verify
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")
        
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image data at {image_path}")
        
    # 2. OpenCV preprocessing: Grayscale
    # Convert image to single-channel gray to improve characters contrast for OCR.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 3. Tesseract OCR Text Extraction
    text = ""
    is_simulated = False
    
    if is_tesseract_installed():
        try:
            # Run OCR on the grayscaled image
            text = pytesseract.image_to_string(gray)
        except Exception:
            is_simulated = True
    else:
        is_simulated = True
        
    if is_simulated:
        # Fallback simulation: read from metadata if tesseract is missing
        filename = os.path.basename(image_path)
        if metadata_cache and filename in metadata_cache:
            data = metadata_cache[filename]
            # Construct synthetic OCR text mirroring the layout drawn by generator.py
            text = (
                f"REPUBLIC OF SYNTHESIA\n"
                f"NATIONAL DIGITAL ONBOARDING IDENTITY CARD\n"
                f"ID NUMBER: {data['id_number']}\n"
                f"FULL NAME: {data['name'].upper()}\n"
                f"DATE OF BIRTH: {data['dob']}\n"
                f"ISSUE DATE: {data['issue_date']}\n"
                f"EXPIRY DATE: {data['expiry_date']}\n"
            )
            # Append simulated MRZ lines for fallback
            try:
                from generator import generate_mrz_lines
                dob_obj = datetime.strptime(data['dob'], "%Y-%m-%d").date()
                mrz_lines = generate_mrz_lines(data['id_number'].replace("ID-", ""), data['name'], dob_obj)
                text += "\n" + "\n".join(mrz_lines) + "\n"
            except Exception:
                pass
        else:
            raise RuntimeError(
                f"Tesseract OCR is not installed, and metadata cache for {filename} is missing. "
                f"Make sure to pass the metadata_cache dictionary."
            )
            
    # 4. Normalize and extract fields using regex
    dob, issue, expiry = extract_dates(text)
    
    return dob, issue, expiry, text, is_simulated
