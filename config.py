# macroedge/config.py — versione espansa
# ================================================================
import os
from dotenv import load_dotenv
load_dotenv()

# ── Provider AI — scegli uno solo ────────────────────────────────
# Opzioni: "groq" (gratis) | "gemini" (gratis) | "mistral" (gratis) | "anthropic" (pagamento)
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")

# Groq — CONSIGLIATO (gratis, veloce) → groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"

# Google Gemini — gratis → aistudio.google.com
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-1.5-flash"

# Mistral — tier gratuito → console.mistral.ai
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL   = "mistral-small-latest"

# Anthropic Claude — a pagamento (fallback) → console.anthropic.com
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL      = "claude-opus-4-5"

TELEGRAM_BOT_TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID        = os.getenv("TELEGRAM_CHAT_ID", "")

# ── Google Sheets (legacy — mantenuto per sheets_writer.py) ───────
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_SHEET_ID         = os.getenv("GOOGLE_SHEET_ID", "")

# ── Notion ────────────────────────────────────────────────────────
# Ottieni il token su: https://www.notion.so/my-integrations
NOTION_API_KEY        = os.getenv("NOTION_API_KEY", "")
# ID della pagina root (MacroEdge HQ) — generato da setup_notion.py
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID", "")
# ID dei tre database — generati da setup_notion.py
NOTION_DB_REPORTS     = os.getenv("NOTION_DB_REPORTS", "")
NOTION_DB_TECNICA     = os.getenv("NOTION_DB_TECNICA", "")
NOTION_DB_NEWS        = os.getenv("NOTION_DB_NEWS", "")

TIMEZONE = "Europe/Rome"

