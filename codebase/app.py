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
from codebase.discord_notifier import send_discord_score_notification, get_discord_config

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
st.set_page_config(page_title="Điểm thưởng cho người chăm chỉ", page_icon="⭐", layout="centered")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp { background: #16233d; }
.block-container {
    max-width: 460px;
    background: #ffffff;
    border-radius: 20px;
    padding: 2rem 1.75rem !important;
    margin-top: 3rem;
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
h3 { color: #16233d !important; font-weight: 600 !important; }
p, span, div, label { color: #16233d; }
.stCaption, [data-testid="stCaptionContainer"] { color: #6b7684 !important; }
.stTextInput input {
    background: #f8f9fb !important;
    border: 1.5px solid #e2e5ea !important;
    border-radius: 10px !important;
    color: #16233d !important;
}
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
[data-testid="stMetricValue"], .stRadio label { color: #16233d !important; }
hr { border-color: #eef0f3 !important; }
/* Sidebar styling override for dark mode readability */
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
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

if run_mode == "Kết nối API thật":
    gemini_key = st.sidebar.text_input("Nhập Gemini API Key:", type="password", help="Dùng cho chấm điểm AI và tìm kiếm fuzzy")
    anthropic_key = st.sidebar.text_input("Nhập Anthropic API Key:", type="password", help="Dùng cho tìm kiếm fuzzy Claude")
    if not gemini_key and not anthropic_key:
        st.sidebar.warning("Vui lòng cấu hình API Key để kết nối AI thật.")
else:
    st.sidebar.info("Đang chạy ở chế độ Mock giả lập (không cần API key, tự động xử lý các tình huống khó).")

st.sidebar.write("---")
st.sidebar.subheader("🤖 Discord Bot Notifier")
bot_token_env, channel_id_env, webhook_env = get_discord_config()

if bot_token_env and channel_id_env:
    st.sidebar.success("✅ Discord Bot API: Đã kết nối (.env)")
elif webhook_env:
    st.sidebar.info("🔗 Discord Webhook: Đã kết nối (.env)")
else:
    st.sidebar.caption("💡 Trạng thái: Mock Notifier (Chưa cấu hình Token/Webhook trong `.env`)")

discord_webhook = st.sidebar.text_input("Override Webhook URL (Tùy chọn):", type="password", placeholder="https://discord.com/api/webhooks/...")

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
    
    query = st.text_input(
        "Tên hoặc mã học viên",
        placeholder="Gõ tên hoặc mã học viên...",
        label_visibility="collapsed",
    )
    
    results = local_search(query, db_records) if query else local_search("", db_records)
    
    ai_note = None
    if query and not results:
        with st.spinner("Không khớp trực tiếp, đang hỏi AI gợi ý..."):
            use_mock_flag = (run_mode == "Chạy Mock (Offline - Khuyên dùng test nhanh)")
            
            # Tính toán roster có count động để gửi làm context cho fuzzy search
            roster_for_suggest = []
            counts_map = {s["code"]: 0 for s in ROSTER}
            for r in db_records:
                sid = r.get("student_id")
                if sid and r.get("status") == "Đã đồng bộ":
                    counts_map[sid] = counts_map.get(sid, 0) + 1
            for s in ROSTER:
                roster_for_suggest.append({
                    "name": s["name"],
                    "code": s["code"],
                    "count": counts_map.get(s["code"], 0)
                })
                
            ai_matches, err = ai_fuzzy_suggest_llm(
                query, 
                roster_for_suggest, 
                gemini_api_key=gemini_key, 
                anthropic_api_key=anthropic_key, 
                use_mock=use_mock_flag
            )
            
        if err and "Mock" not in err:
            ai_note = err
        elif ai_matches:
            results = ai_matches
            ai_note = "Gợi ý từ AI (không khớp trực tiếp theo tên/mã)"
        else:
            ai_note = "AI không đủ tự tin để gợi ý — vui lòng nhập lại tên chính xác."
            
    if ai_note:
        st.caption(ai_note)
        
    for s in results:
        cols = st.columns([5, 2, 2])
        with cols[0]:
            st.write(f"**{s['name']}**")
            st.caption(s["code"])
        with cols[1]:
            if s["count"] > 0:
                st.caption(f"Đã {s['count']} lần")
        with cols[2]:
            if st.button("Chọn", key=f"pick-{s['code']}"):
                st.session_state.selected = s["code"]
                st.session_state.ai_analysis = None
                st.session_state.last_note = ""
                st.rerun()

    if st.session_state.selected:
        sel = next((s for s in ROSTER if s["code"] == st.session_state.selected), None)
        if sel:
            st.divider()
            st.markdown(f"#### Chấm điểm cho: **{sel['name']}** (`{sel['code']}`)")
            
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
                            
                            _, discord_msg = send_discord_score_notification(
                                student_name=sel["name"],
                                student_code=sel["code"],
                                final_score=final_score,
                                coach_note=st.session_state.last_note,
                                feedback=final_feedback,
                                status="Chờ duyệt",
                                suggested_score=suggested_score,
                                override_webhook=discord_webhook
                            )
                            
                            st.success(f"Đã lưu nháp cho {sel['name']}! ({discord_msg})")
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
                            
                            _, discord_msg = send_discord_score_notification(
                                student_name=sel["name"],
                                student_code=sel["code"],
                                final_score=final_score,
                                coach_note=st.session_state.last_note,
                                feedback=final_feedback,
                                status="Đã đồng bộ",
                                suggested_score=suggested_score,
                                override_webhook=discord_webhook
                            )
                            
                            st.success(f"Đã đồng bộ điểm cho {sel['name']}! ({discord_msg})")
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
                    
                    _, discord_msg = send_discord_score_notification(
                        student_name=sel["name"],
                        student_code=sel["code"],
                        final_score=points,
                        coach_note="Chấm điểm nhanh thủ công",
                        feedback=f"Đã ghi nhận điểm cộng +{points} phát biểu.",
                        status="Đã đồng bộ",
                        suggested_score=points,
                        override_webhook=discord_webhook
                    )
                    
                    st.success(f"Đã cộng +{points} điểm cho {sel['name']}. ({discord_msg})")
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
