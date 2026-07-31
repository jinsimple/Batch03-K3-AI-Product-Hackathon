# SPEC — AI Hỗ Trợ Chấm Điểm Cộng Giơ Tay Trả Lời
**Mini Hackathon AI — Batch 03 | Hướng C (Làn mở)**
**Team:** [Bach, Người 2, Người 3] — 3 người

---

## 0. Tóm tắt 1 dòng

AI gợi ý đúng học viên trong roster khi lab coach gõ tên/mã mơ hồ (gõ tắt, sai dấu, biệt danh) để ghi điểm cộng phát biểu nhanh hơn — điểm số và duyệt cuối cùng luôn do lab coach quyết định.

---

## 1. Problem Statement (Bối cảnh & Pain point)

**Ai:** Học viên tại khóa AI thực chiến VinUni — người trực tiếp chịu ảnh hưởng khi giơ tay phát biểu mà không chắc điểm cộng có được ghi nhận. (Lab coach vẫn là người thao tác nhập điểm trong công cụ, nhưng **trọng tâm evidence và giá trị sản phẩm nghiêng về phía học viên** — xem lý do ở mục 1.1.)

**Đang làm gì:** Giơ tay trả lời câu hỏi trong buổi học, kỳ vọng được ghi nhận điểm cộng minh bạch.

**Vướng đâu:** Quy trình hiện tại tốn thời gian **cả 2 bên**: lab coach tự ghi note tay rồi điền lại vào file Excel, hoặc học viên tự gõ câu hỏi/câu trả lời lên Discord rồi lab coach phải đọc lại và note thủ công vào Excel — dù theo cách nào, dữ liệu cũng phải đi qua bước nhập tay 2 lần (note → Excel), và học viên không có cách nào biết chắc điểm của mình đã được ghi nhận hay chưa cho đến khi tổng kết.

**Hậu quả (phía học viên, có evidence — xem mục 2):**
- 60% học viên khảo sát (9/15) không chắc chắn hoặc nghi ngờ điểm cộng của mình có được ghi đúng
- Cảm giác hụt hẫng, hoang mang khi không chắc có nên hỏi lại lab coach hay không
- Một số phải tự note phòng hờ hoặc chấp nhận rủi ro mất điểm

**Vì sao Hướng C:** Pain point này không nằm trong data pack có sẵn của Hướng A (VLearn)/B (Discord trợ lý). Team chọn tự xây evidence từ đầu (khảo sát) để đổi lấy việc giải quyết đúng pain đã tự trải nghiệm trực tiếp.

### 1.1 Vì sao nghiêng về phía học viên thay vì lab coach

Ban đầu team dự định cân bằng evidence giữa 2 phía (lab coach + học viên). Sau khi **tự phỏng vấn trực tiếp lab coach**, team nhận thấy: nhu cầu phía lab coach không rõ ràng — họ điền/báo cáo dữ liệu điểm cộng chủ yếu **cho bên quản lý xem**, chưa thật sự quan tâm đến trải nghiệm minh bạch phía học viên. Đây là quan sát định tính (1 cuộc phỏng vấn), không phải kết luận thống kê.

Ngược lại, khảo sát định lượng phía học viên (n=15) cho kết quả rõ ràng và vượt ngưỡng yêu cầu (≥50%). Vì vậy team quyết định **dùng học viên làm persona chính để chứng minh giá trị sản phẩm**, trong khi lab coach vẫn giữ vai trò người thao tác (do đặc thù vận hành lớp — chỉ lab coach mới có quyền ghi điểm), nhưng không còn là trọng tâm evidence.

---

## 2. Bằng chứng (Evidence) — R1, 15đ

### 2.1 Phương pháp thu thập
- Khảo sát học viên: Jotform, phát qua Discord khóa + trực tiếp cuối buổi học — **n=15**
- Lab coach: phỏng vấn trực tiếp 1-1 (định tính, không phải khảo sát diện rộng — xem lý do ở mục 1.1)
- Chi tiết bảng câu hỏi: xem `evidence/khao-sat-cham-diem-cong.md`

### 2.2 Số liệu tổng hợp

| Chỉ số | Học viên (n=15) |
|---|---|
| % xác nhận pain point (không chắc/nghi ngờ điểm có ghi đúng) | **60% (9/15)** — đạt ngưỡng ≥50% |
| Phân bố chi tiết | 40% "chắc chắn có ghi đủ" · 40% "không chắc" · 20% "khá chắc nhưng thỉnh thoảng nghi ngờ" |
| Tần suất giơ tay/tuần | 6 người: 0 lần · 6 người: 1-2 lần · 3 người: 3-5 lần |
| Đồng ý dùng thử trước demo | 12/15 |
| Đồng ý cho trích dẫn ẩn danh | 14/15 |

**Cách tính % xác nhận:** gộp 2 lựa chọn "không chắc" và "khá chắc nhưng thỉnh thoảng nghi ngờ" ở câu hỏi về mức độ tin tưởng điểm cộng được ghi nhận đúng.

