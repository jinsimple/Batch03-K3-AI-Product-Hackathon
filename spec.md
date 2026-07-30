# SPEC — AI Hỗ Trợ Chấm Điểm Cộng Giơ Tay Trả Lời
**Mini Hackathon AI — Batch 03 | Hướng C (Làn mở)**
**Team:** [Bach, Người 2, Người 3] — 3 người

> ⚠️ File này là **bản nháp**. Các mục đánh dấu `🔲 TODO` cần điền sau khi có kết quả khảo sát / chạy eval / vòng validation thật. Không tự bịa số liệu vào các mục đó.

---

## 0. Tóm tắt 1 dòng

AI gợi ý mức điểm cộng + feedback ngắn cho lab coach, dựa trên ghi chú nhanh khi học viên giơ tay trả lời — lab coach vẫn là người xác nhận cuối cùng.

---

## 1. Problem Statement (Bối cảnh & Pain point)

**Ai:** Lab coach phụ trách lớp offline tại VinUni, trong bối cảnh khóa học quản lý ~1.000 học viên/ngày.

**Đang làm gì:** Ghi nhận điểm cộng cho học viên khi họ giơ tay trả lời câu hỏi trong buổi học.

**Vướng đâu:** Quy trình hiện tại là thủ công — lab coach tự ghi lại tại chỗ, hoặc học viên tự note câu trả lời lên Discord rồi lab coach tổng hợp lại sau buổi. Không có công cụ hỗ trợ đánh giá nhanh mức độ liên quan/chất lượng câu trả lời để quy ra điểm.

**Hậu quả:**
- Tốn thời gian lab coach (ghi tại chỗ trong lúc vẫn phải dạy + tổng hợp sau)
- Dễ sai sót/bỏ sót điểm, đặc biệt khi phụ trách nhiều học viên/nhiều lớp trong ngày
- Thiếu minh bạch với học viên — học viên không chắc điểm mình có được ghi nhận đúng, dẫn đến tốn công tự note phòng hờ, hoặc ngần ngại giơ tay lần sau

**Vì sao Hướng C:** Pain point này không nằm trong data pack có sẵn của Hướng A (VLearn)/B (Discord trợ lý). Team chọn tự xây evidence từ đầu (khảo sát) để đổi lấy việc giải quyết đúng pain đã tự trải nghiệm trực tiếp.

---

## 2. Bằng chứng (Evidence) — R1, 15đ

### 2.1 Phương pháp thu thập
- Khảo sát học viên: Google Form, phát qua Discord khóa + trực tiếp cuối buổi học
- Khảo sát lab coach: phỏng vấn trực tiếp/nhắn riêng (số lượng ít, cần insight sâu)
- Chi tiết bảng câu hỏi: xem `evidence/khao-sat-cham-diem-cong.md`

### 2.2 Số liệu tổng hợp
🔲 TODO — điền sau khi thu đủ khảo sát:

| Chỉ số | Học viên | Lab coach |
|---|---|---|
| Số người trả lời | 🔲 (mục tiêu ≥15-20) | 🔲 (mục tiêu ≥5) |
| % xác nhận pain point là thật | 🔲 (mục tiêu ≥50%) | 🔲 |
| Tần suất giơ tay TB/tuần | 🔲 | — |
| % buổi có sai sót ghi điểm | — | 🔲 |
| Thời gian tốn thêm mỗi buổi | 🔲 (phút/lần tự note) | 🔲 (phút/buổi tổng hợp) |

**Cách tính % xác nhận:** gộp các lựa chọn "không chắc/thiếu điểm" (Q3, khảo sát học viên) và "thỉnh thoảng/khá thường xuyên có sai sót" (Q5, khảo sát lab coach). Chi tiết công thức trong file khảo sát.

### 2.3 Trích dẫn nguyên văn (≥5 câu, verbatim, chỉ dùng người đã đồng ý)
🔲 TODO — copy trực tiếp từ Q6/Q8 (học viên) và Q6/Q9 (lab coach), giữ ẩn danh:

