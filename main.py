#!/usr/bin/env python3
# macroedge/main.py
# ================================================================
# Entry point del sistema MacroEdge.
# Gestisce lo scheduler e orchestra tutti i moduli.
#
# USO:
#   python main.py                  → avvia lo scheduler (modalità produzione)
#   python main.py --run-now A      → esegui subito il ciclo A (test)
#   python main.py --run-now B      → esegui subito il ciclo B (test)
#   python main.py --test-telegram  → testa la connessione Telegram
#   python main.py --test-sheets    → testa la connessione Google Sheets
# ================================================================

import sys
import os
import logging
import colorlog
import argparse
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Aggiungi la root del progetto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import TIMEZONE, SCHEDULE_ANALYSIS_SUN, SCHEDULE_REPORT_MON
from config import SCHEDULE_ANALYSIS_WED, SCHEDULE_REPORT_THU
from config import ASSETS, RSS_FEEDS


# ── Logging ───────────────────────────────────────────────────────
def setup_logging():
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(name)s] %(levelname)s%(reset)s — %(message)s",
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG":    "cyan",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "bold_red",
        }
    ))

    file_handler = logging.FileHandler(
        f"logs/macroedge_{datetime.now().strftime('%Y%m')}.log"
    )
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s — %(message)s"
    ))

    root_logger = logging.getLogger("macroedge")
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    root_logger.addHandler(file_handler)

logger = logging.getLogger("macroedge.main")


# ── Funzioni principali ───────────────────────────────────────────

