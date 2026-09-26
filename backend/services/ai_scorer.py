import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"

def _headers(api_key: str):
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

def _call_gemini(prompt: str, api_key: str) -> dict:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }
    try:
        r = requests.post(GEMINI_API_URL, headers=_headers(api_key), json=payload, timeout=90)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return {"success": True, "data": json.loads(text)}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout khi gọi Gemini AI. Vui lòng thử lại."}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"Lỗi Gemini API ({e.response.status_code}): {e.response.text[:200]}"}
    except json.JSONDecodeError:
        return {"success": False, "error": "AI trả về kết quả không đúng định dạng JSON."}
    except Exception as e:
        return {"success": False, "error": f"Lỗi không xác định: {str(e)}"}


def score_cv(cv_text: str, jd_text: str, api_key: str) -> dict:
    """
    Chấm điểm CV theo JD. Trả về thông tin ứng viên + điểm + đánh giá chuyên sâu.
    """
    prompt = f"""Bạn là một chuyên gia tuyển dụng (HR Expert) giàu kinh nghiệm.
Nhiệm vụ: Phân tích CV ứng viên và so sánh với Mô tả công việc (JD) để đưa ra đánh giá toàn diện, chính xác và khách quan.

## MÔ TẢ CÔNG VIỆC (JD):
---
{jd_text}
---

## CV ỨNG VIÊN (Văn bản trích xuất):
---
{cv_text}
---

## HƯỚNG DẪN CHẤM ĐIỂM (RUBRIC):
- 9-10 điểm: Xuất sắc. Vượt yêu cầu JD, có kinh nghiệm/kỹ năng chuyên sâu, thành tích nổi bật.
- 7-8 điểm: Khá/Tốt. Đáp ứng hầu hết (80-90%) yêu cầu cốt lõi của JD. Có thể làm việc ngay.
- 5-6 điểm: Trung bình/Tiềm năng. Đáp ứng một phần yêu cầu (50-70%), cần đào tạo thêm nhưng có nền tảng.
- Dưới 5 điểm: Không đạt. Thiếu các kỹ năng/kinh nghiệm bắt buộc, background không liên quan.
Lưu ý: Phải dựa trên dẫn chứng CÓ THẬT trong CV, không tự bịa thông tin.

## YÊU CẦU ĐẦU RA:
Trả về MỘT JSON object hợp lệ duy nhất (KHÔNG bọc trong markdown ```json, KHÔNG có text ngoài JSON) với cấu trúc CHÍNH XÁC sau:
{{
  "thong_tin_ung_vien": {{
    "ho_ten": "<Họ và tên đầy đủ của ứng viên, hoặc null nếu không có>",
    "nam_sinh": "<Năm sinh dạng YYYY, hoặc null nếu không có>",
    "so_dien_thoai": "<Số điện thoại, hoặc null nếu không có>",
    "email": "<Email, hoặc null nếu không có>",
    "dia_chi": "<Địa chỉ/thành phố, hoặc null nếu không có>",
    "vi_tri_ung_tuyen": "<Vị trí ứng viên đang ứng tuyển hoặc có kinh nghiệm phù hợp nhất với JD>"
  }},
  "ky_nang": {{
    "diem": <số từ 0 đến 10>,
    "nhan_xet": "<Nhận xét kỹ năng: Liệt kê các kỹ năng ứng viên có khớp với JD, và kỹ năng còn thiếu.>"
  }},
  "kinh_nghiem": {{
    "diem": <số từ 0 đến 10>,
    "nhan_xet": "<Nhận xét kinh nghiệm: Số năm kinh nghiệm, mức độ liên quan của các dự án/công ty cũ so với JD.>"
  }},
  "hoc_van": {{
    "diem": <số từ 0 đến 10>,
    "nhan_xet": "<Nhận xét học vấn: Bằng cấp, chứng chỉ có phù hợp yêu cầu không.>"
  }},
  "tong_diem": <số từ 0 đến 10, đánh giá tổng hợp, có thể là số thập phân như 7.5>,
  "diem_manh": "<Liệt kê 2-3 điểm mạnh nổi bật nhất của ứng viên (ngắn gọn)>",
  "diem_yeu": "<Liệt kê 1-3 điểm yếu, lỗ hổng kinh nghiệm hoặc kỹ năng còn thiếu so với JD>",
  "danh_gia_chi_tiet": "<Đánh giá CHUYÊN SÂU (5-8 câu): Phân tích toàn diện mức độ phù hợp. Dùng dẫn chứng từ CV. Nêu rõ rủi ro nếu tuyển. Lưu ý QUAN TRỌNG: Sử dụng HỌ VÀ TÊN thật của ứng viên (VD: 'Anh Thành', 'Chị Mai', 'Nguyễn Văn A') thay vì gọi là 'Ứng viên'.>",
  "khuyen_nghi": "<Lời khuyên: Nên phỏng vấn ngay / Cân nhắc thêm / Không phù hợp. Giải thích ngắn gọn lý do.>"
}}"""
    result = _call_gemini(prompt, api_key)

    # Thêm delay tránh rate limit khi gọi batch
    time.sleep(0.8)
    return result
