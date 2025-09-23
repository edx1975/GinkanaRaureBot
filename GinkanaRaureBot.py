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

# Missatge fix
fixed_message_id = None
fixed_chat_id = None


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
            "* Aneu formant equips de 2 a 6 persones."
            "* La Ginkana constarà de 3 blocs de 10 proves.\n "
            "* Diumenge a les 1hh fareu la inscripció.\n"
            "* La Gran Ginkana de la Fira del Raure de Ginestar acabarà el mateix diumenge a les 19:02h \n"
            "* Els guanyadors, tindran el gran honor de ser els primers en guanyar per primer cop la Gran Ginkana de la Fira del Raure, i a més, s'emportaran una Gran Cistella de Productes locals de la Fira! \n"
            "* La inscripció és gratuïta"
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


async def countdown_task(context: ContextTypes.DEFAULT_TYPE):
    global fixed_message_id, fixed_chat_id
    if not fixed_message_id or not fixed_chat_id:
        logging.warning("❌ Missatge fix no inicialitzat")
        return

    while True:
        message = generar_countdown()
        try:
            await context.bot.edit_message_text(
                chat_id=fixed_chat_id,
                message_id=fixed_message_id,
                text=message,
                parse_mode=constants.ParseMode.HTML,
            )
        except Exception as e:
            logging.warning(f"No s'ha pogut actualitzar el missatge: {e}")
        await asyncio.sleep(60)  # Actualitza cada minut


# ---------------------------
