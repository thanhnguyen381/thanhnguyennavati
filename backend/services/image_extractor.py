"""
image_extractor.py — V3
Trích xuất ảnh đại diện (avatar) từ file CV (PDF / DOCX).
Chiến lược:
  1. Extract tất cả ảnh nhúng trong file
  2. Lọc heuristic: chọn ảnh có tỉ lệ gần 3:4, kích thước hợp lý
  3. Resize về 150×150 (max), encode base64 → trả về frontend
  4. Nếu không tìm được → trả về None (frontend dùng avatar chữ cái)
"""

import io
import base64
import fitz          # PyMuPDF
import docx
from PIL import Image


# ── Ngưỡng heuristic ──────────────────────────────────────────────
MIN_W, MIN_H   = 60,  60     # px — bỏ ảnh quá nhỏ (icon, bullet)
MAX_W, MAX_H   = 800, 800    # px — bỏ ảnh quá to (banner trang trí)
RATIO_MIN      = 0.55        # width/height — ảnh dọc
RATIO_MAX      = 1.30        # width/height — cho phép gần vuông (một số CV Việt)
OUTPUT_SIZE    = (150, 150)  # kích thước ảnh trả về frontend
JPEG_QUALITY   = 85


def _score_image(img: Image.Image) -> float:
    """
    Tính điểm heuristic cho ảnh: điểm cao hơn = khả năng là ảnh chân dung cao hơn.
    Tỉ lệ ảnh thẻ chuẩn ~3:4 → ratio = 0.75
    """
    w, h = img.size
    if w == 0 or h == 0:
        return -1.0

    ratio = w / h
    if ratio < RATIO_MIN or ratio > RATIO_MAX:
        return -1.0          # loại ảnh ngang hoặc quá dọc
    if w < MIN_W or h < MIN_H:
        return -1.0          # quá nhỏ
    if w > MAX_W or h > MAX_H:
        return -1.0          # quá to (banner)

    # Điểm càng cao nếu ratio gần 0.75 (3:4)
    ideal_ratio = 0.75
    ratio_score = 1.0 - abs(ratio - ideal_ratio) / ideal_ratio

    # Điểm diện tích: ưu tiên ảnh vừa phải (100–400px)
    area  = w * h
    ideal_area = 150 * 200
    area_score = min(area, ideal_area) / ideal_area

    return ratio_score * 0.7 + area_score * 0.3


def _pil_to_base64(img: Image.Image) -> str:
    """Chuyển PIL Image → base64 JPEG string."""
    img = img.convert("RGB")
    img.thumbnail(OUTPUT_SIZE, Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    buf.seek(0)
    return "data:image/jpeg;base64," + base64.b64encode(buf.read()).decode("utf-8")


# ── PDF ─────────────────────────────────────────────────────────────
def extract_avatar_from_pdf(file_bytes: bytes):
    """Trả về base64 string của ảnh tốt nhất, hoặc None nếu không tìm được."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        print(f"[image_extractor] Mở PDF lỗi: {e}")
        return None

    best_img   = None
    best_score = -1.0

    try:
        # Chỉ quét trang đầu (trang 1) — avatar thường ở trang đầu CV
        pages_to_scan = list(doc.pages(0, min(2, len(doc))))
        for page in pages_to_scan:
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                try:
                    raw = doc.extract_image(xref)
                    img_bytes = raw["image"]
                    img = Image.open(io.BytesIO(img_bytes))
                    score = _score_image(img)
                    if score > best_score:
                        best_score = score
                        best_img   = img
                except Exception:
                    continue
    finally:
        doc.close()

    if best_img is None or best_score < 0:
        return None

    try:
        return _pil_to_base64(best_img)
    except Exception as e:
        print(f"[image_extractor] Encode PDF avatar lỗi: {e}")
        return None


# ── DOCX ────────────────────────────────────────────────────────────
def extract_avatar_from_docx(file_bytes: bytes):
    """Trả về base64 string của ảnh tốt nhất, hoặc None nếu không tìm được."""
    try:
        document = docx.Document(io.BytesIO(file_bytes))
    except Exception as e:
        print(f"[image_extractor] Mở DOCX lỗi: {e}")
        return None

    best_img   = None
    best_score = -1.0

    try:
        # Lấy tất cả ảnh từ relationships (bao gồm inline & anchored)
        rels = document.part.rels
        for rel in rels.values():
            if "image" in rel.reltype:
                try:
                    img_bytes = rel.target_part.blob
                    img = Image.open(io.BytesIO(img_bytes))
                    score = _score_image(img)
                    if score > best_score:
                        best_score = score
                        best_img   = img
                except Exception:
                    continue
    except Exception as e:
        print(f"[image_extractor] Duyệt DOCX rels lỗi: {e}")

    if best_img is None or best_score < 0:
        return None

    try:
        return _pil_to_base64(best_img)
    except Exception as e:
        print(f"[image_extractor] Encode DOCX avatar lỗi: {e}")
        return None


# ── Entry point ──────────────────────────────────────────────────────
def extract_avatar(file_bytes: bytes, filename: str):
    """
    Hàm chính — tự nhận diện loại file và trả về avatar base64 hoặc None.
    """
    fname = filename.lower()
    if fname.endswith(".pdf"):
        return extract_avatar_from_pdf(file_bytes)
    elif fname.endswith(".docx"):
        return extract_avatar_from_docx(file_bytes)
    return None
