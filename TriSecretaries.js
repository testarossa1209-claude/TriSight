/* ============================================================
   TriSecretaries.js — 3人の秘書（あずさ・なぎさ・つかさ）の共通部品（2026-11-26）
   ------------------------------------------------------------
   ・「秘書と話す」（TriSight_v5.html）と「よろず相談」の舞台（TriYorozu.html）が同じものを使う。
     秘書の役割・声・名前での指名・返答の取り方は、ここだけを直す（片方だけ直して食い違うのを防ぐ）。
   ・役割は宏史さんの定義（2026-11-26）。トライサイトの基本理念＝一つの見方に偏らず三つの方向から考える。答えを決めるのは人間。
       あずさ＝いまの状況から、これからの姿を自由な発想で描く
       なぎさ＝考えていることを現実の手順に落とし込み、再現性を確かめる
       つかさ＝施策や理屈が現実に通用するかを、忖度せずに評価する
   ・声：あずさ＝Google Sulafat／なぎさ＝Google Achernar（Gemini 3.1 Flash TTS。公開の場では Vertex AI 経由）／つかさ＝OpenAI Marin
   ・返答のAI：画面に TS_MODELS（本体の「使うAIの表」）があればそれに従い、無ければ下の標準を使う。
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
  /* 話の頭の名前で指名（ひらがな・カタカナ・漢字の聞き取り揺れも受ける。漢字は後ろに「さん」か区切りがあるときだけ） */
  var CALL = [
    ['azusa',   /^(?:(?:あずさ|アズサ)(?:さん|ちゃん)?[、,，。\s　]*|梓(?:さん|ちゃん)?[、,，。\s　]+)/],
    ['nagisa',  /^(?:(?:なぎさ|ナギサ)(?:さん|ちゃん)?[、,，。\s　]*|渚(?:さん|ちゃん)?[、,，。\s　]+)/],
    ['tsukasa', /^(?:(?:つかさ|ツカサ)(?:さん|ちゃん)?[、,，。\s　]*|司(?:さん|ちゃん)?[、,，。\s　]+)/]
  ];
  /* 返り値 { who: 指名された秘書（無ければ null）, text: 名前を除いた残り } */
  function takeName(t){
    t = String(t || '').trim();
    for(var i = 0; i < CALL.length; i++){ var m = t.match(CALL[i][1]); if(m) return { who: CALL[i][0], text: t.slice(m[0].length).trim() }; }
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
  /* 会話の履歴 [{role:'user'|'assistant', content}] を渡して、指名した秘書の返答を得る */
  async function ask(k, history){
    var cfg = (global.TS_MODELS && global.TS_MODELS[k]) || MODELS[k];
    var system = today() + sysPrompt(k);
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
      }
      r = await fetch(url, { method:'POST', headers:{ 'Content-Type':'application/json', 'x-trisight-code': code() }, body: JSON.stringify(body) });
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
  global.TriSecretaries = { SEC: SEC, ROLE_TEXT: ROLE_TEXT, sysPrompt: sysPrompt, takeName: takeName, ask: ask, ORDER: ['azusa','nagisa','tsukasa'], version: '1.0' };
})(typeof window !== 'undefined' ? window : this);
