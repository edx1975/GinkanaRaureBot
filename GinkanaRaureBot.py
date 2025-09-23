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
    "🔗 El Bot de la Ginkana serà accessible aquí: @Gi*************Bot\n\n"
    "* L'enllaç al JOC es mostrarà el diumenge 28 de setembre de 2025 a les 11h.\n"
    "* Aneu formant equips de 2 a 6 persones.\n"
    "* La Ginkana constarà de 3 blocs de 10 proves.\n"
    "* Diumenge a les 11h fareu la inscripció.\n"
    "* La Gran Ginkana acabarà el mateix diumenge a les 19:02h.\n"
    "* Els guanyadors tindran l'honor de ser els primers en guanyar per primer cop la Gran Ginkana, i a més, s'emportaran una Gran Cistella de Productes locals!\n"
    "* La inscripció és gratuïta.\n\n"
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
            f"🎉 <b>GRAN GINKANA DE LA FIRA DEL RAURE DE GINESTAR 2025</b> 🎉\n\n"
            f"⏳ Compte enrere fins diumenge 28 de setembre de 2025 a les 11h:\n"
            f"{countdown}\n\n"
            f"{INFO_TEXT}"
        )
    else:
        return generar_final()


def generar_final():
    return (
        "🎉 <b>Ginkana de la Fira del Raure</b> 🎉\n\n"
        "⏳ El compte enrere ha finalitzat!\n\n"
        "🔗 El JOC de la Ginkana és: <b>@GinkanaGinestarBot</b>\n\n"
    )

# ----------------------------
# HANDLERS
# ----------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if update.message.text and update.message.text.startswith("/rebooom"):
        return

    if chat_id not in registered_chats:
        registered_chats[chat_id] = None

    text = generar_countdown()

    if os.path.exists(IMATGE_PATH):
        try:
            with open(IMATGE_PATH, "rb") as f:
                msg = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=text,
                    parse_mode=constants.ParseMode.HTML,
                )
        except Exception as e:
            logger.error(f"❌ Error enviant imatge a {chat_id}: {e}")
            msg = await update.message.reply_text(
                text,
                parse_mode=constants.ParseMode.HTML,
            )
    else:
        logger.error(f"❌ No s’ha trobat la imatge: {os.path.abspath(IMATGE_PATH)}")
        msg = await update.message.reply_text(
            text,
            parse_mode=constants.ParseMode.HTML,
        )

    registered_chats[chat_id] = msg.message_id


async def rebooom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in registered_chats:
        registered_chats[chat_id] = None

    text = generar_final()

    if os.path.exists(IMATGE_PATH):
        try:
            with open(IMATGE_PATH, "rb") as f:
                msg = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=text,
                    parse_mode=constants.ParseMode.HTML,
                )
        except Exception as e:
            logger.error(f"❌ Error enviant imatge a {chat_id}: {e}")
            msg = await update.message.reply_text(
                text,
                parse_mode=constants.ParseMode.HTML,
            )
    else:
        logger.error(f"❌ No s’ha trobat la imatge: {os.path.abspath(IMATGE_PATH)}")
        msg = await update.message.reply_text(
            text,
            parse_mode=constants.ParseMode.HTML,
        )

    registered_chats[chat_id] = msg.message_id

# ----------------------------
# FUNCIONS D’ACTUALITZACIÓ COUNTDOWN
# ----------------------------
async def enviar_recordatori(context: ContextTypes.DEFAULT_TYPE):
    text = generar_countdown()
    for chat_id, msg_id in registered_chats.items():
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=constants.ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"No s'ha pogut enviar recordatori a {chat_id}: {e}")


async def actualitzar_countdown(app: Application):
    """Actualitza el compte enrere cada minut editant l'últim missatge per no spam"""
    while True:
        text = generar_countdown()
        for chat_id, msg_id in registered_chats.items():
            if msg_id is None:
                continue
            try:
                await app.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg_id,
                    text=text,
                    parse_mode=constants.ParseMode.HTML,
                )
            except Exception as e:
                logger.warning(f"No s'ha pogut actualitzar el compte enrere a {chat_id}: {e}")
        await asyncio.sleep(60)


# ----------------------------
# POST_INIT HOOK
# ----------------------------
async def iniciar_countdown(app: Application):
    app.create_task(actualitzar_countdown(app))


# ----------------------------
# MAIN
# ----------------------------
def main():
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(iniciar_countdown)
        .build()
    )

    # Handlers
    app.add_handler(CommandHandler("rebooom", rebooom))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Scheduler
    scheduler = AsyncIOScheduler(timezone=MADRID_TZ)
    scheduler.add_job(
        enviar_recordatori,
        CronTrigger(day_of_week="sat,sun", hour=10, minute=0, timezone=MADRID_TZ),
        args=[app],
    )
    scheduler.start()

    logger.info("🚀 Bot de compte enrere en marxa...")
    app.run_polling()


if __name__ == "__main__":
    main()