**Lưu ý về lab coach:** chỉ có 1 phỏng vấn cá nhân — không đủ mẫu để đưa vào bảng số liệu thống kê. Thông tin định tính đã dùng để quyết định hướng đi ở mục 1.1, không dùng làm bằng chứng % ở đây.

### 2.3 Trích dẫn nguyên văn (verbatim, chỉ từ người đã đồng ý trích dẫn)

1. *"Sau 1 lần dơ tay mình không thấy lab coach lấy mã sinh viên của mình. Mình thấy hơi hụt hẫn, nhưng sau đó đã hỏi lại lab coach"*
2. *"Khá hoang mang - không biết là có nên hỏi hay thôi kệ"*
3. *"Thấy cảm giác hơi buồn vì hụt điểm cộng"*
4. *"Chắc do tin nhắn trôi"*
5. *"quy trình chấm điểm lab chưa minh bạch"*

---

## 3. Bảng Impact — R1, R2 (≥3 ứng viên, không dùng chữ "AI")

| Ứng viên | Số người × tần suất | Tốn gì mỗi lần | Chọn/Loại + lý do |
|---|---|---|---|
| Chấm điểm cộng giơ tay | 9/15 học viên xác nhận (60%), tần suất giơ tay phổ biến 1-2 lần/tuần | Hoang mang, hụt hẫng, đôi khi phải tự note phòng hờ | **Chọn** — pain đã tự trải nghiệm, có lát cắt rõ, có evidence n=15 vượt ngưỡng |
| Quy trình điểm danh (quét mã/điền form điểm danh) | 2/15 nhắc đến độc lập ("Phải quét để điền form điểm danh", "Điểm danh") | Thao tác thủ công lặp lại mỗi buổi | **Loại lúc này** — tín hiệu có lặp lại nhưng còn mỏng (chỉ 2 người), ngoài phạm vi lát cắt đã chọn, để dành làm hướng mở rộng sau |
| Tài liệu học tập rải rác (tìm slides, nhiều nguồn thông tin) | 2/15, nhưng nội dung không hoàn toàn giống nhau ("Tìm slides", "Nhiều nguồn thông tin rải rác") | Mất thời gian tìm kiếm | **Loại — tín hiệu yếu**, chưa đủ rõ để khẳng định là 1 pain point thống nhất, cần thêm dữ liệu nếu muốn theo hướng này |

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

## 6. Prototype — Phạm vi thật đã build (R5, 8đ)

> ⚠️ **Đã vượt xa mức "Sketch/Mock 1 lát cắt" ban đầu** — xem cảnh báo ở cuối mục này trước khi nộp.

Prototype gồm **Web Dashboard (Streamlit)** + **Discord Bot** chạy song song, đồng bộ qua file JSON, chia 3 nhóm tính năng:

### 6.1 Quản lý điểm cộng (lõi sản phẩm)
- Lab coach ghi điểm nhanh trên web: chọn học viên (AI gợi ý tên khi gõ mơ hồ) → chọn điểm → duyệt & đồng bộ
- Học viên tự ghi nhận qua lệnh Discord `/record` (câu hỏi + tóm tắt câu trả lời + ghi chú) → vào hàng chờ duyệt trên web, lab coach xem và duyệt/từ chối — **không tự động ghi điểm**, đúng nguyên tắc HITL đã chốt ở mục 4.1
- Tra cứu điểm theo học viên hoặc toàn lớp, trên cả web lẫn Discord (`/total`)

### 6.2 Hỏi đáp học viên hướng nội — AI nháp, người duyệt
- Học viên ngại giơ tay có thể gửi câu hỏi qua Discord `/ask`
- AI tự sinh câu trả lời nháp, **chỉ dựa trên tài liệu bài giảng** (RAG từ transcript, có trích dẫn), báo rõ khi nội dung chưa được dạy tới thay vì bịa
- Lab coach xem, chỉnh sửa nếu cần, bấm gửi → câu trả lời final gửi về Discord riêng (DM) cho học viên

### 6.3 AI Quiz tương tác trên Discord
- AI chọn/sinh câu hỏi trắc nghiệm từ transcript bài giảng theo chủ đề, phát lên Discord
- Học viên trả lời trực tiếp trên Discord, ai đúng & nhanh nhất được cộng điểm tự động (có cơ chế khóa chống cộng trùng)

### ⚠️ Cảnh báo về phạm vi (đọc trước khi nộp)

Mục 8 (nguyên tắc) trong đề bài gốc ghi rõ: *"giữ tối giản tuyệt đối, không thêm tính năng ngoài đúng 1 lát cắt đã định nghĩa"*. Prototype hiện tại có **3 nhóm tính năng, 2 kênh (web+Discord), nhiều luồng AI khác nhau** — đây không còn là 1 lát cắt tối giản nữa. Rủi ro khi chấm:
- BTC có thể hỏi thẳng "1 lát cắt của các bạn là gì" và bị bối rối nếu không chốt trước
- Càng nhiều tính năng AI càng cần càng nhiều eval — hiện chỉ có eval cho phần gợi ý tên (mục 7), **AI Quiz và AI trả lời câu hỏi chưa có eval nào**

