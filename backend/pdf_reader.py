from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract
import io

# 👇 EXPLICIT TESSERACT PATH (NO ENV REQUIRED) - only for windows user
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    1. Try normal text extraction (digital PDFs)
    2. If empty → fallback to OCR (scanned PDFs)
    """

    # 1️⃣ Try pdfminer first
    try:
        text = extract_text(io.BytesIO(pdf_bytes))
        if text and text.strip():
            return text
    except Exception:
        pass

    # 2️⃣ OCR fallback (scanned PDFs)
    try:
        images = convert_from_bytes(pdf_bytes)
        ocr_text = ""
        for img in images:
            ocr_text += pytesseract.image_to_string(img)
        return ocr_text
    except Exception as e:
        print("OCR FAILED:", e)
        return ""