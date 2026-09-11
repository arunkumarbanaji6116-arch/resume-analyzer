import io
import logging
import os
import re
import shutil
import zipfile

from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)


class ResumeImageError(ValueError):
    """Raised when a resume document or image cannot be safely converted to text."""


ResumeDocumentError = ResumeImageError

_rapidocr_engine = None


def _get_rapidocr():
    """Lazily instantiate and cache the RapidOCR ONNX model for high throughput."""
    global _rapidocr_engine
    if _rapidocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _rapidocr_engine = RapidOCR()
        except Exception as exc:
            logger.warning("RapidOCR could not be initialized: %s", exc)
            _rapidocr_engine = False
    return _rapidocr_engine if _rapidocr_engine is not False else None


def _configure_tesseract() -> bool:
    """Find and configure tesseract binary if available on Windows or system PATH."""
    try:
        import pytesseract
    except ImportError:
        return False

    if shutil.which("tesseract"):
        return True

    candidates = [
        os.environ.get("TESSERACT_CMD"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
    ]

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            tessdata_dir = os.path.join(os.path.dirname(candidate), "tessdata")
            if os.path.isdir(tessdata_dir) and "TESSDATA_PREFIX" not in os.environ:
                os.environ["TESSDATA_PREFIX"] = tessdata_dir
            return True

    return False


def _extract_with_tesseract(image) -> str:
    try:
        import pytesseract
        return pytesseract.image_to_string(image) or ""
    except Exception:
        return ""


def _extract_with_rapidocr(image) -> str:
    ocr = _get_rapidocr()
    if not ocr:
        return ""
    try:
        import numpy as np
        result, _ = ocr(np.array(image))
        if not result:
            return ""
        lines = [item[1] for item in result if len(item) > 1 and item[1]]
        return "\n".join(lines).strip()
    except Exception as exc:
        logger.warning("RapidOCR execution error: %s", exc)
        return ""


def _extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF pages with high-speed digital stream parsing (sub-50ms)."""
    text_chunks = []
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_chunks.append(page_text.strip())
    except Exception as exc:
        logger.warning("pypdf extraction failed: %s", exc)

    extracted = "\n\n".join(text_chunks).strip()
    # If the PDF has text content (99% of digital resumes), return instantly in <0.02s!
    if len(extracted) >= 30 and re.search(r"[A-Za-z0-9]", extracted):
        return extracted

    # Only if digital extraction returned virtually no text (pure scanned image), try cloud/OCR
    try:
        from ai.gemini_client import gemini_extract_text_from_image_bytes
        cloud_txt = gemini_extract_text_from_image_bytes(content, mime_type="application/pdf")
        if cloud_txt and re.search(r"[A-Za-z0-9]", cloud_txt):
            return cloud_txt.strip()
    except Exception:
        pass

    return extracted


def _extract_text_from_docx(content: bytes) -> str:
    """Extract text from Word .docx file (paragraphs and tables)."""
    # 1. Primary: python-docx
    try:
        import docx
        doc = docx.Document(io.BytesIO(content))
        elements = []
        for p in doc.paragraphs:
            if p.text.strip():
                elements.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    elements.append(" | ".join(cells))
        full_text = "\n".join(elements).strip()
        if full_text and re.search(r"[A-Za-z0-9]", full_text):
            return full_text
    except Exception as exc:
        logger.warning("python-docx extraction failed: %s", exc)

    # 2. Fallback: unzip word/document.xml and parse text
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            if "word/document.xml" in z.namelist():
                xml_data = z.read("word/document.xml").decode("utf-8", errors="ignore")
                text = re.sub(r"<[^>]+>", " ", xml_data)
                text = re.sub(r"\s+", " ", text).strip()
                if text and re.search(r"[A-Za-z0-9]", text):
                    return text
    except Exception as exc:
        logger.warning("DOCX zip fallback failed: %s", exc)

    return ""


def _extract_text_from_doc(content: bytes) -> str:
    """Extract legible ASCII/Unicode text blocks from legacy Word 97-2003 (.doc) files."""
    strings = re.findall(rb"[\x20-\x7E\r\n\t]{4,}", content)
    decoded = []
    for s in strings:
        try:
            line = s.decode("ascii", errors="ignore").strip()
            if len(line) > 3:
                decoded.append(line)
        except Exception:
            continue
    return "\n".join(decoded).strip()


def _extract_text_from_txt(content: bytes) -> str:
    """Extract text from plain text or RTF files with encoding fallbacks."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252", "utf-16"):
        try:
            decoded = content.decode(encoding)
            # If RTF format, strip rtf control words
            if decoded.startswith(r"{\rtf"):
                decoded = re.sub(r"\\[a-zA-Z0-9]+", " ", decoded)
                decoded = re.sub(r"[{}]", " ", decoded)
            return re.sub(r"\s+", " ", decoded).strip()
        except UnicodeDecodeError:
            continue
    return ""


