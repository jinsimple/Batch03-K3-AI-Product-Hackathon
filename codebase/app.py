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
import requests
import unicodedata

# Kích hoạt Streamlit CLI nếu chạy trực tiếp bằng python/uv run
if __name__ == "__main__" and not st.runtime.exists():
    sys.argv = ["streamlit", "run", __file__]
    sys.exit(stcli.main())

# Thêm thư mục gốc vào PYTHONPATH để Python nhận diện module codebase
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codebase.llm import analyze_grading_note, ai_fuzzy_suggest_llm

# Đường dẫn lưu trữ database cục bộ
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "points_db.json")
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

def local_search(query: str, db_records):
    q = normalize(query)
    # Tính số lần phát biểu động dựa trên dữ liệu database "Đã đồng bộ"
    counts = {s["code"]: 0 for s in ROSTER}
    for r in db_records:
        sid = r.get("student_id")
        if sid and r.get("status") == "Đã đồng bộ":
            counts[sid] = counts.get(sid, 0) + 1

    roster_with_counts = []
    for s in ROSTER:
        roster_with_counts.append({
            "name": s["name"],
            "code": s["code"],
            "count": counts.get(s["code"], 0)
        })

    if not q:
        return sorted(roster_with_counts, key=lambda s: -s["count"])[:6]
        
    matches = [
        s for s in roster_with_counts
        if q in normalize(s["name"]) or q in s["code"].lower()
    ]
    matches.sort(key=lambda s: (
        0 if (normalize(s["name"]).startswith(q) or s["code"].lower().startswith(q)) else 1,
        -s["count"],
    ))
    return matches

def send_discord_message(webhook_url: str, content: str):
    if not webhook_url:
        return True, "Mock Discord: Chưa cấu hình webhook."
    try:
        res = requests.post(webhook_url, json={"content": content}, timeout=5)
        if res.status_code in [200, 204]:
            return True, "Gửi thông báo Discord thành công!"
        else:
            return False, f"Lỗi gửi Discord (HTTP {res.status_code}): {res.text}"
    except Exception as e:
        return False, f"Lỗi kết nối Discord: {e}"

