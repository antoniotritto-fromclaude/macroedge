#!/usr/bin/env python3
# macroedge/setup_notion.py
# ================================================================
# Esegui UNA SOLA VOLTA per creare la struttura MacroEdge su Notion.
#
#   python setup_notion.py
#
# Cosa crea:
#   📁 MacroEdge HQ          ← pagina root nel tuo workspace
#   ├── 📊 Report Storici    ← un report per ogni lunedì/giovedì
#   ├── 📈 Dati Tecnici      ← snapshot prezzi e indicatori
#   └── 📰 News Log          ← notizie processate
#
# Alla fine stampa 3 ID da copiare in .env e nei Secrets GitHub.
# ================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from notion_client import Client
from config import NOTION_API_KEY, NOTION_PARENT_PAGE_ID


def create_reports_db(notion: Client, parent_id: str) -> str:
    """Crea il database 📊 Report Storici."""
    print("  Creazione database Report Storici...")
    db = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_id},
        title=[{"type": "text", "text": {"content": "📊 Report Storici"}}],
        icon={"type": "emoji", "emoji": "📊"},
        properties={
            # Titolo (obbligatorio, primo campo)
            "Nome":            {"title": {}},
            "Data":            {"date": {}},
            "Ciclo":           {"select": {"options": [
                {"name": "Lunedì (A)",  "color": "blue"},
                {"name": "Giovedì (B)", "color": "green"},
            ]}},
            "Bias":            {"select": {"options": [
                {"name": "Risk-On",  "color": "green"},
                {"name": "Risk-Off", "color": "red"},
                {"name": "Neutrale", "color": "yellow"},
            ]}},
            "Causa Bias":      {"rich_text": {}},
            "Settore":         {"rich_text": {}},
            "Direzione":       {"select": {"options": [
                {"name": "Long",  "color": "green"},
                {"name": "Short", "color": "red"},
            ]}},
            "Forza Segnale":   {"select": {"options": [
                {"name": "Alta",  "color": "red"},
                {"name": "Media", "color": "yellow"},
                {"name": "Bassa", "color": "gray"},
            ]}},
            "ETF 1":           {"rich_text": {}},
            "ETF 2":           {"rich_text": {}},
            "Azione 1":        {"rich_text": {}},
            "Azione 2":        {"rich_text": {}},
            "Azione 3":        {"rich_text": {}},
            "Azione 4":        {"rich_text": {}},
            "Timeframe":       {"rich_text": {}},
            "Esito":           {"select": {"options": [
                {"name": "⏳ In corso",  "color": "yellow"},
                {"name": "✅ Vincente",  "color": "green"},
                {"name": "❌ Perdente",  "color": "red"},
                {"name": "⏸ Annullato", "color": "gray"},
            ]}},
            "Prezzo Entry":    {"number": {"format": "number"}},
            "Prezzo Exit":     {"number": {"format": "number"}},
            "P&L %":           {"number": {"format": "percent"}},
            "Alert Dollaro":   {"checkbox": {}},
            "Divergenza Chiave": {"rich_text": {}},
            "Rationale":       {"rich_text": {}},
            "Sentiment Score": {"number": {"format": "number"}},
        }
    )
    db_id = db["id"]
    print(f"    ✓ Report Storici creato: {db_id}")
    return db_id


def create_tecnica_db(notion: Client, parent_id: str) -> str:
    """Crea il database 📈 Dati Tecnici."""
    print("  Creazione database Dati Tecnici...")
    db = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_id},
        title=[{"type": "text", "text": {"content": "📈 Dati Tecnici"}}],
        icon={"type": "emoji", "emoji": "📈"},
        properties={
            "Asset":       {"title": {}},
            "Data":        {"date": {}},
            "Ticker":      {"rich_text": {}},
            "Categoria":   {"select": {"options": [
                {"name": "energy",            "color": "orange"},
                {"name": "metals_precious",   "color": "yellow"},
                {"name": "metals_industrial", "color": "gray"},
                {"name": "index_us",          "color": "blue"},
                {"name": "index_eu",          "color": "purple"},
                {"name": "fx",                "color": "green"},
                {"name": "etf_sector",        "color": "pink"},
                {"name": "crypto_etf",        "color": "red"},
                {"name": "etf_em",            "color": "brown"},
                {"name": "etf_asia",          "color": "blue"},
                {"name": "etf_latam",         "color": "green"},
                {"name": "softs",             "color": "brown"},
                {"name": "agriculture",       "color": "green"},
                {"name": "bonds",             "color": "gray"},
                {"name": "pe_usa",            "color": "purple"},
                {"name": "eu_smallcap",       "color": "blue"},
                {"name": "asia_smallcap",     "color": "red"},
            ]}},
            "Prezzo":      {"number": {"format": "number"}},
            "Var 1D %":    {"number": {"format": "percent"}},
            "RSI":         {"number": {"format": "number"}},
            "Segnale RSI": {"rich_text": {}},
            "Trend":       {"rich_text": {}},
            "Ciclo":       {"select": {"options": [
                {"name": "Lunedì",   "color": "blue"},
                {"name": "Giovedì",  "color": "green"},
            ]}},
        }
    )
    db_id = db["id"]
    print(f"    ✓ Dati Tecnici creato: {db_id}")
    return db_id


