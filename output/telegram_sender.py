# macroedge/output/telegram_sender.py
# ================================================================
# Invia il report al canale Telegram privato.
# Usa python-telegram-bot in modalità asincrona.
# Il messaggio è formattato con MarkdownV2 per avere bold e emoji.
# ================================================================

import asyncio
import logging
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
import re
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger("macroedge.telegram")


def _escape_md(text: str) -> str:
    """
    Escapa i caratteri speciali per MarkdownV2 di Telegram.
    Caratteri da escapare: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    special = r"\_*[]()~`>#+-=|{}.!"
    for char in special:
        text = text.replace(char, f"\\{char}")
    return text


def _format_report_message(report: dict) -> str:
    """
    Formatta il report JSON in un messaggio Telegram leggibile.
    Usa MarkdownV2 per la formattazione.
    """
    report_day   = report.get("report_day", "Report")
    bias         = report.get("bias", "N/A")
    bias_causa   = report.get("bias_causa", "")
    macro        = report.get("macro_outlook", "")
    divergenza   = report.get("divergenza_chiave", {})
    trade_ideas  = report.get("trade_ideas", [])
    alert_dollar = report.get("alert_dollaro", False)
    alert_detail = report.get("alert_dollaro_dettaglio", "")
    monitoring   = report.get("da_monitorare", [])
    sentiment    = report.get("sentiment_score", 0)
    generated_at = report.get("generated_at", "")

    # Emoji per bias
    bias_emoji = "🟢" if bias == "Risk-On" else "🔴" if bias == "Risk-Off" else "🟡"
    sentiment_bar = "▓" * max(1, abs(sentiment) // 10) + "░" * (10 - max(1, abs(sentiment) // 10))

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    lines = []

    # ── Header ────────────────────────────────────────────────────
    lines.append(f"📊 *MACROEDGE — {report_day.upper()}*")
    lines.append(f"━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🕐 {now_str}")
    lines.append("")

    # ── Bias ──────────────────────────────────────────────────────
    lines.append(f"{bias_emoji} *Bias:* {_escape_md(bias)}")
    lines.append(f"📌 *Causa:* {_escape_md(bias_causa)}")
    sentiment_dir = "+" if sentiment > 0 else ""
    lines.append(f"📊 *Sentiment:* {sentiment_dir}{sentiment} `{sentiment_bar}`")
    lines.append("")

    # ── Divergenza chiave ─────────────────────────────────────────
    if divergenza:
        urgenza_emoji = "🚨" if divergenza.get("urgenza") == "Alta" else "⚡"
        dir_emoji = "📉" if divergenza.get("impatto_atteso") == "Short" else "📈"
        lines.append(f"{urgenza_emoji} *DIVERGENZA CHIAVE*")
        lines.append(f"{_escape_md(divergenza.get('descrizione', ''))}")
        lines.append(f"{dir_emoji} {_escape_md(divergenza.get('asset_coinvolto', ''))} → *{divergenza.get('impatto_atteso', '')}*")
        lines.append("")

    # ── Trade ideas ───────────────────────────────────────────────
    for i, trade in enumerate(trade_ideas, 1):
        settore   = trade.get("settore", "N/A")
        direzione = trade.get("direzione", "N/A")
        forza     = trade.get("forza_segnale", "N/A")
        timeframe = trade.get("timeframe_giorni", "N/A")
        logica    = trade.get("logica_completa", "")
        etfs      = trade.get("etf", [])
        azioni    = trade.get("azioni", [])
        livelli   = trade.get("livelli", {})

        dir_emoji  = "📈" if direzione == "Long" else "📉"
        forza_emoji = "🔥" if forza == "Alta" else "⚡" if forza == "Media" else "💧"

        lines.append(f"─────────────────────")
        lines.append(f"{dir_emoji} *TRADE {i}: {_escape_md(settore)}*")
        lines.append(f"{forza_emoji} {_escape_md(direzione)} | Forza: {_escape_md(forza)} | ⏱ {_escape_md(timeframe)} giorni")
        lines.append("")
        lines.append(f"💡 *Logica:*")
        lines.append(_escape_md(logica))
        lines.append("")

        if etfs:
            lines.append("📦 *ETF:*")
            for etf in etfs[:2]:
                lines.append(f"  • `{etf.get('ticker', '')}` — {_escape_md(etf.get('nome', ''))}")
        if azioni:
            lines.append("🔎 *Azioni:*")
            for az in azioni[:4]:
                lines.append(f"  • `{az.get('ticker', '')}` — {_escape_md(az.get('nome', ''))}")
        if livelli:
            sup  = livelli.get("supporto", "—")
            res  = livelli.get("resistenza", "—")
            stop = livelli.get("stop_loss_indicativo", "—")
            lines.append(f"📐 Sup: {_escape_md(str(sup))} | Res: {_escape_md(str(res))} | SL: {_escape_md(str(stop))}")
        lines.append("")

    # ── Alert dollaro ─────────────────────────────────────────────
    if alert_dollar and alert_detail:
        lines.append(f"━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"⚠️ *ALERT CORRELAZIONE DOLLARO*")
        lines.append(_escape_md(alert_detail))
        lines.append("")

    # ── Macro outlook ─────────────────────────────────────────────
    if macro:
        lines.append(f"━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"🌐 *Macro Outlook Settimana:*")
        lines.append(_escape_md(macro))
        lines.append("")

    # ── Da monitorare ─────────────────────────────────────────────
    if monitoring:
        lines.append(f"👁 *Da monitorare:*")
        for event in monitoring:
            lines.append(f"  • {_escape_md(event)}")
        lines.append("")

    # ── Footer ────────────────────────────────────────────────────
    lines.append(f"━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🤖 _MacroEdge AI \\| Non è consulenza finanziaria_")
    lines.append(f"\\#macroedge \\#{report_day.lower().replace(' ', '')}")

    return "\n".join(lines)


def _format_alert_message(alert_type: str, details: str) -> str:
    """
    Formatta un messaggio di alert semplice (es. alert correlazione dollaro).
    """
    emoji = "⚠️" if alert_type == "warning" else "🚨"
    return (
        f"{emoji} *MACROEDGE ALERT*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{_escape_md(details)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )


async def _send_message_async(text: str, parse_mode: str = ParseMode.MARKDOWN_V2) -> bool:
    """Invia un messaggio Telegram in modo asincrono."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        # Telegram ha un limite di 4096 caratteri per messaggio
        max_length = 4000
        if len(text) <= max_length:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        else:
            # Split in più messaggi se troppo lungo
            chunks = _split_message(text, max_length)
            for i, chunk in enumerate(chunks):
                await bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=chunk,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True
                )
                if i < len(chunks) - 1:
                    await asyncio.sleep(1)  # pausa tra messaggi

        logger.info("  Messaggio Telegram inviato con successo")
        return True

    except TelegramError as e:
        logger.error(f"  Errore Telegram: {e}")
        # Fallback: invia senza markdown se c'è un errore di parsing
        if "can't parse" in str(e).lower():
            logger.info("  Ritento senza markdown...")
            try:
                plain_text = re.sub(r"[*_`\[\]\\]", "", text)
                await bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=plain_text[:4000],
                    disable_web_page_preview=True
                )
                return True
            except Exception as e2:
                logger.error(f"  Fallback fallito: {e2}")
        return False


