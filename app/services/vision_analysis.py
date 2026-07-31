import base64
import json
import os

import httpx

GEMINI_MODEL = "gemini-flash-latest"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

PROMPT_TEMPLATE = """
Tu es un trader professionnel spécialisé en Smart Money Concepts (SMC), ICT, Price Action et analyse institutionnelle.

Tu analyses une capture TradingView.

Les données Binance ci-dessous sont les données officielles en temps réel.

{market_context}

IMPORTANT

Les données Binance sont prioritaires pour :

- prix
- RSI
- MACD
- EMA
- Volume
- Support
- Résistance

La capture TradingView est utilisée pour :

- Structure du marché
- BOS
- CHoCH
- MSS
- Order Blocks
- Supply
- Demand
- Weak High
- Weak Low
- Equal High
- Equal Low
- FVG
- Liquidity Sweep
- Break of Structure
- Bougies
- Tendances
- Zones institutionnelles

Analyse tout ce qui est visible.

Ne jamais inventer un indicateur absent.

Si un élément n'est pas visible écrire null.

Réponds UNIQUEMENT avec un JSON valide.

{

"symbol_detected": "",

"timeframe_detected":"",

"trend":"",

"trend_strength":"",

"signal":"ACHAT",

"confidence":0,

"entry":null,

"stop_loss":null,

"take_profit":null,

"support":null,

"resistance":null,

"risk_reward":null,

"market_structure":{

"bos":false,

"choch":false,

"mss":false,

"trend_direction":"",

"breakout":false,

"pullback":false

},

"smc":{

"order_block":null,

"demand_zone":null,

"supply_zone":null,

"fvg":null,

"liquidity":null,

"weak_high":false,

"weak_low":false,

"equal_high":false,

"equal_low":false

},

"patterns":[

],

"candlestick_patterns":[

],

"visible_indicators":[

],

"scalping":{

"direction":"",

"entry":null,

"stop_loss":null,

"tp1":null,

"tp2":null,

"confidence":0

},

"day_trade":{

"direction":"",

"entry":null,

"stop_loss":null,

"tp1":null,

"tp2":null,

"tp3":null,

"confidence":0

},

"swing_trade":{

"direction":"",

"entry":null,

"stop_loss":null,

"target":null,

"confidence":0

},

"trade_management":{

"break_even":null,

"partial_take_profit":"",

"runner_target":""

},

"decision":"",

"summary":"",

"why":"",

"invalidation":"",

"conditions":[

]

}

Consignes :

- Vérifier si BOS est visible.
- Vérifier si CHoCH est visible.
- Vérifier si MSS est visible.
- Vérifier si Weak High est visible.
- Vérifier si Weak Low est visible.
- Vérifier si Equal High est visible.
- Vérifier si Equal Low est visible.
- Vérifier si FVG est visible.
- Vérifier si Order Block est visible.
- Vérifier si Supply est visible.
- Vérifier si Demand est visible.
- Vérifier si Liquidity Sweep est visible.

Le prix d'entrée doit être cohérent avec Binance.

Le Stop Loss doit être logique.

Le Take Profit doit être réaliste.

Le ratio Risk Reward doit être supérieur à 2 lorsque cela est possible.

Si la capture montre un retracement :

Décision = ATTENDRE

Si BOS + CHOCH + Confirmation :

Décision = ACHAT

Si cassure baissière confirmée :

Décision = VENTE

Le résumé doit être professionnel.

La justification doit expliquer clairement pourquoi l'IA prend cette décision.

Ne jamais répondre autrement qu'avec du JSON.

Analyse également les éléments suivants lorsqu'ils sont visibles :

=========================
SMART MONEY CONCEPTS
=========================

- BOS (Break Of Structure)
- CHoCH (Change Of Character)
- MSS (Market Structure Shift)
- Internal Structure
- External Structure
- Premium Zone
- Discount Zone
- Liquidity Grab
- Buy Side Liquidity
- Sell Side Liquidity
- Inducement
- Breaker Block
- Mitigation Block
- Order Block
- Supply Zone
- Demand Zone
- Fair Value Gap (FVG)
- Imbalance
- Weak High
- Weak Low
- Equal High
- Equal Low
- Premium Array
- Discount Array

=========================
PRICE ACTION
=========================

Détecter si possible :

- Double Top
- Double Bottom
- Triple Top
- Triple Bottom
- Tête épaules
- Triangle
- Canal
- Drapeau
- Fanion
- Wedge
- Range
- Compression
- Expansion
- Rejet
- Cassure

=========================
BOUGIES
=========================

Identifier les bougies importantes :

- Marteau
- Marteau inversé
- Doji
- Englobante haussière
- Englobante baissière
- Étoile du matin
- Étoile du soir
- Pin Bar
- Inside Bar
- Outside Bar

=========================
ANALYSE
=========================

Toujours analyser :

- Force de la tendance
- Momentum
- Pression acheteuse
- Pression vendeuse
- Volatilité
- Probabilité de réussite

=========================
PRISE DE DECISION
=========================

Avant de proposer un achat ou une vente :

Vérifier :

- Structure
- Support
- Résistance
- Momentum
- Volume
- Contexte
- Confluence

Si plusieurs éléments se contredisent :

Décision = ATTENDRE

Ne jamais forcer un signal.

=========================
SCALPING
=========================

Créer automatiquement un plan Scalping.

Calculer :

Entrée

Stop Loss

TP1

TP2

Confiance

Durée estimée

=========================
DAY TRADING
=========================

Créer automatiquement un plan Day Trading.

Calculer :

Entrée

Stop Loss

TP1

TP2

TP3

Durée estimée

Confiance

=========================
SWING
=========================

Créer automatiquement un plan Swing Trading.

Calculer :

Entrée

Stop Loss

Objectif

Durée estimée

Confiance

=========================
GESTION DU TRADE
=========================

Donner également :

- Quand déplacer le Stop Loss au Break Even
- Quand prendre 50 % des bénéfices
- Quand laisser courir la position
- Quand annuler complètement le trade

=========================
EXPLICATION
=========================

Toujours expliquer clairement :

Pourquoi acheter

Pourquoi attendre

Pourquoi vendre

Pourquoi le signal est fiable

Pourquoi il est risqué

Le résumé doit être écrit comme le ferait un analyste professionnel.

"""

