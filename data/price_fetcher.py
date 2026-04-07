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
LOOKBACK_DAYS = 210


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
    Gestisce tutte le varianti di MultiIndex prodotte da diverse versioni di yfinance.
    """
    required = {"Open", "High", "Low", "Close"}
    try:
        # Caso 1: DataFrame semplice (singolo ticker o già estratto)
        if not isinstance(raw.columns, pd.MultiIndex):
            df = raw.copy().dropna(how="all")
            return df if len(df) >= 20 and required.issubset(df.columns) else None

        # Caso 2: MultiIndex — prova struttura (ticker, OHLCV) — group_by="ticker"
        try:
            df = raw[ticker].copy().dropna(how="all")
            if len(df) >= 20 and required.issubset(df.columns):
                return df
        except (KeyError, TypeError):
            pass

        # Caso 3: MultiIndex — prova struttura (OHLCV, ticker) — default yfinance
        try:
            df = raw.xs(ticker, axis=1, level=1).copy().dropna(how="all")
            if len(df) >= 20 and required.issubset(df.columns):
                return df
        except (KeyError, TypeError):
            pass

        # Caso 4: prova con livelli scambiati
        try:
            df = raw.swaplevel(axis=1)[ticker].copy().dropna(how="all")
            if len(df) >= 20 and required.issubset(df.columns):
                return df
        except (KeyError, TypeError):
            pass

        return None

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
    # Se il batch fallisce, scarica solo i top 60 asset prioritari (non tutti 141)
    PRIORITY_CATS = {
        "energy", "metals_precious", "metals_industrial",
        "index_us", "index_eu", "index_asia", "fx", "bonds",
        "agriculture", "softs", "etf_sector", "etf_global",
        "etf_em", "crypto_etf",
    }
    priority_assets = [a for a in assets if a.get("category") in PRIORITY_CATS]
    other_assets    = [a for a in assets if a.get("category") not in PRIORITY_CATS]
    # Ordine: priorità macro prima, poi azioni
    assets_ordered  = priority_assets + other_assets

    tickers   = [a["ticker"] for a in assets_ordered]
    asset_map = {a["ticker"]: a for a in assets_ordered}

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
            threads=True,    # Parallelo = molto più veloce in CI (~15s vs 7+ min)
            timeout=90,      # Evita blocchi infiniti
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
    # Se il batch ha fallito, limita i fallback individuali ai top 60
    # per evitare 141 × 30s = 70 minuti nel caso peggiore
    assets_to_process = assets_ordered
    if raw is None:
        assets_to_process = assets_ordered[:60]
        logger.warning(f"  Batch fallito: fallback limitato a {len(assets_to_process)} asset prioritari")

    results = []
    ok   = 0
    fail = 0

    for asset in assets_to_process:
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
