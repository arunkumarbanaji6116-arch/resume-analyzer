import os
import re
import shutil

from PIL import Image, ImageOps, UnidentifiedImageError


class ResumeImageError(ValueError):
    """Raised when a resume image cannot be safely converted to text."""


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
    import pytesseract
    return pytesseract.image_to_string(image)


def _extract_with_rapidocr(image) -> str:
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    result, _ = ocr(np.array(image))
    if not result:
        return ""
    lines = [item[1] for item in result if len(item) > 1 and item[1]]
    return "\n".join(lines)


def extract_text_from_resume_image(image_file) -> str:
    """Read a resume screenshot with OCR without persisting the uploaded file."""
    try:
        image_file.stream.seek(0)
        with Image.open(image_file.stream) as source:
            source.verify()

        image_file.stream.seek(0)
        with Image.open(image_file.stream) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            if image.width * image.height > 24_000_000:
                image.thumbnail((4000, 4000))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ResumeImageError("Upload a valid PNG, JPG, JPEG, or WEBP resume image.") from error

    text = ""
    engines_attempted = False

    # 1. Try Tesseract OCR if configured or installed
    try:
        import pytesseract
        if _configure_tesseract():
            engines_attempted = True
            text = _extract_with_tesseract(image)
    except Exception:
        text = ""

    # 2. Fall back to RapidOCR if Tesseract was not installed or produced no text
    if not text:
        try:
            from rapidocr_onnxruntime import RapidOCR
            engines_attempted = True
            text = _extract_with_rapidocr(image)
        except Exception:
            pass

    if not engines_attempted:
        raise ResumeImageError(
            "Image review is not configured. Install Tesseract OCR or rapidocr-onnxruntime."
        )

    if not re.search(r"[A-Za-z0-9]", text):
        raise ResumeImageError("We could not read text from that image. Upload a sharper, well-lit resume image.")
    return text.strip()


ACTION_VERBS = {"built", "led", "created", "improved", "designed", "delivered", "managed", "developed", "launched", "increased"}


def analyze_resume(text: str, target_role: str = "") -> dict:
    try:
        from ai.gemini_client import gemini_analyze_resume
        gemini_result = gemini_analyze_resume(text, target_role)
        if gemini_result:
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
