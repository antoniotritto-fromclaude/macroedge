# macroedge/core/ai_analyzer.py
# ================================================================
# Motore AI — supporta provider gratuiti e a pagamento.
# Cambia AI_PROVIDER in config.py per switchare.
#
# Provider supportati:
#   "groq"      → Llama 3.3 70B   — CONSIGLIATO (gratuito, veloce)
#   "gemini"    → Gemini 1.5 Flash — gratuito
#   "mistral"   → Mistral Small    — tier gratuito
#   "anthropic" → Claude Opus/Sonnet — a pagamento
# ================================================================

import json
import logging
from datetime import datetime
from typing import Optional
from config import (
    AI_PROVIDER,
    GROQ_API_KEY, GROQ_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL,
    MISTRAL_API_KEY, MISTRAL_MODEL,
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
)

logger = logging.getLogger("macroedge.ai")


def _call_groq(prompt: str) -> str:
    """Groq — Llama 3.3 70B, gratuito fino a 14.400 req/giorno."""
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    r = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
    )
    return r.choices[0].message.content


def _call_gemini(prompt: str) -> str:
    """Gemini 1.5 Flash — gratuito fino a 1.500 req/giorno."""
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    r = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(temperature=0.3, max_output_tokens=2000)
    )
    return r.text


def _call_mistral(prompt: str) -> str:
    """Mistral Small — tier gratuito disponibile."""
    from mistralai import Mistral
    client = Mistral(api_key=MISTRAL_API_KEY)
    r = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
    )
    return r.choices[0].message.content


def _call_anthropic(prompt: str) -> str:
    """Claude — a pagamento (~$0.05-0.15 per report)."""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    r = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.content[0].text


_PROVIDERS = {
    "groq":      _call_groq,
    "gemini":    _call_gemini,
    "mistral":   _call_mistral,
    "anthropic": _call_anthropic,
}


def _call_ai(prompt: str) -> str:
    fn = _PROVIDERS.get(AI_PROVIDER)
    if not fn:
        raise ValueError(f"Provider '{AI_PROVIDER}' non valido. Scegli: {list(_PROVIDERS)}")
    logger.info(f"  Provider: {AI_PROVIDER.upper()}")
    return fn(prompt)


def _build_technical_summary(snapshot: list) -> str:
    lines = []
    for a in snapshot:
        chg = a.get("change_1d_pct", 0)
        dxy = a.get("dxy_correlation")
        lines.append(
            f"• {a.get('name','')} ({a.get('ticker','')}) [{a.get('category','')}]\n"
            f"  Prezzo: {a.get('price','N/A')} | 1D: {chg:+.2f}% | {a.get('rsi_signal','N/A')}\n"
            f"  Trend: {a.get('trend','N/A')}\n"
            f"  Sup: {a.get('support_20d','N/A')} | Res: {a.get('resistance_20d','N/A')}"
            + (f" | Corr.DXY: {dxy:.2f}" if dxy is not None else "")
        )
    return "\n\n".join(lines)


def _build_prompt(cycle: str, technical_summary: str, news_text: str) -> str:
    today      = datetime.now().strftime("%A %d %B %Y")
    report_day = "Lunedì" if cycle == "A" else "Giovedì"
    window     = "sabato e domenica" if cycle == "A" else "mercoledì"

    return f"""Sei MacroEdge, un sistema di analisi finanziaria quantitativa.
Oggi è {today}. Prepara il report operativo per {report_day} mattina.

DATI TECNICI (chiusura precedente):
{technical_summary}

NEWS {window.upper()}:
{news_text}

COMPITO:
1. Identifica la DIVERGENZA CHIAVE: asset il cui prezzo non riflette ancora le news.
2. Trova trade ideas dove news e tecnica concordano.
3. Segnala rischi correlazione DXY se presente.

Rispondi ESCLUSIVAMENTE con JSON valido. Zero testo prima o dopo.

{{
  "report_day": "{report_day}",
  "bias": "Risk-On|Risk-Off|Neutrale",
  "bias_causa": "causa principale in 1 frase",
  "sentiment_score": 0,
  "divergenza_chiave": {{
    "descrizione": "spiegazione divergenza",
    "asset_coinvolto": "nome",
    "news_che_cambia_tutto": "titolo news",
    "impatto_atteso": "Long|Short",
    "urgenza": "Alta|Media"
  }},
  "trade_ideas": [
    {{
      "settore": "nome",
      "direzione": "Long|Short",
      "forza_segnale": "Alta|Media|Bassa",
      "causa_news": "quale evento guida",
      "causa_tecnica": "stato tecnico",
      "logica_completa": "2-3 frasi",
      "etf": [{{"ticker": "XXX", "nome": "nome", "note": "perché"}}],
      "azioni": [
        {{"ticker": "AAA", "nome": "azienda", "catalizzatore": "evento"}},
        {{"ticker": "BBB", "nome": "azienda", "catalizzatore": "evento"}},
        {{"ticker": "CCC", "nome": "azienda", "catalizzatore": "evento"}},
        {{"ticker": "DDD", "nome": "azienda", "catalizzatore": "evento"}}
      ],
      "timeframe_giorni": "3-7",
      "livelli": {{"supporto": "val", "resistenza": "val", "stop_loss_indicativo": "val"}}
    }}
  ],
  "alert_dollaro": false,
  "alert_dollaro_dettaglio": "",
  "macro_outlook": "2-3 frasi",
  "da_monitorare": ["evento 1", "evento 2", "evento 3"]
}}"""


def analyze(cycle: str, snapshot: list, news_list: list) -> Optional[dict]:
    from data.news_reader import format_news_for_ai

    logger.info(f"Analisi — Ciclo {'A (Lunedì)' if cycle == 'A' else 'B (Giovedì)'} | {AI_PROVIDER.upper()}")

    prompt = _build_prompt(
        cycle,
        _build_technical_summary(snapshot),
        format_news_for_ai(news_list, max_items=25)
    )

    for attempt in range(2):
        try:
            raw   = _call_ai(prompt) if attempt == 0 else _call_ai(
                f"Restituisci SOLO il JSON corretto, zero testo extra:\n\n{raw}"
            )
            clean = raw.strip()
            if "```" in clean:
                for part in clean.split("```"):
                    p = part.lstrip("json").strip()
                    if p.startswith("{"):
                        clean = p
                        break

            report = json.loads(clean)
            report.update({"generated_at": datetime.now().isoformat(), "cycle": cycle, "provider_used": AI_PROVIDER})
            logger.info(f"  OK — Bias: {report.get('bias','N/A')}")
            return report

        except json.JSONDecodeError as e:
            if attempt == 0:
                logger.warning(f"  JSON non valido (tentativo 1), riprovo: {e}")
            else:
                logger.error(f"  JSON non valido anche al 2° tentativo: {e}")
                return None
        except Exception as e:
            logger.error(f"  Errore AI ({AI_PROVIDER}): {e}")
            return None
