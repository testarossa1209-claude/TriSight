/* ============================================================
   TriAIPick.js — トライサイト本体のAIの組み合わせ（2026-09-29／2026-10-01 改2）
   ------------------------------------------------------------
   ・3人のカードの上に役割の看板（理論AI・検証AI・評価AI）を出し、名前の下に、使っているAIを表示する。
   ・標準版は、通常の構成（理論＝OpenAI標準・検証＝Claude標準・評価＝OpenAI標準）で固定。
   ・プロバージョンは、契約のときにお客様と決めたAIの組み合わせで出荷する（2026-09-29・宏史さんの決定）。
     2026-10-01 改1：選択窓オプションを付けたコード（組み合わせの記録に win: true）だけ、3人の下に選択窓を出し、
     お客様が使い勝手や能力に合わせて変えられる。選んだ内容はその端末にコードごとに残す。「契約時組合せに戻す」で戻る。
     オプションの無いプロのコードは、今までどおり画面では変えられない。
   ・流れの図（2026-10-01 改2・標準版も含むすべてのコード）：見出し「出口を解決するプロセス構造」を付け、枠を明確に、
     矢印を見えるように、6つを1行に並べる（宏史さんの指示）。
   ・プロのコードでは表紙をプロの形にする（2026-10-01 確定）：表題の横に「Pro」、
     開始ボタンの下に「プロ：契約時組合せに戻す（オプション付きのみ）・自動発掘・トライゲイト」。組み合わせは当社のリレー（api/gemini の plan）が認証コードごとに答える。
     契約の組み合わせが登録されていないプロのコードは、通常の構成を各社の最上位モデルにしたもの（2026-09-26の決定）。
   ・組み合わせは、本体の「使うAIの表」（TS_MODELS）へそのまま入れる。呼び出しは、その会社の口へ自動で振り分ける。
   ・本体（TriSight_v5.html）とAI連携オプション（TriSight_v5_auto.html）の両方が、このファイルを読み込む。
   ・選択肢の名前は、各社の公式のモデル一覧で確かめたもの（確認日 CHECKED）。定期更新はここだけを書き換える。
   ============================================================ */
