const $=id=>document.getElementById(id), message=t=>$('message').textContent=t;
let eurRate = null;
async function getEurRate(){
  if (eurRate) return eurRate;
  try {
    const r = await fetch('https://api.frankfurter.app/latest?from=USD&to=EUR');
    const d = await r.json();
    eurRate = d.rates.EUR;
  } catch(e) {
    eurRate = 0.92; // taux approximatif de secours si l'API est indisponible
  }
  return eurRate;
}

async function formatPrice(usdValue){
  if (usdValue === null || usdValue === undefined || usdValue === '') return '—';
  const currency = $('currencySelect').value;
  if (currency === 'USD') {
    return usdValue.toLocaleString('fr-FR', {maximumFractionDigits: 2}) + ' $';
  }
  const rate = await getEurRate();
  return (usdValue * rate).toLocaleString('fr-FR', {maximumFractionDigits: 2}) + ' €';
}
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
    loadJournal();
    loadDashboard();
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

    console.log(d);
    console.log(d.summary);
    console.log(d.trade);

    $('analysisCard').classList.remove('hidden');
    $('analysisTitle').textContent =
    `${d.summary.symbol} — ${d.trade.direction}`;

const hasSignal = d.trade.direction === 'ACHAT' || d.trade.direction === 'VENTE';
const priceStr = await formatPrice(d.market.price);
const entryStr = hasSignal ? await formatPrice(d.trade.entry) : '—';
const stopStr = hasSignal ? await formatPrice(d.trade.stop_loss) : '—';
const tpStr = hasSignal ? await formatPrice(d.trade.tp1) : '—';

$('analysisGrid').innerHTML = `
<div><span>Prix</span><b>${priceStr}</b></div>
<div><span>RSI</span><b>${d.market.rsi ?? '—'}</b></div>
<div><span>MACD</span><b>${d.market.macd ?? '—'}</b></div>
<div><span>Tendance</span><b>${d.analysis.decision.trend ?? '—'}</b></div>
<div><span>Confiance</span><b>${d.analysis.decision.confidence ?? 0}%</b></div>
<div><span>Entrée</span><b>${entryStr}</b></div>
<div><span>Stop Loss</span><b>${stopStr}</b></div>
<div><span>Take Profit</span><b>${tpStr}</b></div>
`;

if (!hasSignal) {
  message('Aucun signal confirmé — pas de plan de trade tant que la décision reste ATTENDRE.');
}

    const sq = d.analysis.setup_quality;
    if (sq) {
      const starsFull = '⭐'.repeat(sq.stars);
      const starsEmpty = '☆'.repeat(5 - sq.stars);
      const strengthsHtml = sq.strengths.map(s => `<li class="ok">✔ ${s}</li>`).join('');
      const weaknessesHtml = sq.weaknesses.map(w => `<li class="ko">✖ ${w}</li>`).join('');


const reasonsText = (d.analysis.decision.reasons || []).join(' ');

$('setupQuality').innerHTML = `
  ${reasonsText ? `<h3>Pourquoi ?</h3><p class="why-text">${reasonsText}</p>` : ''}
  <h3>Qualité du setup</h3>
  <div class="quality-score">
    <span class="quality-stars">${starsFull}${starsEmpty}</span>
    <span class="quality-number">${sq.score}/100</span>
  </div>
  <ul class="quality-checklist">${strengthsHtml}</ul>
  ${weaknessesHtml ? `<h3>Faiblesse${sq.weaknesses.length > 1 ? 's' : ''}</h3><ul class="quality-checklist">${weaknessesHtml}</ul>` : ''}
`;
    } else {
      $('setupQuality').innerHTML = '';
    }
try {
  const cmp = await api(`/api/compare/${encodeURIComponent(s)}`);
  if (cmp.available) {
    const deltaSign = cmp.delta_confidence > 0 ? '+' : '';
    const changesHtml = cmp.changes.map(c => `<li>${c}</li>`).join('');
    $('compareBlock').innerHTML = `
      <h3>Aujourd'hui vs précédente analyse</h3>
      <div class="quality-score">
        <span class="quality-number">${cmp.confidence_today}%</span>
        <span>(précédente : ${cmp.confidence_previous}%, ${deltaSign}${cmp.delta_confidence} pts)</span>
      </div>
      ${changesHtml ? `<ul class="quality-checklist">${changesHtml}</ul>` : ''}
    `;
  } else {
    $('compareBlock').innerHTML = `<p>${cmp.message}</p>`;
  }
} catch (e) {
  $('compareBlock').innerHTML = '';
}
const news = d.analysis.news;
if (news) {
  const headlinesHtml = (news.headlines || [])
    .map(n => `<li><a href="${n.url}" target="_blank" rel="noopener">${n.title}</a> <small>(${n.source || '—'})</small></li>`)
    .join('');

  const calendarHtml = (news.calendar || [])
    .map(e => `<li>${e.title} — prévision : ${e.forecast ?? '—'} (précédent : ${e.previous ?? '—'})</li>`)
    .join('');

  $('newsBlock').innerHTML = `
    ${headlinesHtml ? `<h3>Actualités récentes</h3><ul class="quality-checklist">${headlinesHtml}</ul>` : ''}
    ${calendarHtml ? `<h3>Annonces macro à fort impact (USD)</h3><ul class="quality-checklist">${calendarHtml}</ul>` : ''}
    ${!headlinesHtml && !calendarHtml ? '<p>Aucune actualité disponible pour le moment.</p>' : ''}
  `;
} else {
  $('newsBlock').innerHTML = '';
}
$('journalBlock').innerHTML = `
  <h3>Trade pris ?</h3>
  <div class="analysis-form">
    <button id="journalYes" class="secondary">Oui</button>
    <button id="journalNo" class="secondary">Non</button>
  </div>
  <div id="journalForm" class="hidden">
    <input id="journalResult" type="number" step="any" placeholder="Résultat (%)">
    <input id="journalComment" placeholder="Commentaire (ex: sorti trop tôt)">
    <button id="journalSave">Enregistrer</button>
  </div>
  <p id="journalMsg"></p>
`;