def run_data_collection(cycle: str):
    """
    FASE 1 — Raccolta dati (domenica 21:00 / mercoledì 21:00).
    Scarica prezzi e news, li salva in cache locale.
    """
    import json
    from data.price_fetcher import get_full_market_snapshot
    from data.news_reader import fetch_all_news

    logger.info(f"{'='*50}")
    logger.info(f"FASE 1 — Raccolta Dati | Ciclo {'A (→ Lunedì)' if cycle == 'A' else 'B (→ Giovedì)'}")
    logger.info(f"{'='*50}")

    # Scarica prezzi
    logger.info("Scaricamento prezzi da Yahoo Finance...")
    snapshot = get_full_market_snapshot(ASSETS)

    # Leggi RSS news
    hours_back = 52 if cycle == "A" else 30  # weekend: 52h, mid-week: 30h
    logger.info(f"Lettura feed RSS (ultime {hours_back}h)...")
    news_list = fetch_all_news(RSS_FEEDS, hours_back=hours_back)

    # Salva in cache locale
    cache_dir = f"logs/cache_cycle_{cycle}_{datetime.now().strftime('%Y%m%d')}"
    os.makedirs(cache_dir, exist_ok=True)

    with open(f"{cache_dir}/snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)
    with open(f"{cache_dir}/news.json", "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"Cache salvata in {cache_dir}")
    logger.info(f"FASE 1 completata — {len(snapshot)} asset, {len(news_list)} news")
    return snapshot, news_list


def run_analysis_and_report(cycle: str, snapshot=None, news_list=None):
    """
    FASE 2 — Analisi AI e invio report (lunedì 07:00 / giovedì 07:00).
    Carica i dati dalla cache se non passati direttamente.
    """
    import json
    import glob
    from core.ai_analyzer import analyze
    from output.telegram_sender import send_report, send_alert
    from output.notion_writer import log_report, log_technical_snapshot, log_news_batch

    logger.info(f"{'='*50}")
    logger.info(f"FASE 2 — Analisi AI e Report | Ciclo {'A (Lunedì)' if cycle == 'A' else 'B (Giovedì)'}")
    logger.info(f"{'='*50}")

    # Carica dalla cache se i dati non sono passati direttamente
    if snapshot is None or news_list is None:
        today = datetime.now().strftime("%Y%m%d")
        yesterday = datetime.now()
        # Cerca cache di oggi o di ieri
        for date_str in [today, yesterday.strftime("%Y%m%d")]:
            cache_dir = f"logs/cache_cycle_{cycle}_{date_str}"
            snap_file = f"{cache_dir}/snapshot.json"
            news_file = f"{cache_dir}/news.json"
            if os.path.exists(snap_file) and os.path.exists(news_file):
                with open(snap_file, "r", encoding="utf-8") as f:
                    snapshot = json.load(f)
                with open(news_file, "r", encoding="utf-8") as f:
                    news_list = json.load(f)
                logger.info(f"Cache caricata da {cache_dir}")
                break
        else:
            logger.warning("Cache non trovata — raccolta dati in tempo reale")
            snapshot, news_list = run_data_collection(cycle)

    # ── Analisi AI ────────────────────────────────────────────────
    logger.info("Avvio analisi Claude AI...")
    report = analyze(cycle, snapshot, news_list)

    if report is None:
        error_msg = f"Errore nella generazione del report (Ciclo {'A' if cycle == 'A' else 'B'}) — controlla i log"
        logger.error(error_msg)
        send_alert(error_msg, alert_type="error")
        return False

    # ── Salva report JSON ─────────────────────────────────────────
    report_file = f"logs/report_{cycle}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"Report JSON salvato in {report_file}")

    # ── Invia su Telegram ─────────────────────────────────────────
    logger.info("Invio report su Telegram...")
    tg_ok = send_report(report)
    if tg_ok:
        logger.info("  ✓ Telegram: OK")
    else:
        logger.error("  ✗ Telegram: FALLITO")

    # ── Salva su Google Sheets ────────────────────────────────────
    logger.info("Scrittura su Google Sheets...")
    try:
        sh_report = log_report(report, cycle)
        sh_tech   = log_technical_snapshot(snapshot, cycle)
        sh_news   = log_news_batch(news_list, cycle)
        if sh_report and sh_tech and sh_news:
            logger.info("  ✓ Google Sheets: OK")
        else:
            logger.warning("  ⚠ Google Sheets: scrittura parziale")
    except Exception as e:
        logger.error(f"  ✗ Google Sheets: {e}")

    # ── Alert dollaro separato ────────────────────────────────────
    if report.get("alert_dollaro") and report.get("alert_dollaro_dettaglio"):
        logger.info("  Invio alert correlazione dollaro...")
        send_alert(f"💵 {report['alert_dollaro_dettaglio']}", alert_type="warning")

    logger.info(f"FASE 2 completata — Bias: {report.get('bias', 'N/A')}")
    return True


def run_full_cycle(cycle: str):
    """
    Esegue subito il ciclo completo (raccolta + analisi).
    Utile per test o per rieseguire manualmente.
    """
    logger.info(f"Esecuzione ciclo completo {cycle} (raccolta + analisi)...")
    snapshot, news_list = run_data_collection(cycle)
    run_analysis_and_report(cycle, snapshot, news_list)


# ── Scheduler ─────────────────────────────────────────────────────

def start_scheduler():
    """
    Avvia lo scheduler APScheduler con i 4 job configurati.
    Il processo rimane in ascolto finché non viene terminato.
    """
    from output.telegram_sender import send_startup_message

    tz = pytz.timezone(TIMEZONE)
    scheduler = BlockingScheduler(timezone=tz)

    # Parsa gli orari dal config
    sun_h,  sun_m  = map(int, SCHEDULE_ANALYSIS_SUN.split(":"))
    mon_h,  mon_m  = map(int, SCHEDULE_REPORT_MON.split(":"))
    wed_h,  wed_m  = map(int, SCHEDULE_ANALYSIS_WED.split(":"))
    thu_h,  thu_m  = map(int, SCHEDULE_REPORT_THU.split(":"))

    # ── CICLO A ───────────────────────────────────────────────────
    # Domenica sera: raccolta dati
    scheduler.add_job(
        func=lambda: run_data_collection("A"),
        trigger=CronTrigger(day_of_week="sun", hour=sun_h, minute=sun_m, timezone=tz),
        id="cycle_a_collection",
        name="Ciclo A — Raccolta dati (domenica)",
        misfire_grace_time=3600
    )
    # Lunedì mattina: analisi e report
    scheduler.add_job(
        func=lambda: run_analysis_and_report("A"),
        trigger=CronTrigger(day_of_week="mon", hour=mon_h, minute=mon_m, timezone=tz),
        id="cycle_a_report",
        name="Ciclo A — Report Lunedì",
        misfire_grace_time=3600
    )

    # ── CICLO B ───────────────────────────────────────────────────
    # Mercoledì sera: raccolta dati
    scheduler.add_job(
        func=lambda: run_data_collection("B"),
        trigger=CronTrigger(day_of_week="wed", hour=wed_h, minute=wed_m, timezone=tz),
        id="cycle_b_collection",
        name="Ciclo B — Raccolta dati (mercoledì)",
        misfire_grace_time=3600
    )
    # Giovedì mattina: analisi e report
    scheduler.add_job(
        func=lambda: run_analysis_and_report("B"),
        trigger=CronTrigger(day_of_week="thu", hour=thu_h, minute=thu_m, timezone=tz),
        id="cycle_b_report",
        name="Ciclo B — Report Giovedì",
        misfire_grace_time=3600
    )

    logger.info("MacroEdge Scheduler avviato:")
    logger.info(f"  Domenica {SCHEDULE_ANALYSIS_SUN} → raccolta dati Ciclo A")
    logger.info(f"  Lunedì   {SCHEDULE_REPORT_MON}   → report Lunedì (Ciclo A)")
    logger.info(f"  Mercoledì {SCHEDULE_ANALYSIS_WED} → raccolta dati Ciclo B")
    logger.info(f"  Giovedì  {SCHEDULE_REPORT_THU}   → report Giovedì (Ciclo B)")

    send_startup_message()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler fermato.")


# ── CLI ───────────────────────────────────────────────────────────

def main():
    setup_logging()
    os.makedirs("logs", exist_ok=True)

    parser = argparse.ArgumentParser(description="MacroEdge — Trading Intelligence System")
    parser.add_argument("--run-now", choices=["A", "B"],
                        help="Esegui subito un ciclo completo (raccolta + analisi)")
    parser.add_argument("--collect-only", choices=["A", "B"],
                        help="Solo raccolta dati, senza analisi AI")
    parser.add_argument("--analyze-only", choices=["A", "B"],
                        help="Solo analisi (usa cache esistente)")
    parser.add_argument("--test-telegram", action="store_true",
                        help="Testa la connessione Telegram")
    parser.add_argument("--test-sheets", action="store_true",
                        help="Testa la connessione Google Sheets")

    args = parser.parse_args()

    if args.run_now:
        logger.info(f"Esecuzione manuale ciclo {args.run_now}")
        run_full_cycle(args.run_now)

    elif args.collect_only:
        run_data_collection(args.collect_only)

    elif args.analyze_only:
        run_analysis_and_report(args.analyze_only)

    elif args.test_telegram:
        from output.telegram_sender import send_startup_message
        logger.info("Test connessione Telegram...")
        ok = send_startup_message()
        logger.info("  ✓ Telegram OK" if ok else "  ✗ Telegram FALLITO")

    elif args.test_sheets:
        from notion_client import Client
        from config import NOTION_API_KEY, NOTION_DB_REPORTS
        logger.info("Test connessione Notion...")
        try:
            notion = Client(auth=NOTION_API_KEY)
            me = notion.users.me()
            logger.info(f"  ✓ Notion OK — Connesso come: {me.get('name','N/A')}")
            if NOTION_DB_REPORTS:
                db = notion.databases.retrieve(database_id=NOTION_DB_REPORTS)
                logger.info(f"  ✓ Database Reports trovato: {db['title'][0]['plain_text']}")
            else:
                logger.warning("  ⚠ NOTION_DB_REPORTS non configurato — esegui setup_notion.py")
        except Exception as e:
            logger.error(f"  ✗ Notion FALLITO: {e}")

    else:
        # Modalità produzione: avvia lo scheduler
        start_scheduler()


if __name__ == "__main__":
    main()
