import os
import csv
import datetime
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ----------------------------
# Variables d'entorn
# ----------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    print("❌ Falta la variable d'entorn TELEGRAM_TOKEN")
    exit(1)

if not OPENAI_API_KEY:
    print("❌ Falta la variable d'entorn OPENAI_API_KEY")
    exit(1)

openai.api_key = OPENAI_API_KEY

# ----------------------------
# Fitxers CSV
# ----------------------------
PROVES_CSV = os.getenv("GINKANA_PROVES_CSV", "./proves_ginkana.csv")
EQUIPS_CSV = os.getenv("GINKANA_EQUIPS_CSV", "./equips.csv")
PUNTS_CSV = os.getenv("GINKANA_PUNTS_CSV", "./punts_equips.csv")

# ----------------------------
# Helpers
# ----------------------------
def carregar_proves():
    proves = {}
    if os.path.exists(PROVES_CSV):
        with open(PROVES_CSV, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalitza l'ID perquè 01, 1 o 001 siguin el mateix
                proves[str(int(row["id"]))] = row    return proves

def carregar_equips():
    equips = {}
    if os.path.exists(EQUIPS_CSV):
        with open(EQUIPS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                equips[row["equip"]] = {
                    "portaveu": row["portaveu"],
                    "jugadors": [j.strip() for j in row["jugadors"].split(",") if j.strip()]
                }
    return equips

def guardar_equip(equip, portaveu, jugadors_llista):
    hora = datetime.datetime.now().strftime("%H:%M")
    exists = os.path.exists(EQUIPS_CSV)
    with open(EQUIPS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["equip","portaveu","jugadors","hora_inscripcio"])
        writer.writerow([equip, portaveu, ",".join(jugadors_llista), hora])

def guardar_submission(equip, prova_id, resposta, punts, estat):
    exists = os.path.exists(PUNTS_CSV)
    with open(PUNTS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["equip","prova_id","resposta","punts","estat"])
        writer.writerow([equip, prova_id, resposta, punts, estat])

def ja_resposta(equip, prova_id):
    if not os.path.exists(PUNTS_CSV):
        return False
    with open(PUNTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["equip"] == equip and row["prova_id"] == prova_id:
                return True
    return False

# ----------------------------
# Validació de respostes
# ----------------------------
def validate_answer(prova, resposta):
    tipus = prova["tipus"]
    correct_answer = prova["resposta"]
    punts = int(prova["punts"])
    
    if correct_answer == "REVIEW_REQUIRED":
        return 0, "PENDENT"
    
    if tipus in ["trivia", "qr"]:
        if str(resposta).strip().lower() == str(correct_answer).strip().lower():
            return punts, "VALIDADA"
        else:
            return 0, "INCORRECTA"
    
    return 0, "PENDENT"

# ----------------------------
# Comandes
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Benvingut a la Gran Ginkana de la Fira del Raure 2025 de Ginestar!\n\n"
        "📖 Comandes útils:\n"
        "/ajuda - veure menú d'ajuda\n"
        "/inscriure NomEquip nom1,nom2,nom3 - registrar el teu equip\n"
        "/proves - veure llista de proves\n"
        "/ranking - veure puntuacions\n\n"
        "📣 Per respondre una prova envia:\n"
        "resposta <número> <resposta>"
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📚 Menú d'ajuda:\n\n"
        "Per participar, crea un equip de 2 a 6 jugadors i inscriu-lo enviant un missatge de text: /inscripció (espai) nom_jugador1,nom2,nom3 (seguit, sense espais). El jugador que inscrigui l'equip serà el portaveu i el que doni les respostes en nom de tot l'equip. Per contestar les preguntes, envia un missatge per cada una amb el seguent format: resposta (espai) número de la pregunta (espai) resposta (una sola paraula, numero o imatge). Cada pregunta es pot contestar nomes una vegada\n\n" "Presentació: /start\n" "Horaris: 09:00 Inscripcions, 10:00 Inici, 19:00 Final\n" "Inscripció: /inscriure NomEquip nom1,nom2,nom3\n" "Llista de proves: /proves\n" "Classificació: /ranking\n\n" "* Ajuda personalitzada en l´ús del Bot de Telegram a la parada del grup de Natura Lo Margalló.\n" "** Una iniciativa de Lo Corral Associació Cultural"
    )
    await update.message.reply_text(msg)

async def inscriure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Format: /inscriure NomEquip nom1,nom2,nom3")
        return
    equip = context.args[0]
    jugadors_text = " ".join(context.args[1:])
    jugadors_llista = [j.strip() for j in jugadors_text.split(",") if j.strip()]
    if not jugadors_llista:
        await update.message.reply_text("❌ Cal indicar com a mínim un jugador.")
        return
    portaveu = update.message.from_user.username or update.message.from_user.first_name
    guardar_equip(equip, portaveu, jugadors_llista)
    await update.message.reply_text(f"✅ Equip '{equip}' registrat amb portaveu @{portaveu} i jugadors: {', '.join(jugadors_llista)}")

async def llistar_proves(update: Update, context: ContextTypes.DEFAULT_TYPE):
    proves = carregar_proves()
    msg = "📋 Llista de proves:\n"
    for pid, prova in proves.items():
        msg += f"{pid}. {prova['titol']} ({prova['tipus']}) - {prova['punts']} punts\n"
    await update.message.reply_text(msg)

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    equips_punts = {}
    if os.path.exists(PUNTS_CSV):
        with open(PUNTS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["estat"] == "VALIDADA":
                    equips_punts[row["equip"]] = equips_punts.get(row["equip"],0) + int(row["punts"])
    if not equips_punts:
        await update.message.reply_text("No hi ha punts registrats encara.")
        return
    sorted_equips = sorted(equips_punts.items(), key=lambda x: x[1], reverse=True)
    msg = "🏆 Classificació provisional:\n(Classificació pendent de comprovar les imatges)\n\n"
    for i, (equip, punts) in enumerate(sorted_equips, start=1):
        msg += f"{i}. {equip} - {punts} punts\n"
    await update.message.reply_text(msg)

# ----------------------------
# Handler respostes
# ----------------------------
async def resposta_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.lower().startswith("resposta"):
        return
    
    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Format correcte: resposta <id> <text>")
        return
    
    prova_id = parts[1]
    resposta = parts[2]
    
    proves = carregar_proves()
    if prova_id not in proves:
        await update.message.reply_text("❌ Prova no trobada.")
        return

    # Només portaveu pot respondre
    user = update.message.from_user.username or update.message.from_user.first_name
    equips = carregar_equips()
    equip = None
    for e, info in equips.items():
        if info["portaveu"] == user:
            equip = e
            break
    if not equip:
        await update.message.reply_text("❌ Només el portaveu de l’equip pot enviar respostes.")
        return

    if ja_resposta(equip, prova_id):
        await update.message.reply_text(f"⚠️ L'equip '{equip}' ja ha respost la prova {prova_id}.")
        return

    prova = proves[prova_id]
    punts, estat = validate_answer(prova, resposta)
    guardar_submission(equip, prova_id, resposta, punts, estat)
    
    await update.message.reply_text(f"✅ Resposta registrada per l'equip '{equip}': {estat}. Punts: {punts}")

# ----------------------------
# Main
# ----------------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("inscriure", inscriure))
    app.add_handler(CommandHandler("proves", llistar_proves))
    app.add_handler(CommandHandler("ranking", ranking))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, resposta_handler))
    
    print("✅ Bot Ginkana en marxa...")
    app.run_polling()

if __name__ == "__main__":
    main()
