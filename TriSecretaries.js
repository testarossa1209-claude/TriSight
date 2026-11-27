/* ============================================================
   TriSecretaries.js — 3人の秘書（あずさ・なぎさ・つかさ）の共通部品（2026-11-26）
   ------------------------------------------------------------
   ・「秘書と話す」（TriSight_v5.html）・「よろず相談」の舞台（TriYorozu.html）・トライトーク（TriTalk.html）が同じものを使う。
     秘書の役割・声・名前での指名・返答の取り方は、ここだけを直す（片方だけ直して食い違うのを防ぐ）。
   ・役割は宏史さんの定義（2026-11-26）。トライサイトの基本理念＝一つの見方に偏らず三つの方向から考える。答えを決めるのは人間。
       あずさ＝いまの状況から、これからの姿を自由な発想で描く
       なぎさ＝考えていることを現実の手順に落とし込み、再現性を確かめる
       つかさ＝施策や理屈が現実に通用するかを、忖度せずに評価する
   ・声：あずさ＝Google Sulafat／なぎさ＝Google Achernar（Gemini 3.1 Flash TTS。公開の場では Vertex AI 経由）／つかさ＝OpenAI Marin
   ・返答のAI：画面に TS_MODELS（本体の「使うAIの表」）があればそれに従い、無ければ下の標準を使う。
   ・2026-11-27（宏史さんの指摘「あずさだけではなく、なぎさでもつかさでも情報は渡しておいてもらわないとだめ」）：
     トライサイトの知識（TriTalkKnowledge.js の基礎知識＋利用解説書の抜き出し）は、ask の中で必ず添える。
     画面ごとに添える作りでは、本体の「秘書と話す」・同時通訳の板などで渡し忘れが3度起きたため。
     画面が既に添えているとき（「【トライサイトの基礎知識」を含むとき）は二重に添えない。部品が読み込まれていない画面では、ここで読み込む。
   ============================================================ */