def create_news_db(notion: Client, parent_id: str) -> str:
    """Crea il database 📰 News Log."""
    print("  Creazione database News Log...")
    db = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_id},
        title=[{"type": "text", "text": {"content": "📰 News Log"}}],
        icon={"type": "emoji", "emoji": "📰"},
        properties={
            "Titolo":          {"title": {}},
            "Data":            {"date": {}},
            "Fonte":           {"rich_text": {}},
            "Impatto":         {"select": {"options": [
                {"name": "Alta",   "color": "red"},
                {"name": "Media",  "color": "yellow"},
                {"name": "Bassa",  "color": "green"},
            ]}},
            "Direzione":       {"select": {"options": [
                {"name": "Bullish",  "color": "green"},
                {"name": "Bearish",  "color": "red"},
                {"name": "Neutrale", "color": "gray"},
            ]}},
            "Asset Coinvolti": {"rich_text": {}},
            "Sommario":        {"rich_text": {}},
            "Ciclo":           {"select": {"options": [
                {"name": "Lunedì",  "color": "blue"},
                {"name": "Giovedì", "color": "green"},
            ]}},
        }
    )
    db_id = db["id"]
    print(f"    ✓ News Log creato: {db_id}")
    return db_id


def create_hq_page(notion: Client) -> str:
    """Crea la pagina root MacroEdge HQ nel workspace."""
    if NOTION_PARENT_PAGE_ID:
        print(f"  Usando pagina parent esistente: {NOTION_PARENT_PAGE_ID}")
        return NOTION_PARENT_PAGE_ID

    print("  Creazione pagina MacroEdge HQ nel workspace...")
    page = notion.pages.create(
        parent={"type": "workspace", "workspace": True},
        icon={"type": "emoji", "emoji": "🎯"},
        cover={"type": "external", "external": {"url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3"}},
        properties={
            "title": [{"type": "text", "text": {"content": "🎯 MacroEdge HQ"}}]
        },
        children=[
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": "MacroEdge — Trading Intelligence System"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {
                    "content": "Sistema automatizzato di analisi macro + tecnica. Report ogni lunedì e giovedì mattina su Telegram."
                }}]}
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": "I database sono sotto questa pagina. Per aggiornare l'esito di un trade, apri il report in '📊 Report Storici' e modifica il campo 'Esito'."}}],
                    "icon": {"type": "emoji", "emoji": "💡"},
                }
            }
        ]
    )
    page_id = page["id"]
    print(f"    ✓ MacroEdge HQ creato: {page_id}")
    return page_id


def main():
    print("\n🎯 MacroEdge — Setup Notion")
    print("=" * 45)

    if not NOTION_API_KEY:
        print("\n❌  NOTION_API_KEY non trovata in .env")
        print("   1. Vai su https://www.notion.so/my-integrations")
        print("   2. Crea una nuova integration → copia il token")
        print("   3. Aggiungila in .env: NOTION_API_KEY=secret_...")
        sys.exit(1)

    print(f"\n API Key: {NOTION_API_KEY[:20]}...")
    notion = Client(auth=NOTION_API_KEY)

    # Verifica connessione
    try:
        me = notion.users.me()
        print(f" Connesso come: {me.get('name','N/A')}")
    except Exception as e:
        print(f"\n❌  Errore connessione Notion: {e}")
        print("   Verifica che la API key sia corretta e che l'integration")
        print("   sia stata aggiunta alla pagina dove vuoi creare i database.")
        sys.exit(1)

    print("\n Creazione struttura MacroEdge...")
    hq_id     = create_hq_page(notion)
    reports_id = create_reports_db(notion, hq_id)
    tecnica_id = create_tecnica_db(notion, hq_id)
    news_id    = create_news_db(notion, hq_id)

    # ── Stampa il riepilogo da copiare ────────────────────────────
    print("\n" + "=" * 45)
    print("✅  Setup completato! Copia questi valori in .env")
    print("    e nei Secrets di GitHub:\n")
    print(f"NOTION_API_KEY={NOTION_API_KEY}")
    print(f"NOTION_PARENT_PAGE_ID={hq_id}")
    print(f"NOTION_DB_REPORTS={reports_id}")
    print(f"NOTION_DB_TECNICA={tecnica_id}")
    print(f"NOTION_DB_NEWS={news_id}")
    print("\n" + "=" * 45)
    print(" Link diretto alla pagina MacroEdge HQ:")
    print(f" https://notion.so/{hq_id.replace('-','')}")
    print()

    # Salva automaticamente in un file locale per comodità
    config_out = {
        "NOTION_API_KEY":        NOTION_API_KEY,
        "NOTION_PARENT_PAGE_ID": hq_id,
        "NOTION_DB_REPORTS":     reports_id,
        "NOTION_DB_TECNICA":     tecnica_id,
        "NOTION_DB_NEWS":        news_id,
    }
    with open("notion_ids.json", "w") as f:
        import json
        json.dump(config_out, f, indent=2)
    print(" IDs salvati anche in notion_ids.json")
    print(" ⚠️  Non committare notion_ids.json su GitHub!\n")


if __name__ == "__main__":
    main()
