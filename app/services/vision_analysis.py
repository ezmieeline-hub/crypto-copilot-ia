import base64
import json
import os

import httpx

GEMINI_MODEL = "gemini-flash-latest"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

PROMPT_TEMPLATE = """Tu es un analyste technique crypto expert. Analyse cette capture d'écran d'un graphique de trading (TradingView ou équivalent).

{market_context}

Réponds UNIQUEMENT avec un objet JSON valide (rien d'autre : pas de texte avant/après, pas de balises markdown), avec exactement ces clés :
{{
  "symbol_detected": "symbole détecté sur le graphique ou null",
  "timeframe_detected": "unité de temps détectée (ex: 1H, 4H, 1D) ou null",
  "trend": "haussière, baissière ou neutre",
  "candlestick_patterns": ["liste des figures chartistes ou patterns détectés, ex: double top, tête-épaules, triangle..."],
  "support": nombre_ou_null,
  "resistance": nombre_ou_null,
  "visible_indicators": "description courte des indicateurs visibles sur l'image (RSI, MACD, volume...) s'il y en a",
  "signal": "ACHAT, VENTE ou ATTENDRE",
  "confidence": nombre_entre_0_et_100,
  "justification": "explication claire en français en 2 à 4 phrases de pourquoi ce signal",
  "entry": nombre_ou_null,
  "take_profit": nombre_ou_null,
  "stop_loss": nombre_ou_null
}}
"""


class VisionAnalysisError(Exception):
    pass


async def analyze_screenshot(image_bytes: bytes, mime_type: str, market_context: dict | None = None):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise VisionAnalysisError("Clé GEMINI_API_KEY manquante sur le serveur.")

    if market_context:
        context_text = (
            f"Voici les données de marché réelles actuelles pour {market_context.get('pair')} "
            "(elles proviennent de Binance en temps réel et priment sur toute estimation visuelle) :\n"
            f"- Prix actuel : {market_context.get('price')}\n"
            f"- RSI (14, H1) : {market_context.get('rsi')}\n"
            f"- MACD : {market_context.get('macd')} "
            f"(ligne signal : {market_context.get('macd_signal')}, histogramme : {market_context.get('macd_hist')})\n"
            f"- Support récent : {market_context.get('support')}\n"
            f"- Résistance récente : {market_context.get('resistance')}\n"
            "Utilise ces données réelles pour affiner et justifier ton signal."
        )
    else:
        context_text = (
            "Aucune donnée de marché complémentaire n'est disponible pour ce symbole : "
            "base-toi uniquement sur la lecture visuelle de la capture."
        )

    prompt = PROMPT_TEMPLATE.format(market_context=context_text)
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": b64_image}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(GEMINI_URL, params={"key": api_key}, json=payload)
    except httpx.RequestError:
        raise VisionAnalysisError("Impossible de contacter le service d'analyse d'image. Réessayez.")

    if r.status_code != 200:
        raise VisionAnalysisError(
            f"Erreur du service d'analyse d'image (code {r.status_code}). Réessayez dans quelques instants."
        )

    data = r.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except (KeyError, IndexError, json.JSONDecodeError):
        raise VisionAnalysisError("Réponse de l'IA illisible, réessayez.")

    return result
