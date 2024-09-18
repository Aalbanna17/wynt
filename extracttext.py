import fitz
from fastapi import HTTPException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_content: bytes, max_word_count: int = 200) -> (str, bool):
    try:
        with fitz.open(stream=file_content, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()

        word_count = len(text.split())
        logger.info(f"Word count: {word_count}")

        if not text or word_count < max_word_count:
            logger.warning("Text is either empty or exceeds the maximum word count.")
            return "", False

        logger.info(f"extract_text_from_pdf: {text[:100]}")
        return text, True

    except Exception as e:
        logger.error(f"Error reading PDF file: {str(e)}")
        return "", False
    
    
def extract_text_from_pdf_old(file_content: bytes):
    try:
        with fitz.open(stream=file_content, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
                logger.info(f"extract_text_from_pdf: {text}")
        return text
    except Exception as e:
        logger.error(f"Error reading PDF file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process PDF file")