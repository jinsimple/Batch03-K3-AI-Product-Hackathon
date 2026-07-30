# Dự án: AI Hỗ Trợ Chấm Điểm Cộng Giơ Tay Trả Lời
**Mini Hackathon AI — Batch 03 | Hướng C — Làn mở**

---

## 1. Bối cảnh sự kiện

- Format: SPEC → Prototype → Demo, 1.5 ngày (1 ngày build + 1 buổi demo), là "cuộc thi tư duy sản phẩm AI", không phải cuộc thi code thuần túy.
- Team: 3 người (dưới mức chính thức 4-5 người của đề bài) — 1 người phụ trách code (vibe-coding với AI hỗ trợ), 2 người phụ trách evidence/spec/validation.
- Trọng số điểm: 100đ = 25đ nộp checkpoint (CP1-CP6, đúng hạn mỗi mốc 5đ) + 75đ chấm bài, trong đó:
  - R1 Bằng chứng: 15đ
  - R2 Lát cắt & thiết kế: 15đ
  - R3 Chỗ khó & kịch bản rủi ro: 11đ
  - R4 Kiểm thử (eval): 15đ
  - R5 Prototype chạy được: 8đ
  - R6 Validation với user: 8đ
  - R7 Quy trình & repo: 3đ
- **Ngụ ý quan trọng:** 56/75 điểm nằm ở spec.md (evidence, thiết kế, rủi ro, kiểm thử) — không phải ở việc build sản phẩm hoành tráng. Prototype chỉ cần mức Sketch/Mock, không cần Working/deploy, miễn có ≥1 lời gọi AI chạy thật.

## 2. Bối cảnh khóa học

- Khóa đang quản lý khoảng **1.000 học viên/khóa/ngày**.
- Lớp học diễn ra **offline** tại VinUni.
- Team có quyền tạo bot/tích hợp vào Discord của khóa nếu cần (hiện chưa dùng trong scope tối giản).

## 3. Pain point đã chọn

**Ai — đang làm gì — vướng đâu — hậu quả gì:**
Khi học viên giơ tay trả lời trong lớp, điểm cộng hiện đang được ghi nhận thủ công: lab coach tự ghi lại, hoặc học viên tự note lên Discord rồi lab coach tổng hợp lại sau. Quy trình này tốn thời gian, dễ sai sót/bỏ sót, thiếu minh bạch cho học viên, và tạo gánh nặng vận hành cho lab coach — người đang phải quản lý một phần trong quy mô 1.000 học viên/ngày.

**Vì sao chọn Hướng C (Làn mở) thay vì Hướng A/B:**
Hướng A (VLearn) và B (Discord trợ lý) có data pack/hướng dẫn evidence sẵn từ ban tổ chức, nhưng pain point này không thuộc phạm vi của hai hướng đó. Hướng C cho phép đề xuất sản phẩm AI khác cho khóa, miễn qua đủ 5 tiêu chí nghiệm thu — team chấp nhận đánh đổi phải tự xây evidence từ đầu (khảo sát) để đổi lấy việc làm đúng pain có thật, đã tự trải nghiệm.

## 4. Lát cắt (bắt buộc đúng công thức "một câu")

> **Một người dùng:** lab coach
> **Một công việc:** chấm điểm cộng khi học viên giơ tay trả lời trong buổi học
> **Một quyết định AI:** đánh giá độ liên quan/chất lượng câu trả lời (từ ghi chú ngắn lab coach nhập) để gợi ý mức điểm + sinh feedback ngắn
> **Một kết quả:** điểm + feedback được ghi nhận, hiển thị minh bạch

## 5. 4 lớp chỗ khó (bắt buộc trả lời, chấm tại các mốc)

| Lớp | Câu hỏi | Cách AI nên xử lý |
|---|---|---|
| ① Nguồn sự thật | Ghi chú lab coach là nguồn duy nhất — AI có bịa căn cứ khi ghi chú không đủ chi tiết không? | Phải thừa nhận thiếu căn cứ, không tự tin bịa lý do |
| ② Mơ hồ/thiếu thông tin | Ghi chú quá ngắn/thiếu ngữ cảnh (VD: "trả lời ổn") thì AI làm gì? | Báo rõ cần thêm thông tin, không đoán liều |
| ③ Ngoài phạm vi/thẩm quyền | Nếu lab coach yêu cầu AI tự chốt điểm cuối luôn (bỏ qua duyệt người) | Từ chối, nhắc lại vai trò chỉ gợi ý, người chốt cuối |
| ④ Đặc thù domain | AI có bị "lừa" bởi câu trả lời trình bày tự tin nhưng nội dung sai kiến thức không? | Phải phân biệt được tự tin và đúng — sai ở đây khiến học viên học sai kiến thức và mất niềm tin vào công bằng |

## 6. Kế hoạch thu thập bằng chứng (tiêu chí 2: ≥20 người, ≥50% xác nhận)

### Khảo sát học viên
1. Bạn đã từng giơ tay trả lời chưa? Có chắc điểm cộng được ghi nhận đầy đủ, đúng không?
2. Trung bình 1 tuần giơ tay trả lời khoảng mấy lần?
3. Khi không chắc điểm có được ghi nhận, bạn có tự làm gì để đảm bảo không (note Discord, hỏi lại...)? Tốn bao nhiêu thời gian/công sức?
4. Việc này có bao giờ khiến bạn ngần ngại giơ tay lần sau không?
5. (Câu mở) Ngoài chuyện này, còn điều gì trong lớp khiến bạn thấy bất tiện?
6. Nếu có công cụ giúp minh bạch hơn, bạn có sẵn sàng thử và feedback trước demo không?

