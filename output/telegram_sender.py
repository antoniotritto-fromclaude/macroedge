# macroedge/output/telegram_sender.py
# ================================================================
# Invia il report al canale Telegram.
# Usa python-telegram-bot in modalità asincrona.
# Formattazione MarkdownV2.
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
    """Escapa i caratteri speciali per MarkdownV2 di Telegram."""
    special = r"\_*[]()~`>#+-=|{}.!"
    for char in special:
        text = text.replace(char, f"\\{char}")
    return text


def _format_report_message(report: dict) -> list[str]:
    """
    Formatta il report JSON in messaggi Telegram leggibili.
    Restituisce una lista di stringhe (messaggi separati) per gestire
    report lunghi con molti asset e trade ideas.
    """
    report_day   = report.get("report_day", "Report")
    bias         = report.get("bias", "N/A")
    bias_causa   = report.get("bias_causa", "")
    macro        = report.get("macro_outlook", "")
    divergenza   = report.get("divergenza_chiave", {})
    trade_ideas  = report.get("trade_ideas", [])
    top5         = report.get("top5_opportunita", [])
    alert_corr   = report.get("alert_correlazioni", [])
    alert_dollar = report.get("alert_dollaro", False)
    alert_detail = report.get("alert_dollaro_dettaglio", "")
    monitoring   = report.get("da_monitorare", [])
    sentiment    = report.get("sentiment_score", 0) or 0
    asset_count  = report.get("asset_count", "N/A")

    bias_emoji = "🟢" if bias == "Risk-On" else "🔴" if bias == "Risk-Off" else "🟡"
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    messages = []

    # ── MESSAGGIO 1: Header + Bias + Divergenza ───────────────────
    m1 = []
    m1.append(f"📊 *MACROEDGE — {_escape_md(report_day.upper())}*")
    m1.append(f"━━━━━━━━━━━━━━━━━━━━")
    m1.append(f"🕐 {_escape_md(now_str)} \\| 🔭 {_escape_md(str(asset_count))} asset analizzati")
    m1.append("")

    m1.append(f"{bias_emoji} *Bias:* {_escape_md(bias)}")
    m1.append(f"📌 *Causa:* {_escape_md(bias_causa)}")
    sentiment_dir = "+" if sentiment > 0 else ""
    m1.append(f"📊 *Sentiment:* `{sentiment_dir}{sentiment}`")
    m1.append("")

    if divergenza:
        urgenza_emoji = "🚨" if divergenza.get("urgenza") == "Alta" else "⚡"
        dir_emoji = "📉" if divergenza.get("impatto_atteso") == "Short" else "📈"
        m1.append(f"{urgenza_emoji} *DIVERGENZA CHIAVE*")
        m1.append(_escape_md(divergenza.get("descrizione", "")))
        m1.append(f"{dir_emoji} *{_escape_md(divergenza.get('asset_coinvolto',''))}* → {_escape_md(divergenza.get('impatto_atteso',''))}")
        m1.append(f"📰 _{_escape_md(divergenza.get('news_che_cambia_tutto',''))}_")
        m1.append("")

    if macro:
        m1.append(f"🌐 *Macro Outlook:*")
        m1.append(_escape_md(macro))
        m1.append("")

    messages.append("\n".join(m1))

    # ── MESSAGGIO 2+: Trade Ideas ─────────────────────────────────
    for i, trade in enumerate(trade_ideas, 1):
        settore   = trade.get("settore", "N/A")
        direzione = trade.get("direzione", "N/A")
        forza     = trade.get("forza_segnale", "N/A")
        entry     = trade.get("entry", "—")
        stop_loss = trade.get("stop_loss", "—")
        take_prof = trade.get("take_profit", "—")
        rr        = trade.get("rischio_rendimento", "—")
        atr_note  = trade.get("atr_note", "")
        logica    = trade.get("logica_completa", "")
        etfs      = trade.get("etf", [])
        etfs_inv  = trade.get("etf_inverso", [])
        azioni    = trade.get("azioni", [])
        timeframe = trade.get("timeframe_giorni", "N/A")

        dir_emoji   = "📈" if direzione == "Long" else "📉"
        forza_emoji = "🔥" if forza == "Alta" else "⚡" if forza == "Media" else "💧"

        mt = []
        mt.append(f"─────────────────────")
        mt.append(f"{dir_emoji} *TRADE {i}: {_escape_md(settore)}*")
        mt.append(f"{forza_emoji} {_escape_md(direzione)} \\| Forza: {_escape_md(forza)} \\| ⏱ {_escape_md(str(timeframe))}g")
        mt.append("")

        mt.append(f"📐 *Livelli operativi:*")
        mt.append(f"  Entry: `{_escape_md(str(entry))}`")
        mt.append(f"  Stop:  `{_escape_md(str(stop_loss))}`")
        mt.append(f"  Target: `{_escape_md(str(take_prof))}`")
        mt.append(f"  R/R: {_escape_md(str(rr))}")
        if atr_note:
            mt.append(f"  📏 _{_escape_md(str(atr_note))}_")
        mt.append("")

        mt.append(f"💡 *Logica:*")
        mt.append(_escape_md(logica))
        mt.append("")

        if etfs:
            mt.append("📦 *ETF Long:*")
            for etf in etfs[:2]:
                mt.append(f"  • `{etf.get('ticker','')}` — {_escape_md(etf.get('nome',''))}")
        if direzione == "Short" and etfs_inv:
            mt.append("🔄 *ETF Inverso \\(alternativa Short\\):*")
            for etf in etfs_inv[:2]:
                mt.append(f"  • `{etf.get('ticker','')}` — {_escape_md(etf.get('nome',''))}")
        if azioni:
            mt.append("🔎 *Azioni selezionate:*")
            for az in azioni[:4]:
                paese = az.get("paese", "")
                flag = {"US":"🇺🇸","IT":"🇮🇹","FR":"🇫🇷","UK":"🇬🇧","DE":"🇩🇪",
                        "ES":"🇪🇸","CN":"🇨🇳","JP":"🇯🇵","BR":"🇧🇷","MX":"🇲🇽"}.get(paese, "🌐")
                mt.append(f"  {flag} `{az.get('ticker','')}` — {_escape_md(az.get('nome',''))}")
        mt.append("")

        messages.append("\n".join(mt))

    # ── MESSAGGIO: Top 5 Opportunità ──────────────────────────────
    if top5:
        mt5 = []
        mt5.append(f"🏆 *TOP 5 OPPORTUNITÀ*")
        mt5.append(f"━━━━━━━━━━━━━━━━━━━━")
        mt5.append(f"_Migliori setup tecnico \\+ news dell'universo_")
        mt5.append("")

        for opp in top5[:5]:
            rank      = opp.get("rank", "?")
            ticker    = opp.get("ticker", "")
            nome      = opp.get("nome", "")
            paese     = opp.get("paese", "")
            direzione = opp.get("direzione", "")
            entry     = opp.get("entry", "—")
            stop      = opp.get("stop", "—")
            target    = opp.get("target", "—")
            forza     = opp.get("forza", "")
            cataliz   = opp.get("catalizzatore", "")
            tf        = opp.get("timeframe_giorni", "")

            flag = {"US":"🇺🇸","IT":"🇮🇹","FR":"🇫🇷","UK":"🇬🇧","DE":"🇩🇪",
                    "ES":"🇪🇸","CN":"🇨🇳","JP":"🇯🇵","BR":"🇧🇷","MX":"🇲🇽"}.get(paese, "🌐")
            dir_emoji = "📈" if direzione == "Long" else "📉"
            forza_star = "⭐⭐" if forza == "Alta" else "⭐"

            mt5.append(f"*{rank}\\. {flag} `{ticker}` — {_escape_md(nome)}*")
            mt5.append(f"  {dir_emoji} {_escape_md(direzione)} {forza_star} \\| {_escape_md(str(tf))}g")
            mt5.append(f"  💡 {_escape_md(cataliz)}")
            mt5.append(f"  📐 E:`{_escape_md(str(entry))}` S:`{_escape_md(str(stop))}` T:`{_escape_md(str(target))}`")
            mt5.append("")

        messages.append("\n".join(mt5))

    # ── MESSAGGIO: Alert correlazioni + Da monitorare ─────────────
    mfooter = []

    if alert_corr:
        mfooter.append(f"⚠️ *ALERT CORRELAZIONI*")
        for ac in alert_corr[:3]:
            mfooter.append(
                f"  • {_escape_md(ac.get('asset1',''))} ↔ {_escape_md(ac.get('asset2',''))}: "
                f"{_escape_md(ac.get('descrizione',''))}"
            )
        mfooter.append("")

    if alert_dollar and alert_detail:
        mfooter.append(f"💵 *ALERT DOLLARO \\(DXY\\)*")
        mfooter.append(_escape_md(alert_detail))
        mfooter.append("")

    if monitoring:
        mfooter.append(f"👁 *Da monitorare questa settimana:*")
        for event in monitoring:
            mfooter.append(f"  • {_escape_md(event)}")
        mfooter.append("")

    mfooter.append(f"━━━━━━━━━━━━━━━━━━━━")
    mfooter.append(f"🤖 _MacroEdge AI \\| Non è consulenza finanziaria_")
    mfooter.append(f"\\#macroedge \\#{_escape_md(report_day.lower().replace(' ', ''))}")

    if mfooter:
        messages.append("\n".join(mfooter))

    return messages