(function(){
  'use strict';
  var RELAY = 'https://trisight-relay.vercel.app/api/';
  var CHECKED = '2026-09-29';
  var ROLES = ['azusa', 'nagisa', 'tsukasa'];
  var SIGN = { azusa: '理論AI', nagisa: '検証AI', tsukasa: '評価AI' };
  var CHOICES = [
    { id: 'openai-std', vendor: 'openai',    maker: 'OpenAI', grade: '標準',   primary: 'gpt-6-sol',              fallback: 'gpt-4o' },
    { id: 'openai-top', vendor: 'openai',    maker: 'OpenAI', grade: '最上位', primary: 'gpt-6-astra',            fallback: 'gpt-6-sol' },
    { id: 'claude-std', vendor: 'anthropic', maker: 'Claude', grade: '標準',   primary: 'claude-sonnet-5',        fallback: 'claude-sonnet-4-6' },
    { id: 'claude-top', vendor: 'anthropic', maker: 'Claude', grade: '最上位', primary: 'claude-fable-5-1',       fallback: 'claude-opus-5-5' },
    { id: 'gemini-std', vendor: 'google',    maker: 'Gemini', grade: '標準',   primary: 'gemini-3.5-flash',       fallback: 'gemini-3.1-flash-lite' },
    { id: 'gemini-top', vendor: 'google',    maker: 'Gemini', grade: '最上位', primary: 'gemini-3.1-pro-preview', fallback: 'gemini-3.5-flash' }
  ];
  var STD = { azusa: 'openai-std', nagisa: 'claude-std', tsukasa: 'openai-std' };
  var PRO_DEFAULT = { azusa: 'openai-top', nagisa: 'claude-top', tsukasa: 'openai-top' };
  var isPro = false, contracted = null, optWin = false;
  function ownKey(){ return 'trisight_pro_picks:' + code(); }
  function valid(p){ return p && ROLES.every(function(r){ return !!byId(p[r]); }); }
  function loadOwn(){ try{ var j = JSON.parse(localStorage.getItem(ownKey()) || 'null'); return valid(j) ? j : null; }catch(_){ return null; } }
  function saveOwn(p){ try{ if(p) localStorage.setItem(ownKey(), JSON.stringify(p)); else localStorage.removeItem(ownKey()); }catch(_){} }

  function byId(id){ for(var i = 0; i < CHOICES.length; i++){ if(CHOICES[i].id === id) return CHOICES[i]; } return null; }
  function code(){ try{ return localStorage.getItem('trisight_access_code') || ''; }catch(_){ return ''; } }
  function label(c){ return c.maker + '（' + c.grade + '）' + c.primary; }

  /* 選んだ内容を「使うAIの表」へ入れる */
  function apply(picks){
    if(typeof TS_MODELS === 'undefined') return;
    ROLES.forEach(function(r){
      var c = byId(picks[r]) || byId(STD[r]);
      TS_MODELS[r] = { vendor: c.vendor, primary: c.primary, fallback: c.fallback };
    });
    TS_MODELS.checked = CHECKED;
    try{ if(typeof tsModelLine === 'function') tsModelLine(); }catch(_){}
  }
  function current(){ if(!isPro) return STD; var base = contracted || PRO_DEFAULT; return optWin ? (loadOwn() || base) : base; }

  /* ---- 画面：看板と選択窓 ---- */
  function injectStyle(){
    if(document.getElementById('tsAiPickStyle')) return;
    var s = document.createElement('style'); s.id = 'tsAiPickStyle';
    s.textContent =
      '.ai-sign{display:inline-block;margin:0 auto 10px;padding:3px 14px;border:1px solid var(--border-gold,#c9a84c);border-radius:4px;'
      + 'color:var(--gold,#c9a84c);font-size:0.8rem;font-weight:700;letter-spacing:0.12em}'
      + '.ai-pick{margin:4px 0 10px}'
      + '.ai-pick .ai-model{display:inline-block;font-size:0.78rem;padding:4px 10px;border-radius:4px;'
      + 'background:var(--bg3,#1b2a3d);color:var(--text,#f5f0e8);border:1px solid var(--border-gold,#c9a84c)}'
      + '.ai-pick-note{font-size:0.68rem;color:var(--text-dim,#9aa4b2);margin-top:4px}'
      + '.ai-pick select{font-family:inherit;font-size:0.8rem;padding:5px 8px;border-radius:4px;max-width:100%;'
      + 'background:var(--bg3,#12122a);color:var(--text,#e8e0d0);border:1px solid var(--border-gold,#c9a84c44);cursor:pointer}'
      + '.ts-pro-tag{font-size:1rem;margin-left:10px;padding:1px 10px;border:1px solid var(--gold,#c9a84c);border-radius:4px;letter-spacing:0.12em;vertical-align:middle;font-family:\'Zen Kaku Gothic New\',sans-serif}'
      + '.ts-flowbox{background:var(--bg2,#0d0d1e);border:1px solid var(--border,#2a2a3e);border-radius:12px;padding:18px 16px 22px;margin-bottom:40px}'
      + '.ts-flow-title{text-align:center;font-size:0.85rem;color:var(--gold-light,#e0be6a);letter-spacing:0.12em;margin:0 0 14px;font-family:\'Zen Kaku Gothic New\',sans-serif}'
      + '.ts-flowbox .flow-diagram{background:none;border:0;padding:0;margin:0;gap:4px;flex-wrap:nowrap;overflow-x:auto}'
      + '.ts-flowbox .flow-node{background:#1a1a36;border:1.5px solid var(--gold,#c9a84c);color:var(--gold-light,#e0be6a);padding:7px 9px;font-size:0.78rem;flex:none}'
      + '.ts-flowbox .flow-arrow{color:var(--gold,#c9a84c);font-size:1.05rem;padding:0 1px;flex:none}'
      + '.ts-pro-links a{cursor:pointer}';
    document.head.appendChild(s);
  }
  function render(){
    var cards = document.querySelectorAll('#launcher .trinity .ai-card');
    if(cards.length < 3) return;
    injectStyle();
    var picks = current();
    ROLES.forEach(function(r, i){
      var card = cards[i];
      if(!card.querySelector('.ai-sign')){
        var sign = document.createElement('div'); sign.className = 'ai-sign'; sign.textContent = SIGN[r];
        card.insertBefore(sign, card.firstChild);
        var role = card.querySelector('.ai-role'); if(role) role.style.display = 'none';   /* 看板と同じ文言なので二重に出さない */
      }
      var box = card.querySelector('.ai-pick');
      if(!box){
        box = document.createElement('div'); box.className = 'ai-pick';
        var nameEl = card.querySelector('.ai-name');
        if(nameEl && nameEl.nextSibling) card.insertBefore(box, nameEl.nextSibling); else card.appendChild(box);
      }
      var c = byId(picks[r]) || byId(STD[r]);
      if(optWin){                          /* 選択窓オプション付きのプロ：3人それぞれ選べる */
        var sel = document.createElement('select'); sel.setAttribute('data-role', r); sel.setAttribute('aria-label', SIGN[r] + 'に使うAI');
        CHOICES.forEach(function(ch){ var o = document.createElement('option'); o.value = ch.id; o.textContent = label(ch); if(ch.id === c.id) o.selected = true; sel.appendChild(o); });
        sel.onchange = function(){ var p = current(); var q = { azusa: p.azusa, nagisa: p.nagisa, tsukasa: p.tsukasa }; q[sel.getAttribute('data-role')] = sel.value; saveOwn(q); apply(current()); render(); };
        box.innerHTML = ''; box.appendChild(sel);
        return;
      }
      var tag = document.createElement('span'); tag.className = 'ai-model'; tag.setAttribute('data-role', r);
      tag.textContent = label(c);
      box.innerHTML = ''; box.appendChild(tag);
      if(r === 'nagisa'){
        var note = document.createElement('div'); note.className = 'ai-pick-note';
        note.textContent = isPro ? 'ご契約で決めたAIの組み合わせです（変更はトライサイトへご相談ください）'
                                 : '標準版の構成です（AIの組み合わせを契約で決められるのは、トライサイト プロバージョンです）';
        box.appendChild(note);
      }
    });
    renderFlow();
    renderProCover();
  }

  /* ---- プロの表紙（2026-10-01 確定）：プロのコードのときだけ ---- */
  /* ---- 流れの図（2026-10-01 改2）：標準版も含むすべてのコード ---- */
  function renderFlow(){
    var fd = document.querySelector('#launcher .flow-diagram');
    if(fd && !fd.parentNode.classList.contains('ts-flowbox')){
      var box = document.createElement('div'); box.className = 'ts-flowbox';
      var h = document.createElement('div'); h.className = 'ts-flow-title'; h.textContent = '出口を解決するプロセス構造';
      fd.parentNode.insertBefore(box, fd); box.appendChild(h); box.appendChild(fd);
    }
  }
  function renderProCover(){
    if(!isPro) return;
    var t = document.querySelector('#launcher .launcher-title');
    if(t && !t.querySelector('.ts-pro-tag')){ var g = document.createElement('span'); g.className = 'ts-pro-tag'; g.textContent = 'Pro'; t.appendChild(g); }
    var sl = document.querySelector('#launcher .sheet-links');
    if(!sl) return;
    var row = document.getElementById('tsProLinks');
    if(!row){ row = document.createElement('div'); row.id = 'tsProLinks'; row.className = 'sheet-links ts-pro-links'; sl.parentNode.insertBefore(row, sl.nextSibling); }
    row.innerHTML = 'プロ：'
      + (optWin ? '<a role="button" id="tsBackContract">契約時組合せに戻す</a>' : '')
      + '<a href="TriNight.html" target="_blank" rel="noopener">自動発掘</a>'
      + '<a href="TriGate.html" target="_blank" rel="noopener">トライゲイト</a>';
    var b = document.getElementById('tsBackContract');
    if(b) b.onclick = function(e){ e.preventDefault(); saveOwn(null); apply(current()); render();
      var x = document.getElementById('tsBackContract'); if(!x) return; x.textContent = '契約時組合せに戻しました';
      setTimeout(function(){ var y = document.getElementById('tsBackContract'); if(y) y.textContent = '契約時組合せに戻す'; }, 2000); };
  }

  /* ---- 呼び出しの振り分け：選んだ会社の口へ送る ---- */
  /* 表が見えないときは、呼ばれた口をそのまま使う（勝手に別の会社へ寄せない） */
  function vendorOf(role, dflt){ return (typeof TS_MODELS !== 'undefined' && TS_MODELS[role] && TS_MODELS[role].vendor) || dflt; }
  function splitForAnthropic(messages){
    var sys = [], usr = [];
    (messages || []).forEach(function(m){ (m && m.role === 'system' ? sys : usr).push(String((m && m.content) || '')); });
    return { system: sys.join('\n\n'), user: usr.join('\n\n') };
  }
  async function callGemini(role, messages, errLabel, temperature){
    var cfg = TS_MODELS[role];
    var tries = [cfg.primary, cfg.fallback].filter(function(m, i, a){ return m && a.indexOf(m) === i; });
    var lastErr = null;
    for(var i = 0; i < tries.length; i++){
      var model = tries[i];
      var body = { model: model, messages: messages, max_tokens: 16000 };
      if(typeof temperature === 'number') body.temperature = temperature;
      var r = await fetch(RELAY + 'gemini', { method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-trisight-code': code() }, body: JSON.stringify(body) });
      if(r.status === 401){ if(typeof tsAuthFail === 'function') tsAuthFail(401); throw new Error((errLabel || '') + '認証コードが合いません'); }
      if(r.ok){
        var t = '';
        try{ var j = await r.json(); t = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || ''; }catch(_){ t = ''; }
        if(t && String(t).trim()){
          window.TS_AI_USED = window.TS_AI_USED || {};
          window.TS_AI_USED[role] = { model: model, fellBack: i > 0 };
          try{ if(typeof tsModelLine === 'function') tsModelLine(); }catch(_){}
          return t;
        }
        lastErr = new Error((errLabel || '') + '空の答えが返りました（' + model + '）');
      }else{
        var e = null; try{ e = await r.json(); }catch(_){}
        lastErr = new Error((errLabel || '') + ((e && e.error && (e.error.message || e.error)) || r.status) + '（' + model + '）');
      }
    }
    throw lastErr;
  }
  function wrap(){
    if(typeof window.tsCallOpenAI !== 'function' || typeof window.tsCallAnthropic !== 'function' || window.__tsAiPickWrapped) return;
    window.__tsAiPickWrapped = true;
    var _openai = window.tsCallOpenAI, _anthropic = window.tsCallAnthropic;
    window.tsCallOpenAI = async function(role, messages, errLabel){
      var v = vendorOf(role, 'openai');
      if(v === 'anthropic'){ var x = splitForAnthropic(messages); return _anthropic(role, x.system, x.user); }
      if(v === 'google') return callGemini(role, messages, errLabel);
      return _openai(role, messages, errLabel);
    };
    window.tsCallAnthropic = async function(role, system, user, temperature){
      var v = vendorOf(role, 'anthropic');
      var msgs = [{ role: 'system', content: String(system || '') }, { role: 'user', content: String(user || '') }];
      if(v === 'openai') return _openai(role, msgs, '');
      if(v === 'google') return callGemini(role, msgs, '', temperature);
      return _anthropic(role, system, user, temperature);
    };
  }

  /* ---- プロかどうかを、当社のリレーに聞く（聞けなければ標準版として扱う） ---- */
  async function askPlan(){
    var c = code(); if(!c) return { pro: false, picks: null };
    try{
      var r = await fetch(RELAY + 'gemini', { method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-trisight-code': c }, body: JSON.stringify({ op: 'plan' }) });
      if(!r.ok) return { pro: false, picks: null };
      var j = await r.json();
      return { pro: !!(j && j.pro), picks: (j && j.picks) || null };
    }catch(_){ return { pro: false, picks: null }; }
  }

  async function start(){
    wrap();
    apply(STD); render();                 /* まず標準で描き、答えが来たら描き直す */
    var plan = await askPlan();
    isPro = plan.pro;
    contracted = null;
    if(plan.picks){ var ok = ROLES.every(function(r){ return !!byId(plan.picks[r]); }); if(ok) contracted = { azusa: plan.picks.azusa, nagisa: plan.picks.nagisa, tsukasa: plan.picks.tsukasa }; }
    optWin = !!(isPro && contracted && plan.picks.win === true);
    apply(current()); render();
  }
  window.tsAiPick = { choices: CHOICES, std: STD, proDefault: PRO_DEFAULT, checked: CHECKED, isPro: function(){ return isPro; } };
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