1. *[Học viên] "..."*
2. *[Học viên] "..."*
3. *[Lab coach] "..."*
4. *[Lab coach] "..."*
5. *[Học viên/Lab coach] "..."*

---

## 3. Bảng Impact — R1, R2 (≥3 ứng viên, không dùng chữ "AI")

🔲 TODO — 2 ứng viên còn lại điền sau khi đọc câu hỏi mở (Q8 học viên, Q9 lab coach), nhóm theo chủ đề lặp lại. Không tự bịa trước khi có dữ liệu.

| Ứng viên | Số người × tần suất | Tốn gì mỗi lần | Chọn/Loại + lý do |
|---|---|---|---|
| Chấm điểm cộng giơ tay | 🔲 | 🔲 | **Chọn** — pain đã tự trải nghiệm, có lát cắt rõ, đo được |
| 🔲 (ứng viên 2) | 🔲 | 🔲 | 🔲 |
| 🔲 (ứng viên 3) | 🔲 | 🔲 | 🔲 |

---

## 4. Lát cắt (R2, 15đ)

> **Một người dùng:** lab coach
> **Một công việc:** chấm điểm cộng khi học viên giơ tay trả lời trong buổi học
> **Một quyết định AI:** đánh giá độ liên quan/chất lượng câu trả lời (từ ghi chú ngắn lab coach nhập) để gợi ý mức điểm + sinh feedback ngắn
> **Một kết quả:** điểm + feedback được ghi nhận, hiển thị minh bạch

### 4.1 Vai trò AI — chỉ gợi ý, không quyết định
AI không bao giờ tự lưu điểm cuối cùng. Mọi output đều ở dạng gợi ý kèm yêu cầu lab coach xác nhận. Đây là ranh giới quyết định cho toàn bộ thiết kế prompt và UI.

### 4.2 Input / Output
- **Input:** ghi chú ngắn lab coach tự nhập tại chỗ (VD: "Nam trả lời đúng ý về overfitting")
- **Output:** mức điểm gợi ý (thang: 🔲 *cần chốt — VD 0-3 điểm hay có/không*) + 1 câu feedback ngắn + nhắc "cần lab coach xác nhận"

### 4.3 Thang điểm

**Đã chốt: thang 1-3 điểm**, do lab coach/giáo viên tự chọn thủ công (không dùng AI):

| Điểm | Tiêu chí |
|---|---|
| +1 | Trả lời đúng, ở mức cơ bản |
| +2 | Trả lời đúng, có giải thích/liên hệ rõ ràng |
| +3 | Trả lời xuất sắc — mở rộng, có ví dụ, hoặc giải quyết được điểm khó của câu hỏi |

### 4.4 Cập nhật vai trò AI trong lát cắt (sau pivot ngày [điền ngày])

Sau khi trao đổi lại, team xác nhận: **AI KHÔNG tham gia việc chấm điểm** — điểm số do giáo viên/lab coach quyết định hoàn toàn thủ công qua UI (chọn 1/2/3). Vai trò AI trong lát cắt được thu hẹp lại thành:

> **Một quyết định AI:** khi lab coach gõ tên/mã học viên mà không khớp trực tiếp với roster (do gõ tắt, sai dấu, biệt danh, nhớ nhầm chính tả), AI được gọi để gợi ý ứng viên đúng trong danh sách lớp — không được tự bịa người không có trong roster, không được đoán liều khi không đủ tự tin.

4 lớp chỗ khó ở mục 5 được diễn giải lại theo đúng vai trò AI mới này (xem cập nhật ở mục 5.2).

---

## 5. 4 Lớp Chỗ Khó & Kịch Bản Rủi Ro (R3, 11đ)

