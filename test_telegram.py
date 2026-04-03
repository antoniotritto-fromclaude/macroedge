#!/usr/bin/env python3
# macroedge/test_telegram.py
# ================================================================
# Invia un messaggio di test su Telegram con tre modalità:
#
#   python test_telegram.py             → messaggio di stato sistema
#   python test_telegram.py --sample    → report di esempio completo
#   python test_telegram.py --alert     → testa l'alert dollaro
#   python test_telegram.py --msg "testo" → messaggio personalizzato
# ================================================================

import asyncio
import argparse
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from telegram import Bot
from telegram.constants import ParseMode
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


# ── Messaggi di test ──────────────────────────────────────────────

STATUS_MESSAGE = """🟢 *MacroEdge — Sistema Operativo*
━━━━━━━━━━━━━━━━━━━━
✅ Connessione Telegram: OK
✅ Bot attivo e raggiungibile
✅ Canale configurato correttamente

📅 *Prossimi report automatici:*
  • Lunedì 07:00 → Ciclo A \(weekend\)
  • Giovedì 07:00 → Ciclo B \(infrasettimanale\)

🤖 _MacroEdge v1\.0 — Test eseguito il {date}_"""

SAMPLE_REPORT = """📊 *MACROEDGE — TEST REPORT*
━━━━━━━━━━━━━━━━━━━━
🕐 {date} \| Messaggio di prova

🟢 *Bias:* Risk\-On
📌 *Causa:* Fed conferma taglio tassi \+ CPI sotto attese

⚡ *DIVERGENZA CHIAVE:*
Gas \+2\.1% venerdì → pace in Iran annunciata domenica → SHORT atteso lunedì

─────────────────────
📉 *TRADE 1: Energy*
🔥 Short \| Forza: Alta \| ⏱ 3\-7 giorni

💡 *Logica:*
Il mercato era posizionato long sull'energia in uno scenario di tensione geopolitica\. L'annuncio del cessate il fuoco domenica rimuove il premio di rischio dal petrolio e dal gas naturale\. Il RSI a 71 conferma ipercomprato tecnico\.

📦 *ETF:*
  • `SXEW` — Short Energy EU
  • `DUG` — ProShares UltraShort Oil

🔎 *Azioni:*
  • `XOM` — ExxonMobil
  • `CVX` — Chevron
  • `SLB` — Schlumberger
  • `BP` — BP plc

📐 Sup: €34 \| Res: €40 \| SL: \-4%

⚠️ *ALERT CORRELAZIONE DOLLARO*
DXY forte a 104\. Posizioni short su commodity in USD potrebbero subire pressione se il dollaro si apprezza ulteriormente\.

━━━━━━━━━━━━━━━━━━━━
👁 *Da monitorare:*
  • CPI martedì 14:30
  • FOMC minutes mercoledì
  • OPEC\+ comunicato giovedì

━━━━━━━━━━━━━━━━━━━━
🤖 _MacroEdge AI \| ⚠️ Questo è un messaggio di TEST_
\#macroedge \#test"""

ALERT_MESSAGE = """⚠️ *MACROEDGE — TEST ALERT*
━━━━━━━━━━━━━━━━━━━━
💵 *Alert correlazione dollaro:*
Il DXY è sopra 104 \(zona di forza\)\. La posizione Long su CORN e WEAT è correlata negativamente al dollaro con coefficiente \-0\.72 negli ultimi 60 giorni\. Considera di ridurre l'esposizione o di coprire con put sul DXY\.
━━━━━━━━━━━━━━━━━━━━
🕐 {date} \| Messaggio di TEST"""


async def send(text: str, parse_mode: str = ParseMode.MARKDOWN_V2) -> bool:
    """Invia un messaggio Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("❌  TELEGRAM_BOT_TOKEN non configurato in .env")
        return False
    if not TELEGRAM_CHAT_ID:
        print("❌  TELEGRAM_CHAT_ID non configurato in .env")
        return False

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=True
        )
        print("✅  Messaggio inviato su Telegram con successo")
        return True
    except Exception as e:
        print(f"❌  Errore Telegram: {e}")
        # Prova senza markdown
        try:
            import re
            plain = re.sub(r"[*_`\[\]\\]", "", text)
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=plain[:4000],
                disable_web_page_preview=True
            )
            print("✅  Inviato in plain text (markdown fallback)")
            return True
        except Exception as e2:
            print(f"❌  Anche il fallback è fallito: {e2}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="MacroEdge — test rapido Telegram",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
esempi:
  python test_telegram.py              → stato del sistema
  python test_telegram.py --sample     → report di esempio completo
  python test_telegram.py --alert      → test alert correlazione dollaro
  python test_telegram.py --msg "ciao" → messaggio personalizzato
        """
    )
    parser.add_argument("--sample",      action="store_true", help="Invia un report di esempio completo")
    parser.add_argument("--alert",       action="store_true", help="Invia un alert di test")
    parser.add_argument("--msg",         type=str,            help="Invia un messaggio personalizzato")
    args = parser.parse_args()

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    # Escapa il punto per MarkdownV2
    now_escaped = now_str.replace(".", "\\.").replace("/", "\\/").replace(":", "\\:")

    print(f"\n📡 MacroEdge — test Telegram")
    print(f"   Bot:  {'configurato ✅' if TELEGRAM_BOT_TOKEN else 'MANCANTE ❌'}")
    print(f"   Chat: {'configurato ✅' if TELEGRAM_CHAT_ID else 'MANCANTE ❌'}")
    print()

    if args.msg:
        # Messaggio personalizzato in plain text
        text = f"📩 MacroEdge — Messaggio di test:\n\n{args.msg}\n\n🕐 {now_str}"
        ok = asyncio.run(send(text, parse_mode=None))
    elif args.sample:
        text = SAMPLE_REPORT.format(date=now_escaped)
        ok = asyncio.run(send(text))
    elif args.alert:
        text = ALERT_MESSAGE.format(date=now_escaped)
        ok = asyncio.run(send(text))
    else:
        text = STATUS_MESSAGE.format(date=now_escaped)
        ok = asyncio.run(send(text))

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
