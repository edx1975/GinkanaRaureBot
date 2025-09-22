import logging
import asyncio
from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configura el log
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Data objectiu
TARGET_DATE = datetime(2025, 9, 28, 11, 0, 0)

async def countdown_task(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
    while True:
        now = datetime.now()
        remaining = TARGET_DATE - now

        if remaining.total_seconds() > 0:
            days = remaining.days
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            countdown = (
                f"<b>{days} dies</b>\n"
                f"<b>{hours} hores</b>\n"
                f"<b>{minutes} minuts</b>\n"
                f"<b>{seconds} segons</b>"
            )
        else:
            countdown = "🎉 Ja ha començat la Ginkana!"

        message = (
            "<b>🎉 Ginkana de la Fira del Raure 🎉</b>\n\n"
            "⏳ Compte enrere fins diumenge 28 de setembre de 2025 a les 11h:\n"
            f"{countdown}\n\n"
            "🔗 El Bot de la Ginkana serà accessible aquí: <b>@Gi*************Bot</b>\n"
            "ℹ️ L'enllaç al bot es mostrarà el diumenge 28 de setembre de 2025 a les 11h."
        )

        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logging.warning(f"No s'ha pogut actualitzar el missatge: {e}")

        if remaining.total_seconds() <= 0:
            break

        await asyncio.sleep(60)  # Actualitza cada minut

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Envia un missatge inicial
    sent_message = await update.message.reply_text(
        "Iniciant compte enrere...", parse_mode=ParseMode.HTML
    )

    # Llança la tasca d'actualització en segon pla
    context.application.create_task(
        countdown_task(context, update.effective_chat.id, sent_message.message_id)
    )


def main():
    # Substitueix pel teu token de BotFather
    TOKEN = "7914578668:AAGeqije0MbzGrdj4PGxsucRyn2hc-WcXUM"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("Bot en marxa...")
    app.run_polling()

if __name__ == "__main__":
    main()
