const $=id=>document.getElementById(id), message=t=>$('message').textContent=t;

async function api(url,o={}){
  const r=await fetch(url,{headers:{'Content-Type':'application/json',...(o.headers||{})},...o});
  const d=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(d.detail||'Erreur serveur');
  return d;
}

async function refreshSession(){
  try{
    const u=await api('/api/me');
    $('authCard').classList.add('hidden');
    $('dashboard').classList.remove('hidden');
    $('welcome').textContent=`Bienvenue ${u.name} 👋`;
    loadHistory();
    loadAlerts();
  }catch{
    $('authCard').classList.remove('hidden');
    $('dashboard').classList.add('hidden');
  }
}

$('registerBtn').onclick=async()=>{
  try{
    await api('/api/register',{method:'POST',body:JSON.stringify({name:$('registerName').value,email:$('registerEmail').value,password:$('registerPassword').value})});
    message('Compte créé. Vous pouvez vous connecter.');
  }catch(e){message(e.message)}
};

$('loginBtn').onclick=async()=>{
  try{
    await api('/api/login',{method:'POST',body:JSON.stringify({email:$('loginEmail').value,password:$('loginPassword').value})});
    message('');
    refreshSession();
  }catch(e){message(e.message)}
};

$('logoutBtn').onclick=async()=>{await api('/api/logout',{method:'POST'});refreshSession()};

$('analyzeBtn').onclick=async()=>{
  const s=$('symbol').value.trim().toUpperCase();
  if(!s) return message('Saisissez une crypto.');
  message('Analyse en cours...');
  try{
    const d = await api('/api/analyze/' + encodeURIComponent(s));

console.log("ANALYSE :", d);
    $('analysisCard').classList.remove('hidden');
    $('analysisTitle').textContent =
    `${d.summary.symbol} — ${d.trade.direction}`;

$('analysisGrid').innerHTML = `
<div><span>Prix</span><b>${d.market.price.toLocaleString('fr-FR')} $</b></div>
<div><span>RSI</span><b>${d.market.rsi ?? '—'}</b></div>
<div><span>MACD</span><b>${d.market.macd ?? '—'}</b></div>
<div><span>Tendance</span><b>${d.analysis.decision.trend ?? '—'}</b></div>
<div><span>Confiance</span><b>${d.analysis.decision.confidence ?? 0}%</b></div>
<div><span>Entrée</span><b>${d.trade.entry ?? '—'}</b></div>
<div><span>Stop Loss</span><b>${d.trade.stop_loss ?? '—'}</b></div>
<div><span>Take Profit</span><b>${d.trade.tp1 ?? '—'}</b></div>
`;
    message('Analyse terminée.');
    loadHistory();
  }catch(e){message(e.message)}
};

async function loadHistory(){
  try{
    const rows=await api('/api/history');
    $('history').innerHTML=rows.length?rows.map(r=>`<div class="history-row"><b>${r.symbol}</b><span>${r.signal}</span><span>${r.confidence}%</span><small>${r.created_at}</small></div>`).join(''):'Aucune analyse.';
  }catch(e){$('history').textContent=e.message}
}
$('historyBtn').onclick=loadHistory;

$('alertBtn').onclick=async()=>{
  try{
    await api(`/api/alerts/${encodeURIComponent($('alertSymbol').value)}/${$('alertDirection').value}/${$('alertPrice').value}`,{method:'POST'});
    message('Alerte créée.');
    loadAlerts();
  }catch(e){message(e.message)}
};

async function loadAlerts(){
  try{
    const rows=await api('/api/alerts');
    $('alerts').innerHTML=rows.length?rows.map(a=>`<div class="history-row"><b>${a.symbol}</b><span>${a.direction==='above'?'Au-dessus':'En dessous'}</span><span>${a.target_price}</span></div>`).join(''):'Aucune alerte.';
  }catch(e){}
}

function badgeClass(signal){
  if(signal==='ACHAT') return 'achat';
  if(signal==='VENTE') return 'vente';
  return 'attendre';
}

function fmt(v){
  return (v===null||v===undefined||v==='')?'—':v;
}

$('tvBtn').onclick=async()=>{
  const f=$('tvFile').files[0];
  const sym=$('tvSymbol').value.trim().toUpperCase();
  if(!f){$('tvResult').innerHTML='<p class="tv-error">Sélectionnez une image.</p>';return}
  const form=new FormData();
  form.append('file',f);
  form.append('symbol',sym);
  $('tvResult').innerHTML='<p>Analyse de la capture en cours (lecture des bougies, indicateurs, figures chartistes)...</p>';
  try{
    const r=await fetch('/api/tradingview/analyze',{method:'POST',body:form});
    const d=await r.json();
    if(!r.ok) throw new Error(d.detail||'Erreur');

    const patterns=(d.candlestick_patterns||[]).map(p=>`<li>${p}</li>`).join('');

    $('tvResult').innerHTML=`
      <div class="report">
        <span class="badge ${badgeClass(d.signal)}">${d.signal} — ${d.confidence}% de confiance</span>
        <p class="justification">${d.justification||''}</p>
        <div>
          <h3>Symbole / Unité de temps détectés</h3>
          <p>${fmt(d.symbol_detected)} — ${fmt(d.timeframe_detected)}</p>
        </div>
        ${patterns?`<div><h3>Figures chartistes détectées</h3><ul class="patterns">${patterns}</ul></div>`:''}
        <div>
          <h3>Indicateurs visibles</h3>
          <p>${fmt(d.visible_indicators)}</p>
        </div>
        <div class="plan">
          <div><span>Entrée</span><b>${fmt(d.entry)}</b></div>
          <div><span>Take profit</span><b>${fmt(d.take_profit)}</b></div>
          <div><span>Stop-loss</span><b>${fmt(d.stop_loss)}</b></div>
        </div>
        <div class="plan">
          <div><span>Support</span><b>${fmt(d.support)}</b></div>
          <div><span>Résistance</span><b>${fmt(d.resistance)}</b></div>
          <div><span>Tendance</span><b>${fmt(d.trend)}</b></div>
        </div>
      </div>`;
    loadHistory();
  }catch(e){
    $('tvResult').innerHTML=`<p class="tv-error">${e.message}</p>`;
  }
};

if('serviceWorker' in navigator) navigator.serviceWorker.register('/static/sw.js').catch(()=>{});

refreshSession();
