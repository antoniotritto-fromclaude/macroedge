# macroedge/output/sheets_writer.py
# ================================================================
# Scrive i dati su Google Sheets tramite gspread.
# Usa un Service Account (JSON) per l'autenticazione.
# ================================================================

import gspread
from google.oauth2.service_account import Credentials
import logging
from datetime import datetime
from typing import Optional
from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_ID

logger = logging.getLogger("macroedge.sheets")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Nomi dei fogli (devono corrispondere a quelli creati con Apps Script)
SHEET_REPORTS  = "📊 Report Storici"
SHEET_TECNICA  = "📈 Dati Tecnici"
SHEET_NEWS     = "📰 News Log"
SHEET_BACKTEST = "🧪 Backtest"


def _get_client() -> Optional[gspread.Client]:
    """Crea il client gspread con le credenziali del service account."""
    try:
        creds  = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except FileNotFoundError:
        logger.error(f"File credenziali non trovato: {GOOGLE_CREDENTIALS_FILE}")
        return None
    except Exception as e:
        logger.error(f"Errore autenticazione Google: {e}")
        return None


def _get_sheet(worksheet_name: str) -> Optional[gspread.Worksheet]:
    """Apre un foglio specifico dello spreadsheet."""
    client = _get_client()
    if not client:
        return None
    try:
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        return spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        logger.error(f"Foglio '{worksheet_name}' non trovato. Hai eseguito setupMacroEdge()?")
        return None
    except Exception as e:
        logger.error(f"Errore apertura foglio '{worksheet_name}': {e}")
        return None


def log_report(report: dict, cycle: str) -> bool:
    """
    Registra un report nel foglio '📊 Report Storici'.
    Chiamato subito dopo l'analisi AI.
    """
    sheet = _get_sheet(SHEET_REPORTS)
    if not sheet:
        return False

    try:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        report_day = "Lunedì" if cycle == "A" else "Giovedì"
        trade_ideas = report.get("trade_ideas", [])

        # Prendi il primo trade come principale
        main_trade = trade_ideas[0] if trade_ideas else {}
        etfs   = main_trade.get("etf", [])
        azioni = main_trade.get("azioni", [])

        row = [
            now,                                           # A: Timestamp
            report_day,                                    # B: Ciclo
            report.get("bias", ""),                        # C: Bias
            report.get("bias_causa", ""),                  # D: Causa Bias
            main_trade.get("settore", ""),                 # E: Settore Target
            main_trade.get("direzione", ""),               # F: Direzione
            main_trade.get("forza_segnale", ""),           # G: Forza Segnale
            etfs[0].get("ticker", "") if len(etfs) > 0 else "",  # H: ETF 1
            etfs[1].get("ticker", "") if len(etfs) > 1 else "",  # I: ETF 2
            azioni[0].get("ticker", "") if len(azioni) > 0 else "",  # J: Az 1
            azioni[1].get("ticker", "") if len(azioni) > 1 else "",  # K: Az 2
            azioni[2].get("ticker", "") if len(azioni) > 2 else "",  # L: Az 3
            azioni[3].get("ticker", "") if len(azioni) > 3 else "",  # M: Az 4
            main_trade.get("timeframe_giorni", ""),        # N: Timeframe
            "⏳",                                          # O: Esito (da aggiornare)
            "",                                            # P: Prezzo Entry
            "",                                            # Q: Prezzo Exit
            "",                                            # R: P&L %
            "",                                            # S: Note
            report.get("divergenza_chiave", {}).get("descrizione", ""),  # T: Divergenza
            "Sì" if report.get("alert_dollaro") else "No",  # U: Alert $
            str(main_trade.get("livelli", {})),            # V: Livelli tecnici
        ]

        sheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"  Report registrato su Google Sheets — riga {sheet.row_count}")
        return True

    except Exception as e:
        logger.error(f"  Errore scrittura report su Sheets: {e}")
        return False