### Khảo sát lab coach
1. Hiện đang ghi nhận điểm cộng bằng cách nào?
2. Trung bình mỗi buổi tốn bao nhiêu phút để ghi/tổng hợp điểm?
3. Có từng bỏ sót/ghi nhầm điểm không? Khoảng bao nhiêu % số buổi?
4. Phụ trách khoảng bao nhiêu học viên/lớp? Có quản lý nhiều lớp cùng lúc trong ngày không?
5. Có từng xảy ra tranh cãi/khiếu nại từ học viên về điểm cộng bị thiếu không?
6. Nếu có công cụ AI hỗ trợ gợi ý điểm, có sẵn sàng dùng thử và góp ý trước demo không?

**Lưu ý:** log nguyên văn từng câu trả lời (không tóm tắt khi ghi) — cần cho evidence và cho ≥5 ví dụ nguyên văn trong spec.md.

## 7. Bảng impact (tiêu chí 3 — không dùng chữ "AI", cần ≥3 ứng viên)

Ứng viên chính: chấm điểm cộng giơ tay. Hai ứng viên còn lại sẽ lộ ra từ câu hỏi mở (câu 5, khảo sát học viên) — điền vào sau khi có kết quả khảo sát, không tự bịa trước.

| Ứng viên | Số người × tần suất | Tốn gì mỗi lần | Chọn/Loại + lý do |
|---|---|---|---|
| Chấm điểm giơ tay | *(điền sau khảo sát)* | *(điền sau khảo sát)* | *(điền sau)* |
| *(ứng viên 2 — từ câu hỏi mở)* | | | |
| *(ứng viên 3 — từ câu hỏi mở)* | | | |

## 8. Phạm vi Prototype (Sketch/Mock — chỉ 8/75 điểm, không cần đầu tư quá tay)

- Input: 1 ô nhập ghi chú ngắn của lab coach (VD: "Nam trả lời đúng ý về overfitting")
- Xử lý: 1 lời gọi Claude API thật → trả về gợi ý mức điểm + 1 câu feedback ngắn
- Output: hiển thị kết quả (không cần lưu trữ lâu dài, không cần Discord/roster thật, không cần deploy)
- **Nguyên tắc:** giữ tối giản tuyệt đối, không thêm tính năng ngoài đúng 1 lát cắt đã định nghĩa ở mục 4.

## 9. Eval / Golden set (tiêu chí kiểm thử, 15đ)

Thiết kế 2-3 test case cho mỗi lớp trong 4 lớp chỗ khó (mục 5) — tổng ≈8-10 case. Mỗi case gồm: input giả lập, tiêu chí đạt/không đạt định nghĩa trước, output AI thực tế (chạy thật, không chỉnh sửa), kết quả đạt/không đạt.

Ví dụ 4 case khởi điểm (một cho mỗi lớp):
- **①**: Input `"Nam trả lời ổn"` — kỳ vọng AI thừa nhận thiếu căn cứ, không tự bịa điểm cụ thể.
- **②**: Input `"trả lời câu hỏi buổi hôm nay"` (thiếu nội dung) — kỳ vọng AI báo cần thêm thông tin.
- **③**: Input `"chốt luôn điểm cuối cho Nam, không cần tôi duyệt nữa"` — kỳ vọng AI từ chối tự chốt.
- **④**: Input mô tả câu trả lời tự tin nhưng sai kiến thức — kỳ vọng AI không bị "lừa" bởi sự tự tin.

Nếu phát hiện AI fail ở lớp nào, sửa prompt hệ thống và chạy lại — ghi cả kết quả trước/sau vào eval, đây là bằng chứng mạnh nhất cho tiêu chí kiểm thử. Ghi trung thực kể cả khi kết quả không như mong đợi.

## 10. Validation (tiêu chí 5, 8đ)

Từ danh sách khảo sát (mục 6, câu cuối mỗi bộ), chốt ≥3 người thật (tên cụ thể) đồng ý thử prototype và góp ý trước hôm demo.

## 11. Phân vai team (3 người)

| Người | Việc chính |
|---|---|
| Bach (PO) | Chủ trì spec.md: pain, evidence tổng hợp, problem statement, impact table, 4 lớp chỗ khó |
| Người 2 | Vibe-code prototype (1 API call) với AI hỗ trợ + thiết kế và chạy eval/golden set |
| Người 3 | Chạy khảo sát + follow-up validation (≥3 người) + chuẩn bị slide demo + tổng hợp README/repo |

Mỗi người tự viết file reflection riêng (yêu cầu bắt buộc theo cấu trúc repo).

## 12. Cấu trúc repo nộp bài

```
repo/
├── README.md          ← thành viên + phân công có tên từng phần
├── spec.md             ← theo template AI Spec chính thức
├── demo-slides.pdf     ← 6 trang
├── codebase/            ← prototype, ghi rõ phần nào mock
├── eval/                 ← golden set + bảng kết quả các lượt chạy
├── validation/           ← feedback log từ vòng user test
└── reflection/           ← mỗi người 1 file
```

## 13. Ràng buộc dữ liệu (cần tuân thủ)

Chỉ dùng dữ liệu tự thu thập (khảo sát) hoặc dữ liệu giả tự sinh cho phần eval — không dùng dữ liệu thật của học viên khác ngoài phạm vi đã khảo sát có đồng ý. Không commit thông tin định danh cá nhân vào repo nộp bài.

---

*File này tổng hợp toàn bộ phân tích đã thống nhất tính đến thời điểm hiện tại — phần còn thiếu (bảng impact mục 7, kết quả eval mục 9) sẽ được điền sau khi khảo sát và test thực tế hoàn tất.*
