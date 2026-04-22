# macroedge/config.py
# ================================================================
import os
from dotenv import load_dotenv
load_dotenv()

# ── Provider AI — scegli uno solo ────────────────────────────────
# Opzioni: "groq" (gratis) | "gemini" (gratis) | "mistral" (gratis) | "anthropic" (pagamento)
# Se AI_PROVIDER non è configurato come secret GitHub, usa "groq" come default
AI_PROVIDER = (os.getenv("AI_PROVIDER") or "groq").strip().lower()

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

# Qwen (Alibaba Cloud DashScope) — 1M token/giorno gratuiti → dashscope.aliyuncs.com
# Ottimo per prompt grandi: no limite 12k TPM come Groq
QWEN_API_KEY  = os.getenv("QWEN_API_KEY", "")
QWEN_MODEL    = "qwen-turbo"   # qwen-plus = più qualità | qwen-max = best (a pagamento)
QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

TELEGRAM_BOT_TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID        = os.getenv("TELEGRAM_CHAT_ID", "")

# ── Google Sheets (legacy — mantenuto per sheets_writer.py) ───────
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_SHEET_ID         = os.getenv("GOOGLE_SHEET_ID", "")

# ── Notion ────────────────────────────────────────────────────────
NOTION_API_KEY        = os.getenv("NOTION_API_KEY", "")
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID", "")
NOTION_DB_REPORTS     = os.getenv("NOTION_DB_REPORTS", "")
NOTION_DB_TECNICA     = os.getenv("NOTION_DB_TECNICA", "")
NOTION_DB_NEWS        = os.getenv("NOTION_DB_NEWS", "")

TIMEZONE = "Europe/Rome"

# ── EIA (U.S. Energy Information Administration) ─────────────────
# API gratuita → https://www.eia.gov/opendata/register.php
# Se non configurato, il fetcher usa solo i dati RSS/Yahoo
EIA_API_KEY = os.getenv("EIA_API_KEY", "")

# ================================================================
# TASSI DI POLICY BANCHE CENTRALI
# !! AGGIORNA MANUALMENTE DOPO OGNI DECISIONE DI TASSO !!
# Data ultimo aggiornamento: 2026-04
# ================================================================
POLICY_RATES = {
    # valuta: {"rate": float%, "bank": str, "bias": "hawkish|neutral|dovish", "region": str}
    # ── Nord America ───────────────────────────────────────────────
    "USD": {"rate": 4.50,  "bank": "Federal Reserve", "bias": "dovish",   "region": "north_america"},
    "CAD": {"rate": 3.25,  "bank": "Bank of Canada",  "bias": "dovish",   "region": "north_america"},
    "MXN": {"rate": 9.00,  "bank": "Banxico",         "bias": "dovish",   "region": "latam"},
    # ── Europa ─────────────────────────────────────────────────────
    "EUR": {"rate": 2.65,  "bank": "ECB",             "bias": "dovish",   "region": "europe"},
    "GBP": {"rate": 4.50,  "bank": "Bank of England", "bias": "neutral",  "region": "europe"},
    "CHF": {"rate": 0.25,  "bank": "SNB",             "bias": "dovish",   "region": "europe"},
    "NOK": {"rate": 4.50,  "bank": "Norges Bank",     "bias": "neutral",  "region": "europe"},
    # ── Asia/Pacifico ──────────────────────────────────────────────
    "JPY": {"rate": 0.50,  "bank": "Bank of Japan",   "bias": "hawkish",  "region": "apac"},
    "AUD": {"rate": 4.10,  "bank": "RBA",             "bias": "neutral",  "region": "apac"},
    "CNH": {"rate": 3.10,  "bank": "PBoC",            "bias": "dovish",   "region": "apac"},
    "INR": {"rate": 6.00,  "bank": "RBI",             "bias": "dovish",   "region": "apac"},
    "IDR": {"rate": 5.75,  "bank": "Bank Indonesia",  "bias": "neutral",  "region": "apac"},
    "MYR": {"rate": 3.00,  "bank": "BNM",             "bias": "neutral",  "region": "apac"},
    # ── Medio Oriente ──────────────────────────────────────────────
    "SAR": {"rate": 5.50,  "bank": "SAMA",            "bias": "neutral",  "region": "middle_east"},
    # ── Sud America ────────────────────────────────────────────────
    "BRL": {"rate": 13.75, "bank": "BACEN",           "bias": "hawkish",  "region": "latam"},
    "COP": {"rate": 9.50,  "bank": "BanRep Colombia", "bias": "dovish",   "region": "latam"},
    "CLP": {"rate": 5.00,  "bank": "BCCh Chile",      "bias": "neutral",  "region": "latam"},
    "ARS": {"rate": 32.00, "bank": "BCRA Argentina",  "bias": "hawkish",  "region": "latam"},
}

