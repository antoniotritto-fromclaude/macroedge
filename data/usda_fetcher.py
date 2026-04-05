# macroedge/data/usda_fetcher.py
# ================================================================
# Scarica i dati di supply & demand agricoli dal USDA FAS PSD Online.
# API pubblica, nessuna chiave richiesta.
# Documentazione: https://apps.fas.usda.gov/psdonline/app/index.html
#
# Dati forniti (aggiornati mensilmente con il report WASDE):
#   - Produzione mondiale (1000 MT)
#   - Ending stocks mondiali (1000 MT)
#   - Stock-to-Use ratio (calcolato)
#   - Variazione YoY su produzione e scorte
#
# Stock-to-Use Ratio = Ending Stocks / Total Consumption
#   < 10%  → Critico   (prezzi storicamente alti)
#   10-15% → Stretto   (bias rialzista)
#   15-25% → Neutro
#   > 25%  → Abbondante (bias ribassista)
#
# Funzioni pubbliche:
#   fetch_usda_data()        → dict
#   format_usda_context(data) → str
# ================================================================

import logging
import requests
from datetime import datetime
from typing import Optional

logger = logging.getLogger("macroedge.usda")

USDA_FAS_API = "https://apps.fas.usda.gov/psdonline/api/psd/data"

# Commodity codes USDA FAS PSD
COMMODITIES = {
    "corn":     {"code": "0440000", "name": "Corn (Mais)",     "etf": "CORN", "unit": "1000 MT"},
    "wheat":    {"code": "0410000", "name": "Wheat (Grano)",   "etf": "WEAT", "unit": "1000 MT"},
    "soybeans": {"code": "2222000", "name": "Soybeans (Soia)", "etf": "SOYB", "unit": "1000 MT"},
    "rice":     {"code": "0422110", "name": "Rice (Riso)",     "etf": "ZR=F", "unit": "1000 MT"},
    "sugar":    {"code": "0615100", "name": "Sugar (Zucchero)","etf": "SGG",  "unit": "1000 MT"},
    "coffee":   {"code": "0711300", "name": "Coffee (Caffè)",  "etf": "JO",   "unit": "1000 60kg-bags"},
    "cocoa":    {"code": "0720100", "name": "Cocoa (Cacao)",   "etf": "NIB",  "unit": "1000 MT"},
}

# Attribute IDs USDA PSD
ATTR_PRODUCTION      = 28
ATTR_BEGINNING_STOCKS = 176
ATTR_ENDING_STOCKS   = 20
ATTR_DOM_CONSUMPTION = 125   # Domestic Consumption (feed + food + industrial)
ATTR_EXPORTS         = 88
ATTR_TOTAL_SUPPLY    = 85

# Soglie Stock-to-Use ratio per segnali di mercato
STU_CRITICAL  = 10.0   # < 10%  → prezzi molto elevati storicamente
STU_TIGHT     = 15.0   # 10-15% → mercato stretto, bias rialzista
STU_NEUTRAL   = 25.0   # 15-25% → equilibrio
# > 25% → abbondante, bias ribassista

# Paese: WD = World (globale), US = United States
COUNTRY_WORLD = "WD"


def _get_market_years() -> tuple[int, int]:
    """Restituisce l'anno di marketing corrente e quello precedente."""
    now = datetime.now()
    # La maggior parte dei marketing year inizia da set/ott dell'anno precedente
    # Usiamo anno solare corrente e precedente come approssimazione
    current_year = now.year
    return current_year, current_year - 1


def _fetch_commodity_data(commodity_code: str, country: str = COUNTRY_WORLD,
                           market_year: int = None) -> list:
    """Scarica tutti gli attributi per una commodity/paese/anno."""
    if market_year is None:
        market_year, _ = _get_market_years()

    params = {
        "commodityCode": commodity_code,
        "countryCode":   country,
        "marketYear":    market_year,
    }
    try:
        r = requests.get(USDA_FAS_API, params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"  USDA HTTP {e.response.status_code} per {commodity_code}/{country}/{market_year}")
        return []
    except Exception as e:
        logger.error(f"  USDA errore per {commodity_code}: {e}")
        return []


def _extract_value(data: list, attribute_id: int) -> Optional[float]:
    """Estrae il valore di un attributo specifico dalla risposta USDA."""
    for row in data:
        if row.get("attributeId") == attribute_id:
            val = row.get("value")
            if val is not None and str(val).strip() not in ("", "null", "None"):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None
    return None


def _compute_stu(ending_stocks: Optional[float],
                 consumption: Optional[float]) -> Optional[float]:
    """Stock-to-Use ratio in percentuale."""
    if ending_stocks is None or consumption is None or consumption == 0:
        return None
    return round(ending_stocks / consumption * 100, 1)


def _stu_signal(stu: Optional[float]) -> str:
    """Interpreta il Stock-to-Use ratio come segnale di mercato."""
    if stu is None:
        return "N/A"
    if stu < STU_CRITICAL:
        return f"🔴 CRITICO ({stu:.1f}%) — prezzi storicamente elevati"
    elif stu < STU_TIGHT:
        return f"🟠 STRETTO ({stu:.1f}%) — bias rialzista"
    elif stu < STU_NEUTRAL:
        return f"🟡 NEUTRO ({stu:.1f}%) — mercato equilibrato"
    else:
        return f"🟢 ABBONDANTE ({stu:.1f}%) — bias ribassista"


