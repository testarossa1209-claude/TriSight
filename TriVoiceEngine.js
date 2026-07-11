/*! ===========================================================================
 *  TriVoiceEngine.js  —  TriSight® 横串・共通音声エンジン（正）
 *  ---------------------------------------------------------------------------
 *  役割：録音 → リレー → 文字起こし(Whisper) → ［任意］AI構造化(Claude) → 落とし込み
 *  構成：iPad Safari でも確実に動く MediaRecorder 方式。
 *        ブラウザの音声認識(Web Speech API)は使わない。
 *
 *  落とす先は2モード（同じエンジン・出口だけ差し替え）：
 *    ① スキーマモード … 多欄フォーム（看護記録・会議記録 等）。
 *                       schema を渡すと STT→AI構造化→各DOM欄へ自動振り分け。
 *    ② 素通しモード   … 単一入力欄（本体あずさ 等）。
 *                       onText を渡すと STT結果をそのまま渡す（AI構造化は省く）。
 *
 *  使い方（最小）：
 *    TriVoice.init({ micButton:'#btnMic', status:'#status',
 *                    schema: FORM_SCHEMA, promptIntro:'…' });        // ①
 *    TriVoice.init({ micButton:'#btnMic',
 *                    onText:function(t){ box.value += t; } });        // ②
 *
 *  依存なし。1ページ1フォーム前提（エンジン状態はモジュール内シングルトン）。
 * ========================================================================= */