# Mappa ticker FX → coppia di valute (base, quote)
FX_PAIR_CURRENCIES = {
    # Majors
    "EURUSD=X": ("EUR", "USD"),
    "GBPUSD=X": ("GBP", "USD"),
    "JPY=X":    ("USD", "JPY"),
    "CHF=X":    ("USD", "CHF"),
    "CAD=X":    ("USD", "CAD"),
    "AUDUSD=X": ("AUD", "USD"),
    "EURJPY=X": ("EUR", "JPY"),
    "EURCHF=X": ("EUR", "CHF"),
    "EURGBP=X": ("EUR", "GBP"),
    # EM Asia
    "CNH=X":    ("USD", "CNH"),
    "INR=X":    ("USD", "INR"),
    "IDR=X":    ("USD", "IDR"),
    "MYR=X":    ("USD", "MYR"),
    # EM Latam
    "BRL=X":    ("USD", "BRL"),
    "MXN=X":    ("USD", "MXN"),
    "COP=X":    ("USD", "COP"),
    "CLP=X":    ("USD", "CLP"),
    "ARS=X":    ("USD", "ARS"),
    # Europa
    "NOK=X":    ("USD", "NOK"),
}

# ── Orari scheduler ───────────────────────────────────────────────
SCHEDULE_ANALYSIS_SUN = os.getenv("SCHEDULE_ANALYSIS_SUN", "19:30")
SCHEDULE_REPORT_MON   = os.getenv("SCHEDULE_REPORT_MON",   "05:30")
SCHEDULE_ANALYSIS_WED = os.getenv("SCHEDULE_ANALYSIS_WED", "19:30")
SCHEDULE_REPORT_THU   = os.getenv("SCHEDULE_REPORT_THU",   "05:30")

