<<<<<<< HEAD
import streamlit as st
import unicodedata
import json
import os
from datetime import datetime

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

st.set_page_config(page_title="Điểm thưởng cho người chăm chỉ", page_icon="⭐", layout="centered")

# --- CSS tùy chỉnh để khớp bộ nhận diện VLearn (navy + đỏ) ---
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
</style>
""", unsafe_allow_html=True)

# --- Roster giả lập (MOCK) — thay bằng file/roster thật của lớp khi triển khai ---
ROSTER = [
    {"name": "Nguyễn Văn Nam", "code": "2A202601742", "count": 5},
    {"name": "Trần Thu Linh", "code": "2A202601756", "count": 4},
    {"name": "Lê Minh Quân", "code": "2A202601761", "count": 3},
    {"name": "Phạm Bảo An", "code": "2A202601778", "count": 2},
    {"name": "Hoàng Gia Huy", "code": "2A202601783", "count": 1},
    {"name": "Đỗ Thảo Vy", "code": "2A202601790", "count": 1},
    {"name": "Vũ Đức Anh", "code": "2A202601805", "count": 0},
    {"name": "Ngô Khánh Linh", "code": "2A202601812", "count": 0},
    {"name": "Bùi Tấn Phát", "code": "2A202601829", "count": 0},
    {"name": "Đặng Ngọc Mai", "code": "2A202601834", "count": 0},
]

if "roster" not in st.session_state:
    st.session_state.roster = [dict(s) for s in ROSTER]
if "log" not in st.session_state:
    st.session_state.log = []
if "selected" not in st.session_state:
    st.session_state.selected = None


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    return s


def local_search(query: str):
    """Lọc + xếp hạng cục bộ, không cần AI — nhanh, chạy tại chỗ."""
    q = normalize(query)
    if not q:
        return sorted(st.session_state.roster, key=lambda s: -s["count"])[:6]
    matches = [
        s for s in st.session_state.roster
        if q in normalize(s["name"]) or q in s["code"].lower()
    ]
    matches.sort(key=lambda s: (
        0 if (normalize(s["name"]).startswith(q) or s["code"].lower().startswith(q)) else 1,
        -s["count"],
    ))
    return matches


def ai_fuzzy_suggest(query: str):
    """
    LỜI GỌI AI THẬT — chỉ kích hoạt khi tìm chuỗi cục bộ không ra kết quả nào.
    Xử lý các trường hợp gõ tắt/biệt danh/sai dấu/nhớ nhầm chính tả mà so khớp
    chuỗi thường không bắt được. Đây là lớp AI xử lý mơ hồ (lớp ② trong 4 lớp
    chỗ khó của spec) — AI phải báo rõ khi không đủ tự tin, KHÔNG được đoán liều.
    AI ở đây KHÔNG liên quan đến việc chấm điểm — chỉ hỗ trợ tìm đúng người.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or Anthropic is None:
        return None, "Chưa cấu hình ANTHROPIC_API_KEY, bỏ qua gợi ý AI."

    client = Anthropic(api_key=api_key)
    roster_names = "\n".join(f"- {s['name']} ({s['code']})" for s in st.session_state.roster)

    prompt = f"""Bạn là trợ lý tìm tên học viên cho lab coach. Lab coach gõ: "{query}"

Danh sách học viên trong lớp:
{roster_names}

Nhiệm vụ: tìm TỐI ĐA 3 học viên có khả năng khớp với input trên (có thể do gõ tắt,
sai dấu, gọi biệt danh, hoặc nhớ nhầm chính tả).
Nếu không đủ tự tin để gợi ý người nào, trả lời rõ là không tìm thấy — KHÔNG đoán liều.

Trả lời CHỈ bằng JSON, không thêm chữ nào khác, đúng định dạng:
{{"matches": ["Tên chính xác 1", "Tên chính xác 2"], "confident": true}}
"""

    try:
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
        matched = [s for s in st.session_state.roster if s["name"] in data["matches"]]
        return matched, None
    except Exception as e:
        return None, f"Lỗi gọi AI: {e}"


st.markdown("### ⭐ Điểm thưởng cho người chăm chỉ")
st.caption("VLearn · VinUni AI Thực Chiến — ghi nhận nhanh điểm cộng phát biểu")

query = st.text_input(
    "Tên hoặc mã học viên",
    placeholder="Gõ tên hoặc mã học viên...",
    label_visibility="collapsed",
)

