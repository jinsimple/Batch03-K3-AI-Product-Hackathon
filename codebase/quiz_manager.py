import os
import json
import datetime

# Đường dẫn file dữ liệu
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ACTIVE_QUIZ_PATH = os.path.join(BASE_DIR, "data", "active_quiz.json")
POINTS_DB_PATH = os.path.join(BASE_DIR, "data", "points_db.json")

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

def set_active_quiz(quiz_data: dict, reward_score: float = 1.0) -> dict:
    """Lưu bài Quiz vừa được phát sóng lên hệ thống."""
    active_quiz = {
        "id": f"quiz_{int(datetime.datetime.now().timestamp())}",
        "topic": quiz_data.get("topic", "AI/ML"),
        "question": quiz_data.get("question", ""),
        "options": quiz_data.get("options", {}),
        "correct_option": quiz_data.get("correct_option", "A").upper().strip(),
        "explanation": quiz_data.get("explanation", ""),
        "reward_score": float(reward_score),
        "status": "Đang diễn ra",
        "winner": None,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_json(ACTIVE_QUIZ_PATH, active_quiz)
    return active_quiz

def get_active_quiz() -> dict:
    """Lấy câu hỏi Quiz đang hoạt động."""
    return load_json(ACTIVE_QUIZ_PATH, default={})

def process_quiz_answer(student_name: str, student_code: str, answer_option: str) -> tuple[bool, str, dict]:
    """
    Xử lý câu trả lời của học viên:
    - Trả về: (is_success, message, active_quiz)
    - Nếu đúng & nhanh nhất -> Khóa Quiz, cộng +reward_score vào points_db.json.
    """
    active_quiz = get_active_quiz()
    if not active_quiz or active_quiz.get("status") != "Đang diễn ra":
        winner = active_quiz.get("winner", "chưa xác định") if active_quiz else "chưa có"
        return False, f"⚠️ Câu hỏi Quiz đã kết thúc hoặc chưa được khởi tạo. (Người thắng: {winner})", active_quiz

    clean_ans = answer_option.upper().strip()
    correct_ans = active_quiz.get("correct_option", "").upper().strip()

    if clean_ans != correct_ans:
        return False, f"❌ Rất tiếc, đáp án **{clean_ans}** chưa chính xác!", active_quiz

    # ĐÚNG VÀ NHANH NHẤT!
    reward = active_quiz.get("reward_score", 1.0)
    topic = active_quiz.get("topic", "AI/ML")

    active_quiz["status"] = "Đã kết thúc"
    active_quiz["winner"] = f"{student_name} ({student_code})"
    save_json(ACTIVE_QUIZ_PATH, active_quiz)

    # Ghi nhận cộng điểm vào points_db.json
    db_records = load_json(POINTS_DB_PATH, default=[])
    new_record = {
        "id": len(db_records) + 1,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "student_id": student_code,
        "student_name": student_name,
        "coach_note": f"Thắng AI Quiz Discord (Chủ đề: {topic})",
        "suggested_score": reward,
        "final_score": reward,
        "feedback": f"🎉 Bạn là người trả lời ĐÚNG & NHANH NHẤT bài Quiz '{topic}'. Đã được +{reward} điểm!",
        "status": "Đã đồng bộ"
    }
    db_records.append(new_record)
    save_json(POINTS_DB_PATH, db_records)

    msg = f"🎉 CHÚC MỪNG **{student_name}** (`{student_code}`) đã trả lời **ĐÚNG & NHANH NHẤT**! Đã cộng **+{reward:.1f} điểm** vào bảng điểm!"
    return True, msg, active_quiz
