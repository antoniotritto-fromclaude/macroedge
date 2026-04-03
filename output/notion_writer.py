# macroedge/output/notion_writer.py
# ================================================================
# Sostituisce sheets_writer.py — usa Notion come database.
# Al primo avvio, setup_notion.py crea automaticamente
# tutti i database nel workspace. Poi questo modulo ci scrive.
#
# Struttura creata su Notion:
#   📁 MacroEdge HQ  (pagina root)
#   ├── 📊 Report Storici   (database)
#   ├── 📈 Dati Tecnici     (database)
#   └── 📰 News Log         (database)
# ================================================================

import os
import json
import logging
from datetime import datetime
from typing import Optional
from notion_client import Client
from config import (
    NOTION_API_KEY,
    NOTION_DB_REPORTS,
    NOTION_DB_TECNICA,
    NOTION_DB_NEWS,
)

logger = logging.getLogger("macroedge.notion")

# ── Client singleton ──────────────────────────────────────────────
def _client() -> Client:
    if not NOTION_API_KEY:
        raise ValueError("NOTION_API_KEY non configurata in .env")
    return Client(auth=NOTION_API_KEY)


# ── 1. LOG REPORT ─────────────────────────────────────────────────
def log_report(report: dict, cycle: str) -> bool:
    """
    Aggiunge una riga al database '📊 Report Storici'.
    Chiamato dopo ogni analisi AI completata.
    """
    if not NOTION_DB_REPORTS:
        logger.error("NOTION_DB_REPORTS non configurato")
        return False

    notion = _client()
    trade_ideas = report.get("trade_ideas", [])
    main = trade_ideas[0] if trade_ideas else {}
    etfs   = main.get("etf",    [])
    azioni = main.get("azioni", [])

    # Costruisci le properties Notion
    props = {
        # Titolo (campo obbligatorio in Notion)
        "Nome": {
            "title": [{"text": {"content":
                f"{'Lunedì' if cycle == 'A' else 'Giovedì'} — {main.get('settore','N/A')} {main.get('direzione','')}"
            }}]
        },
        "Data": {
            "date": {"start": datetime.now().strftime("%Y-%m-%d")}
        },
        "Ciclo": {
            "select": {"name": "Lunedì (A)" if cycle == "A" else "Giovedì (B)"}
        },
        "Bias": {
            "select": {"name": report.get("bias", "Neutrale")}
        },
        "Causa Bias": {
            "rich_text": [{"text": {"content": report.get("bias_causa", "")[:2000]}}]
        },
        "Settore": {
            "rich_text": [{"text": {"content": main.get("settore", "")}}]
        },
        "Direzione": {
            "select": {"name": main.get("direzione", "Long")}
        },
        "Forza Segnale": {
            "select": {"name": main.get("forza_segnale", "Media")}
        },
        "ETF 1": {
            "rich_text": [{"text": {"content": etfs[0].get("ticker","") if len(etfs)>0 else ""}}]
        },
        "ETF 2": {
            "rich_text": [{"text": {"content": etfs[1].get("ticker","") if len(etfs)>1 else ""}}]
        },
        "Azione 1": {
            "rich_text": [{"text": {"content": azioni[0].get("ticker","") if len(azioni)>0 else ""}}]
        },
        "Azione 2": {
            "rich_text": [{"text": {"content": azioni[1].get("ticker","") if len(azioni)>1 else ""}}]
        },
        "Azione 3": {
            "rich_text": [{"text": {"content": azioni[2].get("ticker","") if len(azioni)>2 else ""}}]
        },
        "Azione 4": {
            "rich_text": [{"text": {"content": azioni[3].get("ticker","") if len(azioni)>3 else ""}}]
        },
        "Timeframe": {
            "rich_text": [{"text": {"content": main.get("timeframe_giorni","")}}]
        },
        "Esito": {
            "select": {"name": "⏳ In corso"}
        },
        "Alert Dollaro": {
            "checkbox": report.get("alert_dollaro", False)
        },
        "Divergenza Chiave": {
            "rich_text": [{"text": {"content":
                report.get("divergenza_chiave", {}).get("descrizione", "")[:2000]
            }}]
        },
        "Rationale": {
            "rich_text": [{"text": {"content": main.get("logica_completa","")[:2000]}}]
        },
        "Sentiment Score": {
            "number": report.get("sentiment_score", 0)
        },
    }

    try:
        notion.pages.create(
            parent={"database_id": NOTION_DB_REPORTS},
            properties=props
        )
        logger.info("  ✓ Report aggiunto a Notion (Report Storici)")
        return True
    except Exception as e:
        logger.error(f"  ✗ Errore Notion log_report: {e}")
        return False


