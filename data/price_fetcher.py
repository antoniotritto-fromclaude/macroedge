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
import time
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
    Tenta con yf.download(), poi con yf.Ticker().history() come fallback.
    """
    end   = datetime.now()
    start = end - timedelta(days=period_days)

    for attempt in range(2):
        try:
            if attempt == 0:
                df = yf.download(
                    ticker,
                    start=start.strftime("%Y-%m-%d"),
                    end=end.strftime("%Y-%m-%d"),
                    progress=False,
                    auto_adjust=True,
                    timeout=30,
                )
            else:
                # Fallback alternativo: Ticker.history()
                t = yf.Ticker(ticker)
                df = t.history(start=start.strftime("%Y-%m-%d"),
                               end=end.strftime("%Y-%m-%d"),
                               auto_adjust=True)

            if df is None or df.empty:
                continue

            # Appiattisci MultiIndex se presente (yfinance 1.x a volte lo aggiunge)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Rinomina "Price" → "Close" se necessario (yfinance 1.x)
            if "Price" in df.columns and "Close" not in df.columns:
                df = df.rename(columns={"Price": "Close"})

            if len(df) < 10:
                continue

            return df

        except Exception as e:
            logger.debug(f"  {ticker} tentativo {attempt+1}: {type(e).__name__}: {e}")

    logger.warning(f"  {ticker}: download fallito dopo 2 tentativi")
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
    Gestisce tutte le varianti di MultiIndex prodotte da yfinance 0.x e 1.x.
    """
    MIN_BARS = 10  # soglia minima ridotta per gestire asset con storia più breve
    required = {"Open", "High", "Low", "Close"}

    def _clean(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Normalizza colonne e restituisce df se valido."""
        df = df.copy().dropna(how="all")
        # In yfinance 1.x con auto_adjust, le colonne possono avere nomi diversi
        # Mappa "Price"→"Close" se presente
        rename_map = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if col_lower == "price":
                rename_map[col] = "Close"
        if rename_map:
            df = df.rename(columns=rename_map)
        if len(df) >= MIN_BARS and required.issubset(df.columns):
            return df
        return None

    try:
        # Caso 1: DataFrame semplice (singolo ticker o già estratto)
        if not isinstance(raw.columns, pd.MultiIndex):
            return _clean(raw)

        # Caso 2: MultiIndex (Ticker, Field) — group_by="ticker" yfinance 0.x/1.x
        try:
            return _clean(raw[ticker])
        except (KeyError, TypeError):
            pass

        # Caso 3: MultiIndex (Field, Ticker) — default yfinance (no group_by)
        try:
            return _clean(raw.xs(ticker, axis=1, level=1))
        except (KeyError, TypeError):
            pass

        # Caso 4: livelli swappati
        try:
            return _clean(raw.swaplevel(axis=1)[ticker])
        except (KeyError, TypeError):
            pass

        # Caso 5: prova con il ticker come level=0 (yfinance 1.x variante)
        try:
            lvl0 = raw.columns.get_level_values(0)
            if ticker in lvl0.tolist():
                mask = lvl0 == ticker
                df = raw.iloc[:, mask].copy()
                df.columns = df.columns.get_level_values(1)
                return _clean(df)
        except Exception:
            pass

        logger.debug(f"  {ticker}: nessuna struttura MultiIndex riconosciuta")
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

    # ── Batch download con retry ────────────────────────────────────
    raw = None
    for attempt in range(3):
        try:
            raw = yf.download(
                tickers,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,    # Parallelo = molto più veloce in CI
                timeout=90,
            )
            if raw is not None and not raw.empty and len(raw) >= 5:
                logger.info(f"  Batch download OK al tentativo {attempt+1}: {raw.shape}")
                break
            else:
                raw = None
                logger.warning(f"  Batch download vuoto (tentativo {attempt+1}/3)")
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
        except Exception as e:
            logger.warning(f"  Batch download fallito tentativo {attempt+1}/3: {type(e).__name__}: {e}")
            raw = None
            if attempt < 2:
                time.sleep(3 * (attempt + 1))

    if raw is None:
        logger.warning("  Tutti i tentativi batch falliti — uso download singolo")

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
