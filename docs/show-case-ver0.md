# Tài Liệu Showcase - AI Lab Coach Point Grader (Phiên bản Demo v0)

Tài liệu này ghi nhận quá trình xây dựng bản demo nhanh cho hệ thống hỗ trợ chấm điểm cộng thông minh của Lab Coach, giải quyết bài toán: **Lab Coach ghi điểm thủ công -> Học viên không biết mình đã được cộng hay chưa**.

---

## 1. Công Nghệ Sử Dụng (Tech Stack)

Để tối ưu hóa thời gian phát triển trong vòng **1 giờ** và mang lại hiệu quả demo tốt nhất, chúng tôi đã sử dụng các công nghệ sau:

*   **Ngôn ngữ chính:** Python.
*   **Giao diện Web (Frontend & Backend):** **Streamlit**.
    *   *Lý do:* Streamlit cho phép tạo ra giao diện web động, trực quan và tương tác tốt chỉ bằng Python thuần. Phù hợp tuyệt đối cho việc tạo nhanh một "Prototype chạy được" (tiêu chí R5) trong hackathon.
*   **Trí tuệ nhân tạo (AI Engine):** **Gemini API (mô hình `gemini-1.5-flash`)**.
    *   *Lý do:* Khả năng xử lý logic phức tạp, phản hồi nhanh, hỗ trợ định dạng JSON đầu ra trực tiếp (`response_mime_type="application/json"`).
*   **Quản lý chạy dự án:** **`uv`**.
    *   *Lý do:* Sử dụng chuẩn PEP 723 khai báo inline dependency. Người dùng chỉ cần chạy đúng 1 câu lệnh là chạy được app/script kiểm thử mà không cần cài đặt môi trường ảo (virtualenv) hoặc pip install thủ công.
*   **Cơ sở dữ liệu tạm thời (Database):** Lưu trữ cục bộ dạng file JSON (`data/points_db.json`) giúp bảo toàn dữ liệu khi tải lại trang web trong quá trình demo.

---

## 2. Các Chức Năng Đã Triển Khai

Bản demo được chia thành 2 không gian chức năng tương ứng với 2 đối tượng sử dụng:

### A. Giao diện dành cho Lab Coach (Tab 1)
*   **Nhập ghi chú nhanh:** Coach điền MSSV, Họ tên học viên và nội dung ghi chú phát biểu của học viên trong lớp (nhập nháp).
*   **Gửi AI phân tích & gợi ý:** 
    *   AI tự động đọc ghi chú và đề xuất mức điểm phù hợp (+0.5, +1.0 hoặc 0.0) kèm theo nội dung feedback (phản hồi nháp) bằng tiếng Việt.
    *   AI tự động kiểm duyệt qua **4 lớp chỗ khó (Safety Constraints)**:
        1.  *Nguồn sự thật:* Từ chối chấm điểm nếu ghi chú quá chung chung không có bằng chứng phát biểu (VD: `"Nam trả lời ổn"`).
        2.  *Mơ hồ/Thiếu thông tin:* Yêu cầu bổ sung thêm thông tin chi tiết câu trả lời (VD: `"giơ tay trả lời"`).
        3.  *Ngoài thẩm quyền:* Từ chối và nhắc nhở vai trò nếu Coach yêu cầu AI tự quyết định chốt điểm bỏ qua quyền duyệt (VD: `"chốt luôn điểm cho Nam không cần duyệt"`).
        4.  *Đặc thù domain:* Phát hiện và cảnh báo nếu học viên nói tự tin nhưng sai kiến thức kỹ thuật (VD: giải thích sai bias-variance hoặc overfitting).
*   **Quyền kiểm soát của con người (Human-in-the-loop):** Coach có quyền chỉnh sửa lại điểm số và nội dung feedback do AI gợi ý trước khi bấm duyệt.
*   **Hành động ghi nhận:**
    *   *Lưu nháp:* Lưu điểm ở trạng thái `"Chờ duyệt"`.
    *   *Duyệt & Đồng bộ:* Lưu điểm ở trạng thái `"Đã đồng bộ"`.

### B. Cổng tra cứu minh bạch dành cho Học viên (Tab 2)
*   **Giải quyết triệt để pain-point:** Học viên nhập MSSV để tra cứu ngay lập tức.
*   **Thông tin hiển thị:** 
    *   Tổng số điểm cộng tích lũy đã được đồng bộ chính thức.
    *   Số điểm cộng nháp đang ở trạng thái **"Chờ duyệt" (Pending)** (giúp học viên biết chắc chắn phát biểu của mình đã được Coach ghi nhận vào hệ thống mà không cần đợi tổng hợp cuối buổi).
    *   Lịch sử chi tiết: Thời gian phát biểu, nội dung phát biểu, điểm số, và lời nhắn phản hồi (feedback) của Coach/AI.

---

## 3. Hướng Dẫn Chạy Demo

Do dự án đã tích hợp quản lý bằng `uv` nên bạn không cần cấu hình gì thêm. Chỉ cần mở Terminal tại thư mục gốc của dự án và chạy các lệnh sau:

### Bước 1: Thiết lập cấu hình (Tùy chọn)
Mặc định, ứng dụng sẽ chạy ở chế độ **Mock (Offline)** giúp bạn test nhanh các kịch bản của 4 lớp chỗ khó mà không cần API Key.
Nếu muốn kết nối tới Gemini API thật:
1. Bạn có thể chọn chế độ **"Kết nối Gemini API thật"** ngay trên giao diện Sidebar của trang web và dán API Key vào.
2. Hoặc xuất API Key ra môi trường trước khi chạy:
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key-here"
   ```

### Bước 2: Chạy ứng dụng Web tương tác (Streamlit)
Chạy lệnh sau để khởi động Web App:
```bash
uv run codebase/app.py
```
*Hệ thống sẽ tự động khởi tạo server Streamlit và mở trình duyệt tại địa chỉ mặc định: `http://localhost:8501`*

### Bước 3: Chạy bộ kiểm thử tự động (Evaluation Script)
Chạy lệnh sau để đánh giá chất lượng prompt AI đối với bộ Golden Set (bao gồm các ca kiểm thử thuộc 4 lớp chỗ khó):
```bash
uv run eval/run_eval.py
```
*Lệnh này sẽ quét qua file `eval/golden_set.json`, chạy kiểm thử và xuất ra báo cáo kết quả chi tiết dưới dạng Markdown tại file `eval/eval_report.md`.*

### Bước 4: Chia sẻ demo với đồng đội (Sử dụng Pinggy)
Nếu muốn gửi link demo trực tuyến cho các thành viên khác trong nhóm xem và tương tác (giải quyết lỗi Wi-Fi cô lập thiết bị mạng nội bộ), hãy mở một terminal mới và chạy lệnh SSH Tunnel:
```bash
ssh -R 80:localhost:8501 a.pinggy.io
```
*(Nếu Streamlit đang chạy ở cổng khác, ví dụ `8502`, bạn hãy thay đổi số cổng tương ứng: `ssh -R 80:localhost:8502 a.pinggy.io`).*

Sau khi chạy, Pinggy sẽ cung cấp các liên kết công khai (dạng `https://...pinggy.link`) ngay trong terminal. Bạn chỉ cần gửi liên kết này cho đồng đội truy cập từ bất cứ đâu.