def _split_message(text: str, max_length: int) -> list:
    """Divide un testo lungo in parti rispettando le righe."""
    parts = []
    lines = text.split("\n")
    current = []
    current_len = 0

    for line in lines:
        if current_len + len(line) + 1 > max_length:
            if current:
                parts.append("\n".join(current))
                current = [line]
                current_len = len(line)
        else:
            current.append(line)
            current_len += len(line) + 1

    if current:
        parts.append("\n".join(current))

    return parts


def send_report(report: dict) -> bool:
    """
    Funzione principale per inviare il report su Telegram.
    Chiama la versione async in modo sincrono.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Token Telegram o Chat ID non configurati in .env")
        return False

    logger.info("Formattazione messaggio Telegram...")
    message = _format_report_message(report)

    logger.info(f"Invio report Telegram (ciclo {report.get('cycle', '?')})...")
    return asyncio.run(_send_message_async(message))


def send_alert(message: str, alert_type: str = "warning") -> bool:
    """Invia un messaggio di alert rapido su Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    formatted = _format_alert_message(alert_type, message)
    return asyncio.run(_send_message_async(formatted))


def send_startup_message() -> bool:
    """Invia un messaggio di avvio del sistema."""
    msg = (
        "🚀 *MacroEdge avviato*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Il sistema è operativo\\.\n"
        "📅 *Ciclo A:* Domenica analisi → Lunedì 07:00 report\n"
        "📅 *Ciclo B:* Mercoledì analisi → Giovedì 07:00 report\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {_escape_md(datetime.now().strftime('%d/%m/%Y %H:%M'))}"
    )
    return asyncio.run(_send_message_async(msg))