# --- CẤU HÌNH TRANG & CSS NHẬN DIỆN THƯƠNG HIỆU VLEARN (NAVY + ĐỎ) ---
st.set_page_config(page_title="Điểm thưởng cho người chăm chỉ", page_icon="⭐", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp { background: #16233d; }

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
</style>
""", unsafe_allow_html=True)

# Khởi tạo các biến session state
if "selected" not in st.session_state:
    st.session_state.selected = None
if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = None
if "last_note" not in st.session_state:
    st.session_state.last_note = ""

# --- SIDEBAR CONFIG ---
st.sidebar.header("⚙️ Cấu Hình Hệ Thống")

run_mode = st.sidebar.radio(
    "Chế độ hoạt động:",
    ["Chạy Mock (Offline - Khuyên dùng test nhanh)", "Kết nối API thật"]
)

gemini_key = ""
anthropic_key = ""
discord_webhook = ""

if run_mode == "Kết nối API thật":
    gemini_key = st.sidebar.text_input("Nhập Gemini API Key:", type="password", help="Dùng cho chấm điểm AI và tìm kiếm fuzzy")
    anthropic_key = st.sidebar.text_input("Nhập Anthropic API Key:", type="password", help="Dùng cho tìm kiếm fuzzy Claude")
    if not gemini_key and not anthropic_key:
        st.sidebar.warning("Vui lòng cấu hình API Key để kết nối AI thật.")
else:
    st.sidebar.info("Đang chạy ở chế độ Mock giả lập (không cần API key, tự động xử lý các tình huống khó).")

discord_webhook = st.sidebar.text_input("Discord Webhook URL (Tùy chọn):", type="password", placeholder="https://discord.com/api/webhooks/...")

st.sidebar.write("---")
st.sidebar.write("📊 **Quản lý dữ liệu**")
if st.sidebar.button("Reset Database về mặc định", type="secondary"):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    st.session_state.selected = None
    st.session_state.ai_analysis = None
    st.rerun()

# Tải danh sách điểm hiện tại
db_records = load_db()

# --- MAIN WORKSPACE ---
tab1, tab2 = st.tabs(["✍️ Ghi nhận điểm cộng", "🔍 Tra cứu minh bạch"])

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
            st.session_state.ai_analysis = None
            st.session_state.last_note = ""
            st.rerun()
    else:
        if st.session_state.selected is not None:
            st.session_state.selected = None
            st.session_state.ai_analysis = None
            st.session_state.last_note = ""
            st.rerun()

    if st.session_state.selected:
        sel = next((s for s in ROSTER if s["code"] == st.session_state.selected), None)
        if sel:
            st.divider()
            # Khởi tạo thẻ neo để scroll đến khi click nút Chọn
            st.markdown('<div id="grading-section"></div>', unsafe_allow_html=True)
            st.markdown(f"#### Chấm điểm cho: **{sel['name']}** (`{sel['code']}`)")
            
            # Kích hoạt JS scroll nếu flag st.session_state.scroll_to_grading được đặt
            if st.session_state.get("scroll_to_grading"):
                st.markdown(
                    '<img src="x" style="display:none;" onerror="const el = window.parent.document.getElementById(\'grading-section\'); if(el) el.scrollIntoView({behavior: \'smooth\'});">',
                    unsafe_allow_html=True
                )
                st.session_state.scroll_to_grading = False
            
            award_mode = st.radio("Phương thức chấm điểm:", ["Dùng AI phân tích ghi chú", "Chấm điểm nhanh thủ công"], horizontal=True)
            
            if award_mode == "Dùng AI phân tích ghi chú":
                coach_note = st.text_area(
                    "Ghi chú ngắn của Coach (Nội dung trả lời):",
                    value=st.session_state.last_note,
                    placeholder="Ví dụ: Nam giải thích đúng ý về overfitting là do mô hình quá phức tạp...",
                    height=80
                )
                
                if st.button("Gửi AI phân tích 🚀", type="primary"):
                    if not coach_note.strip():
                        st.error("Vui lòng nhập ghi chú của Coach!")
                    else:
                        with st.spinner("AI đang phân tích câu trả lời..."):
                            use_mock_flag = (run_mode == "Chạy Mock (Offline - Khuyên dùng test nhanh)")
                            analysis = analyze_grading_note(coach_note, api_key=gemini_key, use_mock=use_mock_flag)
                            st.session_state.ai_analysis = analysis
                            st.session_state.last_note = coach_note
                            st.rerun()
                            
                if st.session_state.ai_analysis:
                    analysis = st.session_state.ai_analysis
                    status = analysis.get("status", "success")
                    suggested_score = float(analysis.get("suggested_score", 0.0))
                    feedback = analysis.get("feedback", "")
                    explanation = analysis.get("explanation", "")
                    
                    if status == "need_more_info":
                        st.warning(f"⚠️ **CẦN BỔ SUNG THÔNG TIN:** {explanation}")
                    elif status == "rejected":
                        st.error(f"❌ **TỪ CHỐI CHUYỂN ĐỔI:** {explanation}")
                    else:
                        st.success("✅ **PHÂN TÍCH THÀNH CÔNG:** Ghi chú hợp lệ và đầy đủ thông tin.")
                        
                    st.divider()
                    st.markdown("**Bản nháp phê duyệt:**")
                    
                    final_score = st.selectbox(
                        "Điểm cộng đề xuất (Coach có thể sửa):",
                        [0.0, 0.5, 1.0],
                        index=[0.0, 0.5, 1.0].index(suggested_score) if suggested_score in [0.0, 0.5, 1.0] else 0
                    )
                    
                    final_feedback = st.text_area("Feedback nháp gửi học viên (Coach có thể sửa):", value=feedback, height=80)
                    st.caption(f"*Giải thích nội bộ:* {explanation}")
                    
                    col_b1, col_b2 = st.columns([1, 1])
                    with col_b1:
                        if st.button("Lưu nháp (Chờ duyệt)", use_container_width=True):
                            new_record = {
                                "id": len(db_records) + 1,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "student_id": sel["code"],
                                "student_name": sel["name"],
                                "coach_note": st.session_state.last_note,
                                "suggested_score": suggested_score,
                                "final_score": final_score,
                                "feedback": final_feedback,
                                "status": "Chờ duyệt"
                            }
                            db_records.append(new_record)
                            save_db(db_records)
                            
                            discord_content = f"⏳ [CHỜ DUYỆT] Học viên {sel['name']} ({sel['code']}) được cộng +{final_score} điểm. Ghi chú: {st.session_state.last_note}. Feedback: {final_feedback}"
                            send_discord_message(discord_webhook, discord_content)
                            
                            st.success(f"Đã lưu nháp cho {sel['name']}!")
                            st.session_state.selected = None
                            st.session_state.ai_analysis = None
                            st.session_state.last_note = ""
                            st.rerun()
                            
                    with col_b2:
                        if st.button("Duyệt & Đồng bộ ngay ⚡", use_container_width=True, type="primary"):
                            new_record = {
                                "id": len(db_records) + 1,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "student_id": sel["code"],
                                "student_name": sel["name"],
                                "coach_note": st.session_state.last_note,
                                "suggested_score": suggested_score,
                                "final_score": final_score,
                                "feedback": final_feedback,
                                "status": "Đã đồng bộ"
                            }
                            db_records.append(new_record)
                            save_db(db_records)
                            
                            discord_content = f"⭐ [ĐÃ ĐỒNG BỘ] Học viên {sel['name']} ({sel['code']}) được cộng +{final_score} điểm! Ghi chú: {st.session_state.last_note}. Feedback: {final_feedback}"
                            send_discord_message(discord_webhook, discord_content)
                            
                            st.success(f"Đã đồng bộ điểm cho {sel['name']}!")
                            st.session_state.selected = None
                            st.session_state.ai_analysis = None
                            st.session_state.last_note = ""
                            st.rerun()
            
            else: # Chấm điểm nhanh thủ công
                points = st.radio("Số điểm cộng:", [1.0, 2.0, 3.0], horizontal=True)
                if st.button("Gửi điểm và thông báo Discord", type="primary", use_container_width=True):
                    new_record = {
                        "id": len(db_records) + 1,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "student_id": sel["code"],
                        "student_name": sel["name"],
                        "coach_note": "Chấm điểm nhanh thủ công",
                        "suggested_score": points,
                        "final_score": points,
                        "feedback": f"Đã ghi nhận điểm cộng +{points} phát biểu.",
                        "status": "Đã đồng bộ"
                    }
                    db_records.append(new_record)
                    save_db(db_records)
                    
                    discord_content = f"⭐ [ĐÃ ĐỒNG BỘ] Học viên {sel['name']} ({sel['code']}) được cộng nhanh +{points} điểm!"
                    send_discord_message(discord_webhook, discord_content)
                    
                    st.success(f"Đã cộng +{points} điểm cho {sel['name']}. (Mock) Thông báo Discord đã gửi.")
                    st.session_state.selected = None
                    st.session_state.ai_analysis = None
                    st.session_state.last_note = ""
                    st.rerun()
                    
            if st.button("Đóng bảng chấm điểm"):
                st.session_state.selected = None
                st.session_state.ai_analysis = None
                st.session_state.last_note = ""
                st.rerun()

# --- TAB 2: TRA CỨU HỌC VIÊN ---
with tab2:
    st.markdown("### 🔍 Cổng Tra Cứu Minh Bạch")
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
            total_score = sum(r["final_score"] for r in filtered_records if r["status"] == "Đã đồng bộ")
            pending_score = sum(r["final_score"] for r in filtered_records if r["status"] == "Chờ duyệt")
            
            st.markdown(f"#### Lịch sử của: **{filtered_records[0]['student_name']}**")
            
            col_s1, col_s2 = st.columns(2)
            col_s1.metric("Đã đồng bộ ✅", f"+{total_score}")
            col_s2.metric("Chờ duyệt ⏳", f"+{pending_score}")
            
            st.markdown("##### Chi tiết các lượt phát biểu:")
            for record in reversed(filtered_records):
                status_color = "green" if record["status"] == "Đã đồng bộ" else "orange"
                status_badge = f"<span style='background-color: {status_color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;'>{record['status']}</span>"
                
                with st.container(border=True):
                    st.markdown(
                        f"""
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <strong>⏱️ {record['timestamp']}</strong>
                            {status_badge}
                        </div>
                        <div style='margin-top: 5px; font-size: 14px;'>
                            <p><strong>Ghi chú:</strong> <i>{record['coach_note']}</i></p>
                            <p><strong>Điểm cộng:</strong> +{record['final_score']} (AI đề xuất: +{record.get('suggested_score', 0.0)})</p>
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
                display_records.append({
                    "Thời gian": r["timestamp"],
                    "Mã HV": r["student_id"],
                    "Học viên": r["student_name"],
                    "Ghi chú": r["coach_note"],
                    "Điểm": f"+{r['final_score']}",
                    "Feedback": r["feedback"],
                    "Trạng thái": r["status"]
                })
            st.table(display_records)
        else:
            st.info("Hiện tại chưa có bản ghi điểm cộng nào.")
