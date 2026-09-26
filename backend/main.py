import io
import os
import time
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from services.cv_parser import extract_text
from services.ai_scorer import score_cv
from services.image_extractor import extract_avatar
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Frontend folder nằm cùng cấp với backend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

# ─────────────────────────────────────────────
# GET / — Serve Frontend
# ─────────────────────────────────────────────
@app.route("/", methods=["GET"])
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, "index.html")

# ─────────────────────────────────────────────
# GET /api/health — Health check
# ─────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "version": "3.0", "message": "AI CV Scoring API V3 is running — with Avatar Extraction"})


# ─────────────────────────────────────────────
# POST /score — Batch CV scoring
# ─────────────────────────────────────────────
@app.route("/score", methods=["POST"])
def score():
    # Lấy API Key từ Header V4
    api_key = request.headers.get("X-Gemini-Key", "").strip()
    if not api_key:
        return jsonify({"success": False, "error": "Thiếu Google Gemini API Key. Vui lòng nhập ở giao diện."}), 400

    # Lấy JD
    jd_text = request.form.get("jd_text", "").strip()
    if not jd_text:
        return jsonify({"success": False, "error": "Thiếu Mô tả công việc (JD)."}), 400

    # Lấy danh sách CV files
    cv_files = request.files.getlist("cvs")
    if not cv_files or all(f.filename == "" for f in cv_files):
        return jsonify({"success": False, "error": "Vui lòng tải lên ít nhất 1 file CV."}), 400

    results = []
    errors  = []

    for idx, cv_file in enumerate(cv_files):
        if cv_file.filename == "":
            continue
        try:
            cv_bytes = cv_file.read()
            cv_text  = extract_text(cv_bytes, cv_file.filename)

            if not cv_text or len(cv_text) < 30:
                errors.append({"file": cv_file.filename, "error": "Không đọc được nội dung file."})
                continue

            # ── V3: Trích xuất avatar song song với chấm điểm ──
            avatar_b64 = extract_avatar(cv_bytes, cv_file.filename)

            # ── V4: Gọi hàm score_cv với api_key người dùng ──
            result = score_cv(cv_text, jd_text, api_key)

            if result["success"]:
                result["data"]["_file"]        = cv_file.filename
                result["data"]["avatar_base64"] = avatar_b64  # None nếu không tìm được
                results.append(result["data"])
            else:
                errors.append({"file": cv_file.filename, "error": result["error"]})

        except Exception as e:
            errors.append({"file": cv_file.filename, "error": str(e)})

        # Delay nhỏ giữa các lần gọi API
        if idx < len(cv_files) - 1:
            time.sleep(0.5)

    # Xếp hạng theo tổng điểm giảm dần
    results.sort(key=lambda x: float(x.get("tong_diem", 0)), reverse=True)

    return jsonify({
        "success": True,
        "total": len(results),
        "results": results,
        "errors": errors
    }), 200


# ─────────────────────────────────────────────
# POST /export — Xuất Excel
# ─────────────────────────────────────────────
@app.route("/export", methods=["POST"])
def export_excel():
    data = request.get_json()
    if not data or "results" not in data:
        return jsonify({"success": False, "error": "Không có dữ liệu để xuất."}), 400

    results  = data["results"]
    jd_title = data.get("jd_title", "Vị trí tuyển dụng")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Kết quả chấm điểm CV"

    # ── Màu sắc ──
    COLOR_HEADER    = "1E293B"   # dark navy
    COLOR_ACCENT    = "6366F1"   # indigo
    COLOR_PASS      = "D1FAE5"   # light green
    COLOR_FAIL      = "FEE2E2"   # light red
    COLOR_WARN      = "FEF3C7"   # light yellow
    COLOR_ROW_ALT   = "F8FAFF"

    thin = Side(style="thin", color="CBD5E1")
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)

    # ── Tiêu đề file ──
    ws.merge_cells("A1:L1")
    ws["A1"] = f"BÁO CÁO CHẤM ĐIỂM CV — {jd_title.upper()}"
    ws["A1"].font = Font(name="Calibri", bold=True, size=14, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=COLOR_HEADER)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    ws.merge_cells("A2:L2")
    ws["A2"] = f"Tổng số ứng viên: {len(results)}"
    ws["A2"].font = Font(name="Calibri", italic=True, size=10, color="64748B")
    ws["A2"].alignment = Alignment(horizontal="center")
    ws.row_dimensions[2].height = 18

    # ── Header cột ──
    headers = [
        "STT", "Họ và tên", "Năm sinh", "Số điện thoại",
        "Email", "Địa chỉ", "Vị trí ứng tuyển",
        "Điểm kỹ năng", "Điểm kinh nghiệm", "Điểm học vấn",
        "Tổng điểm", "Đánh giá / Ghi chú"
    ]
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.font = Font(name="Calibri", bold=True, size=10, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=COLOR_ACCENT)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_all
    ws.row_dimensions[3].height = 28

    # ── Data rows ──
    for i, r in enumerate(results, start=1):
        row_num = i + 3
        info    = r.get("thong_tin_ung_vien", {})
        tong    = float(r.get("tong_diem", 0))

        # Đánh giá
        if tong >= 7.5:
            label      = "✅ ĐẠT — Nên phỏng vấn"
            row_color  = COLOR_PASS
        elif tong >= 5:
            label      = "🔶 CÂN NHẮC — Phỏng vấn thêm"
            row_color  = COLOR_WARN
        else:
            label      = "❌ KHÔNG ĐẠT"
            row_color  = COLOR_FAIL

        row_data = [
            i,
            info.get("ho_ten")         or "—",
            info.get("nam_sinh")       or "—",
            info.get("so_dien_thoai")  or "—",
            info.get("email")          or "—",
            info.get("dia_chi")        or "—",
            info.get("vi_tri_ung_tuyen") or jd_title,
            r.get("ky_nang",     {}).get("diem", "—"),
            r.get("kinh_nghiem", {}).get("diem", "—"),
            r.get("hoc_van",     {}).get("diem", "—"),
            tong,
            label
        ]

        fill = PatternFill("solid", fgColor=row_color if i % 2 == 0 else ("FFFFFF" if row_color == COLOR_ROW_ALT else row_color))
        for col, val in enumerate(row_data, start=1):
            cell = ws.cell(row=row_num, column=col, value=val)
            cell.font = Font(name="Calibri", size=10)
            cell.fill = PatternFill("solid", fgColor=row_color)
            cell.alignment = Alignment(horizontal="center" if col in [1,3,8,9,10,11] else "left", vertical="center", wrap_text=True)
            cell.border = border_all
        ws.row_dimensions[row_num].height = 22

    # ── Độ rộng cột ──
    col_widths = [5, 22, 10, 16, 28, 18, 24, 12, 14, 12, 12, 30]
    for i, w in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ── Xuất file ──
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"KetQua_ChamDiemCV_{jd_title.replace(' ', '_')[:30]}.xlsx"
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )


if __name__ == "__main__":
    app.run(port=8000, debug=True)
