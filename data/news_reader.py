# macroedge/data/news_reader.py
# ================================================================
# Legge i feed RSS, classifica le notizie per impatto e direzione,
# e le prepara per il prompt AI.
#
# Funzioni pubbliche:
#   fetch_feed(feed, hours_back)              → list[dict]
#   fetch_all_news(feeds, hours_back)         → list[dict]
#   format_news_for_ai(news_list, max_items)  → str
# ================================================================

import feedparser
import logging
import re
import requests
import time
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import Optional

from config import HIGH_IMPACT_KEYWORDS, ASSETS

logger = logging.getLogger("macroedge.news_reader")

# ── Keyword maps per riconoscimento asset/categoria ───────────────
_ASSET_KEYWORDS: dict = {}
for _a in ASSETS:
    _ASSET_KEYWORDS[_a["ticker"]] = [
        _a["name"].lower(),
        _a["ticker"].lower().replace("=f", "").replace("=x", "").replace("^", ""),
    ]

_CATEGORY_KEYWORDS = {
    "energy":             ["oil", "gas", "energy", "opec", "petrolio", "energia", "crude", "brent", "lng"],
    "metals_precious":    ["gold", "silver", "oro", "argento", "precious metals"],
    "metals_industrial":  ["copper", "steel", "iron", "rame", "acciaio", "aluminum", "alluminio"],
    "index_us":           ["s&p 500", "nasdaq", "dow jones", "wall street", "s&p500", "sp500"],
    "index_eu":           ["eurostoxx", "dax", "cac 40", "ftse mib", "ibex", "borse europee"],
    "fx":                 ["dollar", "euro", "yen", "sterling", "forex", "dollaro", "valuta", "dxy", "currency"],
    "crypto_etf":         ["bitcoin", "btc", "ethereum", "eth", "crypto", "digital asset", "criptovaluta"],
    "bonds":              ["treasury", "yield", "bond", "spread", "btp", "bund", "obbligazioni", "tassi"],
    "agriculture":        ["wheat", "corn", "soy", "grain", "grano", "mais", "cereali", "soybean"],
    "softs":              ["cocoa", "coffee", "sugar", "cacao", "caffè", "zucchero"],
    "etf_em":             ["emerging market", "mercati emergenti", "cina", "china", "india", "brasile"],
}

_BULLISH_KEYWORDS = [
    "taglio tassi", "rate cut", "stimulus", "stimolo", "ripresa", "recovery",
    "accordo", "deal", "crescita", "growth", "surplus", "profitti", "utili",
    "pace", "ceasefire", "accordo commerciale", "trade deal",
    "better than expected", "sopra attese", "record high", "rally",
    "buyback", "dividend", "upgrade",
]
_BEARISH_KEYWORDS = [
    "rialzo tassi", "rate hike", "inflation", "inflazione alta", "recessione", "recession",
    "guerra", "war", "sanzioni", "sanctions", "default", "crisi", "crisis",
    "tagli produzione", "supply cut", "disoccupazione", "unemployment",
    "worse than expected", "sotto attese", "sell-off", "crollo", "crash",
    "debt ceiling", "shutdown", "downgrade", "bankruptcy",
]


def _parse_date(entry) -> Optional[datetime]:
    """Tenta di parsare la data di pubblicazione da una entry feedparser."""
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw).astimezone(timezone.utc)
            except Exception:
                pass

    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                ts = time.mktime(parsed)
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception:
                pass

    return None


def _classify_impact(title: str, summary: str) -> str:
    """Classifica l'impatto della notizia: alta / media / bassa."""
    text = (title + " " + summary).lower()
    hits = sum(1 for kw in HIGH_IMPACT_KEYWORDS if kw in text)
    if hits >= 2:
        return "alta"
    elif hits == 1:
        return "media"
    return "bassa"


def _classify_direction(title: str, summary: str) -> str:
    """Classifica la direzione della notizia: Bullish / Bearish / Neutrale."""
    text = (title + " " + summary).lower()
    bullish = sum(1 for kw in _BULLISH_KEYWORDS if kw in text)
    bearish = sum(1 for kw in _BEARISH_KEYWORDS if kw in text)
    if bullish > bearish:
        return "Bullish"
    elif bearish > bullish:
        return "Bearish"
    return "Neutrale"


def _extract_assets(title: str, summary: str) -> list:
    """Identifica gli asset o categorie menzionati nella notizia."""
    text = (title + " " + summary).lower()
    matched = []

    # Prima cerca ticker/nomi specifici
    for ticker, keywords in _ASSET_KEYWORDS.items():
        if any(len(kw) > 2 and kw in text for kw in keywords):
            matched.append(ticker)

    # Poi aggiungi categorie generiche non ancora coperte
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if cat not in matched and any(kw in text for kw in keywords):
            matched.append(cat)

    return matched[:8]


