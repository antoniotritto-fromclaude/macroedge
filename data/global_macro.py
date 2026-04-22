# macroedge/data/global_macro.py
# ================================================================
# Global Macro Module — analisi regionale avanzata
#
# Prende lo snapshot dei prezzi già calcolato e produce:
#   1. Regional Heatmap — performance per area geografica
#   2. CB→FX→Commodity Correlation — correlazioni strutturali attive
#   3. Policy Divergence Index — divergenza tra banche centrali
#   4. Global Liquidity Proxies — proxy della liquidità globale
#
# Non esegue download aggiuntivi: usa il snapshot esistente.
#
# Funzioni pubbliche:
#   compute_regional_heatmap(snapshot)       → dict
#   compute_cb_correlations(snapshot)        → dict
#   compute_policy_divergence()              → dict
#   compute_liquidity_proxies(snapshot)      → dict
#   format_global_macro_context(snapshot)    → str
# ================================================================

import logging
from typing import Optional
from config import (
    MACRO_REGIONS,
    CB_COMMODITY_CORRELATIONS,
    POLICY_RATES,
    FX_PAIR_CURRENCIES,
)

logger = logging.getLogger("macroedge.global_macro")


# ── Helpers ────────────────────────────────────────────────────────

def _snapshot_index(snapshot: list) -> dict:
    """Crea indice ticker → row per accesso rapido."""
    return {row["ticker"]: row for row in snapshot if row.get("ticker")}


def _avg(values: list) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else None


def _trend_score(change: Optional[float], trend: Optional[str]) -> int:
    """
    Converte change_1d_pct + trend in un punteggio -3 … +3.
    Usato per costruire la heatmap visiva.
    """
    score = 0
    if change is not None:
        if change > 1.0:   score += 2
        elif change > 0:   score += 1
        elif change < -1.0: score -= 2
        elif change < 0:   score -= 1
    if trend:
        if "Uptrend" in trend:        score += 1
        elif "Downtrend" in trend:    score -= 1
        elif "Sopra MA200" in trend:  score += 1
        elif "Sotto MA200" in trend:  score -= 1
    return max(-3, min(3, score))


def _score_to_emoji(score: int) -> str:
    mapping = {3: "🟢🟢", 2: "🟢", 1: "🟡", 0: "⚪", -1: "🟠", -2: "🔴", -3: "🔴🔴"}
    return mapping.get(score, "⚪")


# ── 1. Regional Heatmap ───────────────────────────────────────────

def compute_regional_heatmap(snapshot: list) -> dict:
    """
    Calcola la performance media per regione geografica.

    Returns:
        dict region_key → {
            label, avg_change_1d, trend_score, emoji,
            best_asset, worst_asset, n_assets
        }
    """
    idx = _snapshot_index(snapshot)
    results = {}

    for region_key, region_info in MACRO_REGIONS.items():
        key_tickers = region_info["key_assets"]
        changes   = []
        scores    = []
        best      = None
        worst     = None

        for ticker in key_tickers:
            row = idx.get(ticker)
            if row is None:
                continue
            c = row.get("change_1d_pct")
            t = row.get("trend", "")
            if c is not None:
                changes.append(c)
                s = _trend_score(c, t)
                scores.append(s)
                name = row.get("name", ticker)
                if best is None or c > best["change"]:
                    best = {"name": name, "change": c}
                if worst is None or c < worst["change"]:
                    worst = {"name": name, "change": c}

        avg_chg = _avg(changes)
        avg_score = round(_avg(scores) or 0)
        avg_score = max(-3, min(3, avg_score))

        results[region_key] = {
            "label":        region_info["label"],
            "avg_change_1d": avg_chg,
            "trend_score":   avg_score,
            "emoji":         _score_to_emoji(avg_score),
            "best_asset":    best,
            "worst_asset":   worst,
            "n_assets":      len(changes),
            "cb_focus":      region_info["cb_focus"],
        }

    return results