# ================================================================
# ASSET UNIVERSE — ~130 asset · 24 categorie
# ================================================================
ASSETS = [

    # ── Energia ──────────────────────────────────────────────────
    {"name": "Natural Gas",              "ticker": "NG=F",       "category": "energy",            "currency": "USD"},
    {"name": "Crude Oil WTI",            "ticker": "CL=F",       "category": "energy",            "currency": "USD"},
    {"name": "Brent Oil",                "ticker": "BZ=F",       "category": "energy",            "currency": "USD"},

    # ── Metalli preziosi ─────────────────────────────────────────
    {"name": "Gold",                     "ticker": "GC=F",       "category": "metals_precious",   "currency": "USD"},
    {"name": "Silver",                   "ticker": "SI=F",       "category": "metals_precious",   "currency": "USD"},
    {"name": "Platinum",                 "ticker": "PL=F",       "category": "metals_precious",   "currency": "USD"},
    {"name": "Palladium",                "ticker": "PA=F",       "category": "metals_precious",   "currency": "USD"},

    # ── Metalli industriali ──────────────────────────────────────
    {"name": "Copper futures",           "ticker": "HG=F",       "category": "metals_industrial", "currency": "USD"},
    {"name": "Base Metals ETF (DBB)",    "ticker": "DBB",        "category": "metals_industrial", "currency": "USD"},
    {"name": "Steel ETF (SLX)",          "ticker": "SLX",        "category": "metals_industrial", "currency": "USD"},
    {"name": "Global Mining ETF (PICK)", "ticker": "PICK",       "category": "metals_industrial", "currency": "USD"},

    # ── Indici USA ───────────────────────────────────────────────
    {"name": "S&P 500",                  "ticker": "^GSPC",      "category": "index_us",          "currency": "USD"},
    {"name": "NASDAQ 100",               "ticker": "^NDX",       "category": "index_us",          "currency": "USD"},
    {"name": "Russell 2000",             "ticker": "^RUT",       "category": "index_us",          "currency": "USD"},
    {"name": "Dow Jones",                "ticker": "^DJI",       "category": "index_us",          "currency": "USD"},

    # ── Indici Europa ────────────────────────────────────────────
    {"name": "Eurostoxx 50",             "ticker": "^STOXX50E",  "category": "index_eu",          "currency": "EUR"},
    {"name": "DAX",                      "ticker": "^GDAXI",     "category": "index_eu",          "currency": "EUR"},
    {"name": "CAC 40",                   "ticker": "^FCHI",      "category": "index_eu",          "currency": "EUR"},
    {"name": "FTSE MIB",                 "ticker": "FTSEMIB.MI", "category": "index_eu",          "currency": "EUR"},
    {"name": "IBEX 35",                  "ticker": "^IBEX",      "category": "index_eu",          "currency": "EUR"},
    {"name": "FTSE 100",                 "ticker": "^FTSE",      "category": "index_eu",          "currency": "GBP"},

    # ── Indici Asia/Pacifico ─────────────────────────────────────
    {"name": "Nikkei 225",               "ticker": "^N225",      "category": "index_asia",        "currency": "JPY"},
    {"name": "Hang Seng",                "ticker": "^HSI",       "category": "index_asia",        "currency": "HKD"},
    {"name": "Shanghai Composite",       "ticker": "000001.SS",  "category": "index_asia",        "currency": "CNY"},
    {"name": "ASX 200 (Australia)",      "ticker": "^AXJO",      "category": "index_asia",        "currency": "AUD"},

    # ── Valute principali ────────────────────────────────────────
    {"name": "EUR/USD",                  "ticker": "EURUSD=X",   "category": "fx",                "currency": "-"},
    {"name": "GBP/USD",                  "ticker": "GBPUSD=X",   "category": "fx",                "currency": "-"},
    {"name": "USD/JPY",                  "ticker": "JPY=X",      "category": "fx",                "currency": "-"},
    {"name": "DXY (Dollaro Index)",      "ticker": "DX-Y.NYB",   "category": "fx",                "currency": "USD"},
    {"name": "EUR/GBP",                  "ticker": "EURGBP=X",   "category": "fx",                "currency": "-"},
    {"name": "USD/CHF",                  "ticker": "CHF=X",      "category": "fx",                "currency": "-"},
    {"name": "USD/CAD",                  "ticker": "CAD=X",      "category": "fx",                "currency": "-"},
    {"name": "AUD/USD",                  "ticker": "AUDUSD=X",   "category": "fx",                "currency": "-"},
    {"name": "EUR/JPY",                  "ticker": "EURJPY=X",   "category": "fx",                "currency": "-"},
    {"name": "EUR/CHF",                  "ticker": "EURCHF=X",   "category": "fx",                "currency": "-"},
    {"name": "USD/CNH (Yuan offshore)",  "ticker": "CNH=X",      "category": "fx",                "currency": "-"},
    {"name": "USD/BRL",                  "ticker": "BRL=X",      "category": "fx",                "currency": "-"},
    {"name": "USD/MXN",                  "ticker": "MXN=X",      "category": "fx",                "currency": "-"},
    # FX Emergenti — APAC
    {"name": "USD/INR (Rupia Indiana)",  "ticker": "INR=X",      "category": "fx",                "currency": "-"},
    {"name": "USD/IDR (Rupia Indonesiana)","ticker": "IDR=X",    "category": "fx",                "currency": "-"},
    {"name": "USD/MYR (Ringgit Malesia)","ticker": "MYR=X",      "category": "fx",                "currency": "-"},
    # FX Emergenti — Latam
    {"name": "USD/COP (Peso Colombiano)","ticker": "COP=X",      "category": "fx",                "currency": "-"},
    {"name": "USD/CLP (Peso Cileno)",    "ticker": "CLP=X",      "category": "fx",                "currency": "-"},
    {"name": "USD/ARS (Peso Argentino)", "ticker": "ARS=X",      "category": "fx",                "currency": "-"},
    # FX Europa
    {"name": "USD/NOK (Corona Norvegese)","ticker": "NOK=X",     "category": "fx",                "currency": "-"},

    # ── ETF settoriali USA ───────────────────────────────────────
    {"name": "Energy Select ETF (XLE)",  "ticker": "XLE",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Financial ETF (XLF)",      "ticker": "XLF",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Technology ETF (XLK)",     "ticker": "XLK",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Defense ETF (ITA)",        "ticker": "ITA",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Healthcare ETF (XLV)",     "ticker": "XLV",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Utilities ETF (XLU)",      "ticker": "XLU",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Materials ETF (XLB)",      "ticker": "XLB",        "category": "etf_sector",        "currency": "USD"},
    {"name": "Industrials ETF (XLI)",    "ticker": "XLI",        "category": "etf_sector",        "currency": "USD"},

    # ── ETF Globali / MSCI ───────────────────────────────────────
    {"name": "MSCI World (URTH)",        "ticker": "URTH",       "category": "etf_global",        "currency": "USD"},
    {"name": "MSCI ACWI (ACWI)",         "ticker": "ACWI",       "category": "etf_global",        "currency": "USD"},
    {"name": "Japan ETF (EWJ)",          "ticker": "EWJ",        "category": "etf_global",        "currency": "USD"},
    {"name": "Saudi Arabia ETF (KSA)",   "ticker": "KSA",        "category": "etf_global",        "currency": "USD"},
    {"name": "ASEAN ETF (ASEA)",         "ticker": "ASEA",       "category": "etf_global",        "currency": "USD"},

    # ── Crypto ETF (quotati USA) ─────────────────────────────────
    {"name": "Bitcoin ETF (IBIT)",       "ticker": "IBIT",       "category": "crypto_etf",        "currency": "USD"},
    {"name": "Ethereum ETF (FETH)",      "ticker": "FETH",       "category": "crypto_etf",        "currency": "USD"},

    # ── Mercati Emergenti ETF ────────────────────────────────────
    {"name": "Emerging Markets (EEM)",   "ticker": "EEM",        "category": "etf_em",            "currency": "USD"},
    {"name": "EM ex-China (EMXC)",       "ticker": "EMXC",       "category": "etf_em",            "currency": "USD"},
    {"name": "India ETF (INDA)",         "ticker": "INDA",       "category": "etf_em",            "currency": "USD"},
    {"name": "Asia ex-Japan (AAXJ)",     "ticker": "AAXJ",       "category": "etf_em",            "currency": "USD"},
    {"name": "China Large Cap (FXI)",    "ticker": "FXI",        "category": "etf_em",            "currency": "USD"},
    {"name": "Korea ETF (EWY)",          "ticker": "EWY",        "category": "etf_em",            "currency": "USD"},

    # ── Sud America ETF ──────────────────────────────────────────
    {"name": "Latin America 40 (ILF)",   "ticker": "ILF",        "category": "etf_latam",         "currency": "USD"},
    {"name": "Brazil ETF (EWZ)",         "ticker": "EWZ",        "category": "etf_latam",         "currency": "USD"},
    {"name": "Mexico ETF (EWW)",         "ticker": "EWW",        "category": "etf_latam",         "currency": "USD"},

    # ── Australia / APAC ETF ─────────────────────────────────────
    {"name": "Australia ETF (EWA)",      "ticker": "EWA",        "category": "etf_global",        "currency": "USD"},
    {"name": "China ETF MSCI (MCHI)",    "ticker": "MCHI",       "category": "etf_em",            "currency": "USD"},

    # ── Soft Commodities ─────────────────────────────────────────
    {"name": "Cocoa futures (CC=F)",     "ticker": "CC=F",       "category": "softs",             "currency": "USD"},
    {"name": "Coffee futures (KC=F)",    "ticker": "KC=F",       "category": "softs",             "currency": "USD"},
    {"name": "Sugar #11 futures (SB=F)", "ticker": "SB=F",       "category": "softs",             "currency": "USD"},

    # ── Agricoltura / Cereali ────────────────────────────────────
    {"name": "Wheat ETF (WEAT)",         "ticker": "WEAT",       "category": "agriculture",       "currency": "USD"},
    {"name": "Corn ETF (CORN)",          "ticker": "CORN",       "category": "agriculture",       "currency": "USD"},
    {"name": "Soybean ETF (SOYB)",       "ticker": "SOYB",       "category": "agriculture",       "currency": "USD"},
    {"name": "Rice futures (ZR=F)",      "ticker": "ZR=F",       "category": "agriculture",       "currency": "USD"},
    {"name": "Broad Ag ETF (DBA)",       "ticker": "DBA",        "category": "agriculture",       "currency": "USD"},

    # ── Obbligazioni ─────────────────────────────────────────────
    {"name": "US 10Y Treasury Yield",    "ticker": "^TNX",       "category": "bonds",             "currency": "USD"},
    {"name": "US 2Y Treasury Yield",     "ticker": "^IRX",       "category": "bonds",             "currency": "USD"},
    {"name": "EU Govt Bond ETF (XGLE)",  "ticker": "XGLE.DE",    "category": "bonds",             "currency": "EUR"},
    {"name": "High Yield Bond (HYG)",    "ticker": "HYG",        "category": "bonds",             "currency": "USD"},
    {"name": "EM Bond ETF (EMB)",        "ticker": "EMB",        "category": "bonds",             "currency": "USD"},

    # ── Private Equity USA — paniere 5 ──────────────────────────
    {"name": "Blackstone (BX)",          "ticker": "BX",         "category": "pe_usa",            "currency": "USD"},
    {"name": "KKR & Co (KKR)",           "ticker": "KKR",        "category": "pe_usa",            "currency": "USD"},
    {"name": "Apollo Global (APO)",      "ticker": "APO",        "category": "pe_usa",            "currency": "USD"},
    {"name": "Carlyle Group (CG)",       "ticker": "CG",         "category": "pe_usa",            "currency": "USD"},
    {"name": "Ares Management (ARES)",   "ticker": "ARES",       "category": "pe_usa",            "currency": "USD"},

    # ── Azioni USA Mega-Cap ──────────────────────────────────────
    {"name": "Apple (AAPL)",             "ticker": "AAPL",       "category": "stocks_us",         "currency": "USD"},
    {"name": "Microsoft (MSFT)",         "ticker": "MSFT",       "category": "stocks_us",         "currency": "USD"},
    {"name": "NVIDIA (NVDA)",            "ticker": "NVDA",       "category": "stocks_us",         "currency": "USD"},
    {"name": "Amazon (AMZN)",            "ticker": "AMZN",       "category": "stocks_us",         "currency": "USD"},
    {"name": "Alphabet (GOOGL)",         "ticker": "GOOGL",      "category": "stocks_us",         "currency": "USD"},
    {"name": "Meta Platforms (META)",    "ticker": "META",       "category": "stocks_us",         "currency": "USD"},
    {"name": "JPMorgan Chase (JPM)",     "ticker": "JPM",        "category": "stocks_us",         "currency": "USD"},
    {"name": "ExxonMobil (XOM)",         "ticker": "XOM",        "category": "stocks_us",         "currency": "USD"},
    {"name": "Tesla (TSLA)",             "ticker": "TSLA",       "category": "stocks_us",         "currency": "USD"},

    # ── Azioni Italiane (Borsa Milano) ───────────────────────────
    {"name": "ENI (ENI.MI)",             "ticker": "ENI.MI",     "category": "stocks_eu_it",      "currency": "EUR"},
    {"name": "Stellantis (STLAM.MI)",    "ticker": "STLAM.MI",   "category": "stocks_eu_it",      "currency": "EUR"},
    {"name": "Intesa Sanpaolo (ISP.MI)", "ticker": "ISP.MI",     "category": "stocks_eu_it",      "currency": "EUR"},
    {"name": "Enel (ENEL.MI)",           "ticker": "ENEL.MI",    "category": "stocks_eu_it",      "currency": "EUR"},
    {"name": "Ferrari (RACE.MI)",        "ticker": "RACE.MI",    "category": "stocks_eu_it",      "currency": "EUR"},

    # ── Azioni Francesi (Euronext Paris) ─────────────────────────
    {"name": "LVMH (MC.PA)",             "ticker": "MC.PA",      "category": "stocks_eu_fr",      "currency": "EUR"},
    {"name": "TotalEnergies (TTE.PA)",   "ticker": "TTE.PA",     "category": "stocks_eu_fr",      "currency": "EUR"},
    {"name": "BNP Paribas (BNP.PA)",     "ticker": "BNP.PA",     "category": "stocks_eu_fr",      "currency": "EUR"},
    {"name": "Air Liquide (AI.PA)",      "ticker": "AI.PA",      "category": "stocks_eu_fr",      "currency": "EUR"},
    {"name": "Airbus (AIR.PA)",          "ticker": "AIR.PA",     "category": "stocks_eu_fr",      "currency": "EUR"},

    # ── Azioni UK (London Stock Exchange) ────────────────────────
    {"name": "Shell (SHEL.L)",           "ticker": "SHEL.L",     "category": "stocks_eu_uk",      "currency": "GBP"},
    {"name": "HSBC (HSBA.L)",            "ticker": "HSBA.L",     "category": "stocks_eu_uk",      "currency": "GBP"},
    {"name": "AstraZeneca (AZN.L)",      "ticker": "AZN.L",      "category": "stocks_eu_uk",      "currency": "GBP"},
    {"name": "BP (BP.L)",                "ticker": "BP.L",       "category": "stocks_eu_uk",      "currency": "GBP"},
    {"name": "Unilever (ULVR.L)",        "ticker": "ULVR.L",     "category": "stocks_eu_uk",      "currency": "GBP"},

    # ── Azioni Tedesche (XETRA) ──────────────────────────────────
    {"name": "SAP (SAP.DE)",             "ticker": "SAP.DE",     "category": "stocks_eu_de",      "currency": "EUR"},
    {"name": "Siemens (SIE.DE)",         "ticker": "SIE.DE",     "category": "stocks_eu_de",      "currency": "EUR"},
    {"name": "BASF (BAS.DE)",            "ticker": "BAS.DE",     "category": "stocks_eu_de",      "currency": "EUR"},
    {"name": "BMW (BMW.DE)",             "ticker": "BMW.DE",     "category": "stocks_eu_de",      "currency": "EUR"},
    {"name": "Allianz (ALV.DE)",         "ticker": "ALV.DE",     "category": "stocks_eu_de",      "currency": "EUR"},

    # ── Azioni Spagnole (BME Madrid) ─────────────────────────────
    {"name": "Inditex/Zara (ITX.MC)",    "ticker": "ITX.MC",     "category": "stocks_eu_es",      "currency": "EUR"},
    {"name": "Santander (SAN.MC)",       "ticker": "SAN.MC",     "category": "stocks_eu_es",      "currency": "EUR"},
    {"name": "Iberdrola (IBE.MC)",       "ticker": "IBE.MC",     "category": "stocks_eu_es",      "currency": "EUR"},
    {"name": "Telefonica (TEF.MC)",      "ticker": "TEF.MC",     "category": "stocks_eu_es",      "currency": "EUR"},

    # ── Azioni Cinesi (US-listed ADR / NYSE / NASDAQ) ────────────
    {"name": "Alibaba (BABA)",           "ticker": "BABA",       "category": "stocks_cn",         "currency": "USD"},
    {"name": "Baidu (BIDU)",             "ticker": "BIDU",       "category": "stocks_cn",         "currency": "USD"},
    {"name": "JD.com (JD)",              "ticker": "JD",         "category": "stocks_cn",         "currency": "USD"},
    {"name": "NIO (NIO)",                "ticker": "NIO",        "category": "stocks_cn",         "currency": "USD"},
    {"name": "PDD Holdings (PDD)",       "ticker": "PDD",        "category": "stocks_cn",         "currency": "USD"},

    # ── Azioni Giapponesi (Tokyo Stock Exchange) ─────────────────
    {"name": "Toyota (7203.T)",          "ticker": "7203.T",     "category": "stocks_jp",         "currency": "JPY"},
    {"name": "Sony (6758.T)",            "ticker": "6758.T",     "category": "stocks_jp",         "currency": "JPY"},
    {"name": "SoftBank (9984.T)",        "ticker": "9984.T",     "category": "stocks_jp",         "currency": "JPY"},
    {"name": "Nintendo (7974.T)",        "ticker": "7974.T",     "category": "stocks_jp",         "currency": "JPY"},
    {"name": "Keyence (6861.T)",         "ticker": "6861.T",     "category": "stocks_jp",         "currency": "JPY"},

    # ── Azioni Brasiliane (ADR NYSE) ─────────────────────────────
    {"name": "Petrobras (PBR)",          "ticker": "PBR",        "category": "stocks_br",         "currency": "USD"},
    {"name": "Vale (VALE)",              "ticker": "VALE",       "category": "stocks_br",         "currency": "USD"},
    {"name": "Itaú Unibanco (ITUB)",     "ticker": "ITUB",       "category": "stocks_br",         "currency": "USD"},
    {"name": "Embraer (ERJ)",            "ticker": "ERJ",        "category": "stocks_br",         "currency": "USD"},
    {"name": "Ambev (ABEV)",             "ticker": "ABEV",       "category": "stocks_br",         "currency": "USD"},

    # ── Azioni Messicane (ADR NYSE) ──────────────────────────────
    {"name": "América Móvil (AMX)",      "ticker": "AMX",        "category": "stocks_mx",         "currency": "USD"},
    {"name": "Cemex (CX)",               "ticker": "CX",         "category": "stocks_mx",         "currency": "USD"},
    {"name": "FEMSA (FMX)",              "ticker": "FMX",        "category": "stocks_mx",         "currency": "USD"},

    # ── Azioni Europee Small Cap ─────────────────────────────────
    {"name": "BE Semiconductor (BESI)",  "ticker": "BESI.AS",    "category": "eu_smallcap",       "currency": "EUR"},
    {"name": "Aalberts Industries",      "ticker": "AALB.AS",    "category": "eu_smallcap",       "currency": "EUR"},
    {"name": "Fluidra SA (FDR)",         "ticker": "FDR.MC",     "category": "eu_smallcap",       "currency": "EUR"},
    {"name": "Alfen NV",                 "ticker": "ALFEN.AS",   "category": "eu_smallcap",       "currency": "EUR"},
    {"name": "Eramet SA",                "ticker": "ERA.PA",     "category": "eu_smallcap",       "currency": "EUR"},

    # ── Azioni Asiatiche Small Cap ───────────────────────────────
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
    # Aggregati macro
    "US_MEGACAP":    ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "JPM", "XOM", "TSLA"],
    "EU_BLUECHIP":   ["ENI.MI", "STLAM.MI", "MC.PA", "TTE.PA", "SAP.DE", "SIE.DE", "SHEL.L", "ITX.MC"],
    "ASIA_BLUECHIP": ["7203.T", "6758.T", "9984.T", "BABA", "BIDU"],
    "LATAM":         ["ILF", "EWZ", "EWW", "PBR", "VALE", "ITUB"],
    # Settori / temi
    "PE_USA":        ["BX", "KKR", "APO", "CG", "ARES"],
    "EU_SMALLCAP":   ["BESI.AS", "AALB.AS", "FDR.MC", "ALFEN.AS", "ERA.PA"],
    "ASIA_SMALLCAP": ["2382.TW", "3711.TW", "036570.KS", "6981.T", "6920.T"],
    "CEREALI":       ["WEAT", "CORN", "SOYB", "ZR=F", "DBA"],
    "METALLI_IND":   ["DBB", "SLX", "PICK", "HG=F"],
    "METALLI_PZ":    ["GC=F", "SI=F", "PL=F", "PA=F"],
    "CRYPTO_ETF":    ["IBIT", "FETH"],
    "EM":            ["EEM", "EMXC", "INDA", "AAXJ", "KSA", "ASEA"],
    "EU_INDICES":    ["^STOXX50E", "^GDAXI", "^FCHI", "FTSEMIB.MI", "^IBEX", "^FTSE"],
    "ASIA_INDICES":  ["^N225", "^HSI", "000001.SS", "^AXJO"],
    "FX_MAJOR":      ["EURUSD=X", "GBPUSD=X", "JPY=X", "CHF=X", "CAD=X", "AUDUSD=X"],
    "FX_EM_ASIA":    ["CNH=X", "INR=X", "IDR=X", "MYR=X"],
    "FX_EM_LATAM":   ["BRL=X", "MXN=X", "COP=X", "CLP=X"],
    "FX_EUROPE":     ["NOK=X"],
    "BONDS":         ["^TNX", "^IRX", "HYG", "EMB"],
    "APAC_ETF":      ["EWJ", "MCHI", "EWA", "INDA", "EWY", "AAXJ"],
    "LATAM_ETF":     ["EWZ", "EWW", "ILF"],
    "CB_CORRELATIONS_FX": ["AUDUSD=X", "CAD=X", "BRL=X", "IDR=X", "CLP=X", "NOK=X"],
}

