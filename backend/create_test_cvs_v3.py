"""
create_test_cvs_v3.py
Tạo 3 CV mẫu mới dạng PDF có nhúng ảnh avatar minh họa để test tính năng V3.
Ảnh avatar được sinh tự động bằng Pillow (không cần ảnh thật).
"""

import os
import io
import fitz          # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = r"e:\THANH NGUYEN\TN-Vibecoding\TN-APP CHAM DIEM CV TU DONG CHO HR\test_cvs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────
# HELPER: Tạo ảnh avatar chân dung minh họa
# ──────────────────────────────────────────────────────
def make_avatar_image(initials: str, bg_color: tuple, size: int = 200) -> bytes:
    """Tạo ảnh avatar hình vuông với chữ cái đầu tên, trả về bytes PNG."""
    img = Image.new("RGB", (size, size), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Vẽ hình tròn nền sáng hơn ở giữa (giả lập khuôn mặt)
    face_r = int(size * 0.38)
    cx, cy = size // 2, int(size * 0.42)
    face_color = tuple(min(c + 60, 255) for c in bg_color)
    draw.ellipse(
        [cx - face_r, cy - face_r, cx + face_r, cy + face_r],
        fill=face_color
    )

    # Vẽ chữ cái
    try:
        font = ImageFont.truetype("arial.ttf", int(size * 0.35))
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2), initials, fill="white", font=font)

    # Vẽ thân người bên dưới (hình bán nguyệt)
    body_color = tuple(max(c - 30, 0) for c in bg_color)
    body_r = int(size * 0.52)
    draw.ellipse(
        [cx - body_r, size - body_r, cx + body_r, size + body_r],
        fill=body_color
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ──────────────────────────────────────────────────────
# HELPER: Tạo file PDF có nội dung văn bản + ảnh nhúng
# ──────────────────────────────────────────────────────
def build_pdf(cv_data: dict, avatar_bytes: bytes, output_path: str):
    """Xây dựng PDF CV với ảnh avatar ở góc trên bên phải."""
    doc  = fitz.open()
    page = doc.new_page(width=595, height=842)   # A4

    # ── Màu sắc ──
    COLOR_DARK   = (0.07, 0.1, 0.18)    # navy
    COLOR_ACCENT = (0.39, 0.40, 0.95)   # indigo
    COLOR_LIGHT  = (0.58, 0.64, 0.73)   # slate

    # ── Header nền ──
    page.draw_rect(fitz.Rect(0, 0, 595, 160), color=None, fill=COLOR_DARK)

    # ── Nhúng ảnh avatar ──
    img_rect = fitz.Rect(450, 20, 560, 130)     # góc phải header (110×110px)
    page.insert_image(img_rect, stream=avatar_bytes, keep_proportion=True)

    # ── Tên ứng viên ──
    page.insert_text(
        fitz.Point(30, 55),
        cv_data["name"],
        fontsize=22, fontname="helv",
        color=(1, 1, 1)
    )

    # ── Vị trí ứng tuyển ──
    page.insert_text(
        fitz.Point(30, 80),
        cv_data["position"],
        fontsize=12, fontname="helv",
        color=COLOR_ACCENT
    )

    # ── Thông tin liên hệ ──
    contact = f"📧 {cv_data['email']}   📞 {cv_data['phone']}   📍 {cv_data['address']}"
    page.insert_text(
        fitz.Point(30, 105),
        contact,
        fontsize=9, fontname="helv",
        color=COLOR_LIGHT
    )

    # Năm sinh
    page.insert_text(
        fitz.Point(30, 120),
        f"Năm sinh: {cv_data['birth_year']}",
        fontsize=9, fontname="helv",
        color=COLOR_LIGHT
    )

    # ── Đường kẻ phân cách ──
    page.draw_line(fitz.Point(30, 170), fitz.Point(565, 170),
                   color=COLOR_ACCENT, width=1.5)

    # ── Sections ──
    y = 185

    def section_title(text, y_pos):
        page.draw_rect(fitz.Rect(30, y_pos - 2, 6, y_pos + 14),
                       color=None, fill=COLOR_ACCENT)
        page.insert_text(fitz.Point(14, y_pos + 12), "▐",
                         fontsize=14, color=COLOR_ACCENT)
        page.insert_text(fitz.Point(30, y_pos + 12), text.upper(),
                         fontsize=11, fontname="helv",
                         color=COLOR_DARK)
        return y_pos + 26

    def add_text(text, y_pos, indent=0, fontsize=9, color=None):
        if color is None:
            color = (0.1, 0.1, 0.2)
        lines = text.split("\n")
        for line in lines:
            # Wrap dài
            while len(line) > 95:
                page.insert_text(fitz.Point(30 + indent, y_pos),
                                 line[:95], fontsize=fontsize, color=color)
                y_pos += fontsize + 3
                line = "  " + line[95:]
            page.insert_text(fitz.Point(30 + indent, y_pos),
                             line, fontsize=fontsize, color=color)
            y_pos += fontsize + 4
        return y_pos

    # MỤC TIÊU NGHỀ NGHIỆP
    y = section_title("Mục tiêu nghề nghiệp", y)
    y = add_text(cv_data["objective"], y, indent=4)
    y += 8

    # KINH NGHIỆM
    y = section_title("Kinh nghiệm làm việc", y)
    for exp in cv_data["experiences"]:
        page.insert_text(fitz.Point(34, y), exp["title"],
                         fontsize=10, fontname="helv",
                         color=COLOR_ACCENT)
        y += 14
        page.insert_text(fitz.Point(34, y), exp["company"],
                         fontsize=9, color=(0.4, 0.4, 0.5))
        y += 12
        for bullet in exp["bullets"]:
            y = add_text(f"• {bullet}", y, indent=8)
        y += 4
    y += 4

    # KỸ NĂNG
    y = section_title("Kỹ năng", y)
    y = add_text(cv_data["skills"], y, indent=4)
    y += 8

    # HỌC VẤN
    y = section_title("Học vấn", y)
    for edu in cv_data["education"]:
        page.insert_text(fitz.Point(34, y), edu["degree"],
                         fontsize=10, fontname="helv",
                         color=(0.1, 0.1, 0.2))
        y += 14
        page.insert_text(fitz.Point(34, y), edu["school"],
                         fontsize=9, color=(0.4, 0.4, 0.5))
        y += 14

    # ── Footer ──
    page.draw_line(fitz.Point(30, 800), fitz.Point(565, 800),
                   color=(0.85, 0.87, 0.9), width=0.5)
    page.insert_text(fitz.Point(30, 820), "CV được tạo tự động để test hệ thống AI CV Scorer V3",
                     fontsize=7, color=(0.7, 0.7, 0.75))

    doc.save(output_path)
    doc.close()
    print(f"  ✅ Đã tạo: {os.path.basename(output_path)}")


# ══════════════════════════════════════════════════════
# CV 4: Phạm Thị Lan Anh — HR Manager xuất sắc
# ══════════════════════════════════════════════════════
avatar4 = make_avatar_image("LA", bg_color=(139, 92, 246))   # tím violet
cv4 = {
    "name":       "PHẠM THỊ LAN ANH",
    "position":   "HR Manager | 6 năm kinh nghiệm",
    "email":      "lananh.pham@hrcorp.vn",
    "phone":      "0978 321 654",
    "address":    "Quận 7, TP.HCM",
    "birth_year": "1993",
    "objective": (
        "HR Manager với 6 năm kinh nghiệm quản lý nhân sự toàn diện tại các tập đoàn đa quốc gia. "
        "Chuyên sâu về tuyển dụng, đào tạo phát triển năng lực và xây dựng văn hóa doanh nghiệp. "
        "Mong muốn đóng góp vào chiến lược phát triển con người bền vững của tổ chức."
    ),
    "experiences": [
        {
            "title":   "2021 – Nay | HR Manager",
            "company": "Tập đoàn FPT Software — TP.HCM",
            "bullets": [
                "Quản lý đội ngũ HR gồm 8 người, phụ trách 1.200+ nhân viên",
                "Thiết kế hệ thống KPI và đánh giá năng lực hàng quý",
                "Giảm tỷ lệ nghỉ việc từ 18% xuống 9% trong 2 năm",
                "Triển khai hệ thống HRIS (SAP SuccessFactors)",
                "Tuyển dụng thành công 300+ vị trí/năm với tỷ lệ phù hợp 92%",
            ]
        },
        {
            "title":   "2018 – 2021 | Senior HR Executive",
            "company": "Unilever Vietnam",
            "bullets": [
                "Phụ trách toàn bộ quy trình tuyển dụng cấp trung và cấp cao",
                "Xây dựng chương trình onboarding giảm thời gian thích nghi 40%",
                "Điều phối chương trình Management Trainee hàng năm",
            ]
        },
    ],
    "skills": (
        "Tuyển dụng & Headhunting, HRIS (SAP, Workday), KPI Design, L&D (Learning & Development), "
        "Compensation & Benefit, Labour Law, Tiếng Anh (IELTS 7.0), Kỹ năng đàm phán, "
        "Phỏng vấn hành vi (BEI), Assessment Center"
    ),
    "education": [
        {"degree": "Thạc sĩ Quản trị Nhân lực — Đại học Kinh tế TP.HCM (2016–2018)", "school": "GPA: 3.7/4.0"},
        {"degree": "Cử nhân Quản trị Kinh doanh — Đại học Ngoại thương (2011–2015)",  "school": "GPA: 3.5/4.0"},
        {"degree": "Chứng chỉ: SHRM-CP, PHRi (HRCI International)", "school": ""},
    ]
}
build_pdf(cv4, avatar4, os.path.join(OUTPUT_DIR, "CV4_PhamThiLanAnh_HR_XUAT_SAC.pdf"))


# ══════════════════════════════════════════════════════
# CV 5: Trần Minh Đức — Sales Executive trung bình
# ══════════════════════════════════════════════════════
avatar5 = make_avatar_image("MĐ", bg_color=(234, 88, 12))    # cam
cv5 = {
    "name":       "TRẦN MINH ĐỨC",
    "position":   "Sales Executive",
    "email":      "minhduc.tran@gmail.com",
    "phone":      "0345 678 901",
    "address":    "Cầu Giấy, Hà Nội",
    "birth_year": "1998",
    "objective": (
        "Nhân viên kinh doanh 2 năm kinh nghiệm trong lĩnh vực bán hàng B2C. "
        "Đang tìm kiếm cơ hội phát triển lên vị trí Sales Executive trong môi trường chuyên nghiệp hơn."
    ),
    "experiences": [
        {
            "title":   "2023 – Nay | Sales Staff",
            "company": "Công ty TNHH Thương mại Minh Phú",
            "bullets": [
                "Bán hàng trực tiếp các sản phẩm điện tử tiêu dùng",
                "Đạt 85-90% chỉ tiêu doanh số hàng tháng",
                "Chăm sóc khoảng 50 khách hàng thân thiết",
                "Hỗ trợ nhập hàng và kiểm tra tồn kho",
            ]
        },
        {
            "title":   "2022 – 2023 | CTV Bán hàng Online",
            "company": "Cộng tác viên Shopee / TikTok Shop",
            "bullets": [
                "Đăng sản phẩm và chạy livestream TikTok Shop",
                "Doanh thu đạt 30-50 triệu/tháng thời điểm tốt nhất",
            ]
        },
    ],
    "skills": (
        "Kỹ năng bán hàng B2C, Chăm sóc khách hàng, Excel cơ bản, "
        "Facebook, Zalo Marketing, TikTok Shop, Thuyết phục và đàm phán đơn giản"
    ),
    "education": [
        {"degree": "Cử nhân Quản trị Kinh doanh — Đại học Thương mại (2016–2020)", "school": "GPA: 2.8/4.0"},
        {"degree": "Chứng chỉ: Kỹ năng bán hàng — Toastmasters HN (2022)", "school": ""},
    ]
}
build_pdf(cv5, avatar5, os.path.join(OUTPUT_DIR, "CV5_TranMinhDuc_Sales_TRUNG_BINH.pdf"))


# ══════════════════════════════════════════════════════
# CV 6: Nguyễn Hoàng Nam — Data Analyst không phù hợp HR
# ══════════════════════════════════════════════════════
avatar6 = make_avatar_image("HN", bg_color=(20, 184, 166))   # teal
cv6 = {
    "name":       "NGUYỄN HOÀNG NAM",
    "position":   "Data Analyst | Python & SQL",
    "email":      "hoangnam.data@outlook.com",
    "phone":      "0911 456 789",
    "address":    "Bình Thạnh, TP.HCM",
    "birth_year": "1996",
    "objective": (
        "Data Analyst 3 năm kinh nghiệm chuyên phân tích dữ liệu lớn, xây dựng dashboard và "
        "mô hình dự báo. Tìm kiếm vị trí Senior Data Analyst hoặc Data Scientist trong lĩnh vực FinTech."
    ),
    "experiences": [
        {
            "title":   "2022 – Nay | Data Analyst",
            "company": "VPBank — Khối Dữ liệu & Phân tích",
            "bullets": [
                "Phân tích hành vi khách hàng từ 5M+ bản ghi/ngày bằng Python & SQL",
                "Xây dựng 15+ dashboard BI trên Power BI và Tableau",
                "Phát triển mô hình churn prediction với độ chính xác 87%",
                "Tự động hóa báo cáo định kỳ bằng Python, tiết kiệm 20h/tuần",
            ]
        },
        {
            "title":   "2021 – 2022 | Junior Data Analyst",
            "company": "Tiki Corporation",
            "bullets": [
                "Phân tích dữ liệu giao dịch e-commerce và hành vi người dùng",
                "Viết SQL queries phức tạp trên BigQuery để tạo báo cáo",
                "Hỗ trợ A/B testing và đo lường hiệu quả chiến dịch",
            ]
        },
    ],
    "skills": (
        "Python (Pandas, NumPy, Scikit-learn, Matplotlib), SQL (MySQL, PostgreSQL, BigQuery), "
        "Power BI, Tableau, Excel (Advanced), Machine Learning cơ bản, "
        "Git, Jupyter Notebook, Apache Spark (cơ bản)"
    ),
    "education": [
        {"degree": "Kỹ sư Toán Tin — Đại học Bách Khoa TP.HCM (2014–2019)", "school": "GPA: 3.4/4.0"},
        {"degree": "Chứng chỉ: Google Data Analytics, IBM Data Science (Coursera)", "school": ""},
        {"degree": "Chứng chỉ: Microsoft Power BI Data Analyst (PL-300)", "school": ""},
    ]
}
build_pdf(cv6, avatar6, os.path.join(OUTPUT_DIR, "CV6_NguyenHoangNam_DataAnalyst_KHONG_PH.pdf"))


print(f"\n🎉 Đã tạo 3 CV mới (PDF có ảnh avatar) vào: {OUTPUT_DIR}")
print("\nDùng JD sau để test (vị trí HR Manager):")
print("""
=== JD TEST V3 ===
VỊ TRÍ: HR MANAGER
Yêu cầu:
- 5+ năm kinh nghiệm Nhân sự tổng hợp
- Có kinh nghiệm quản lý đội nhóm HR
- Thành thạo: tuyển dụng, KPI, L&D, Comp & Ben
- Biết dùng hệ thống HRIS (SAP, Workday)
- Tốt nghiệp Đại học chuyên ngành Nhân sự / QTKD
- Tiếng Anh tốt
""")