# ── 2. CB→FX→Commodity Correlations ──────────────────────────────

def compute_cb_correlations(snapshot: list) -> dict:
    """
    Verifica se le correlazioni strutturali CB→FX→Commodity sono attive.

    Returns:
        dict currency → {
            bank, correlation, fx_change, commodity_avg_change,
            alignment, signal
        }
    """
    idx = _snapshot_index(snapshot)
    results = {}

    for currency, info in CB_COMMODITY_CORRELATIONS.items():
        # FX ticker principale
        fx_tickers = info["tickers_fx"]
        fx_changes = []
        for ftk in fx_tickers:
            row = idx.get(ftk)
            if row:
                c = row.get("change_1d_pct")
                if c is not None:
                    fx_changes.append(c)
        fx_chg = _avg(fx_changes)

        # Commodity tickers
        comm_changes = []
        comm_names   = []
        for ctk in info["commodities"]:
            row = idx.get(ctk)
            if row:
                c = row.get("change_1d_pct")
                if c is not None:
                    comm_changes.append(c)
                    comm_names.append(row.get("name", ctk))
        comm_chg = _avg(comm_changes)

        # Verifica alignment della correlazione
        alignment = None
        signal    = "N/A"
        if fx_chg is not None and comm_chg is not None:
            corr_type = info.get("correlation", "positiva")
            if corr_type == "positiva":
                if (fx_chg > 0) == (comm_chg > 0):
                    alignment = True
                    signal = f"{'📈' if comm_chg > 0 else '📉'} Correlazione attiva — {currency} e materie prime in accordo"
                else:
                    alignment = False
                    signal = f"⚠️ Divergenza — {currency} {'sale' if fx_chg > 0 else 'scende'} ma commodity {'salgono' if comm_chg > 0 else 'scendono'}"
            elif corr_type == "inversa":
                if (fx_chg > 0) != (comm_chg > 0):
                    alignment = True
                    signal = f"{'📈' if fx_chg > 0 else '📉'} Correlazione inversa attiva — {currency} in risk-off"
                else:
                    alignment = False
                    signal = f"⚠️ Divergenza — correlazione inversa non rispettata per {currency}"

        results[currency] = {
            "bank":              info["bank"],
            "correlation_type":  info.get("correlation", "positiva"),
            "rationale":         info["rationale"],
            "fx_change":         fx_chg,
            "commodity_avg_change": comm_chg,
            "commodity_names":   comm_names,
            "alignment":         alignment,
            "signal":            signal,
        }

    return results


# ── 3. Policy Divergence Index ─────────────────────────────────────

def compute_policy_divergence() -> dict:
    """
    Calcola la divergenza di policy tra banche centrali.

    Returns:
        dict con:
          - ranked_rates: lista di (currency, rate, bias, bank) ordinata per rate
          - most_hawkish: list[currency] con bias="hawkish"
          - most_dovish:  list[currency] con bias="dovish"
          - spread_usd_eur: differenziale USD-EUR
          - spread_usd_jpy: differenziale USD-JPY
          - divergence_summary: testo descrittivo
    """
    ranked = sorted(
        [(k, v["rate"], v["bias"], v["bank"], v.get("region", ""))
         for k, v in POLICY_RATES.items()],
        key=lambda x: x[1],
        reverse=True
    )

    most_hawkish = [k for k, r, b, bk, reg in ranked if b == "hawkish"]
    most_dovish  = [k for k, r, b, bk, reg in ranked if b == "dovish"]

    usd_rate = POLICY_RATES.get("USD", {}).get("rate", 0)
    eur_rate = POLICY_RATES.get("EUR", {}).get("rate", 0)
    jpy_rate = POLICY_RATES.get("JPY", {}).get("rate", 0)
    aud_rate = POLICY_RATES.get("AUD", {}).get("rate", 0)

    spread_usd_eur = round(usd_rate - eur_rate, 2)
    spread_usd_jpy = round(usd_rate - jpy_rate, 2)
    spread_aud_jpy = round(aud_rate - jpy_rate, 2)

    # Sintesi
    lines = []
    if spread_usd_eur > 1.5:
        lines.append(f"Spread USD-EUR {spread_usd_eur:+.2f}% → vantaggio tasso USA, supporto al dollaro")
    elif spread_usd_eur < 0.5:
        lines.append(f"Spread USD-EUR {spread_usd_eur:+.2f}% → convergenza tassi, pressione sull'EUR")
    if spread_usd_jpy > 3:
        lines.append(f"Spread USD-JPY {spread_usd_jpy:+.2f}% → carry trade JPY ancora vantaggioso")
    if most_hawkish:
        lines.append(f"Banche centrali hawkish: {', '.join(most_hawkish)} — rischio inversion curva")
    if most_dovish:
        lines.append(f"Banche centrali dovish: {', '.join(most_dovish)} — spinte risk-on")

    return {
        "ranked_rates":   [(k, r, b, bk) for k, r, b, bk, reg in ranked],
        "most_hawkish":   most_hawkish,
        "most_dovish":    most_dovish,
        "spread_usd_eur": spread_usd_eur,
        "spread_usd_jpy": spread_usd_jpy,
        "spread_aud_jpy": spread_aud_jpy,
        "divergence_notes": lines,
    }


