/* ===========================================================================
 *  TriSheetSync.js — 基本情報シート（元帳 trisight_office_master_v1）を
 *  認証コードで端末どうし共有する部品（2026-10-19・宏史さんの指示）
 *  ---------------------------------------------------------------------------
 *  ・同じ認証コードを入れた端末どうしで、登録した会社（自社・顧客）と職員名簿を同じにする。
 *  ・共有するかどうかは端末ごとに決める（基本情報シートの「この端末と共有」で印を付けた端末だけ）。
 *    印を付けない端末は、これまでどおり端末の中だけに置く。
 *  ・受け渡しはトライタイムと同じ中継（api/gate の task "tritime"）の、種類 "sheet" を使う。
 *    1社＝1件。会社ごとに時刻（upd）を付け、新しい方を残す。
 *  ・利用者の記録（アセスメント等）は送らない。送る前に必ず抜く（トライケア側の持ち物のため）。
 *  ・この部品を読み込んだ画面は、開いたときと、開いている間1分ごとに共有する。
 *    他の端末で直した内容が届いたら、画面の下に「読み込み直す」の帯を出す（作業中の入力を消さないため、
 *    自動では読み込み直さない）。
 * ========================================================================= */
(function(){
  'use strict';
  var MKEY = 'trisight_office_master_v1';
  var SHARE_KEY = 'trisheet_share';
  var STATE_KEY = 'trisheet_sync';
  var LOCK_KEY = 'trisheet_sync_lock';   /* 同じ端末で複数の画面を開いていても、共有は1つの画面だけが行う */
  var ME = 'p' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  var DEF_URL = 'https://trisight-relay.vercel.app/api/gate';
  var busy = false, timer = null, opts = { notify:true, onPulled:null, onStatus:null };
  /* 2026-10-27：画面のアドレスの後ろに ?hold=1 を付けて開いたときは、共有（送る・受け取る）を止める。
     ほかの端末から古い版が届いて、この端末に残っている正しい版を上書きしないようにするための開き方。
     送るのは、人が「この端末の情報を、共有の正しい版として送る」を押したとき（forceSend）だけ。 */
  var HOLD = /[?&]hold=1(&|$)/.test(location.search);

  function lj(k, d){ try{ var v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); }catch(e){ return d; } }
  function sj(k, v){ try{ localStorage.setItem(k, JSON.stringify(v)); return true; }catch(e){ return false; } }
  function relayUrl(){ var u = lj('trisheet_relay', '') || lj('tritime_relay', ''); return u || DEF_URL; }
  function enabled(){ try{ return localStorage.getItem(SHARE_KEY) === '1'; }catch(e){ return false; } }
  function state(){ var s = lj(STATE_KEY, {}); s.h = s.h || {}; s.u = s.u || {}; return s; }

  /* 文字列の指紋（変わったかどうかを見るだけ。暗号の用途ではない） */
  function fp(str){ var h = 5381, i = str.length; while(i) h = (h * 33) ^ str.charCodeAt(--i); return (h >>> 0).toString(36) + ':' + str.length; }

  /* 送る前に、利用者の記録を抜く（元帳の中に古い形で残っていても、外へは出さない） */
  function clean(org){
    var o = JSON.parse(JSON.stringify(org || {}));
    var K = 'アセスメント対象の利用者';
    var strip = function(j){ if(j && typeof j === 'object'){ delete j[K]; } };
    if(o.sheet){
      delete o.sheet.users; delete o.sheet.useCare;
      strip(o.sheet.BASE);
      (o.sheet.offices || []).forEach(function(of){ if(of) delete of.asm; });
    }
    strip(o.gateJSON);
    return o;
  }
  function readDoc(){ var d = lj(MKEY, null); return (d && Array.isArray(d.orgs)) ? d : null; }
  function blankDoc(){ return { version:2, activeOrg:'', orgs:[], updated:'' }; }

  function tsCode(ask){
    var c = null; try{ c = localStorage.getItem('trisight_access_code'); }catch(e){}
    if(c && /[^\x21-\x7E]/.test(c)){ try{ localStorage.removeItem('trisight_access_code'); }catch(e){} c = null; }
    while(!c && ask){
      c = prompt('TriSight 認証コードを入力してください（この端末での初回のみ・半角英数字）');
      if(c === null) return '';
      c = c.trim();
      if(c === '' || /[^\x21-\x7E]/.test(c)){ alert('認証コードは半角英数字で入力してください（全角文字・日本語・空白は使えません）。'); c = null; continue; }
      try{ localStorage.setItem('trisight_access_code', c); }catch(e){}
    }
    return c || '';
  }
  function call(op, extra, ask){
    var code = tsCode(ask);
    if(!code) return Promise.reject(new Error('認証コードが入っていないため、共有できません。'));
    var payload = Object.assign({ op:op }, extra || {});
    return fetch(relayUrl(), { method:'POST', headers:{ 'Content-Type':'application/json', 'x-trisight-code':code }, body:JSON.stringify({ task:'tritime', payload:payload }) })
      .then(function(res){
        return res.json().catch(function(){ return null; }).then(function(j){
          if(res.status === 401){ try{ localStorage.removeItem('trisight_access_code'); }catch(e){} throw new Error('認証コードが一致しませんでした。画面を開き直して、正しいコードを入れてください。'); }
          if(!res.ok || !j || !j.ok){
            var m = (j && j.error) ? String(j.error) : ('中継の応答 ' + res.status);
            if(/種類が正しくありません/.test(m)) m = '中継に、基本情報シートの受け口がまだありません（中継の更新が済むと共有が始まります）。';
            throw new Error(m);
          }
          return j;
        });
      }, function(){ throw new Error('中継につながりませんでした。通信の状態を確かめてください。'); });
  }

  /* この端末で変わった会社を、送る件にする */
  function collect(doc, s, now){
    var items = [], seen = {};
    (doc ? doc.orgs : []).forEach(function(o){
      if(!o || !o.id) return;
      var id = 'org:' + o.id; seen[id] = 1;
      var c = clean(o), h = fp(JSON.stringify(c));
      if(s.h[id] === h) return;
      items.push({ col:'sheet', id:id, data:{ id:id, upd:now, org:c }, h:h });
    });
    Object.keys(s.h).forEach(function(id){
      if(id.indexOf('org:') !== 0 || seen[id] || s.h[id] === 'del') return;
      items.push({ col:'sheet', id:id, data:{ id:id, upd:now, del:true }, h:'del' });
    });
    var self = doc ? (doc.activeOrg || '') : '';
    var hs = fp('self:' + self);
    if(doc && !s.pendSelf && s.h.__self !== hs) items.push({ col:'sheet', id:'__self', data:{ id:'__self', upd:now, activeOrg:self }, h:hs });
    return items;
  }

  /* 他の端末から届いた件を、この端末の元帳へ入れる。戻り値＝入れた件数 */
  function merge(items, s){
    var doc = readDoc() || blankDoc(), n = 0;
    /* 2026-10-26：「自社」の印（__self）は、会社の中身より後に入れる。
       印の指す会社がまだ届いていなければ捨てずに覚えておき（s.pendSelf）、会社が届いたときに付ける。 */
    items = (items || []).slice().sort(function(a, b){ return (String(a && a.id) === '__self') - (String(b && b.id) === '__self'); });
    items.forEach(function(it){
      var d = it && it.data; if(!d || it.col !== 'sheet') return;
      var id = String(it.id || d.id || ''), upd = Number(d.upd) || 0;
      if(upd <= (s.u[id] || 0)) return;   /* この端末が知っている版と同じか古い */
      if(id === '__self'){
        s.u[id] = upd; s.h[id] = fp('self:' + (d.activeOrg || ''));
        if(doc.orgs.some(function(o){ return o.id === d.activeOrg; }) || !d.activeOrg){ doc.activeOrg = d.activeOrg || ''; delete s.pendSelf; }
        else s.pendSelf = d.activeOrg;
        n++; return;
      }
      if(id.indexOf('org:') !== 0) return;
      var oid = id.slice(4), i = -1;
      doc.orgs.forEach(function(o, k){ if(o && o.id === oid) i = k; });
      if(d.del){
        if(i >= 0){ doc.orgs.splice(i, 1); n++; }
        s.h[id] = 'del'; s.u[id] = upd; return;
      }
      if(!d.org) return;
      var org = d.org; org.id = oid;
      if(i >= 0) doc.orgs[i] = org; else doc.orgs.push(org);
      s.h[id] = fp(JSON.stringify(clean(org))); s.u[id] = upd; n++;
    });
    if(s.pendSelf && doc.orgs.some(function(o){ return o.id === s.pendSelf; })){ doc.activeOrg = s.pendSelf; delete s.pendSelf; n++; }
    if(n){
      if(doc.activeOrg && !doc.orgs.some(function(o){ return o.id === doc.activeOrg; })) doc.activeOrg = '';
      if(!doc.activeOrg){ var f = doc.orgs.filter(function(o){ return o.role !== 'client'; })[0]; doc.activeOrg = f ? f.id : ''; }
      doc.updated = new Date().toLocaleString('ja-JP');
      if(!sj(MKEY, doc)) throw new Error('届いた会社の情報を、この端末に保存できませんでした（ブラウザの保存の容量を超えています）。');
    }
    return n;
  }

  /* 初めて共有に入る端末：先に受け取り、同じ番号で中身の違う会社は、この端末の方の番号を付け替える
     （古い形から移した会社は、どの端末でも "org1" の番号になっているため） */
  function firstJoin(s){
    return call('pull', { since:0, cols:['sheet'] }, true).then(function(j){
      var items = Array.isArray(j.items) ? j.items : [];
      var doc = readDoc();
      if(doc){
        var remote = {};
        items.forEach(function(it){ if(it && it.data && it.data.org && String(it.id).indexOf('org:') === 0) remote[String(it.id).slice(4)] = it.data.org; });
        var nameOf = function(o){ return (o && o.corp && o.corp.name) || (o && o.sheet && o.sheet.val && o.sheet.val['法人名']) || ''; };
        var moved = false;
        doc.orgs.forEach(function(o){
          var r = o && remote[o.id];
          if(!r || nameOf(r) === nameOf(o)) return;
          var nid = 'o' + Date.now().toString(36) + Math.floor(Math.random() * 1e6).toString(36);
          if(doc.activeOrg === o.id) doc.activeOrg = nid;
          if(doc.sheetOrg === o.id) doc.sheetOrg = nid;
          o.id = nid; moved = true;
        });
        if(moved) sj(MKEY, doc);
      }
      var n = merge(items, s);
      s.since = j.now || 0; s.joined = true;
      return n;
    });
  }

  function status(msg, err){
    var s = state(); s.err = err ? msg : ''; if(!err) s.last = Date.now(); sj(STATE_KEY, s);
    if(typeof opts.onStatus === 'function'){ try{ opts.onStatus(info()); }catch(e){} }
  }
  function info(){ var s = state(); return { enabled:enabled(), last:s.last || 0, err:s.err || '' }; }

  function lock(){
    var l = lj(LOCK_KEY, null), now = Date.now();
    if(l && l.by !== ME && now - (l.t || 0) < 60000) return false;   /* 他の画面が共有している最中（1分で失効） */
    sj(LOCK_KEY, { by:ME, t:now });
    var c = lj(LOCK_KEY, null); return !!(c && c.by === ME);
  }
  function unlock(){ var l = lj(LOCK_KEY, null); if(l && l.by === ME){ try{ localStorage.removeItem(LOCK_KEY); }catch(e){} } }
  function syncNow(ask, force){
    if(!enabled() || busy) return Promise.resolve(0);
    if(HOLD && !force) return Promise.resolve(0);
    if(!lock()) return Promise.resolve(0);
    busy = true;
    var s = state(), got = 0;
    var start = s.joined ? Promise.resolve(0) : firstJoin(s);
    return start.then(function(n){
      got += n; sj(STATE_KEY, s);
      var now = Date.now(), items = collect(readDoc(), s, now);
      var chain = Promise.resolve();
      /* 1社ずつ送る（1件が大きいため） */
      items.forEach(function(it){
        chain = chain.then(function(){
          return call('push', { items:[{ col:it.col, id:it.id, data:it.data }] }, ask).then(function(){ s.h[it.id] = it.h; s.u[it.id] = now; sj(STATE_KEY, s); });
        });
      });
      return chain;
    }).then(function(){
      return call('pull', { since:s.since || 0, cols:['sheet'] }, ask);
    }).then(function(j){
      got += merge(Array.isArray(j.items) ? j.items : [], s);
      s.since = j.now || s.since || 0; sj(STATE_KEY, s);
      status('', false);
      if(got) pulled();
      return got;
    }).catch(function(e){
      sj(STATE_KEY, s); status(e.message, true); return 0;
    }).then(function(n){ busy = false; unlock(); return n; });
  }

  function pulled(){
    if(typeof opts.onPulled === 'function'){ try{ opts.onPulled(); }catch(e){} }
    if(opts.notify) showBar();
  }
  function showBar(){
    if(document.getElementById('tssBar')) return;
    var bar = document.createElement('div');
    bar.id = 'tssBar'; bar.setAttribute('role', 'status');
    bar.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:9998;background:#1f3a2e;color:#fff;padding:12px 16px;font-size:14px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;box-shadow:0 -2px 12px rgba(0,0,0,.25)';
    var m = document.createElement('span'); m.style.flex = '1 1 auto';
    m.textContent = '他の端末で直した会社の情報（基本情報シート）が届きました。読み込み直すと、この画面に映ります。';
    var go = document.createElement('button'); go.type = 'button'; go.textContent = '読み込み直す';
    go.style.cssText = 'padding:6px 16px;border:0;border-radius:6px;background:#fff;color:#1f3a2e;font-weight:700;cursor:pointer';
    go.onclick = function(){ location.reload(); };
    var later = document.createElement('button'); later.type = 'button'; later.textContent = 'あとで';
    later.style.cssText = 'padding:6px 14px;border:1px solid rgba(255,255,255,.5);border-radius:6px;background:transparent;color:#fff;cursor:pointer';
    later.onclick = function(){ bar.remove(); };
    bar.appendChild(m); bar.appendChild(go); bar.appendChild(later);
    document.body.appendChild(bar);
  }

  function setEnabled(on){
    try{ localStorage.setItem(SHARE_KEY, on ? '1' : '0'); }catch(e){}
    if(on){ tsCode(true); return syncNow(true); }
    status('', false); return Promise.resolve(0);
  }
  function soon(){ if(!enabled()) return; clearTimeout(timer); timer = setTimeout(function(){ syncNow(false); }, 1500); }
  function init(o){
    opts = Object.assign(opts, o || {});
    if(!enabled()) return;
    var go = function(){ syncNow(false); };
    if(document.readyState === 'complete') setTimeout(go, 300); else window.addEventListener('load', function(){ setTimeout(go, 300); });
    setInterval(function(){ if(document.visibilityState === 'visible') syncNow(false); }, 60000);
    document.addEventListener('visibilitychange', function(){ if(document.visibilityState === 'visible') syncNow(false); });
  }

  /* この端末にある会社（orgId）の中身を、時刻を今にして送り直す。中継の版は、これで置き換わる */
  function forceSend(orgId){
    if(!enabled()) return Promise.reject(new Error('この端末は、基本情報シートの共有の印が付いていません。'));
    var id = 'org:' + orgId, doc = readDoc(), org = doc && doc.orgs.filter(function(o){ return o && o.id === orgId; })[0];
    if(!org) return Promise.reject(new Error('この端末に、その会社の登録がありません。'));
    var c = clean(org), h = fp(JSON.stringify(c)), upd = 0;
    /* 中継にある版より必ず新しい時刻で送る（端末の時計がずれていても負けないように） */
    return call('pull', { since:0, cols:['sheet'] }, true).then(function(j){
      (j.items || []).forEach(function(it){ if(String(it.id) === id && it.data) upd = Math.max(upd, Number(it.data.upd) || 0); });
      upd = Math.max(Date.now(), upd + 1);
      return call('push', { items:[{ col:'sheet', id:id, data:{ id:id, upd:upd, org:c } }] }, true);
    }).then(function(){
      return call('pull', { since:0, cols:['sheet'] }, true);
    }).then(function(j){
      var it = (j.items || []).filter(function(x){ return String(x.id) === id; })[0];
      if(!it || !it.data || !it.data.org || fp(JSON.stringify(clean(it.data.org))) !== h) throw new Error('中継の版が置き換わっていません。もう一度押してください。');
      var s = state(); s.joined = true; s.h[id] = h; s.u[id] = upd; sj(STATE_KEY, s); status('', false);
      return 1;
    });
  }
  /* 2026-10-27：同じ名前の会社を一つにまとめたあと、その結果（消した会社・自社の印）を一度だけ送り、中継の版で確かめる */
  function forceSync(keepId, goneIds){
    if(!enabled()) return Promise.reject(new Error('この端末は、基本情報シートの共有の印が付いていません。'));
    var s = state(); s.joined = true; sj(STATE_KEY, s);
    (goneIds || []).forEach(function(g){ if(!s.h['org:' + g]) s.h['org:' + g] = 'x'; });   /* 中継にあるかもしれない会社は、消した印を必ず送る */
    s.h.__self = ''; delete s.pendSelf; sj(STATE_KEY, s);
    busy = false; try{ localStorage.removeItem(LOCK_KEY); }catch(e){}
    return syncNow(true, true).then(function(){
      var e = state().err; if(e) throw new Error(e);
      return call('pull', { since:0, cols:['sheet'] }, true);
    }).then(function(j){
      var items = j.items || [], byId = {};
      items.forEach(function(it){ byId[String(it.id)] = it.data || {}; });
      var bad = [];
      if(!byId.__self || byId.__self.activeOrg !== keepId) bad.push('自社の印');
      (goneIds || []).forEach(function(g){ var x = byId['org:' + g]; if(x && !x.del) bad.push('消した会社'); });
      if(!byId['org:' + keepId] || byId['org:' + keepId].del) bad.push('残す会社');
      if(bad.length) throw new Error('中継の版が、まとめた結果になっていません（' + bad.join('・') + '）。もう一度押してください。');
      return true;
    });
  }
  window.TriSheetSync = { init:init, syncNow:syncNow, soon:soon, enabled:enabled, setEnabled:setEnabled, info:info, showBar:showBar, held:HOLD, forceSend:forceSend, forceSync:forceSync };
})();
