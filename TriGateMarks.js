/*! ===========================================================================
 *  TriGateMarks.js — トライゲイト：印の付いた案件の隠し方と、額の確かめ
 *  版：2026-10-19-01
 *  ---------------------------------------------------------------------------
 *  2026-10-19・宏史さんの指摘。上限の目安を入れているのに、目安を超えた案件が
 *  「規模大」の印付きで一覧に出てくる。使う側から見れば「上限が効いていない」。
 *
 *  1. 目安の欄の下に、目安がどう効くかの説明を出す
 *     （消さずに印を付けて隠す。掲載の上限額が1社あたりの額か事業全体の予算かを、
 *      掲載情報だけでは見分けられないため）
 *  2. 印（事業外の可能性・地域外の可能性・規模大・規模小）の付いた案件を、
 *     最初は一覧から隠す。「印の付いた案件も見る（〇件）」で出せる。消しはしない
 *  3. 「規模大」の案件に「1社あたりの額か確かめる」ボタンを付ける。
 *     掲載元の説明文（Jグランツ等の詳細）を取り寄せ、端末の中で
 *     「1事業者あたり」「補助上限」などの書き方と「予算」「総額」などの書き方を探して、
 *     見つかった文をそのまま見せる。AIは使わない（トークンを使わない）。
 *     1社あたりの額が目安の内と読める記載があれば、その案件は隠さない。
 *     確かめた結果は端末に覚え、次からは取り寄せ直さない。
 *
 *  トライゲイトの画面（TriGate.html）の一覧（#digOut）を見張り、描き直されるたびに当て直す。
 *  一覧の作り・判定・見込み額には触れない（表示だけ）。
 * ========================================================================= */
