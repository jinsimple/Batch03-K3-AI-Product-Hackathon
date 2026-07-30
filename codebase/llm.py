import os
import json
import google.generativeai as genai
from codebase.prompts import SYSTEM_PROMPT

def run_mock_llm(user_input: str) -> dict:
    """
    Quy tắc giả lập (Mock LLM) để phản hồi giống như AI thật đối với các case mẫu và 4 lớp chỗ khó.
    """
    user_input_lower = user_input.lower()
    
    # 3. NGOÀI PHẠM VI (Out of Scope)
    if "chốt" in user_input_lower or "không cần" in user_input_lower or "bỏ qua duyệt" in user_input_lower:
        return {
            "status": "rejected",
            "suggested_score": 0.0,
            "feedback": "Hệ thống AI không được cấp quyền tự động chốt điểm mà không qua phê duyệt của Lab Coach. Quyền quyết định cuối cùng luôn thuộc về Coach.",
            "explanation": "Từ chối yêu cầu do vi phạm Quy tắc ③ Ngoài phạm vi: Coach yêu cầu AI tự chốt điểm hoặc bỏ qua quyền kiểm soát của con người."
        }
        
    # 4. ĐẶC THÙ DOMAIN (Domain Specifics) - Lỗi sai kiến thức AI/ML
    if "overfitting" in user_input_lower and ("đơn giản" in user_input_lower or "simple" in user_input_lower):
        return {
            "status": "success",
            "suggested_score": 0.0,
            "feedback": "Rất tiếc, định nghĩa của bạn chưa chính xác. Overfitting (quá khớp) xảy ra khi mô hình quá phức tạp (complex) và học cả nhiễu trong dữ liệu training, chứ không phải do mô hình quá đơn giản. Bạn hãy xem lại bài học về Underfitting & Overfitting nhé!",
            "explanation": "Phát hiện sai kiến thức chuyên môn (Quy tắc ④ Đặc thù domain): Định nghĩa sai về hiện tượng Overfitting (cho rằng overfitting là do mô hình đơn giản)."
        }
        
    if "bias" in user_input_lower and ("học quá kỹ" in user_input_lower or "phức tạp" in user_input_lower or "quá phức tạp" in user_input_lower):
        return {
            "status": "success",
            "suggested_score": 0.0,
            "feedback": "Rất tiếc, câu trả lời chưa đúng. Bias cao (độ lệch lớn) đại diện cho việc mô hình quá đơn giản (underfitting) và không học được các đặc trưng của dữ liệu, chứ không phải do mô hình học quá kỹ hay quá phức tạp. Bạn hãy xem lại khái niệm Bias-Variance tradeoff nhé!",
            "explanation": "Phát hiện sai kiến thức chuyên môn (Quy tắc ④ Đặc thù domain): Định nghĩa sai về Bias cao (cho rằng bias cao là do mô hình phức tạp hoặc học quá kỹ)."
        }

    # 1. NGUỒN SỰ THẬT (Source of Truth) - Ghi chú quá chung chung không có căn cứ
    if len(user_input) <= 22 and any(word in user_input_lower for word in ["ổn", "tốt", "được", "ok", "tuyệt"]):
        return {
            "status": "need_more_info",
            "suggested_score": 0.0,
            "feedback": "AI chưa đủ cơ sở để gợi ý điểm cộng. Ghi chú của Coach chỉ nêu đánh giá chung chung mà không mô tả nội dung hay bằng chứng câu trả lời của học viên.",
            "explanation": "Cần thêm thông tin (Quy tắc ① Nguồn sự thật): Ghi chú quá chung chung, không có bằng chứng cụ thể về nội dung phát biểu để AI chấm điểm."
        }

    # 2. MƠ HỒ/THIẾU THÔNG TIN (Ambiguity) - Thiếu hẳn ngữ cảnh hành động
    if len(user_input) <= 40 and any(word in user_input_lower for word in ["trả lời", "giơ tay", "phát biểu"]):
        if not any(keyword in user_input_lower for keyword in ["đúng", "sai", "ý", "về", "giải thích"]):
            return {
                "status": "need_more_info",
                "suggested_score": 0.0,
                "feedback": "Ghi chú thiếu ngữ cảnh. AI cần biết rõ học viên đã phát biểu về chủ đề gì, hoặc trả lời đúng/sai ở điểm cụ thể nào để đưa ra gợi ý điểm phù hợp.",
                "explanation": "Cần thêm thông tin (Quy tắc ② Mơ hồ/Thiếu thông tin): Ghi chú chỉ ghi nhận hành động giơ tay/phát biểu mà thiếu ngữ cảnh nội dung câu hỏi/câu trả lời."
            }

    # Trường hợp chấm điểm bình thường thành công
    suggested = 1.0
    if "khá" in user_input_lower or "chưa đầy đủ" in user_input_lower or "thiếu" in user_input_lower:
        suggested = 0.5
        
    return {
        "status": "success",
        "suggested_score": suggested,
        "feedback": f"Tuyệt vời! Cảm ơn đóng góp của bạn cho buổi học. Điểm cộng của bạn đã được ghi nhận nháp trên hệ thống với nội dung: '{user_input}'.",
        "explanation": f"Chấm điểm thành công. Ghi chú cung cấp đủ thông tin và đúng kiến thức chuyên môn. Gợi ý mức điểm +{suggested}."
    }