# ================================================================
# MACRO REGIONS — raggruppa valute per area geografica
# ================================================================
MACRO_REGIONS = {
    "north_america": {
        "label": "Nord America",
        "currencies": ["USD", "CAD"],
        "key_assets": ["^GSPC", "^NDX", "^DJI", "^RUT", "CL=F", "NG=F"],
        "cb_focus":   ["Federal Reserve", "Bank of Canada"],
    },
    "europe": {
        "label": "Europa",
        "currencies": ["EUR", "GBP", "CHF", "NOK"],
        "key_assets": ["^STOXX50E", "^GDAXI", "^FCHI", "^FTSE", "XGLE.DE"],
        "cb_focus":   ["ECB", "Bank of England", "SNB", "Norges Bank"],
    },
    "apac": {
        "label": "Asia/Pacifico",
        "currencies": ["JPY", "AUD", "CNH", "INR", "IDR", "MYR"],
        "key_assets": ["^N225", "^HSI", "000001.SS", "^AXJO", "EWA", "MCHI", "INDA"],
        "cb_focus":   ["Bank of Japan", "RBA", "PBoC", "RBI", "Bank Indonesia", "BNM"],
    },
    "latam": {
        "label": "Sud America",
        "currencies": ["BRL", "MXN", "COP", "CLP", "ARS"],
        "key_assets": ["EWZ", "EWW", "ILF", "PBR", "VALE"],
        "cb_focus":   ["BACEN", "Banxico", "BanRep Colombia", "BCCh Chile", "BCRA Argentina"],
    },
    "middle_east": {
        "label": "Medio Oriente",
        "currencies": ["SAR"],
        "key_assets": ["KSA"],
        "cb_focus":   ["SAMA"],
    },
}