# ── 4. Global Liquidity Proxies ────────────────────────────────────

# Proxy ticker per la liquidità globale (da snapshot Yahoo Finance)
LIQUIDITY_PROXIES = {
    "fed":  {
        "label":   "Fed (liquidità USA)",
        "tickers": ["TLT", "HYG", "^TNX"],
        "logic":   "TLT↑ HYG↑ = risk-on / QE; TNX↓ = allentamento monetario",
    },
    "pboc": {
        "label":   "PBoC (liquidità Cina)",
        "tickers": ["CNH=X", "MCHI", "FXI"],
        "logic":   "CNH↑ (apprezzamento) + FXI/MCHI↑ = stimolo PBoC attivo",
    },
    "boj":  {
        "label":   "BoJ (YCC/QE Giappone)",
        "tickers": ["JPY=X", "^N225", "EWJ"],
        "logic":   "JPY debole (JPY=X↑ = USD/JPY alto) + Nikkei↑ = YCC/QE attivo",
    },
    "ecb":  {
        "label":   "ECB (liquidità Europa)",
        "tickers": ["EURUSD=X", "^STOXX50E", "XGLE.DE"],
        "logic":   "EURUSD↑ + STOXX↑ = condizioni finanziarie accomodanti",
    },
}


def compute_liquidity_proxies(snapshot: list) -> dict:
    """
    Stima la direzione della liquidità globale usando proxy da Yahoo Finance.
    Non richiede FRED API o accessi speciali.

    Returns:
        dict cb_key → {label, signal, change_avg, logic}
    """
    idx = _snapshot_index(snapshot)
    results = {}

    for cb_key, info in LIQUIDITY_PROXIES.items():
        changes = []
        for ticker in info["tickers"]:
            row = idx.get(ticker)
            if row:
                c = row.get("change_1d_pct")
                if c is not None:
                    changes.append(c)

        avg_chg = _avg(changes)
        if avg_chg is None:
            signal = "⚪ Dati insufficienti"
        elif avg_chg > 0.5:
            signal = "🟢 Condizioni espansive (proxy positivo)"
        elif avg_chg > 0:
            signal = "🟡 Leggermente espansivo"
        elif avg_chg > -0.5:
            signal = "🟠 Leggermente restrittivo"
        else:
            signal = "🔴 Condizioni restrittive (proxy negativo)"

        results[cb_key] = {
            "label":       info["label"],
            "signal":      signal,
            "change_avg":  avg_chg,
            "logic":       info["logic"],
        }

    return results


# ── 5. Format context per il prompt AI ────────────────────────────

