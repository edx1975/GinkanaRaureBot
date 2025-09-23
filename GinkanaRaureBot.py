import logging
import asyncio
import os
from datetime import datetime as dt
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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_RAURE")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ La variable d'entorn TELEGRAM_TOKEN_RAURE no està definida")

MADRID_TZ = ZoneInfo("Europe/Madrid")
TARGET_DATE = dt(2025, 9, 28, 11, 0, 0, tzinfo=MADRID_TZ)

registered_chats = set()
IMATGE_PATH = "imatge.jpg"  # Ruta de la imatge local

# ----------------------------
# FUNCIONS COMPTE ENRERE
# ----------------------------
def generar_countdown():
    now = dt.now(MADRID_TZ)
    remaining = TARGET_DATE - now
    extra_text = (
        "\n\n🔗 El Bot de la Ginkana serà accessible aquí: @Gi*************Bot\n\n"
        "* L'enllaç al JOC es mostrarà el diumenge 28 de setembre de 2025 a les 11h.\n"
        "* Aneu formant equips de 2 a 6 persones.\n"
        "* La Ginkana constarà de 3 blocs de 10 proves.\n"
        "* Diumenge a les 11h fareu la inscripció.\n"
        "* La Gran Ginkana acabarà el mateix diumenge a les 19:02h.\n"
        "* Els guanyadors tindran l'honor de ser els primers en guanyar per primer cop la Gran Ginkana, i a més, s'emportaran una Gran Cistella de Productes locals!\n"
        "* La inscripció és gratuïta."
    )

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
            f"{countdown}"
            f"{extra_text}"
        )
    else:
        return generar_final()

def generar_final():
    return (
        "🎉 <b>Ginkana de la Fira del Raure</b> 🎉\n\n"
        "⏳ El compte enrere ha finalitzat!\n\n"
        "🔗 El JOC de la Ginkana és: <b>@GinkanaGinestarBot</b>\n"
        "Accediu-hi per inscriure-us i començar la Ginkana!"
    )

# ----------------------------
# HANDLERS
# ----------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    registered_chats.add(chat_id)

    if os.path.exists(IMATGE_PATH):
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=open(IMATGE_PATH, "rb"),
            caption=generar_countdown(),
            parse_mode=constants.ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            generar_countdown(),
            parse_mode=constants.ParseMode.HTML,
        )

async def rebooom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    registered_chats.add(chat_id)

    if os.path.exists(IMATGE_PATH):
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=open(IMATGE_PATH, "rb"),
            caption=generar_final(),
            parse_mode=constants.ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            generar_final(),
            parse_mode=constants.ParseMode.HTML,
        )

async def enviar_recordatori(context: ContextTypes.DEFAULT_TYPE):
    message = generar_countdown()
    for chat_id in registered_chats:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=constants.ParseMode.HTML,
            )
        except Exception as e:
            logging.warning(f"No s'ha pogut enviar recordatori a {chat_id}: {e}")

async def actualitzar_countdown(app):
    while True:
        message = generar_countdown()
        for chat_id in registered_chats:
            try:
                await app.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=constants.ParseMode.HTML,
                )
            except Exception as e:
                logging.warning(f"No s'ha pogut actualitzar el compte enrere a {chat_id}: {e}")
        await asyncio.sleep(60)

# ----------------------------
# MAIN
# ----------------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.add_handler(CommandHandler("rebooom", rebooom))

    scheduler = AsyncIOScheduler(timezone=MADRID_TZ)
    scheduler.add_job(
        enviar_recordatori,
        CronTrigger(day_of_week="sat,sun", hour=10, minute=0, timezone=MADRID_TZ),
        args=[app],
    )
    scheduler.start()

    asyncio.create_task(actualitzar_countdown(app))

    logging.info("🚀 Bot de compte enrere en marxa...")
    app.run_polling()

if __name__ == "__main__":
    main()