# ================================================================
# CB → CURRENCY → COMMODITY CORRELATIONS
# Correlazioni strutturali tra politica monetaria, FX e commodity
# ================================================================
CB_COMMODITY_CORRELATIONS = {
    "AUD": {
        "bank":        "RBA",
        "commodities": ["GC=F", "HG=F", "PICK", "DBB"],
        "tickers_fx":  ["AUDUSD=X"],
        "rationale":   "Australia è grande esportatore di oro, rame e minerali ferrosi. AUD↑ → commodity demand forte.",
        "correlation":  "positiva",  # AUD si muove con i metalli
    },
    "CAD": {
        "bank":        "Bank of Canada",
        "commodities": ["CL=F", "BZ=F", "NG=F"],
        "tickers_fx":  ["CAD=X"],
        "rationale":   "Canada è il maggior fornitore di petrolio agli USA. CAD↑ quando il WTI sale.",
        "correlation":  "positiva",
    },
    "BRL": {
        "bank":        "BACEN",
        "commodities": ["KC=F", "SOYB", "CORN"],
        "tickers_fx":  ["BRL=X"],
        "rationale":   "Brasile = 1° esportatore di caffè e soia. BRL si rafforza con le soft commodity.",
        "correlation":  "positiva",
    },
    "IDR": {
        "bank":        "Bank Indonesia",
        "commodities": ["DBB", "DBA"],
        "tickers_fx":  ["IDR=X"],
        "rationale":   "Indonesia = principale esportatore di nichel e olio di palma. IDR legata ai metalli industriali.",
        "correlation":  "positiva",
    },
    "MYR": {
        "bank":        "BNM",
        "commodities": ["DBA"],
        "tickers_fx":  ["MYR=X"],
        "rationale":   "Malaysia = grande esportatore di olio di palma e gas naturale liquefatto.",
        "correlation":  "positiva",
    },
    "CLP": {
        "bank":        "BCCh Chile",
        "commodities": ["HG=F", "DBB"],
        "tickers_fx":  ["CLP=X"],
        "rationale":   "Cile produce oltre il 25% del rame mondiale. CLP e HG=F sono quasi sincronizzati.",
        "correlation":  "positiva",
    },
    "NOK": {
        "bank":        "Norges Bank",
        "commodities": ["NG=F", "CL=F", "BZ=F"],
        "tickers_fx":  ["NOK=X"],
        "rationale":   "Norvegia è grande esportatore di gas e petrolio nel Nord Europa. NOK↑ con l'energia.",
        "correlation":  "positiva",
    },
    "JPY": {
        "bank":        "Bank of Japan",
        "commodities": ["GC=F", "^TNX"],
        "tickers_fx":  ["JPY=X", "EURJPY=X"],
        "rationale":   "JPY è valuta rifugio. Si apprezza in risk-off. Correlazione inversa con equity e bond yield USA.",
        "correlation":  "inversa",
    },
    "CHF": {
        "bank":        "SNB",
        "commodities": ["GC=F"],
        "tickers_fx":  ["CHF=X", "EURCHF=X"],
        "rationale":   "CHF è valuta rifugio come JPY. Si apprezza in crisi geopolitiche e risk-off globale.",
        "correlation":  "inversa",
    },
}

