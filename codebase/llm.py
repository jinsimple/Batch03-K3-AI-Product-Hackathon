import os
import json
import google.generativeai as genai

# --- KHU VỰC SĨ AI QUIZ GENERATOR (CÂU HỎI TRẮC NGHIỆM) ---
MOCK_QUIZ_DATABASE = [
    {
        "topic": "Overfitting & Underfitting",
        "question": "Hiện tượng Overfitting trong Machine Learning xảy ra khi nào và đâu là giải pháp khắc phục chính xác?",
        "options": {
            "A": "Mô hình quá đơn giản; khắc phục bằng cách giảm bớt số lượng feature.",
            "B": "Mô hình quá phức tạp và ghi nhớ cả nhiễu (noise) dữ liệu train; khắc phục bằng Regularization hoặc Dropout.",
            "C": "Mô hình học quá chậm; khắc phục bằng cách tăng Learning Rate lên gấp đôi.",
            "D": "Dữ liệu huấn luyện quá nhiều; khắc phục bằng cách xóa bớt 50% dữ liệu train."
        },
        "correct_option": "B",
        "explanation": "Overfitting (Quá khớp) xảy ra khi mô hình quá phức tạp, học kỹ cả nhiễu trong tập train. Các kỹ thuật như Regularization (L1/L2), Dropout hoặc Early Stopping giúp khắc phục."
    },
    {
        "topic": "Bias-Variance Tradeoff",
        "question": "Trong đánh giá mô hình AI, hiện tượng High Bias (Độ lệch cao) đại diện cho điều gì?",
        "options": {
            "A": "Mô hình bị Underfitting do quá đơn giản, không học được quy luật của dữ liệu.",
            "B": "Mô hình bị Overfitting do học quá sâu vào tập dữ liệu training.",
            "C": "Mô hình có độ chính xác 100% trên cả tập Train và Validation.",
            "D": "Mô hình có số lượng tham số quá lớn làm tràn bộ nhớ GPU."
        },
        "correct_option": "A",
        "explanation": "High Bias (Bias cao) thể hiện sự giả định sai lầm hoặc mô hình quá đơn giản không học đủ đặc trưng (Underfitting). Trái lại High Variance thể hiện Overfitting."
    },
    {
        "topic": "Prompt Engineering",
        "question": "Kỹ thuật 'Few-shot Prompting' khi làm việc với các Mô hình Ngôn ngữ Lớn (LLM) là gì?",
        "options": {
            "A": "Hỏi AI đúng 1 câu duy nhất không kèm hướng dẫn.",
            "B": "Cung cấp một vài ví dụ minh họa (input-output mẫu) trong prompt để AI bắt chước định dạng.",
            "C": "Chia nhỏ câu hỏi thành 10 prompt liên tiếp cho AI trả lời.",
            "D": "Tắt tính năng temperature của LLM về 0."
        },
        "correct_option": "B",
        "explanation": "Few-shot Prompting là việc đưa thêm một vài cặp ví dụ minh họa vào ngữ cảnh prompt giúp LLM hiểu định dạng và yêu cầu đầu ra chính xác hơn."
    },
    {
        "topic": "Transformers & Attention",
        "question": "Cơ chế 'Self-Attention' trong kiến trúc Transformer có vai trò cốt lõi nào?",
        "options": {
            "A": "Nén kích thước file mô hình xuống 10 lần.",
            "B": "Tính toán mối quan hệ và trọng số liên kết giữa tất cả các từ trong câu cùng một lúc.",
            "C": "Tự động sửa lỗi chính tả trong văn bản đầu vào.",
            "D": "Chỉ chú ý đến từ đầu tiên và từ cuối cùng của đoạn văn."
        },
        "correct_option": "B",
        "explanation": "Self-Attention cho phép mô hình nhìn vào tất cả các vị trí trong chuỗi đầu vào và tính toán mức độ liên quan giữa các từ với nhau, xử lý song song hiệu quả."
    }
]

def generate_quiz_question(topic: str = "", api_key: str = "", use_mock: bool = True) -> tuple[dict, str]:
    """
    Sinh câu hỏi trắc nghiệm tự động bằng AI (hoặc Offline Mock).
    Trả về: (quiz_dict, error_message)
    quiz_dict format: {
        "topic": str,
        "question": str,
        "options": {"A": str, "B": str, "C": str, "D": str},
        "correct_option": str,
        "explanation": str
    }
    """
    topic_clean = topic.strip() if topic else "Kiến thức AI/ML tổng hợp"

    # Chế độ 1: Offline Mock Generator
    if use_mock or not api_key:
        import random
        # Tìm câu hỏi trùng chủ đề nếu có, không thì chọn ngẫu nhiên
        matched = [q for q in MOCK_QUIZ_DATABASE if topic_clean.lower() in q["topic"].lower()]
        selected = random.choice(matched) if matched else random.choice(MOCK_QUIZ_DATABASE)
        
        quiz_res = dict(selected)
        if topic_clean and topic_clean not in quiz_res["topic"]:
            quiz_res["topic"] = f"{topic_clean} ({quiz_res['topic']})"
        return quiz_res, "💡 Đã sinh câu hỏi thành công bằng AI Mock (Offline Mode)."

    # Chế độ 2: Gemini API Real Generator
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json", "temperature": 0.3}
        )
        
        prompt = f"""Bạn là một chuyên gia huấn luyện AI/Machine Learning. Hãy tạo 1 câu hỏi trắc nghiệm chất lượng cao về chủ đề: "{topic_clean}".

Yêu cầu:
- Câu hỏi rõ ràng, có tính thực tiễn hoặc phân biệt các khái niệm hay nhầm lẫn trong AI/ML.
- Có 4 phương án lựa chọn A, B, C, D (trong đó chỉ có duy nhất 1 phương án đúng).
- Lời giải thích ngắn gọn, súc tích (1-2 câu).

Trả về CHÍNH XÁC bằng định dạng JSON sau (không chứa markdown khác):
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
  "explanation": "Giải thích ngắn gọn tại sao phương án đó đúng..."
}}
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        data = json.loads(text)
        if "question" in data and "options" in data and "correct_option" in data:
            return data, "⚡ Đã sinh câu hỏi trắc nghiệm thành công qua Gemini API!"
        else:
            return MOCK_QUIZ_DATABASE[0], "⚠️ Gemini trả về thiếu trường dữ liệu, đã sử dụng câu hỏi mặc định."
    except Exception as e:
        import random
        fallback = random.choice(MOCK_QUIZ_DATABASE)
        return fallback, f"⚠️ Lỗi kết nối Gemini API ({e}), đã tự động chuyển sang AI Mock."