results = local_search(query) if query else sorted(st.session_state.roster, key=lambda s: -s["count"])[:6]

ai_note = None
if query and not results:
    with st.spinner("Không khớp trực tiếp, đang hỏi AI gợi ý..."):
        ai_matches, err = ai_fuzzy_suggest(query)
    if err:
        ai_note = err
    elif ai_matches:
        results = ai_matches
        ai_note = "Gợi ý từ AI (không khớp trực tiếp theo tên/mã)"
    else:
        ai_note = "AI cũng không đủ tự tin để gợi ý — kiểm tra lại tên hoặc thêm học viên mới."

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
            st.rerun()

if st.session_state.selected:
    sel = next((s for s in st.session_state.roster if s["code"] == st.session_state.selected), None)
    if sel:
        st.divider()
        st.write(f"**{sel['name']}**  ·  `{sel['code']}`")
        points = st.radio("Số điểm cộng", [1, 2, 3], horizontal=True)
        if st.button("Gửi điểm và thông báo Discord", type="primary"):
            sel["count"] += 1
            st.session_state.log.insert(0, {
                "name": sel["name"],
                "code": sel["code"],
                "points": points,
                "time": datetime.now().strftime("%H:%M:%S"),
            })
            st.session_state.selected = None
            st.success(f"Đã cộng +{points} điểm cho {sel['name']}. (Mock) Thông báo Discord đã gửi.")
            st.rerun()

if st.session_state.log:
    st.divider()
    st.caption("Đã ghi nhận buổi này")
    for item in st.session_state.log[:8]:
        st.write(f"{item['time']} — {item['name']} — +{item['points']}")
=======
# /// script
# dependencies = [
#   "streamlit",
#   "google-generativeai",
#   "python-dotenv"
# ]
# ///

import os
import json
import datetime
import sys
import streamlit as st
import streamlit.web.cli as stcli

# Kiểm tra nếu chạy trực tiếp bằng python chay (ví dụ: uv run codebase/app.py)
# thì tự động kích hoạt Streamlit CLI để chạy chính file này và thoát ngay lập tức,
# tránh việc chạy các lệnh Streamlit UI gây nhiễm bẩn FormContext trước khi server bắt đầu.
if __name__ == "__main__" and not st.runtime.exists():
    sys.argv = ["streamlit", "run", __file__]
    sys.exit(stcli.main())

# Thêm thư mục gốc vào sys.path để Python nhận diện module codebase
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codebase.llm import analyze_grading_note

# Đường dẫn lưu trữ database cục bộ
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "points_db.json")

# Đảm bảo thư mục dữ liệu tồn tại
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

# Danh sách học viên mẫu (Mock data)
MOCK_STUDENTS = [
    {"student_id": "SV001", "student_name": "Nguyễn Văn Bách"},
    {"student_id": "SV002", "student_name": "Trần Thị Nam"},
    {"student_id": "SV003", "student_name": "Nguyễn Văn Anh"},
    {"student_id": "SV004", "student_name": "Phạm Minh Hoàng"},
    {"student_id": "SV005", "student_name": "Lê Thu Thảo"},
    {"student_id": "SV006", "student_name": "Đỗ Hoàng Long"},
    {"student_id": "SV007", "student_name": "Vũ Mỹ Linh"},
    {"student_id": "SV008", "student_name": "Hoàng Đức Anh"},
    {"student_id": "SV009", "student_name": "Trần Thanh Bình"},
    {"student_id": "SV010", "student_name": "Phan Quốc Bảo"},
    {"student_id": "SV011", "student_name": "Ngô Tiến Đạt"},
    {"student_id": "SV012", "student_name": "Lê Minh Thư"},
    {"student_id": "SV013", "student_name": "Bùi Anh Tuấn"},
    {"student_id": "SV014", "student_name": "Phạm Ngọc Ánh"},
    {"student_id": "SV015", "student_name": "Nguyễn Hoàng Nam"}
]

# Hàm lấy danh sách học viên động bằng cách gộp mock data và học viên đã lưu
def get_student_list(db_records):
    students_dict = {s["student_id"]: s["student_name"] for s in MOCK_STUDENTS}
    for record in db_records:
        sid = record.get("student_id", "").strip()
        sname = record.get("student_name", "").strip()
        if sid:
            students_dict[sid] = sname
            
    sorted_students = [{"student_id": sid, "student_name": sname} for sid, sname in students_dict.items()]
    sorted_students.sort(key=lambda x: x["student_id"])
    return sorted_students

