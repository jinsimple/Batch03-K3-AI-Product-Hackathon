import os
import re
from typing import List, Dict, Any

# Đường dẫn mặc định tới thư mục transcript
TRANSCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vlearn-pack", "transcript")

_TRANSCRIPT_CHUNKS_CACHE: List[Dict[str, Any]] = []

def load_and_index_transcripts(transcript_dir: str = TRANSCRIPT_DIR) -> List[Dict[str, Any]]:
    """
    Đọc 6 file transcript clean và tạo bộ index phân đoạn (chunks).
    Cache dữ liệu trong bộ nhớ để truy xuất nhanh.
    """
    global _TRANSCRIPT_CHUNKS_CACHE
    if _TRANSCRIPT_CHUNKS_CACHE:
        return _TRANSCRIPT_CHUNKS_CACHE

    chunks = []
    if not os.path.exists(transcript_dir):
        print(f"[RAG Manager] Warning: Transcript dir not found: {transcript_dir}")
        return chunks

    # 6 file transcript chuẩn
    target_files = [f"transcript-0{i}-clean.md" for i in range(1, 7)]

    for filename in target_files:
        filepath = os.path.join(transcript_dir, filename)
        if not os.path.exists(filepath):
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            current_section = "Nội dung bài giảng"
            lines = content.split("\n")
            
            buffer_lines = []
            current_tag = ""

            for line in lines:
                stripped = line.strip()
                if stripped.startswith("#"):
                    current_section = stripped.lstrip("#").strip()
                    continue
                
                # Bắt mã thẻ đoạn [Txx-NNN]
                tag_match = re.search(r"\*\*\[(T\d+-\d+)\]\*\*", stripped)
                if tag_match:
                    if buffer_lines and current_tag:
                        text_block = "\n".join(buffer_lines).strip()
                        if len(text_block) > 30:
                            chunks.append({
                                "file_name": filename,
                                "section": current_section,
                                "tag": current_tag,
                                "content": text_block
                            })
                    current_tag = tag_match.group(1)
                    buffer_lines = [stripped]
                else:
                    if buffer_lines:
                        buffer_lines.append(stripped)

            # Flush đoạn cuối
            if buffer_lines and current_tag:
                text_block = "\n".join(buffer_lines).strip()
                if len(text_block) > 30:
                    chunks.append({
                        "file_name": filename,
                        "section": current_section,
                        "tag": current_tag,
                        "content": text_block
                    })
        except Exception as e:
            print(f"[RAG Manager] Error reading {filename}: {e}")

    _TRANSCRIPT_CHUNKS_CACHE = chunks
    print(f"[RAG Manager] Indexing complete: {len(chunks)} chunks loaded from 6 transcript files.")
    return chunks


def retrieve_transcript_context(query_topic: str, top_k: int = 3, transcript_dir: str = TRANSCRIPT_DIR) -> List[Dict[str, Any]]:
    """
    Truy xuất các đoạn transcript liên quan nhất tới query_topic từ 6 file bài giảng.
    Sử dụng giải thuật tính điểm từ khóa / TF-IDF trọng số.
    """
    chunks = load_and_index_transcripts(transcript_dir)
    if not chunks:
        return []

    topic_clean = query_topic.strip().lower()
    if not topic_clean:
        import random
        return random.sample(chunks, min(top_k, len(chunks)))

    # Tách từ khóa
    keywords = [kw for kw in re.split(r"\W+", topic_clean) if len(kw) > 1]
    
    scored_chunks = []
    for chunk in chunks:
        score = 0.0
        text_lower = chunk["content"].lower()
        section_lower = chunk["section"].lower()

        # 1. Trùng khớp cụm từ chính xác (Exact phrase match)
        if topic_clean in text_lower:
            score += 15.0
        if topic_clean in section_lower:
            score += 20.0

        # 2. Trùng khớp từ khóa rời (Individual keywords match)
        for kw in keywords:
            count_text = text_lower.count(kw)
            count_section = section_lower.count(kw)
            score += count_text * 2.0
            score += count_section * 5.0

        if score > 0:
            scored_chunks.append((score, chunk))

    # Sắp xếp giảm dần theo score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    # Trả về top_k chunks
    results = [item[1] for item in scored_chunks[:top_k]]
    
    # Nếu không tìm thấy match trực tiếp, lấy top chunks để luôn có context
    if not results:
        results = chunks[:top_k]

    return results


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    res = retrieve_transcript_context("Overfitting", top_k=2)
    for r in res:
        print(f"[{r['file_name']} | {r['tag']}] {r['section']}\n{r['content'][:150]}...\n---")