$('journalNo').onclick = async () => {
  try {
    await api(`/api/journal/${d.analysis_id}`, {method: 'POST', body: JSON.stringify({taken: false})});
    $('journalMsg').textContent = 'Enregistré : trade non pris.';
  } catch (e) { $('journalMsg').textContent = e.message; }
};

$('journalYes').onclick = () => {
  $('journalForm').classList.remove('hidden');
};

$('journalSave').onclick = async () => {
  const result_percent = parseFloat($('journalResult').value);
  const comment = $('journalComment').value;
  try {
    await api(`/api/journal/${d.analysis_id}`, {
      method: 'POST',
      body: JSON.stringify({
        taken: true,
        result_percent: isNaN(result_percent) ? null : result_percent,
        comment,
      }),
    });
    $('journalMsg').textContent = 'Trade enregistré dans le journal ✅';
    $('journalForm').classList.add('hidden');
  } catch (e) { $('journalMsg').textContent = e.message; }
};
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
$('simBtn').onclick = () => {
  const entry = parseFloat($('simEntry').value);
  const stop = parseFloat($('simStop').value);
  const tp = parseFloat($('simTp').value);

  if (!entry || !stop || !tp) {
    $('simResult').innerHTML = '<p class="tv-error">Remplissez les 3 champs.</p>';
    return;
  }

  const risk = Math.abs(entry - stop);
  const reward = Math.abs(tp - entry);

  if (risk === 0) {
    $('simResult').innerHTML = '<p class="tv-error">Le stop ne peut pas être égal à l\'entrée.</p>';
    return;
  }

  const lossPct = ((stop - entry) / entry) * 100;
  const gainPct = ((tp - entry) / entry) * 100;
  const rr = (reward / risk).toFixed(2);

  $('simResult').innerHTML = `
    <div class="plan">
      <div><span>Perte maximale</span><b class="neg">${lossPct.toFixed(2)}%</b></div>
      <div><span>Gain potentiel</span><b class="pos">${gainPct > 0 ? '+' : ''}${gainPct.toFixed(2)}%</b></div>
      <div><span>Risk / Reward</span><b>${rr}</b></div>
    </div>
  `;
};
async function loadAlerts(){
  try{
    const rows=await api('/api/alerts');
    $('alerts').innerHTML=rows.length?rows.map(a=>`<div class="history-row"><b>${a.symbol}</b><span>${a.direction==='above'?'Au-dessus':'En dessous'}</span><span>${a.target_price}</span></div>`).join(''):'Aucune alerte.';
  }catch(e){}
}
function decisionCorrecte(signal, resultPercent){
  if (resultPercent == null) return null;
  if (signal === 'ACHAT') return resultPercent > 0;
  if (signal === 'VENTE') return resultPercent < 0;
  return null;
}

