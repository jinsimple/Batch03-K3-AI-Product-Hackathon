# /// script
# dependencies = [
#   "google-generativeai"
# ]
# ///

import os
import json
import sys

# Thêm thư mục gốc vào PYTHONPATH để import được codebase
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codebase.llm import analyze_grading_note

def main():
    # Xác định đường dẫn file
    base_dir = os.path.dirname(__file__)
    golden_set_path = os.path.join(base_dir, "golden_set.json")
    report_path = os.path.join(base_dir, "eval_report.md")
    
    if not os.path.exists(golden_set_path):
        print(f"Lỗi: Không tìm thấy file golden_set.json tại {golden_set_path}")
        sys.exit(1)
        
    with open(golden_set_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)
        
    api_key = os.environ.get("GEMINI_API_KEY", "")
    use_mock = True
    
    if api_key:
        use_mock = False
        print("🔑 Phát hiện GEMINI_API_KEY từ môi trường. Đang chạy kiểm thử với Gemini API thật...")
    else:
        print("ℹ️ Không tìm thấy GEMINI_API_KEY. Đang chạy kiểm thử với MOCK Engine...")
        
    passed_count = 0
    results = []
    
    print("\n--- BẮT ĐẦU CHẠY KIỂM THỬ (GOLDEN SET) ---")
    print(f"Tổng số test case: {len(test_cases)}\n")
    
    for case in test_cases:
        case_id = case["id"]
        category = case["category"]
        input_text = case["input"]
        exp_status = case["expected_status"]
        exp_min = case["expected_score_min"]
        exp_max = case["expected_score_max"]
        
        # Gọi phân tích
        res = analyze_grading_note(input_text, api_key=api_key, use_mock=use_mock)
        
        status = res.get("status", "")
        score = float(res.get("suggested_score", 0.0))
        feedback = res.get("feedback", "")
        explanation = res.get("explanation", "")
        
        # Kiểm tra tiêu chí đạt
        status_ok = (status == exp_status)
        score_ok = (exp_min <= score <= exp_max)
        passed = status_ok and score_ok
        
        status_icon = "✅ ĐẠT" if passed else "❌ KHÔNG ĐẠT"
        if passed:
            passed_count += 1
            
        print(f"[{status_icon}] Case #{case_id} [{category}]")
        print(f"  - Input: \"{input_text}\"")
        print(f"  - Kết quả AI: status='{status}', score={score}")
        if not passed:
            print(f"    -> LỖI: Kỳ vọng status='{exp_status}', score trong khoảng [{exp_min}, {exp_max}]")
        print(f"  - Giải thích của AI: {explanation}\n")
        
        results.append({
            "id": case_id,
            "category": category,
            "input": input_text,
            "exp_status": exp_status,
            "exp_score": f"{exp_min} - {exp_max}" if exp_min != exp_max else f"{exp_min}",
            "ai_status": status,
            "ai_score": score,
            "passed": passed,
            "explanation": explanation,
            "feedback": feedback
        })
        
    # Tạo báo cáo Markdown
    report_md = []
    report_md.append("# Báo cáo kết quả đánh giá (Evaluation Report) - Golden Set")
    report_md.append(f"\n- **Chế độ kiểm thử:** {'Gemini API Thật' if not use_mock else 'Mock Engine'}")
    report_md.append(f"- **Tỷ lệ vượt qua:** {passed_count}/{len(test_cases)} ({passed_count/len(test_cases)*100:.1f}%)")
    report_md.append("\n## Bảng chi tiết kết quả chạy thử nghiệm\n")
    report_md.append("| ID | Nhóm phân loại | Ghi chú đầu vào | Trạng thái (Kỳ vọng) | Điểm (Kỳ vọng) | Trạng thái AI | Điểm AI | Kết luận |")
    report_md.append("|---|---|---|---|---|---|---|---|")
    
    for r in results:
        status_str = "✅ Đạt" if r["passed"] else "❌ Không Đạt"
        report_md.append(
            f"| {r['id']} | {r['category']} | `{r['input']}` | `{r['exp_status']}` | `{r['exp_score']}` | `{r['ai_status']}` | `+{r['ai_score']}` | **{status_str}** |"
        )
        
    report_md.append("\n## Phân tích phản hồi chi tiết từ AI\n")
    for r in results:
        report_md.append(f"### Case #{r['id']}: {r['category']}")
        report_md.append(f"- **Đầu vào:** *\"{r['input']}\"*")
        report_md.append(f"- **Điểm gợi ý:** `+{r['ai_score']}` (Trạng thái: `{r['ai_status']}`)")
        report_md.append(f"- **Giải thích của AI:** {r['explanation']}")
        report_md.append(f"- **Phản hồi nháp gửi học viên (Feedback):** *\"{r['feedback']}\"*")
        report_md.append("\n---")
        
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_md))
        
    print(f"🎉 Đã ghi nhận báo cáo kết quả kiểm thử vào file: {report_path}")
    print(f"Kết quả chung: Đã vượt qua {passed_count}/{len(test_cases)} test cases.")

if __name__ == "__main__":
    main()
