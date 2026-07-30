import os
import sys
import re
import asyncio
from dotenv import load_dotenv

# Reconfigure stdout for Windows console UTF-8 support
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


try:
    import discord
except ImportError:
    print("❌ Thư viện 'discord.py' chưa được cài đặt! Hãy chạy: pip install discord.py")
    sys.exit(1)

from codebase.quiz_manager import process_quiz_answer, get_active_quiz
from codebase.app import ROSTER, normalize

load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "").strip()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def match_student(author: discord.User | discord.Member):
    """Ánh xạ tài khoản Discord sang thông tin học viên trong ROSTER."""
    disp_name = normalize(author.display_name)
    user_name = normalize(author.name)

    # 1. Tìm khớp trực tiếp trong Roster
    for s in ROSTER:
        norm_r = normalize(s["name"])
        if norm_r in disp_name or norm_r in user_name or disp_name in norm_r:
            return s["name"], s["code"]

    # 2. Fallback dùng tên hiển thị trên Discord
    return author.display_name, f"DISCORD_{author.name.upper()}"

@client.event
async def on_ready():
    print("=" * 60)
    print(f"🤖 Discord Bot Listener đã sẵn sàng! Logged in as: {client.user} (ID: {client.user.id})")
    if CHANNEL_ID:
        print(f"📌 Đang lắng nghe kênh Channel ID: {CHANNEL_ID}")
    else:
        print("⚠️ Chưa cấu hình DISCORD_CHANNEL_ID trong .env! Bot sẽ lắng nghe tất cả kênh bot có quyền đọc.")
    print("=" * 60)

@client.event
async def on_message(message: discord.Message):
    # Bỏ qua tin nhắn do chính Bot gửi
    if message.author.bot:
        return

    # Lọc đúng Channel ID nếu có cấu hình
    if CHANNEL_ID and str(message.channel.id) != CHANNEL_ID:
        return

    raw_text = message.content.strip()
    # Loại bỏ đề cập @bot (mentions)
    clean_text = re.sub(r'<@!?\d+>', '', raw_text).strip().upper()

    # Bỏ các từ thừa như "đáp án a", "chọn a", "câu a" -> "A"
    m = re.search(r'\b([A-D])\b', clean_text)
    if not m:
        return

    selected_option = m.group(1)

    # Kiểm tra xem có Quiz nào đang diễn ra không
    active_quiz = get_active_quiz()
    if not active_quiz or active_quiz.get("status") != "Đang diễn ra":
        return

    student_name, student_code = match_student(message.author)

    # Xử lý chấm điểm & khóa câu hỏi
    is_success, msg, quiz_data = process_quiz_answer(
        student_name=student_name,
        student_code=student_code,
        answer_option=selected_option
    )

    if is_success:
        reward = quiz_data.get("reward_score", 1.0)
        topic = quiz_data.get("topic", "AI/ML")
        
        reply_text = (
            f"🎉 **CHÚC MỪNG {message.author.mention}!**\n"
            f"Bạn đã trả lời **ĐÚNG ({selected_option}) & NHANH NHẤT** câu đố trắc nghiệm chủ đề **{topic}**!\n"
            f"🏆 Phần thưởng: **+{reward:.1f} điểm cộng** đã tự động ghi nhận vào Cổng Tra Cứu Minh Bạch (`{student_code}`)."
        )
        await message.reply(reply_text)
    else:
        # Nếu trả lời sai
        if "chưa chính xác" in msg:
            await message.reply(f"❌ Rất tiếc {message.author.mention}, đáp án **{selected_option}** chưa chính xác! Các bạn khác tiếp tục thử sức nhé.")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ LỖI: Chưa cấu hình DISCORD_BOT_TOKEN trong file .env!")
        sys.exit(1)

    print("🚀 Đang khởi chạy Discord Bot Listener Listener...")
    client.run(BOT_TOKEN)
