# macroedge/data/fx_analyzer.py
# ================================================================
# Analisi differenziale FX: tasso di policy, carry trade bias,
# momentum tecnico per ogni coppia valutaria nell'universo.
#
# Non richiede API esterne: usa i tassi da config.POLICY_RATES
# e i dati tecnici già presenti nello snapshot di Yahoo Finance.
#
# Funzioni pubbliche:
#   compute_fx_differentials(snapshot) → list[dict]
#   format_fx_context(fx_data)         → str
# ================================================================

import logging
from config import POLICY_RATES, FX_PAIR_CURRENCIES

logger = logging.getLogger("macroedge.fx_analyzer")


def compute_fx_differentials(snapshot: list) -> list:
    """
    Per ogni coppia FX nell'universo calcola:
    - differenziale di tasso tra base e quote (proxy carry trade)
    - bias carry trade (direzione teorica della coppia)
    - conferma/divergenza con il trend attuale
    - score opportunità carry (0-10)

    Args:
        snapshot: lista di dict dall'output di get_full_market_snapshot()

    Returns:
        Lista di dict con analisi FX, ordinata per |differenziale| decrescente.
    """
    snapshot_map = {a["ticker"]: a for a in snapshot}
    results = []

    for ticker, (base, quote) in FX_PAIR_CURRENCIES.items():
        asset = snapshot_map.get(ticker)
        if asset is None:
            continue

        base_info  = POLICY_RATES.get(base,  {"rate": 0.0, "bank": "N/A", "bias": "neutral"})
        quote_info = POLICY_RATES.get(quote, {"rate": 0.0, "bank": "N/A", "bias": "neutral"})

        base_rate  = base_info["rate"]
        quote_rate = quote_info["rate"]
        differential = round(base_rate - quote_rate, 2)

        # Carry bias: long la valuta col tasso più alto
        # Per EUR/USD: se EUR rate > USD rate → carry Long EUR/USD
        # Per USD/JPY: base=USD, se USD rate > JPY rate → carry Long USD/JPY
        if differential > 0.25:
            carry_bias      = f"Long {base}/{quote} (carry +{differential:.2f}%)"
            carry_direction = "Long"
        elif differential < -0.25:
            carry_bias      = f"Short {base}/{quote} (carry {differential:.2f}%)"
            carry_direction = "Short"
        else:
            carry_bias      = f"Neutro (spread {differential:+.2f}% insufficiente)"
            carry_direction = "Neutro"

        # Verifica se il trend tecnico conferma o diverge dal carry
        trend = asset.get("trend", "")
        chg   = asset.get("change_1d_pct", 0) or 0

        carry_confirmed = False
        carry_divergent = False
        if carry_direction == "Long" and ("Uptrend" in trend or "sopra MA" in trend.lower()):
            carry_confirmed = True
        elif carry_direction == "Short" and ("Downtrend" in trend or "sotto MA" in trend.lower()):
            carry_confirmed = True
        elif carry_direction != "Neutro":
            # Divergenza: carry suggerisce Long ma trend è ribassista (o viceversa)
            if carry_direction == "Long" and "Downtrend" in trend:
                carry_divergent = True
            elif carry_direction == "Short" and "Uptrend" in trend:
                carry_divergent = True

        # Score opportunità: alto se carry forte + trend confermato
        abs_diff = abs(differential)
        score = 0
        if abs_diff >= 4.0:
            score += 5
        elif abs_diff >= 2.0:
            score += 3
        elif abs_diff >= 0.5:
            score += 1

        rsi_val = asset.get("rsi")
        if carry_confirmed:
            score += 3
        if rsi_val is not None:
            if (carry_direction == "Long" and 40 <= rsi_val <= 65):
                score += 2  # RSI in zona neutro-rialzista → buon entry carry Long
            elif (carry_direction == "Short" and 35 <= rsi_val <= 60):
                score += 2
        score = min(score, 10)

        results.append({
            "ticker":            ticker,
            "name":              asset.get("name", ticker),
            "price":             asset.get("price", "N/A"),
            "change_1d_pct":     chg,
            "base":              base,
            "quote":             quote,
            "base_rate":         base_rate,
            "quote_rate":        quote_rate,
            "base_bank":         base_info["bank"],
            "quote_bank":        quote_info["bank"],
            "base_bias":         base_info["bias"],
            "quote_bias":        quote_info["bias"],
            "differential":      differential,
            "carry_direction":   carry_direction,
            "carry_bias":        carry_bias,
            "carry_confirmed":   carry_confirmed,
            "carry_divergent":   carry_divergent,
            "trend":             trend,
            "rsi_signal":        asset.get("rsi_signal", "N/A"),
            "support_20d":       asset.get("support_20d"),
            "resistance_20d":    asset.get("resistance_20d"),
            "opportunity_score": score,
        })

    results.sort(key=lambda x: x["opportunity_score"], reverse=True)
    logger.info(f"FX analizzate: {len(results)} coppie | Top carry: {results[0]['name'] if results else 'N/A'}")
    return results


def format_fx_context(fx_data: list) -> str:
    """
    Genera il blocco di testo FX da inserire nel prompt AI.
    Compatto ma informativo: differenziale, carry bias, status tecnico.
    """
    if not fx_data:
        return "Dati FX non disponibili."

    lines = ["=== FX — Differenziali di Tasso e Carry Trade ==="]

    # Prima le coppie con divergenza (più interessanti)
    divergenti = [x for x in fx_data if x["carry_divergent"]]
    confermati = [x for x in fx_data if x["carry_confirmed"]]
    altri      = [x for x in fx_data if not x["carry_divergent"] and not x["carry_confirmed"]]

    if divergenti:
        lines.append("\n⚠️ DIVERGENZE CARRY (prezzi contro il carry → segnale anomalia):")
        for p in divergenti:
            lines.append(_format_pair_line(p, marker="⚡"))

    if confermati:
        lines.append("\n✅ CARRY CONFERMATI (trend + carry allineati):")
        for p in confermati[:5]:
            lines.append(_format_pair_line(p, marker="✓"))

    if altri:
        lines.append("\n— Altre coppie:")
        for p in altri[:4]:
            lines.append(_format_pair_line(p, marker="·"))

    # Riepilogo bias banche centrali
    lines.append("\n📋 Bias banche centrali:")
    seen_banks = set()
    for p in fx_data:
        for currency, bank, bias in [
            (p["base"], p["base_bank"], p["base_bias"]),
            (p["quote"], p["quote_bank"], p["quote_bias"]),
        ]:
            if bank not in seen_banks and bank != "N/A":
                emoji = {"hawkish": "🦅", "dovish": "🕊️", "neutral": "⚖️"}.get(bias, "")
                lines.append(f"  {emoji} {bank} ({currency}): {bias}")
                seen_banks.add(bank)

    return "\n".join(lines)


def _format_pair_line(p: dict, marker: str = "•") -> str:
    diff   = p["differential"]
    sign   = "+" if diff >= 0 else ""
    chg    = p.get("change_1d_pct", 0) or 0
    return (
        f"  {marker} {p['name']} ({p['ticker']}): {p['price']} ({chg:+.2f}%)\n"
        f"      Spread {p['base']}-{p['quote']}: {sign}{diff:.2f}% | {p['carry_bias']}\n"
        f"      {p['trend']} | {p['rsi_signal']}"
    )