# Mappa categoria → etichetta leggibile (usata nel prompt AI)
CATEGORY_LABELS = {
    "energy":          "Energia",
    "metals_precious": "Metalli Preziosi",
    "metals_industrial":"Metalli Industriali",
    "index_us":        "Indici USA",
    "index_eu":        "Indici Europa",
    "index_asia":      "Indici Asia/Pacifico",
    "fx":              "Valute (FX)",
    "etf_sector":      "ETF Settoriali USA",
    "etf_global":      "ETF Globali / MSCI",
    "crypto_etf":      "Crypto ETF",
    "etf_em":          "ETF Mercati Emergenti",
    "etf_latam":       "ETF Sud America",
    "softs":           "Soft Commodities",
    "agriculture":     "Agricoltura / Cereali",
    "bonds":           "Obbligazioni",
    "pe_usa":          "Private Equity USA",
    "stocks_us":       "Azioni USA (Mega-Cap)",
    "stocks_eu_it":    "Azioni Italia",
    "stocks_eu_fr":    "Azioni Francia",
    "stocks_eu_uk":    "Azioni UK",
    "stocks_eu_de":    "Azioni Germania",
    "stocks_eu_es":    "Azioni Spagna",
    "stocks_cn":       "Azioni Cina (US-listed)",
    "stocks_jp":       "Azioni Giappone",
    "stocks_br":       "Azioni Brasile (ADR)",
    "stocks_mx":       "Azioni Messico (ADR)",
    "eu_smallcap":     "Azioni EU Small Cap",
    "asia_smallcap":   "Azioni Asia Small Cap",
}

