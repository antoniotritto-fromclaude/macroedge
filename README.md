# MacroEdge 🎯
## Sistema di analisi macro + tecnica con report automatici su Telegram

---

## Struttura del progetto

```
macroedge/
├── main.py                    ← entry point + scheduler
├── config.py                  ← configurazione asset, feed RSS, orari
├── requirements.txt
├── .env.example               ← copia in .env e compila
├── credentials.json           ← service account Google (scarica da Cloud Console)
│
├── data/
│   ├── price_fetcher.py       ← Yahoo Finance + indicatori tecnici (MA, RSI, ATR)
│   └── news_reader.py         ← RSS reader + classificazione impatto
│
├── core/
│   └── ai_analyzer.py         ← Claude API — incrocio news × tecnica
│
├── output/
│   ├── telegram_sender.py     ← formattazione e invio Telegram
│   └── sheets_writer.py       ← scrittura su Google Sheets
│
└── logs/                      ← log di sistema + cache dati + report JSON
```

---

## Setup in 15 minuti

### 1. Installa le dipendenze

```bash
cd macroedge
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configura le credenziali

```bash
cp .env.example .env
# Apri .env e compila con le tue chiavi
```

**Anthropic API Key**
→ https://console.anthropic.com → API Keys → Create Key

**Telegram Bot**
1. Scrivi a `@BotFather` → `/newbot` → dai un nome al bot
2. Salva il token (tipo: `1234567890:ABCDEF...`)
3. Crea un canale privato su Telegram → aggiungi il bot come admin
4. Manda un messaggio nel canale, poi visita:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Cerca `"chat":{"id": -100XXXXXXXXX}` → quello è il `TELEGRAM_CHAT_ID`

**Google Sheets Service Account**
1. Vai su https://console.cloud.google.com
2. Crea un nuovo progetto (es. "macroedge")
3. Abilita: **Google Sheets API** + **Google Drive API**
4. IAM e Admin → Service Account → Crea → scarica il JSON
5. Rinomina il JSON in `credentials.json` e mettilo nella cartella del progetto
6. Copia l'email del service account (es. `macroedge@progetto.iam.gserviceaccount.com`)
7. Apri il tuo Google Sheet → Condividi con quell'email (ruolo: Editor)
8. Copia l'ID del foglio dall'URL e mettilo in `.env`

> **Nota**: Il Google Sheet deve essere già configurato con i fogli giusti.
> Usa il file `MacroEdge_Setup.gs` (Apps Script) per crearlo automaticamente.

### 3. Testa le connessioni

```bash
# Testa Telegram
python main.py --test-telegram

# Testa Google Sheets
python main.py --test-sheets
```

### 4. Esegui un ciclo di test

```bash
# Ciclo A (→ report Lunedì)
python main.py --run-now A

# Ciclo B (→ report Giovedì)
python main.py --run-now B
```

### 5. Avvia in produzione

```bash
# Avvia lo scheduler (rimane in ascolto)
python main.py

# Oppure con nohup per tenerlo in background su un server
nohup python main.py > logs/scheduler.out 2>&1 &
```

---

## Come funziona il ciclo

```
DOMENICA 21:00
└── Raccolta dati:
    ├── Yahoo Finance → prezzi chiusura venerdì + indicatori (MA50/200, RSI, ATR)
    └── RSS feed (52h) → news sabato + domenica

LUNEDÌ 07:00
└── Analisi + Report:
    ├── Claude AI → incrocio news × tecnica → trade ideas
    ├── Telegram → messaggio nel canale privato
    └── Google Sheets → riga aggiunta in "📊 Report Storici"

MERCOLEDÌ 21:00
└── Raccolta dati (come sopra, ultime 30h)

GIOVEDÌ 07:00
└── Analisi + Report (come sopra)
```

---

## Aggiornare gli esiti (backtesting)

Dopo aver chiuso un trade, aggiorna l'esito nel Google Sheet:

```python
from output.sheets_writer import update_trade_outcome

# row_number = numero riga nel foglio "📊 Report Storici" (es. 3)
# ✅ = vincente, ❌ = perdente
update_trade_outcome(
    row_number=3,
    esito="✅",
    prezzo_entry=38.42,
    prezzo_exit=35.10
)
# P&L calcolato automaticamente: -8.6%
```

---

## Eseguire su un server cloud (opzionale)

Per tenere il sistema sempre attivo usa un VPS economico (Railway, Render free tier,
DigitalOcean, Hetzner) o anche un Raspberry Pi a casa.

```bash
# Con systemd (Linux)
sudo nano /etc/systemd/system/macroedge.service

# Contenuto:
[Unit]
Description=MacroEdge Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/macroedge
ExecStart=/home/ubuntu/macroedge/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Abilita e avvia
sudo systemctl enable macroedge
sudo systemctl start macroedge
sudo systemctl status macroedge
```

---

## Personalizzazioni

### Aggiungere asset
In `config.py`, nella lista `ASSETS`, aggiungi:
```python
{"name": "Bitcoin", "ticker": "BTC-USD", "category": "crypto", "currency": "USD"},
```

### Aggiungere feed RSS
In `config.py`, nella lista `RSS_FEEDS`, aggiungi:
```python
{"name": "MilanoFinanza", "url": "https://www.milanofinanza.it/rss", "priority": 2},
```

### Cambiare il modello Claude
In `config.py`:
```python
CLAUDE_MODEL = "claude-opus-4-5"  # più potente, più lento
# oppure
CLAUDE_MODEL = "claude-haiku-4-5-20251001"  # più veloce, meno costoso
```

---

*MacroEdge non fornisce consulenza finanziaria. I segnali generati sono strumenti
di supporto all'analisi e non costituiscono raccomandazioni di investimento.*
