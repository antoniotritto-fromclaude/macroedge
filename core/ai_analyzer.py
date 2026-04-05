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
    CATEGORY_LABELS,
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
        max_tokens=3000,
    )
    return r.choices[0].message.content


def _call_gemini(prompt: str) -> str:
    """Gemini 1.5 Flash — gratuito fino a 1.500 req/giorno."""
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    r = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(temperature=0.3, max_output_tokens=3000)
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
        max_tokens=3000,
    )
    return r.choices[0].message.content


def _call_anthropic(prompt: str) -> str:
    """Claude — a pagamento (~$0.05-0.15 per report)."""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    r = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=3000,
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
    """Raggruppa gli asset per categoria nel riepilogo tecnico."""
    from collections import defaultdict
    by_cat = defaultdict(list)
    for a in snapshot:
        by_cat[a.get("category", "other")].append(a)

    sections = []
    for cat, assets in by_cat.items():
        label = CATEGORY_LABELS.get(cat, cat.upper())
        lines = [f"=== {label} ==="]
        for a in assets:
            chg = a.get("change_1d_pct", 0) or 0
            dxy = a.get("dxy_correlation")
            atr = a.get("atr")
            lines.append(
                f"• {a.get('name','')} ({a.get('ticker','')})\n"
                f"  Prezzo: {a.get('price','N/A')} | 1D: {chg:+.2f}% | {a.get('rsi_signal','N/A')}\n"
                f"  Trend: {a.get('trend','N/A')}\n"
                f"  Sup20d: {a.get('support_20d','N/A')} | Res20d: {a.get('resistance_20d','N/A')}"
                + (f" | ATR: {atr}" if atr is not None else "")
                + (f" | Corr.DXY: {dxy:.2f}" if dxy is not None else "")
            )
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def _build_prompt(cycle: str, technical_summary: str, news_text: str,
                  fx_context: str = "", eia_context: str = "",
                  geo_context: str = "", usda_context: str = "") -> str:
    today      = datetime.now().strftime("%A %d %B %Y")
    report_day = "Lunedì" if cycle == "A" else "Giovedì"
    window     = "sabato e domenica" if cycle == "A" else "mercoledì"

    # Sezioni opzionali — incluse solo se hanno contenuto
    specialized_sections = ""
    if fx_context:
        specialized_sections += f"\n\n{fx_context}"
    if eia_context:
        specialized_sections += f"\n\n{eia_context}"
    if usda_context:
        specialized_sections += f"\n\n{usda_context}"
    if geo_context:
        specialized_sections += f"\n\n{geo_context}"

    return f"""Sei MacroEdge, un sistema di analisi finanziaria quantitativa professionale.
Oggi è {today}. Prepara il report operativo per {report_day} mattina.
L'universo copre ~130 asset: indici globali, valute FX, commodities, obbligazioni,
ETF settoriali/regionali, crypto ETF, e azioni individuali di USA, Europa (IT/FR/UK/DE/ES),
Cina, Giappone, Brasile e Messico.

DATI TECNICI PER CATEGORIA (chiusura precedente):
{technical_summary}{specialized_sections}

NEWS {window.upper()}:
{news_text}

COMPITO:
1. Identifica la DIVERGENZA CHIAVE: asset il cui prezzo non riflette ancora le news.
2. Trova 2-3 trade ideas dove news e tecnica concordano, con livelli Entry/Stop/Target precisi.
   - Per trade Short: suggerisci sempre un ETF inverso alternativo (es. SH, PSQ, SDS, DOG).
   - Usa ATR per dimensionare lo stop: stop = entry ± 1.5×ATR.
   - Per trade FX: considera il carry trade bias dai differenziali di tasso.
   - Per trade Energia: pesa i dati EIA (crude stocks draw/build) vs trend tecnico.
   - Per trade Agricoltura: usa Stock-to-Use ratio USDA per identificare mercati stretti.
   - Per trade EM/Latam: considera il rischio geopolitico e USD/BRL, USD/MXN.
3. Seleziona le TOP 5 OPPORTUNITÀ singole (azioni o ETF) con il miglior setup tecnico+news.
4. Segnala alert correlazione DXY e altre correlazioni anomale tra asset.
5. Per ogni trade, specifica il paese dell'azione se si tratta di un singolo titolo.

Rispondi ESCLUSIVAMENTE con JSON valido. Zero testo prima o dopo il JSON.

{{
  "report_day": "{report_day}",
  "bias": "Risk-On|Risk-Off|Neutrale",
  "bias_causa": "causa principale in 1 frase",
  "sentiment_score": 0,
  "divergenza_chiave": {{
    "descrizione": "spiegazione divergenza",
    "asset_coinvolto": "nome asset",
    "news_che_cambia_tutto": "titolo news chiave",
    "impatto_atteso": "Long|Short",
    "urgenza": "Alta|Media"
  }},
  "trade_ideas": [
    {{
      "settore": "nome settore/tema",
      "direzione": "Long|Short",
      "forza_segnale": "Alta|Media|Bassa",
      "entry": "prezzo o range di ingresso",
      "stop_loss": "prezzo di stop (1.5×ATR)",
      "take_profit": "prezzo target",
      "rischio_rendimento": "1:2",
      "atr_note": "ATR asset principale per sizing posizione",
      "causa_news": "quale evento guida il trade",
      "causa_tecnica": "stato tecnico che conferma",
      "logica_completa": "2-3 frasi che spiegano il setup",
      "etf": [{{"ticker": "XXX", "nome": "nome ETF long", "note": "perché"}}],
      "etf_inverso": [{{"ticker": "SH", "nome": "nome ETF inverso", "note": "alternativa Short"}}],
      "azioni": [
        {{"ticker": "AAA", "nome": "azienda", "paese": "US|IT|FR|UK|DE|ES|CN|JP|BR|MX", "catalizzatore": "evento"}},
        {{"ticker": "BBB", "nome": "azienda", "paese": "...", "catalizzatore": "evento"}},
        {{"ticker": "CCC", "nome": "azienda", "paese": "...", "catalizzatore": "evento"}}
      ],
      "timeframe_giorni": "3-7"
    }}
  ],
  "top5_opportunita": [
    {{
      "rank": 1,
      "ticker": "AAPL",
      "nome": "Apple",
      "paese": "US",
      "direzione": "Long|Short",
      "catalizzatore": "evento news o tecnico che crea il setup",
      "entry": "prezzo",
      "stop": "prezzo",
      "target": "prezzo",
      "forza": "Alta|Media",
      "timeframe_giorni": "3-7"
    }}
  ],
  "alert_correlazioni": [
    {{
      "asset1": "nome",
      "asset2": "nome",
      "tipo": "divergenza|inversione|rottura",
      "descrizione": "spiegazione breve dell'anomalia"
    }}
  ],
  "alert_dollaro": false,
  "alert_dollaro_dettaglio": "",
  "macro_outlook": "2-3 frasi sull'outlook macro della settimana",
  "da_monitorare": ["evento 1", "evento 2", "evento 3"]
}}"""


