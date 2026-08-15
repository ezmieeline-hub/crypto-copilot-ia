const $=id=>document.getElementById(id), message=t=>$('message').textContent=t;
let eurRate = null;
async function getEurRate(){
 if (eurRate) return eurRate;
 try {
 const r = await fetch('https://api.frankfurter.app/latest?from=USD&to=EUR');
 const d = await r.json();
 eurRate = d.rates.EUR;
 } catch(e) {
 eurRate = 0.92;
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

async function renderAnalysisResult(d) {
 $('analysisCard').classList.remove('hidden');
 $('analysisTitle').textContent =
 `${d.summary.symbol} — ${d.trade.direction}`;

const hasSignal = d.trade.direction === 'ACHAT' || d.trade.direction === 'VENTE';
const priceStr = await formatPrice(d.market.price);
const entryStr = hasSignal ? await formatPrice(d.trade.entry) : '—';
const stopStr = hasSignal ? await formatPrice(d.trade.stop_loss) : '—';
const tpStr = hasSignal ? await formatPrice(d.trade.tp1) : '—';

$('analysisGrid').innerHTML = `
<div class="grid-item"><div class="label">Prix</div><div class="value">${priceStr}</div></div>
<div class="grid-item"><div class="label">RSI</div><div class="value">${d.market.rsi ?? '—'}</div></div>
<div class="grid-item"><div class="label">MACD</div><div class="value">${d.market.macd ?? '—'}</div></div>
<div class="grid-item"><div class="label">Tendance</div><div class="value">${d.analysis.decision.trend ?? '—'}</div></div>
<div class="grid-item"><div class="label">Confiance</div><div class="value">${d.analysis.decision.confidence ?? 0}%</div></div>
<div class="grid-item"><div class="label">Entrée</div><div class="value">${entryStr}</div></div>
<div class="grid-item"><div class="label">Stop Loss</div><div class="value">${stopStr}</div></div>
<div class="grid-item"><div class="label">Take Profit</div><div class="value">${tpStr}</div></div>
`;

if (!hasSignal) {
 message('Aucun signal confirmé — pas de plan de trade tant que la décision reste ATTENDRE.');
}

 const sq = d.analysis.setup_quality;
 if (sq) {
 const starsFull = '⭐'.repeat(sq.stars);
 const starsEmpty = '☆'.repeat(5 - sq.stars);
 const strengthsHtml = sq.strengths.map(s => `✔ ${s}<br>`).join('');
 const weaknessesHtml = sq.weaknesses.map(w => `✖ ${w}<br>`).join('');

const reasonsText = (d.analysis.decision.reasons || []).join(' ');

$('setupQuality').innerHTML = `
 ${reasonsText ? `<div class="info-box"><h4>Pourquoi ?</h4><p>${reasonsText}</p></div>` : ''}

<div class="info-box">
<h4>Qualité du setup</h4>
<p>${starsFull}${starsEmpty} <strong>${sq.score}/100</strong></p>
${strengthsHtml}
 ${weaknessesHtml ? `<p style="color:#ef4444;margin-top:8px;">${weaknessesHtml}</p>` : ''}
</div>
`;
 } else {
 $('setupQuality').innerHTML = '';
 }
try {
 const cmp = await api(`/api/compare/${encodeURIComponent(d.summary.symbol || d.symbol)}`);
 if (cmp.available) {
 const deltaSign = cmp.delta_confidence > 0 ? '+' : '';
 const changesHtml = cmp.changes.map(c => `<li>${c}</li>`).join('');
 $('compareBlock').innerHTML = `
<div class="info-box">
<h4>Aujourd'hui vs précédente analyse</h4>
<p><strong>${cmp.confidence_today}%</strong> (précédente : ${cmp.confidence_previous}%, ${deltaSign}${cmp.delta_confidence} pts)</p>
 ${changesHtml ? `<ul>${changesHtml}</ul>` : ''}
 </div>
 `;
 } else {
 $('compareBlock').innerHTML = `
<div class="info-box">
<p>${cmp.message}</p>
</div>
`;
 }
} catch (e) {
 $('compareBlock').innerHTML = '';
}
const news = d.analysis.news;
if (news) {
 const headlinesHtml = (news.headlines || [])
 .map(n => `<p><a href="${n.url || '#'}" target="_blank">${n.title}</a> <em>(${n.source || '—'})</em></p>`)
 .join('');

 const calendarHtml = (news.calendar || [])
 .map(e => `<p>${e.title} — prévision : ${e.forecast ?? '—'} (précédent : ${e.previous ?? '—'})</p>`)
 .join('');

 $('newsBlock').innerHTML = `
 ${headlinesHtml ? `<div class="info-box"><h4>Actualités récentes</h4>${headlinesHtml}</div>` : ''}
 ${calendarHtml ? `<div class="info-box"><h4>Annonces macro à fort impact (USD)</h4>${calendarHtml}</div>` : ''}
 ${!headlinesHtml && !calendarHtml ? '<div class="info-box"><p>Aucune actualité disponible pour le moment.</p></div>' : ''}
 `;
} else {
 $('newsBlock').innerHTML = '';
}

// MORNING NOTE (affichage dans l'analyse classique)
const mn = d.morning_note;
if (mn) {
 const biasColor = mn.bias === 'BULL' ? '#22c55e' : mn.bias === 'BEAR' ? '#ef4444' : '#eab308';
 const bullBar = mn.bias_scores?.bull || 0;
 const baseBar = mn.bias_scores?.base || 0;
 const bearBar = mn.bias_scores?.bear || 0;

 let overnightHtml = '';
 if (mn.overnight_developments) {
 overnightHtml = mn.overnight_developments.map(dev => `
 <div style="margin:6px 0;padding:8px;background:#1e293b;border-radius:6px;">
 <strong style="color:#94a3b8;font-size:11px;text-transform:uppercase;">${dev.category}</strong><br>
 <span style="color:#f8fafc;">${dev.title}</span><br>
 <span style="color:#cbd5e1;font-size:13px;">📝 ${dev.take}</span>
 </div>
 `).join('');
 }

 let eventsHtml = '';
 if (mn.key_events_today) {
 eventsHtml = mn.key_events_today.map(ev => `
 <div style="margin:4px 0;font-size:13px;color:#cbd5e1;">
 <span style="color:#64748b;">${ev.time}</span> — ${ev.title} <em style="color:#475569;">(${ev.source})</em>
 </div>
 `).join('');
 }

 let ideasHtml = '';
 if (mn.trade_ideas) {
 ideasHtml = mn.trade_ideas.map(idea => {
 const color = idea.direction === 'LONG' ? '#22c55e' : idea.direction === 'SHORT' ? '#ef4444' : '#eab308';
 return `
 <div style="margin:6px 0;padding:10px;border-left:3px solid ${color};background:#1e293b;border-radius:0 6px 6px 0;">
 <strong style="color:${color};">
 ${idea.direction} ${idea.symbol}
 </strong><br>
 <span style="color:#f8fafc;font-size:13px;">${idea.thesis}</span><br>
 <span style="color:#94a3b8;font-size:12px;">🎯 ${idea.catalyst}</span><br>
 <span style="color:#f87171;font-size:12px;">⚠️ ${idea.risk}</span>
 </div>
 `;
 }).join('');
 }

 const topCallHtml = mn.top_call?.body
 ? `<div style="margin-bottom:12px;padding:12px;background:#1e293b;border-radius:8px;border-left:3px solid #3b82f6;"><strong style="color:#60a5fa;">🔔 Top Call</strong><p style="margin:6px 0 0 0;color:#cbd5e1;font-size:14px;line-height:1.5;">${mn.top_call.body}</p></div>`
 : '';

 const ind = mn.indicators || {};
 const indicatorsHtml = `
 <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px;">
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">Prix</span><strong style="font-size:14px;color:#f8fafc;">${ind.price ?? '—'}</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">24h</span><strong style="font-size:14px;color:${(ind.change_24h_pct||0)>0?'#22c55e':'#ef4444'}">${ind.change_24h_pct ?? '—'}%</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">RSI</span><strong style="font-size:14px;color:#f8fafc;">${ind.rsi_1h ?? '—'}</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">Vol</span><strong style="font-size:14px;color:#f8fafc;">${ind.volatility_1h ?? '—'}%</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">BTC Dom</span><strong style="font-size:14px;color:#f8fafc;">${ind.btc_dominance ?? '—'}%</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">F&G</span><strong style="font-size:14px;color:#f8fafc;">${ind.fear_greed_value ?? '—'}</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">Funding</span><strong style="font-size:14px;color:#f8fafc;">${ind.funding_rate ? (ind.funding_rate*100).toFixed(4)+'%' : '—'}</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">Bid/Ask</span><strong style="font-size:14px;color:#f8fafc;">${ind.orderbook_bid_ask_ratio ?? '—'}</strong></div>
 </div>
 `;

 $('morningNoteBlock').innerHTML = `
 <div style="background:#0f172a;border:1px solid #334155;border-radius:12px;padding:16px;margin-top:16px;color:#f8fafc;">
 <h3 style="margin:0 0 12px 0;font-size:16px;">📰 Morning Note — ${mn.symbol} <span style="font-size:12px;color:#64748b;">${mn.date}</span></h3>
 <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
 <div style="flex:1;height:8px;background:#1e293b;border-radius:4px;overflow:hidden;display:flex;">
 <div style="width:${bullBar}%;background:#22c55e;"></div>
 <div style="width:${baseBar}%;background:#eab308;"></div>
 <div style="width:${bearBar}%;background:#ef4444;"></div>
 </div>
 <span style="font-weight:bold;color:${biasColor};font-size:14px;white-space:nowrap;">${mn.bias}</span>
 </div>
 ${indicatorsHtml}
 ${topCallHtml}
 ${overnightHtml ? `<h4 style="margin:16px 0 8px 0;font-size:13px;color:#94a3b8;text-transform:uppercase;">🌙 Développements Overnight</h4>${overnightHtml}` : ''}
 ${eventsHtml ? `<h4 style="margin:16px 0 8px 0;font-size:13px;color:#94a3b8;text-transform:uppercase;">📅 Événements Clés</h4>${eventsHtml}` : ''}
 ${ideasHtml ? `<h4 style="margin:16px 0 8px 0;font-size:13px;color:#94a3b8;text-transform:uppercase;">💡 Trade Ideas</h4>${ideasHtml}` : ''}
 </div>
 `;
} else {
 $('morningNoteBlock').innerHTML = '';
}
$('journalBlock').innerHTML = `
<div class="info-box">
<h4>Trade pris ?</h4>
<div class="row">
<button id="journalYes" class="btn-primary">✅ Oui</button>
<button id="journalNo" class="secondary">❌ Non</button>
</div>
<div id="journalForm" class="hidden" style="margin-top:12px;">
<input id="journalResult" type="number" step="0.01" placeholder="Résultat % (ex: -2.5 ou +5.3)">
<textarea id="journalComment" placeholder="Commentaire..."></textarea>
<button id="journalSave" class="btn-primary">Enregistrer</button>
</div>
<p id="journalMsg" style="margin-top:8px;color:#94a3b8;"></p>
</div>
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
}

$('analyzeBtn').onclick=async()=>{
 const s=$('symbol').value.trim().toUpperCase();
 if(!s) return message('Saisissez une crypto.');
 message('Analyse en cours...');
 try{
  const d = await api('/api/analyze/' + encodeURIComponent(s));
  console.log("ANALYSE :", d);
  await renderAnalysisResult(d);
  message('Analyse terminée.');
  loadHistory();
 }catch(e){message(e.message)}
};

async function loadHistory(){
 try{
  const rows=await api('/api/history');
  if(!rows.length){
   $('history').innerHTML='Aucune analyse.';
   return;
  }
  $('history').innerHTML=rows.map(r=>`<div class="history-row" style="cursor:pointer;" onclick="loadAnalysisById(${r.id})" title="Cliquer pour revoir l'analyse"><b>${r.symbol}</b><span>${r.signal}</span><span>${r.confidence}%</span><small>${r.created_at}</small></div>`).join('');
 }catch(e){$('history').textContent=e.message}
}

async function loadAnalysisById(id){
 window.loadAnalysisById = loadAnalysisById;
 message("Chargement...");
 try{
  const d = await api('/api/history/' + id);
  await renderAnalysisResult(d);
  message("Analyse chargée depuis l'historique.");
 }catch(e){message(e.message)}
}

$('clearHistoryBtn').onclick=async()=>{
 if(!confirm("Supprimer tout l'historique ? Cette action est irréversible.")) return;
 try{
  await api('/api/history',{method:'DELETE'});
  $('history').innerHTML='Aucune analyse.';
  message("Historique supprimé.");
 }catch(e){message(e.message)}
};
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
 $('simResult').innerHTML = '<div class="info-box"><p>Remplissez les 3 champs.</p></div>';
 return;
 }

 const risk = Math.abs(entry - stop);
 const reward = Math.abs(tp - entry);

 if (risk === 0) {
 $('simResult').innerHTML = '<div class="info-box"><p>Le stop ne peut pas être égal à l\'entrée.</p></div>';
 return;
 }

 const lossPct = ((stop - entry) / entry) * 100;
 const gainPct = ((tp - entry) / entry) * 100;
 const rr = (reward / risk).toFixed(2);

 $('simResult').innerHTML = `
<div class="grid-3">
<div class="grid-item"><div class="label">Perte maximale</div><div class="value">${lossPct.toFixed(2)}%</div></div>
<div class="grid-item"><div class="label">Gain potentiel</div><div class="value">${gainPct > 0 ? '+' : ''}${gainPct.toFixed(2)}%</div></div>
<div class="grid-item"><div class="label">Risk / Reward</div><div class="value">${rr}</div></div>
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
 correct ? '<span style="color:#22c55e;">✅ Décision correcte</span>' : '<span style="color:#ef4444;">❌ Décision incorrecte</span>';
 return `<div class="history-row"><b>${r.symbol}</b><span>IA : ${r.signal ?? '—'}${r.confidence != null ? ' (' + r.confidence + '%)' : ''}</span><span>${r.result_percent != null ? (r.result_percent > 0 ? '+' : '') + r.result_percent + '%' : '—'}</span><small>${correctBadge || r.comment || '—'}</small></div>`;
 }).join('') : 'Aucune entrée.';
 }catch(e){ $('journalList').textContent = e.message; }
}
async function loadDashboard(){
 try{
 const d = await api('/api/dashboard');
 $('dashboardGrid').innerHTML = `
<div class="grid-3">
<div class="grid-item"><div class="label">📈 Analyses totales</div><div class="value">${d.total_analyses}</div></div>
<div class="grid-item"><div class="label">🎯 Taux de réussite</div><div class="value">${d.success_rate}%</div></div>
<div class="grid-item"><div class="label">💰 Gain théorique cumulé</div><div class="value">${d.cumulative_gain > 0 ? '+' : ''}${d.cumulative_gain}%</div></div>
<div class="grid-item"><div class="label">📊 Crypto la plus rentable</div><div class="value">${d.best_symbol ?? '—'}</div></div>
<div class="grid-item"><div class="label">📉 Crypto la moins fiable</div><div class="value">${d.worst_symbol ?? '—'}</div></div>
<div class="grid-item"><div class="label">⭐ Score moyen des setups</div><div class="value">${d.avg_score}</div></div>
<div class="grid-item"><div class="label">🔥 Meilleur mois</div><div class="value">${d.best_month ?? '—'}</div></div>
<div class="grid-item"><div class="label">📅 Analyses / jour (moyenne)</div><div class="value">${d.avg_analyses_per_day}</div></div>
</div>
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
 if(!f){$('tvResult').innerHTML='<div class="info-box"><p>Sélectionnez une image.</p></div>';return}
 const form=new FormData();
 form.append('file',f);
 form.append('symbol',sym);
 $('tvResult').innerHTML='<div class="info-box"><p>Analyse de la capture en cours (lecture des bougies, indicateurs, figures chartistes)...</p></div>';
 try{
 const r=await fetch('/api/tradingview/analyze',{method:'POST',body:form});
 const d=await r.json();
 if(!r.ok) throw new Error(d.detail||'Erreur');

 const fmtEur = (v) => formatPrice(v);

 const patterns=(d.candlestick_patterns||[]).map(p=>`<span class="badge">${p}</span>`).join('');

 $('tvResult').innerHTML=`
<div class="info-box">
<h3 class="${badgeClass(d.signal)}">${d.signal} — ${d.confidence}% de confiance</h3>
<p>${d.justification||''}</p>
</div>

<div class="info-box">
<h4>Symbole / Unité de temps détectés</h4>
<p>${fmt(d.symbol_detected)} — ${fmt(d.timeframe_detected)}</p>
</div>

${patterns?`<div class="info-box"><h4>Figures chartistes détectées</h4><div class="row">${patterns}</div></div>`:''}

<div class="info-box">
<h4>Indicateurs visibles</h4>
<p>${fmt(d.visible_indicators)}</p>
</div>

<div class="grid-3">
<div class="grid-item"><div class="label">Entrée</div><div class="value">${await fmtEur(d.entry)}</div></div>
<div class="grid-item"><div class="label">Take profit</div><div class="value">${await fmtEur(d.take_profit)}</div></div>
<div class="grid-item"><div class="label">Stop-loss</div><div class="value">${await fmtEur(d.stop_loss)}</div></div>
<div class="grid-item"><div class="label">Support</div><div class="value">${await fmtEur(d.support)}</div></div>
<div class="grid-item"><div class="label">Résistance</div><div class="value">${await fmtEur(d.resistance)}</div></div>
<div class="grid-item"><div class="label">Tendance</div><div class="value">${fmt(d.trend)}</div></div>
</div>
`;

 // Morning Note (TradingView)
 const mn = d.morning_note;
 if (mn) {
 const biasColor = mn.bias === 'BULL' ? '#22c55e' : mn.bias === 'BEAR' ? '#ef4444' : '#eab308';
 const bull = mn.bias_scores?.bull || 0;
 const base = mn.bias_scores?.base || 0;
 const bear = mn.bias_scores?.bear || 0;

 const overnightHtml = (mn.overnight_developments || []).map(dev => `
 <div style="margin:6px 0;padding:8px;background:#1e293b;border-radius:6px;">
 <strong style="color:#94a3b8;font-size:11px;text-transform:uppercase;">${dev.category}</strong><br>
 <span style="color:#f8fafc;">${dev.title}</span><br>
 <span style="color:#cbd5e1;font-size:13px;">📝 ${dev.take}</span>
 </div>
 `).join('');

 const ideasHtml = (mn.trade_ideas || []).map(idea => {
 const color = idea.direction === 'LONG' ? '#22c55e' : idea.direction === 'SHORT' ? '#ef4444' : '#eab308';
 return `
 <div style="margin:6px 0;padding:10px;border-left:3px solid ${color};background:#1e293b;border-radius:0 6px 6px 0;">
 <strong style="color:${color}">${idea.direction} ${idea.symbol}</strong><br>
 <span style="color:#f8fafc;font-size:13px;">${idea.thesis}</span><br>
 <span style="color:#94a3b8;font-size:12px;">🎯 ${idea.catalyst}</span><br>
 <span style="color:#f87171;font-size:12px;">⚠️ ${idea.risk}</span>
 </div>
 `;
 }).join('');

 const mnHtml = `
 <div style="background:#0f172a;border:1px solid #334155;border-radius:12px;padding:16px;margin-top:16px;color:#f8fafc;">
 <h3 style="margin:0 0 12px 0;font-size:16px;">📰 Morning Note — ${mn.symbol} <span style="font-size:12px;color:#64748b;">${mn.date}</span></h3>
 <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
 <div style="flex:1;height:8px;background:#1e293b;border-radius:4px;overflow:hidden;display:flex;">
 <div style="width:${bull}%;background:#22c55e;"></div>
 <div style="width:${base}%;background:#eab308;"></div>
 <div style="width:${bear}%;background:#ef4444;"></div>
 </div>
 <span style="font-weight:bold;color:${biasColor};font-size:14px;white-space:nowrap;">${mn.bias}</span>
 </div>
 ${mn.top_call?.body ? `<div style="padding:12px;background:#1e293b;border-radius:8px;margin-bottom:12px;border-left:3px solid #3b82f6;"><strong style="color:#60a5fa;">🔔 Top Call</strong><p style="margin:6px 0 0 0;color:#cbd5e1;font-size:14px;line-height:1.5;">${mn.top_call.body}</p></div>` : ''}
 ${overnightHtml ? `<h4 style="margin:16px 0 8px 0;font-size:13px;color:#94a3b8;text-transform:uppercase;">🌙 Développements Overnight</h4>${overnightHtml}` : ''}
 ${ideasHtml ? `<h4 style="margin:16px 0 8px 0;font-size:13px;color:#94a3b8;text-transform:uppercase;">💡 Trade Ideas</h4>${ideasHtml}` : ''}
 </div>
 `;

 $('tvResult').innerHTML = $('tvResult').innerHTML + mnHtml;
 }

 loadHistory();
 }catch(e){
 $('tvResult').innerHTML=`<div class="error">${e.message}</div>`;
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

 const biasColor = mn.bias === 'BULL' ? '#22c55e' : mn.bias === 'BEAR' ? '#ef4444' : '#eab308';
 const bull = mn.bias_scores?.bull || 0;
 const base = mn.bias_scores?.base || 0;
 const bear = mn.bias_scores?.bear || 0;

 const overnightHtml = (mn.overnight_developments || []).map(dev => `
 <div style="margin:6px 0;padding:8px;background:#1e293b;border-radius:6px;">
 <strong style="color:#94a3b8;font-size:11px;text-transform:uppercase;">${dev.category}</strong><br>
 <span style="color:#f8fafc;">${dev.title}</span><br>
 <span style="color:#cbd5e1;font-size:13px;">📝 ${dev.take}</span>
 </div>
 `).join('');

 const eventsHtml = (mn.key_events_today || []).map(ev => `
 <div style="margin:4px 0;font-size:13px;color:#cbd5e1;">
 <span style="color:#64748b;">${ev.time}</span> — ${ev.title} <em style="color:#475569;">(${ev.source})</em>
 </div>
 `).join('');

 const ideasHtml = (mn.trade_ideas || []).map(idea => {
 const color = idea.direction === 'LONG' ? '#22c55e' : idea.direction === 'SHORT' ? '#ef4444' : '#eab308';
 return `
 <div style="margin:6px 0;padding:10px;border-left:3px solid ${color};background:#1e293b;border-radius:0 6px 6px 0;">
 <strong style="color:${color}">${idea.direction} ${idea.symbol}</strong><br>
 <span style="color:#f8fafc;font-size:13px;">${idea.thesis}</span><br>
 <span style="color:#94a3b8;font-size:12px;">🎯 ${idea.catalyst}</span><br>
 <span style="color:#f87171;font-size:12px;">⚠️ ${idea.risk}</span>
 </div>
 `;
 }).join('');

 const topCallHtml = mn.top_call?.body
 ? `<div style="padding:12px;background:#1e293b;border-radius:8px;margin-bottom:12px;border-left:3px solid #3b82f6;"><strong style="color:#60a5fa;">🔔 Top Call</strong><p style="margin:6px 0 0 0;color:#cbd5e1;font-size:14px;line-height:1.5;">${mn.top_call.body}</p></div>`
 : '';

 const ind = mn.indicators || {};
 const indicatorsHtml = `
 <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px;">
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">Prix</span><strong style="font-size:14px;color:#f8fafc;">${ind.price ?? '—'}</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">24h</span><strong style="font-size:14px;color:${(ind.change_24h_pct||0)>0?'#22c55e':'#ef4444'}">${ind.change_24h_pct ?? '—'}%</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">RSI</span><strong style="font-size:14px;color:#f8fafc;">${ind.rsi_1h ?? '—'}</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">Vol</span><strong style="font-size:14px;color:#f8fafc;">${ind.volatility_1h ?? '—'}%</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">BTC Dom</span><strong style="font-size:14px;color:#f8fafc;">${ind.btc_dominance ?? '—'}%</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">F&G</span><strong style="font-size:14px;color:#f8fafc;">${ind.fear_greed_value ?? '—'}</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">Funding</span><strong style="font-size:14px;color:#f8fafc;">${ind.funding_rate ? (ind.funding_rate*100).toFixed(4)+'%' : '—'}</strong></div>
 <div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;"><span style="display:block;font-size:10px;color:#64748b;text-transform:uppercase;">Bid/Ask</span><strong style="font-size:14px;color:#f8fafc;">${ind.orderbook_bid_ask_ratio ?? '—'}</strong></div>
 </div>
 `;

 $('morningNoteResult').innerHTML = `
 <div style="background:#0f172a;border:1px solid #334155;border-radius:12px;padding:16px;color:#f8fafc;">
 <h3 style="margin:0 0 12px 0;font-size:16px;">📰 Morning Note — ${mn.symbol} <span style="font-size:12px;color:#64748b;">${mn.date}</span></h3>
 <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
 <div style="flex:1;height:8px;background:#1e293b;border-radius:4px;overflow:hidden;display:flex;">
 <div style="width:${bull}%;background:#22c55e;"></div>
 <div style="width:${base}%;background:#eab308;"></div>
 <div style="width:${bear}%;background:#ef4444;"></div>
 </div>
 <span style="font-weight:bold;color:${biasColor};font-size:14px;white-space:nowrap;">${mn.bias}</span>
 </div>
 ${indicatorsHtml}
 ${topCallHtml}
 ${overnightHtml ? `<h4 style="margin:16px 0 8px 0;font-size:13px;color:#94a3b8;text-transform:uppercase;">🌙 Développements Overnight</h4>${overnightHtml}` : ''}
 ${eventsHtml ? `<h4 style="margin:16px 0 8px 0;font-size:13px;color:#94a3b8;text-transform:uppercase;">📅 Événements Clés</h4>${eventsHtml}` : ''}
 ${ideasHtml ? `<h4 style="margin:16px 0 8px 0;font-size:13px;color:#94a3b8;text-transform:uppercase;">💡 Trade Ideas</h4>${ideasHtml}` : ''}
 </div>
 `;

 $('morningNoteCard').classList.remove('hidden');
 message('Morning Note généré.');
 } catch (e) {
 message(e.message);
 $('morningNoteCard').classList.add('hidden');
 }
};