class VisionAnalysisError(Exception):
    pass


async def analyze_screenshot(
    image_bytes: bytes,
    mime_type: str,
    market_context: dict | None = None,
):

    api_key = os.environ.get("GEMINI_API_KEY", "")

    if not api_key:
        raise VisionAnalysisError(
            "Clé GEMINI_API_KEY manquante."
        )

    if market_context:

        context_text = (
            f"PAIR : {market_context.get('pair')}\n"
            f"PRIX : {market_context.get('price')}\n"
            f"RSI : {market_context.get('rsi')}\n"
            f"MACD : {market_context.get('macd')}\n"
            f"Signal MACD : {market_context.get('macd_signal')}\n"
            f"Histogramme MACD : {market_context.get('macd_hist')}\n"
            f"EMA20 : {market_context.get('ema20')}\n"
            f"EMA50 : {market_context.get('ema50')}\n"
            f"EMA100 : {market_context.get('ema100')}\n"
            f"EMA200 : {market_context.get('ema200')}\n"
            f"ATR : {market_context.get('atr')}\n"
            f"ADX : {market_context.get('adx')}\n"
            f"Support : {market_context.get('support')}\n"
            f"Résistance : {market_context.get('resistance')}\n"
            f"Volume relatif : {market_context.get('relative_volume')}\n"
            f"Tendance : {market_context.get('trend')}\n\n"

            "Ces données proviennent directement de Binance."

            " Elles doivent toujours être considérées comme prioritaires."
        )

    else:

        context_text = (
            "Aucune donnée Binance disponible."
        )

    prompt = PROMPT_TEMPLATE.replace(
    "{market_context}",
    context_text,
)

    image_b64 = base64.b64encode(
        image_bytes
    ).decode()

    payload = {

        "contents": [

            {

                "parts": [

                    {

                        "text": prompt

                    },

                    {

                        "inline_data": {

                            "mime_type": mime_type,

                            "data": image_b64

                        }

                    }

                ]

            }

        ],

        "generationConfig": {

            "temperature": 0.15,

            "topP": 0.9,

            "topK": 20,

            "responseMimeType": "application/json"

        }

    }

    try:

        async with httpx.AsyncClient(

            timeout=60

        ) as client:

            response = await client.post(

                GEMINI_URL,

                params={

                    "key": api_key

                },

                json=payload,

            )

    except httpx.RequestError:

        raise VisionAnalysisError(

            "Impossible de contacter Gemini."

        )

    if response.status_code != 200:

        raise VisionAnalysisError(

            f"Erreur Gemini ({response.status_code})"

        )

    try:

        data = response.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception:

        raise VisionAnalysisError(

            "Réponse Gemini invalide."

        )

    text = text.replace(

        "```json",

        ""

    )

    text = text.replace(

        "```",

        ""

    )

    text = text.strip()

    try:

        result = json.loads(text)

    except Exception:

        raise VisionAnalysisError(

            "JSON Gemini illisible."

        )

    result.setdefault(

        "generated_by",

        "Gemini"

    )

    result.setdefault(

        "generated_at",

        os.environ.get(

            "RENDER_GIT_COMMIT",

            "unknown"

        )

    )

    return result