def analyze(cycle: str, snapshot: list, news_list: list,
            fx_data: list = None, eia_data: dict = None,
            geo_data: dict = None, usda_data: dict = None) -> Optional[dict]:
    from data.news_reader import format_news_for_ai
    from data.fx_analyzer import format_fx_context
    from data.eia_fetcher import format_eia_context
    from data.geo_risk_scorer import format_geo_context
    from data.usda_fetcher import format_usda_context

    logger.info(f"Analisi — Ciclo {'A (Lunedì)' if cycle == 'A' else 'B (Giovedì)'} | {AI_PROVIDER.upper()}")

    fx_ctx   = format_fx_context(fx_data or [])
    eia_ctx  = format_eia_context(eia_data or {})
    geo_ctx  = format_geo_context(geo_data or {})
    usda_ctx = format_usda_context(usda_data or {})

    prompt = _build_prompt(
        cycle,
        _build_technical_summary(snapshot),
        format_news_for_ai(news_list, max_items=25),
        fx_context=fx_ctx,
        eia_context=eia_ctx,
        geo_context=geo_ctx,
        usda_context=usda_ctx,
    )

    raw = ""
    for attempt in range(2):
        try:
            raw = _call_ai(prompt) if attempt == 0 else _call_ai(
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
            report.update({
                "generated_at": datetime.now().isoformat(),
                "cycle": cycle,
                "provider_used": AI_PROVIDER,
                "asset_count": len(snapshot),
            })
            logger.info(f"  OK — Bias: {report.get('bias','N/A')} | Top5: {len(report.get('top5_opportunita',[]))}")
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
