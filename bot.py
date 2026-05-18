import os
import re
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from downloader import detect_platform, download_media, get_playlist_info
from database import db

BOT_TOKEN = os.getenv("BOT_TOKEN", "8012788722:AAGP9BOM7EAzZ40upGkGxBWLJ7VGKiwGuRk")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7747890249"))  # Sizning Telegram ID ingiz

URL_PATTERN = re.compile(
    r'https?://(www\.)?(youtube\.com|youtu\.be|instagram\.com|tiktok\.com|pinterest\.com|pin\.it)',
    re.IGNORECASE
)

PLATFORM_EMOJIS = {
    "youtube": "📺",
    "instagram": "📸",
    "tiktok": "🎵",
    "pinterest": "📌",
}


# ─── COMMANDS ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username or "", user.full_name or "")

    text = (
        f"👋 Salom, {user.first_name}!\n\n"
        "📥 Men media yuklovchi botman.\n\n"
        "🔗 Quyidagi platformalardan yuklayman:\n"
        "📺 YouTube — video & audio (MP3)\n"
        "📸 Instagram — reel & post\n"
        "🎵 TikTok — video\n"
        "📌 Pinterest — video\n\n"
        "▶️ Shunchaki link yuboring!"
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Yordam*\n\n"
        "1️⃣ Link yuboring\n"
        "2️⃣ Format va sifat tanlang\n"
        "3️⃣ Yuklab olishni kuting\n\n"
        "📋 *Buyruqlar:*\n"
        "/start — Botni boshlash\n"
        "/help — Yordam\n"
        "/stats — Statistika (admin)\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_ID and user_id != ADMIN_ID:
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun.")
        return

    stats = db.get_stats()
    text = (
        "📊 *Bot Statistikasi*\n\n"
        f"👥 Jami foydalanuvchilar: `{stats['total_users']}`\n"
        f"📥 Jami yuklanmalar: `{stats['total_downloads']}`\n"
        f"📺 YouTube: `{stats['youtube']}`\n"
        f"📸 Instagram: `{stats['instagram']}`\n"
        f"🎵 TikTok: `{stats['tiktok']}`\n"
        f"📌 Pinterest: `{stats['pinterest']}`\n"
        f"🎵 Audio: `{stats['audio']}`\n"
        f"🎬 Video: `{stats['video']}`\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── URL HANDLER ─────────────────────────────────────────────────────────────

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username or "", user.full_name or "")

    url = update.message.text.strip()

    if not URL_PATTERN.search(url):
        await update.message.reply_text(
            "❌ Link qo'llab-quvvatlanmaydi.\n"
            "YouTube, Instagram, TikTok yoki Pinterest linkini yuboring."
        )
        return

    platform = detect_platform(url)
    context.user_data["url"] = url
    context.user_data["platform"] = platform

    # Playlist tekshirish (faqat YouTube)
    if platform == "youtube" and ("playlist" in url or "list=" in url):
        await handle_playlist(update, context, url)
        return

    emoji = PLATFORM_EMOJIS.get(platform, "🌐")

    if platform == "youtube":
        keyboard = [
            [
                InlineKeyboardButton("🎬 Video", callback_data="type_video"),
                InlineKeyboardButton("🎵 Audio (MP3)", callback_data="type_audio"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"{emoji} *YouTube* linki!\n\nQaysi formatda?",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    else:
        await process_download(update, context, url, platform, "video", "best")


# ─── PLAYLIST ────────────────────────────────────────────────────────────────

async def handle_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    msg = await update.message.reply_text("⏳ Playlist ma'lumotlari yuklanmoqda...")

    try:
        info = await asyncio.get_event_loop().run_in_executor(
            None, get_playlist_info, url
        )
        count = info.get("count", 0)
        title = info.get("title", "Playlist")

        context.user_data["is_playlist"] = True

        keyboard = [
            [
                InlineKeyboardButton(f"📥 Hammasini yukla ({count} ta)", callback_data="playlist_all"),
                InlineKeyboardButton("❌ Bekor", callback_data="playlist_cancel"),
            ]
        ]
        await msg.edit_text(
            f"📋 *{title}*\n\n"
            f"🎬 Videolar soni: `{count}` ta\n\n"
            f"⚠️ Hammasi yuklansa, ko'p vaqt ketishi mumkin.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
    except Exception as e:
        await msg.edit_text(f"❌ Playlist yuklanmadi: {e}")


# ─── BUTTON HANDLER ──────────────────────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    url = context.user_data.get("url")
    platform = context.user_data.get("platform")

    if not url:
        await query.edit_message_text("❌ Link topilmadi. Qaytadan yuboring.")
        return

    # Format tanlash
    if data == "type_audio":
        await query.edit_message_text("⏳ Yuklanmoqda... 🎵")
        await process_download(query, context, url, platform, "audio", "best")
        return

    if data == "type_video":
        keyboard = [
            [
                InlineKeyboardButton("📱 360p", callback_data="quality_360"),
                InlineKeyboardButton("📺 720p", callback_data="quality_720"),
                InlineKeyboardButton("🖥️ 1080p", callback_data="quality_1080"),
            ]
        ]
        await query.edit_message_text(
            "🎬 Sifat tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # Sifat tanlash
    if data.startswith("quality_"):
        quality = data.split("_")[1]  # 360, 720, 1080
        await query.edit_message_text(f"⏳ {quality}p sifatda yuklanmoqda...")
        await process_download(query, context, url, platform, "video", quality)
        return

    # Playlist
    if data == "playlist_all":
        await query.edit_message_text("⏳ Playlist yuklanmoqda... Bu biroz vaqt olishi mumkin.")
        await process_playlist_download(query, context, url)
        return

    if data == "playlist_cancel":
        await query.edit_message_text("❌ Bekor qilindi.")
        return


# ─── DOWNLOAD ────────────────────────────────────────────────────────────────

async def process_download(update_or_query, context, url, platform, media_type, quality):
    is_query = hasattr(update_or_query, "edit_message_text")

    if is_query:
        chat_id = update_or_query.message.chat_id
        user_id = update_or_query.from_user.id
    else:
        chat_id = update_or_query.message.chat_id
        user_id = update_or_query.effective_user.id

    bot = context.bot

    async def send_msg(text):
        if is_query:
            try:
                await update_or_query.edit_message_text(text)
            except Exception:
                pass
        else:
            await update_or_query.message.reply_text(text)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            file_path = await asyncio.get_event_loop().run_in_executor(
                None, download_media, url, platform, media_type, quality, tmpdir
            )

            if file_path and Path(file_path).exists():
                size_mb = Path(file_path).stat().st_size / (1024 * 1024)

                if size_mb > 50:
                    await send_msg(
                        f"❌ Fayl hajmi {size_mb:.1f} MB — Telegram 50 MB gacha qabul qiladi.\n"
                        "Pastroq sifat tanlang."
                    )
                    return

                emoji = PLATFORM_EMOJIS.get(platform, "🌐")
                type_label = "🎵 Audio" if media_type == "audio" else f"🎬 {quality}p Video"
                caption = f"{emoji} {platform.capitalize()} | {type_label} | {size_mb:.1f} MB"

                await send_msg("📤 Yuborilmoqda...")

                suffix = Path(file_path).suffix.lower()
                try:
                    if media_type == "audio" or suffix == ".mp3":
                        with open(file_path, "rb") as f:
                            await bot.send_audio(chat_id=chat_id, audio=f, caption=caption)
                    else:
                        with open(file_path, "rb") as f:
                            await bot.send_video(chat_id=chat_id, video=f, caption=caption, supports_streaming=True)
                except Exception:
                    with open(file_path, "rb") as f:
                        await bot.send_document(chat_id=chat_id, document=f, caption=caption)

                # Statistika saqlash
                db.add_download(user_id, platform, media_type)

            else:
                await send_msg("❌ Yuklab bo'lmadi. Link to'g'ri ekanligini tekshiring.")

        except Exception as e:
            err = str(e)
            if "private" in err.lower():
                await send_msg("🔒 Bu post shaxsiy (private). Yuklab bo'lmaydi.")
            elif "age" in err.lower():
                await send_msg("🔞 Yosh cheklovi bor kontent yuklanmadi.")
            elif "unavailable" in err.lower():
                await send_msg("❌ Video mavjud emas yoki o'chirilgan.")
            else:
                await send_msg(f"❌ Xato: {err[:200]}")


async def process_playlist_download(query, context, url):
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    bot = context.bot

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            from downloader import download_playlist
            files = await asyncio.get_event_loop().run_in_executor(
                None, download_playlist, url, tmpdir
            )

            if not files:
                await bot.send_message(chat_id, "❌ Playlist yuklanmadi.")
                return

            await bot.send_message(chat_id, f"📤 {len(files)} ta video yuborilmoqda...")

            for i, file_path in enumerate(files, 1):
                if Path(file_path).exists():
                    size_mb = Path(file_path).stat().st_size / (1024 * 1024)
                    if size_mb > 50:
                        await bot.send_message(chat_id, f"⚠️ {i}-video {size_mb:.1f} MB — o'tkazib yuborildi.")
                        continue
                    try:
                        with open(file_path, "rb") as f:
                            await bot.send_video(
                                chat_id=chat_id,
                                video=f,
                                caption=f"📺 {i}/{len(files)}",
                                supports_streaming=True,
                            )
                        db.add_download(user_id, "youtube", "video")
                    except Exception as e:
                        await bot.send_message(chat_id, f"❌ {i}-video xato: {e}")

            await bot.send_message(chat_id, f"✅ Playlist yuklandi! Jami: {len(files)} ta")

        except Exception as e:
            await bot.send_message(chat_id, f"❌ Xato: {e}")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    print("🤖 Bot ishga tushdi (v2.0)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