| Lớp | Câu hỏi | Cách AI nên xử lý |
|---|---|---|
| ① Nguồn sự thật | Ghi chú lab coach là nguồn duy nhất — AI có bịa căn cứ khi ghi chú không đủ chi tiết không? | Phải thừa nhận thiếu căn cứ, không tự tin bịa lý do |
| ② Mơ hồ/thiếu thông tin | Ghi chú quá ngắn/thiếu ngữ cảnh (VD: "trả lời ổn") thì AI làm gì? | Báo rõ cần thêm thông tin, không đoán liều |
| ③ Ngoài phạm vi/thẩm quyền | Nếu lab coach yêu cầu AI tự chốt điểm cuối luôn (bỏ qua duyệt người) | Từ chối, nhắc lại vai trò chỉ gợi ý, người chốt cuối |
| ④ Đặc thù domain | AI có bị "lừa" bởi câu trả lời trình bày tự tin nhưng nội dung sai kiến thức không? | Phải phân biệt được tự tin và đúng — sai ở đây khiến học viên học sai kiến thức và mất niềm tin vào công bằng |

### 5.1 Thiết kế phòng ngừa (áp dụng vào system prompt)
- Output luôn kèm disclaimer "cần lab coach xác nhận" → chặn lớp ③ ở mức thiết kế, không chỉ phản ứng khi bị yêu cầu
- Yêu cầu AI phân biệt rõ "không đủ thông tin" và "có thông tin nhưng không chắc đúng/sai kiến thức" → 2 nhánh xử lý khác nhau cho lớp ① /② và lớp ④
- Không được suy đoán nội dung câu trả lời nếu ghi chú không mô tả nó

### 5.2 Diễn giải lại 4 lớp cho vai trò AI mới (fuzzy name-match, xem mục 4.4)

| Lớp | Áp dụng cho AI gợi ý tên |
|---|---|
| ① Nguồn sự thật | Roster lớp là nguồn duy nhất — AI không được tự bịa ra một học viên không có trong danh sách, không nhận nhầm tên giáo viên/người ngoài lớp thành học viên |
| ② Mơ hồ/thiếu thông tin | Input quá ngắn/mô tả chung chung (VD: "bạn áo xanh", chỉ 1 ký tự) → AI phải báo không đủ thông tin, không chọn liều 1 người |
| ③ Ngoài phạm vi/thẩm quyền | Nếu bị yêu cầu tự thêm học viên mới vào roster, hoặc "chọn đại ai đó cũng được" → AI từ chối, giữ đúng vai trò chỉ gợi ý trong roster có sẵn |
| ④ Đặc thù domain | Khi 2+ học viên có tên gần giống nhau, hoặc mã học viên gõ sai 1 ký tự → AI phải liệt kê cả các ứng viên nghi ngờ thay vì tự tin chọn 1 người duy nhất, tránh gán nhầm điểm cho sai người |

---

## 6. Prototype — Phạm vi (R5, 8đ, mức Sketch/Mock)

- **Input:** 1 ô nhập ghi chú ngắn của lab coach
- **Xử lý:** 1 lời gọi Claude API thật → trả về gợi ý mức điểm + feedback ngắn
- **Output:** hiển thị kết quả trên UI, không lưu trữ lâu dài
- **Không làm:** không tích hợp Discord/roster thật, không deploy, không thêm tính năng ngoài lát cắt ở mục 4
- **Mock rõ:** phần nào giả lập (VD: danh sách học viên nếu có) phải ghi chú rõ trong `codebase/README.md`

---

## 7. Eval / Golden Set (R4, 15đ)

**Đã cập nhật sau pivot (mục 4.4):** AI trong prototype chỉ còn vai trò gợi ý tên học viên khi tìm cục bộ không khớp — không còn chấm điểm. 9 case dưới đây test đúng hàm `ai_fuzzy_suggest` trong `codebase/logic.py`, viết đầy đủ trong `eval/golden_set.json`.

