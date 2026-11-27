/*! ===========================================================================
 *  TriVersions.js — 版の一覧（2026-11-27 新設・宏史さんの指示）
 *  ---------------------------------------------------------------------------
 *  ・全システムの版を、version.json から読んで一覧にする（GitHubに上がった版がそのまま出る）。
 *  ・開いている間は1分ごと・画面に戻ったときに読み直す（改修してマージすれば、一覧も自動で変わる）。
 *  ・いま開いている画面の版が最新でなければ、その行を赤字で「新しい版があります」と出す。
 *  ・画面の版の表示（id="verLabel"）の横に「版の一覧」ボタンを自動で付ける。
 *    表札のように一覧を画面に直接並べるときは、<div id="tvList"></div> を置けばそこに出る。
 * ========================================================================== */
(function () {
  'use strict';
  if (window.TriVersions) return;
  /* version.json の名前 → 画面での呼び名・開くファイル */
  var NAMES = {
    trisight: ['トライサイトシステム（本体）', 'TriSight_v5.html'],
    trisight_auto: ['トライサイト AI連携オプション', 'TriSight_v5_auto.html'],
    trigate: ['トライゲイト', 'TriGate.html'],
    tritime: ['トライタイム', 'TriTime.html'],
    tritalk: ['トライトーク', 'TriTalk.html'],
    tritask: ['トライタスク', 'TriTask.html'],
    triform: ['トライフォーム', 'TriForm.html'],
    trisheet: ['基本情報シート', 'TriSheet.html'],
    triplan: ['受給計画書（トライプラン）', 'TriPlan.html'],
    trirobo: ['トライロボ（利用解説書）', 'TriRobo.html'],
    tricare_asm: ['トライケア（アセスメント）', 'TriCare_Assessment.html'],
    report_business: ['ビジネス報告書', 'TriSight_Report_Business.html']
  };
  var FILE2KEY = {}; Object.keys(NAMES).forEach(function (k) { FILE2KEY[NAMES[k][1].toLowerCase()] = k; });
  var here = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  var myKey = FILE2KEY[here] || '';
  var data = null, at = null, timer = null;

  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function myVer() { var el = document.getElementById('verLabel'); var t = el ? String(el.textContent || '').trim() : ''; return /^\d{4}-\d{2}-\d{2}-\d{2}$/.test(t) ? t : ''; }
  function load() {
    return fetch('version.json?t=' + Date.now(), { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { if (j) { data = j; at = new Date(); } render(); return data; }, function () { render(); return data; });
  }
  function table() {
    if (!data) return '<p style="margin:6px 0;color:#b42318">版の一覧を読み込めませんでした。通信を確かめてください。</p>';
    var keys = Object.keys(data).filter(function (k) { return typeof data[k] === 'string'; });
    keys.sort(function (a, b) { return (a === myKey ? -1 : b === myKey ? 1 : 0) || String(data[b]).localeCompare(String(data[a])); });
    var mv = myVer();
    var rows = keys.map(function (k) {
      var nm = NAMES[k] ? NAMES[k][0] : k, f = NAMES[k] ? NAMES[k][1] : '';
      var mine = k === myKey, old = mine && mv && mv !== data[k];
      var note = mine ? (old ? '<b style="color:#b42318">この画面は ' + esc(mv) + '。新しい版があります（「最新の版に更新」等のボタンで更新してください）</b>' : '<span style="color:#1a7f37">この画面（最新）</span>') : '';
      return '<tr' + (mine ? ' style="background:#fff8e1"' : '') + '><td style="padding:5px 8px;border-bottom:1px solid #e3e7ee">' + (f ? '<a href="' + esc(f) + '" style="color:#10243b">' + esc(nm) + '</a>' : esc(nm)) + '</td>' +
        '<td style="padding:5px 8px;border-bottom:1px solid #e3e7ee;font-variant-numeric:tabular-nums;white-space:nowrap">' + esc(data[k]) + '</td>' +
        '<td style="padding:5px 8px;border-bottom:1px solid #e3e7ee;font-size:12px">' + note + '</td></tr>';
    }).join('');
    var t = at ? ('0' + at.getHours()).slice(-2) + ':' + ('0' + at.getMinutes()).slice(-2) : '';
    return '<table style="border-collapse:collapse;width:100%;font-size:13.5px;color:#10243b;background:#fff"><tr><th style="text-align:left;padding:5px 8px;border-bottom:2px solid #10243b">システム</th><th style="text-align:left;padding:5px 8px;border-bottom:2px solid #10243b">最新の版</th><th style="border-bottom:2px solid #10243b"></th></tr>' + rows + '</table>' +
      '<p style="margin:6px 0 0;font-size:12px;color:#5b6680">GitHubに上がっている版です。' + (t ? t + ' に読み込みました。' : '') + '開いている間は1分ごとに読み直します。</p>';
  }
  function render() {
    var box = document.getElementById('tvBody'); if (box) box.innerHTML = table();
    var inl = document.getElementById('tvList'); if (inl) inl.innerHTML = table();
    var b = document.getElementById('tvBtn');
    if (b && data && myKey) { var mv = myVer(); var old = mv && data[myKey] && mv !== data[myKey]; b.style.background = old ? '#b42318' : '#10243b'; b.title = old ? 'この画面より新しい版があります' : '全システムの版を見る'; }
  }
  function open() {
    var w = document.getElementById('tvPop');
    if (!w) {
      w = document.createElement('div'); w.id = 'tvPop';
      w.setAttribute('style', 'position:fixed;inset:0;z-index:2147483000;background:rgba(15,29,58,.55);display:flex;align-items:center;justify-content:center;padding:16px;box-sizing:border-box;font-family:inherit');
      w.innerHTML = '<div style="background:#fff;border-radius:12px;max-width:560px;width:100%;max-height:calc(100vh - 32px);overflow:auto;padding:16px 18px;box-sizing:border-box;box-shadow:0 20px 50px rgba(0,0,0,.35)">' +
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px"><b style="font-size:16px;color:#10243b">版の一覧（全システム）</b>' +
        '<button type="button" id="tvClose" style="font:inherit;font-size:13px;padding:4px 14px;border:1px solid #10243b;border-radius:999px;background:#fff;color:#10243b;cursor:pointer">閉じる</button></div><div id="tvBody"></div></div>';
      document.body.appendChild(w);
      w.addEventListener('click', function (e) { if (e.target === w) close(); });
      document.getElementById('tvClose').onclick = close;
    }
    w.style.display = 'flex'; render(); load();
    if (!timer) timer = setInterval(function () { if (document.visibilityState === 'visible') load(); }, 60000);
  }
  function close() { var w = document.getElementById('tvPop'); if (w) w.style.display = 'none'; if (timer && !document.getElementById('tvList')) { clearInterval(timer); timer = null; } }
  function addBtn() {
    var lbl = document.getElementById('verLabel'); if (!lbl || document.getElementById('tvBtn')) return;
    var b = document.createElement('button'); b.type = 'button'; b.id = 'tvBtn'; b.textContent = '版の一覧';
    b.setAttribute('style', 'margin-left:8px;font-family:inherit;font-size:12px;padding:2px 12px;border:0;border-radius:999px;background:#10243b;color:#fff;cursor:pointer;vertical-align:middle');
    b.onclick = open;
    lbl.parentNode.insertBefore(b, lbl.nextSibling);
  }
  function start() {
    addBtn();
    if (document.getElementById('tvList')) { load(); timer = setInterval(function () { if (document.visibilityState === 'visible') load(); }, 60000); }
    else load();
    document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible' && (document.getElementById('tvList') || (document.getElementById('tvPop') || {}).style && document.getElementById('tvPop').style.display === 'flex')) load(); });
  }
  window.TriVersions = { open: open, load: load, version: '1.0' };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