def _extract_text_from_image_bytes(content: bytes) -> str:
    """Extract text from image bytes using RapidOCR, Tesseract, and Gemini Vision."""
    try:
        with Image.open(io.BytesIO(content)) as source:
            source.verify()

        with Image.open(io.BytesIO(content)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            if image.width * image.height > 24_000_000:
                image.thumbnail((4000, 4000))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ResumeImageError("Please upload a valid PDF, DOCX, or PNG/JPG/WEBP image.") from error

    text = ""

    # 1. Try RapidOCR first (fast, local, neural ONNX OCR, handles rotated text)
    try:
        text = _extract_with_rapidocr(image)
    except Exception:
        text = ""

    # 2. Try Tesseract if RapidOCR yielded no text
    if not text:
        try:
            if _configure_tesseract():
                text = _extract_with_tesseract(image)
        except Exception:
            text = ""

    # 3. Try Gemini Multimodal Vision if local OCR yielded no text
    if not text or not re.search(r"[A-Za-z0-9]", text):
        try:
            from ai.gemini_client import gemini_extract_text_from_image_bytes
            gemini_txt = gemini_extract_text_from_image_bytes(content, mime_type="image/png")
            if gemini_txt and re.search(r"[A-Za-z0-9]", gemini_txt):
                text = gemini_txt
        except Exception:
            pass

    if not text or not re.search(r"[A-Za-z0-9]", text):
        raise ResumeImageError("We could not read text from that image. Please upload a clearer image or paste the text.")

    return text.strip()


def extract_text_from_file(file_obj) -> str:
    """
    Unified extractor for uploaded resume files.
    Supports PDF (.pdf), Word (.docx, .doc), plain text (.txt), and images (.png, .jpg, .jpeg, .webp).
    Performs in-memory extraction with zero temporary file persistence.
    """
    if not file_obj:
        raise ResumeImageError("No file was provided.")

    # Read binary content from FileStorage stream, file-like object, or bytes
    if hasattr(file_obj, "stream"):
        file_obj.stream.seek(0)
        content = file_obj.stream.read()
        file_obj.stream.seek(0)
    elif hasattr(file_obj, "read"):
        file_obj.seek(0)
        content = file_obj.read()
        file_obj.seek(0)
    elif isinstance(file_obj, (bytes, bytearray)):
        content = bytes(file_obj)
    else:
        raise ResumeImageError("Invalid file payload.")

    if not content:
        raise ResumeImageError("The uploaded file is empty. Please select a valid resume file.")

    if len(content) > 15 * 1024 * 1024:
        raise ResumeImageError("The file size exceeds the 15 MB limit. Please upload a smaller file.")

    filename = getattr(file_obj, "filename", "") or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    text = ""

    # Detect file type by extension and magic bytes
    is_pdf = ext == "pdf" or content.startswith(b"%PDF")
    is_docx = ext == "docx" or (content.startswith(b"PK\x03\x04") and (b"word/" in content[:4096]))
    is_doc = ext == "doc" or content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
    is_txt = ext in {"txt", "rtf", "md"}

    if is_pdf:
        text = _extract_text_from_pdf(content)
    elif is_docx:
        text = _extract_text_from_docx(content)
    elif is_doc:
        text = _extract_text_from_doc(content)
    elif is_txt:
        text = _extract_text_from_txt(content)
    else:
        # Image file (PNG, JPG, WEBP, etc.) or unknown
        try:
            text = _extract_text_from_image_bytes(content)
        except ResumeImageError:
            # If image parse failed, try text decoding as a last resort
            text = _extract_text_from_txt(content)
            if not text or not re.search(r"[A-Za-z0-9]", text):
                raise

    if not text or not re.search(r"[A-Za-z0-9]", text):
        raise ResumeImageError("We could not extract readable text from your file. Please ensure it is not password-protected, or copy and paste the text directly.")

    return text.strip()


# Backward-compatible alias for existing imports
extract_text_from_resume_image = extract_text_from_file


ACTION_VERBS = {"built", "led", "created", "improved", "designed", "delivered", "managed", "developed", "launched", "increased"}


import hashlib

_RESUME_ANALYSIS_CACHE = {}


def analyze_resume(text: str, target_role: str = "") -> dict:
    cache_key = hashlib.md5((text.strip() + "###" + target_role.strip()).encode("utf-8")).hexdigest()
    if cache_key in _RESUME_ANALYSIS_CACHE:
        return _RESUME_ANALYSIS_CACHE[cache_key]

    try:
        from ai.gemini_client import gemini_analyze_resume
        gemini_result = gemini_analyze_resume(text, target_role)
        if gemini_result:
            _RESUME_ANALYSIS_CACHE[cache_key] = gemini_result
            return gemini_result
    except Exception:
        pass

    words = re.findall(r"\b[\w+#.-]+\b", text.lower())
    word_set = set(words)
    word_count = len(words)
    action_count = sum(word in ACTION_VERBS for word in word_set)
    metrics = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", text))
    sections = sum(label in text.lower() for label in ("experience", "education", "skills", "projects"))
    score = min(100, 35 + min(word_count, 350) // 7 + action_count * 4 + metrics * 3 + sections * 4)
    notes = []
    if word_count < 180:
        notes.append("Add more concrete detail to your projects and work experience.")
    if metrics < 2:
        notes.append("Quantify impact with numbers, percentages, scope, or time saved.")
    if action_count < 3:
        notes.append("Start experience bullets with stronger action verbs.")
    if target_role and target_role.lower() not in text.lower():
        notes.append(f"Mention the target role, {target_role}, naturally in your summary.")
    return {"score": score, "word_count": word_count, "metrics": metrics, "notes": notes or ["Strong foundation. Tailor keywords to each job description."]}
