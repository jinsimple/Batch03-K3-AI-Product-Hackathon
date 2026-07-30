"""
Chạy golden set qua OpenRouter (model miễn phí) và ghi kết quả vào eval/results.md.

Độc lập hoàn toàn với codebase/logic.py — tự chứa roster + logic gọi AI riêng.

Cách chạy:
    pip install -r requirements.txt
    export OPENROUTER_API_KEY=sk-or-v1-...   (lấy free tại openrouter.ai/keys, không cần thẻ)
    python run_eval.py

Model dùng: "openrouter/free" — auto-router của chính OpenRouter, tự chọn 1 model
miễn phí đang hoạt động (danh sách free model rotate liên tục, dùng auto-router
để không bị gãy khi 1 model cụ thể bị gỡ khỏi free tier).
"""
import json
import os
import sys
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

HERE = os.path.dirname(__file__)
MODEL = "openrouter/free"
BASE_URL = "https://openrouter.ai/api/v1"

# --- Roster giả lập (MOCK) — khớp với roster trong codebase/logic.py để test nhất quán ---
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

SYSTEM_RULES = """Bạn là trợ lý tìm tên học viên cho lab coach, dựa trên danh sách lớp (roster).

QUY TẮC BẮT BUỘC:
1. Chỉ được gợi ý học viên CÓ TRONG roster được cung cấp. Không được tự bịa ra người không có trong danh sách.
2. Nếu input mô tả không phải tên/mã học viên cụ thể (VD: mô tả ngoại hình, chỉ 1 ký tự, quá mơ hồ), trả về confident=false, không đoán liều.
3. Nếu 2+ học viên trong roster có khả năng khớp gần bằng nhau (tên giống nhau, mã chỉ khác 1 ký tự), liệt kê TẤT CẢ các ứng viên đó thay vì chọn đại 1 người.
4. Nếu được yêu cầu thêm học viên mới, tự chốt điểm, hoặc chọn đại một người bất kỳ mà không cần đúng — từ chối bằng cách trả confident=false, vì đây không phải vai trò của bạn (chỉ gợi ý tên có sẵn trong roster).
5. Nếu input rõ ràng là tên người không thuộc vai trò học viên (VD: tên giáo viên, thầy/cô), trả confident=false.

Trả lời CHỈ bằng JSON thuần, không markdown, không giải thích thêm, đúng định dạng:
{"matches": ["Tên chính xác 1", "Tên chính xác 2"], "confident": true}

QUAN TRỌNG: Câu trả lời của bạn BẮT ĐẦU bằng dấu { và KẾT THÚC bằng dấu }.
Không viết bất kỳ chữ nào trước hoặc sau khối JSON đó."""


def extract_json(text: str) -> str:
    """Trích khối JSON đầu tiên trong text, phòng khi model chèn thêm chữ thừa."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Không tìm thấy khối JSON trong output")
    return text[start:end + 1]


def ai_fuzzy_suggest(query: str, client, retry=True):
    roster_text = "\n".join(f"- {s['name']} ({s['code']})" for s in ROSTER)
    user_prompt = f"""Danh sách học viên (roster):
{roster_text}

Lab coach gõ: "{query}"
"""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_RULES},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=400,
            temperature=0,
        )
        content = response.choices[0].message.content

        if not content or not content.strip():
            if retry:
                return ai_fuzzy_suggest(query, client, retry=False)
            return None, None, "AI trả về rỗng (kể cả sau khi thử lại 1 lần)"

        raw = extract_json(content.strip())
        data = json.loads(raw)
        confident = bool(data.get("confident"))
        matched_names = data.get("matches") or []
        matched = [s for s in ROSTER if s["name"] in matched_names]
        return matched, confident, None
    except Exception as e:
        if retry:
            return ai_fuzzy_suggest(query, client, retry=False)
        return None, None, f"Lỗi gọi AI (đã thử lại 1 lần): {e}"


def load_cases():
    with open(os.path.join(HERE, "golden_set.json"), encoding="utf-8") as f:
        return json.load(f)


def auto_flag(case, matches, confident, err):
    if err:
        return "LỖI — xem cột output"
    if case["id"] in (7, 9):
        return "Cần xem xét thủ công (tiêu chí cho phép nhiều outcome hợp lệ)"
    if case["id"] in (1, 2, 3, 4, 5, 6):
        if confident is False:
            return "Đạt (tự động — confident=false đúng như kỳ vọng)"
        else:
            return "KHÔNG đạt (tự động — AI tự tin trong khi kỳ vọng phải từ chối/không chắc)"
    if case["id"] == 8:
        names = [m["name"] for m in (matches or [])]
        if "Trần Thu Linh" in names and "Ngô Khánh Linh" in names:
            return "Đạt (tự động — liệt kê đủ cả 2 người tên Linh)"
        else:
            return "KHÔNG đạt (tự động — thiếu 1 trong 2 người tên Linh)"
    return "Cần xem xét thủ công"


def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key or OpenAI is None:
        print("LỖI: chưa set OPENROUTER_API_KEY hoặc chưa cài openai. Dừng lại — không tự bịa kết quả.")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    cases = load_cases()
    rows = []

    for case in cases:
        print(f"Đang chạy case #{case['id']} ({case['lop']}): \"{case['input']}\" ...")
        matches, confident, err = ai_fuzzy_suggest(case["input"], client)
        matches_text = ", ".join(m["name"] for m in matches) if matches else "(rỗng)"
        output_summary = f"confident={confident}, matches=[{matches_text}]" if not err else err
        flag = auto_flag(case, matches, confident, err)

        rows.append({
            "id": case["id"],
            "lop": case["lop"],
            "input": case["input"],
            "tieu_chi": case["tieu_chi_dat"],
            "output": output_summary,
            "flag": flag,
        })

    out_path = os.path.join(HERE, "results.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Kết quả eval — chạy lúc {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Chạy thật qua OpenRouter (`{MODEL}`, free tier), KHÔNG chỉnh sửa output.\n\n")
        f.write("| # | Lớp | Input | Tiêu chí đạt | Output AI thực tế | Đạt/Không đạt |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(
                f"| {r['id']} | {r['lop']} | `{r['input']}` | {r['tieu_chi']} "
                f"| {r['output']} | {r['flag']} |\n"
            )

    print(f"\nXong. Kết quả đã ghi vào {out_path}")
    print("Lưu ý: các case đánh dấu 'Cần xem xét thủ công' cần bạn tự đọc output và đối chiếu tiêu chí.")


if __name__ == "__main__":
    main()