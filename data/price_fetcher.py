# macroedge/data/price_fetcher.py
# ================================================================
# Scarica i prezzi da Yahoo Finance e calcola gli indicatori tecnici.
# Usa yfinance per i dati OHLCV e calcola manualmente MA, RSI, ATR.
#
# Funzioni pubbliche:
#   fetch_asset_data(ticker)          → pd.DataFrame | None
#   compute_indicators(df)            → dict
#   get_full_market_snapshot(assets)  → list[dict]
# ================================================================

import logging
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("macroedge.price_fetcher")

# Giorni di dati scaricati per avere abbastanza storia per MA200 + ATR
LOOKBACK_DAYS = 260


def fetch_asset_data(ticker: str, period_days: int = LOOKBACK_DAYS) -> Optional[pd.DataFrame]:
    """
    Scarica i dati OHLCV da Yahoo Finance per un singolo ticker.

    Returns:
        DataFrame con colonne Open, High, Low, Close, Volume,
        oppure None se il download fallisce o i dati sono insufficienti.
    """
    try:
        end   = datetime.now()
        start = end - timedelta(days=period_days)

        df = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
            timeout=30,
        )

        if df is None or df.empty:
            logger.warning(f"  {ticker}: nessun dato ricevuto da Yahoo Finance")
            return None

        # yfinance può restituire MultiIndex con il ticker come secondo livello
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if len(df) < 20:
            logger.warning(f"  {ticker}: dati insufficienti ({len(df)} barre)")
            return None

        return df

    except Exception as e:
        logger.error(f"  Errore download {ticker}: {e}")
        return None


def compute_indicators(df: pd.DataFrame) -> dict:
    """
    Calcola indicatori tecnici su un DataFrame OHLCV.

    Returns:
        dict con: price, change_1d_pct, ma50, ma200, rsi, rsi_signal,
                  atr, trend, support_20d, resistance_20d
    """
    close = df["Close"].squeeze()
    high  = df["High"].squeeze()
    low   = df["Low"].squeeze()
    n     = len(close)

    # ── Prezzi correnti ────────────────────────────────────────────
    price      = round(float(close.iloc[-1]), 4)
    prev_close = float(close.iloc[-2]) if n >= 2 else price
    change_1d  = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0.0

    # ── Medie mobili ───────────────────────────────────────────────
    ma50  = round(float(close.rolling(50).mean().iloc[-1]), 4)  if n >= 50  else None
    ma200 = round(float(close.rolling(200).mean().iloc[-1]), 4) if n >= 200 else None

    # ── RSI 14 periodi ─────────────────────────────────────────────
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))

    rsi_val = rsi_series.iloc[-1]
    if pd.isna(rsi_val):
        rsi        = None
        rsi_signal = "RSI N/A"
    else:
        rsi = round(float(rsi_val), 1)
        if rsi >= 70:
            rsi_signal = f"RSI {rsi} (ipercomprato)"
        elif rsi <= 30:
            rsi_signal = f"RSI {rsi} (ipervenduto)"
        else:
            rsi_signal = f"RSI {rsi} (neutro)"

    # ── ATR 14 periodi ─────────────────────────────────────────────
    prev_c = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_c).abs(),
        (low  - prev_c).abs(),
    ], axis=1).max(axis=1)
    atr_val = tr.rolling(14).mean().iloc[-1]
    atr = round(float(atr_val), 4) if not pd.isna(atr_val) else None

    # ── Trend ──────────────────────────────────────────────────────
    if ma50 is not None and ma200 is not None:
        if price > ma50 > ma200:
            trend = "Uptrend (price > MA50 > MA200)"
        elif price < ma50 < ma200:
            trend = "Downtrend (price < MA50 < MA200)"
        elif price > ma200:
            trend = "Sopra MA200 (fase di recupero)"
        else:
            trend = "Sotto MA200 (debolezza strutturale)"
    elif ma50 is not None:
        trend = "Sopra MA50" if price > ma50 else "Sotto MA50"
    else:
        trend = "Dati insuff. per trend"

    # ── Supporto / Resistenza ultimi 20 giorni ─────────────────────
    window      = min(20, n)
    support_20d    = round(float(low.iloc[-window:].min()), 4)
    resistance_20d = round(float(high.iloc[-window:].max()), 4)

    return {
        "price":          price,
        "change_1d_pct":  change_1d,
        "ma50":           ma50,
        "ma200":          ma200,
        "rsi":            rsi,
        "rsi_signal":     rsi_signal,
        "atr":            atr,
        "trend":          trend,
        "support_20d":    support_20d,
        "resistance_20d": resistance_20d,
    }


def _compute_dxy_correlation(asset_df: pd.DataFrame, dxy_df: pd.DataFrame) -> Optional[float]:
    """Calcola la correlazione a 60 giorni tra i rendimenti di un asset e il DXY."""
    try:
        asset_ret = asset_df["Close"].squeeze().pct_change().dropna()
        dxy_ret   = dxy_df["Close"].squeeze().pct_change().dropna()

        aligned = pd.concat([asset_ret, dxy_ret], axis=1, join="inner").dropna()
        if len(aligned) < 20:
            return None

        aligned = aligned.iloc[-60:]
        corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
        return round(float(corr), 2) if not np.isnan(corr) else None
    except Exception:
        return None


def get_full_market_snapshot(assets: list) -> list:
    """
    Scarica dati e calcola indicatori per tutti gli asset in lista.
    Aggiunge la correlazione con il DXY (Dollar Index) per ogni asset.

    Args:
        assets: lista di dict con keys: name, ticker, category, currency

    Returns:
        Lista di dict con indicatori tecnici completi.
        Gli asset con errori di download vengono saltati.
    """
    logger.info(f"Scaricamento dati per {len(assets)} asset da Yahoo Finance...")

    # Scarica prima il DXY per calcolare le correlazioni
    dxy_df = fetch_asset_data("DX-Y.NYB")
    if dxy_df is None:
        logger.warning("  DXY non disponibile — correlazioni non calcolate")

    results = []
    ok   = 0
    fail = 0

    for asset in assets:
        ticker = asset["ticker"]
        name   = asset["name"]

        try:
            df = fetch_asset_data(ticker)
            if df is None:
                logger.warning(f"  SKIP {name} ({ticker})")
                fail += 1
                continue

            indicators = compute_indicators(df)

            row = {
                "name":     name,
                "ticker":   ticker,
                "category": asset.get("category", "other"),
                "currency": asset.get("currency", "USD"),
                **indicators,
            }

            # Correlazione DXY (escludi il DXY stesso)
            if dxy_df is not None and ticker != "DX-Y.NYB":
                row["dxy_correlation"] = _compute_dxy_correlation(df, dxy_df)
            else:
                row["dxy_correlation"] = None

            results.append(row)
            ok += 1

        except Exception as e:
            logger.error(f"  Errore {name} ({ticker}): {e}")
            fail += 1

    logger.info(f"Snapshot completato: {ok}/{len(assets)} asset ({fail} errori)")
    return results
