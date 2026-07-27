import os,base64
from openai import OpenAI
def analyze_image(content,mime,question):
    key=os.getenv("OPENAI_API_KEY","").strip()
    if not key: raise RuntimeError("OPENAI_API_KEY n'est pas configurée")
    b64=base64.b64encode(content).decode(); c=OpenAI(api_key=key)
    prompt="""Tu es Crypto Copilot IA. Analyse prudemment cette capture TradingView en français. Repère symbole, unité de temps, tendance, HH/HL/LH/LL, BOS, CHOCH, supports/résistances, Order Blocks, FVG, liquidité et bougie de confirmation. Sépare les faits visibles des hypothèses. Termine par VALIDÉ, À SURVEILLER ou AUCUN TRADE. Ne promets jamais un gain. Question: """+question
    r=c.responses.create(model="gpt-4.1-mini",input=[{"role":"user","content":[{"type":"input_text","text":prompt},{"type":"input_image","image_url":f"data:{mime};base64,{b64}"}]}]); return r.output_text