def analyze_grading_note(user_input: str, api_key: str = None, use_mock: bool = False) -> dict:
    """
    Hàm phân tích ghi chú từ Lab Coach.
    Nếu use_mock = True hoặc không có API Key, sử dụng run_mock_llm.
    Nếu có API Key và use_mock = False, gọi Gemini API.
    """
    if use_mock or not api_key:
        return run_mock_llm(user_input)
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config={"response_mime_type": "application/json", "temperature": 0.1}
        )
        
        response = model.generate_content(user_input)
        text = response.text.strip()
        
        # Làm sạch markdown nếu LLM trả về dạng ```json ... ```
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        return json.loads(text)
    except Exception as e:
        # Nếu có lỗi gọi API (ví dụ lỗi mạng, sai key), tự động fallback về mock kèm giải thích lỗi
        mock_res = run_mock_llm(user_input)
        mock_res["explanation"] = f"[FALLBACK MOCK do lỗi API: {str(e)}] " + mock_res["explanation"]
        return mock_res

def normalize(s: str) -> str:
    import unicodedata
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    return s

def ai_fuzzy_suggest_llm(query: str, roster: list, gemini_api_key: str = None, anthropic_api_key: str = None, use_mock: bool = False) -> tuple:
    """
    Hàm gợi ý học viên mờ (fuzzy) bằng AI (Claude hoặc Gemini) hoặc Mock offline.
    Trả về: (list_of_matched_students, error_message)
    """
    if use_mock or (not gemini_api_key and not anthropic_api_key):
        # Mock logic based on common abbreviations / typos
        q = normalize(query)
        
        matches = []
        if "mih quan" in q or "m quan" in q or "quan m" in q or "min quan" in q:
            matches.append("Lê Minh Quân")
        if "t linh" in q or "thu linh" in q or "t.linh" in q:
            matches.append("Trần Thu Linh")
        if "thao vi" in q or "t vy" in q or "thao vy" in q or "t.vy" in q:
            matches.append("Đỗ Thảo Vy")
        if "van nam" in q or "v nam" in q or "nam v" in q:
            matches.append("Nguyễn Văn Nam")
        if "bao an" in q or "b an" in q:
            matches.append("Phạm Bảo An")
        if "gia huy" in q or "g huy" in q:
            matches.append("Hoàng Gia Huy")
        if "duc anh" in q or "d anh" in q:
            matches.append("Vũ Đức Anh")
        if "khanh linh" in q or "k linh" in q:
            matches.append("Ngô Khánh Linh")
        if "tan phat" in q or "t phat" in q:
            matches.append("Bùi Tấn Phát")
        if "ngoc mai" in q or "n mai" in q:
            matches.append("Đặng Ngọc Mai")
            
        matched_students = [s for s in roster if s["name"] in matches]
        if matched_students:
            return matched_students, "[Mock Offline] Tìm thấy gợi ý từ AI."
        return [], "[Mock Offline] AI cũng không tìm thấy kết quả phù hợp."

    # Call Anthropic if key exists
    if anthropic_api_key:
        try:
            from anthropic import Anthropic
        except ImportError:
            return None, "Thư viện 'anthropic' chưa được cài đặt."
            
        try:
            client = Anthropic(api_key=anthropic_api_key)
            roster_names = "\n".join(f"- {s['name']} ({s['code']})" for s in roster)
            
            prompt = f"""Bạn là trợ lý tìm tên học viên cho lab coach. Lab coach gõ: "{query}"

Danh sách học viên trong lớp:
{roster_names}

Nhiệm vụ: tìm TỐI ĐA 3 học viên có khả năng khớp với input trên (có thể do gõ tắt,
sai dấu, gọi biệt danh, hoặc nhớ nhầm chính tả).
Nếu không đủ tự tin để gợi ý người nào, trả lời rõ là không tìm thấy — KHÔNG đoán liều.

Trả lời CHỈ bằng JSON, không thêm chữ nào khác, đúng định dạng:
{{"matches": ["Tên chính xác 1", "Tên chính xác 2"], "confident": true}}
"""
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            text = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            if not data.get("confident") or not data.get("matches"):
                return [], None
            matched = [s for s in roster if s["name"] in data["matches"]]
            return matched, None
        except Exception as e:
            return None, f"Lỗi gọi Claude: {e}"

    # Call Gemini if key exists
    if gemini_api_key:
        try:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={"response_mime_type": "application/json", "temperature": 0.1}
            )
            roster_names = "\n".join(f"- {s['name']} ({s['code']})" for s in roster)
            prompt = f"""Bạn là trợ lý tìm tên học viên cho lab coach. Lab coach gõ: "{query}"

Danh sách học viên trong lớp:
{roster_names}

Nhiệm vụ: tìm TỐI ĐA 3 học viên có khả năng khớp với input trên (có thể do gõ tắt,
sai dấu, gọi biệt danh, hoặc nhớ nhầm chính tả).
Nếu không đủ tự tin để gợi ý người nào, trả lời rõ là không tìm thấy — KHÔNG đoán liều.

Trả lời CHỈ bằng JSON, không thêm chữ nào khác, đúng định dạng:
{{"matches": ["Tên chính xác 1", "Tên chính xác 2"], "confident": true}}
"""
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            if not data.get("confident") or not data.get("matches"):
                return [], None
            matched = [s for s in roster if s["name"] in data["matches"]]
            return matched, None
        except Exception as e:
            return None, f"Lỗi gọi Gemini: {e}"

    return [], None


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

