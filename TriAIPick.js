/* ============================================================
   TriAIPick.js — トライサイト本体のAIの組み合わせ（2026-09-29）
   ------------------------------------------------------------
   ・3人のカードの上に役割の看板（理論AI・検証AI・評価AI）を出し、名前の下に、使っているAIを表示する。
   ・標準版は、通常の構成（理論＝OpenAI標準・検証＝Claude標準・評価＝OpenAI標準）で固定。
   ・プロバージョンは、契約のときにお客様と決めたAIの組み合わせで固定して出荷する（2026-09-29・宏史さんの決定）。
     画面では変えられない。組み合わせは当社のリレー（api/gemini の plan）が認証コードごとに答える。
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
  var isPro = false, contracted = null;

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
  function current(){ return isPro ? (contracted || PRO_DEFAULT) : STD; }

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
      + '.ai-pick-note{font-size:0.68rem;color:var(--text-dim,#9aa4b2);margin-top:4px}';
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
    if(plan.picks){ var ok = ROLES.every(function(r){ return !!byId(plan.picks[r]); }); if(ok) contracted = plan.picks; }
    apply(current()); render();
  }
  window.tsAiPick = { choices: CHOICES, std: STD, proDefault: PRO_DEFAULT, checked: CHECKED, isPro: function(){ return isPro; } };
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
