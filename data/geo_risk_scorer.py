# macroedge/data/geo_risk_scorer.py
# ================================================================
# Scoring del rischio geopolitico basato sulle notizie raccolte.
# Non richiede API esterne: usa le news già parsate da news_reader.py.
#
# Produce:
#   - uno score globale 0-10
#   - gli eventi ad alto rischio identificati
#   - l'impatto stimato per categoria asset
#
# Funzioni pubbliche:
#   score_geopolitical_risk(news_list) → dict
#   format_geo_context(geo_data)       → str
# ================================================================

import logging
import re
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("macroedge.geo_risk")


# ================================================================
# DIZIONARIO EVENTI GEOPOLITICI — keyword → (peso, categoria, impatto)
# peso 1-5 per impatto sul rischio globale
# ================================================================
GEO_RISK_EVENTS = [
    # Conflitti armati — massima priorità
    ("guerra",        5, "conflict",   "risk-off"),
    ("war",           5, "conflict",   "risk-off"),
    ("attack",        4, "conflict",   "risk-off"),
    ("attacco",       4, "conflict",   "risk-off"),
    ("missile",       4, "conflict",   "risk-off"),
    ("airstrike",     4, "conflict",   "risk-off"),
    ("invasion",      5, "conflict",   "risk-off"),
    ("invasione",     5, "conflict",   "risk-off"),
    ("nuclear",       5, "conflict",   "risk-off"),
    ("nucleare",      5, "conflict",   "risk-off"),
    ("ceasefire",     3, "conflict",   "risk-on"),
    ("tregua",        3, "conflict",   "risk-on"),
    ("peace",         3, "conflict",   "risk-on"),
    ("pace",          3, "conflict",   "risk-on"),
    # Sanzioni e commercio
    ("sanction",      4, "sanctions",  "risk-off"),
    ("sanzione",      4, "sanctions",  "risk-off"),
    ("embargo",       4, "sanctions",  "risk-off"),
    ("tariff",        3, "trade",      "risk-off"),
    ("dazio",         3, "trade",      "risk-off"),
    ("trade war",     4, "trade",      "risk-off"),
    ("guerra commerciale", 4, "trade", "risk-off"),
    ("export ban",    3, "trade",      "risk-off"),
    # Istabilità politica
    ("coup",          5, "political",  "risk-off"),
    ("golpe",         5, "political",  "risk-off"),
    ("protest",       2, "political",  "risk-off"),
    ("protesta",      2, "political",  "risk-off"),
    ("election",      2, "political",  "mixed"),
    ("elezioni",      2, "political",  "mixed"),
    ("impeachment",   3, "political",  "risk-off"),
    ("default",       5, "financial",  "risk-off"),
    ("sovereign debt",4, "financial",  "risk-off"),
    ("debt crisis",   4, "financial",  "risk-off"),
    # Crisi energetiche
    ("opec",          3, "energy",     "mixed"),
    ("oil supply",    3, "energy",     "mixed"),
    ("gas supply",    3, "energy",     "mixed"),
    ("pipeline",      2, "energy",     "mixed"),
    ("strait of hormuz", 5, "energy",  "risk-off"),
    # Hotspot geografici
    ("ukraine",       4, "conflict",   "risk-off"),
    ("russia",        3, "conflict",   "risk-off"),
    ("gaza",          4, "conflict",   "risk-off"),
    ("iran",          4, "conflict",   "risk-off"),
    ("taiwan",        5, "conflict",   "risk-off"),
    ("north korea",   4, "conflict",   "risk-off"),
    ("corea del nord",4, "conflict",   "risk-off"),
    ("china sea",     3, "conflict",   "risk-off"),
    ("sudan",         2, "conflict",   "risk-off"),
    ("middle east",   3, "conflict",   "risk-off"),
    ("medio oriente", 3, "conflict",   "risk-off"),
    # Asset-specific
    ("opec cut",      4, "energy",     "bullish-oil"),
    ("opec increase", 4, "energy",     "bearish-oil"),
    ("gold",          1, "metals",     "safe-haven"),
    ("safe haven",    3, "metals",     "safe-haven"),
    ("risk-off",      3, "general",    "risk-off"),
    ("risk off",      3, "general",    "risk-off"),
]

# Pesi per headline vs body (le headline contano di più)
WEIGHT_HEADLINE = 2.0
WEIGHT_BODY     = 0.5

# Soglie score per classificazione
SCORE_HIGH_RISK   = 6.0
SCORE_MEDIUM_RISK = 3.0


