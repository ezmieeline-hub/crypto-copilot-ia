import numpy as np, pandas as pd
def ema(s,n): return s.ewm(span=n,adjust=False).mean()
def sma(s,n): return s.rolling(n).mean()
def rsi(c,n=14):
    d=c.diff(); up=d.clip(lower=0).ewm(alpha=1/n,adjust=False).mean(); dn=(-d.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean(); rs=up/dn.replace(0,np.nan); return 100-100/(1+rs)
def atr(d,n=14):
    pc=d.close.shift(1); tr=pd.concat([(d.high-d.low).abs(),(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1); return tr.ewm(alpha=1/n,adjust=False).mean()
def adx(d,n=14):
    up=d.high.diff(); down=-d.low.diff(); plus=up.where((up>down)&(up>0),0.0); minus=down.where((down>up)&(down>0),0.0); a=atr(d,n); p=100*plus.ewm(alpha=1/n,adjust=False).mean()/a; m=100*minus.ewm(alpha=1/n,adjust=False).mean()/a; dx=100*(p-m).abs()/(p+m).replace(0,np.nan); return dx.ewm(alpha=1/n,adjust=False).mean(),p,m
def indicators(d):
    d=d.copy()
    for n in [9,20,50,100,200]: d[f"ema{n}"]=ema(d.close,n)
    d["sma200"]=sma(d.close,200); d["rsi"]=rsi(d.close); d["macd"]=ema(d.close,12)-ema(d.close,26); d["macd_signal"]=ema(d.macd,9); d["atr"]=atr(d); d["adx"],d["plus_di"],d["minus_di"]=adx(d); d["vol_ma20"]=d.volume.rolling(20).mean(); return d
def pivots(d,l=3,r=3):
    hs=[]; ls=[]
    for i in range(l,len(d)-r):
        if d.high.iloc[i]==d.high.iloc[i-l:i+r+1].max(): hs.append((i,float(d.high.iloc[i])))
        if d.low.iloc[i]==d.low.iloc[i-l:i+r+1].min(): ls.append((i,float(d.low.iloc[i])))
    return hs,ls
def structure(d):
    hs,ls=pivots(d); out=[]
    for arr,k in [(hs,"H"),(ls,"L")]:
        prev=None
        for i,p in arr[-8:]:
            lab=k if prev is None else (("HH" if p>prev else "LH") if k=="H" else ("HL" if p>prev else "LL")); out.append({"index":i,"price":p,"label":lab}); prev=p
    out.sort(key=lambda x:x["index"]); H=[x for x in out if x["label"] in ("HH","LH","H")]; L=[x for x in out if x["label"] in ("HL","LL","L")]; trend="neutre"
    if H and L and H[-1]["label"]=="HH" and L[-1]["label"]=="HL": trend="haussière"
    if H and L and H[-1]["label"]=="LH" and L[-1]["label"]=="LL": trend="baissière"
    return out[-10:],trend
def analyze(df):
    d=indicators(df).dropna(); x=d.iloc[-1]; labels,trend=structure(d); sup=float(d.tail(120).low.quantile(.08)); res=float(d.tail(120).high.quantile(.92)); lp=sp=0; good=[]; risk=[]
    if x.ema20>x.ema50>x.ema200: lp+=22; good.append("EMA 20 > 50 > 200")
    elif x.ema20<x.ema50<x.ema200: sp+=22; good.append("EMA 20 < 50 < 200")
    if trend=="haussière": lp+=20; good.append("Structure HH/HL")
    if trend=="baissière": sp+=20; good.append("Structure LH/LL")
    if x.macd>x.macd_signal: lp+=12
    else: sp+=12
    if 50<=x.rsi<=68: lp+=10
    elif 32<=x.rsi<50: sp+=10
    if x.adx>=25:
        if x.plus_di>x.minus_di: lp+=10
        else: sp+=10
    else: risk.append("ADX faible")
    if x.volume>x.vol_ma20:
        if x.close>x.open: lp+=8
        else: sp+=8
    else: risk.append("Volume inférieur à la moyenne")
    side="LONG" if lp>sp else "SHORT"; prev=d.iloc[-2]; confirmed=(x.close>x.open and x.close>prev.high and x.volume>x.vol_ma20) if side=="LONG" else (x.close<x.open and x.close<prev.low and x.volume>x.vol_ma20)
    score=min(96,max(20,max(lp,sp)+(10 if confirmed else 0)))
    if confirmed: good.append("Bougie de confirmation clôturée")
    else: risk.append("Bougie de confirmation non validée")
    price=float(x.close); av=float(x.atr)
    if side=="LONG": stop=min(price-1.5*av,sup*.997); rr=price-stop; tps=[price+rr,price+2*rr,price+3*rr]
    else: stop=max(price+1.5*av,res*1.003); rr=stop-price; tps=[price-rr,price-2*rr,price-3*rr]
    verdict="VALIDÉ" if confirmed and score>=75 else ("À SURVEILLER" if score>=60 else "AUCUN TRADE")
    return {"price":price,"trend":trend,"side":side,"score":int(score),"verdict":verdict,"confirmed":confirmed,"entry":price,"stop":stop,"tp1":tps[0],"tp2":tps[1],"tp3":tps[2],"support":sup,"resistance":res,"rsi":float(x.rsi),"adx":float(x.adx),"atr":av,"volume_ratio":float(x.volume/x.vol_ma20),"structure":labels,"reasons":good,"risks":risk}