(function (global) {
  'use strict';

  /* ---- 既定値（必要なら init で上書き） ---------------------------------- */
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


  /* ---- 内部状態（1ページ1インスタンス） -------------------------------- */
  var cfg = null;
  var micEl = null, statusTarget = null;
  var mediaRecorder = null, recChunks = [], currentStream = null, listening = false;

  /* ---- ユーティリティ --------------------------------------------------- */
  function el(sel){ return (typeof sel === 'string') ? document.querySelector(sel) : sel; }

  function setStatus(t){
    if(!statusTarget) return;
    if(typeof statusTarget === 'function'){ try{ statusTarget(t); }catch(e){} }
    else if(statusTarget.textContent !== undefined){ statusTarget.textContent = t; }
  }

  function pickMime(){
    var prefs = ['audio/mp4', 'audio/aac', 'audio/webm']; // iOS Safari は mp4
    if(global.MediaRecorder){
      for(var i=0;i<prefs.length;i++){
        try{ if(MediaRecorder.isTypeSupported(prefs[i])) return prefs[i]; }catch(e){}
      }
    }
    return ''; // 未指定＝ブラウザ既定に委ねる
  }

  function stopStream(){
    if(currentStream){ currentStream.getTracks().forEach(function(t){ t.stop(); }); currentStream = null; }
  }

  /* 録音中なら止める（印刷・クリア前などに外部から呼べる） */
  function stopRec(){
    if(mediaRecorder && mediaRecorder.state !== 'inactive'){ try{ mediaRecorder.stop(); }catch(e){} }
    stopStream();
    if(micEl){ micEl.classList.remove('listening'); }
    listening = false;
  }

  /* ---- 録音開始 --------------------------------------------------------- */
  function startRec(){
    if(!global.MediaRecorder || !navigator.mediaDevices){
      setStatus('この端末は録音に未対応です（手入力・印刷は可能です）。'); return;
    }
    if(listening){ stopRec(); return; }       // トグル：録音中の再押下で停止

    navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream){
      currentStream = stream;
      var mime = pickMime();
      try{
        mediaRecorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      }catch(e){ setStatus('録音を開始できません：' + e.message); stopStream(); return; }
      recChunks = [];
      listening = true;
      if(micEl) micEl.classList.add('listening');
      setStatus(cfg.msgRecording);
      mediaRecorder.ondataavailable = function(ev){ if(ev.data && ev.data.size) recChunks.push(ev.data); };
      mediaRecorder.onstop = function(){
        if(micEl) micEl.classList.remove('listening');
        listening = false;
        var usedMime = (mediaRecorder && mediaRecorder.mimeType) || mime || 'audio/mp4';
        var blob = new Blob(recChunks, { type: usedMime });
        recChunks = []; stopStream();
        transcribe(blob, usedMime);
      };
      mediaRecorder.start();
    }).catch(function(e){
      setStatus('マイクを使用できません（端末設定でマイク許可を確認）：' + e.name);
    });
  }

  /* ---- ① 文字起こし（Whisper） ----------------------------------------- */
  function transcribe(blob, mime){
    var ext = mime.indexOf('mp4') >= 0 ? 'mp4' : (mime.indexOf('webm') >= 0 ? 'webm' : 'm4a');
    var fd = new FormData();
    fd.append('file', blob, 'audio.' + ext);
    fd.append('model', cfg.sttModel);
    fd.append('language', cfg.language);
    fd.append('response_format', 'json');
    setStatus('送信中… 文字起こしを待っています。');
    fetch(cfg.relay + cfg.sttPath, { method:'POST', headers:{ 'x-trisight-code': tsCode() }, body:fd })
      .then(function(resp){ return resp.json().then(function(d){ return { ok:resp.ok, status:resp.status, d:d }; }); })
      .then(function(r){
        if(tsAuthFail(r.status)){ setStatus('認証コード不一致。再読み込みして入力し直してください。'); return; }
        if(!r.ok || r.d.error){ setStatus('文字起こし失敗：' + (r.d.error || ('HTTP ' + r.status))); return; }
        var txt = (r.d.text || '').trim();
        if(!txt){ setStatus('音声を認識できませんでした。もう一度お試しください。'); return; }

        if(cfg.rawBox){ cfg.rawBox.value = txt; }
        if(cfg.rawDetails){ cfg.rawDetails.open = true; }

        if(cfg.mode === 'passthrough'){
          /* ② 素通し：STT結果をそのまま呼び元へ（AI構造化なし） */
          setStatus('文字起こし完了。');
          try{ cfg.onText(txt); }catch(e){ setStatus('受け渡しエラー：' + e.message); }
        }else{
          /* ① スキーマ：AIで各欄へ振り分け */
          setStatus('文字起こし完了。AIが各欄へ振り分けています…');
          distribute(txt);
        }
      })
      .catch(function(e){ setStatus('通信エラー：' + e.message); });
  }

  /* ---- ① AI構造化（Claude経由で各欄へ振り分け） ------------------------ */
  function distribute(txt){
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
        if(!obj){ setStatus('AIの振り分け結果を読み取れませんでした。聞き取り全文から手入力してください。'); return; }
        applyFields(obj);
      })
      .catch(function(e){ setStatus('AI振り分けの通信エラー：' + e.message + '（聞き取り全文は残っています）'); });
  }

  function parseJSONLoose(t){
    if(!t) return null;
    t = t.replace(/```json/gi,'').replace(/```/g,'').trim();
    var a = t.indexOf('{'), b = t.lastIndexOf('}');
    if(a >= 0 && b > a){ t = t.slice(a, b+1); }
    try{ return JSON.parse(t); }catch(e){ return null; }
  }

  function applyFields(obj){
    var n = 0;
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
    setStatus(n ? ('AIが ' + n + ' 項目を下書きしました。色のついた欄を必ず確認・修正してください。')
                : 'AIは該当項目を見つけられませんでした。聞き取り全文を見て手入力してください。');
    if(typeof cfg.onApply === 'function'){ try{ cfg.onApply(n); }catch(e){} }
  }

  /* ---- 初期化 ----------------------------------------------------------- */
  function init(opts){
    opts = opts || {};
    cfg = {};
    for(var k in DEFAULTS){ cfg[k] = (k in opts) ? opts[k] : DEFAULTS[k]; }

    /* モード判定：onText があれば素通し、schema があればスキーマ */
    if(typeof opts.onText === 'function'){ cfg.mode = 'passthrough'; cfg.onText = opts.onText; }
    else if(opts.schema && opts.schema.length){ cfg.mode = 'schema'; }
    else { console.warn('[TriVoice] schema も onText も無いため初期化を中止しました。'); return; }

    cfg.schema      = opts.schema || [];
    cfg.promptIntro = opts.promptIntro ||
      'あなたは記録入力の補助です。次の【文字起こし】を読み、下の【項目一覧】の各欄に該当する情報だけを抜き出し、JSONオブジェクトとして返してください。';
    cfg.overflowId  = opts.overflowId || 't_other';
    cfg.onApply     = opts.onApply || null;

    cfg.msgRecording = opts.recordingMessage ||
      '録音中… 観察したこと・バイタル・ケアを続けて話してください。終わったらもう一度マイクを押します。';

    /* UI要素の解決（いずれも任意。無ければその機能だけ静かに省く） */
    micEl        = el(opts.micButton) || null;
    statusTarget = (typeof opts.status === 'function') ? opts.status : (el(opts.status) || null);
    cfg.rawBox     = el(opts.rawBox) || null;
    cfg.rawDetails = el(opts.rawDetails) || null;
    cfg.banner     = el(opts.banner) || null;
    var bannerClose = el(opts.bannerClose) || null;

    /* マイクボタン配線：トグル＋押下時にキーボードを畳む（iPad対策） */
    if(micEl){
      micEl.addEventListener('click', function(){
        if(listening){ stopRec(); return; }
        if(document.activeElement && document.activeElement.blur){ document.activeElement.blur(); }
        startRec();
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

    setStatus(global.MediaRecorder ? (opts.readyMessage || '準備完了。マイクを押して話してください。')
                                   : 'この端末は録音に未対応です（手入力・印刷は可能です）。');
  }

  /* ---- 公開API --------------------------------------------------------- */
  global.TriVoice = {
    init:    init,        // フォーム初期化
    stop:    stopRec,     // 録音停止（印刷・クリア前に呼ぶ）
    version: '1.0'
  };

})(window);
