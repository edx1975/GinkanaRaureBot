import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Config
TELEGRAM_TOKEN = "EL_TEU_TOKEN"
MADRID_TZ = ZoneInfo("Europe/Madrid")

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variables globals
temps_objectiu = datetime.now(MADRID_TZ) + timedelta(minutes=1)
countdown_message_id = None
chat_id_global = None


# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id_global
    chat_id_global = update.effective_chat.id
    await update.message.reply_text("Compte enrere iniciat! 🎉")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Missatge rebut: {update.message.text}")


async def rebooom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💥 REBOOOM! 💥")


# Funcions countdown
async def actualitzar_countdown(app: Application):
    global countdown_message_id, chat_id_global
    while True:
        if chat_id_global:
            temps_rest = temps_objectiu - datetime.now(MADRID_TZ)
            if temps_rest.total_seconds() > 0:
                text = f"⏳ Temps restant: {temps_rest}"
            else:
                text = "🎉 S'ha acabat el compte enrere!"
            try:
                if countdown_message_id:
                    await app.bot.edit_message_text(
                        chat_id=chat_id_global,
                        message_id=countdown_message_id,
                        text=text,
                    )
                else:
                    msg = await app.bot.send_message(chat_id=chat_id_global, text=text)
                    countdown_message_id = msg.message_id
            except Exception as e:
                logger.error(f"Error actualitzant countdown: {e}")
        await asyncio.sleep(10)


# Recordatoris
async def enviar_recordatori(app: Application):
    if chat_id_global:
        await app.bot.send_message(chat_id=chat_id_global, text="📢 Recordatori setmanal!")


# Hook perquè el countdown s’iniciï quan el bot ja està actiu
async def iniciar_countdown(app: Application):
    app.create_task(actualitzar_countdown(app))


def main():
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(iniciar_countdown)  # 👈 Ens assegurem que el loop ja corre
        .build()
    )

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rebooom", rebooom))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    # Scheduler
    scheduler = AsyncIOScheduler(timezone=MADRID_TZ)
    scheduler.add_job(
        enviar_recordatori,
        CronTrigger(day_of_week="sat,sun", hour=10, minute=0, timezone=MADRID_TZ),
        args=[app],
    )
    scheduler.start()

    logger.info("🚀 Bot de compte enrere en marxa...")
    app.run_polling()  # ✅ Aquí gestionem el loop correctament


if __name__ == "__main__":
    main()
