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
