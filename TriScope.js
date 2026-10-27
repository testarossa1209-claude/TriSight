/* ============================================================
   TriScope.js ― 認証コードで使える製品（契約の範囲）を確かめる共通部品　版 2026-10-28-01
   ------------------------------------------------------------
   2026-10-28（宏史さんの決定）：製品の範囲を認証コードに紐づける。
   ・リレー（api/gate.js の task 'scope'）に「この認証コードで使える製品」を尋ね、
     その画面の製品が範囲に無ければ、画面の上に「ご契約の範囲外です」を出して使えなくする。
   ・セット契約の決まりはリレー側（lib/codes.js の BUNDLES）が持つ。
     トライサイト＝全製品／トライゲイト＝トライフォーム・トライタスク付き／トライタイム＝トライケア付き。
   ・訪問先などで通信できないときは、前に確かめた結果（この端末に控えたもの）で判断する。
     一度も確かめていない端末で通信できないときは止めずに使わせ、次に通信できたときに確かめる
     （訪問中の記録を、通信の具合で書けなくしないため）。
   ・認証コードは各画面と同じ置き場所（trisight_access_code）を使う。トライタイムで入れた端末なら、もう一度は聞かない。
   使い方：TriScope.check('tricare').then(function(r){ r.products … });
          TriScope.has('tricare') … 前に確かめた結果で、その製品が範囲にあるか（未確認なら true）
   ============================================================ */
(function(){
  var GATE = 'https://trisight-relay.vercel.app/api/gate';
  var CODE_KEY = 'trisight_access_code', CACHE_KEY = 'trisight_scope_v1';
  var NAMES = { trisight:'トライサイト', trigate:'トライゲイト', triform:'トライフォーム', tritask:'トライタスク',
    trireward:'トライリワード', tritime:'トライタイム', tricare:'トライケア' };
  function ls(k){ try{ return localStorage.getItem(k); }catch(e){ return null; } }
  function lsSet(k, v){ try{ if(v == null) localStorage.removeItem(k); else localStorage.setItem(k, v); }catch(e){} }
  function code(ask){
    var c = ls(CODE_KEY);
    if(c && /[^\x21-\x7E]/.test(c)){ lsSet(CODE_KEY, null); c = null; }
    while(!c && ask){
      c = prompt('TriSight 認証コードを入力してください（この端末での初回のみ・半角英数字）');
      if(c === null) return '';
      c = c.trim();
      if(c === '' || /[^\x21-\x7E]/.test(c)){ alert('認証コードは半角英数字で入力してください（全角文字・日本語・空白は使えません）。'); c = null; continue; }
      lsSet(CODE_KEY, c);
    }
    return c || '';
  }
  /* 控えはコードの頭と尻だけで照合する（コードの全文を二重に置かない） */
  function tag(c){ c = String(c || ''); return c.length + ':' + c.slice(0, 4) + c.slice(-3); }
  function cached(){
    var j = null; try{ j = JSON.parse(ls(CACHE_KEY) || 'null'); }catch(e){ j = null; }
    return (j && j.tag === tag(code(false)) && Array.isArray(j.products)) ? j : null;
  }
  function overlay(product, kind){
    var id = 'triScopeBlock', el = document.getElementById(id);
    if(!el){ el = document.createElement('div'); el.id = id; document.body.appendChild(el); }
    el.setAttribute('style', 'position:fixed;inset:0;z-index:99999;background:rgba(16,36,59,.92);display:flex;align-items:center;justify-content:center;padding:16px;box-sizing:border-box;font-family:inherit');
    var nm = NAMES[product] || product, msg;
    if(kind === 'nocode') msg = '<b>認証コードが入っていません。</b><br>' + nm + 'を使うには、ご契約の認証コードを入れてください。';
    else if(kind === 'badcode') msg = '<b>認証コードが一致しませんでした。</b><br>正しい認証コードを入れ直してください。';
    else msg = '<b>この認証コードのご契約には「' + nm + '」が含まれていません。</b><br>' + nm + 'をお使いになるには、ご契約の範囲の変更が必要です。お取引先の代理店、または合同会社トライサイトへご連絡ください。';
    el.innerHTML = '<div style="background:#fff;color:#1f2328;max-width:460px;width:100%;border-radius:14px;padding:20px 18px;line-height:1.7;font-size:15px">' + msg +
      '<div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">' +
      '<button type="button" id="triScopeRe" style="font:inherit;font-size:14px;font-weight:700;border:1px solid #10243b;background:#10243b;color:#fff;padding:8px 14px;border-radius:10px;cursor:pointer">認証コードを入れ直す</button>' +
      '<button type="button" id="triScopeBack" style="font:inherit;font-size:14px;border:1px solid #afb8c1;background:#fff;color:#1f2328;padding:8px 14px;border-radius:10px;cursor:pointer">前のページに戻る</button></div></div>';
    document.getElementById('triScopeRe').onclick = function(){ lsSet(CODE_KEY, null); lsSet(CACHE_KEY, null); location.reload(); };
    document.getElementById('triScopeBack').onclick = function(){ if(history.length > 1) history.back(); else location.href = 'index.html'; };
  }
  function clearOverlay(){ var el = document.getElementById('triScopeBlock'); if(el) el.remove(); }
  function ready(fn){ if(document.body) fn(); else document.addEventListener('DOMContentLoaded', fn); }

  var TriScope = {
    names: NAMES,
    has: function(product){ var c = cached(); return !c || c.products.indexOf(product) >= 0; },
    check: function(product){
      var c = code(true);
      if(!c){ ready(function(){ overlay(product, 'nocode'); }); return Promise.resolve({ ok:false, why:'nocode', products:[] }); }
      var ctl = (typeof AbortController === 'function') ? new AbortController() : null;
      var timer = ctl ? setTimeout(function(){ try{ ctl.abort(); }catch(e){} }, 10000) : null;
      return fetch(GATE, { method:'POST', headers:{ 'Content-Type':'application/json', 'x-trisight-code':c },
        body:JSON.stringify({ task:'scope' }), signal: ctl ? ctl.signal : undefined })
        .then(function(res){
          if(timer) clearTimeout(timer);
          if(res.status === 401){ lsSet(CACHE_KEY, null); ready(function(){ overlay(product, 'badcode'); }); return { ok:false, why:'badcode', products:[] }; }
          return res.json().then(function(j){
            if(!res.ok || !j || !j.ok || !Array.isArray(j.products)) throw new Error('scope');
            lsSet(CACHE_KEY, JSON.stringify({ tag:tag(c), products:j.products, limited:!!j.limited, at:Date.now() }));
            if(j.products.indexOf(product) < 0){ ready(function(){ overlay(product, 'out'); }); return { ok:false, why:'out', products:j.products }; }
            ready(clearOverlay);
            return { ok:true, products:j.products, limited:!!j.limited };
          });
        })
        .catch(function(){
          if(timer) clearTimeout(timer);
          var k = cached();
          if(k && k.products.indexOf(product) < 0){ ready(function(){ overlay(product, 'out'); }); return { ok:false, why:'out', products:k.products, offline:true }; }
          return { ok:true, products: k ? k.products : null, offline:true };
        });
    }
  };
  window.TriScope = TriScope;
})();