def score_geopolitical_risk(news_list: list) -> dict:
    """
    Analizza la lista di news e calcola lo score di rischio geopolitico.

    Args:
        news_list: lista di dict con keys 'title', 'summary', 'published'

    Returns:
        dict con:
        - score: 0-10 (rischio geopolitico globale)
        - level: "Alto"|"Medio"|"Basso"
        - events: lista di eventi rilevati (top 5)
        - asset_impact: impatto stimato per categoria asset
        - risk_bias: "risk-off"|"risk-on"|"misto"
    """
    total_score      = 0.0
    event_hits       = {}   # event_key → {count, score, category, impact, titles}
    risk_off_score   = 0.0
    risk_on_score    = 0.0

    for news in news_list:
        title   = (news.get("title", "") or "").lower()
        summary = (news.get("summary", "") or "").lower()

        for keyword, peso, category, impact in GEO_RISK_EVENTS:
            kw_lower = keyword.lower()

            in_title   = kw_lower in title
            in_summary = kw_lower in summary

            if not (in_title or in_summary):
                continue

            hit_score = 0.0
            if in_title:
                hit_score += peso * WEIGHT_HEADLINE
            if in_summary:
                hit_score += peso * WEIGHT_BODY

            total_score += hit_score

            # Traccia per category
            key = f"{keyword}|{category}"
            if key not in event_hits:
                event_hits[key] = {
                    "keyword":  keyword,
                    "category": category,
                    "impact":   impact,
                    "score":    0.0,
                    "count":    0,
                    "titles":   [],
                }
            event_hits[key]["score"] += hit_score
            event_hits[key]["count"] += 1
            if in_title and len(event_hits[key]["titles"]) < 3:
                event_hits[key]["titles"].append(news.get("title", "")[:120])

            # Accumula per bias
            if impact == "risk-off":
                risk_off_score += hit_score
            elif impact == "risk-on":
                risk_on_score += hit_score

    # Normalizza score 0-10 con soft cap logaritmico
    import math
    normalized = min(10.0, round(math.log1p(total_score) * 1.5, 1)) if total_score > 0 else 0.0

    # Livello
    if normalized >= SCORE_HIGH_RISK:
        level = "Alto"
    elif normalized >= SCORE_MEDIUM_RISK:
        level = "Medio"
    else:
        level = "Basso"

    # Bias
    if risk_off_score > risk_on_score * 1.5:
        risk_bias = "risk-off"
    elif risk_on_score > risk_off_score * 1.5:
        risk_bias = "risk-on"
    else:
        risk_bias = "misto"

    # Top eventi per score
    top_events = sorted(event_hits.values(), key=lambda x: x["score"], reverse=True)[:7]

    # Impatto per asset class
    asset_impact = _compute_asset_impact(top_events, normalized)

    logger.info(f"Geo-risk score: {normalized}/10 ({level}) | bias: {risk_bias}")

    return {
        "score":        normalized,
        "level":        level,
        "risk_bias":    risk_bias,
        "events":       top_events[:5],
        "asset_impact": asset_impact,
        "news_count":   len(news_list),
    }


def _compute_asset_impact(top_events: list, score: float) -> dict:
    """Stima l'impatto sul portfolio per categoria asset."""
    categories = {e["category"] for e in top_events}
    impact = {}

    if score >= SCORE_HIGH_RISK:
        impact["metalli_preziosi"]   = "bullish (safe-haven demand)"
        impact["dollaro_usa"]        = "bullish (safe-haven)"
        impact["equity"]             = "bearish (risk-off)"
        impact["emerging_markets"]   = "bearish (flight to quality)"
        impact["obbligazioni_usa"]   = "bullish (safe-haven bonds)"

    elif score >= SCORE_MEDIUM_RISK:
        impact["metalli_preziosi"]   = "moderatamente bullish"
        impact["equity"]             = "neutro-bearish"
        impact["emerging_markets"]   = "moderatamente bearish"

    if "energy" in categories:
        impact["petrolio"] = "alta volatilità — monitorare supply disruption"
    if "trade" in categories:
        impact["emerging_markets"] = "bearish (reshoring + dazi)"
        impact["semiconductori"]   = "attenzione a restrizioni export"
    if "conflict" in categories and score >= 5:
        impact["petrolio"]        = "bullish (rischio supply)"
        impact["difesa_defense"]  = "bullish (aumento spesa militare)"

    return impact


def format_geo_context(geo_data: dict) -> str:
    """
    Genera il blocco di testo geopolitico da inserire nel prompt AI.
    """
    if not geo_data:
        return ""

    score = geo_data.get("score", 0)
    level = geo_data.get("level", "N/A")
    bias  = geo_data.get("risk_bias", "misto")
    events = geo_data.get("events", [])
    impact = geo_data.get("asset_impact", {})

    level_emoji = {"Alto": "🔴", "Medio": "🟡", "Basso": "🟢"}.get(level, "⚪")
    bias_emoji  = {"risk-off": "🔴", "risk-on": "🟢", "misto": "🟡"}.get(bias, "⚪")

    lines = [f"=== RISCHIO GEOPOLITICO ==="]
    lines.append(f"{level_emoji} Score: {score}/10 ({level}) | {bias_emoji} Bias: {bias}")

    if events:
        lines.append("\nEventi principali rilevati:")
        for ev in events[:5]:
            lines.append(f"  • [{ev['category'].upper()}] '{ev['keyword']}' — {ev['count']} notizie | impatto: {ev['impact']}")
            if ev.get("titles"):
                lines.append(f"    Ex: {ev['titles'][0][:100]}")

    if impact:
        lines.append("\nImpatto stimato per asset class:")
        for asset_class, imp in impact.items():
            lines.append(f"  • {asset_class}: {imp}")

    return "\n".join(lines)
