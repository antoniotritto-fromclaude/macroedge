# macroedge/data/eia_fetcher.py
# ================================================================
# Scarica dati settimanali dall'EIA (Energy Information Administration).
# API gratuita → https://www.eia.gov/opendata/register.php
#
# Se EIA_API_KEY non è configurato, restituisce un dict vuoto
# senza errori (la mancanza di questi dati è gestita con graceful fallback).
#
# Serie chiave:
#   WCRSTUS1  — US Crude Oil Ending Stocks (Thousand Barrels)
#   WCRFPUS2  — US Crude Oil Production (Thousand Barrels/Day)
#   WGTSTUS1  — US Gasoline Total Stocks (Thousand Barrels)
#   WDISTUS1  — US Distillate Fuel Stocks (Thousand Barrels)
#   WPULEUS2  — US Refinery Utilization (%)
#
# Funzioni pubbliche:
#   fetch_eia_data(api_key)  → dict
#   format_eia_context(data) → str
# ================================================================

import logging
import requests

logger = logging.getLogger("macroedge.eia")

EIA_API_V2 = "https://api.eia.gov/v2/petroleum/{path}/data/"

# Serie da scaricare: (key_risultato, path_endpoint, series_id, label, unità)
EIA_SERIES = [
    ("crude_stocks",       "stoc/wstk", "WCRSTUS1", "Crude Oil Stocks",        "Mbbl"),
    ("crude_production",   "sum/sndw",  "WCRFPUS2", "Crude Production",        "Mbbl/d"),
    ("gasoline_stocks",    "stoc/wstk", "WGTSTUS1", "Gasoline Stocks",         "Mbbl"),
    ("distillate_stocks",  "stoc/wstk", "WDISTUS1", "Distillate Stocks",       "Mbbl"),
    ("refinery_util",      "sum/alls",  "WPULEUS2", "Refinery Utilization",    "%"),
]

# Soglie di mercato per crude oil stocks
CRUDE_STOCKS_BULLISH_DRAW    = -3_000   # −3M bbl draw → bullish per petrolio
CRUDE_STOCKS_BEARISH_BUILD   = +3_000   # +3M bbl build → bearish per petrolio