def _format_alert_message(alert_type: str, details: str) -> str:
    emoji = "⚠️" if alert_type == "warning" else "🚨"
    return (
        f"{emoji} *MACROEDGE ALERT*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{_escape_md(details)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {_escape_md(datetime.now().strftime('%d/%m/%Y %H:%M'))}"
    )


async def _send_message_async(text: str, parse_mode: str = ParseMode.MARKDOWN_V2) -> bool:
    """Invia un singolo messaggio Telegram (max 4096 chars con auto-split)."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        max_length = 4000
        if len(text) <= max_length:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        else:
            chunks = _split_message(text, max_length)
            for j, chunk in enumerate(chunks):
                await bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=chunk,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True
                )
                if j < len(chunks) - 1:
                    await asyncio.sleep(1)

        return True

    except TelegramError as e:
        logger.error(f"  Errore Telegram: {e}")
        if "can't parse" in str(e).lower():
            logger.info("  Ritento senza markdown...")
            try:
                plain = re.sub(r"[*_`\[\]\\]", "", text)
                await bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=plain[:4000],
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


async def _send_report_async(report: dict) -> bool:
    """Invia tutti i messaggi del report in sequenza con pausa tra essi."""
    messages = _format_report_message(report)
    ok = True
    for i, msg in enumerate(messages):
        success = await _send_message_async(msg)
        if not success:
            ok = False
        if i < len(messages) - 1:
            await asyncio.sleep(2)  # pausa tra messaggi del report
    return ok


def send_report(report: dict) -> bool:
    """Funzione principale per inviare il report su Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Token Telegram o Chat ID non configurati in .env")
        return False

    logger.info(f"Invio report Telegram (ciclo {report.get('cycle', '?')})...")
    return asyncio.run(_send_report_async(report))


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
        "🔭 *Asset monitorati:* ~130 \\(indici, FX, azioni 10 paesi, ETF, crypto\\)\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {_escape_md(datetime.now().strftime('%d/%m/%Y %H:%M'))}"
    )
    return asyncio.run(_send_message_async(msg))
