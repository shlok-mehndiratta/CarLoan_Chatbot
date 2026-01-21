from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract
import io
import os

TESSERACT_PATH = os.getenv("TESSERACT_PATH")
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

MAX_PAGES = 5


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        text = extract_text(io.BytesIO(pdf_bytes))
        if text and text.strip():
            return text
    except Exception:
        pass

    try:
        images = convert_from_bytes(
            pdf_bytes,
            dpi=300,
            first_page=1,
            last_page=MAX_PAGES
        )
        ocr_text = ""
        for img in images:
            ocr_text += pytesseract.image_to_string(img)

        ocr_text = ocr_text.replace("\n", " ")
        return " ".join(ocr_text.split())

    except Exception:
        return ""