import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("shared.ai.document_analysis")

MEDICAL_KEYWORDS_FR = [
    "médicament", "traitement", "diagnostic", "prescription", "posologie",
    "mg", "g", "ml", "comprimé", "gélule", "sirop", "injection",
    "hopital", "clinique", "urgences", "consultation", "radiographie",
    "scanner", "irm", "échographie", "analyse", "prise de sang",
    "ordonnance", "certificat médical", "vaccin", "allergie",
    "diabète", "hypertension", "asthme", "cardiaque", "infection",
    "fièvre", "douleur", "céphalée", "nausée", "vertige",
    "chirurgie", "intervention", "hospitalisation", "rééducation",
]

DIAGNOSIS_PATTERNS = [
    (r"(diagnostic|diagnostiqué|diagnostiquée)\s*[:\-]?\s*(.+?)(?:\.|$)", 2),
    (r"(pathologie|maladie|affection|syndrome)\s*[:\-]?\s*(.+?)(?:\.|$)", 2),
    (r"(souffre de|souffrant|présente)\s+(.+?)(?:\.|$)", 2),
    (r"(diabète|hypertension|asthme|allergie|épilepsie|arthrose|cancer)", 1),
]

MEDICATION_PATTERNS = [
    r"\b(\d+)\s*(mg|g|ml|µg|ui)\b",
    r"(comprim[ée]|gélule|capsule|sachet|injection|pipette)\s+(de\s+)?(\w+)",
    r"(prendre|appliquer|injecter|avaler)\s+(\w+)",
]


def extract_text_from_image(file_path: str) -> str:
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img, lang="fra+ara+eng")
        return text.strip()
    except ImportError:
        logger.warning("pytesseract or PIL not available")
        return ""
    except Exception as exc:
        logger.error("OCR failed: %s", exc)
        return ""


def extract_text_from_pdf(file_path: str) -> tuple[str, int]:
    try:
        import PyPDF2
        pages = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    pages.append(txt)
        return "\n".join(pages), len(reader.pages)
    except ImportError:
        logger.warning("PyPDF2 not available")
        return "", 0
    except Exception as exc:
        logger.error("PDF extraction failed: %s", exc)
        return "", 0


def extract_text_from_txt(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as exc:
            logger.error("TXT extraction failed: %s", exc)
            return ""


def detect_language(text: str) -> str:
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    total = arabic_chars + latin_chars
    if total == 0:
        return "fr"
    return "ar" if arabic_chars / total > 0.3 else "fr"


def extract_medical_keywords(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for kw in MEDICAL_KEYWORDS_FR:
        if kw in text_lower:
            found.append(kw)
    return sorted(set(found))


def extract_diagnosis_mentions(text: str) -> list[str]:
    mentions = []
    for pattern, group_idx in DIAGNOSIS_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            if isinstance(m, tuple):
                mentions.append(m[group_idx - 1].strip())
            else:
                mentions.append(m.strip())
    return list(dict.fromkeys(mentions))


def extract_medication_mentions(text: str) -> list[str]:
    mentions = []
    for pattern in MEDICATION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            if isinstance(m, tuple):
                mentions.append(" ".join(m).strip())
            else:
                mentions.append(m.strip())
    return list(dict.fromkeys(mentions))


def generate_summary(text: str, category: str, keywords: list[str]) -> str:
    sentences = re.split(r"[.!?\n]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    summary_parts = []
    if category:
        summary_parts.append(f"Catégorie : {category}")
    if keywords:
        summary_parts.append(f"Mots-clés : {', '.join(keywords[:5])}")
    if sentences:
        summary_parts.append(sentences[0][:200])
    return " | ".join(summary_parts)


def classify_document_category(text: str, hint: str = "") -> str:
    text_lower = text.lower()
    if hint and hint != "other":
        return hint

    category_scores = {
        "prescription": ["ordonnance", "prescription", "posologie", "comprimé", "mg"],
        "report": ["rapport médical", "compte rendu", "c.r.", "certificat", "examen"],
        "imaging": ["radiographie", "scanner", "irm", "échographie", "imagerie"],
        "lab_result": ["analyse", "prise de sang", "résultat", "bilan", "laboratoire"],
        "invoice": ["facture", "reçu", "paiement", "montant", "tva", "total"],
        "id_document": ["pièce d'identité", "cin", "passeport", "permis", "carte"],
    }

    scores = {}
    for cat, keywords in category_scores.items():
        scores[cat] = sum(1 for kw in keywords if kw in text_lower)

    return max(scores, key=scores.get) if max(scores.values(), default=0) > 0 else "other"


class DocumentAnalysisService:

    def analyze(self, file_path: str, title: str = "", category: str = "",
                language: str = "fr") -> dict:
        start = time.time()
        path = Path(file_path)
        ext = path.suffix.lower()
        file_size = path.stat().st_size

        extracted_text = ""
        page_count = None

        if ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
            extracted_text = extract_text_from_image(file_path)
            if not extracted_text:
                extracted_text = extract_text_from_txt(file_path)
        elif ext == ".pdf":
            extracted_text, page_count = extract_text_from_pdf(file_path)
            if not extracted_text:
                extracted_text = extract_text_from_image(file_path)
        elif ext == ".txt":
            extracted_text = extract_text_from_txt(file_path)
        else:
            extracted_text = extract_text_from_txt(file_path)
            if not extracted_text:
                pass

        if not extracted_text:
            detected_lang = language
            return {
                "extracted_text": "",
                "language": detected_lang,
                "category": category or "other",
                "category_auto": "other",
                "medical_keywords": [],
                "diagnosis_mentions": [],
                "medication_mentions": [],
                "summary": "Aucun texte n'a pu être extrait de ce document.",
                "file_name": path.name,
                "file_size_bytes": file_size,
                "file_type": ext[1:] if ext else "unknown",
                "page_count": page_count,
                "ocr_confidence": None,
                "analysis_duration_ms": int((time.time() - start) * 1000),
                "error": "text_extraction_failed",
            }

        detected_lang = detect_language(extracted_text)
        detected_category = classify_document_category(extracted_text, category)
        keywords = extract_medical_keywords(extracted_text)
        diagnoses = extract_diagnosis_mentions(extracted_text)
        medications = extract_medication_mentions(extracted_text)
        summary = generate_summary(extracted_text, detected_category, keywords)

        return {
            "extracted_text": extracted_text[:10000],
            "language": detected_lang,
            "category": category or detected_category,
            "category_auto": detected_category,
            "medical_keywords": keywords,
            "diagnosis_mentions": diagnoses,
            "medication_mentions": medications,
            "summary": summary,
            "file_name": path.name,
            "file_size_bytes": file_size,
            "file_type": ext[1:] if ext else "unknown",
            "page_count": page_count,
            "ocr_confidence": None,
            "analysis_duration_ms": int((time.time() - start) * 1000),
        }


document_analysis_service = DocumentAnalysisService()
