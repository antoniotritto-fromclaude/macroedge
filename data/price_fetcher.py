# macroedge/data/price_fetcher.py
# ================================================================
# Scarica i prezzi da Yahoo Finance e calcola gli indicatori tecnici.
# Usa yfinance batch download per scaricare tutti i ticker in una sola
# chiamata (~15s per 130 asset invece di ~4 minuti uno alla volta).
#
# Funzioni pubbliche:
#   fetch_asset_data(ticker)          → pd.DataFrame | None  (fallback singolo)
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
    Usato come fallback individuale se il batch download fallisce.
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


def _extract_ticker_df(raw: pd.DataFrame, ticker: str) -> Optional[pd.DataFrame]:
    """
    Estrae il DataFrame di un singolo ticker dal risultato batch di yfinance.
    Gestisce sia MultiIndex (batch) che DataFrame normale (singolo ticker).
    """
    try:
        if isinstance(raw.columns, pd.MultiIndex):
            # yfinance batch con group_by="ticker": livello 0 = ticker, livello 1 = OHLCV
            level0 = raw.columns.get_level_values(0).unique().tolist()
            level1 = raw.columns.get_level_values(1).unique().tolist()

            # Determina la struttura: (ticker, Price) o (Price, ticker)
            ohlcv_cols = {"Open", "High", "Low", "Close", "Volume"}
            if ticker in level0 and any(c in ohlcv_cols for c in level1):
                df = raw[ticker].copy()
            elif ticker in level1 and any(c in ohlcv_cols for c in level0):
                df = raw.xs(ticker, axis=1, level=1).copy()
            else:
                return None
        else:
            df = raw.copy()

        df = df.dropna(how="all")
        if df.empty or len(df) < 20:
            return None

        # Assicura che le colonne OHLCV siano presenti
        required = {"Open", "High", "Low", "Close"}
        if not required.issubset(set(df.columns)):
            return None

        return df

    except Exception as e:
        logger.debug(f"  Errore estrazione {ticker}: {e}")
        return None


def get_full_market_snapshot(assets: list) -> list:
    """
    Scarica dati e calcola indicatori per tutti gli asset in lista.
    Usa batch download per massima efficienza (~15s per 130 asset).
    Fallback su download singolo per ticker che falliscono nel batch.

    Args:
        assets: lista di dict con keys: name, ticker, category, currency

    Returns:
        Lista di dict con indicatori tecnici completi.
    """
    tickers   = [a["ticker"] for a in assets]
    asset_map = {a["ticker"]: a for a in assets}

    end   = datetime.now()
    start = end - timedelta(days=LOOKBACK_DAYS)

    logger.info(f"Batch download {len(tickers)} ticker da Yahoo Finance...")

    # ── Batch download ─────────────────────────────────────────────
    raw = None
    try:
        raw = yf.download(
            tickers,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
            timeout=120,
        )
        if raw is None or raw.empty:
            raw = None
            logger.warning("  Batch download vuoto — uso download singolo per tutti")
    except Exception as e:
        logger.warning(f"  Batch download fallito ({e}) — uso download singolo")
        raw = None

    # ── Scarica DXY per correlazioni ───────────────────────────────
    dxy_df = None
    if raw is not None:
        dxy_df = _extract_ticker_df(raw, "DX-Y.NYB")
    if dxy_df is None:
        logger.info("  Download DXY individuale...")
        dxy_df = fetch_asset_data("DX-Y.NYB")
    if dxy_df is None:
        logger.warning("  DXY non disponibile — correlazioni non calcolate")

    # ── Processa ogni asset ────────────────────────────────────────
    results = []
    ok   = 0
    fail = 0

    for asset in assets:
        ticker = asset["ticker"]
        name   = asset["name"]

        try:
            # Prova prima dal batch, poi download singolo
            df = None
            if raw is not None:
                df = _extract_ticker_df(raw, ticker)
            if df is None:
                logger.debug(f"  {ticker}: fallback download singolo")
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