def fetch_feed(feed: dict, hours_back: int = 48) -> list:
    """
    Scarica e filtra un singolo feed RSS.

    Args:
        feed:       dict con keys: name, url, priority
        hours_back: quante ore indietro considerare

    Returns:
        Lista di dict notizia con: title, source, published,
        summary, impact, direction, assets, priority
    """
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)

    try:
        # Fetch con timeout esplicito per evitare hang infiniti
        try:
            resp = requests.get(
                feed["url"],
                timeout=10,
                headers={"User-Agent": "MacroEdge/1.0"},
            )
            parsed = feedparser.parse(resp.text)
        except requests.exceptions.RequestException:
            parsed = feedparser.parse(feed["url"])  # fallback senza requests

        if parsed.bozo and not parsed.entries:
            logger.warning(f"  Feed non raggiungibile o mal-formattato: {feed['name']}")
            return []

        items = []
        for entry in parsed.entries:
            pub_date = _parse_date(entry)

            # Se la data non è disponibile, include comunque la notizia
            if pub_date is not None and pub_date < cutoff:
                continue

            title   = getattr(entry, "title",   "").strip()
            summary_raw = getattr(entry, "summary", title).strip()

            # Rimuovi tag HTML e normalizza spazi
            summary = re.sub(r"<[^>]+>", " ", summary_raw)
            summary = re.sub(r"\s+", " ", summary).strip()[:500]

            if not title:
                continue

            items.append({
                "title":     title,
                "source":    feed["name"],
                "published": pub_date.strftime("%Y-%m-%d %H:%M") if pub_date else "N/A",
                "summary":   summary,
                "impact":    _classify_impact(title, summary),
                "direction": _classify_direction(title, summary),
                "assets":    _extract_assets(title, summary),
                "priority":  feed.get("priority", 3),
            })

        logger.debug(f"  {feed['name']}: {len(items)} notizie (ultime {hours_back}h)")
        return items

    except Exception as e:
        logger.error(f"  Errore feed {feed['name']}: {e}")
        return []


def fetch_all_news(feeds: list, hours_back: int = 48) -> list:
    """
    Scarica tutti i feed RSS e restituisce le notizie ordinate per rilevanza.

    Args:
        feeds:      lista di dict {name, url, priority}
        hours_back: finestra temporale in ore

    Returns:
        Lista di notizie deduplicata e ordinata (alta priorità + alto impatto prima).
    """
    all_news = []
    ok_feeds = 0

    for feed in feeds:
        items = fetch_feed(feed, hours_back=hours_back)
        all_news.extend(items)
        if items:
            ok_feeds += 1

    # Deduplication approssimativa per titolo (primi 60 caratteri)
    seen = set()
    deduped = []
    for item in all_news:
        key = item["title"][:60].lower().strip()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    # Ordina: prima priorità feed, poi impatto
    impact_rank = {"alta": 0, "media": 1, "bassa": 2}
    deduped.sort(key=lambda x: (x["priority"], impact_rank.get(x["impact"], 2)))

    logger.info(f"News totali: {len(deduped)} da {ok_feeds}/{len(feeds)} feed")
    return deduped


def format_news_for_ai(news_list: list, max_items: int = 25) -> str:
    """
    Formatta le notizie in testo per il prompt AI.
    Prioritizza notizie ad alto impatto.

    Args:
        news_list: lista di dict notizia
        max_items: numero massimo di notizie da includere

    Returns:
        Stringa formattata con le notizie più rilevanti.
    """
    high   = [n for n in news_list if n["impact"] == "alta"]
    medium = [n for n in news_list if n["impact"] == "media"]
    low    = [n for n in news_list if n["impact"] == "bassa"]

    selected = (high + medium + low)[:max_items]

    if not selected:
        return "(Nessuna notizia trovata nel periodo)"

    lines = []
    for i, n in enumerate(selected, 1):
        assets_str = ", ".join(n["assets"][:4]) if n["assets"] else "mercati generali"
        dir_icon   = "📈" if n["direction"] == "Bullish" else "📉" if n["direction"] == "Bearish" else "➡️"
        lines.append(
            f"{i}. [{n['impact'].upper()}] {dir_icon} {n['title']}\n"
            f"   Fonte: {n['source']} | {n['published']}\n"
            f"   Asset: {assets_str}\n"
            f"   {n['summary'][:200]}"
        )

    return "\n\n".join(lines)