# ── 2. LOG DATI TECNICI ───────────────────────────────────────────
def log_technical_snapshot(snapshot: list, cycle: str) -> bool:
    """
    Salva lo snapshot tecnico nel database '📈 Dati Tecnici'.
    """
    if not NOTION_DB_TECNICA:
        logger.warning("NOTION_DB_TECNICA non configurato — skip")
        return True

    notion = _client()
    cycle_label = "Lunedì" if cycle == "A" else "Giovedì"
    errors = 0

    for asset in snapshot:
        rsi = asset.get("rsi")
        price = asset.get("price", 0)
        chg = asset.get("change_1d_pct", 0)

        props = {
            "Asset": {
                "title": [{"text": {"content": f"{asset.get('name','')} ({asset.get('ticker','')})"}}]
            },
            "Data": {
                "date": {"start": datetime.now().strftime("%Y-%m-%d")}
            },
            "Ticker": {
                "rich_text": [{"text": {"content": asset.get("ticker","")}}]
            },
            "Categoria": {
                "select": {"name": asset.get("category","altro")}
            },
            "Prezzo": {
                "number": float(price) if price else None
            },
            "Var 1D %": {
                "number": round(float(chg), 2) if chg else None
            },
            "RSI": {
                "number": round(float(rsi), 1) if rsi else None
            },
            "Segnale RSI": {
                "rich_text": [{"text": {"content": asset.get("rsi_signal","")}}]
            },
            "Trend": {
                "rich_text": [{"text": {"content": asset.get("trend","")}}]
            },
            "Ciclo": {
                "select": {"name": cycle_label}
            },
        }
        try:
            notion.pages.create(
                parent={"database_id": NOTION_DB_TECNICA},
                properties=props
            )
        except Exception as e:
            logger.error(f"  Errore Notion tecnica {asset.get('ticker','?')}: {e}")
            errors += 1

    total = len(snapshot)
    ok = total - errors
    logger.info(f"  ✓ Dati tecnici su Notion: {ok}/{total} asset")
    return errors == 0


# ── 3. LOG NEWS ───────────────────────────────────────────────────
def log_news_batch(news_list: list, cycle: str) -> bool:
    """
    Salva le notizie rilevanti nel database '📰 News Log'.
    Solo impatto alto/medio.
    """
    if not NOTION_DB_NEWS:
        logger.warning("NOTION_DB_NEWS non configurato — skip")
        return True

    notion = _client()
    relevant = [n for n in news_list if n.get("impact") in ("alta","media")][:20]
    errors = 0

    for news in relevant:
        title = news.get("title","")[:200]
        props = {
            "Titolo": {
                "title": [{"text": {"content": title}}]
            },
            "Data": {
                "date": {"start": datetime.now().strftime("%Y-%m-%d")}
            },
            "Fonte": {
                "rich_text": [{"text": {"content": news.get("source","")}}]
            },
            "Impatto": {
                "select": {"name": news.get("impact","media").capitalize()}
            },
            "Direzione": {
                "select": {"name": news.get("direction","Neutrale")}
            },
            "Asset Coinvolti": {
                "rich_text": [{"text": {"content": ", ".join(news.get("assets",[]))}}]
            },
            "Sommario": {
                "rich_text": [{"text": {"content": news.get("summary","")[:500]}}]
            },
            "Ciclo": {
                "select": {"name": "Lunedì" if cycle=="A" else "Giovedì"}
            },
        }
        try:
            notion.pages.create(
                parent={"database_id": NOTION_DB_NEWS},
                properties=props
            )
        except Exception as e:
            logger.error(f"  Errore Notion news '{title[:40]}': {e}")
            errors += 1

    logger.info(f"  ✓ News su Notion: {len(relevant)-errors}/{len(relevant)}")
    return errors == 0


# ── 4. AGGIORNA ESITO ─────────────────────────────────────────────
def update_trade_outcome(page_id: str, esito: str,
                         prezzo_entry: float = None,
                         prezzo_exit: float = None) -> bool:
    """
    Aggiorna l'esito di un trade nella pagina report.
    page_id si trova nell'URL della pagina Notion del report.

    Args:
        page_id:      ID della pagina (es. "abc123def456...")
        esito:        "✅ Vincente" | "❌ Perdente"
        prezzo_entry: prezzo di entrata
        prezzo_exit:  prezzo di uscita
    """
    notion = _client()
    props = {
        "Esito": {"select": {"name": esito}}
    }
    if prezzo_entry is not None:
        props["Prezzo Entry"] = {"number": prezzo_entry}
    if prezzo_exit is not None:
        props["Prezzo Exit"] = {"number": prezzo_exit}
    if prezzo_entry and prezzo_exit:
        pnl = round((prezzo_exit - prezzo_entry) / prezzo_entry * 100, 2)
        props["P&L %"] = {"number": pnl}

    try:
        notion.pages.update(page_id=page_id, properties=props)
        logger.info(f"  ✓ Esito aggiornato: {esito}")
        return True
    except Exception as e:
        logger.error(f"  ✗ Errore aggiornamento esito: {e}")
        return False