**✅ ĐÃ CHỐT: 6.1 là lát cắt trọng tâm cho chấm điểm.** 6.2 và 6.3 là tính năng mở rộng đã build nhưng **nằm ngoài phạm vi trọng tâm** — trình bày với BTC như "đã làm thêm nhưng chưa kiểm thử đầy đủ", không dùng làm câu trả lời chính cho câu hỏi "AI quyết định điều gì" hay "lát cắt của các bạn là gì".

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

🔲 TODO — ~~cần bạn tự chạy thật~~ **ĐÃ CHẠY THẬT**, xem chi tiết bên dưới.

### Kết quả chạy thật — trước và sau khi sửa

**Lần chạy đầu (2026-07-30 14:50):** 5/9 case chạy được, 4 case lỗi kỹ thuật (case 2, 4, 7, 8) — model miễn phí trên OpenRouter đôi khi trả về text lẫn với JSON hoặc trả rỗng, khiến script parse lỗi. Đây không phải lỗi logic AI mà là lỗi hạ tầng (model free kém ổn định về format). File gốc: `eval/results_before_fix.md`.

**Đã sửa `run_eval.py`:**
- Trích JSON linh hoạt hơn (tìm khối `{...}` thay vì bắt buộc toàn bộ response là JSON thuần)
- Tự động thử lại 1 lần khi content rỗng hoặc parse lỗi
- `temperature=0` để giảm dao động ngẫu nhiên
- Tăng `max_tokens` 200 → 400 phòng bị cắt giữa chừng

**Lần chạy sau khi sửa (2026-07-30 14:53):** 9/9 case chạy sạch, không còn lỗi kỹ thuật. File: `eval/results_after_fix.md`.

| # | Lớp | Input | Kết quả | Đánh giá |
|---|---|---|---|---|
| 1 | ① | `Minh Anh` | confident=False, matches=rỗng | ✅ Đạt |
| 2 | ① | `thầy Hiếu vừa nói gì đó` | confident=False, matches=rỗng | ✅ Đạt |
| 3 | ② | `bạn áo xanh ngồi bàn đầu` | confident=False, matches=rỗng | ✅ Đạt |
| 4 | ② | `A` | confident=False, matches=rỗng | ✅ Đạt |
| 5 | ③ | `thêm học viên mới tên Test123` | confident=False, matches=rỗng | ✅ Đạt |
| 6 | ③ | `chọn đại ai đó cũng được` | confident=False, matches=rỗng | ✅ Đạt |
| 7 | ④ | `thanh nam` | confident=False, matches=rỗng | ✅ Đạt (từ chối vì không đủ chắc — 1 trong 2 outcome hợp lệ theo tiêu chí) |
| 8 | ④ | `Linh` | confident=True, matches=[Trần Thu Linh, Ngô Khánh Linh] | ✅ Đạt — liệt kê đúng cả 2 người |
| 9 | ④ | `2A202601741` | confident=False, matches=rỗng | ⚠️ Đạt có điều kiện — an toàn (không gán nhầm) nhưng hơi bảo thủ, lẽ ra nên gợi ý "Nguyễn Văn Nam, độ tin cậy thấp" thay vì im lặng hoàn toàn |

**Tổng kết: 8/9 đạt hoàn toàn, 1/9 đạt nhưng chưa tối ưu.** Nhận xét quan trọng: bộ quy tắc (`SYSTEM_RULES`) hoạt động đúng ở mọi lớp chỗ khó, kể cả khi chạy trên model miễn phí (không phải Claude) — cho thấy prompt design chặt, không phụ thuộc quá nhiều vào sức mạnh model. Điểm cần cải thiện nếu làm tiếp: case 9 gợi ý nên thêm chỉ dẫn để AI chủ động đề xuất ứng viên kèm cảnh báo độ tin cậy thấp, thay vì chỉ có 2 lựa chọn nhị phân "chắc chắn" hoặc "im lặng hoàn toàn".

---

## 8. Validation với User (R6, 8đ)

**12/15 học viên đã đồng ý dùng thử trước demo** — vượt xa yêu cầu ≥3. Team cần liên hệ sớm để chốt tên cụ thể + lịch thử nghiệm trước khi họ quên đã đăng ký.

🔲 TODO — điền tên thật + ngày thử + góp ý sau khi liên hệ xong (lấy từ dữ liệu liên hệ trong Jotform, không đưa số điện thoại/Discord ID vào bản spec commit lên repo — theo đúng mục 10):

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

- [x] Mục 2 (evidence) đã điền số liệu + ≥5 quote thật (n=15 học viên, 60% xác nhận)
- [x] Mục 3 (impact table) đã có đủ 3 ứng viên (2 ứng viên phụ đã "Loại" có lý do rõ ràng)
- [x] Mục 4.3 đã chốt thang điểm (1-3)
- [x] Mục 7 (eval) đã chạy thật 9 case, có bằng chứng trước/sau khi sửa lỗi
- [ ] Mục 8 (validation) — đã có ≥12 người đồng ý, **còn thiếu bước liên hệ lấy tên thật + lịch thử + góp ý**
- [ ] Không còn thông tin định danh cá nhân trong repo (kiểm tra lại trước khi commit)
