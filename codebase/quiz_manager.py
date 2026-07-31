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

def set_active_quiz(quiz_data: dict, reward_score: int = 1) -> dict:
    """Lưu bài Quiz vừa được phát sóng lên hệ thống."""
    active_quiz = {
        "id": f"quiz_{int(datetime.datetime.now().timestamp())}",
        "topic": quiz_data.get("topic", "AI/ML"),
        "question": quiz_data.get("question", ""),
        "options": quiz_data.get("options", {}),
        "correct_option": quiz_data.get("correct_option", "A").upper().strip(),
        "explanation": quiz_data.get("explanation", ""),
        "reward_score": int(reward_score),
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
    reward = int(active_quiz.get("reward_score", 1))
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

    msg = f"🎉 CHÚC MỪNG **{student_name}** (`{student_code}`) đã trả lời **ĐÚNG & NHANH NHẤT**! Đã cộng **+{reward} điểm** vào bảng điểm!"
    return True, msg, active_quiz


def normalize_text(s: str) -> str:
    import unicodedata
    if not s:
        return ""
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    return s


def get_student_points_summary(student_code: str = None, student_name: str = None) -> dict:
    """
    Tính tổng điểm cộng tích lũy và lấy lịch sử chi tiết cho học viên theo mã HV hoặc họ tên.
    """
    db_records = load_json(POINTS_DB_PATH, default=[])

    code_upper = student_code.strip().upper() if student_code else ""
    norm_name = normalize_text(student_name) if student_name else ""

    matched_records = []
    for r in db_records:
        r_code = r.get("student_id", "").strip().upper()
        r_name = r.get("student_name", "")
        norm_r_name = normalize_text(r_name)

        match_code = bool(code_upper and r_code == code_upper)
        match_name = bool(norm_name and (norm_r_name == norm_name or norm_name in norm_r_name or norm_r_name in norm_name))

        if match_code or match_name:
            matched_records.append(r)

    synced_records = [r for r in matched_records if r.get("status") == "Đã đồng bộ"]
    pending_records = [r for r in matched_records if r.get("status") == "Chờ duyệt"]

    total_synced = sum(r.get("final_score", 0) for r in synced_records)
    total_pending = sum(r.get("final_score", 0) for r in pending_records)

    synced_val = int(total_synced) if total_synced == int(total_synced) else round(total_synced, 1)
    pending_val = int(total_pending) if total_pending == int(total_pending) else round(total_pending, 1)

    display_name = student_name
    if not display_name and matched_records:
        display_name = matched_records[0].get("student_name")
    if not display_name:
        display_name = "Học viên"

    return {
        "student_code": student_code or (matched_records[0].get("student_id") if matched_records else "N/A"),
        "student_name": display_name,
        "total_synced": synced_val,
        "total_pending": pending_val,
        "synced_count": len(synced_records),
        "pending_count": len(pending_records),
        "matched_records": matched_records
    }


def record_student_submission(
    student_name: str,
    student_code: str,
    question: str,
    answer: str,
    student_note: str = ""
) -> dict:
    """
    Ghi nhận lượt phát biểu trên lớp từ Discord (/record) với trạng thái 'Chờ duyệt'.
    """
    db_records = load_json(POINTS_DB_PATH, default=[])

    note_clean = student_note.strip() if student_note else ""
    coach_note_text = f"Xác nhận phát biểu trên lớp từ Discord (/record)"
    if note_clean:
        coach_note_text += f" • Ghi chú: {note_clean}"

    new_record = {
        "id": len(db_records) + 1,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "student_id": student_code,
        "student_name": student_name,
        "question": question.strip(),
        "answer": answer.strip(),
        "student_note": note_clean,
        "coach_note": coach_note_text,
        "suggested_score": 1,
        "final_score": 1,
        "feedback": "Yêu cầu cộng điểm từ Discord /record đang chờ Lab Coach duyệt.",
        "status": "Chờ duyệt",
        "source": "discord_record"
    }
    db_records.append(new_record)
    save_json(POINTS_DB_PATH, db_records)
    return new_record