# ================================================================
# FEED RSS
# ================================================================
RSS_FEEDS = [
    # ── Nord America ─────────────────────────────────────────────
    {"name": "Reuters Business",     "url": "https://feeds.reuters.com/reuters/businessNews",       "priority": 1, "region": "north_america"},
    {"name": "Reuters World",        "url": "https://feeds.reuters.com/Reuters/worldNews",          "priority": 1, "region": "global"},
    {"name": "Bloomberg Markets",    "url": "https://feeds.bloomberg.com/markets/news.rss",         "priority": 1, "region": "global"},
    {"name": "Financial Times",      "url": "https://www.ft.com/rss/home",                          "priority": 1, "region": "global"},
    {"name": "AP Business",          "url": "https://rsshub.app/apnews/topics/business",            "priority": 1, "region": "north_america"},
    {"name": "Federal Reserve",      "url": "https://www.federalreserve.gov/feeds/press_all.xml",   "priority": 1, "region": "north_america"},
    {"name": "Nasdaq News",          "url": "https://www.nasdaq.com/feed/rssoutbound?category=Markets", "priority": 1, "region": "north_america"},
    # ── Europa ────────────────────────────────────────────────────
    {"name": "ECB Releases",         "url": "https://www.ecb.europa.eu/rss/press.html",             "priority": 1, "region": "europe"},
    {"name": "CNBC Europe",          "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "priority": 1, "region": "europe"},
    {"name": "The Telegraph UK",     "url": "https://www.telegraph.co.uk/rss.xml",                  "priority": 2, "region": "europe"},
    {"name": "Il Sole 24 Ore",       "url": "https://www.ilsole24ore.com/rss/finanza-e-mercati.xml","priority": 2, "region": "europe"},
    {"name": "MilanoFinanza",        "url": "https://www.milanofinanza.it/rss",                     "priority": 2, "region": "europe"},
    # ── Medio Oriente ────────────────────────────────────────────
    {"name": "Al Jazeera Economy",   "url": "https://www.aljazeera.com/xml/rss/all.xml",            "priority": 1, "region": "middle_east"},
    # ── Asia/Pacifico ─────────────────────────────────────────────
    {"name": "Nikkei Asia Pacific",  "url": "https://asia.nikkei.com/rss/feed/nar",                 "priority": 1, "region": "apac"},
    # ── Sud America ───────────────────────────────────────────────
    {"name": "MercoPress Sud America","url": "https://en.mercopress.com/rss/",                      "priority": 2, "region": "latam"},
    # ── Globale / Mercati ─────────────────────────────────────────
    {"name": "CNBC Markets",         "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258", "priority": 2, "region": "global"},
    {"name": "Investing.com IT",     "url": "https://it.investing.com/rss/news_14.rss",             "priority": 2, "region": "global"},
    {"name": "TradingEconomics",     "url": "https://tradingeconomics.com/rss/news.aspx",           "priority": 2, "region": "global"},
    {"name": "Yahoo Finance Energy", "url": "https://finance.yahoo.com/rss/headline?s=XLE",         "priority": 2, "region": "global"},
    {"name": "Yahoo Finance Crypto", "url": "https://finance.yahoo.com/rss/headline?s=IBIT",        "priority": 2, "region": "global"},
    {"name": "Yahoo Finance EM",     "url": "https://finance.yahoo.com/rss/headline?s=EEM",         "priority": 2, "region": "global"},
    {"name": "Seeking Alpha",        "url": "https://seekingalpha.com/market_currents.xml",         "priority": 3, "region": "global"},
    {"name": "CoinDesk",             "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",      "priority": 3, "region": "global"},
    {"name": "MarketWatch",          "url": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines", "priority": 3, "region": "global"},
    {"name": "Kauppalehti (FI)",     "url": "https://www.kauppalehti.fi/5/i/rss/uutiset.rss",      "priority": 3, "region": "europe"},
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
    "nvidia", "apple", "tesla", "amazon", "microsoft",
    "china", "cina", "tariff", "dazio", "trump", "trade war",
]
