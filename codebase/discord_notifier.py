import os
import json
import datetime
import urllib.request
import urllib.error

# Tự động nạp biến môi trường từ .env nếu file tồn tại
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_discord_config():
    """Lấy cấu hình Discord từ biến môi trường."""
    bot_token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    channel_id = os.getenv("DISCORD_CHANNEL_ID", "").strip()
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    return bot_token, channel_id, webhook_url


def build_score_embed(
    student_name: str,
    student_code: str,
    final_score: float,
    coach_note: str,
    feedback: str = "",
    status: str = "Đã đồng bộ",
    suggested_score: float = None
) -> dict:
    """Tạo cấu trúc Discord Rich Embed chuẩn hóa cho thông báo điểm cộng."""
    is_synced = status == "Đã đồng bộ"
    
    # Màu sắc: Xanh lá (0x2EA043) cho Đã đồng bộ, Vàng cam (0xD97706) cho Chờ duyệt
    color = 0x2EA043 if is_synced else 0xD97706
    status_icon = "⭐" if is_synced else "⏳"
    title_text = f"{status_icon} THÔNG BÁO ĐIỂM THƯỞNG PHÁT BIỂU"

    fields = [
        {
            "name": "👤 Học viên",
            "value": f"**{student_name}** (`{student_code}`)",
            "inline": True
        },
        {
            "name": "🎯 Điểm cộng",
            "value": f"**+{final_score:.1f} điểm**" + (f" *(AI gợi ý: +{suggested_score:.1f})*" if suggested_score is not None else ""),
            "inline": True
        },
        {
            "name": "📌 Trạng thái",
            "value": f"`{status}`",
            "inline": True
        }
    ]

    if coach_note:
        fields.append({
            "name": "📝 Ghi chú của Coach",
            "value": coach_note[:1024],
            "inline": False
        })

    if feedback:
        fields.append({
            "name": "💬 Feedback học viên",
            "value": feedback[:1024],
            "inline": False
        })

    embed = {
        "title": title_text,
        "color": color,
        "fields": fields,
        "footer": {
            "text": "VLearn Lab Coach System • Discord Bot Notification"
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    return embed


def _post_json(url: str, payload: dict, headers: dict = None) -> tuple[int, str]:
    """Hàm gửi HTTP POST JSON sử dụng thư viện chuẩn urllib (không cần cài thêm package)."""
    headers = headers or {}
    headers.setdefault("Content-Type", "application/json")
    headers.setdefault("User-Agent", "DiscordBot (https://vlearn.vn, 1.0)")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            return status_code, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else str(e)
        return e.code, body
    except Exception as e:
        return 0, str(e)


def send_discord_score_notification(
    student_name: str,
    student_code: str,
    final_score: float,
    coach_note: str,
    feedback: str = "",
    status: str = "Đã đồng bộ",
    suggested_score: float = None,
    override_webhook: str = None
) -> tuple[bool, str]:
    """
    Gửi thông báo điểm cộng lên Discord.
    Ưu tiên 1: Bot API (DISCORD_BOT_TOKEN + DISCORD_CHANNEL_ID)
    Ưu tiên 2: Discord Webhook (DISCORD_WEBHOOK_URL hoặc override_webhook)
    Ưu tiên 3: Mock Notifier (giả lập khi không có cấu hình)
    """
    bot_token, channel_id, env_webhook = get_discord_config()
    webhook_url = override_webhook or env_webhook
    embed = build_score_embed(
        student_name=student_name,
        student_code=student_code,
        final_score=final_score,
        coach_note=coach_note,
        feedback=feedback,
        status=status,
        suggested_score=suggested_score
    )

    # 1. Gửi qua Discord Bot REST API nếu có Bot Token và Channel ID
    if bot_token and channel_id:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json"
        }
        payload = {"embeds": [embed]}
        status_code, body = _post_json(url, payload, headers)
        if status_code in [200, 201]:
            return True, "🤖 Gửi qua Discord Bot API thành công!"
        else:
            return False, f"⚠️ Lỗi Discord Bot API (HTTP {status_code}): {body}"

    # 2. Fallback gửi qua Discord Webhook nếu có Webhook URL
    if webhook_url:
        payload = {"embeds": [embed]}
        status_code, body = _post_json(webhook_url, payload)
        if status_code in [200, 204]:
            return True, "🔗 Gửi qua Discord Webhook thành công!"
        else:
            return False, f"⚠️ Lỗi Discord Webhook (HTTP {status_code}): {body}"

    # 3. Fallback Mock Notifier khi chạy Offline hoặc thiếu cấu hình
    mock_msg = f"[MOCK DISCORD BOT] Notified {status}: {student_name} ({student_code}) +{final_score} pts."
    return True, f"💡 {mock_msg} (Chưa cấu hình DISCORD_BOT_TOKEN/CHANNEL_ID hoặc WEBHOOK_URL trong .env)"


def build_quiz_embed(quiz_data: dict, reward_score: float = 1.0) -> dict:
    """Tạo Discord Rich Embed đính kèm 4 phương án lựa chọn trắc nghiệm."""
    topic = quiz_data.get("topic", "Trắc nghiệm AI/ML")
    question = quiz_data.get("question", "")
    options = quiz_data.get("options", {})

    options_text = ""
    for opt_key in ["A", "B", "C", "D"]:
        if opt_key in options:
            options_text += f"**{opt_key}.** {options[opt_key]}\n\n"

    embed = {
        "title": f"🎮 AI QUIZ TRẮC NGHIỆM: {topic.upper()}",
        "description": f"### ❓ {question}\n\n{options_text}",
        "color": 0x5865F2,  # Discord Blurple Color
        "fields": [
            {
                "name": "🎁 Phần thưởng",
                "value": f"**+{reward_score:.1f} điểm cộng** vào bảng điểm Lab Coach cho học viên trả lời **ĐÚNG & NHANH NHẤT**!",
                "inline": False
            },
            {
                "name": "📌 Hướng dẫn",
                "value": "Chọn đáp án đúng (A, B, C hoặc D) ngay trong ứng dụng hoặc phản hồi bot trên Discord.",
                "inline": False
            }
        ],
        "footer": {
            "text": "VLearn AI Quiz Engine • First-Come, First-Served Rewards"
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    return embed


def send_discord_quiz_notification(quiz_data: dict, reward_score: float = 1.0, override_webhook: str = None) -> tuple[bool, str]:
    """Gửi bài Quiz trắc nghiệm đính kèm phương án lên Discord."""
    bot_token, channel_id, env_webhook = get_discord_config()
    webhook_url = override_webhook or env_webhook
    embed = build_quiz_embed(quiz_data, reward_score=reward_score)

    if bot_token and channel_id:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
        payload = {"embeds": [embed]}
        status_code, body = _post_json(url, payload, headers)
        if status_code in [200, 201]:
            return True, "🤖 Đã phát bài Quiz trắc nghiệm lên Discord qua Bot API!"
        else:
            return False, f"⚠️ Lỗi Discord Bot API (HTTP {status_code}): {body}"

    if webhook_url:
        payload = {"embeds": [embed]}
        status_code, body = _post_json(webhook_url, payload)
        if status_code in [200, 204]:
            return True, "🔗 Đã phát bài Quiz trắc nghiệm lên Discord qua Webhook!"
        else:
            return False, f"⚠️ Lỗi Discord Webhook (HTTP {status_code}): {body}"

    mock_msg = f"[MOCK DISCORD BOT] Quiz Broadcasted: '{quiz_data.get('topic')}' (+{reward_score} pts)"
    return True, f"💡 {mock_msg} (Chưa cấu hình Token/Webhook trong `.env`)"


def send_discord_quiz_winner(student_name: str, student_code: str, topic: str, score: float = 1.0, override_webhook: str = None) -> tuple[bool, str]:
    """Gửi thông báo vinh danh người thắng cuộc lên Discord."""
    bot_token, channel_id, env_webhook = get_discord_config()
    webhook_url = override_webhook or env_webhook

    embed = {
        "title": "🏆 VINH DANH NGƯỜI THẮNG AI QUIZ!",
        "description": f"Chúc mừng học viên **{student_name}** (`{student_code}`) đã xuất sắc trả lời **ĐÚNG & NHANH NHẤT** câu đố trắc nghiệm chủ đề **{topic}**!",
        "color": 0xFEE75C,  # Gold Color
        "fields": [
            {
                "name": "🎯 Điểm phần thưởng",
                "value": f"**+{score:.1f} điểm** (Đã tự động ghi nhận vào Cổng Tra Cứu)",
                "inline": True
            }
        ],
        "footer": {
            "text": "VLearn AI Quiz Engine • System Synced"
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    if bot_token and channel_id:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
        payload = {"embeds": [embed]}
        status_code, body = _post_json(url, payload, headers)
        if status_code in [200, 201]:
            return True, f"🏆 Đã vinh danh {student_name} trên Discord!"
        else:
            return False, f"⚠️ Lỗi Discord Bot API (HTTP {status_code}): {body}"

    if webhook_url:
        payload = {"embeds": [embed]}
        status_code, body = _post_json(webhook_url, payload)
        if status_code in [200, 204]:
            return True, f"🏆 Đã vinh danh {student_name} trên Discord!"
        else:
            return False, f"⚠️ Lỗi Discord Webhook (HTTP {status_code}): {body}"

    return True, f"💡 [MOCK DISCORD] Winner Announced: {student_name} (+{score} pts)"


def send_discord_dm_or_notification(
    student_name: str,
    student_code: str,
    question: str,
    answer: str,
    discord_user_id: str = "",
    override_webhook: str = None
) -> tuple[bool, str]:
    """
    Gửi câu trả lời đã duyệt trực tiếp từ Lab Coach cho học viên đã hỏi qua tin nhắn riêng (Discord DM).
    Nếu không gửi được DM (ví dụ học viên đóng DM), sẽ fallback gửi tin nhắn thông báo tag tên trên kênh chung.
    """
    bot_token, channel_id, env_webhook = get_discord_config()
    webhook_url = override_webhook or env_webhook

    embed = {
        "title": "💬 MÔN HỌC AI/ML - PHẢN HỒI TỪ LAB COACH",
        "description": "Dưới đây là câu trả lời chính thức từ Lab Coach cho câu hỏi của bạn:",
        "color": 0x2EA043,  # Green color
        "fields": [
            {
                "name": "👤 Học viên",
                "value": f"**{student_name}** (`{student_code}`)",
                "inline": False
            },
            {
                "name": "❓ Câu hỏi của bạn",
                "value": question[:1024],
                "inline": False
            },
            {
                "name": "✅ Phản hồi chính thức từ Lab Coach",
                "value": answer[:1024],
                "inline": False
            }
        ],
        "footer": {
            "text": "VLearn Lab Coach System • Direct Student Response"
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    # 1. Nếu có bot_token và discord_user_id -> Thử tạo kênh DM và gửi tin nhắn riêng
    if bot_token and discord_user_id:
        try:
            # 1a. Tạo DM Channel với user
            dm_channel_url = "https://discord.com/api/v10/users/@me/channels"
            headers = {
                "Authorization": f"Bot {bot_token}",
                "Content-Type": "application/json"
            }
            dm_payload = {"recipient_id": str(discord_user_id)}
            status_code, body = _post_json(dm_channel_url, dm_payload, headers)
            
            if status_code in [200, 201]:
                res_data = json.loads(body)
                dm_channel_id = res_data.get("id")
                if dm_channel_id:
                    # 1b. Gửi tin nhắn Embed vào DM Channel
                    msg_url = f"https://discord.com/api/v10/channels/{dm_channel_id}/messages"
                    msg_payload = {"embeds": [embed]}
                    msg_status, msg_body = _post_json(msg_url, msg_payload, headers)
                    if msg_status in [200, 201]:
                        return True, f"📩 Đã gửi tin nhắn riêng (DM) thành công tới học viên {student_name}!"
        except Exception as e:
            print(f"[Discord DM Error]: {e}")

    # 2. Fallback: Nếu không gửi được DM hoặc không có DM channel, gửi thông báo tag user trên channel chính
    if bot_token and channel_id:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
        content_mention = f"🔔 <@{discord_user_id}> Lab Coach đã trả lời câu hỏi của bạn!" if discord_user_id else f"🔔 Học viên **{student_name}** (`{student_code}`): Lab Coach đã trả lời câu hỏi của bạn!"
        payload = {"content": content_mention, "embeds": [embed]}
        status_code, body = _post_json(url, payload, headers)
        if status_code in [200, 201]:
            return True, f"🤖 Đã gửi câu trả lời lên Kênh Discord chung (Mention {student_name})!"

    # 3. Webhook fallback
    if webhook_url:
        payload = {"embeds": [embed]}
        status_code, body = _post_json(webhook_url, payload)
        if status_code in [200, 204]:
            return True, f"🔗 Đã gửi câu trả lời qua Discord Webhook!"

    # 4. Mock fallback
    return True, f"💡 [MOCK DISCORD DM] Answer Sent to {student_name} ({student_code}): '{answer[:50]}...'"


