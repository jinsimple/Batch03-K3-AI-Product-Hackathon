# Codebase — Điểm thưởng cho người chăm chỉ

Prototype Streamlit cho luồng: lab coach tìm học viên → chọn điểm cộng → (mock) gửi thông báo Discord.

## Chạy thử local

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # bắt buộc để phần AI fuzzy-suggest hoạt động
streamlit run app.py
```

Không set `ANTHROPIC_API_KEY` vẫn chạy được — chỉ mất phần gợi ý AI khi gõ không khớp trực tiếp.

## Phần nào thật, phần nào mock

| Phần | Trạng thái | Ghi chú |
|---|---|---|
| Tìm kiếm cục bộ theo tên/mã học viên | Thật | Chạy hoàn toàn phía client, không cần AI |
| Gợi ý AI khi không khớp trực tiếp (`ai_fuzzy_suggest`) | **Thật — gọi Claude API** | Model `claude-haiku-4-5-20251001`, chỉ kích hoạt khi tìm cục bộ ra 0 kết quả |
| Danh sách học viên (`ROSTER`) | **Mock** | Dữ liệu giả tự sinh, không phải học viên thật — thay bằng roster thật của lớp khi triển khai |
| Gửi thông báo Discord | **Mock** | Chỉ hiện thông báo thành công trên UI, chưa gọi Discord webhook thật |
| Lưu trữ lâu dài | **Mock** | Dữ liệu chỉ tồn tại trong session Streamlit, mất khi refresh |

## Bước tiếp theo nếu làm thật

1. Thay `ROSTER` bằng danh sách học viên thật (đã xin phép/trong phạm vi đã khảo sát)
2. Thêm tích hợp Discord webhook thật ở chỗ hiện đang mock trong khối `st.success(...)`
3. Thêm lưu trữ bền (DB nhẹ như SQLite hoặc Google Sheet) thay cho `st.session_state`
