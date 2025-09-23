import logging
import asyncio
import os
import json
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

IMATGE_PATH = "imatge.jpg"  # Ruta de la imatge local
CHATS_FILE = "chats.json"

# ----------------------------
# FUNCIONS PERSISTÈNCIA
# ----------------------------
def carregar_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_chats(chats):
    with open(CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, indent=2, ensure_ascii=False)

# Diccionari: {chat_id: message_id}
registered_chats = carregar_chats()

# ----------------------------
# FUNCIONS COMPTE ENRERE
# ----------------------------
def generar_countdown():
    now = dt.now(MADRID_TZ)
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
            f"{countdown}"
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
    chat_id = str(update.effective_chat.id)

    # Si no tenim registrat aquest xat → enviar missatge i guardar ID del missatge
    if chat_id not in registered_chats:
        if os.path.exists(IMATGE_PATH):
            with open(IMATGE_PATH, "rb") as f:
                msg = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=generar_countdown(),
                    parse_mode=constants.ParseMode.HTML,
                )
        else:
            msg = await update.message.reply_text(
                generar_countdown(),
                parse_mode=constants.ParseMode.HTML,
            )

        registered_chats[chat_id] = msg.message_id
        guardar_chats(registered_chats)

async def rebooom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if os.path.exists(IMATGE_PATH):
        with open(IMATGE_PATH, "rb") as f:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=f,
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
    for chat_id in registered_chats.keys():
        try:
            await context.bot.send_message(
                chat_id=int(chat_id),
                text=message,
                parse_mode=constants.ParseMode.HTML,
            )
        except Exception as e:
            logging.warning(f"No s'ha pogut enviar recordatori a {chat_id}: {e}")

async def actualitzar_countdown(app):
    """Actualitza el missatge del compte enrere cada minut"""
    while True:
        message = generar_countdown()
        for chat_id, message_id in registered_chats.items():
            try:
                await app.bot.edit_message_text(
                    chat_id=int(chat_id),
                    message_id=message_id,
                    text=message,
                    parse_mode=constants.ParseMode.HTML,
                )
            except Exception as e:
                logging.warning(f"No s'ha pogut editar el missatge a {chat_id}: {e}")
        await asyncio.sleep(60)

# ----------------------------
# MAIN
# ----------------------------
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Handlers
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.add_handler(CommandHandler("rebooom", rebooom))

    # Programador de tasques: dissabte i diumenge a les 10h
    scheduler = AsyncIOScheduler(timezone=MADRID_TZ)
    scheduler.add_job(
        enviar_recordatori,
        CronTrigger(day_of_week="sat,sun", hour=10, minute=0, timezone=MADRID_TZ),
        args=[app],
    )
    scheduler.start()

    # Iniciar la tasca de comptador actualitzable
    app.create_task(actualitzar_countdown(app))

    logging.info("🚀 Bot de compte enrere en marxa...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
