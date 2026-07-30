import os
import json
import re
import google.generativeai as genai
from openai import OpenAI

try:
    from codebase.rag_manager import retrieve_transcript_context
except ImportError:
    from rag_manager import retrieve_transcript_context

# --- KHU VỰC SĨ AI QUIZ GENERATOR (CÂU HỎI TRẮC NGHIỆM) ---
MOCK_QUIZ_DATABASE = [
    {
        "topic": "Transformers & Attention Mechanism",
        "question": "Hiện tượng Overfitting trong Machine Learning xảy ra khi nào và đâu là giải pháp khắc phục chính xác?",
        "options": {
            "A": "Mô hình quá đơn giản; khắc phục bằng cách giảm bớt số lượng feature.",
            "B": "Mô hình quá phức tạp và ghi nhớ cả nhiễu (noise) dữ liệu train; khắc phục bằng Regularization hoặc Dropout.",
            "C": "Mô hình học quá chậm; khắc phục bằng cách tăng Learning Rate lên gấp đôi.",
            "D": "Dữ liệu huấn luyện quá nhiều; khắc phục bằng cách xóa bớt 50% dữ liệu train."
        },
        "correct_option": "B",
        "explanation": "Overfitting (Quá khớp) xảy ra khi mô hình quá phức tạp, học kỹ cả nhiễu trong tập train (theo bài giảng transcript-06-clean.md [T06-139])."
    },
    {
        "topic": "Đánh giá mô hình & Dữ liệu AI",
        "question": "Trong đánh giá mô hình AI, hiện tượng High Bias (Độ lệch cao) đại diện cho điều gì?",
        "options": {
            "A": "Mô hình bị Underfitting do quá đơn giản, không học được quy luật của dữ liệu.",
            "B": "Mô hình bị Overfitting do học quá sâu vào tập dữ liệu training.",
            "C": "Mô hình có độ chính xác 100% trên cả tập Train và Validation.",
            "D": "Mô hình có số lượng tham số quá lớn làm tràn bộ nhớ GPU."
        },
        "correct_option": "A",
        "explanation": "High Bias (Bias cao) thể hiện sự giả định sai lầm hoặc mô hình quá đơn giản không học đủ đặc trưng (Underfitting)."
    },
    {
        "topic": "Triển khai AI & Ràng buộc hệ thống",
        "question": "Theo bài giảng khóa học, khi nào nên sử dụng RAG (Retrieval-Augmented Generation) thay vì Fine-tuning?",
        "options": {
            "A": "Khi cần thay đổi hoàn toàn kiến thức nền tảng của mô hình ngôn ngữ.",
            "B": "Khi cần chatbot nắm rõ quy tắc/tài liệu nội bộ thường xuyên cập nhật mà không cần huấn luyện lại mô hình.",
            "C": "Khi muốn giảm kích thước file mô hình trên GPU xuống 10 lần.",
            "D": "Khi chỉ có đúng 1 câu hỏi duy nhất trong cơ sở dữ liệu."
        },
        "correct_option": "B",
        "explanation": "RAG giúp truy xuất thông tin tài liệu nội bộ chính xác mà không tốn công sức fine-tune lại mô hình (trích từ transcript-03-clean.md [T03-036])."
    }
]


