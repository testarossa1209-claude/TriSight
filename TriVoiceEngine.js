/*! ===========================================================================
 *  TriVoiceEngine.js  —  TriSight® 横串・共通音声エンジン（正）  v2.0（2026-10-15）
 *  ---------------------------------------------------------------------------
 *  役割：録音 → リレー → 文字起こし(Whisper) → ［任意］AI構造化(Claude) → 落とし込み
 *  構成：iPad Safari でも確実に動く MediaRecorder 方式。
 *        ブラウザの音声認識(Web Speech API)は使わない。
 *
 *  落とす先は3つ（録音・文字起こしの仕組みは1つを共有する）：
 *    ① スキーマモード … 多欄フォーム（看護記録・キャンセル記録 等）。
 *                       schema を渡すと STT→AI構造化→各DOM欄へ自動振り分け。   TriVoice.init({schema:…})
 *    ② 素通しモード   … 単一入力欄（本体あずさ・看護メモ 等）。
 *                       onText を渡すと STT結果をそのまま渡す（AI構造化は省く）。 TriVoice.init({onText:…})
 *    ③ 口述モード     … どの画面でも使う汎用の音声入力（2026-10-15 追加）。
 *                       画面右下にマイクを1つ出し、最後に押した入力欄へ、話した文字をカーソル位置に入れる。
 *                       TriVoice.dictation({ exclude:'#r_職員名簿' })
 *                       exclude に当たる欄（個人情報を送らない約束の欄）には入れない。
 *
 *  2026-10-15：トライケア（看護部採用）の看護記録・看護メモが、それぞれ画面の中に別の録音の仕組みを
 *  持っていたのを、この部品へ一本化した。どのシステムでも同じ部品で音声入力できることを共通エンジンの条件とする。
 *
 *  依存なし。①②は1ページ1フォーム。③は①②と同じページでも使えるが、録音は同時に1つだけ。
 * ========================================================================= */
