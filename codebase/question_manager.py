import os
import json
import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STUDENT_QUESTIONS_PATH = os.path.join(BASE_DIR, "data", "student_questions.json")

def load_json(file_path: str, default=None):
    if default is None:
        default = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(file_path: str, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def record_student_question(
    student_name: str,
    student_code: str,
    question: str,
    ai_answer: str = "",
    rag_sources: list = None,
    discord_user_id: str = "",
    discord_username: str = ""
) -> dict:
    """
    Ghi nhận câu hỏi mới từ học viên thông qua lệnh /ask trên Discord.
    """
    questions = load_json(STUDENT_QUESTIONS_PATH, default=[])
    
    q_id = f"q_{int(datetime.datetime.now().timestamp())}_{len(questions) + 1}"
    
    new_q = {
        "id": q_id,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "student_id": student_code,
        "student_name": student_name,
        "discord_user_id": str(discord_user_id) if discord_user_id else "",
        "discord_username": str(discord_username) if discord_username else "",
        "question": question.strip(),
        "ai_answer": ai_answer.strip(),
        "rag_sources": rag_sources or [],
        "coach_answer": ai_answer.strip(),  # Mặc định lấy từ câu trả lời gợi ý của AI
        "status": "Chờ trả lời",
        "answered_at": None
    }
    
    questions.append(new_q)
    save_json(STUDENT_QUESTIONS_PATH, questions)
    return new_q

def get_all_questions() -> list:
    """Lấy danh sách tất cả câu hỏi của học viên."""
    return load_json(STUDENT_QUESTIONS_PATH, default=[])

def get_question_by_id(q_id: str) -> dict | None:
    """Tìm câu hỏi theo ID."""
    questions = get_all_questions()
    for q in questions:
        if q.get("id") == q_id:
            return q
    return None

def update_question_answer(q_id: str, coach_answer: str, status: str = "Đã trả lời") -> dict | None:
    """
    Cập nhật câu trả lời đã được Lab Coach chỉnh sửa/chấp nhận.
    """
    questions = get_all_questions()
    updated_q = None
    
    for q in questions:
        if q.get("id") == q_id:
            q["coach_answer"] = coach_answer.strip()
            q["status"] = status
            q["answered_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_q = q
            break
            
    if updated_q:
        save_json(STUDENT_QUESTIONS_PATH, questions)
        
    return updated_q