def generate_quiz_question(
    topic: str = "",
    api_key: str = "",
    gemini_model: str = "",
    openrouter_key: str = "",
    openrouter_model: str = "",
    openrouter_base_url: str = "",
    anthropic_key: str = "",
    anthropic_model: str = "",
    use_mock: bool = False,
    use_rag: bool = True
) -> tuple[dict, str, list]:
    """
    Sinh câu hỏi trắc nghiệm tự động bằng AI kết hợp RAG từ 6 file transcript bài giảng.
    Hỗ trợ kết nối OpenRouter API, Gemini API, Anthropic API hoặc Offline Mock.

    Các thông số model, base_url và API key nếu không truyền trực tiếp sẽ tự động lấy từ file .env:
    - OPENROUTER_API_KEY, OPENROUTER_MODEL & OPENROUTER_BASE_URL (hoặc BASE_URL)
    - GEMINI_API_KEY & GEMINI_MODEL
    - ANTHROPIC_API_KEY & ANTHROPIC_MODEL

    Trả về: (quiz_dict, status_message, rag_chunks)
    """
    topic_clean = topic.strip() if topic else "Kiến thức AI/ML khóa học"

    # Đọc từ biến môi trường (.env) nếu tham số đầu vào rỗng
    # Ưu tiên cấu hình chuẩn OpenAI-compatible: API_KEY, MODEL, BASE_URL
    universal_api_key = os.getenv("API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    universal_model = os.getenv("MODEL", "") or os.getenv("OPENROUTER_MODEL", "") or os.getenv("OPENAI_MODEL", "")
    universal_base_url = os.getenv("BASE_URL", "") or os.getenv("OPENROUTER_BASE_URL", "") or os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

    openrouter_key = openrouter_key or universal_api_key or os.getenv("GEMINI_API_KEY", "")
    openrouter_model_name = openrouter_model.strip() if openrouter_model else (universal_model or os.getenv("GEMINI_MODEL", "google/gemini-2.5-flash"))
    openrouter_base_url = openrouter_base_url.strip() if openrouter_base_url else universal_base_url

    # Tự động loại bỏ /chat/completions nếu người dùng nhập dư trong BASE_URL
    if openrouter_base_url.endswith("/chat/completions"):
        openrouter_base_url = openrouter_base_url[:-17]
    openrouter_base_url = openrouter_base_url.rstrip("/")

    api_key = api_key or os.getenv("GEMINI_API_KEY", "")
    gemini_model_name = gemini_model.strip() if gemini_model else os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    anthropic_key = anthropic_key or os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model_name = anthropic_model.strip() if anthropic_model else os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # 1. Truy xuất RAG Context từ 6 file transcript bài giảng
    rag_chunks = []
    rag_context_str = ""
    if use_rag:
        try:
            rag_chunks = retrieve_transcript_context(topic_clean, top_k=3)
            if rag_chunks:
                context_blocks = []
                for idx, chunk in enumerate(rag_chunks, 1):
                    context_blocks.append(
                        f"--- Đoạn trích {idx} [{chunk['file_name']} | Thẻ: {chunk['tag']} | Phần: {chunk['section']}] ---\n{chunk['content']}"
                    )
                rag_context_str = "\n\n".join(context_blocks)
        except Exception as e:
            print(f"[RAG Retrieval Error]: {e}")

    # Chế độ Offline Mock Generator
    if use_mock or (not api_key and not openrouter_key and not anthropic_key):
        import random
        matched = [q for q in MOCK_QUIZ_DATABASE if topic_clean.lower() in q["topic"].lower()]
        selected = random.choice(matched) if matched else random.choice(MOCK_QUIZ_DATABASE)
        
        quiz_res = dict(selected)
        if topic_clean and topic_clean not in quiz_res["topic"]:
            quiz_res["topic"] = f"{topic_clean} ({quiz_res['topic']})"
        return quiz_res, "💡 Đã sinh câu hỏi RAG thành công bằng AI Mock (Offline Mode).", rag_chunks

    # Xây dựng Prompt cho LLM
    prompt_rag_instruction = f"""Dựa trên các đoạn trích dẫn bài giảng thực tế dưới đây từ khóa học để soạn câu hỏi và phương án:

{rag_context_str}
""" if rag_context_str else "Dựa trên kiến thức bài giảng AI/ML của khóa học."

    prompt = f"""Bạn là một chuyên gia huấn luyện AI/Machine Learning. Hãy tạo 1 câu hỏi trắc nghiệm chất lượng cao về chủ đề: "{topic_clean}".

{prompt_rag_instruction}

Yêu cầu:
- Câu hỏi rõ ràng, có tính thực tiễn hoặc phân biệt các khái niệm trong bài giảng.
- Có 4 phương án lựa chọn A, B, C, D (trong đó chỉ có duy nhất 1 phương án đúng).
- Lời giải thích ngắn gọn, súc tích (1-2 câu), PHẢI trích dẫn rõ mã thẻ bài giảng (ví dụ: [T03-036] trong transcript-03-clean.md).

Trả về CHÍNH XÁC bằng định dạng JSON sau (không chứa markdown nào khác ngoài JSON):
{{
  "topic": "{topic_clean}",
  "question": "Nội dung câu hỏi...",
  "options": {{
    "A": "Nội dung đáp án A",
    "B": "Nội dung đáp án B",
    "C": "Nội dung đáp án C",
    "D": "Nội dung đáp án D"
  }},
  "correct_option": "A" hoặc "B" hoặc "C" hoặc "D",
  "explanation": "Lời giải thích kèm trích dẫn mã đoạn bài giảng..."
}}
"""

    last_err = ""
    # Chế độ 1: OpenRouter / OpenAI API Generator
    if openrouter_key and not use_mock:
        try:
            client = OpenAI(
                base_url=openrouter_base_url,
                api_key=openrouter_key
            )
            response = client.chat.completions.create(
                model=openrouter_model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            raw_text = response.choices[0].message.content.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()
            
            data = json.loads(raw_text)
            if "question" in data and "options" in data and "correct_option" in data:
                return data, f"⚡ Đã sinh câu hỏi RAG thành công qua OpenRouter API ({openrouter_model_name})!", rag_chunks
        except Exception as e:
            last_err = f"OpenRouter: {e}"
            print(f"[OpenRouter API Error]: {e}")

    # Chế độ 2: Gemini API Real Generator (Fallback)
    if api_key and not use_mock:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=gemini_model_name,
                generation_config={"response_mime_type": "application/json", "temperature": 0.3}
            )
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            if "question" in data and "options" in data and "correct_option" in data:
                return data, f"⚡ Đã sinh câu hỏi RAG thành công qua Gemini API ({gemini_model_name})!", rag_chunks
        except Exception as e:
            err_msg = f"Gemini: {e}"
            last_err = f"{last_err} | {err_msg}" if last_err else err_msg
            print(f"[Gemini API Error]: {e}")

    # Chế độ 3: Anthropic API Real Generator (Fallback)
    if anthropic_key and not use_mock:
        try:
            import anthropic
            ant_client = anthropic.Anthropic(api_key=anthropic_key)
            response = ant_client.messages.create(
                model=anthropic_model_name,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            raw_text = response.content[0].text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            data = json.loads(raw_text)
            if "question" in data and "options" in data and "correct_option" in data:
                return data, f"⚡ Đã sinh câu hỏi RAG thành công qua Anthropic API ({anthropic_model_name})!", rag_chunks
        except Exception as e:
            err_msg = f"Anthropic: {e}"
            last_err = f"{last_err} | {err_msg}" if last_err else err_msg
            print(f"[Anthropic API Error]: {e}")

    # Fallback cuối cùng sang Mock Mode
    import random
    fallback = random.choice(MOCK_QUIZ_DATABASE)
    msg = f"⚠️ Lỗi kết nối API ({last_err}), đã chuyển sang AI Mock." if last_err else "⚠️ Lỗi kết nối LLM API, đã tự động chuyển sang AI Mock."
    return fallback, msg, rag_chunks


def clean_citations(text: str) -> str:
    """Loại bỏ các mã thẻ trích dẫn bài giảng như [T02-025], [T06-059] hoặc tên file transcript khỏi văn bản."""
    if not text:
        return ""
    text = re.sub(r'\s*\[T\d{2,}-\d{3,}(?:\s*,\s*T\d{2,}-\d{3,})*\]', '', text)
    text = re.sub(r'\s*\[T[^\]]+\]', '', text)
    text = re.sub(r'\s*\([^)]*transcript[^)]*\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def generate_rag_answer(
    question: str,
    api_key: str = "",
    gemini_model: str = "",
    openrouter_key: str = "",
    openrouter_model: str = "",
    openrouter_base_url: str = "",
    anthropic_key: str = "",
    anthropic_model: str = "",
    use_mock: bool = False
) -> tuple[str, list]:
    """
    Sinh câu trả lời cho câu hỏi của học viên dựa HOÀN TOÀN vào tài liệu bài giảng (RAG).
    Không tự ý sinh ra những câu trả lời ngoài phạm vi bài giảng.
    Trả về: (ai_answer, rag_chunks)
    """
    clean_q = question.strip()
    if not clean_q:
        return "Vui lòng nhập câu hỏi rõ ràng.", []

    # 1. Truy xuất RAG Context từ 6 file transcript
    rag_chunks = []
    rag_context_str = ""
    try:
        rag_chunks = retrieve_transcript_context(clean_q, top_k=4)
        if rag_chunks:
            context_blocks = []
            for idx, chunk in enumerate(rag_chunks, 1):
                context_blocks.append(
                    f"--- Đoạn trích {idx} [{chunk['file_name']} | Mã thẻ: {chunk['tag']} | Phần: {chunk['section']}] ---\n{chunk['content']}"
                )
            rag_context_str = "\n\n".join(context_blocks)
    except Exception as e:
        print(f"[RAG Answer Retrieval Error]: {e}")

    # Đọc từ biến môi trường (.env) nếu tham số rỗng
    universal_api_key = os.getenv("API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    universal_model = os.getenv("MODEL", "") or os.getenv("OPENROUTER_MODEL", "") or os.getenv("OPENAI_MODEL", "")
    universal_base_url = os.getenv("BASE_URL", "") or os.getenv("OPENROUTER_BASE_URL", "") or os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

    openrouter_key = openrouter_key or universal_api_key or os.getenv("GEMINI_API_KEY", "")
    openrouter_model_name = openrouter_model.strip() if openrouter_model else (universal_model or os.getenv("GEMINI_MODEL", "google/gemini-2.5-flash"))
    openrouter_base_url = openrouter_base_url.strip() if openrouter_base_url else universal_base_url

    if openrouter_base_url.endswith("/chat/completions"):
        openrouter_base_url = openrouter_base_url[:-17]
    openrouter_base_url = openrouter_base_url.rstrip("/")

    api_key = api_key or os.getenv("GEMINI_API_KEY", "")
    gemini_model_name = gemini_model.strip() if gemini_model else os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    anthropic_key = anthropic_key or os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model_name = anthropic_model.strip() if anthropic_model else os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # Nếu ở chế độ mock hoặc không có bất kỳ API Key nào
    if use_mock or (not api_key and not openrouter_key and not anthropic_key):
        if rag_chunks:
            summary_content = rag_chunks[0]['content'][:250].replace('\n', ' ')
            res_text = (
                f"Dựa vào bài giảng khóa học:\n"
                f"{summary_content}...\n\n"
                f"*(Lưu ý: Câu trả lời trên được tổng hợp tự động từ bài giảng ở chế độ Offline. Lab Coach sẽ xem xét trước khi hoàn tất gửi cho bạn)*"
            )
            return clean_citations(res_text), rag_chunks
        else:
            return (
                "Nội dung này chưa được đề cập rõ trong các bài giảng đã nạp. Lab Coach sẽ xem xét và giải đáp trực tiếp cho bạn.",
                []
            )

    prompt = f"""Bạn là trợ lý AI học tập của khóa học AI/Machine Learning VLearn. 
Nhiệm vụ của bạn là giải đáp câu hỏi của học viên DỰA HOÀN TOÀN VÀO CÁC ĐOẠN TRÍCH DẪN BÀI GIẢNG DƯỚI ĐÂY.

--- TÀI LIỆU BÀI GIẢNG TRUY XUẤT (RAG CONTEXT) ---
{rag_context_str if rag_context_str else 'Không tìm thấy tài liệu phù hợp trực tiếp.'}

--- CÂU HỎI CỦA HỌC VIÊN ---
"{clean_q}"

QUY TẮC BẮT BUỘC KHÔNG ĐƯỢC VI PHẠM:
1. CHỈ được trả lời dựa trên thông tin có trong tài liệu bài giảng ở trên. KHÔNG tự ý suy đoán, KHÔNG sử dụng kiến thức bên ngoài phạm vi tài liệu.
2. Nếu tài liệu không chứa đủ thông tin để trả lời câu hỏi, hãy ghi rõ: "Nội dung này chưa được đề cập trực tiếp trong tài liệu bài giảng của khóa học. Lab Coach sẽ hỗ trợ thêm cho bạn."
3. Hãy trình bày ngắn gọn, dễ hiểu, súc tích (khoảng 2-4 câu). KHÔNG đính kèm trích dẫn nguồn, KHÔNG ghi các mã thẻ dạng [T01-001], [T02-025], [T...] hay tên file transcript trong câu trả lời.
"""

    # Gọi API
    if openrouter_key and not use_mock:
        try:
            client = OpenAI(base_url=openrouter_base_url, api_key=openrouter_key)
            response = client.chat.completions.create(
                model=openrouter_model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            ans_text = response.choices[0].message.content.strip()
            if ans_text:
                return clean_citations(ans_text), rag_chunks
        except Exception as e:
            print(f"[OpenRouter RAG Answer Error]: {e}")

    if api_key and not use_mock:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name=gemini_model_name)
            response = model.generate_content(prompt)
            ans_text = response.text.strip()
            if ans_text:
                return clean_citations(ans_text), rag_chunks
        except Exception as e:
            print(f"[Gemini RAG Answer Error]: {e}")

    if anthropic_key and not use_mock:
        try:
            import anthropic
            ant_client = anthropic.Anthropic(api_key=anthropic_key)
            response = ant_client.messages.create(
                model=anthropic_model_name,
                max_tokens=1000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            ans_text = response.content[0].text.strip()
            if ans_text:
                return ans_text, rag_chunks
        except Exception as e:
            print(f"[Anthropic RAG Answer Error]: {e}")

    # Fallback khi gọi API thất bại
    if rag_chunks:
        source_tags = ", ".join([f"[{c['tag']}]" for c in rag_chunks[:2]])
        summary_content = rag_chunks[0]['content'][:250].replace('\n', ' ')
        return (
            f"Dựa vào bài giảng khóa học ({source_tags}):\n"
            f"{summary_content}...\n\n"
            f"*(Lưu ý: Câu trả lời được trích xuất từ tài liệu bài giảng. Lab Coach sẽ duyệt lại câu trả lời này)*",
            rag_chunks
        )
    return "Nội dung này chưa được đề cập rõ trong các bài giảng đã nạp. Lab Coach sẽ xem xét và giải đáp trực tiếp cho bạn.", []


