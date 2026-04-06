#!/usr/bin/env python3
# macroedge/bot_listener.py
# ================================================================
# Bot Telegram interattivo con comandi.
# Avvialo una volta per configurare i comandi, poi puoi fermarlo.
# In produzione (GitHub Actions) non serve tenerlo attivo:
# i report vengono spediti in push, non in pull.
#
# COMANDI DISPONIBILI NEL BOT:
#   /test     → messaggio di stato sistema
#   /sample   → report di esempio completo
#   /status   → stato dell'ultimo ciclo (da log)
#   /next     → quando arriva il prossimo report
#   /help     → lista comandi
#
# USO:
#   python bot_listener.py        → avvia in ascolto (Ctrl+C per fermare)
#   python bot_listener.py --set  → registra i comandi su BotFather e poi esce
# ================================================================

import asyncio
import argparse
import sys
import os
import glob
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import logging

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger("macroedge.bot_listener")


# ── Handler comandi ────────────────────────────────────────────────

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra la lista dei comandi disponibili."""
    msg = (
        "🤖 *MacroEdge Bot — Comandi*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "/test — stato del sistema\n"
        "/sample — report di esempio\n"
        "/status — ultimo ciclo eseguito\n"
        "/next — prossimo report\n"
        "/help — questo messaggio"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


async def cmd_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Invia un messaggio di stato del sistema."""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    msg = (
        f"🟢 *MacroEdge — Sistema Operativo*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Bot online e raggiungibile\n"
        f"✅ Canale Telegram configurato\n\n"
        f"📅 *Schedule attivo:*\n"
        f"  • Lunedì 07:00 → Ciclo A\n"
        f"  • Giovedì 07:00 → Ciclo B\n\n"
        f"🕐 Test eseguito: {now}"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


async def cmd_sample(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Invia un report di esempio."""
    await update.message.reply_text(
        "⏳ Generazione report di esempio...",
        parse_mode=ParseMode.MARKDOWN
    )
    # Importa e usa il modulo di test
    from test_telegram import SAMPLE_REPORT
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    # plain text per semplicità nella risposta diretta
    await update.message.reply_text(
        f"📊 *Report di esempio MacroEdge*\n\n"
        f"Questo è un anteprima del formato report che riceverai ogni lunedì e giovedì.\n\n"
        f"Contiene:\n"
        f"• Bias di mercato (Risk-On/Off)\n"
        f"• Divergenza chiave news vs tecnica\n"
        f"• Trade ideas con ETF + azioni\n"
        f"• Alert correlazione dollaro\n"
        f"• Da monitorare nella settimana\n\n"
        f"_Usa /test per verificare la connessione._",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra l'ultimo ciclo eseguito dal log."""
    report_files = sorted(glob.glob("logs/report_*.json"), reverse=True)

    if not report_files:
        await update.message.reply_text(
            "📋 *Nessun report trovato nei log.*\n\n"
            "Il sistema non ha ancora generato report in questa sessione.\n"
            "I report vengono creati automaticamente lunedì e giovedì alle 07:00.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    latest = report_files[0]
    try:
        with open(latest, "r", encoding="utf-8") as f:
            data = json.load(f)

        generated = data.get("generated_at", "N/A")[:16].replace("T", " ")
        bias = data.get("bias", "N/A")
        cycle = data.get("cycle", "N/A")
        trades = data.get("trade_ideas", [])
        settore = trades[0].get("settore", "N/A") if trades else "N/A"
        dir_ = trades[0].get("direzione", "N/A") if trades else "N/A"

        bias_emoji = "🟢" if bias == "Risk-On" else "🔴" if bias == "Risk-Off" else "🟡"

        msg = (
            f"📋 *Ultimo report generato*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {generated}\n"
            f"📅 Ciclo: {cycle}\n"
            f"{bias_emoji} Bias: {bias}\n"
            f"🏭 Trade principale: {settore} — {dir_}\n\n"
            f"_File: {os.path.basename(latest)}_"
        )
    except Exception as e:
        msg = f"⚠️ Errore lettura log: {e}"

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera e invia un report completo su richiesta."""
    # Accetta /report, /report A, /report B
    args = context.args
    cycle = "A"
    if args and args[0].upper() in ("A", "B"):
        cycle = args[0].upper()
    else:
        # Determina automaticamente in base al giorno
        today = datetime.now().weekday()  # 0=lun ... 6=dom
        cycle = "B" if today in (2, 3) else "A"  # mer/gio → B, resto → A

    cycle_label = "Lunedì (Ciclo A)" if cycle == "A" else "Giovedì (Ciclo B)"
    await update.message.reply_text(
        f"⚙️ *Generazione report in corso...*\n"
        f"Ciclo: {cycle_label}\n\n"
        f"Sto raccogliendo prezzi, leggendo le news e chiamando Claude AI.\n"
        f"_Attendi 2-3 minuti — riceverai il report nel canale._",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        import threading
        def run_pipeline():
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from main import run_full_cycle
            run_full_cycle(cycle)

        thread = threading.Thread(target=run_pipeline, daemon=True)
        thread.start()

    except Exception as e:
        await update.message.reply_text(
            f"❌ Errore avvio pipeline: {e}",
            parse_mode=ParseMode.MARKDOWN
        )


async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Calcola quando arriva il prossimo report."""
    now = datetime.now()
    weekday = now.weekday()  # 0=lun, 6=dom

    # Calcola giorni al prossimo lunedì (0) e giovedì (3)
    days_to_mon = (0 - weekday) % 7 or 7
    days_to_thu = (3 - weekday) % 7 or 7

    next_mon = now + timedelta(days=days_to_mon)
    next_thu = now + timedelta(days=days_to_thu)

    next_mon_str = next_mon.strftime("%A %d %B") + " alle 07:00"
    next_thu_str = next_thu.strftime("%A %d %B") + " alle 07:00"

    # Quale è più vicino?
    next_report = "Lunedì" if days_to_mon <= days_to_thu else "Giovedì"
    next_date = next_mon_str if days_to_mon <= days_to_thu else next_thu_str
    days_left = min(days_to_mon, days_to_thu)

    msg = (
        f"📅 *Prossimi report MacroEdge*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏭ *Prossimo:* {next_report} — {next_date}\n"
        f"   ({days_left} {'giorno' if days_left == 1 else 'giorni'})\n\n"
        f"📋 Lunedì: {next_mon_str}\n"
        f"📋 Giovedì: {next_thu_str}"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


# ── Inoltro messaggi al canale ────────────────────────────────────

async def handle_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Inoltra al canale ogni messaggio non-comando ricevuto dal bot.
    Il bot deve essere amministratore del canale target.
    """
    if not TELEGRAM_CHAT_ID or update.message is None:
        return
    try:
        await context.bot.forward_message(
            chat_id=TELEGRAM_CHAT_ID,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id,
        )
    except Exception as e:
        logger.warning(f"Forward al canale fallito: {e}")


# ── Registra comandi su BotFather ─────────────────────────────────

async def register_commands():
    """Registra i comandi del bot su Telegram (appare nel menu /)."""
    from telegram import Bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    commands = [
        BotCommand("report", "Genera report ora  [A|B]"),
        BotCommand("test",   "Stato del sistema"),
        BotCommand("sample", "Report di esempio"),
        BotCommand("status", "Ultimo ciclo eseguito"),
        BotCommand("next",   "Prossimo report automatico"),
        BotCommand("help",   "Lista comandi"),
    ]
    await bot.set_my_commands(commands)
    print("✅ Comandi registrati su Telegram. Premi '/' nel bot per vederli.")
    await bot.close()


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MacroEdge — Bot Telegram interattivo")
    parser.add_argument("--set", action="store_true",
                        help="Registra i comandi su BotFather e poi esci")
    args = parser.parse_args()

    if not TELEGRAM_BOT_TOKEN:
        print("❌  TELEGRAM_BOT_TOKEN non configurato in .env")
        sys.exit(1)

    if args.set:
        asyncio.run(register_commands())
        return

    print("🤖 MacroEdge Bot — avviato in ascolto")
    print("   Comandi disponibili: /test /sample /status /next /help")
    print("   Premi Ctrl+C per fermare\n")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("test",   cmd_test))
    app.add_handler(CommandHandler("sample", cmd_sample))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("next",   cmd_next))

    # Inoltra al canale tutti i messaggi non-comando
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_forward))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