# Khởi tạo dữ liệu mẫu nếu database trống
if not os.path.exists(DB_PATH) or len(load_db()) == 0:
    sample_data = [
        {
            "id": 1,
            "timestamp": "2026-07-30 08:30:15",
            "student_id": "SV001",
            "student_name": "Nguyễn Văn Bách",
            "coach_note": "Bách giải thích rất rõ về bias-variance tradeoff",
            "suggested_score": 1.0,
            "final_score": 1.0,
            "feedback": "Tuyệt vời! Giải thích rất tốt về Bias-Variance tradeoff, phân biệt được rõ mô hình phức tạp và đơn giản.",
            "status": "Đã đồng bộ"
        },
        {
            "id": 2,
            "timestamp": "2026-07-30 09:15:22",
            "student_id": "SV002",
            "student_name": "Trần Thị Nam",
            "coach_note": "Nam giơ tay phát biểu ý kiến bổ sung phần regularization",
            "suggested_score": 0.5,
            "final_score": 0.5,
            "feedback": "Cảm ơn đóng góp bổ sung của em về phương pháp Regularization (L1/L2) giúp tránh overfitting.",
            "status": "Đã đồng bộ"
        }
    ]
    save_db(sample_data)

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="AI Lab Coach Point Grader 🎯",
    page_icon="🎯",
    layout="wide"
)