def fetch_usda_data() -> dict:
    """
    Scarica i dati USDA FAS PSD per le principali commodity agricole.

    Returns:
        dict key=commodity_key → {name, etf, unit,
                                   production, ending_stocks, consumption, exports,
                                   stu, stu_signal, stu_prev,
                                   prod_yoy_pct, stocks_yoy_pct,
                                   market_year}
        Restituisce {} se l'API non è raggiungibile.
    """
    current_year, prev_year = _get_market_years()
    results = {}

    for key, info in COMMODITIES.items():
        code  = info["code"]
        name  = info["name"]

        try:
            # Anno corrente
            data_curr = _fetch_commodity_data(code, COUNTRY_WORLD, current_year)
            # Anno precedente (per confronto YoY)
            data_prev = _fetch_commodity_data(code, COUNTRY_WORLD, prev_year)

            if not data_curr:
                logger.warning(f"  USDA {name}: nessun dato per {current_year}")
                continue

            prod_curr   = _extract_value(data_curr, ATTR_PRODUCTION)
            stocks_curr = _extract_value(data_curr, ATTR_ENDING_STOCKS)
            cons_curr   = _extract_value(data_curr, ATTR_DOM_CONSUMPTION)
            exports_curr = _extract_value(data_curr, ATTR_EXPORTS)

            prod_prev   = _extract_value(data_prev, ATTR_PRODUCTION)   if data_prev else None
            stocks_prev = _extract_value(data_prev, ATTR_ENDING_STOCKS) if data_prev else None
            cons_prev   = _extract_value(data_prev, ATTR_DOM_CONSUMPTION) if data_prev else None

            stu_curr = _compute_stu(stocks_curr, cons_curr)
            stu_prev = _compute_stu(stocks_prev, cons_prev)

            # Variazioni YoY
            prod_yoy = None
            if prod_curr is not None and prod_prev and prod_prev > 0:
                prod_yoy = round((prod_curr - prod_prev) / prod_prev * 100, 1)

            stocks_yoy = None
            if stocks_curr is not None and stocks_prev and stocks_prev > 0:
                stocks_yoy = round((stocks_curr - stocks_prev) / stocks_prev * 100, 1)

            results[key] = {
                "name":         name,
                "etf":          info["etf"],
                "unit":         info["unit"],
                "market_year":  current_year,
                "production":   prod_curr,
                "ending_stocks":stocks_curr,
                "consumption":  cons_curr,
                "exports":      exports_curr,
                "stu":          stu_curr,
                "stu_prev":     stu_prev,
                "stu_signal":   _stu_signal(stu_curr),
                "prod_yoy_pct": prod_yoy,
                "stocks_yoy_pct": stocks_yoy,
            }

            logger.info(
                f"  USDA {name}: STU={stu_curr}% "
                f"(prev {stu_prev}%) | prod YoY: {prod_yoy:+.1f}%" if prod_yoy is not None
                else f"  USDA {name}: STU={stu_curr}%"
            )

        except Exception as e:
            logger.error(f"  USDA {name} errore imprevisto: {e}")

    if results:
        logger.info(f"USDA completato: {len(results)}/{len(COMMODITIES)} commodity")
    else:
        logger.warning("USDA: nessun dato disponibile (API non raggiungibile?)")

    return results


def format_usda_context(usda_data: dict) -> str:
    """
    Genera il blocco di testo USDA da inserire nel prompt AI.
    Compatto ma con i dati chiave: STU ratio, YoY changes, segnali.
    """
    if not usda_data:
        return (
            "=== USDA — Supply & Demand Agricoltura ===\n"
            "Dati non disponibili (API USDA temporaneamente non raggiungibile)."
        )

    lines = ["=== USDA WASDE — Supply & Demand Mondiale (ultimo report) ==="]

    # Raggruppa per urgenza del segnale
    critical = [(k, v) for k, v in usda_data.items() if v.get("stu") and v["stu"] < STU_TIGHT]
    neutral  = [(k, v) for k, v in usda_data.items() if v.get("stu") and v["stu"] >= STU_TIGHT]

    def _format_commodity(key: str, d: dict) -> str:
        prod      = d.get("production")
        stocks    = d.get("ending_stocks")
        prod_yoy  = d.get("prod_yoy_pct")
        stk_yoy   = d.get("stocks_yoy_pct")
        unit      = d.get("unit", "1000 MT")

        prod_str  = f"{prod:,.0f} {unit}" if prod else "N/A"
        stk_str   = f"{stocks:,.0f} {unit}" if stocks else "N/A"
        yoy_prod  = f" (YoY: {prod_yoy:+.1f}%)" if prod_yoy is not None else ""
        yoy_stk   = f" (YoY: {stk_yoy:+.1f}%)" if stk_yoy is not None else ""

        return (
            f"• {d['name']} [ETF: {d['etf']}]\n"
            f"  {d['stu_signal']}\n"
            f"  Produzione: {prod_str}{yoy_prod}\n"
            f"  Ending Stocks: {stk_str}{yoy_stk}"
        )

    if critical:
        lines.append("\n⚠️ Commodity con mercato STRETTO (opportunità rialziste):")
        for k, d in sorted(critical, key=lambda x: x[1].get("stu") or 99):
            lines.append(_format_commodity(k, d))

    if neutral:
        lines.append("\n— Altre commodity:")
        for k, d in sorted(neutral, key=lambda x: x[1].get("stu") or 0):
            lines.append(_format_commodity(k, d))

    # Sintesi per l'AI
    bullish_ag = [d["name"] for k, d in usda_data.items()
                  if d.get("stu") and d["stu"] < STU_TIGHT]
    bearish_ag = [d["name"] for k, d in usda_data.items()
                  if d.get("stu") and d["stu"] > STU_NEUTRAL]
    if bullish_ag:
        lines.append(f"\n📈 Bias rialzista USDA: {', '.join(bullish_ag)}")
    if bearish_ag:
        lines.append(f"📉 Bias ribassista USDA: {', '.join(bearish_ag)}")

    return "\n".join(lines)