(function(global){
  'use strict';
  var RELAY = 'https://trisight-relay.vercel.app';
  var MODELS = {
    azusa:   { vendor: 'openai',    primary: 'gpt-6-sol',       fallback: 'gpt-4o' },
    nagisa:  { vendor: 'anthropic', primary: 'claude-sonnet-5', fallback: 'claude-sonnet-4-6' },
    tsukasa: { vendor: 'openai',    primary: 'gpt-6-sol',       fallback: 'gpt-4o' }
  };
  var SEC = {
    azusa:   { name:'あずさ', role:'構想', tag:'自由な発想で、これからの姿を描く',
               voice:{ vendor:'google', voice:'Sulafat',  model:'gemini-3.1-flash-tts-preview', instructions:'柔らかく明るい口調で、親しみを込めて話す。' } },
    nagisa:  { name:'なぎさ', role:'検証', tag:'現実の手順に落とし込み、再現性を確かめる',
               voice:{ vendor:'google', voice:'Achernar', model:'gemini-3.1-flash-tts-preview', instructions:'温かく、迎え入れるような口調で、落ち着いて丁寧に話す。' } },
    tsukasa: { name:'つかさ', role:'評価', tag:'忖度せず、現実に照らして評価する',
               voice:{ vendor:'openai', voice:'marin',    model:'gpt-4o-mini-tts',      instructions:'結論からはっきり言い切る、落ち着いた口調で話す。' } }
  };
  var ROLE_TEXT = {
    azusa:   '担当は「構想」。いまの状況から、これからの姿を一緒に描く。思いつきの段階の話も否定せず、枠にとらわれない自由な発想で案を広げる。実行の細部や評価は、なぎさ・つかさに任せてよい。',
    nagisa:  '担当は「検証」。相手が考えていることを、現実の手順に落とし込む。誰がやっても同じ結果になるか（再現性）を確かめ、確かめられていること・確かめていないこと・抜けている前提を見分けて、実際に動ける形に整える。',
    tsukasa: '担当は「評価」。考えた施策や理屈が、現実に照らして本当に通用するかを評価する。忖度はしない。相手に合わせて甘くせず、良いところも足りないところもはっきり言い、実行してよいか・条件は何か・どう測るかを結論から伝える。'
  };
  function sysPrompt(k){
    return 'あなたはTriSight®の秘書「' + SEC[k].name + '」です。' + ROLE_TEXT[k] + '\n'
      + 'これは声の会話です。返答はそのまま声で読み上げられるので、次を守ってください。\n'
      + '・話し言葉の日本語で、短く（目安は3〜5文）。長くなる話は要点だけ言い、続きを聞くか相手に尋ねる。\n'
      + '・箇条書き、見出し、記号（＊・＃・矢印など）、URL、表は使わない。\n'
      + '・確かめていないことは「確かめていません」と言い、推測を断定で言わない。\n'
      + '・最後に決めるのは相手（人間）。結論を押し付けず、判断の材料を渡す。\n'
      + '・相手の聞き取り間違いと思われる言葉は、文脈から正しく受け取る。意味が取れないときは聞き返す。';
  }
  /* 名前で指名（2026-11-26 宏史さん「秘書を指名すると名前を呼ぶすべての機能を装備」）
     ・ひらがな・カタカナ・漢字の聞き取り揺れを受ける（漢字は後ろに敬称か区切りがあるときだけ）
     ・敬称：さん／ちゃん／くん／君／様／さま
     ・頭の呼びかけ：「ねえ、なぎさ」「じゃあ、つかさ」「では、あずさ」「ちょっと、〜」「あの、〜」「おい、〜」も、その後に名前が来れば指名として受ける */
  var HON = '(?:さん|ちゃん|くん|君|様|さま)?';
  var SEP = '[、,，。！!？?\\s　]';
  var LEAD = new RegExp('^(?:(?:ねえ|ねぇ|ねー|じゃあ|じゃ|それでは|では|ちょっと|あのう|あの|おい)' + SEP + '*|ね' + SEP + '+)');
  function callRe(kana, kanji){ return new RegExp('^(?:(?:' + kana + ')' + HON + SEP + '*|(?:' + kanji + ')' + HON + SEP + '+|(?:' + kanji + ')(?:さん|ちゃん|くん|様|さま)' + SEP + '*)'); }
  var CALL = [
    ['azusa',   callRe('あずさ|アズサ', '梓')],
    ['nagisa',  callRe('なぎさ|ナギサ', '渚')],
    ['tsukasa', callRe('つかさ|ツカサ', '司')]
  ];
  /* 名前のすぐ後に助詞が続くとき（「なぎさはどう思う？」「あずさに聞きます」）は、呼びかけではなく文の一部なので、指名だけして文はそのまま残す */
  var PARTICLE = new RegExp('^(?:あずさ|アズサ|なぎさ|ナギサ|つかさ|ツカサ|梓|渚|司)' + HON + '(?=[にはがのもをとへやっ])');
  /* 返り値 { who: 指名された秘書（無ければ null）, text: 名前（と頭の呼びかけ）を除いた残り } */
  function takeName(t){
    t = String(t || '').trim();
    var lead = t.match(LEAD), body = lead ? t.slice(lead[0].length) : t;
    for(var i = 0; i < CALL.length; i++){
      var m = body.match(CALL[i][1]);
      if(m) return { who: CALL[i][0], text: PARTICLE.test(body) ? body : body.slice(m[0].length).trim() };
    }
    return { who: null, text: t };
  }
  function code(){
    if(typeof global.tsCode === 'function') return global.tsCode();
    var c = null; try{ c = localStorage.getItem('trisight_access_code'); }catch(e){}
    if(c && /[^\x21-\x7E]/.test(c)){ try{ localStorage.removeItem('trisight_access_code'); }catch(e){} c = null; }
    while(!c){
      c = prompt('TriSight 認証コードを入力してください（この端末での初回のみ・半角英数字）');
      if(c === null) return '';
      c = c.trim();
      if(c === '' || /[^\x21-\x7E]/.test(c)){ alert('認証コードは半角英数字で入力してください。'); c = null; continue; }
      try{ localStorage.setItem('trisight_access_code', c); }catch(e){}
    }
    return c;
  }
  function authFail(st){
    if(st !== 401) return false;
    if(typeof global.tsAuthFail === 'function') return global.tsAuthFail(st);
    try{ localStorage.removeItem('trisight_access_code'); }catch(e){}
    alert('TriSight認証コードが未入力または不一致です。ページを再読み込みして、正しいコードを入力し直してください。');
    return true;
  }
  function today(){ var d = new Date(); return '【今日の日付】' + d.getFullYear() + '年' + (d.getMonth()+1) + '月' + d.getDate() + '日\n\n'; }
  /* 会話の履歴 [{role:'user'|'assistant', content}] を渡して、指名した秘書の返答を得る
     opts.extra … その画面だけの添え書き（例：トライトークの「みんな」で3人が順に答えるときの決まり）。system の末尾に足す（2026-11-26） */
  var kLoading = null;
  function knowledgeLib(){
    if(global.TriTalkKnowledge) return Promise.resolve(global.TriTalkKnowledge);
    if(typeof document === 'undefined') return Promise.resolve(null);
    if(!kLoading) kLoading = new Promise(function(res){
      var sc = document.createElement('script'); sc.src = 'TriTalkKnowledge.js';
      sc.onload = function(){ res(global.TriTalkKnowledge || null); }; sc.onerror = function(){ res(null); };
      document.head.appendChild(sc);
    });
    return kLoading;
  }
  async function withKnowledge(extra, history){
    if(extra.indexOf('【トライサイトの基礎知識') >= 0) return extra;
    try{
      var K = await knowledgeLib(); if(!K || !K.forQuery) return extra;
      var q = ''; for(var i = history.length - 1; i >= 0; i--){ if(history[i].role === 'user'){ q = String(history[i].content || ''); break; } }
      return extra + await K.forQuery(q);
    }catch(e){ return extra; }
  }
  async function ask(k, history, opts){
    var cfg = (global.TS_MODELS && global.TS_MODELS[k]) || MODELS[k];
    var extra = await withKnowledge((opts && opts.extra) ? String(opts.extra) : '', history);   /* 3人とも、どの画面からでも知識を添える（2026-11-27） */
    var system = today() + sysPrompt(k) + (extra ? '\n' + extra : '');
    var msgs = history.slice(-20).map(function(m){ return { role: m.role, content: m.content }; });
    var tries = [cfg.primary, cfg.fallback].filter(function(m, i, a){ return m && a.indexOf(m) === i; }), lastErr = null;
    for(var i = 0; i < tries.length; i++){
      var model = tries[i], r, url, body;
      if(cfg.vendor === 'anthropic'){
        url = RELAY + '/api/anthropic';
        body = { model: model, max_tokens: 1200, system: system, messages: msgs };
      } else {
        url = RELAY + '/api/openai';
        body = { model: model, messages: [{ role:'system', content: system }].concat(msgs) };
        if(/^gpt-4/.test(model)) body.max_tokens = 1200; else body.max_completion_tokens = 4000;
        /* 2026-11-26：会話の画面（トライトーク）は速さを優先し、考える段階を飛ばす（gpt-6-sol は考えてから答える型で、指定が無いと中くらいに考える。
           OpenAI の説明では reasoning.effort に none を選べる）。受け付けられなかったときは、指定を外して同じAIで取り直す */
        if(opts && opts.fast && !/^gpt-4/.test(model)){ body.reasoning_effort = 'none'; body.max_completion_tokens = 1200; }
      }
      r = await fetch(url, { method:'POST', headers:{ 'Content-Type':'application/json', 'x-trisight-code': code() }, body: JSON.stringify(body) });
      if(r.status === 400 && body.reasoning_effort){ delete body.reasoning_effort; body.max_completion_tokens = 4000;
        r = await fetch(url, { method:'POST', headers:{ 'Content-Type':'application/json', 'x-trisight-code': code() }, body: JSON.stringify(body) }); }
      if(r.status === 401){ authFail(401); throw new Error('認証コードが合いません'); }
      if(r.ok){
        var j = await r.json(), t = '';
        if(cfg.vendor === 'anthropic') t = (j.content || []).map(function(c){ return c && c.text || ''; }).join('');
        else t = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || '';
        t = String(t || '').trim();
        if(t) return t;
        lastErr = new Error('空の答えが返りました（' + model + '）');
      } else {
        var e = null; try{ e = await r.json(); }catch(_){}
        lastErr = new Error(((e && e.error && (e.error.message || e.error)) || r.status) + '（' + model + '）');
      }
    }
    throw lastErr;
  }
  global.TriSecretaries = { SEC: SEC, ROLE_TEXT: ROLE_TEXT, sysPrompt: sysPrompt, takeName: takeName, LEAD: LEAD, ask: ask, ORDER: ['azusa','nagisa','tsukasa'], version: '1.4' };
})(typeof window !== 'undefined' ? window : this);