# Header trang web
st.write(
    """
    <div style='text-align: center; margin-bottom: 20px;'>
        <h1 style='color: #1E3A8A; font-family: sans-serif;'>🎯 AI Lab Coach Point Grader</h1>
        <p style='color: #4B5563; font-size: 16px;'>
            Giải quyết pain-point: Ghi nhận điểm cộng tức thời và minh bạch hóa điểm số cho học viên.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Khởi tạo các biến session state
if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = None
if "last_note" not in st.session_state:
    st.session_state.last_note = ""
if "student_selector" not in st.session_state:
    st.session_state.student_selector = "-- Tự nhập học viên mới --"

# --- SIDEBAR CONFIG ---
st.sidebar.header("⚙️ Cấu Hình Hệ Thống")

# Chọn chế độ chạy
run_mode = st.sidebar.radio(
    "Chế độ hoạt động:",
    ["Chạy Mock (Offline - Khuyên dùng test nhanh)", "Kết nối Gemini API thật"]
)

api_key = ""
if run_mode == "Kết nối Gemini API thật":
    api_key = st.sidebar.text_input("Nhập Gemini API Key:", type="password", help="Lấy từ Google AI Studio")
    if not api_key:
        st.sidebar.warning("Vui lòng nhập API Key để kết nối Gemini thật.")
else:
    st.sidebar.info("Đang chạy ở chế độ Mock giả lập (không cần API key, tự động xử lý các tình huống chỗ khó).")

st.sidebar.write("---")
st.sidebar.write("📊 **Quản lý dữ liệu**")
if st.sidebar.button("Reset Database về mặc định", type="secondary"):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    st.rerun()

# --- MAIN WORKSPACE ---
tab1, tab2 = st.tabs(["✍️ Giao Diện Lab Coach", "🔍 Tra Cứu Học Viên (Minh Bạch)"])

# Tải danh sách điểm hiện tại
db_records = load_db()

# --- TAB 1: GIAO DIỆN LAB COACH ---
with tab1:
    st.subheader("Trình ghi nhận & Duyệt điểm AI")
    
    col_input, col_preview = st.columns([1, 1])
    
    with col_input:
        st.markdown("##### 📝 Nhập thông tin phát biểu")
        
        # Danh sách học viên động
        student_list = get_student_list(db_records)
        suggestion_options = ["-- Tự nhập học viên mới --"] + [f"{s['student_id']} - {s['student_name']}" for s in student_list]
        
        selected_suggest = st.selectbox(
            "🔍 Gợi ý nhanh (Chọn học viên từ danh sách):",
            options=suggestion_options,
            key="student_selector",
            help="Chọn học viên có sẵn để tự động điền MSSV và Họ tên."
        )
        
        # Trích xuất MSSV và Họ tên từ lựa chọn gợi ý
        prefilled_id = ""
        prefilled_name = ""
        if selected_suggest != "-- Tự nhập học viên mới --":
            parts = selected_suggest.split(" - ", 1)
            if len(parts) == 2:
                prefilled_id = parts[0]
                prefilled_name = parts[1]
                
        with st.form("grading_form"):
            student_id = st.text_input("Mã số học viên (MSSV):", value=prefilled_id, placeholder="Ví dụ: SV003")
            student_name = st.text_input("Họ và tên học viên:", value=prefilled_name, placeholder="Ví dụ: Nguyễn Văn A")
            coach_note = st.text_area(
                "Ghi chú ngắn của Coach (Nội dung trả lời):",
                placeholder="Ví dụ: Nam giải thích đúng ý về overfitting là do mô hình quá phức tạp...",
                height=100
            )
            submit_btn = st.form_submit_button("Gửi AI phân tích 🚀")
            
            if submit_btn:
                if not student_id or not student_name or not coach_note:
                    st.error("Vui lòng điền đầy đủ MSSV, Họ tên và Ghi chú ngắn!")
                else:
                    with st.spinner("AI đang phân tích câu trả lời..."):
                        is_mock = (run_mode == "Chạy Mock (Offline - Khuyên dùng test nhanh)")
                        analysis = analyze_grading_note(coach_note, api_key=api_key, use_mock=is_mock)
                        st.session_state.ai_analysis = analysis
                        st.session_state.last_note = coach_note
                        st.rerun()

    with col_preview:
        st.markdown("##### 🤖 Kết quả phân tích từ AI")
        
        analysis = st.session_state.ai_analysis
        
        if analysis:
            status = analysis.get("status", "success")
            suggested_score = float(analysis.get("suggested_score", 0.0))
            feedback = analysis.get("feedback", "")
            explanation = analysis.get("explanation", "")
            
            # Hiển thị thông báo trạng thái dựa trên status của AI
            if status == "need_more_info":
                st.warning(f"⚠️ **CẦN BỔ SUNG THÔNG TIN:** {explanation}")
            elif status == "rejected":
                st.error(f"❌ **TỪ CHỐI CHUYỂN ĐỔI:** {explanation}")
            else:
                st.success("✅ **PHÂN TÍCH THÀNH CÔNG:** Thông tin đầy đủ và đúng kiến thức chuyên môn.")
                
            # Form duyệt để Coach điều chỉnh trước khi lưu
            st.write("---")
            st.markdown("**Bản nháp phê duyệt:**")
            
            final_score = st.selectbox(
                "Điểm cộng đề xuất (Coach có thể sửa):",
                [0.0, 0.5, 1.0],
                index=[0.0, 0.5, 1.0].index(suggested_score) if suggested_score in [0.0, 0.5, 1.0] else 0
            )
            
            final_feedback = st.text_area("Feedback nháp gửi học viên (Coach có thể sửa):", value=feedback, height=100)
            
            st.markdown(f"**Giải thích nội bộ:** *{explanation}*")
            
            col_b1, col_b2 = st.columns([1, 1])
            with col_b1:
                # Nút Lưu Nháp (Để học viên biết mình đã được ghi nhận nhưng đang duyệt)
                if st.button("Lưu nháp (Hiện trạng thái Chờ duyệt)", use_container_width=True, type="secondary"):
                    new_record = {
                        "id": len(db_records) + 1,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "student_id": student_id,
                        "student_name": student_name,
                        "coach_note": st.session_state.last_note,
                        "suggested_score": suggested_score,
                        "final_score": final_score,
                        "feedback": final_feedback,
                        "status": "Chờ duyệt"
                    }
                    db_records.append(new_record)
                    save_db(db_records)
                    st.success(f"Đã lưu nháp cho {student_name}!")
                    st.session_state.ai_analysis = None
                    st.session_state.student_selector = "-- Tự nhập học viên mới --"
                    st.rerun()
                    
            with col_b2:
                # Nút Duyệt & Đồng bộ chính thức
                if st.button("Duyệt & Đồng bộ ngay ⚡", use_container_width=True, type="primary"):
                    new_record = {
                        "id": len(db_records) + 1,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "student_id": student_id,
                        "student_name": student_name,
                        "coach_note": st.session_state.last_note,
                        "suggested_score": suggested_score,
                        "final_score": final_score,
                        "feedback": final_feedback,
                        "status": "Đã đồng bộ"
                    }
                    db_records.append(new_record)
                    save_db(db_records)
                    st.success(f"Đã đồng bộ điểm cho {student_name}!")
                    st.session_state.ai_analysis = None
                    st.session_state.student_selector = "-- Tự nhập học viên mới --"
                    st.rerun()
        else:
            st.info("Chưa có dữ liệu phân tích. Hãy điền thông tin và bấm gửi AI bên trái.")

# --- TAB 2: TRA CỨU HỌC VIÊN ---
with tab2:
    st.subheader("Cổng thông tin tra cứu minh bạch dành cho Học viên")
    st.write(
        """
        *Giải pháp cho Pain Point:* Học viên giơ tay trả lời sẽ không phải lo lắng điểm của mình có được ghi nhận hay chưa. 
        Ngay khi Lab Coach lưu nháp hoặc duyệt điểm, học viên có thể chọn MSSV dưới đây để tra cứu tức thì trạng thái điểm của mình.
        """
    )
    
    student_list = get_student_list(db_records)
    search_options = ["-- Chọn học viên để tra cứu --"] + [f"{s['student_id']} - {s['student_name']}" for s in student_list]
    
    selected_search = st.selectbox(
        "🔍 Chọn Mã số học viên (MSSV) hoặc Họ tên để tra cứu:",
        options=search_options,
        index=0,
        help="Chọn học viên để xem bảng lịch sử điểm cộng chi tiết."
    )
    
    search_query = ""
    if selected_search != "-- Chọn học viên để tra cứu --":
        parts = selected_search.split(" - ", 1)
        if len(parts) == 2:
            search_query = parts[0]
            
    if search_query:
        # Lọc danh sách theo MSSV
        filtered_records = [r for r in db_records if r["student_id"].strip().upper() == search_query.strip().upper()]
        
        if len(filtered_records) > 0:
            # Tính tổng điểm
            total_score = sum(r["final_score"] for r in filtered_records if r["status"] == "Đã đồng bộ")
            pending_score = sum(r["final_score"] for r in filtered_records if r["status"] == "Chờ duyệt")
            
            st.markdown(f"#### 📊 Kết quả học tập của: **{filtered_records[0]['student_name']}** ({search_query.upper()})")
            
            col_s1, col_s2 = st.columns(2)
            col_s1.metric("Điểm cộng Đã đồng bộ ✅", f"+{total_score}")
            col_s2.metric("Điểm cộng Chờ duyệt (Nháp) ⏳", f"+{pending_score}")
            
            st.markdown("##### Danh sách lịch sử chi tiết:")
            for record in reversed(filtered_records):
                status_color = "green" if record["status"] == "Đã đồng bộ" else "orange"
                status_badge = f"<span style='background-color: {status_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;'>{record['status']}</span>"
                
                with st.container(border=True):
                    st.markdown(
                        f"""
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <strong>⏱️ Thời gian: {record['timestamp']}</strong>
                            {status_badge}
                        </div>
                        <div style='margin-top: 10px;'>
                            <p><strong>Ghi chú phát biểu:</strong> <i>{record['coach_note']}</i></p>
                            <p><strong>Số điểm:</strong> +{record['final_score']} (Gợi ý ban đầu của AI: +{record['suggested_score']})</p>
                            <p><strong>Lời nhắn phản hồi (Feedback):</strong> {record['feedback']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.warning(f"Không tìm thấy dữ liệu điểm cộng nào cho học viên có MSSV: '{search_query}'")
    else:
        # Nếu chưa tìm kiếm, hiển thị bảng toàn bộ học viên để tiện theo dõi demo
        st.markdown("##### 📋 Bảng tổng hợp toàn bộ điểm cộng trong hệ thống (Demo View)")
        if len(db_records) > 0:
            # Format dữ liệu để hiển thị bảng gọn gàng
            display_records = []
            for r in db_records:
                display_records.append({
                    "Thời gian": r["timestamp"],
                    "MSSV": r["student_id"],
                    "Học viên": r["student_name"],
                    "Ghi chú của Coach": r["coach_note"],
                    "Điểm": f"+{r['final_score']}",
                    "Feedback": r["feedback"],
                    "Trạng thái": r["status"]
                })
            st.table(display_records)
        else:
            st.info("Hiện tại chưa có bản ghi điểm cộng nào.")



>>>>>>> a2bfbf693161ffbae1ae759927b9c07b6f2f465a
