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