def format_global_macro_context(snapshot: list) -> str:
    """
    Genera il blocco di testo Global Macro da inserire nel prompt AI.
    Include: heatmap regionale, CB correlations, policy divergence, liquidity.
    """
    lines = ["=" * 60]
    lines.append("GLOBAL MACRO FRAMEWORK — Analisi Regionale Avanzata")
    lines.append("=" * 60)

    # ── A. Regional Heatmap ────────────────────────────────────────
    heatmap = compute_regional_heatmap(snapshot)
    lines.append("\n📍 HEATMAP REGIONALE (variazione media 1 giorno):")
    lines.append(f"{'Regione':<20} {'Var%':>7}  Segnale")
    lines.append("-" * 50)
    for key, d in sorted(heatmap.items(), key=lambda x: -(x[1].get("trend_score") or 0)):
        chg = d["avg_change_1d"]
        chg_str = f"{chg:+.2f}%" if chg is not None else "N/A"
        lines.append(f"{d['emoji']} {d['label']:<18} {chg_str:>7}  ({d['n_assets']} asset)")
        if d["best_asset"]:
            lines.append(f"   ↑ Best:  {d['best_asset']['name']} ({d['best_asset']['change']:+.2f}%)")
        if d["worst_asset"]:
            lines.append(f"   ↓ Worst: {d['worst_asset']['name']} ({d['worst_asset']['change']:+.2f}%)")

    # ── B. CB→FX→Commodity ─────────────────────────────────────────
    cb_corrs = compute_cb_correlations(snapshot)
    lines.append("\n🔗 CB→FX→COMMODITY CORRELAZIONI:")
    divergences = [(k, v) for k, v in cb_corrs.items() if v.get("alignment") is False]
    alignments  = [(k, v) for k, v in cb_corrs.items() if v.get("alignment") is True]

    if divergences:
        lines.append("⚠️ Divergenze rilevate (potenziali opportunità di trading):")
        for currency, d in divergences:
            lines.append(f"  • {currency} ({d['bank']}): {d['signal']}")
            if d["fx_change"] is not None:
                lines.append(f"    FX: {d['fx_change']:+.2f}%  |  Commodity: {d['commodity_avg_change']:+.2f}%")
            lines.append(f"    Rationale: {d['rationale']}")
    if alignments:
        lines.append("✅ Correlazioni attive (trend confermati):")
        for currency, d in alignments:
            lines.append(f"  • {currency} ({d['bank']}): {d['signal']}")

    # ── C. Policy Divergence ──────────────────────────────────────
    pol = compute_policy_divergence()
    lines.append("\n🏦 BANCHE CENTRALI — POLICY DIVERGENCE:")
    # Top 5 tassi più alti
    top5 = pol["ranked_rates"][:5]
    bottom5 = pol["ranked_rates"][-3:]
    bias_map = {"hawkish": "🦅", "dovish": "🕊️", "neutral": "⚖️"}
    lines.append("  Tassi più alti (bias restrittivo):")
    for currency, rate, bias, bank in top5:
        lines.append(f"    {bias_map.get(bias,'?')} {bank} ({currency}): {rate:.2f}% — {bias}")
    lines.append("  Tassi più bassi (accomodanti):")
    for currency, rate, bias, bank in bottom5:
        lines.append(f"    {bias_map.get(bias,'?')} {bank} ({currency}): {rate:.2f}% — {bias}")
    for note in pol["divergence_notes"]:
        lines.append(f"  → {note}")

    # ── D. Global Liquidity ────────────────────────────────────────
    liq = compute_liquidity_proxies(snapshot)
    lines.append("\n💧 GLOBAL LIQUIDITY TRACKER (proxy da mercato):")
    for cb_key, d in liq.items():
        chg = d["change_avg"]
        chg_str = f"{chg:+.2f}%" if chg is not None else "N/A"
        lines.append(f"  {d['signal']} | {d['label']} ({chg_str})")

    lines.append("=" * 60)
    return "\n".join(lines)