# ================================================================
# ASSET UNIVERSE — 65 asset · 14 categorie
# ================================================================
ASSETS = [

    # ── Energia ──────────────────────────────────────────────────
    {"name": "Natural Gas",              "ticker": "NG=F",       "category": "energy",            "currency": "USD"},
    {"name": "Crude Oil WTI",            "ticker": "CL=F",       "category": "energy",            "currency": "USD"},
    {"name": "Brent Oil",                "ticker": "BZ=F",       "category": "energy",            "currency": "USD"},

    # ── Metalli preziosi ─────────────────────────────────────────
    {"name": "Gold",                     "ticker": "GC=F",       "category": "metals_precious",   "currency": "USD"},
    {"name": "Silver",                   "ticker": "SI=F",       "category": "metals_precious",   "currency": "USD"},

    # ── Metalli industriali ──────────────────────────────────────
    # DBB = basket (zinco + alluminio + rame) — proxy per zinco e piombo
    {"name": "Base Metals ETF (DBB)",    "ticker": "DBB",        "category": "metals_industrial", "currency": "USD"},
    # SLX = acciaio e minerale di ferro
    {"name": "Steel ETF (SLX)",          "ticker": "SLX",        "category": "metals_industrial", "currency": "USD"},
    # PICK = miniere globali (ferro, rame, carbone)
    {"name": "Global Mining ETF (PICK)", "ticker": "PICK",       "category": "metals_industrial", "currency": "USD"},
    # Rame come proxy commodities industriali
    {"name": "Copper futures",           "ticker": "HG=F",       "category": "metals_industrial", "currency": "USD"},

    # ── Indici USA ───────────────────────────────────────────────
    {"name": "S&P 500",                  "ticker": "^GSPC",      "category": "index_us",          "currency": "USD"},
    {"name": "NASDAQ 100",               "ticker": "^NDX",       "category": "index_us",          "currency": "USD"},
    {"name": "Russell 2000",             "ticker": "^RUT",       "category": "index_us",          "currency": "USD"},

    # ── Indici Europa ────────────────────────────────────────────
    {"name": "Eurostoxx 50",             "ticker": "^STOXX50E",  "category": "index_eu",          "currency": "EUR"},
    {"name": "DAX",                      "ticker": "^GDAXI",     "category": "index_eu",          "currency": "EUR"},
    {"name": "CAC 40",                   "ticker": "^FCHI",      "category": "index_eu",          "currency": "EUR"},
    {"name": "FTSE MIB",                 "ticker": "FTSEMIB.MI", "category": "index_eu",          "currency": "EUR"},
    {"name": "IBEX 35",                  "ticker": "^IBEX",      "category": "index_eu",          "currency": "EUR"},

    # ── Valute ───────────────────────────────────────────────────
    {"name": "EUR/USD",                  "ticker": "EURUSD=X",   "category": "fx",                "currency": "-"},
    {"name": "GBP/USD",                  "ticker": "GBPUSD=X",   "category": "fx",                "currency": "-"},
    {"name": "USD/JPY",                  "ticker": "JPY=X",      "category": "fx",                "currency": "-"},
    {"name": "DXY (Dollaro Index)",      "ticker": "DX-Y.NYB",   "category": "fx",                "currency": "USD"},
    {"name": "EUR/GBP",                  "ticker": "EURGBP=X",   "category": "fx",                "currency": "-"},

    # ── ETF settoriali USA ───────────────────────────────────────
    {"name": "Energy Select ETF (XLE)",  "ticker": "XLE",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Financial ETF (XLF)",      "ticker": "XLF",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Technology ETF (XLK)",     "ticker": "XLK",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Defense ETF (ITA)",        "ticker": "ITA",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Healthcare ETF (XLV)",     "ticker": "XLV",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Utilities ETF (XLU)",      "ticker": "XLU",        "category": "etf_sector",        "currency": "USD"},

    # ── Crypto ETF (quotati USA) ─────────────────────────────────
    {"name": "Bitcoin ETF (IBIT)",       "ticker": "IBIT",       "category": "crypto_etf",        "currency": "USD"},
    {"name": "Ethereum ETF (FETH)",      "ticker": "FETH",       "category": "crypto_etf",        "currency": "USD"},

    # ── Mercati Emergenti ETF ────────────────────────────────────
    {"name": "Emerging Markets (EEM)",   "ticker": "EEM",        "category": "etf_em",            "currency": "USD"},
    {"name": "EM ex-China (EMXC)",       "ticker": "EMXC",       "category": "etf_em",            "currency": "USD"},
    {"name": "India ETF (INDA)",         "ticker": "INDA",       "category": "etf_em",            "currency": "USD"},

    # ── Far East ex-Japan ETF ────────────────────────────────────
    {"name": "Asia ex-Japan (AAXJ)",     "ticker": "AAXJ",       "category": "etf_asia",          "currency": "USD"},
    {"name": "China Large Cap (FXI)",    "ticker": "FXI",        "category": "etf_asia",          "currency": "USD"},
    {"name": "Korea ETF (EWY)",          "ticker": "EWY",        "category": "etf_asia",          "currency": "USD"},

    # ── Sud America ETF ──────────────────────────────────────────
    {"name": "Latin America 40 (ILF)",   "ticker": "ILF",        "category": "etf_latam",         "currency": "USD"},
    {"name": "Brazil ETF (EWZ)",         "ticker": "EWZ",        "category": "etf_latam",         "currency": "USD"},
    {"name": "Mexico ETF (EWW)",         "ticker": "EWW",        "category": "etf_latam",         "currency": "USD"},

    # ── Soft Commodities ─────────────────────────────────────────
    # NIB = iPath Bloomberg Cocoa Subindex ETN
    {"name": "Cocoa ETN (NIB)",          "ticker": "NIB",        "category": "softs",             "currency": "USD"},
    # JO = iPath Bloomberg Coffee Subindex ETN
    {"name": "Coffee ETN (JO)",          "ticker": "JO",         "category": "softs",             "currency": "USD"},
    # SGG = iPath Bloomberg Sugar Subindex ETN
    {"name": "Sugar ETN (SGG)",          "ticker": "SGG",        "category": "softs",             "currency": "USD"},

    # ── Agricoltura / Cereali ────────────────────────────────────
    {"name": "Wheat ETF (WEAT)",         "ticker": "WEAT",       "category": "agriculture",       "currency": "USD"},
    {"name": "Corn ETF (CORN)",          "ticker": "CORN",       "category": "agriculture",       "currency": "USD"},
    {"name": "Soybean ETF (SOYB)",       "ticker": "SOYB",       "category": "agriculture",       "currency": "USD"},
    {"name": "Rice futures (ZR=F)",      "ticker": "ZR=F",       "category": "agriculture",       "currency": "USD"},
    {"name": "Broad Ag ETF (DBA)",       "ticker": "DBA",        "category": "agriculture",       "currency": "USD"},

    # ── Obbligazioni ─────────────────────────────────────────────
    {"name": "US 10Y Treasury Yield",    "ticker": "^TNX",       "category": "bonds",             "currency": "USD"},
    {"name": "US 2Y Treasury Yield",     "ticker": "^IRX",       "category": "bonds",             "currency": "USD"},
    {"name": "EU Bund ETF (IBTE)",       "ticker": "IBTE.DE",    "category": "bonds",             "currency": "EUR"},
    {"name": "High Yield Bond (HYG)",    "ticker": "HYG",        "category": "bonds",             "currency": "USD"},

    # ── Private Equity USA — paniere 5 ──────────────────────────
    {"name": "Blackstone (BX)",          "ticker": "BX",         "category": "pe_usa",            "currency": "USD"},
    {"name": "KKR & Co (KKR)",           "ticker": "KKR",        "category": "pe_usa",            "currency": "USD"},
    {"name": "Apollo Global (APO)",      "ticker": "APO",        "category": "pe_usa",            "currency": "USD"},
    {"name": "Carlyle Group (CG)",       "ticker": "CG",         "category": "pe_usa",            "currency": "USD"},
    {"name": "Ares Management (ARES)",   "ticker": "ARES",       "category": "pe_usa",            "currency": "USD"},

    # ── Azioni Europee Small Cap — paniere 5 ────────────────────
    # Diversificati per paese e settore: NL, NL, ES, NL, FR
    {"name": "BE Semiconductor (BESI)",  "ticker": "BESI.AS",    "category": "eu_smallcap",       "currency": "EUR"},
    {"name": "Aalberts Industries",      "ticker": "AALB.AS",    "category": "eu_smallcap",       "currency": "EUR"},
    {"name": "Fluidra SA (FDR)",         "ticker": "FDR.MC",     "category": "eu_smallcap",       "currency": "EUR"},
    {"name": "Alfen NV",                 "ticker": "ALFEN.AS",   "category": "eu_smallcap",       "currency": "EUR"},
    {"name": "Eramet SA",                "ticker": "ERA.PA",     "category": "eu_smallcap",       "currency": "EUR"},

    # ── Azioni Asiatiche Small Cap — paniere 5 ──────────────────
    # Mix Taiwan (tech), Korea (gaming/materiali), Giappone (elettronica)
    {"name": "Quanta Computer (TW)",     "ticker": "2382.TW",    "category": "asia_smallcap",     "currency": "TWD"},
    {"name": "ASE Technology (TW)",      "ticker": "3711.TW",    "category": "asia_smallcap",     "currency": "TWD"},
    {"name": "NCsoft (KR)",              "ticker": "036570.KS",  "category": "asia_smallcap",     "currency": "KRW"},
    {"name": "Murata Manufacturing (JP)","ticker": "6981.T",     "category": "asia_smallcap",     "currency": "JPY"},
    {"name": "Lasertec Corp (JP)",       "ticker": "6920.T",     "category": "asia_smallcap",     "currency": "JPY"},
]

# ================================================================
# PANIERI LOGICI — usati nel prompt AI per contesto
# ================================================================
BASKETS = {
    "PE_USA":        ["BX", "KKR", "APO", "CG", "ARES"],
    "EU_SMALLCAP":   ["BESI.AS", "AALB.AS", "FDR.MC", "ALFEN.AS", "ERA.PA"],
    "ASIA_SMALLCAP": ["2382.TW", "3711.TW", "036570.KS", "6981.T", "6920.T"],
    "CEREALI":       ["WEAT", "CORN", "SOYB", "ZR=F", "DBA"],
    "METALLI_IND":   ["DBB", "SLX", "PICK", "HG=F"],
    "CRYPTO_ETF":    ["IBIT", "FETH"],
    "EM":            ["EEM", "EMXC", "INDA", "AAXJ"],
    "LATAM":         ["ILF", "EWZ", "EWW"],
    "SOFTS":         ["NIB", "JO", "SGG"],
    "EU_INDICES":    ["^STOXX50E", "^GDAXI", "^FCHI", "FTSEMIB.MI", "^IBEX"],
}

# ================================================================
# FEED RSS
# ================================================================
RSS_FEEDS = [
    {"name": "Reuters Business",     "url": "https://feeds.reuters.com/reuters/businessNews",       "priority": 1},
    {"name": "Reuters World",        "url": "https://feeds.reuters.com/Reuters/worldNews",          "priority": 1},
    {"name": "Bloomberg Markets",    "url": "https://feeds.bloomberg.com/markets/news.rss",         "priority": 1},
    {"name": "Financial Times",      "url": "https://www.ft.com/rss/home",                          "priority": 1},
    {"name": "AP Business",          "url": "https://rsshub.app/apnews/topics/business",            "priority": 1},
    {"name": "Federal Reserve",      "url": "https://www.federalreserve.gov/feeds/press_all.xml",   "priority": 1},
    {"name": "ECB Releases",         "url": "https://www.ecb.europa.eu/rss/press.html",             "priority": 1},
    {"name": "Investing.com IT",     "url": "https://it.investing.com/rss/news_14.rss",             "priority": 2},
    {"name": "TradingEconomics",     "url": "https://tradingeconomics.com/rss/news.aspx",           "priority": 2},
    {"name": "CNBC Markets",         "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258", "priority": 2},
    {"name": "Yahoo Finance Energy", "url": "https://finance.yahoo.com/rss/headline?s=XLE",         "priority": 2},
    {"name": "Yahoo Finance Crypto", "url": "https://finance.yahoo.com/rss/headline?s=IBIT",        "priority": 2},
    {"name": "Yahoo Finance EM",     "url": "https://finance.yahoo.com/rss/headline?s=EEM",         "priority": 2},
    {"name": "Il Sole 24 Ore",       "url": "https://www.ilsole24ore.com/rss/finanza-e-mercati.xml","priority": 2},
    {"name": "MilanoFinanza",        "url": "https://www.milanofinanza.it/rss",                     "priority": 2},
    {"name": "Seeking Alpha",        "url": "https://seekingalpha.com/market_currents.xml",         "priority": 3},
    {"name": "CoinDesk",             "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",      "priority": 3},
    {"name": "Nasdaq News",          "url": "https://www.nasdaq.com/feed/rssoutbound?category=Markets", "priority": 3},
    {"name": "MarketWatch",          "url": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines", "priority": 3},
    {"name": "Kauppalehti (FI)",     "url": "https://www.kauppalehti.fi/5/i/rss/uutiset.rss",      "priority": 3},
]

HIGH_IMPACT_KEYWORDS = [
    "fed", "federal reserve", "fomc", "ecb", "bce", "banca centrale",
    "rate cut", "rate hike", "taglio tassi", "rialzo tassi",
    "powell", "lagarde", "interest rate", "tasso d'interesse",
    "cpi", "inflazione", "inflation", "gdp", "pil", "unemployment",
    "nonfarm", "jobs report", "opec", "iran", "russia", "ukraine",
    "guerra", "war", "ceasefire", "pace", "peace", "embargo",
    "bitcoin", "crypto", "btc", "ethereum",
    "recession", "recessione", "default", "crash",
    "cocoa", "cacao", "coffee", "caffè", "wheat", "grano",
]