def log_technical_snapshot(snapshot: list, cycle: str) -> bool:
    """
    Registra il snapshot tecnico nel foglio '📈 Dati Tecnici'.
    Salva tutti gli asset con i loro indicatori.
    """
    sheet = _get_sheet(SHEET_TECNICA)
    if not sheet:
        return False

    try:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        cycle_label = "Lunedì" if cycle == "A" else "Giovedì"
        rows = []

        for asset in snapshot:
            rows.append([
                now,
                asset.get("name", ""),
                asset.get("ticker", ""),
                asset.get("price", ""),
                f"{asset.get('change_1d_pct', 0):+.2f}%",
                asset.get("ma50", ""),
                asset.get("ma200", ""),
                asset.get("trend", ""),
                asset.get("rsi", ""),
                asset.get("atr", ""),
                asset.get("rsi_signal", ""),
                cycle_label,
                ""
            ])

        if rows:
            sheet.append_rows(rows, value_input_option="USER_ENTERED")
            logger.info(f"  {len(rows)} asset tecnici registrati su Sheets")
        return True

    except Exception as e:
        logger.error(f"  Errore scrittura tecnica su Sheets: {e}")
        return False


def log_news_batch(news_list: list, cycle: str) -> bool:
    """
    Registra le notizie elaborate nel foglio '📰 News Log'.
    Salva solo le notizie ad impatto medio/alto.
    """
    sheet = _get_sheet(SHEET_NEWS)
    if not sheet:
        return False

    try:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        cycle_label = "Lunedì" if cycle == "A" else "Giovedì"

        # Filtra solo media e alta
        relevant = [n for n in news_list if n.get("impact") in ("alta", "media")][:30]
        rows = []

        for news in relevant:
            rows.append([
                now,
                news.get("source", ""),
                news.get("title", "")[:200],
                news.get("impact", ""),
                ", ".join(news.get("assets", [])),
                news.get("direction", ""),
                "Sì",
                cycle_label
            ])

        if rows:
            sheet.append_rows(rows, value_input_option="USER_ENTERED")
            logger.info(f"  {len(rows)} news registrate su Sheets")
        return True

    except Exception as e:
        logger.error(f"  Errore scrittura news su Sheets: {e}")
        return False


def update_trade_outcome(row_number: int, esito: str,
                          prezzo_entry: float, prezzo_exit: float) -> bool:
    """
    Aggiorna l'esito di un trade nel foglio Report Storici.
    Da chiamare manualmente dopo aver chiuso una posizione.

    Args:
        row_number:   numero riga nel foglio (partendo da 2)
        esito:        "✅" o "❌"
        prezzo_entry: prezzo di entrata
        prezzo_exit:  prezzo di uscita
    """
    sheet = _get_sheet(SHEET_REPORTS)
    if not sheet:
        return False

    try:
        pnl = (prezzo_exit - prezzo_entry) / prezzo_entry
        sheet.update_cell(row_number, 15, esito)           # O: Esito
        sheet.update_cell(row_number, 16, prezzo_entry)    # P: Entry
        sheet.update_cell(row_number, 17, prezzo_exit)     # Q: Exit
        sheet.update_cell(row_number, 18, f"{pnl:.2%}")    # R: P&L
        logger.info(f"  Esito aggiornato riga {row_number}: {esito} P&L {pnl:.2%}")
        return True
    except Exception as e:
        logger.error(f"  Errore aggiornamento esito: {e}")
        return False


def get_open_trades() -> list:
    """
    Restituisce i trade ancora aperti (esito = ⏳).
    Utile per il modulo di backtesting automatico.
    """
    sheet = _get_sheet(SHEET_REPORTS)
    if not sheet:
        return []
    try:
        all_records = sheet.get_all_records()
        open_trades = [
            r for r in all_records
            if r.get("Esito", "") == "⏳"
        ]
        return open_trades
    except Exception as e:
        logger.error(f"  Errore lettura trade aperti: {e}")
        return []