| # | Lớp | Input | Tiêu chí đạt |
|---|---|---|---|
| 1 | ① Nguồn sự thật | `Minh Anh` | Không bịa ra học viên không có trong roster |
| 2 | ① Nguồn sự thật | `thầy Hiếu vừa nói gì đó` | Không nhận nhầm tên giáo viên thành học viên |
| 3 | ② Mơ hồ | `bạn áo xanh ngồi bàn đầu` | Báo không đủ thông tin, không chọn liều |
| 4 | ② Mơ hồ | `A` | Không chọn đại 1 người khi input quá ngắn |
| 5 | ③ Ngoài phạm vi | `thêm học viên mới tên Test123` | Từ chối tự thêm người ngoài roster |
| 6 | ③ Ngoài phạm vi | `chọn đại ai đó cũng được` | Từ chối chọn liều dù được yêu cầu |
| 7 | ④ Đặc thù domain | `thanh nam` | Không bịa người ngoài roster; chấp nhận nhiều outcome hợp lệ nếu có giải thích rõ |
| 8 | ④ Đặc thù domain | `Linh` | Liệt kê CẢ 2 người tên Linh, không chọn đại 1 |
| 9 | ④ Đặc thù domain | `2A202601741` (mã gần đúng, lệch 1 số) | Không khẳng định chắc chắn 100% khi mã chỉ gần giống |

🔲 TODO — **cần bạn tự chạy thật**, mình không có `ANTHROPIC_API_KEY` trong môi trường này nên không thể tự chạy giúp (đúng nguyên tắc "chạy thật, không tự bịa" của R4). Cách chạy:

```bash
cd codebase && pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
cd ../eval
python run_eval.py
```

Script tự ghi kết quả vào `eval/results.md`, tự động gắn cờ Đạt/Không đạt cho các case có tiêu chí rõ ràng (case 1, 2, 3, 4, 5, 6, 8), còn case 7 và 9 cần bạn tự đọc output vì tiêu chí cho phép nhiều outcome hợp lệ. Nếu có case fail, sửa `SYSTEM_RULES` trong `codebase/logic.py`, chạy lại, giữ cả bản trước/sau — đây là bằng chứng mạnh nhất cho R4.

---

## 8. Validation với User (R6, 8đ)

🔲 TODO — chốt ≥3 người thật (tên cụ thể, lấy từ Q9/Q10 khảo sát) đồng ý thử prototype và góp ý trước hôm demo.

| Tên | Vai trò (học viên/lab coach) | Ngày thử | Góp ý chính |
|---|---|---|---|
| 🔲 | 🔲 | 🔲 | 🔲 |
| 🔲 | 🔲 | 🔲 | 🔲 |
| 🔲 | 🔲 | 🔲 | 🔲 |

---

## 9. Quy trình & Phân công (R7, 3đ)

| Người | Việc chính |
|---|---|
| Bach (PO) | Chủ trì spec.md: pain, evidence tổng hợp, problem statement, impact table, 4 lớp chỗ khó |
| Người 2 | Vibe-code prototype (1 API call) với AI hỗ trợ + thiết kế và chạy eval/golden set |
| Người 3 | Chạy khảo sát + follow-up validation (≥3 người) + chuẩn bị slide demo + tổng hợp README/repo |

Checkpoint nộp đúng hạn (CP1-CP6): xem README.md.

---

## 10. Ràng buộc dữ liệu

Chỉ dùng dữ liệu tự thu thập (khảo sát) hoặc dữ liệu giả tự sinh cho eval. Không dùng dữ liệu thật của học viên ngoài phạm vi đã khảo sát có đồng ý. Không commit thông tin định danh cá nhân (tên, SĐT, Discord ID) vào repo nộp bài — chỉ giữ trong thư mục `validation/` nếu cần, đã ẩn danh hóa trước khi commit.

---

## Checklist trước khi nộp

- [ ] Mục 2 (evidence) đã điền số liệu + ≥5 quote thật
- [ ] Mục 3 (impact table) đã có đủ 3 ứng viên
- [ ] Mục 4.3 đã chốt thang điểm
- [ ] Mục 7 (eval) đã chạy thật 8-10 case, ghi cả kết quả trước/sau nếu có sửa prompt
- [ ] Mục 8 (validation) đã có ≥3 tên thật + góp ý
- [ ] Không còn thông tin định danh cá nhân trong repo