def _fetch_series(api_key: str, path: str, series_id: str, n_weeks: int = 5) -> list:
    """Scarica le ultime n_weeks settimane per una singola serie EIA."""
    url = EIA_API_V2.format(path=path)
    params = {
        "api_key":              api_key,
        "frequency":            "weekly",
        "data[0]":              "value",
        f"facets[series][]":    series_id,
        "sort[0][column]":      "period",
        "sort[0][direction]":   "desc",
        "length":               n_weeks,
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("response", {}).get("data", [])


def fetch_eia_data(api_key: str) -> dict:
    """
    Scarica le principali serie EIA settimanali e calcola le variazioni.

    Returns:
        dict con le serie disponibili, o {} se EIA_API_KEY non configurato.
        Ogni voce: {"label", "current", "previous", "change", "period", "unit", "signal"}
    """
    if not api_key:
        logger.info("EIA_API_KEY non configurato — dati EIA non disponibili")
        return {}

    results = {}

    for key, path, series_id, label, unit in EIA_SERIES:
        try:
            data = _fetch_series(api_key, path, series_id, n_weeks=5)
            if len(data) < 2:
                logger.warning(f"  EIA {series_id}: dati insufficienti ({len(data)} record)")
                continue

            current  = float(data[0]["value"])
            previous = float(data[1]["value"])
            change   = round(current - previous, 1)
            change_pct = round((change / previous * 100), 2) if previous else 0

            # Segnale di mercato per crude stocks
            signal = "neutro"
            if key == "crude_stocks":
                if change <= CRUDE_STOCKS_BULLISH_DRAW:
                    signal = "bullish (draw significativo)"
                elif change >= CRUDE_STOCKS_BEARISH_BUILD:
                    signal = "bearish (build significativo)"
            elif key == "crude_production":
                if change_pct >= 1.0:
                    signal = "bearish (produzione in aumento)"
                elif change_pct <= -1.0:
                    signal = "bullish (produzione in calo)"
            elif key == "refinery_util":
                if current >= 93:
                    signal = "domanda elevata"
                elif current <= 85:
                    signal = "domanda debole"

            results[key] = {
                "label":      label,
                "current":    round(current, 1),
                "previous":   round(previous, 1),
                "change":     change,
                "change_pct": change_pct,
                "period":     data[0].get("period", ""),
                "unit":       unit,
                "signal":     signal,
            }
            logger.info(f"  EIA {series_id}: {current} {unit} ({change:+.1f}) — {signal}")

        except requests.exceptions.HTTPError as e:
            logger.error(f"  EIA {series_id} HTTP error: {e}")
        except Exception as e:
            logger.error(f"  EIA {series_id} errore: {e}")

    if results:
        logger.info(f"EIA completato: {len(results)}/{len(EIA_SERIES)} serie scaricate")
    else:
        logger.warning("EIA: nessun dato disponibile")

    return results




def format_eia_context(eia_data: dict) -> str:
    """
    Genera il blocco di testo EIA da inserire nel prompt AI.
    """
    if not eia_data:
        return "=== EIA — Dati Settimanali Petrolio ===\nEIA_API_KEY non configurato. Usa news e prezzi futures per il contesto energia."

    lines = ["=== EIA — Dati Settimanali Petrolio (USA) ==="]

    # Crude oil stocks: il dato più importante
    if "crude_stocks" in eia_data:
        cs = eia_data["crude_stocks"]
        chg_sign = "+" if cs["change"] >= 0 else ""
        signal_emoji = {"bullish (draw significativo)": "📈", "bearish (build significativo)": "📉"}.get(cs["signal"], "➡️")
        lines.append(
            f"\n🛢️ {cs['label']} ({cs['period']}):\n"
            f"   Livello: {cs['current']:,.1f} {cs['unit']} "
            f"(prec: {cs['previous']:,.1f} | Δ: {chg_sign}{cs['change']:,.1f})\n"
            f"   {signal_emoji} Segnale: {cs['signal']}"
        )

    # Produzione
    if "crude_production" in eia_data:
        cp = eia_data["crude_production"]
        chg_sign = "+" if cp["change"] >= 0 else ""
        lines.append(
            f"\n⛽ {cp['label']} ({cp['period']}):\n"
            f"   {cp['current']:,.1f} {cp['unit']} "
            f"(Δ: {chg_sign}{cp['change']:,.1f} | {chg_sign}{cp['change_pct']:.1f}%)\n"
            f"   Segnale: {cp['signal']}"
        )

    # Raffinerie
    if "refinery_util" in eia_data:
        ru = eia_data["refinery_util"]
        lines.append(
            f"\n🏭 {ru['label']}: {ru['current']}% — {ru['signal']}"
        )

    # Scorte prodotti raffinati
    for key in ("gasoline_stocks", "distillate_stocks"):
        if key in eia_data:
            d = eia_data[key]
            chg_sign = "+" if d["change"] >= 0 else ""
            lines.append(
                f"\n📦 {d['label']}: {d['current']:,.1f} {d['unit']} "
                f"(Δ {chg_sign}{d['change']:,.1f})"
            )

    # Sintesi per il modello AI
    signals = [v["signal"] for v in eia_data.values() if v.get("signal") and v["signal"] != "neutro"]
    if signals:
        bullish_count = sum(1 for s in signals if "bullish" in s or "domanda elevata" in s)
        bearish_count = sum(1 for s in signals if "bearish" in s or "domanda debole" in s)
        overall = "Bias EIA: BULLISH per petrolio" if bullish_count > bearish_count else \
                  "Bias EIA: BEARISH per petrolio" if bearish_count > bullish_count else \
                  "Bias EIA: NEUTRO"
        lines.append(f"\n💡 {overall}")

    return "\n".join(lines)
