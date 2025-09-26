import asyncio
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# ----------------------------
# CONFIGURACIÓ
# ----------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_RAURE")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ La variable d'entorn TELEGRAM_TOKEN_RAURE no està definida")

MADRID_TZ = ZoneInfo("Europe/Madrid")
TARGET_DATE = datetime(2025, 9, 28, 11, 0, 0, tzinfo=MADRID_TZ)

registered_chats = {}
IMATGE_PATH = "image.png"

INFO_TEXT = (
    "🔗 El Bot de la Ginkana serà accessible aqui\n"
    "   /start : @Gi*************Bot\n\n"
    "* L'enllaç al JOC es mostrarà el diumenge 28 de setembre de 2025 a les 11h.\n"
    "* Aneu formant equips de 2 a 6 persones.\n"
    "* La Ginkana constarà de 3 blocs de 10 proves.\n"
    "* Diumenge a les 11h fareu la inscripció.\n"
    "* La Gran Ginkana acabarà el mateix diumenge a les 19:02h.\n"
    "* Els guanyadors tindran l'honor de ser els primers en guanyar per primer cop la Gran Ginkana, i a més, s'emportaran una Gran Cistella de Productes locals!\n"
    "* La inscripció és gratuïta.\n"
    "* Mentrestant, aqui tens info de la Fira Raure:\n"
    "   /raure2025\n\n"
    "Lo Corral AC"
)

# ----------------------------
# FUNCIONS COMPTE ENRERE
# ----------------------------
def generar_countdown():
    now = datetime.now(MADRID_TZ)
    remaining = TARGET_DATE - now
    if remaining.total_seconds() > 0:
        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        countdown = (
            f"       ⏳ {days} dies\n"
            f"       ⏰ {hours} hores\n"
            f"       ⏱️ {minutes} minuts\n"
            f"       ⏲️ {seconds} segons"
        )
        return (
            f"🎉 <b>GRAN GINKANA DE LA FIRA RAURE DE GINESTAR 2025</b> 🎉\n\n"
            f"⏳ Compte enrere fins diumenge 28 de setembre de 2025 a les 11h:\n"
            f"{countdown}\n\n"
            f"{INFO_TEXT}"
        )
    else:
        return generar_final()


def generar_final():
    return (
        "🎉 <b>Ginkana de la Fira Raure</b> 🎉\n"
        "/raure2025 per veure horaris de la fira\n\n"
        "⏳ El compte enrere ha finalitzat!\n\n"
        "🔗 El JOC de la Ginkana és a aquest altre canal de Telegram: <b>@GinkanaGinestarBOT</b>\n\n"
    )

# ----------------------------
# FUNCIO GENERAL PER ENVIAR MISSATGE
# ----------------------------
async def enviar_benviguda(chat_id, context, text_func):
    text = text_func()
    with open(IMATGE_PATH, "rb") as f:
        msg = await context.bot.send_photo(
            chat_id=chat_id,
            photo=f,
            caption=text,
            parse_mode=constants.ParseMode.HTML,
        )
    registered_chats[chat_id] = msg.message_id

# ----------------------------
# HANDLERS
# ----------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.message.text and update.message.text.startswith("/rebooom"):
        return
    await enviar_benviguda(chat_id, context, generar_countdown)


async def rebooom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await enviar_benviguda(chat_id, context, generar_final)


# ----------------------------
# USUARIS CONNECTATS
# ----------------------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👥 Usuaris registrats: {len(registered_chats)}")

# ----------------------------
# FUNCIONS D’ACTUALITZACIÓ COUNTDOWN
# ----------------------------
async def enviar_recordatori(context: ContextTypes.DEFAULT_TYPE):
    text = generar_countdown()
    for chat_id in registered_chats.keys():
        try:
            with open(IMATGE_PATH, "rb") as f:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=text,
                    parse_mode=constants.ParseMode.HTML,
                )
        except Exception as e:
            logger.warning(f"No s'ha pogut enviar recordatori a {chat_id}: {e}")


last_texts = {}  # per evitar "Message is not modified"

async def actualitzar_countdown(app: Application):
    """Actualitza el compte enrere cada minut editant la caption"""
    while True:
        text = generar_countdown()
        for chat_id, msg_id in registered_chats.items():
            if msg_id is None:
                continue
            if last_texts.get(chat_id) == text:
                continue  # evita error "Message is not modified"
            try:
                await app.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=msg_id,
                    caption=text,
                    parse_mode=constants.ParseMode.HTML,
                )
                last_texts[chat_id] = text
            except Exception as e:
                logger.warning(f"No s'ha pogut actualitzar el compte enrere a {chat_id}: {e}")
        await asyncio.sleep(60)

# ----------------------------
# HANDLER RAURE2025
# ----------------------------
async def raure2025(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📅 <b>PROGRAMA FIRA RAURE 2025</b>\n"
        "Diumenge, 28 de setembre\n\n"
        "⏰ 10:00H Obertura de la XVI Fira Raure\n"
        "🪡 10:00H-12H XVII Trobada de Puntaires\n"
        "🏃‍♀️ 11:00H-19:02H Ginkana Fira Raure 2025\n"
        "🎶 12:30H Vermut Electrònic amb <i>Diberty Musica</i>\n\n"
        "🎺 *** Durant tot el matí cercavila a càrrec de Musicam Turba***\n\n"
        "🍽️ 13:30H Fideuada Popular\n"
        "🎭 17:00H L'hora dels Joglars (Animació infantil)\n"
        "✨ 19:30H Espectacle \"L'encanteri dels Trobadors\"\n"
        "🎉 21:00H Cloenda de la XVI Fira Raure 2025\n\n"
        "🖼 *** Durant tot el dia: Exposició a l'Església Vella "
        "\"Camins Històrics i Tradicionals\"***"
    )
    await update.message.reply_text(
        text,
        parse_mode=constants.ParseMode.HTML,
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await enviar_benviguda(chat_id, context, generar_countdown)

# ----------------------------
# MAIN
# ----------------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Afegir handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("raure2025", raure2025))
    app.add_handler(CommandHandler("rebooom", rebooom))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Scheduler per recordatoris
    scheduler = AsyncIOScheduler(timezone=MADRID_TZ)
    scheduler.add_job(
        enviar_recordatori,
        CronTrigger(day_of_week="sat,sun", hour=10, minute=0, timezone=MADRID_TZ),
        args=[app],
    )
    scheduler.start()

    # Crear tasca del countdown automàticament
    app.create_task(actualitzar_countdown(app))

    logger.info("🚀 Bot de compte enrere en marxa...")
    app.run_polling()


if __name__ == "__main__":
    main()
