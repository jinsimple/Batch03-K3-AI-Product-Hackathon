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