async function loadJournal(){
  try{
    const rows = await api('/api/journal');
    $('journalList').innerHTML = rows.length ? rows.map(r => {
      const correct = decisionCorrecte(r.signal, r.result_percent);
      const correctBadge = correct === null ? '' :
        correct ? '<span class="pos">✅ Décision correcte</span>' : '<span class="neg">❌ Décision incorrecte</span>';
      return `
        <div class="history-row">
          <b>${r.symbol}</b>
          <span>IA : ${r.signal ?? '—'}${r.confidence != null ? ' (' + r.confidence + '%)' : ''}</span>
          <span>${r.result_percent != null ? (r.result_percent > 0 ? '+' : '') + r.result_percent + '%' : '—'}</span>
          <small>${correctBadge || r.comment || '—'}</small>
        </div>
      `;
    }).join('') : 'Aucune entrée.';
  }catch(e){ $('journalList').textContent = e.message; }
}
async function loadDashboard(){
  try{
    const d = await api('/api/dashboard');
    $('dashboardGrid').innerHTML = `
      <div><span>📈 Analyses totales</span><b>${d.total_analyses}</b></div>
      <div><span>🎯 Taux de réussite</span><b>${d.success_rate}%</b></div>
      <div><span>💰 Gain théorique cumulé</span><b>${d.cumulative_gain > 0 ? '+' : ''}${d.cumulative_gain}%</b></div>
      <div><span>📊 Crypto la plus rentable</span><b>${d.best_symbol ?? '—'}</b></div>
      <div><span>📉 Crypto la moins fiable</span><b>${d.worst_symbol ?? '—'}</b></div>
      <div><span>⭐ Score moyen des setups</span><b>${d.avg_score}</b></div>
      <div><span>🔥 Meilleur mois</span><b>${d.best_month ?? '—'}</b></div>
      <div><span>📅 Analyses / jour (moyenne)</span><b>${d.avg_analyses_per_day}</b></div>
    `;
  }catch(e){ $('dashboardGrid').textContent = e.message; }
}
$('dashboardBtn').onclick = loadDashboard;
$('journalBtn').onclick = loadJournal;
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

    const fmtEur = (v) => formatPrice(v);

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
          <div><span>Entrée</span><b>${await fmtEur(d.entry)}</b></div>
          <div><span>Take profit</span><b>${await fmtEur(d.take_profit)}</b></div>
          <div><span>Stop-loss</span><b>${await fmtEur(d.stop_loss)}</b></div>
        </div>
        <div class="plan">
          <div><span>Support</span><b>${await fmtEur(d.support)}</b></div>
          <div><span>Résistance</span><b>${await fmtEur(d.resistance)}</b></div>
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
$('morningNoteBtn').onclick = async () => {
    const s = $('symbol').value.trim().toUpperCase();
    if (!s) return message('Saisissez une crypto.');
    message('Génération du Morning Note...');
    
    try {
        const mn = await api(`/morning-note/${encodeURIComponent(s)}`);
        
        // Bias color
        const biasColor = mn.bias === 'BULL' ? '#22c55e' 
                        : mn.bias === 'BEAR' ? '#ef4444' 
                        : '#eab308';
        
        // Barre visuelle BULL/BASE/BEAR
        const bull = mn.bias_scores?.bull || 0;
        const base = mn.bias_scores?.base || 0;
        const bear = mn.bias_scores?.bear || 0;
        
        // Overnight
        const overnightHtml = (mn.overnight_developments || []).map(dev => `
            <div class="mn-item">
                <span class="mn-cat">${dev.category}</span>
                <div class="mn-title">${dev.title}</div>
                <div class="mn-take">📝 ${dev.take}</div>
            </div>
        `).join('');
        
        // Événements
        const eventsHtml = (mn.key_events_today || []).map(ev => `
            <div class="mn-event">
                <span class="mn-time">${ev.time}</span> — ${ev.title}
                <em>(${ev.source})</em>
            </div>
        `).join('');
        
        // Trade ideas
        const ideasHtml = (mn.trade_ideas || []).map(idea => {
            const color = idea.direction === 'LONG' ? '#22c55e' 
                        : idea.direction === 'SHORT' ? '#ef4444' 
                        : '#eab308';
            return `
            <div class="mn-idea" style="border-left-color:${color}">
                <strong style="color:${color}">${idea.direction} ${idea.symbol}</strong>
                <p>${idea.thesis}</p>
                <div class="mn-catalyst">🎯 ${idea.catalyst}</div>
                <div class="mn-risk">⚠️ ${idea.risk}</div>
            </div>
            `;
        }).join('');
        
        // Top Call
        const topCallHtml = mn.top_call?.body 
            ? `<div class="mn-topcall"><strong>🔔 Top Call</strong><p>${mn.top_call.body}</p></div>` 
            : '';
        
        // Rendu
        $('morningNoteResult').innerHTML = `
            <div class="mn-card">
                <h3>📰 Morning Note — ${mn.symbol} <span>${mn.date}</span></h3>
                
                <div class="mn-bias-bar">
                    <div class="mn-bar-track">
                        <div class="mn-bar-bull" style="width:${bull}%"></div>
                        <div class="mn-bar-base" style="width:${base}%"></div>
                        <div class="mn-bar-bear" style="width:${bear}%"></div>
                    </div>
                    <span class="mn-bias-label" style="color:${biasColor}">${mn.bias}</span>
                </div>
                
                ${topCallHtml}
                
                ${overnightHtml ? `<h4>🌙 Développements Overnight</h4>${overnightHtml}` : ''}
                ${eventsHtml ? `<h4>📅 Événements Clés</h4>${eventsHtml}` : ''}
                ${ideasHtml ? `<h4>💡 Trade Ideas</h4>${ideasHtml}` : ''}
            </div>
        `;
        
        message('Morning Note généré.');
    } catch (e) {
        message(e.message);
    }
};
