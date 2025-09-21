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
def normalize_id(id_raw: str) -> str:
    """Normalitza un id: si és numèric retorna str(int(id)), si no, retorna trim() tal qual."""
    s = str(id_raw).strip()
    if s == "":
        return s
    try:
        return str(int(s))
    except Exception:
        return s

def carregar_proves():
    proves = {}
    if os.path.exists(PROVES_CSV):
        with open(PROVES_CSV, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_id = row.get("id", "").strip()
                if raw_id == "":
                    continue
                key = normalize_id(raw_id)
                # guardem la fila sencera; la clau ja està normalitzada
                proves[key] = row
    return proves

def carregar_equips():
    equips = {}
    if os.path.exists(EQUIPS_CSV):
        with open(EQUIPS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # normalitzem portaveu (li treiem '@' si hi és i ho fem minúscula)
                port = row.get("portaveu", "").strip()
                if port.startswith("@"):
                    port = port[1:]
                port = port.lower()
                # assumim que jugadors estan en una sola cel·la separats per coma
                jugadors_field = row.get("jugadors", "")
                jugadors = [j.strip() for j in jugadors_field.split(",") if j.strip()]
                equips[row["equip"]] = {
                    "portaveu": port,
                    "jugadors": jugadors
                }
    return equips

def guardar_equip(equip, portaveu, jugadors_llista):
    hora = datetime.datetime.now().strftime("%H:%M")
    exists = os.path.exists(EQUIPS_CSV)
    # guardem portaveu sense '@' i en minúscules si possible
    portaveu_to_store = (portaveu or "").lstrip("@")
    with open(EQUIPS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["equip","portaveu","jugadors","hora_inscripcio"])
        writer.writerow([equip, portaveu_to_store, ",".join(jugadors_llista), hora])

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
    tipus = prova.get("tipus", "")
    correct_answer = prova.get("resposta", "")
    try:
        punts = int(prova.get("punts", 0))
    except Exception:
        punts = 0

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
        "👋 Benvingut a la Gran Ginkana!\n\n"
        "📖 Comandes útils:\n"
        "/ajuda - veure menú d'ajuda\n"
        "/inscriure NomEquip nom1,nom2,nom3 - registrar el teu equip\n"
        "/proves - veure llista de proves\n"
        "/ranking - veure puntuacions\n\n"
        "📣 Per respondre una prova envia:\n"
        "resposta <número> <resposta>  (o /resposta <número> <resposta>)"
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📚 Menú d'ajuda:\n\n"
        "Inscripció: /inscriure NomEquip nom1,nom2,nom3\n"
        "Llista de proves: /proves\n"
        "Classificació: /ranking\n\n"
        "Per contestar: escriu 'resposta 1 text' o '/resposta 1 text'."
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
    # preferim username; si no hi ha username guardem first_name
    user = update.message.from_user
    portaveu = user.username if user.username else (user.first_name or "")
    guardar_equip(equip, portaveu, jugadors_llista)
    await update.message.reply_text(f"✅ Equip '{equip}' registrat amb portaveu @{portaveu} i jugadors: {', '.join(jugadors_llista)}")

async def llistar_proves(update: Update, context: ContextTypes.DEFAULT_TYPE):
    proves = carregar_proves()
    if not proves:
        await update.message.reply_text("No hi ha proves carregades.")
        return
    msg = "📋 Llista de proves:\n"
    # Ordena per id numeric si es pot
    try:
        sorted_items = sorted(proves.items(), key=lambda x: int(x[0]))
    except Exception:
        sorted_items = sorted(proves.items(), key=lambda x: x[0])
    for pid, prova in sorted_items:
        # Usem prova['id'] original si vols mostrar exactament com està al CSV
        display_id = prova.get("id", pid)
        msg += f"{display_id}. {prova.get('titol','(sense títol)')} ({prova.get('tipus','')}) - {prova.get('punts','0')} punts\n"
    await update.message.reply_text(msg)

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    equips_punts = {}
    if os.path.exists(PUNTS_CSV):
        with open(PUNTS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("estat") == "VALIDADA":
                    equips_punts[row["equip"]] = equips_punts.get(row["equip"], 0) + int(row.get("punts", 0))
    if not equips_punts:
        await update.message.reply_text("No hi ha punts registrats encara.")
        return
    sorted_equips = sorted(equips_punts.items(), key=lambda x: x[1], reverse=True)
    msg = "🏆 Classificació provisional:\n\n"
    for i, (equip, punts) in enumerate(sorted_equips, start=1):
        msg += f"{i}. {equip} - {punts} punts\n"
    await update.message.reply_text(msg)

# ----------------------------
# Resposta: lògica comuna
# ----------------------------
async def process_resposta(update: Update, context: ContextTypes.DEFAULT_TYPE, prova_id_raw: str, resposta_text: str):
    prova_id = normalize_id(prova_id_raw)
    proves = carregar_proves()

    if prova_id not in proves:
        # missatge amb info útil per depurar
        disponibles = ", ".join(sorted(proves.keys()))
        await update.message.reply_text(
            "❌ Prova no trobada.\n"
            f"Has enviat ID: '{prova_id_raw}' (normalitzat a '{prova_id}').\n"
            f"IDs disponibles: {disponibles if disponibles else '(cap prova carregada)'}\n"
            "Assegura't d'enviar el número tal com surt a /proves (ex: 1 o 01)."
        )
        return

    # Només portaveu pot respondre
    user = update.message.from_user
    user_ident = (user.username if user.username else (user.first_name or "")).lower()
    equips = carregar_equips()
    equip = None
    for e, info in equips.items():
        if info.get("portaveu", "").lower() == user_ident:
            equip = e
            break

    if not equip:
        await update.message.reply_text("❌ Només el portaveu de l’equip pot enviar respostes.")
        return

    if ja_resposta(equip, prova_id):
        await update.message.reply_text(f"⚠️ L'equip '{equip}' ja ha respost la prova {prova_id}.")
        return

    prova = proves[prova_id]
    punts, estat = validate_answer(prova, resposta_text)
    guardar_submission(equip, prova_id, resposta_text, punts, estat)

    await update.message.reply_text(f"✅ Resposta registrada per l'equip '{equip}': {estat}. Punts: {punts}")

# ----------------------------
# Handler respostes (missatge pla: "resposta 1 text")
# ----------------------------
async def resposta_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if not text.lower().startswith("resposta"):
        return

    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Format correcte: resposta <id> <text>")
        return

    prova_id_raw = parts[1]
    resposta_text = parts[2]
    await process_resposta(update, context, prova_id_raw, resposta_text)

# ----------------------------
# Handler respostes via comanda "/resposta 1 text"
# ----------------------------
async def resposta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Format correcte: /resposta <id> <text>")
        return
    prova_id_raw = context.args[0]
    resposta_text = " ".join(context.args[1:])
    await process_resposta(update, context, prova_id_raw, resposta_text)

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
    # afegim handler per la comanda /resposta
    app.add_handler(CommandHandler("resposta", resposta_command))
    # i també per missatges de text plans que comencin per "resposta"
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, resposta_handler))

    print("✅ Bot Ginkana en marxa...")
    app.run_polling()

if __name__ == "__main__":
    main()
