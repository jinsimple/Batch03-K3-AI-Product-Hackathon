# /// script
# dependencies = [
#   "streamlit",
#   "google-generativeai",
#   "anthropic",
#   "python-dotenv",
#   "requests"
# ]
# ///

import os
import json
import datetime
import sys
import streamlit as st
import streamlit.web.cli as stcli
import unicodedata

# Kích hoạt Streamlit CLI nếu chạy trực tiếp bằng python/uv run
if __name__ == "__main__" and not st.runtime.exists():
    sys.argv = ["streamlit", "run", __file__]
    sys.exit(stcli.main())

# Thêm thư mục gốc vào PYTHONPATH để Python nhận diện module codebase
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codebase.llm import generate_quiz_question, clean_citations
from codebase.discord_notifier import (
    send_discord_score_notification,
    get_discord_config,
    send_discord_quiz_notification,
    send_discord_quiz_winner,
    send_discord_dm_or_notification
)
from codebase.quiz_manager import set_active_quiz, get_active_quiz, process_quiz_answer
from codebase.question_manager import get_all_questions, update_question_answer

# Lấy webhook Discord từ biến môi trường
discord_webhook = os.getenv("DISCORD_WEBHOOK_URL", "")



# Đường dẫn lưu trữ database cục bộ
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "points_db.json")
STUDENT_QUESTIONS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "student_questions.json")
ACTIVE_QUIZ_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "active_quiz.json")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Hàm tải dữ liệu
def load_db():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# Hàm lưu dữ liệu
def save_db(data):
    try:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Không thể ghi dữ liệu: {e}")

# Danh sách học viên đề xuất (Roster mới)
ROSTER = [
    {"name": "Nguyễn Văn Nam", "code": "2A202601742"},
    {"name": "Trần Thu Linh", "code": "2A202601756"},
    {"name": "Lê Minh Quân", "code": "2A202601761"},
    {"name": "Phạm Bảo An", "code": "2A202601778"},
    {"name": "Hoàng Gia Huy", "code": "2A202601783"},
    {"name": "Đỗ Thảo Vy", "code": "2A202601790"},
    {"name": "Vũ Đức Anh", "code": "2A202601805"},
    {"name": "Ngô Khánh Linh", "code": "2A202601812"},
    {"name": "Bùi Tấn Phát", "code": "2A202601829"},
    {"name": "Đặng Ngọc Mai", "code": "2A202601834"},
]