(function () {
  'use strict';

  var VERSION = '2026-10-19-01';
  var K_SHOW = 'trigate_show_marked';   /* 印の付いた案件を見せるか（この端末） */
  var K_AMT = 'trigate_amount_check';   /* 額を確かめた結果（案件ごと） */
  var K_WEB = 'trisight_dig_web_items'; /* 手元の控え（画面と同じ鍵） */
  var K_TH = 'trigate_pj_threshold';    /* 目安（画面と同じ鍵） */
  var RELAY = {
    'mlit-': 'https://trisight-relay.vercel.app/api/mlit',
    'mhlw-': 'https://trisight-relay.vercel.app/api/mhlw',
    'pref-': 'https://trisight-relay.vercel.app/api/pref'
  };
  var JG = 'https://trisight-relay.vercel.app/api/jgrants';

  function $(id) { return document.getElementById(id); }
  function lj(k, d) { try { var v = JSON.parse(localStorage.getItem(k) || 'null'); return v == null ? d : v; } catch (e) { return d; } }
  function ls(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function yen(n) { return Number(n).toLocaleString('ja-JP') + '円'; }

  /* 目安（画面と同じ読み方。上限の既定は5,000万円） */
  function limits() {
    var code = ''; try { code = localStorage.getItem('trisight_access_code') || ''; } catch (e) {}
    var m = lj(K_TH, {}), e = (m && typeof m === 'object') ? m[code] : null;
    if (typeof e === 'number') e = { min: 0, max: e };
    if (!e || typeof e !== 'object') e = {};
    var max = (isFinite(Number(e.max)) && Number(e.max) > 0) ? Number(e.max) : 50000000;
    var min = (isFinite(Number(e.min)) && Number(e.min) > 0) ? Number(e.min) : null;
    return { min: min, max: max };
  }

  /* ======================================================================
     1. 額の確かめ（AIを使わない）
     ====================================================================== */
  /* 「1,000万円」「5億円」「3億5,000万円」「50,000,000円」を円の数へ */
  function yenOf(t) {
    var s = String(t || '').replace(/[,，\s]/g, '').replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
    var m = /^(?:([\d.]+)億)?(?:([\d.]+)万)?(?:([\d.]+))?円$/.exec(s);
    if (!m || (!m[1] && !m[2] && !m[3])) return null;
    var n = (m[1] ? Number(m[1]) * 1e8 : 0) + (m[2] ? Number(m[2]) * 1e4 : 0) + (m[3] ? Number(m[3]) : 0);
    return isFinite(n) && n > 0 ? Math.round(n) : null;
  }
  var AMT_RE = /[0-9０-９][0-9０-９,，.]*\s*(?:億\s*(?:[0-9０-９][0-9０-９,，.]*\s*万)?|万)?\s*円/g;
  var PER_RE = /([1１一]\s*(?:事業者|者|社|法人|団体|申請|件|事業所|施設|台|両|計画|グループ|事業)\s*(?:あたり|当たり|につき|毎))|補助上限|上限額|補助金の上限|交付上限|限度額|上限は|を上限/;
  var BUD_RE = /予算(?:額|総額|規模)?|総額|予定額|事業規模|事業費総額|全体で|執行額/;

  function plain(html) {
    var s = String(html || '');
    try { s = new DOMParser().parseFromString(s, 'text/html').body.textContent || ''; } catch (e) { s = s.replace(/<[^>]*>/g, ' '); }
    return s.replace(/[ \t　]+/g, ' ');
  }
  function sentences(t) {
    return String(t || '').replace(/\r/g, '').split(/(?<=[。．\n])/).map(function (x) { return x.replace(/\s+/g, ' ').trim(); }).filter(Boolean);
  }
  /* 詳細の文から、額の書かれた文を拾って分ける */
  function analyze(d, lim) {
    var text = [d.subsidy_catch_phrase, d.subsidy_rate ? '補助率：' + d.subsidy_rate : '', d.target_number_of_employees, d.use_purpose, plain(d.detail)]
      .filter(Boolean).join('\n');
    var per = [], bud = [], other = [];
    sentences(text).forEach(function (s) {
      var amts = (s.match(AMT_RE) || []).map(yenOf).filter(function (v) { return v != null; });
      if (!amts.length) return;
      var hit = { s: s.length > 160 ? s.slice(0, 160) + '…' : s, amts: amts };
      if (PER_RE.test(s)) per.push(hit); else if (BUD_RE.test(s)) bud.push(hit); else other.push(hit);
    });
    var perMax = null;
    per.forEach(function (h) { h.amts.forEach(function (v) { if (perMax == null || v > perMax) perMax = v; }); });
    var verdict;
    if (per.length && perMax != null && perMax <= lim.max) verdict = 'in';
    else if (per.length) verdict = 'over';
    else if (bud.length) verdict = 'budget';
    else verdict = 'none';
    return { verdict: verdict, perMax: perMax, per: per.slice(0, 3), bud: bud.slice(0, 2), other: other.slice(0, 2), at: new Date().toISOString(), max: lim.max };
  }
  async function fetchDetail(id) {
    if (/^(web-|list-)/.test(id)) {
      var all = lj(K_WEB, {}) || {};
      if (all[id]) return all[id];
      throw new Error('この案件の中身が手元にありません。もう一度「新着探索」を押してください。');
    }
    var code = ''; try { code = localStorage.getItem('trisight_access_code') || ''; } catch (e) {}
    if (!code) throw new Error('認証コードが入っていません。');
    var url = JG;
    Object.keys(RELAY).forEach(function (p) { if (id.indexOf(p) === 0) url = RELAY[p]; });
    var r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'x-trisight-code': code }, body: JSON.stringify({ action: 'detail', params: { id: id } }) });
    if (r.status === 401) throw new Error('認証コードが合いません。');
    if (!r.ok) throw new Error('掲載元の説明を取り寄せられませんでした（' + r.status + '）。');
    var j = await r.json(), a = Array.isArray(j.result) ? j.result : [];
    if (!a.length) throw new Error('掲載元に、この案件の説明が見つかりませんでした。');
    return a[0];
  }
  function memo() { var m = lj(K_AMT, {}); return (m && typeof m === 'object') ? m : {}; }
  function memoFor(id) {
    var r = memo()[id];
    if (!r) return null;
    /* 目安を変えたら、記載の額は同じでも「目安の内か」は変わるため、目安で読み直す */
    var lim = limits();
    if (r.max !== lim.max && (r.verdict === 'in' || r.verdict === 'over') && r.perMax != null) {
      r = Object.assign({}, r, { verdict: r.perMax <= lim.max ? 'in' : 'over', max: lim.max });
    }
    return r;
  }

  function resultHtml(r) {
    var head = {
      in: '申請の単位あたり（1者・1台など）の上限は ' + (r.perMax != null ? yen(r.perMax) : '') + ' と読める記載があります。目安の内のため、この案件は隠しません。1台あたり等の場合は、台数により1社の受給額は増えます。',
      over: '申請の単位あたり（1者・1台など）の上限も ' + (r.perMax != null ? yen(r.perMax) : '') + ' と読める記載があり、目安を超えています。',
      budget: '掲載の額は、事業全体の予算と読める記載があります。1社あたりの額は掲載情報からは分かりません。公募要領でご確認ください。',
      none: '掲載情報には、1社あたりの額か事業全体の予算かを示す記載がありません。公募要領でご確認ください。'
    }[r.verdict];
    var col = r.verdict === 'in' ? '#1f7a45' : (r.verdict === 'over' ? '#b0203a' : '#8a5a00');
    var lines = [];
    r.per.forEach(function (h) { lines.push('<li><b>申請の単位あたりの書き方：</b>' + esc(h.s) + '</li>'); });
    r.bud.forEach(function (h) { lines.push('<li><b>予算の書き方：</b>' + esc(h.s) + '</li>'); });
    if (!r.per.length && !r.bud.length) r.other.forEach(function (h) { lines.push('<li><b>額の書かれた文：</b>' + esc(h.s) + '</li>'); });
    return '<div class="tgm-res" style="margin-top:4px;padding:6px 8px;border:1px solid #e1e6ee;border-radius:6px;background:#fbfcfe;font-size:11.5px;line-height:1.6;color:#333">'
      + '<div style="color:' + col + ';font-weight:700">' + esc(head) + '</div>'
      + (lines.length ? '<ul style="margin:4px 0 0 1.2em;padding:0">' + lines.join('') + '</ul>' : '')
      + '<div style="color:#5f6b7a;margin-top:2px">掲載元の説明文から、書き方で拾ったものです（AIは使っていません）。最後は公募要領でお確かめください。</div></div>';
  }

  async function check(id, btn) {
    var box = btn.parentNode;
    btn.disabled = true; btn.textContent = '掲載元の説明を取り寄せています…';
    try {
      var d = await fetchDetail(id);
      var r = analyze(d, limits());
      var m = memo(); m[id] = r; ls(K_AMT, JSON.stringify(m));
      btn.remove();
      var old = box.querySelector('.tgm-res'); if (old) old.remove();
      box.insertAdjacentHTML('beforeend', resultHtml(r));
      apply();
    } catch (e) {
      btn.disabled = false; btn.textContent = '1社あたりの額か確かめる';
      var o = box.querySelector('.tgm-err'); if (o) o.remove();
      box.insertAdjacentHTML('beforeend', '<div class="tgm-err" style="font-size:11px;color:#b0203a">' + esc(e.message || e) + '</div>');
    }
  }

  /* ======================================================================
     2. 印の付いた案件を隠す
     ====================================================================== */
  function marksOf(row) {
    var el = row.querySelector('.tg-offbiz');
    if (!el) return [];
    var t = '';
    for (var n = el.firstChild; n; n = n.nextSibling) { if (n.nodeType === 3) t += n.nodeValue; else if (n.tagName === 'BR') break; }
    return t.split('・').map(function (x) { return x.trim(); }).filter(Boolean);
  }
  var applying = false;
  function apply() {
    var out = $('digOut'); if (!out || applying) return;
    applying = true;
    try {
      var show = localStorage.getItem(K_SHOW) === '1';
      var rows = [].slice.call(out.querySelectorAll('tr[data-id]'));
      var hidden = 0;
      rows.forEach(function (row) {
        var id = row.dataset.id || '', ms = marksOf(row);
        var big = ms.indexOf('規模大') >= 0;
        var r = big ? memoFor(id) : null;
        var cleared = !!(r && r.verdict === 'in');
        var other = ms.filter(function (m) { return m !== '規模大'; });
        var marked = other.length > 0 || (big && !cleared);
        row.classList.toggle('tgm-marked', marked);
        if (marked) hidden++;
        var next = row.nextElementSibling;
        if (next && next.classList.contains('digdetail')) next.classList.toggle('tgm-marked', marked);
        /* 規模大の行に、額を確かめるボタンか、確かめた結果を出す */
        var cell = row.querySelector('.tg-offbiz');
        if (big && cell && !cell.querySelector('.tgm-btn') && !cell.querySelector('.tgm-res')) {
          if (r) cell.insertAdjacentHTML('beforeend', resultHtml(r));
          else {
            var b = document.createElement('button');
            b.type = 'button'; b.className = 'rbtn tgm-btn';
            b.style.cssText = 'font-weight:400;font-size:10px;padding:1px 6px;margin-top:2px;display:block';
            b.title = '掲載元の説明文から、この額が1社あたりの上限なのか、事業全体の予算なのかを探します。AIは使いません';
            b.textContent = '1社あたりの額か確かめる';
            b.addEventListener('click', function (ev) { ev.stopPropagation(); check(id, b); });
            cell.appendChild(b);
          }
        }
      });
      /* 施主向けの見出しなど、下に印の無い行が残らない区切りの行も隠す */
      [].forEach.call(out.querySelectorAll('tr.digsep'), function (sep) {
        var n = sep.nextElementSibling, any = false;
        while (n && !n.classList.contains('digsep')) { if (n.matches('tr[data-id]') && !n.classList.contains('tgm-marked')) { any = true; break; } n = n.nextElementSibling; }
        sep.classList.toggle('tgm-marked', !any);
      });
      out.classList.toggle('tgm-hide', !show);
      var bar = $('tgmBar');
      if (bar) {
        if (!rows.length || !hidden) { bar.style.display = 'none'; }
        else {
          bar.style.display = '';
          bar.innerHTML = (show
            ? '印の付いた案件 ' + hidden + '件も表示しています。'
            : '印（事業外の可能性・地域外の可能性・規模大・規模小）の付いた案件 ' + hidden + '件は隠しています。')
            + ' <button type="button" class="rc-toggle" id="tgmToggle">' + (show ? '印の付いた案件を隠す' : '印の付いた案件も見る（' + hidden + '件）') + '</button>'
            + '<div style="font-size:11.5px;color:#5f6b7a;margin-top:2px">消してはいません。「規模大」の案件は、印の横の「1社あたりの額か確かめる」で、掲載の額が1社あたりの上限か事業全体の予算かを確かめられます（AIは使いません）。</div>';
          $('tgmToggle').onclick = function () { ls(K_SHOW, show ? '0' : '1'); apply(); };
        }
      }
    } finally { applying = false; }
  }

  /* ======================================================================
     3. 画面
     ====================================================================== */
  function mount() {
    var out = $('digOut');
    if (!out || $('tgmBar')) return;
    var css = document.createElement('style');
    css.textContent = '#digOut.tgm-hide .tgm-marked{display:none}'
      + '#tgmBar{margin:8px 0 4px;padding:8px 12px;border:1px solid #cdd6e4;border-radius:8px;background:#f8fafd;font-size:13px}'
      + '#tgmNote{margin:6px 0 2px;font-size:12px;color:#5f6b7a;line-height:1.7}';
    document.head.appendChild(css);
    var bar = document.createElement('div');
    bar.id = 'tgmBar'; bar.style.display = 'none';
    out.parentNode.insertBefore(bar, out);
    /* 目安の欄の下に、目安がどう効くかを書く */
    var minRow = $('pjThreshMinRow');
    if (minRow && !$('tgmNote')) {
      var note = document.createElement('div');
      note.id = 'tgmNote';
      note.textContent = '目安の効き方：上限・下限の目安を外れた案件は、消さずに「規模大」「規模小」の印を付けて、一覧から隠します。'
        + '掲載元の上限額が、1社あたりに出る額なのか、事業全体の予算なのかを、掲載情報だけでは見分けられないためです'
        + '（事業全体の予算を見て消すと、1社あたりなら取れる制度まで消してしまいます）。'
        + '隠した案件は、一覧の上の「印の付いた案件も見る」で出せます。「規模大」の案件は「1社あたりの額か確かめる」で確かめられます。';
      minRow.parentNode.insertBefore(note, minRow.nextSibling);
    }
    if (window.MutationObserver) new MutationObserver(function () { if (!applying) apply(); }).observe(out, { childList: true, subtree: true });
    apply();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
  window.TriGateMarks = { version: VERSION, analyze: analyze, yenOf: yenOf, apply: apply };
})();
