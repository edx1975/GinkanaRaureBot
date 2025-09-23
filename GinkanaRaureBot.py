import logging
import asyncio
import os
from datetime import datetime as dt, time
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

# Zona horària Madrid
MADRID_TZ = ZoneInfo("Europe/Madrid")
TARGET_DATE = dt(2025, 9, 28, 11, 0, 0, tzinfo=MADRID_TZ)

# Llista de xats que ja han parlat amb el bot
registered_chats = set()

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
            f"{countdown}\n\n"
            f"🔗 El Bot de la Ginkana serà accessible aquí: <b>@Gi*************Bot</b>\n\n"
            "* L'enllaç al JOC es mostrarà el diumenge 28 de setembre de 2025 a les 11h.\n"
            "* Aneu formant equips de 2 a 6 persones.\n"
            "* La Ginkana constarà de 3 blocs de 10 proves.\n"
            "* Diumenge a les 11h fareu la inscripció.\n"
            "* La Gran Ginkana acabarà el mateix diumenge a les 19:02h.\n"
            "* Els guanyadors tindran l'honor de ser els primers en guanyar per primer cop la Gran Ginkana, i a més, s'emportaran una Gran Cistella de Productes locals!\n"
            "* La inscripció és gratuïta."
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
    """Respon amb el compte enrere a qualsevol missatge"""
    chat_id = update.effective_chat.id
    registered_chats.add(chat_id)  # Guardem el xat per futurs recordatoris
    await update.message.reply_text(
        generar_countdown(),
        parse_mode=constants.ParseMode.HTML,
    )

async def enviar_recordatori(context: ContextTypes.DEFAULT_TYPE):
    """Envia automàticament el compte enrere als xats registrats"""
    if not registered_chats:
        logging.info("ℹ️ No hi ha xats registrats per enviar recordatori.")
        return

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

async def rebooom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra el missatge final temporalment sense aturar el compte enrere"""
        logging.info(f"/rebooom rebut de {update.effective_chat.id}")
    await update.message.reply_text(
        generar_final(),
        parse_mode=constants.ParseMode.HTML
    )

# ----------------------------
# MAIN
# ----------------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Qualsevol missatge → mostrar compte enrere
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    # Comandament /rebooom
    app.add_handler(CommandHandler("rebooom", rebooom))

    # Programador de tasques
    scheduler = AsyncIOScheduler(timezone=MADRID_TZ)
    scheduler.add_job(
        enviar_recordatori,
        CronTrigger(day_of_week="sat,sun", hour=10, minute=0, timezone=MADRID_TZ),
        args=[app],
    )
    scheduler.start()

    logging.info("🚀 Bot de compte enrere en marxa...")
    app.run_polling()

if __name__ == "__main__":
    main()