def normalize(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    return s



# --- CẤU HÌNH TRANG & CSS NHẬN DIỆN THƯƠNG HIỆU VLEARN (NAVY + ĐỎ) ---
st.set_page_config(page_title="Điểm thưởng cho người chăm chỉ", page_icon="⭐", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp { background: #16233d; }

/* Bỏ và ẩn hoàn toàn thanh sidebar */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
button[data-testid="baseButton-header"],
button[title="Collapse sidebar"],
button[title="Expand sidebar"] {
    display: none !important;
}

/* Thùng chứa chính mở rộng ngang và căn giữa */
.block-container {
    max-width: 1000px;
    background: #ffffff;
    border-radius: 20px;
    padding: 2rem 2.5rem !important;
    margin: 3rem auto !important;
    box-shadow: 0 8px 30px rgba(0,0,0,0.25);
}
.block-container::before {
    content: "";
    display: block;
    height: 4px;
    width: 100%;
    background: linear-gradient(90deg, #dc2626 0%, #dc2626 22%, #e5e7eb 22%);
    border-radius: 4px;
    margin-bottom: 1.5rem;
}

/* Kiểu chữ nội dung chính - giới hạn trong block-container để không làm mất tương phản ngoài main */
.block-container h3, .block-container h4, .block-container h5 { 
    color: #16233d !important; 
    font-weight: 600 !important; 
}
.block-container p, .block-container span, .block-container div, .block-container label { 
    color: #16233d; 
}
.stCaption, [data-testid="stCaptionContainer"] { color: #6b7684 !important; }

/* Ô nhập liệu */
.stTextInput input {
    background: #f8f9fb !important;
    border: 1.5px solid #e2e5ea !important;
    border-radius: 10px !important;
    color: #16233d !important;
}

/* Nút bấm */
.stButton button {
    border-radius: 10px !important;
    border: 1.5px solid #e2e5ea !important;
    background: #ffffff !important;
    color: #16233d !important;
    font-weight: 500 !important;
}
.stButton button:hover { border-color: #1e3a6e !important; color: #1e3a6e !important; }
.stButton button[kind="primary"] { background: #1e3a6e !important; border: none !important; color: #ffffff !important; }
.stButton button[kind="primary"]:hover { background: #16305e !important; color: #ffffff !important; }

/* Đảm bảo chữ bên trong nút bấm kế thừa màu chữ của nút (không bị đè bởi màu chữ của block-container) */
.stButton button p,
.stButton button span,
.stButton button div {
    color: inherit !important;
}

[data-testid="stMetricValue"], .block-container .stRadio label { color: #16233d !important; }
hr { border-color: #eef0f3 !important; }

/* Tùy chỉnh sidebar để có giao diện tối màu, tương phản cao */
[data-testid="stSidebar"] {
    background-color: #0f172a !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] h6,
[data-testid="stSidebar"] p, 
[data-testid="stSidebar"] label, 
[data-testid="stSidebar"] span {
    color: #f8f9fb !important;
}
/* Đảm bảo ô nhập liệu trong sidebar giữ chữ tối trên nền sáng */
[data-testid="stSidebar"] .stTextInput input {
    color: #16233d !important;
    background-color: #f8f9fb !important;
}

/* Giữ chữ tối màu trong hộp thông báo Alert ở màn hình chính (để đọc rõ trên nền cảnh báo sáng màu) */
.block-container [data-testid="stAlert"] p, 
.block-container [data-testid="stAlert"] span, 
.block-container [data-testid="stAlert"] div {
    color: #0f172a !important;
}

/* Tùy chỉnh hộp thông báo Alert trong sidebar: chữ sáng, viền tinh tế trên nền tối */
[data-testid="stSidebar"] [data-testid="stAlert"] {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
}
[data-testid="stSidebar"] [data-testid="stAlert"] p,
[data-testid="stSidebar"] [data-testid="stAlert"] span,
[data-testid="stSidebar"] [data-testid="stAlert"] div {
    color: #f8f9fb !important;
}

/* Custom Toast Notification at bottom-left corner */
.custom-toast {
    position: fixed;
    bottom: 24px;
    left: 24px;
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-left: 4px solid #10b981 !important; /* Green line for success */
    color: #f8f9fb !important;
    padding: 16px 20px !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4), 0 8px 10px -6px rgba(0, 0, 0, 0.4) !important;
    z-index: 999999 !important;
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
    width: 380px !important;
    max-width: calc(100vw - 48px) !important;
    animation: toast-fade-in-out 5s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
}

.custom-toast.draft {
    border-left: 4px solid #f59e0b !important; /* Amber/orange line for draft/pending */
}

.custom-toast .toast-icon {
    font-size: 24px !important;
    flex-shrink: 0 !important;
}

.custom-toast .toast-content {
    display: flex !important;
    flex-direction: column !important;
    gap: 2px !important;
}

.custom-toast .toast-title {
    font-weight: 600 !important;
    font-size: 15px !important;
    color: #f8f9fb !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.2 !important;
}

.custom-toast .toast-body {
    font-size: 13px !important;
    color: #cbd5e1 !important;
    line-height: 1.4 !important;
    margin: 0 !important;
    padding: 0 !important;
}

@keyframes toast-fade-in-out {
    0% {
        transform: translateY(20px) scale(0.95);
        opacity: 0;
    }
    6% {
        transform: translateY(0) scale(1);
        opacity: 1;
    }
    90% {
        transform: translateY(0) scale(1);
        opacity: 1;
    }
    100% {
        transform: translateY(10px) scale(0.95);
        opacity: 0;
        visibility: hidden;
    }
}
</style>
""", unsafe_allow_html=True)

# Khởi tạo các biến session state
if "selected" not in st.session_state:
    st.session_state.selected = None
if "last_note" not in st.session_state:
    st.session_state.last_note = ""
if "toast_message" not in st.session_state:
    st.session_state.toast_message = None
if "last_db_mtime" not in st.session_state:
    st.session_state.last_db_mtime = 0.0
if "auto_sync_enabled" not in st.session_state:
    st.session_state.auto_sync_enabled = True


# --- REAL-TIME DISCORD AUTO-SYNC FRAGMENT ---
@st.fragment(run_every=2)
def check_discord_data_updates():
    if not st.session_state.get("auto_sync_enabled", True):
        return
    
    data_files = [DB_PATH, STUDENT_QUESTIONS_PATH, ACTIVE_QUIZ_PATH]
    latest_mtime = 0.0
    for fpath in data_files:
        if os.path.exists(fpath):
            try:
                m = os.path.getmtime(fpath)
                if m > latest_mtime:
                    latest_mtime = m
            except Exception:
                pass
                
    last_mtime = st.session_state.get("last_db_mtime", 0.0)
    if last_mtime == 0.0:
        st.session_state.last_db_mtime = latest_mtime
    elif latest_mtime > last_mtime:
        st.session_state.last_db_mtime = latest_mtime
        st.rerun()

# Kích hoạt worker kiểm tra cập nhật ngầm từ Discord
check_discord_data_updates()

# --- RENDER TOAST NOTIFICATION IF SET ---
if st.session_state.get("toast_message"):
    toast = st.session_state.toast_message
    toast_class = "custom-toast draft" if toast["type"] == "draft" else "custom-toast"
    toast_icon = "⏳" if toast["type"] == "draft" else "✅"
    
    st.markdown(f"""
    <div class="{toast_class}">
        <span class="toast-icon">{toast_icon}</span>
        <div class="toast-content">
            <div class="toast-title">{toast["title"]}</div>
            <div class="toast-body">{toast["body"]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Xoá khỏi session state để không lặp lại khi tương tác tiếp theo
    st.session_state.toast_message = None




# Tải danh sách điểm hiện tại
db_records = load_db()

# --- BAR THÔNG BÁO & ĐIỀU KHIỂN ĐỒNG BỘ DISCORD ---
sync_col1, sync_col2 = st.columns([3, 1])
with sync_col1:
    if st.session_state.get("auto_sync_enabled", True):
        st.markdown("<div style='margin-bottom: 12px; font-size: 13px; color: #10b981; font-weight: 600; display: flex; align-items: center; gap: 6px;'><span>🟢</span> <span>Real-time Discord Sync: Tự động cập nhật dữ liệu khi học viên tương tác trên Discord</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='margin-bottom: 12px; font-size: 13px; color: #f59e0b; font-weight: 600; display: flex; align-items: center; gap: 6px;'><span>⏸️</span> <span>Real-time Sync đang tạm dừng (Bật lại để tự động tải dữ liệu từ Discord)</span></div>", unsafe_allow_html=True)

with sync_col2:
    btn_c1, btn_c2 = st.columns([1, 1])
    with btn_c1:
        is_syncing = st.toggle("Sync", value=st.session_state.auto_sync_enabled, help="Bật/Tắt tự động đồng bộ từ Discord")
        if is_syncing != st.session_state.auto_sync_enabled:
            st.session_state.auto_sync_enabled = is_syncing
            st.rerun()
    with btn_c2:
        if st.button("🔄", help="Tải lại dữ liệu ngay lập tức", use_container_width=True):
            st.rerun()

# --- MAIN WORKSPACE ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "✍️ Ghi nhận điểm cộng", 
    "📥 Duyệt điểm +", 
    "🔍 Tra cứu", 
    "🎮 AI Quiz (Discord)",
    "❓ Câu hỏi từ học viên"
])


# --- TAB 1: GHI NHẬN ĐIỂM CỘNG ---
with tab1:
    st.markdown("### ⭐ Điểm thưởng cho người chăm chỉ")
    st.caption("VLearn · VinUni AI Thực Chiến — ghi nhận nhanh điểm cộng phát biểu")
    
    # Chế độ chọn nhanh bằng Selectbox tự động gợi ý/lọc
    counts = {s["code"]: 0 for s in ROSTER}
    for r in db_records:
        sid = r.get("student_id")
        if sid and r.get("status") == "Đã đồng bộ":
            counts[sid] = counts.get(sid, 0) + 1
            
    sorted_roster = sorted(ROSTER, key=lambda s: -counts.get(s["code"], 0))
    options = ["-- Chọn học viên --"] + sorted_roster
    
    def format_student(opt):
        if isinstance(opt, str):
            return opt
        name = opt["name"]
        code = opt["code"]
        count = counts.get(code, 0)
        count_str = f" ({count} lần phát biểu)" if count > 0 else ""
        return f"{name} ({code}){count_str} | {normalize(name)}"
        
    # Tìm index hiện tại dựa trên st.session_state.selected
    current_sel = st.session_state.selected
    default_index = 0
    if current_sel:
        for idx, opt in enumerate(options):
            if not isinstance(opt, str) and opt["code"] == current_sel:
                default_index = idx
                break
                
    selected_opt = st.selectbox(
        "Tên hoặc mã học viên (Chọn nhanh)",
        options=options,
        format_func=format_student,
        index=default_index,
        label_visibility="collapsed"
    )
    
    if selected_opt != "-- Chọn học viên --":
        if st.session_state.selected != selected_opt["code"]:
            st.session_state.selected = selected_opt["code"]
            st.session_state.scroll_to_grading = True
            st.session_state.last_note = ""
            st.rerun()
    else:
        if st.session_state.selected is not None:
            st.session_state.selected = None
            st.session_state.last_note = ""
            st.rerun()

    if st.session_state.selected:
        sel = next((s for s in ROSTER if s["code"] == st.session_state.selected), None)
        if sel:
            st.divider()
            # Khởi tạo thẻ neo & kích hoạt JS scroll (dùng HTML thuần túy để tránh lỗi render Markdown)
            scroll_script = ""
            if st.session_state.get("scroll_to_grading"):
                scroll_script = '<img src="x" style="display:none;" onerror="const el = window.parent.document.getElementById(\'grading-section\'); if(el) el.scrollIntoView({behavior: \'smooth\'});">'
                st.session_state.scroll_to_grading = False
                
            st.markdown(
                f'<div id="grading-section"></div>'
                f'<h4 style="color: #16233d; font-weight: 600; margin-top: 0.5rem; margin-bottom: 0.5rem;">'
                f'Chấm điểm cho: <strong>{sel["name"]}</strong> (<code>{sel["code"]}</code>)'
                f'</h4>'
                f'{scroll_script}',
                unsafe_allow_html=True
            )
            
            # 1. Chọn điểm số trực tiếp bằng st.number_input
            points = st.number_input("Số điểm cộng:", min_value=1, max_value=5, value=1, step=1)
            
            # 2. Nhập ghi chú ngắn của Coach (Tùy chọn)
            coach_note = st.text_area(
                "Ghi chú ngắn của Coach (Nội dung trả lời) (Tùy chọn):",
                value=st.session_state.last_note,
                placeholder="Ví dụ: Nam giải thích đúng ý về overfitting là do mô hình quá phức tạp...",
                height=80
            )
            
            # 3. Nhập feedback gửi học viên (Tùy chọn)
            final_feedback = st.text_area(
                "Feedback gửi học viên (Tùy chọn):",
                value="",
                placeholder="Ví dụ: Đã ghi nhận điểm cộng +1 phát biểu.",
                height=80
            )
            
            # 4. Hai nút Lưu nháp và Duyệt & Đồng bộ
            col_b1, col_b2 = st.columns([1, 1])
            with col_b1:
                if st.button("Lưu nháp (Chờ duyệt)", use_container_width=True):
                    note_content = coach_note.strip() if coach_note.strip() else "Chấm điểm nhanh thủ công"
                    new_record = {
                        "id": len(db_records) + 1,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "student_id": sel["code"],
                        "student_name": sel["name"],
                        "coach_note": note_content,
                        "suggested_score": int(points),
                        "final_score": int(points),
                        "feedback": final_feedback,
                        "status": "Chờ duyệt"
                    }
                    db_records.append(new_record)
                    save_db(db_records)
                    
                    st.session_state.toast_message = {
                        "type": "draft",
                        "title": "Đã lưu nháp! ⏳",
                        "body": f"Lưu nháp thành công cho <b>{sel['name']}</b> (+{int(points)} điểm)."
                    }
                    st.session_state.selected = None
                    st.session_state.last_note = ""
                    st.rerun()
                    
            with col_b2:
                if st.button("Duyệt & Đồng bộ ngay ⚡", use_container_width=True, type="primary"):
                    note_content = coach_note.strip() if coach_note.strip() else "Chấm điểm nhanh thủ công"
                    new_record = {
                        "id": len(db_records) + 1,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "student_id": sel["code"],
                        "student_name": sel["name"],
                        "coach_note": note_content,
                        "suggested_score": int(points),
                        "final_score": int(points),
                        "feedback": final_feedback,
                        "status": "Đã đồng bộ"
                    }
                    db_records.append(new_record)
                    save_db(db_records)
                    
                    _, discord_msg = send_discord_score_notification(
                        student_name=sel["name"],
                        student_code=sel["code"],
                        final_score=int(points),
                        coach_note=note_content,
                        feedback=final_feedback,
                        status="Đã đồng bộ",
                        override_webhook=discord_webhook
                    )
                    
                    st.session_state.toast_message = {
                        "type": "sync",
                        "title": "Đã đồng bộ! ⚡",
                        "body": f"Đồng bộ điểm thành công cho <b>{sel['name']}</b> (+{int(points)} điểm).<br><span style='font-size:11px;color:#94a3b8;'>{discord_msg}</span>"
                    }
                    st.session_state.selected = None
                    st.session_state.last_note = ""
                    st.rerun()

                    
            if st.button("Đóng bảng chấm điểm"):
                st.session_state.selected = None
                st.session_state.last_note = ""
                st.rerun()

# --- TAB 2: DUYỆT ĐIỂM + ---
with tab2:
    st.markdown("### 📥 Duyệt điểm +")
    st.caption("Lab Coach đối soát câu hỏi & tóm tắt câu trả lời học viên đã phát biểu trên lớp để cộng điểm tích lũy.")

    pending_list = [r for r in db_records if r.get("status") == "Chờ duyệt"]
    if pending_list:
        for idx, rec in enumerate(pending_list):
            rec_id = rec.get("id")
            st_name = rec.get("student_name", "Học viên")
            st_code = rec.get("student_id", "N/A")
            q_text = rec.get("question", "")
            a_text = rec.get("answer", "")
            s_note = rec.get("student_note", "")
            ts = rec.get("timestamp", "")

            with st.container(border=True):
                col_h1, col_h2 = st.columns([3, 1])
                with col_h1:
                    st.markdown(f"**👤 {st_name}** (`{st_code}`) • ⏱️ *{ts}*")
                with col_h2:
                    st.markdown("<span style='background-color: #d97706; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;'>⏳ Chờ duyệt</span>", unsafe_allow_html=True)

                if q_text:
                    st.markdown(f"**❓ Câu hỏi trên lớp:** {q_text}")
                if a_text:
                    st.markdown(f"**💡 Tóm tắt câu trả lời:** {a_text}")
                if s_note:
                    st.markdown(f"**📝 Ghi chú từ học viên:** {s_note}")

                col_p1, col_p2 = st.columns([1, 2])
                with col_p1:
                    approval_points = st.number_input(
                        f"Số điểm cộng (+):",
                        min_value=1,
                        max_value=5,
                        value=int(rec.get("final_score", 1)),
                        step=1,
                        key=f"approve_pts_{rec_id}_{idx}"
                    )
                with col_p2:
                    approval_feedback = st.text_input(
                        f"Feedback gửi học viên:",
                        value="",
                        key=f"approve_fb_{rec_id}_{idx}"
                    )

                col_act1, col_act2 = st.columns([1, 1])
                with col_act1:
                    if st.button("✅ Duyệt điểm + & Đồng bộ ⚡", key=f"btn_approve_{rec_id}_{idx}", type="primary", use_container_width=True):
                        for r in db_records:
                            if r.get("id") == rec_id:
                                r["status"] = "Đã đồng bộ"
                                r["final_score"] = int(approval_points)
                                r["suggested_score"] = int(approval_points)
                                r["feedback"] = approval_feedback.strip()
                                r["coach_note"] = f"Duyệt điểm + phát biểu: {q_text[:50]}" if q_text else "Duyệt điểm + phát biểu trên lớp"
                                break
                        save_db(db_records)

                        _, discord_msg = send_discord_score_notification(
                            student_name=st_name,
                            student_code=st_code,
                            final_score=int(approval_points),
                            coach_note=f"Xác thực phát biểu trên lớp: {q_text[:60]}" if q_text else "Xác thực phát biểu trên lớp",
                            feedback=approval_feedback,
                            status="Đã đồng bộ",
                            override_webhook=discord_webhook
                        )

                        st.session_state.toast_message = {
                            "type": "sync",
                            "title": "Đã duyệt điểm + thành công! ⚡",
                            "body": f"Đã cộng <b>+{int(approval_points)} điểm</b> cho <b>{st_name}</b>.<br><span style='font-size:11px;color:#94a3b8;'>{discord_msg}</span>"
                        }
                        st.rerun()

                with col_act2:
                    if st.button("❌ Từ chối", key=f"btn_reject_{rec_id}_{idx}", use_container_width=True):
                        db_records = [r for r in db_records if r.get("id") != rec_id]
                        save_db(db_records)
                        st.session_state.toast_message = {
                            "type": "draft",
                            "title": "Đã hủy yêu cầu!",
                            "body": f"Đã từ chối yêu cầu cộng điểm của <b>{st_name}</b>."
                        }
                        st.rerun()
    else:
        st.info("Hiện tại không có yêu cầu điểm cộng nào đang chờ duyệt.")


# --- TAB 3: TRA CỨU HỌC VIÊN ---
with tab3:

    st.markdown("### 🔍 Cổng Tra Cứu")
    st.caption("Tra cứu lịch sử và số lượng điểm cộng phát biểu")
    
    student_options = ["-- Chọn học viên để tra cứu --"] + [f"{s['code']} - {s['name']}" for s in ROSTER]
    selected_search = st.selectbox(
        "Tìm mã số học viên (MSSV) hoặc Họ tên để tra cứu:",
        options=student_options,
        index=0
    )
    
    search_query = ""
    if selected_search != "-- Chọn học viên để tra cứu --":
        parts = selected_search.split(" - ", 1)
        if len(parts) == 2:
            search_query = parts[0]
            
    if search_query:
        filtered_records = [r for r in db_records if r["student_id"].strip().upper() == search_query.strip().upper()]
        
        if filtered_records:
            total_score = int(sum(r["final_score"] for r in filtered_records if r["status"] == "Đã đồng bộ"))
            pending_score = int(sum(r["final_score"] for r in filtered_records if r["status"] == "Chờ duyệt"))
            
            st.markdown(f"#### Lịch sử của: **{filtered_records[0]['student_name']}**")
            
            col_s1, col_s2 = st.columns(2)
            col_s1.metric("Đã đồng bộ ✅", f"+{total_score}")
            col_s2.metric("Chờ duyệt ⏳", f"+{pending_score}")
            
            st.markdown("##### Chi tiết các lượt phát biểu:")
            for record in reversed(filtered_records):
                status_color = "green" if record["status"] == "Đã đồng bộ" else "orange"
                status_badge = f"<span style='background-color: {status_color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;'>{record['status']}</span>"
                
                final_score_val = int(record['final_score']) if record['final_score'] == int(record['final_score']) else record['final_score']
                
                with st.container(border=True):
                    st.markdown(
                        f"""
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <strong>⏱️ {record['timestamp']}</strong>
                            {status_badge}
                        </div>
                        <div style='margin-top: 5px; font-size: 14px;'>
                            <p><strong>Ghi chú:</strong> <i>{record['coach_note']}</i></p>
                            <p><strong>Điểm cộng:</strong> +{final_score_val}</p>
                            <p><strong>Feedback:</strong> {record['feedback']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.warning(f"Chưa có dữ liệu điểm cộng nào cho học viên '{search_query}'.")
    else:
        st.markdown("##### 📋 Lịch sử ghi nhận gần đây (Toàn lớp)")
        if db_records:
            display_records = []
            for r in reversed(db_records[-10:]):
                score_val = int(r['final_score']) if r['final_score'] == int(r['final_score']) else r['final_score']
                display_records.append({
                    "Thời gian": r["timestamp"],
                    "Mã HV": r["student_id"],
                    "Học viên": r["student_name"],
                    "Ghi chú": r["coach_note"],
                    "Điểm": f"+{score_val}",
                    "Feedback": r["feedback"],
                    "Trạng thái": r["status"]
                })
            st.table(display_records)
        else:
            st.info("Hiện tại chưa có bản ghi điểm cộng nào.")

# --- TAB 4: AI QUIZ & TRẮC NGHIỆM DISCORD ---
with tab4:
    st.markdown("### 🎮 AI Quiz & Mini-Game Trắc Nghiệm Discord")
    st.caption("AI tự động tạo câu hỏi trắc nghiệm · Phát đề lên Discord · Tự động cộng +1 điểm cho người trả lời ĐÚNG & NHANH NHẤT!")

    if "current_quiz" not in st.session_state:
        st.session_state.current_quiz = None
    if "quiz_status" not in st.session_state:
        st.session_state.quiz_status = "Chưa phát"
    if "quiz_winner" not in st.session_state:
        st.session_state.quiz_winner = None
    if "quiz_msg" not in st.session_state:
        st.session_state.quiz_msg = ""
    if "quiz_rag_chunks" not in st.session_state:
        st.session_state.quiz_rag_chunks = []

    # Sub-section 1: Sinh câu hỏi với AI
    st.markdown("#### 1. 🤖 Sinh câu hỏi trắc nghiệm AI (RAG 6 Transcripts)")
    
    active_topic = st.selectbox(
        "Chọn chủ đề kiến thức bài giảng (từ 6 Transcripts):",
        [
            "Xác định bài toán kinh doanh cho AI",
            "Chỉ số thành công & Mức tự động hóa",
            "Triển khai AI & Ràng buộc hệ thống",
            "LLM Foundations & Cách LLM hoạt động",
            "Đánh giá mô hình & Dữ liệu AI",
            "Transformers & Attention Mechanism"
        ]
    )

    if st.button("✨ Sinh câu hỏi trắc nghiệm mới 🚀", type="primary"):
        with st.spinner("AI đang truy xuất 6 file transcript & soạn câu hỏi trắc nghiệm..."):
            q_dict, q_msg, rag_chunks = generate_quiz_question(
                topic=active_topic,
                use_mock=False,
                use_rag=True
            )
            st.session_state.current_quiz = q_dict
            st.session_state.quiz_status = "Chưa phát"
            st.session_state.quiz_winner = None
            st.session_state.quiz_msg = q_msg
            st.session_state.quiz_rag_chunks = rag_chunks
            st.rerun()

    if st.session_state.quiz_msg:
        st.caption(st.session_state.quiz_msg)

    # Sub-section 2: Xem trước & Đăng bài Quiz
    if st.session_state.current_quiz:
        st.divider()
        st.markdown("#### 2. 📋 Xem trước & Phát đề lên Discord")
        
        cq = st.session_state.current_quiz
        with st.container(border=True):
            st.markdown(f"**📌 Chủ đề:** `{cq.get('topic', 'AI/ML')}`")
            st.markdown(f"**❓ Câu hỏi:** {cq.get('question')}")
            st.markdown("**Các phương án lựa chọn:**")
            opts = cq.get("options", {})
            for key in ["A", "B", "C", "D"]:
                if key in opts:
                    is_correct_tag = " ✅ *(Đáp án đúng)*" if key == cq.get("correct_option") else ""
                    st.write(f"- **{key}.** {opts[key]}{is_correct_tag}")
            st.caption(f"💡 *Giải thích:* {cq.get('explanation')}")

        if st.session_state.get("quiz_rag_chunks"):
            with st.expander("📚 xem các đoạn trích dẫn bài giảng RAG đã trích xuất (6 Transcripts)", expanded=False):
                for idx, chunk in enumerate(st.session_state.quiz_rag_chunks, 1):
                    st.markdown(f"**Đoạn {idx}: [{chunk['file_name']}] — Mã thẻ: `{chunk['tag']}` — Phần: *{chunk['section']}***")
                    st.info(chunk['content'])

        reward_points = st.number_input("Điểm phần thưởng cho lượt trả lời đúng nhanh nhất:", min_value=1, max_value=5, value=1, step=1)

        col_dis1, col_dis2 = st.columns([1, 1])
        with col_dis1:
            if st.button("🚀 Gửi Quiz lên Discord Channel", type="primary", use_container_width=True):
                # Lưu câu hỏi hoạt động vào quiz_manager để Discord Bot Listener nhận diện được
                set_active_quiz(cq, reward_score=reward_points)

                _, d_msg = send_discord_quiz_notification(
                    quiz_data=cq,
                    reward_score=reward_points,
                    override_webhook=discord_webhook
                )
                st.session_state.quiz_status = "Đang diễn ra"
                st.success(f"Đã phát đề lên Discord! {d_msg}")
                st.rerun()

        with col_dis2:
            if st.button("🔄 Đổi câu hỏi khác", use_container_width=True):
                with st.spinner("AI đang truy xuất transcript & sinh câu hỏi mới..."):
                    q_dict, q_msg, rag_chunks = generate_quiz_question(
                        topic=active_topic,
                        use_mock=False,
                        use_rag=True
                    )
                    st.session_state.current_quiz = q_dict
                    st.session_state.quiz_status = "Chưa phát"
                    st.session_state.quiz_winner = None
                    st.session_state.quiz_msg = q_msg
                    st.session_state.quiz_rag_chunks = rag_chunks
                    st.rerun()

    # Đồng bộ trạng thái mới nhất từ active_quiz.json (đối với trường hợp Discord Bot tự động xử lý)
    latest_active = get_active_quiz()
    if latest_active and latest_active.get("status") == "Đã kết thúc" and latest_active.get("winner"):
        st.session_state.quiz_status = "Đã kết thúc"
        st.session_state.quiz_winner = latest_active.get("winner")

    # Sub-section 3: Giả lập / Xử lý câu trả lời Real-time
    if st.session_state.current_quiz and st.session_state.quiz_status in ["Đang diễn ra", "Đã kết thúc"]:
        st.divider()
        st.markdown("#### 3. ⚡ Xử lý câu trả lời & Tự động cộng điểm")
        
        if st.session_state.quiz_status == "Đang diễn ra":
            st.info("🟢 **ĐANG DIỄN RA:** Đang chờ học viên gửi câu trả lời...")
        else:
            st.success(f"🔴 **ĐÃ KẾT THÚC:** Người chiến thắng: **{st.session_state.quiz_winner}**")

        st.markdown("**Giả lập / Nộp đáp án trực tiếp:**")
        
        sim_col1, sim_col2 = st.columns([2, 1])
        with sim_col1:
            student_select_list = [f"{s['code']} - {s['name']}" for s in ROSTER]
            sim_student = st.selectbox("Chọn học viên thực hiện trả lời:", options=student_select_list)
        with sim_col2:
            sim_ans = st.selectbox("Chọn đáp án:", options=["A", "B", "C", "D"])

        if st.button("🎯 Nộp đáp án trả lời!", type="primary", use_container_width=True):
            parts = sim_student.split(" - ", 1)
            st_code, st_name = parts[0], parts[1]

            is_success, msg, _ = process_quiz_answer(
                student_name=st_name,
                student_code=st_code,
                answer_option=sim_ans
            )

            if is_success:
                st.session_state.quiz_status = "Đã kết thúc"
                st.session_state.quiz_winner = f"{st_name} ({st_code})"

                # Vinh danh lên Discord
                _, w_msg = send_discord_quiz_winner(
                    student_name=st_name,
                    student_code=st_code,
                    topic=st.session_state.current_quiz.get('topic', 'AI/ML'),
                    score=reward_points,
                    override_webhook=discord_webhook
                )

                st.balloons()
                st.success(f"{msg} ({w_msg})")
                st.rerun()
            else:
                st.error(msg)


# --- TAB 5: CÂU HỎI TỪ HỌC VIÊN ---
with tab5:
    st.markdown("### ❓ Câu hỏi từ học viên (Discord /ask)")
    
    questions = get_all_questions()
    
    # Chỉ số thống kê
    total_q = len(questions)
    pending_q = len([q for q in questions if q.get("status") == "Chờ trả lời"])
    answered_q = len([q for q in questions if q.get("status") == "Đã trả lời"])
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Tổng số câu hỏi", total_q)
    m_col2.metric("⏳ Chờ phản hồi", pending_q)
    m_col3.metric("✅ Đã phản hồi", answered_q)
    
    st.divider()
    
    # Bộ lọc danh sách
    filter_status = st.radio(
        "Lọc theo trạng thái câu hỏi:",
        ["Chờ trả lời", "Đã trả lời", "Tất cả"],
        horizontal=True
    )
    
    if filter_status == "Chờ trả lời":
        filtered = [q for q in questions if q.get("status") == "Chờ trả lời"]
    elif filter_status == "Đã trả lời":
        filtered = [q for q in questions if q.get("status") == "Đã trả lời"]
    else:
        filtered = questions
        
    filtered = list(reversed(filtered))  # Mới nhất lên đầu
    
    if not filtered:
        st.info("Chưa có câu hỏi nào trong danh sách này.")
    else:
        for idx, q in enumerate(filtered):
            q_id = q.get("id")
            s_name = q.get("student_name", "Học viên")
            s_code = q.get("student_id", "N/A")
            q_text = q.get("question", "")
            ai_ans = clean_citations(q.get("ai_answer", ""))
            coach_ans = clean_citations(q.get("coach_answer", ai_ans))
            sources = q.get("rag_sources", [])
            status = q.get("status", "Chờ trả lời")
            ts = q.get("timestamp", "")
            discord_id = q.get("discord_user_id", "")
            
            is_pending = status == "Chờ trả lời"
            status_badge = "⏳ Chờ trả lời" if is_pending else "✅ Đã trả lời"
            
            with st.expander(f"[{status_badge}] {s_name} ({s_code}) - {ts}", expanded=is_pending):
                st.markdown("**❓ Nội dung câu hỏi:**")
                st.info(q_text)
                
                st.markdown("**💡 Câu trả lời được gợi ý:**")
                
                input_key = f"coach_ans_input_{q_id}"
                edited_answer = st.text_area(
                    "Nội dung câu trả lời gửi tới học viên:",
                    value=coach_ans,
                    key=input_key,
                    height=120,
                    help="Lab Coach có thể tự do chỉnh sửa văn bản này trước khi gửi cho học viên"
                )
                
                btn_col1, btn_col2 = st.columns([2, 3])
                with btn_col1:
                    if st.button("✅ Accept & Gửi riêng cho Học viên", key=f"btn_accept_{q_id}", type="primary", use_container_width=True):
                        if not edited_answer.strip():
                            st.error("Vui lòng nhập nội dung câu trả lời trước khi nộp.")
                        else:
                            # 1. Cập nhật vào DB
                            update_question_answer(q_id, edited_answer.strip(), status="Đã trả lời")
                            
                            # 2. Gửi tin nhắn riêng / thông báo qua Discord
                            success, notify_msg = send_discord_dm_or_notification(
                                student_name=s_name,
                                student_code=s_code,
                                question=q_text,
                                answer=edited_answer.strip(),
                                discord_user_id=discord_id,
                                override_webhook=discord_webhook
                            )
                            
                            st.session_state.toast_message = {
                                "type": "success",
                                "title": "Đã gửi câu trả lời!",
                                "body": f"Phản hồi đã được duyệt và gửi cho {s_name}: {notify_msg}"
                            }
                            st.rerun()
                
                with btn_col2:
                    if not is_pending:
                        ans_time = q.get("answered_at", "")
                        st.caption(f"✅ Đã gửi phản hồi vào lúc: `{ans_time}`")



