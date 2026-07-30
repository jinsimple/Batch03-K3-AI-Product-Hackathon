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