(function (global) {
  'use strict';

  /* ---- 既定値（必要なら init / dictation で上書き） ---------------------- */
  var DEFAULTS = {
    relay:       'https://trisight-relay.vercel.app',
    sttPath:     '/api/transcribe',
    aiPath:      '/api/anthropic',
    sttModel:    'whisper-1',
    aiModel:     'claude-sonnet-4-6',
    language:    'ja',
    filledClass: 'ai-filled',
    maxTokens:   2000
  };

  /* ===== TriSight 認証コード（リレー保護・2026-07-11導入） ===== */
  function tsCode(){
    var c = localStorage.getItem('trisight_access_code');
    if(c && /[^\x21-\x7E]/.test(c)){ localStorage.removeItem('trisight_access_code'); c = null; }
    while(!c){
      c = prompt('TriSight 認証コードを入力してください（この端末での初回のみ・半角英数字）');
      if(c === null){ return ''; }
      c = c.trim();
      if(c === '' || /[^\x21-\x7E]/.test(c)){
        alert('認証コードは半角英数字で入力してください（全角文字・日本語・空白は使えません）。\n日本語入力（IME）をオフにして、打ち直してください。');
        c = null;
        continue;
      }
      localStorage.setItem('trisight_access_code', c);
    }
    return c;
  }
  function tsAuthFail(status){
    if(status === 401){
      localStorage.removeItem('trisight_access_code');
      alert('TriSight認証コードが未入力または不一致です。ページを再読み込みして、正しいコードを入力し直してください。');
      return true;
    }
    return false;
  }

  /* ---- ユーティリティ --------------------------------------------------- */
  function el(sel){ return (typeof sel === 'string') ? document.querySelector(sel) : sel; }
  function merge(opts){ var c = {}; for(var k in DEFAULTS){ c[k] = (opts && k in opts) ? opts[k] : DEFAULTS[k]; } return c; }

  function pickMime(){
    var prefs = ['audio/mp4', 'audio/aac', 'audio/webm']; // iOS Safari は mp4
    if(global.MediaRecorder){
      for(var i=0;i<prefs.length;i++){
        try{ if(MediaRecorder.isTypeSupported(prefs[i])) return prefs[i]; }catch(e){}
      }
    }
    return ''; // 未指定＝ブラウザ既定に委ねる
  }

  /* =====================================================================
     録音器（全モード共通・同時に1つだけ）
     rec.start(owner) … owner = { button, status(t), recordingMessage, conf, onText(txt) }
     ===================================================================== */
  var rec = { mr:null, chunks:[], stream:null, owner:null };

  function stopStream(){
    if(rec.stream){ rec.stream.getTracks().forEach(function(t){ t.stop(); }); rec.stream = null; }
  }
  function isRecording(){ return !!(rec.mr && rec.mr.state !== 'inactive'); }

  /* 録音中なら止める（止めた分は文字起こしへ回る）。印刷・クリア前などに外部から呼べる */
  function stopRec(){
    if(isRecording()){ try{ rec.mr.stop(); }catch(e){} }
    else { stopStream(); if(rec.owner && rec.owner.button){ rec.owner.button.classList.remove('listening'); } rec.owner = null; }
  }

  function startRec(owner){
    var say = owner.status || function(){};
    if(!global.MediaRecorder || !navigator.mediaDevices){
      say('この端末は録音に未対応です（手入力・印刷は可能です）。'); return;
    }
    if(isRecording()){
      var same = (rec.owner === owner);
      stopRec();
      if(same) return;                 // トグル：録音中の再押下で停止
    }
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream){
      rec.stream = stream;
      var mime = pickMime(), mr;
      try{ mr = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream); }
      catch(e){ say('録音を開始できません：' + e.message); stopStream(); return; }
      rec.mr = mr; rec.chunks = []; rec.owner = owner;
      if(owner.button) owner.button.classList.add('listening');
      say(owner.recordingMessage);
      mr.ondataavailable = function(ev){ if(ev.data && ev.data.size) rec.chunks.push(ev.data); };
      mr.onstop = function(){
        if(owner.button) owner.button.classList.remove('listening');
        var usedMime = mr.mimeType || mime || 'audio/mp4';
        var blob = new Blob(rec.chunks, { type: usedMime });
        rec.chunks = []; stopStream(); rec.owner = null;
        transcribe(blob, usedMime, owner);
      };
      mr.start();
    }).catch(function(e){
      say('マイクを使用できません（端末設定でマイク許可を確認）：' + e.name);
    });
  }

  /* ---- 文字起こし（Whisper・全モード共通） ------------------------------ */
  function transcribe(blob, mime, owner){
    var c = owner.conf, say = owner.status || function(){};
    var ext = mime.indexOf('mp4') >= 0 ? 'mp4' : (mime.indexOf('webm') >= 0 ? 'webm' : 'm4a');
    var fd = new FormData();
    fd.append('file', blob, 'audio.' + ext);
    fd.append('model', c.sttModel);
    fd.append('language', c.language);
    fd.append('response_format', 'json');
    say('送信中… 文字起こしを待っています。');
    fetch(c.relay + c.sttPath, { method:'POST', headers:{ 'x-trisight-code': tsCode() }, body:fd })
      .then(function(resp){ return resp.json().then(function(d){ return { ok:resp.ok, status:resp.status, d:d }; }); })
      .then(function(r){
        if(tsAuthFail(r.status)){ say('認証コード不一致。再読み込みして入力し直してください。'); return; }
        if(!r.ok || r.d.error){ say('文字起こし失敗：' + (r.d.error || ('HTTP ' + r.status))); return; }
        var txt = (r.d.text || '').trim();
        if(!txt){ say('音声を認識できませんでした。もう一度お試しください。'); return; }
        owner.onText(txt);
      })
      .catch(function(e){ say('通信エラー：' + e.message); });
  }

  /* =====================================================================
     ①② フォーム（init）
     ===================================================================== */
  var form = null;   // { conf, owner, statusTarget, … }

  function formStatus(t){
    if(!form || !form.statusTarget) return;
    var s = form.statusTarget;
    if(typeof s === 'function'){ try{ s(t); }catch(e){} }
    else if(s.textContent !== undefined){ s.textContent = t; }
  }

  function distribute(txt){
    var cfg = form.conf;
    var schemaText = cfg.schema.map(function(f){ return f.id + ' (' + f.t + '): ' + f.d; }).join('\n');
    var prompt =
      cfg.promptIntro + '\n\n' +
      '規則：\n'+
      '1) 出力はJSONオブジェクトのみ。前置き・説明・コードフェンスは付けない。\n'+
      '2) キーは項目のid。値はテキスト項目は文字列、(check)項目は該当すれば true。\n'+
      '3) 文字起こしに述べられていない項目はキーごと省く。推測で埋めない。\n'+
      '4) 数値項目は単位を付けず数字だけ。\n'+
      '5) どの欄にも当てはまらない内容は ' + cfg.overflowId + ' にまとめる。\n'+
      '6) 実名や住所など個人を特定する情報は出力に含めない（イニシャルは可）。\n\n'+
      '【項目一覧】\n' + schemaText + '\n\n【文字起こし】\n' + txt;

    fetch(cfg.relay + cfg.aiPath, {
      method:'POST', headers:{ 'Content-Type':'application/json', 'x-trisight-code': tsCode() },
      body: JSON.stringify({ model: cfg.aiModel, max_tokens: cfg.maxTokens, messages:[{ role:'user', content: prompt }] })
    })
      .then(function(resp){ return resp.json(); })
      .then(function(j){
        var out = (j && j.content && j.content[0] && j.content[0].text) || '';
        var obj = parseJSONLoose(out);
        if(!obj){ formStatus('AIの振り分け結果を読み取れませんでした。聞き取り全文から手入力してください。'); return; }
        applyFields(obj);
      })
      .catch(function(e){ formStatus('AI振り分けの通信エラー：' + e.message + '（聞き取り全文は残っています）'); });
  }

  function parseJSONLoose(t){
    if(!t) return null;
    t = t.replace(/```json/gi,'').replace(/```/g,'').trim();
    var a = t.indexOf('{'), b = t.lastIndexOf('}');
    if(a >= 0 && b > a){ t = t.slice(a, b+1); }
    try{ return JSON.parse(t); }catch(e){ return null; }
  }

  function applyFields(obj){
    var cfg = form.conf, n = 0;
    cfg.schema.forEach(function(f){
      if(!(f.id in obj)) return;
      var node = document.getElementById(f.id); if(!node) return;
      var v = obj[f.id];
      if(f.t === 'check'){
        if(v === true || v === 'true' || v === 1 || v === '1'){ node.checked = true; node.classList.add(cfg.filledClass); n++; }
      }else{
        if(v != null && String(v).trim() !== ''){
          node.value = String(v).trim();
          node.dispatchEvent(new Event('input'));
          node.classList.add(cfg.filledClass); n++;
        }
      }
    });
    if(cfg.banner){ cfg.banner.style.display = n ? '' : 'none'; }
    formStatus(n ? ('AIが ' + n + ' 項目を下書きしました。色のついた欄を必ず確認・修正してください。')
                 : 'AIは該当項目を見つけられませんでした。聞き取り全文を見て手入力してください。');
    if(typeof cfg.onApply === 'function'){ try{ cfg.onApply(n); }catch(e){} }
  }

  function init(opts){
    opts = opts || {};
    var cfg = merge(opts);

    /* モード判定：onText があれば素通し、schema があればスキーマ */
    if(typeof opts.onText === 'function'){ cfg.mode = 'passthrough'; cfg.onText = opts.onText; }
    else if(opts.schema && opts.schema.length){ cfg.mode = 'schema'; }
    else { console.warn('[TriVoice] schema も onText も無いため初期化を中止しました。'); return; }

    cfg.schema      = opts.schema || [];
    cfg.promptIntro = opts.promptIntro ||
      'あなたは記録入力の補助です。次の【文字起こし】を読み、下の【項目一覧】の各欄に該当する情報だけを抜き出し、JSONオブジェクトとして返してください。';
    cfg.overflowId  = opts.overflowId || 't_other';
    cfg.onApply     = opts.onApply || null;
    cfg.rawBox      = el(opts.rawBox) || null;
    cfg.rawDetails  = el(opts.rawDetails) || null;
    cfg.banner      = el(opts.banner) || null;
    var bannerClose = el(opts.bannerClose) || null;

    if(form && form.owner && rec.owner === form.owner){ stopRec(); }
    form = { conf: cfg, statusTarget: (typeof opts.status === 'function') ? opts.status : (el(opts.status) || null) };
    var micEl = el(opts.micButton) || null;
    form.owner = {
      button: micEl, conf: cfg, status: formStatus,
      recordingMessage: opts.recordingMessage || '録音中… 観察したこと・バイタル・ケアを続けて話してください。終わったらもう一度マイクを押します。',
      onText: function(txt){
        if(cfg.rawBox){ cfg.rawBox.value = txt; }
        if(cfg.rawDetails){ cfg.rawDetails.open = true; }
        if(cfg.mode === 'passthrough'){
          formStatus('文字起こし完了。');
          try{ cfg.onText(txt); }catch(e){ formStatus('受け渡しエラー：' + e.message); }
        }else{
          formStatus('文字起こし完了。AIが各欄へ振り分けています…');
          distribute(txt);
        }
      }
    };

    /* マイクボタン配線：トグル＋押下時にキーボードを畳む（iPad対策） */
    if(micEl){
      micEl.addEventListener('click', function(){
        if(rec.owner === form.owner && isRecording()){ stopRec(); return; }
        if(document.activeElement && document.activeElement.blur){ document.activeElement.blur(); }
        startRec(form.owner);
      });
    }
    if(bannerClose && cfg.banner){
      bannerClose.addEventListener('click', function(){ cfg.banner.style.display = 'none'; });
    }

    /* 手で直したら下書き色を外す（確認済みの合図）— スキーマモードのみ */
    if(cfg.mode === 'schema'){
      document.querySelectorAll('[data-v]').forEach(function(node){
        var ev = (node.type === 'checkbox') ? 'change' : 'input';
        node.addEventListener(ev, function(){ node.classList.remove(cfg.filledClass); });
      });
    }

    formStatus(global.MediaRecorder ? (opts.readyMessage || '準備完了。マイクを押して話してください。')
                                    : 'この端末は録音に未対応です（手入力・印刷は可能です）。');
  }

  /* =====================================================================
     ③ 口述モード（dictation）— どの画面でも使う汎用の音声入力（2026-10-15）
     ===================================================================== */
  var dict = null;   // { owner, btn, tip, last, selS, selE, exclude }

  var TEXT_TYPES = { '':1, text:1, search:1, email:1, tel:1, url:1 };
  function isTextField(n){
    if(!n || !n.tagName) return false;
    if(n.disabled || n.readOnly) return false;
    if(n.tagName === 'TEXTAREA') return true;
    if(n.tagName === 'INPUT') return !!TEXT_TYPES[(n.getAttribute('type') || '').toLowerCase()];
    return false;
  }
  function excluded(n){
    if(!dict || !dict.exclude) return false;
    try{ return !!n.closest(dict.exclude); }catch(e){ return false; }
  }

  function dictTip(t, kind){
    if(!dict) return;
    var tip = dict.tip;
    tip.textContent = t || '';
    tip.style.display = t ? 'block' : 'none';
    tip.setAttribute('data-kind', kind || '');
    clearTimeout(dict.tipTimer);
    if(t && kind === 'done'){ dict.tipTimer = setTimeout(function(){ tip.style.display = 'none'; }, 6000); }
  }

  function insertText(n, txt){
    var v = n.value || '';
    var s = (typeof dict.selS === 'number' && dict.last === n) ? dict.selS : v.length;
    var e = (typeof dict.selE === 'number' && dict.last === n) ? dict.selE : v.length;
    if(s > v.length) s = v.length; if(e > v.length) e = v.length;
    var before = v.slice(0, s), after = v.slice(e);
    var add = txt;
    if(before && !/[\s　、。,.\n]$/.test(before)){ add = (n.tagName === 'TEXTAREA' ? '\n' : '　') + add; }
    n.value = before + add + after;
    var pos = (before + add).length;
    try{ n.setSelectionRange(pos, pos); }catch(e){}
    dict.selS = dict.selE = pos;
    n.dispatchEvent(new Event('input', { bubbles:true }));
    n.dispatchEvent(new Event('change', { bubbles:true }));
    n.classList.add('tv-dict-filled');
    setTimeout(function(){ n.classList.remove('tv-dict-filled'); }, 2500);
  }

  function dictation(opts){
    opts = opts || {};
    if(dict) return;                        // 1ページ1つ
    var cfg = merge(opts);

    var css = document.createElement('style');
    css.textContent =
      '.tv-dict-btn{position:fixed;right:16px;bottom:16px;z-index:2147483000;width:56px;height:56px;border-radius:50%;border:0;'+
      'background:#c0392b;color:#fff;font-size:26px;line-height:56px;text-align:center;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.3);padding:0}'+
      '.tv-dict-btn.listening{background:#e74c3c;animation:tvDictPulse 1s infinite}'+
      '@keyframes tvDictPulse{0%{box-shadow:0 0 0 0 rgba(231,76,60,.6)}100%{box-shadow:0 0 0 16px rgba(231,76,60,0)}}'+
      '.tv-dict-tip{position:fixed;right:16px;bottom:80px;z-index:2147483000;max-width:min(340px,calc(100vw - 32px));display:none;'+
      'background:#1f2328;color:#fff;font-size:13px;line-height:1.6;padding:8px 12px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.3)}'+
      '.tv-dict-tip[data-kind="warn"]{background:#9a3412}'+
      '.tv-dict-filled{outline:2px solid #c0392b !important;outline-offset:1px}'+
      '@media print{.tv-dict-btn,.tv-dict-tip{display:none !important}}';
    document.head.appendChild(css);

    var btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'tv-dict-btn'; btn.textContent = '🎤';
    btn.title = '音声入力：文字を入れたい欄を押してから、このボタンを押して話します。もう一度押すと止まり、話した文字がその欄に入ります';
    btn.setAttribute('aria-label', '音声入力');
    var tip = document.createElement('div'); tip.className = 'tv-dict-tip'; tip.setAttribute('role', 'status');
    document.body.appendChild(tip); document.body.appendChild(btn);

    dict = { btn: btn, tip: tip, last: null, lastEx: false, selS: null, selE: null, exclude: opts.exclude || '' };

    /* 最後に押した入力欄と、カーソルの位置を覚えておく */
    function remember(n){
      if(!isTextField(n)) return;
      if(excluded(n)){ dict.last = null; dict.lastEx = true; return; }
      dict.last = n; dict.lastEx = false;
      try{ dict.selS = n.selectionStart; dict.selE = n.selectionEnd; }catch(e){ dict.selS = dict.selE = null; }
    }
    document.addEventListener('focusin', function(ev){ remember(ev.target); }, true);
    document.addEventListener('focusout', function(ev){ if(ev.target === dict.last) remember(ev.target); }, true);
    document.addEventListener('keyup', function(ev){ if(ev.target === dict.last) remember(ev.target); }, true);
    document.addEventListener('mouseup', function(ev){ if(ev.target === dict.last) remember(ev.target); }, true);
    document.addEventListener('selectionchange', function(){ if(dict.last && document.activeElement === dict.last) remember(dict.last); });
    /* マイクを押しても入力欄から外れないようにする（カーソル位置を保つ） */
    btn.addEventListener('mousedown', function(ev){ ev.preventDefault(); });

    dict.owner = {
      button: btn, conf: cfg,
      status: function(t){ dictTip(t, /失敗|エラー|できません|未対応|不一致|認識できません/.test(t) ? 'warn' : ''); },
      recordingMessage: '録音中… 話し終えたら、もう一度マイクを押してください。',
      onText: function(txt){
        var n = dict.last;
        if(!n || !document.body.contains(n) || !isTextField(n) || excluded(n)){
          dictTip('文字を入れる欄が見つかりませんでした。聞き取った文字：' + txt, 'warn'); return;
        }
        insertText(n, txt);
        dictTip('「' + (txt.length > 40 ? txt.slice(0, 40) + '…' : txt) + '」を入れました。違っていれば手で直してください。', 'done');
      }
    };

    btn.addEventListener('click', function(){
      if(rec.owner === dict.owner && isRecording()){ stopRec(); return; }
      if(document.activeElement && isTextField(document.activeElement)) remember(document.activeElement);
      var n = dict.last;
      if(!n && dict.lastEx){
        dictTip('この欄は音声入力の対象外です（個人の情報を外へ送らない欄のため）。手で入力してください。', 'warn'); return;
      }
      if(!n || !document.body.contains(n) || !isTextField(n)){
        dictTip('文字を入れたい欄を先に押してから、マイクを押してください。', 'warn'); return;
      }
      if(excluded(n)){
        dictTip('この欄は音声入力の対象外です（個人の情報を外へ送らない欄のため）。手で入力してください。', 'warn'); return;
      }
      startRec(dict.owner);
    });
  }

  /* ---- 公開API --------------------------------------------------------- */
  global.TriVoice = {
    init:      init,        // ①② フォーム初期化
    dictation: dictation,   // ③ 汎用の音声入力（画面右下のマイク）
    stop:      stopRec,     // 録音停止（印刷・クリア前に呼ぶ）
    version:   '2.0'
  };

})(window);
