import os
import sys
import re
import asyncio
import datetime
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
    from discord import app_commands
except ImportError:
    print("❌ Thư viện 'discord.py' chưa được cài đặt! Hãy chạy: pip install discord.py")
    sys.exit(1)

from codebase.quiz_manager import process_quiz_answer, get_active_quiz, get_student_points_summary, record_student_submission
from codebase.question_manager import record_student_question
from codebase.llm import generate_rag_answer
from codebase.app import ROSTER, normalize


load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "").strip()
GUILD_ID = os.getenv("DISCORD_GUILD_ID", "").strip()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


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


def find_student_by_query(query: str):
    """Tìm thông tin học viên theo từ khóa (Mã HV hoặc Tên)."""
    norm_q = normalize(query)
    q_upper = query.strip().upper()

    for s in ROSTER:
        if q_upper == s["code"].upper():
            return s["name"], s["code"]
        norm_r = normalize(s["name"])
        if norm_q in norm_r or norm_r in norm_q:
            return s["name"], s["code"]

    return query, query.upper()


def build_total_points_embed(summary: dict) -> discord.Embed:
    """Tạo Embed hiển thị tổng điểm cộng của học viên."""
    name = summary["student_name"]
    code = summary["student_code"]
    total_synced = summary["total_synced"]
    total_pending = summary["total_pending"]
    synced_count = summary["synced_count"]
    records = summary["matched_records"]

    embed = discord.Embed(
        title="📊 BẢNG TỔNG ĐIỂM CỘNG HỌC VIÊN",
        color=0x2EA043 if total_synced > 0 else 0x5865F2,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.add_field(name="👤 Học viên", value=f"**{name}** (`{code}`)", inline=False)

    score_display = f"**+{total_synced} điểm**" if total_synced > 0 else "**0 điểm**"
    count_display = f" *(qua {synced_count} lượt)*" if synced_count > 0 else ""
    embed.add_field(name="🏆 Tổng điểm đã đồng bộ", value=f"{score_display}{count_display}", inline=True)

    if total_pending > 0:
        embed.add_field(name="⏳ Điểm chờ duyệt", value=f"**+{total_pending} điểm** ({summary['pending_count']} lượt)", inline=True)

    if records:
        recent_text = ""
        for r in reversed(records[-5:]):
            score_val = r.get("final_score", 0)
            score_str = f"+{int(score_val)}" if score_val == int(score_val) else f"+{score_val}"
            status_icon = "✅" if r.get("status") == "Đã đồng bộ" else "⏳"
            note = r.get("coach_note", "Điểm cộng")
            ts = r.get("timestamp", "").split(" ")[0]
            recent_text += f"{status_icon} **{score_str} điểm** - *{note}* ({ts})\n"

        if recent_text:
            embed.add_field(name="📝 Lịch sử ghi nhận gần nhất", value=recent_text[:1024], inline=False)
    else:
        embed.add_field(name="ℹ️ Ghi chú", value="Học viên chưa có điểm cộng nào được ghi nhận.", inline=False)

    embed.set_footer(text="VLearn Lab Coach System • Cổng Tra Cứu")
    return embed


def build_record_submission_embed(student_name: str, student_code: str, question: str, answer: str, note: str = "") -> discord.Embed:
    """Tạo Embed hiển thị thông báo đã gửi câu hỏi & tóm tắt câu trả lời lên Web Dashboard."""
    embed = discord.Embed(
        title="📥 ĐÃ GỬI YÊU CẦU DUYỆT ĐIỂM +",
        description="Thông tin câu hỏi & tóm tắt câu trả lời phát biểu trên lớp đã được chuyển lên Web Dashboard cho Lab Coach.",
        color=0xD97706,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.add_field(name="👤 Học viên", value=f"**{student_name}** (`{student_code}`)", inline=False)
    embed.add_field(name="❓ Câu hỏi trên lớp", value=question[:1024], inline=False)
    embed.add_field(name="💡 Tóm tắt câu trả lời", value=answer[:1024], inline=False)
    if note:
        embed.add_field(name="📝 Ghi chú", value=note[:1024], inline=False)
    embed.add_field(name="📌 Trạng thái", value="`Chờ duyệt` (Lab Coach đang đối soát)", inline=False)
    embed.set_footer(text="VLearn Lab Coach System • Cổng Tra Cứu")
    return embed


def build_ask_submission_embed(student_name: str, student_code: str, question: str) -> discord.Embed:
    """Tạo Embed thông báo ghi nhận câu hỏi gửi tới Lab Coach."""
    embed = discord.Embed(
        title="📥 ĐÃ GỬI CÂU HỎI TỚI LAB COACH",
        description="Câu hỏi của bạn đã được chuyển tới mục **'Câu hỏi từ học viên'** trên Web Dashboard.",
        color=0x5865F2,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.add_field(name="👤 Học viên", value=f"**{student_name}** (`{student_code}`)", inline=False)
    embed.add_field(name="❓ Câu hỏi", value=question[:1024], inline=False)
    embed.add_field(name="📌 Trạng thái", value="`Chờ duyệt` (Lab Coach đang xem xét và sẽ gửi câu trả lời hoàn chỉnh qua DM)", inline=False)
    embed.set_footer(text="VLearn Lab Coach System • Hỏi Đáp Trực Tuyến")
    return embed


@tree.command(name="total", description="Hiển thị tổng điểm cộng tích lũy của bản thân cho đến thời điểm hiện tại")
async def slash_total(interaction: discord.Interaction):
    student_name, student_code = match_student(interaction.user)
    summary = get_student_points_summary(student_code=student_code, student_name=student_name)
    embed = build_total_points_embed(summary)
    await interaction.response.send_message(embed=embed)


@tree.command(name="record", description="Ghi nhận câu hỏi & tóm tắt câu trả lời trên lớp để Lab Coach duyệt điểm +")
@app_commands.describe(
    question="Nội dung câu hỏi đã trả lời trên lớp",
    answer="Tóm tắt câu trả lời bạn đã trình bày",
    note="Ghi chú thêm cho Lab Coach (Không bắt buộc)"
)
async def slash_record(
    interaction: discord.Interaction,
    question: str,
    answer: str,
    note: str = ""
):
    student_name, student_code = match_student(interaction.user)
    record_student_submission(
        student_name=student_name,
        student_code=student_code,
        question=question,
        answer=answer,
        student_note=note
    )
    embed = build_record_submission_embed(
        student_name=student_name,
        student_code=student_code,
        question=question,
        answer=answer,
        note=note
    )
    await interaction.response.send_message(embed=embed)


@tree.command(name="ask", description="Hỏi Lab Coach thắc mắc bài học và nhận câu trả lời gợi ý từ AI dựa trên giáo trình")
@app_commands.describe(
    question="Nội dung thắc mắc hoặc câu hỏi cần Lab Coach giải đáp"
)
async def slash_ask(
    interaction: discord.Interaction,
    question: str
):
    await interaction.response.defer()
    student_name, student_code = match_student(interaction.user)
    
    # Sinh câu trả lời RAG từ AI dựa vào tài liệu bài giảng và lưu DB cho Lab Coach xem trên Dashboard
    ai_ans, rag_chunks = generate_rag_answer(question)
    
    record_student_question(
        student_name=student_name,
        student_code=student_code,
        question=question,
        ai_answer=ai_ans,
        rag_sources=rag_chunks,
        discord_user_id=str(interaction.user.id),
        discord_username=str(interaction.user)
    )
    
    embed = build_ask_submission_embed(
        student_name=student_name,
        student_code=student_code,
        question=question
    )
    await interaction.followup.send(embed=embed)




@client.event
async def on_ready():
    print("=" * 60, flush=True)
    print(f"🤖 Discord Bot Listener đã sẵn sàng! Logged in as: {client.user} (ID: {client.user.id})", flush=True)
    if CHANNEL_ID:
        print(f"📌 Đang lắng nghe kênh Channel ID: {CHANNEL_ID}", flush=True)
    else:
        print("⚠️ Chưa cấu hình DISCORD_CHANNEL_ID trong .env! Bot sẽ lắng nghe tất cả kênh bot có quyền đọc.", flush=True)

    try:
        target_guild_id = GUILD_ID
        if not target_guild_id and CHANNEL_ID:
            try:
                ch = await client.fetch_channel(int(CHANNEL_ID))
                if ch and hasattr(ch, "guild") and ch.guild:
                    target_guild_id = ch.guild.id
            except Exception as ex:
                print(f"⚠️ Không thể fetch channel guild: {ex}", flush=True)

        if target_guild_id:
            guild_obj = discord.Object(id=int(target_guild_id))
            # 1. Sao chép lệnh global sang guild trước khi đồng bộ
            tree.copy_global_to(guild=guild_obj)
            synced = await tree.sync(guild=guild_obj)

            # 2. Xóa các lệnh global trên Discord Server API để tránh trùng lặp gợi ý
            try:
                empty_tree = app_commands.CommandTree(client)
                await empty_tree.sync()
            except Exception:
                pass

            print(f"⚡ Đã đồng bộ {len(synced)} lệnh Slash Command duy nhất cho Server Guild ID {target_guild_id}!", flush=True)
        else:
            synced_total = 0
            for g in client.guilds:
                tree.copy_global_to(guild=g)
                s = await tree.sync(guild=g)
                synced_total += len(s)
            print(f"⚡ Đã đồng bộ Slash Command cho {len(client.guilds)} Server!", flush=True)
    except Exception as e:
        print(f"ℹ️ Trạng thái Slash Command Sync: {e}", flush=True)
    print("=" * 60, flush=True)


@client.event
async def on_message(message: discord.Message):
    # Bỏ qua tin nhắn do chính Bot gửi
    if message.author.bot:
        return

    # Lọc đúng Channel ID nếu có cấu hình
    if CHANNEL_ID and str(message.channel.id) != CHANNEL_ID:
        return

    raw_text = message.content.strip()

    # 1. Xử lý lệnh /total (Chỉ cho phép tra cứu điểm của chính bản thân)
    if raw_text.lower().startswith("/total"):
        student_name, student_code = match_student(message.author)
        summary = get_student_points_summary(student_code=student_code, student_name=student_name)
        embed = build_total_points_embed(summary)
        await message.reply(embed=embed)
        return

    # 1.5 Xử lý lệnh /record dạng text: /record câu hỏi | tóm tắt câu trả lời | [ghi chú]
    if raw_text.lower().startswith("/record"):
        content_args = raw_text[7:].strip()
        parts = [p.strip() for p in content_args.split("|") if p.strip()]
        if len(parts) >= 2:
            q_text = parts[0]
            a_text = parts[1]
            n_text = parts[2] if len(parts) > 2 else ""
            student_name, student_code = match_student(message.author)
            record_student_submission(
                student_name=student_name,
                student_code=student_code,
                question=q_text,
                answer=a_text,
                student_note=n_text
            )
            embed = build_record_submission_embed(
                student_name=student_name,
                student_code=student_code,
                question=q_text,
                answer=a_text,
                note=n_text
            )
            await message.reply(embed=embed)
        else:
            help_msg = (
                "⚠️ **Cú pháp chưa đúng!**\n"
                "• Sử dụng lệnh Slash `/record` với các ô nhập liệu **question**, **answer**, **note**.\n"
                "• Hoặc gõ: `/record <câu hỏi> | <tóm tắt câu trả lời> | [ghi chú]`"
            )
            await message.reply(help_msg)
        return

    # 1.6 Xử lý lệnh /ask dạng text: /ask <nội dung câu hỏi>
    if raw_text.lower().startswith("/ask"):
        q_content = raw_text[4:].strip()
        if q_content:
            student_name, student_code = match_student(message.author)
            ai_ans, rag_chunks = generate_rag_answer(q_content)
            record_student_question(
                student_name=student_name,
                student_code=student_code,
                question=q_content,
                ai_answer=ai_ans,
                rag_sources=rag_chunks,
                discord_user_id=str(message.author.id),
                discord_username=str(message.author)
            )
            embed = build_ask_submission_embed(
                student_name=student_name,
                student_code=student_code,
                question=q_content
            )

            await message.reply(embed=embed)
        else:
            help_msg = (
                "⚠️ **Cú pháp chưa đúng!**\n"
                "• Sử dụng lệnh Slash `/ask question=<Nội dung câu hỏi>`.\n"
                "• Hoặc gõ: `/ask <Nội dung câu hỏi>`"
            )
            await message.reply(help_msg)
        return



    # 2. Xử lý trả lời Quiz trắc nghiệm
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
            f"🏆 Phần thưởng: **+{reward:.1f} điểm cộng** đã tự động ghi nhận vào Cổng Tra Cứu (`{student_code}`)."
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

    print("🚀 Đang khởi chạy Discord Bot Listener...")
    client.run(BOT_TOKEN)

