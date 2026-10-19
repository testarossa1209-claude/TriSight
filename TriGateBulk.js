/*! ===========================================================================
 *  TriGateBulk.js — トライゲイト：まとめて探す・手元の助成金一覧
 *  版：2026-10-19-01
 *  ---------------------------------------------------------------------------
 *  トライグラント（会員と助成金の突き合わせ）の働きを、トライゲイトへ移したもの
 *  （2026-10-19・宏史さんの決定。補助金・助成金の入口をトライゲイト一つにまとめる）。
 *
 *  1. 制度の入手元を選べるようにする
 *     ・国・自治体を探す（いつもどおり）
 *     ・国・自治体に加えて、手元の助成金一覧も入れる
 *     ・手元の助成金一覧だけで探す（国・自治体へは探しに行かない）
 *     手元の一覧の制度も、トライゲイトの同じ足切り・仕分け・判定を通す（2026-07-21の原則）。
 *     この部品は一覧を読んで渡すだけで、当て方は持たない。
 *  2. 使い方を選べるようにする
 *     ・一社ずつ探す（自社、または顧客一社）＝いつもどおり
 *     ・複数の会社をまとめて探す（顧問先・会員など）
 *       登録してある会社を選び、画面の「新着探索」を会社ごとに順に押して回す。
 *       一社ずつ探すときと同じ処理を、そのまま使う（夜の自動発掘と同じ作り）。
 *       結果は会社ごとに控え、「どの制度が、どの会社に当たったか」の表にまとめる。
 *
 *  トライゲイトの画面（TriGate.html）とは、次の口でつながる。
 *    window.TriGateList.items() / only()  … 手元の一覧の制度と、「手元の一覧だけ」かどうか
 *    window.__tsSkipWeb                   … まとめて探す中で、同じ地域の検索を二社目から省く
 * ========================================================================= */
(function () {
  'use strict';

  var VERSION = '2026-10-19-01';
  var K_LIST = 'trigate_local_grants';     /* 手元の助成金一覧（この端末） */
  var K_SRC = 'trigate_source_mode';       /* 制度の入手元：net／both／only */
  var K_WHO = 'trigate_use_mode';          /* 使い方：one／many */
  var K_CAP = 'trigate_bulk_cap';          /* まとめて回す社数の上限（この端末の設定） */
  var K_RUNS = 'trigate_bulk_runs';        /* まとめて探した結果の控え（会社ごと） */
  var K_LIB = 'trisight_dig_company_lib';  /* トライゲイトの会社の一覧（画面と同じ鍵） */
  var K_SAVED = 'trisight_dig_saved';      /* 画面の一覧の控え（画面と同じ鍵） */
  var K_CANDS = 'trisight_dig_candidates'; /* 判定した候補（画面と同じ鍵） */
  var K_WEB = 'trisight_dig_web_items';    /* 詳細を手元から返すための控え（画面と同じ鍵） */

  function lsGet(k, d) { try { var v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } }
  function lj(k, d) { try { var v = JSON.parse(localStorage.getItem(k) || 'null'); return v == null ? d : v; } catch (e) { return d; } }
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function $(id) { return document.getElementById(id); }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  /* ======================================================================
     1. 手元の助成金一覧（CSV）
     ====================================================================== */
  /* 列の名前の読み替え。日本語の見出しと、トライグラントの書き出しの見出しの両方を読む */
  var COLS = {
    title: ['制度名', '助成金名', '補助金名', 'grant_name', 'title', 'name'],
    issuer: ['交付元', '実施機関', '所管', 'ministry', 'institution_name'],
    max: ['上限額', '上限額（円）', '上限額(円)', 'max_grant_amount_yen', 'subsidy_max_limit'],
    rate: ['補助率', '助成率', 'subsidy_rate'],
    start: ['受付開始日', 'acceptance_start_datetime'],
    end: ['締切', '受付終了日', '申請期限', 'application_deadline', 'acceptance_end_datetime'],
    area: ['対象地域', 'target_prefecture', 'target_area_search'],
    industry: ['対象業種', 'target_industries', 'industry'],
    empMax: ['従業員数の上限', 'max_employee_count'],
    empMin: ['従業員数の下限', 'min_employee_count'],
    emp: ['従業員規模', 'target_number_of_employees'],
    purpose: ['利用目的', '分類', 'category', 'use_purpose'],
    detail: ['概要', '説明', 'description', 'detail'],
    url: ['公式ページ', 'URL', 'url', 'front_subsidy_detail_page_url']
  };
  var SAMPLE_CSV = '制度名,交付元,上限額,補助率,締切,対象地域,対象業種,従業員規模,利用目的,概要,公式ページ\r\n'
    + '（例）〇〇県 介護職員の定着支援助成金,〇〇県,500000,1/2,2026-12-25,〇〇県,医療・福祉,30人以下,人材の定着,職員の研修や面談の仕組みを整える費用の一部を助成します,https://www.example.jp/\r\n';

  function parseLine(line) {
    var out = [], cur = '', q = false;
    for (var i = 0; i < line.length; i++) {
      var c = line[i];
      if (c === '"') { if (q && line[i + 1] === '"') { cur += '"'; i++; } else q = !q; }
      else if (c === ',' && !q) { out.push(cur.trim()); cur = ''; }
      else cur += c;
    }
    out.push(cur.trim());
    return out;
  }
  function pick(row, names) {
    for (var i = 0; i < names.length; i++) {
      if (row[names[i]] != null && String(row[names[i]]).trim() !== '') return String(row[names[i]]).trim();
    }
    return '';
  }
  /* 「1,000万円」「500000」「5億円」などを円の数へ。読めなければ null */
  function yenOf(t) {
    var s = String(t || '').replace(/[,，\s円]/g, '').replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
    if (!s) return null;
    var m = /^([\d.]+)(億|万)?$/.exec(s);
    if (!m) { var m2 = /^([\d.]+)億([\d.]+)万$/.exec(s); return m2 ? Math.round(Number(m2[1]) * 1e8 + Number(m2[2]) * 1e4) : null; }
    var n = Number(m[1]); if (!isFinite(n)) return null;
    return Math.round(n * (m[2] === '億' ? 1e8 : m[2] === '万' ? 1e4 : 1));
  }
  /* 日付を「YYYY-MM-DD の日本時間の終わり」へ。読めなければ空 */
  function dayEnd(t, start) {
    var s = String(t || '').trim().replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
    var m = /^(\d{4})[\/\-年.](\d{1,2})[\/\-月.](\d{1,2})/.exec(s);
    if (!m) return '';
    var d = m[1] + '-' + ('0' + m[2]).slice(-2) + '-' + ('0' + m[3]).slice(-2);
    return d + (start ? 'T00:00:00+09:00' : 'T23:59:00+09:00');
  }
  function hash(t) {
    var h1 = 0x811c9dc5, h2 = 5381;
    for (var i = 0; i < t.length; i++) { var c = t.charCodeAt(i); h1 = Math.imul(h1 ^ c, 16777619) >>> 0; h2 = ((h2 * 33) ^ c) >>> 0; }
    return h1.toString(36) + h2.toString(36);
  }
  /* CSVの1行を、トライゲイトの制度の形（Jグランツと同じ項目名）へ */
  function toItem(row) {
    var title = pick(row, COLS.title);
    if (!title) return null;
    var issuer = pick(row, COLS.issuer);
    var area = pick(row, COLS.area).replace(/\|/g, '、');
    var emp = pick(row, COLS.emp);
    if (!emp) {
      var mx = pick(row, COLS.empMax), mn = pick(row, COLS.empMin);
      if (mx) emp = '従業員' + mx + '人以下'; else if (mn) emp = '従業員' + mn + '人以上';
    }
    var end = dayEnd(pick(row, COLS.end), false);
    var it = {
      id: 'list-' + hash(title + '|' + issuer + '|' + end),
      title: title, name: title,
      subsidy_max_limit: yenOf(pick(row, COLS.max)),
      subsidy_rate: pick(row, COLS.rate) || null,
      acceptance_start_datetime: dayEnd(pick(row, COLS.start), true) || null,
      acceptance_end_datetime: end || null,
      target_area_search: area || '全国',
      target_area_detail: area || '',
      industry: pick(row, COLS.industry).replace(/\|/g, '、'),
      target_number_of_employees: emp,
      use_purpose: pick(row, COLS.purpose),
      detail: pick(row, COLS.detail),
      subsidy_catch_phrase: '',
      front_subsidy_detail_page_url: pick(row, COLS.url),
      ts_source: '手元の助成金一覧（利用者が入れたもの・当社未確認）' + (issuer ? '／交付元：' + issuer : ''),
      application_guidelines: [], outline_of_grant: [], application_form: [], ts_guidelines: []
    };
    return it;
  }
  function parseCsv(text) {
    var lines = String(text || '').replace(/^﻿/, '').split(/\r?\n/).filter(function (l) { return l.trim(); });
    if (lines.length < 2) throw new Error('見出しの行と、制度の行が1行以上必要です。');
    var head = parseLine(lines[0]);
    var hasTitle = head.some(function (h) { return COLS.title.indexOf(h) >= 0; });
    if (!hasTitle) throw new Error('見出しの行に「制度名」の列がありません（「一覧の書き方（見本を保存）」の形で作ってください）。');
    var items = [], skip = 0, seen = {};
    for (var i = 1; i < lines.length; i++) {
      var v = parseLine(lines[i]), row = {};
      head.forEach(function (h, j) { row[h] = v[j] == null ? '' : v[j]; });
      var it = toItem(row);
      if (!it || seen[it.id]) { skip++; continue; }
      seen[it.id] = 1; items.push(it);
    }
    return { items: items, skip: skip };
  }
  function listDoc() { return lj(K_LIST, null); }
  function srcMode() { var m = lsGet(K_SRC, 'net'); return (m === 'both' || m === 'only') ? m : 'net'; }
  function listItems() {
    var d = listDoc();
    return (d && Array.isArray(d.items)) ? d.items : [];
  }
  /* 詳細を開いたとき・詳細AI判定のとき、画面は手元の控え（K_WEB）から中身を返す */
  function cacheItems(items) {
    var all = lj(K_WEB, {}) || {};
    items.forEach(function (it) { if (it && it.id) all[it.id] = it; });
    lsSet(K_WEB, JSON.stringify(all));
  }

  window.TriGateList = Object.freeze({
    version: VERSION,
    items: function () { return srcMode() === 'net' ? [] : listItems(); },
    only: function () { return srcMode() === 'only'; }
  });

  /* ======================================================================
     2. まとめて探す
     ====================================================================== */
  function lib() { var m = lj(K_LIB, {}); return (m && typeof m === 'object' && !Array.isArray(m)) ? m : {}; }
  function industryOf(c) {
    c = c || {};
    var a = (c['事業'] && c['事業']['業種_大分類']) || '';
    var b = (c['機械足切り条件'] && c['機械足切り条件']['業種']) || '';
    return String(a || b || '（業種の記載なし）').split(/[，,、]/)[0].trim();
  }
  function norm(t) {
    return String(t || '').replace(/[【】〔〕（）()\[\]]/g, '').replace(/(令和|平成)\s*[0-9０-９元]+\s*年度?/g, '')
      .replace(/[\s　_,、・]/g, '').trim();
  }
  /* 会社の本店所在地（都道府県・市区町村）。トライゲイトの画面が地域の初期値に使うのと同じ欄を読む */
  function areaOf(c) {
    c = c || {};
    var comp = c['会社'] || {}, fil = c['機械足切り条件'] || {};
    return { pref: comp['本店所在地_都道府県'] || fil['対象地域'] || '', city: comp['本店所在地_市区町村'] || '' };
  }
  /* 地域の選択窓を合わせる。市区町村は、選択窓にその名前があるときだけ選ぶ */
  function setArea(pref, city) {
    var ps = $('digPref'), cs = $('digCity');
    if (!ps) return '';
    var has = [].some.call(ps.options, function (o) { return o.value === pref; });
    ps.value = has ? pref : '';
    ps.dispatchEvent(new Event('change'));
    if (cs && city && !cs.disabled && [].some.call(cs.options, function (o) { return o.value === city; })) cs.value = city;
    return ps.value + ((cs && !cs.disabled) ? cs.value : '');
  }
  function runs() { var r = lj(K_RUNS, {}); return (r && typeof r === 'object') ? r : {}; }
  function capOf() { var n = Number(lsGet(K_CAP, '10')); return [3, 5, 10, 20].indexOf(n) >= 0 ? n : 10; }

  var stopReq = false, running = false;

  async function waitIdle(btn, ms) {
    var t0 = Date.now();
    while (btn.disabled && Date.now() - t0 < ms) await sleep(1500);
    return !btn.disabled;
  }
  /* ボタンを押し、始まって終わるまで待つ（夜の自動発掘と同じ見分け方）。
     始まりは、ボタンが薄くなった（disabled になった）瞬間を見張って確かめる。
     一定の間隔で見に行くだけだと、すぐ終わったときに薄くなった一瞬を見逃すため */
  async function pressAndWait(btn, startMs, endMs) {
    var started = false, t1 = Date.now(), mo = null;
    if (window.MutationObserver) {
      mo = new MutationObserver(function () { if (btn.disabled) started = true; });
      mo.observe(btn, { attributes: true, attributeFilter: ['disabled'] });
    }
    btn.click();
    if (btn.disabled) started = true;
    try {
      while (Date.now() - t1 < endMs) {
        await sleep(1000);
        if (btn.disabled) started = true;
        else if (started) break;
        else if (Date.now() - t1 > startMs) break;
      }
    } finally { if (mo) mo.disconnect(); }
    return { started: started, done: !btn.disabled };
  }

  async function runBulk() {
    if (running) return;
    var btn = $('digBtn'), sel = $('digCompanySel'), st = $('digStatus'), fg = $('digFullGateBtn');
    var say = function (t) { var el = $('tgBulkSt'); if (el) el.textContent = t; };
    if (!btn || !sel) { say('トライゲイトの画面の部品が見つからないため、まとめて探せません。'); return; }
    var names = [].slice.call(document.querySelectorAll('#tgCoList input[type=checkbox]:checked')).map(function (x) { return x.value; });
    if (!names.length) { say('まとめて探す会社に印を付けてください。'); return; }
    var cap = capOf();
    if (names.length > cap) { say('印を付けた会社が ' + names.length + '社あり、一度に回す社数の上限（' + cap + '社）を超えています。印を減らすか、上限を変えてください。'); return; }
    if (srcMode() === 'only' && !listItems().length) { say('「手元の助成金一覧だけで探す」を選んでいますが、一覧がまだ入っていません。'); return; }
    var gate = !!($('tgGate') && $('tgGate').checked);
    var own = !($('tgAreaFix') && $('tgAreaFix').checked);
    var origPref = $('digPref') ? $('digPref').value : '', origCity = ($('digCity') && !$('digCity').disabled) ? $('digCity').value : '';
    if (!confirm(names.length + '社を、一社ずつ順に探します。\n\n'
      + (own ? '・地域は、各社の本店所在地で探します。\n' : '・地域「' + ((origPref + origCity) || '全国（絞らない）') + '」を全社に使います。\n')
      + '・検索する語・発掘の目的は、いま画面で選んでいるものを全社に使います。\n'
      + '・足切りと事業に照らした仕分けは、会社ごとにAIを使います（今月の使用量に入ります）。\n'
      + (srcMode() !== 'only' ? '・同じ地域の検索は一度だけ行い、同じ地域の二社目からは台帳に入った分を使います。\n' : '')
      + (gate ? '・詳細AI判定まで通すため、会社ごと・案件ごとにAIを使います。\n' : '')
      + '\n始めてよろしいですか？')) return;

    if (window.tsBoxReady && typeof window.tsBoxReady.then === 'function') { say('保管庫の読み込みが終わるのを待っています…'); try { await window.tsBoxReady; } catch (e) {} }
    running = true; stopReq = false;
    $('tgBulkGo').disabled = true; $('tgBulkStop').disabled = false;
    var orig = sel.value, all = runs(), doneN = 0, searched = {};
    window.__tsSkipWeb = null;
    try {
      for (var i = 0; i < names.length; i++) {
        if (stopReq) { say('止めました（' + doneN + '/' + names.length + '社まで探しました）。'); break; }
        var nm = names[i];
        say((i + 1) + '/' + names.length + '社目「' + nm + '」を探しています…（下の「新着補助金探索」の表示も動きます）');
        if (!(await waitIdle(btn, 300000))) { say('「新着探索」が使える状態に戻らないため、止めました。'); break; }
        sel.value = nm; sel.dispatchEvent(new Event('change'));
        var ar = areaOf(lib()[nm]);
        var area = own ? setArea(ar.pref, ar.city) : setArea(origPref, origCity);
        window.__tsSkipWeb = (area && searched[area]) ? area : null;
        await sleep(300);
        var tStart = Date.now() - 1000;
        var r = await pressAndWait(btn, 60000, 90 * 60000);
        if (r.started && area && srcMode() !== 'only') searched[area] = 1;
        var sv = lj(K_SAVED, null);
        var rows = (r.started && sv && sv.company === nm && Array.isArray(sv.rows) && Date.parse(sv.savedAt) >= tStart) ? sv.rows : [];
        var gateNote = '';
        if (gate && rows.length && fg && fg.style.display !== 'none') {
          say((i + 1) + '/' + names.length + '社目「' + nm + '」の詳細AI判定を回しています…');
          var g = await pressAndWait(fg, 30000, 120 * 60000);
          gateNote = g.started ? (g.done ? '詳細AI判定まで通しました' : '詳細AI判定が時間内に終わりませんでした（途中までの判定は残っています）') : '詳細AI判定に回す案件がありませんでした';
        }
        all[nm] = { at: new Date().toISOString(), area: area, source: srcMode(), rows: rows,
          status: r.started ? String((st && st.textContent) || '').slice(0, 300) : '「新着探索」が始まりませんでした',
          ok: r.started && r.done, gate: gateNote };
        lsSet(K_RUNS, JSON.stringify(all));
        doneN++;
        render();
      }
      if (!stopReq && doneN === names.length) say(names.length + '社を探し終えました。下の表で、どの制度がどの会社に当たったかを確かめてください。');
    } finally {
      window.__tsSkipWeb = null;
      running = false;
      $('tgBulkGo').disabled = false; $('tgBulkStop').disabled = true;
      /* 元の会社と地域に戻す。探した結果は、表の「この会社の一覧を開く」から見られる */
      if (orig && orig !== sel.value && lib()[orig]) { sel.value = orig; sel.dispatchEvent(new Event('change')); }
      setArea(origPref, origCity);
      render();
    }
  }

  /* 一覧の中の、会社ごとの判定の印 */
  function verdictOf(company, id) {
    var cands = lj(K_CANDS, []);
    if (!Array.isArray(cands)) return null;
    for (var i = 0; i < cands.length; i++) {
      var c = cands[i];
      if (c && c.id === id && String(c['会社'] || '') === company && c.gate) return String(c.gate['判定'] || '');
    }
    return null;
  }
  function cellOf(company, id) {
    var v = verdictOf(company, id);
    if (v === '追う') return { k: 3, t: '◎追う' };
    if (v === '要確認') return { k: 2, t: '△要確認' };
    if (v === '見送り') return { k: 0, t: '×見送り' };
    return { k: 1, t: '○一覧に出た' };
  }
  function yen(n) { return (n == null || !isFinite(Number(n))) ? '—' : Number(n).toLocaleString('ja-JP') + '円'; }
  function day(t) { var d = new Date(t); return isNaN(d) ? '—' : (d.getFullYear() + '/' + (d.getMonth() + 1) + '/' + d.getDate()); }

  function buildTable() {
    var R = runs(), L = lib();
    var cos = Object.keys(R).filter(function (n) { return R[n] && Array.isArray(R[n].rows); }).sort();
    var progs = {};
    cos.forEach(function (n) {
      R[n].rows.forEach(function (it) {
        if (!it || !it.id) return;
        var key = norm(it.title || it.name) || it.id;
        var p = progs[key] || (progs[key] = { title: it.title || it.name || '（名称不明）', id: it.id, max: it.subsidy_max_limit, end: it.acceptance_end_datetime, src: it.id, by: {} });
        var c = cellOf(n, it.id);
        if (!p.by[n] || c.k > p.by[n].k) p.by[n] = c;
      });
    });
    var list = Object.keys(progs).map(function (k) {
      var p = progs[k]; p.hit = cos.filter(function (n) { return p.by[n] && p.by[n].k > 0; }).length; return p;
    }).sort(function (a, b) { return b.hit - a.hit || String(a.title).localeCompare(String(b.title), 'ja'); });
    return { R: R, L: L, cos: cos, list: list };
  }

  function render() {
    var box = $('tgBulkOut'); if (!box) return;
    var T = buildTable();
    if (!T.cos.length) { box.innerHTML = ''; return; }
    var h = '<div class="tgb-hd">まとめて探した結果<span>どの制度が、どの会社に当たったか（◎＝詳細AI判定で「追う」／△＝要確認／○＝一覧に出た・判定前／×＝見送り／空欄＝その会社の一覧に出なかった）</span></div>';
    h += '<div class="tgb-cos">';
    T.cos.forEach(function (n) {
      var r = T.R[n], ok = r.rows.length, follow = r.rows.filter(function (it) { return verdictOf(n, it.id) === '追う'; }).length;
      h += '<div class="tgb-co"><b>' + esc(n) + '</b><span>' + esc(industryOf(T.L[n])) + '・' + day(r.at) + ' 探索' + (r.area ? '・' + esc(r.area) : '') + '</span>'
        + '<span>一覧 ' + ok + '件' + (follow ? '・追う ' + follow + '件' : '') + (r.gate ? '（' + esc(r.gate) + '）' : '') + '</span>'
        + (!r.ok ? '<span class="ng">' + esc(r.status || '探し終えていません') + '</span>' : '')
        + (ok ? '<button type="button" class="rc-toggle" data-open="' + esc(n) + '">この会社の一覧を開く</button>' : '') + '</div>';
    });
    h += '</div>';
    if (T.list.length) {
      h += '<div class="tgb-wrap"><table class="tgb-tbl"><thead><tr><th>制度名</th><th>上限額</th><th>受付期間の終わり</th><th>当たった会社</th>'
        + T.cos.map(function (n) { return '<th>' + esc(n) + '</th>'; }).join('') + '</tr></thead><tbody>';
      T.list.forEach(function (p) {
        var src = (typeof window.tsSrcOf === 'function') ? window.tsSrcOf(p.src) : null;
        h += '<tr><td>' + esc(p.title) + (src ? ' <span class="tgb-src" style="background:' + src.bg + ';color:' + src.fg + '">' + esc(src.short) + '</span>' : '') + '</td>'
          + '<td>' + yen(p.max) + '</td><td>' + day(p.end) + '</td><td>' + p.hit + '/' + T.cos.length + '社</td>'
          + T.cos.map(function (n) { var c = p.by[n]; return '<td class="k' + (c ? c.k : 'n') + '">' + (c ? c.t : '') + '</td>'; }).join('') + '</tr>';
      });
      h += '</tbody></table></div>';
      /* 業種別のまとめ（トライグラントの「業界別サマリー」を移したもの） */
      var byInd = {};
      T.cos.forEach(function (n) { var k = industryOf(T.L[n]); (byInd[k] = byInd[k] || []).push(n); });
      h += '<div class="tgb-hd" style="margin-top:12px">業種別のまとめ<span>同じ業種の会社に共通して当たった制度（当たった会社の多い順に上位5件）</span></div>';
      Object.keys(byInd).sort().forEach(function (k) {
        var cs = byInd[k];
        var top = T.list.map(function (p) { return { p: p, n: cs.filter(function (n) { return p.by[n] && p.by[n].k > 0; }).length }; })
          .filter(function (x) { return x.n > 0; }).sort(function (a, b) { return b.n - a.n; }).slice(0, 5);
        h += '<div class="tgb-ind"><b>' + esc(k) + '</b>（' + cs.length + '社）' + (top.length
          ? '<ul>' + top.map(function (x) { return '<li>' + esc(x.p.title) + '　' + x.n + '社中' + cs.length + '社に当たりました</li>'; }).join('') + '</ul>'
          : '<div class="tgb-sub">当たった制度はありません。</div>') + '</div>';
      });
    } else {
      h += '<div class="tgb-sub">選んだ会社の一覧には、制度が出ませんでした。</div>';
    }
    h += '<div style="margin-top:10px"><button type="button" class="rc-toggle" id="tgBulkCsv">この表を書き出す（CSV）</button>'
      + ' <button type="button" class="rc-toggle" id="tgBulkClear">まとめて探した結果を消す</button></div>';
    box.innerHTML = h;
    [].forEach.call(box.querySelectorAll('button[data-open]'), function (b) { b.onclick = function () { openCompany(b.getAttribute('data-open')); }; });
    $('tgBulkCsv').onclick = exportCsv;
    $('tgBulkClear').onclick = function () {
      if (!confirm('まとめて探した結果の表を消します。\n（会社ごとの判定の記憶と、獲得実績は消えません）\n\nよろしいですか？')) return;
      try { localStorage.removeItem(K_RUNS); } catch (e) {}
      render();
    };
  }

  /* 会社を切り替え、その会社をまとめて探したときの一覧を画面に戻す */
  function openCompany(n) {
    var r = runs()[n], sel = $('digCompanySel');
    if (!r || !sel || !lib()[n]) { alert('この会社の登録か、探した結果が見つかりませんでした。'); return; }
    sel.value = n; sel.dispatchEvent(new Event('change'));
    var sv = lj(K_SAVED, {}) || {};
    lsSet(K_SAVED, JSON.stringify({ company: n, keyword: sv.keyword || '', status: r.status || '', savedAt: r.at, night: false, nightAt: sv.nightAt || null, nightNote: sv.nightNote || '', rows: r.rows }));
    try { if (typeof window.tsDigRestore === 'function') window.tsDigRestore(); } catch (e) {}
    var o = $('digOut'); if (o) o.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function exportCsv() {
    var T = buildTable();
    var q = function (v) { v = String(v == null ? '' : v); return /[",\r\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var lines = [['制度名', '出所', '上限額（円）', '受付期間の終わり', '当たった会社の数'].concat(T.cos).map(q).join(',')];
    T.list.forEach(function (p) {
      var src = (typeof window.tsSrcOf === 'function') ? window.tsSrcOf(p.src).full : '';
      lines.push([p.title, src, p.max == null ? '' : p.max, day(p.end), p.hit].concat(T.cos.map(function (n) { return p.by[n] ? p.by[n].t : ''; })).map(q).join(','));
    });
    save('﻿' + lines.join('\r\n'), 'まとめて探した結果_' + new Date().toISOString().slice(0, 10) + '.csv');
  }
  function save(text, name) {
    var b = new Blob([text], { type: 'text/csv;charset=utf-8' }), a = document.createElement('a');
    a.href = URL.createObjectURL(b); a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  /* ======================================================================
     3. 画面
     ====================================================================== */
  function renderCoList() {
    var box = $('tgCoList'); if (!box) return;
    var L = lib(), names = Object.keys(L).sort();
    var was = {}; [].forEach.call(box.querySelectorAll('input:checked'), function (x) { was[x.value] = 1; });
    if (!names.length) { box.innerHTML = '<div class="tgb-sub">まだ会社が登録されていません。上の「企業基礎情報を追加」か「シートから読み込む」で、探す会社を先に登録してください。</div>'; return; }
    box.innerHTML = names.map(function (n) {
      return '<label><input type="checkbox" value="' + esc(n) + '"' + (was[n] ? ' checked' : '') + '> ' + esc(n) + '<span>' + esc(industryOf(L[n])) + (areaOf(L[n]).pref ? '・' + esc(areaOf(L[n]).pref + areaOf(L[n]).city) : '') + '</span></label>';
    }).join('');
  }
  function renderListSt() {
    var el = $('tgListSt'); if (!el) return;
    var d = listDoc();
    el.textContent = (d && d.items && d.items.length) ? '入っている一覧：' + (d.name || '（名前なし）') + '（' + d.items.length + '件・' + day(d.at) + ' 取り込み）' : '一覧はまだ入っていません。';
  }
  function syncModes() {
    var m = srcMode(), w = lsGet(K_WHO, 'one');
    [].forEach.call(document.querySelectorAll('input[name=tgSrc]'), function (x) { x.checked = (x.value === m); });
    [].forEach.call(document.querySelectorAll('input[name=tgWho]'), function (x) { x.checked = (x.value === w); });
    var lr = $('tgListRow'); if (lr) lr.style.display = (m === 'net') ? 'none' : '';
    var mb = $('tgManyBox'); if (mb) mb.style.display = (w === 'many') ? '' : 'none';
    var wn = $('tgSrcWarn');
    if (wn) wn.style.display = (m === 'only' && !listItems().length) ? '' : 'none';
    if (w === 'many') renderCoList();
  }

  function mount() {
    var anchor = $('digStatus');
    if (!anchor || $('tgModeBox')) return;
    var css = document.createElement('style');
    css.textContent =
      '#tgModeBox{margin:10px 0 4px;display:grid;gap:10px}' +
      '#tgModeBox .tgb-box{border:1px solid #cdd6e4;border-radius:8px;padding:10px 12px;background:#f8fafd}' +
      '#tgModeBox .tgb-t{font-size:13px;font-weight:700;color:#16213a;margin-bottom:4px}' +
      '#tgModeBox label.tgb-r{display:block;font-size:13px;cursor:pointer;margin:2px 0}' +
      '#tgModeBox .tgb-sub,.tgb-sub{font-size:12px;color:#5f6b7a;margin-top:4px;line-height:1.6}' +
      '#tgListRow{margin-top:6px;font-size:13px}' +
      '#tgCoList{display:flex;flex-wrap:wrap;gap:4px 14px;margin:6px 0;font-size:13px}' +
      '#tgCoList label{cursor:pointer}#tgCoList label span{font-size:11.5px;color:#5f6b7a;margin-left:4px}' +
      '#tgBulkSt{font-size:13px;margin-top:6px;color:#16213a}' +
      '#tgBulkOut{margin-top:10px}' +
      '.tgb-hd{font-size:14px;font-weight:700;color:#16213a;margin:6px 0}.tgb-hd span{display:block;font-size:11.5px;font-weight:400;color:#5f6b7a}' +
      '.tgb-cos{display:grid;gap:6px;margin-bottom:8px}' +
      '.tgb-co{display:flex;flex-wrap:wrap;align-items:center;gap:4px 12px;font-size:12.5px;border:1px solid #e1e6ee;border-radius:6px;padding:6px 10px;background:#fff}' +
      '.tgb-co span{color:#5f6b7a}.tgb-co .ng{color:#b3261e}.tgb-co button{margin-left:auto}' +
      '.tgb-wrap{overflow-x:auto}.tgb-tbl{border-collapse:collapse;font-size:12.5px;min-width:100%}' +
      '.tgb-tbl th,.tgb-tbl td{border:1px solid #d9dee8;padding:4px 6px;text-align:left;vertical-align:top;white-space:nowrap}' +
      '.tgb-tbl td:first-child{white-space:normal;min-width:220px}.tgb-tbl th{background:#eef2f8}' +
      '.tgb-tbl td.k3{color:#1f7a45;font-weight:700}.tgb-tbl td.k2{color:#8a5a00}.tgb-tbl td.k0{color:#8a8f99}' +
      '.tgb-src{font-size:.8em;padding:1px 5px;border-radius:3px;white-space:nowrap}' +
      '.tgb-ind{font-size:12.5px;margin:4px 0}.tgb-ind ul{margin:2px 0 0 1.2em;padding:0}';
    document.head.appendChild(css);

    var box = document.createElement('div');
    box.id = 'tgModeBox';
    box.innerHTML =
      '<div class="tgb-box"><div class="tgb-t">制度の入手元</div>' +
      '<label class="tgb-r"><input type="radio" name="tgSrc" value="net"> 国・自治体を探す（いつもどおり）</label>' +
      '<label class="tgb-r"><input type="radio" name="tgSrc" value="both"> 国・自治体に加えて、手元の助成金一覧も入れる</label>' +
      '<label class="tgb-r"><input type="radio" name="tgSrc" value="only"> 手元の助成金一覧だけで探す（国・自治体へは探しに行きません）</label>' +
      '<div id="tgListRow">' +
        '<label class="digfile">手元の助成金一覧（CSV）：<input type="file" id="tgListFile" accept=".csv,text/csv"></label> ' +
        '<button type="button" class="rc-toggle" id="tgListSample" title="一覧の列の並びを見本のファイルで保存します。表計算ソフトで開いて書き足し、CSV形式で保存してから入れてください">一覧の書き方（見本を保存）</button> ' +
        '<button type="button" class="rc-toggle" id="tgListClear">一覧を消す</button>' +
        '<div class="tgb-sub" id="tgListSt"></div>' +
        '<div class="tgb-sub" id="tgSrcWarn" style="display:none;color:#b3261e">「手元の助成金一覧だけで探す」を選んでいますが、一覧がまだ入っていません。このままでは「新着探索」はいつもどおり国・自治体を探します。</div>' +
        '<div class="tgb-sub">手元の一覧の制度も、国・自治体の制度と同じ足切り・仕分け・判定を通ります。一覧の中身は利用者が入れたもので、当社は確かめていません（一覧の行に「手元の一覧」の札が付きます）。</div>' +
      '</div></div>' +
      '<div class="tgb-box"><div class="tgb-t">使い方</div>' +
      '<label class="tgb-r"><input type="radio" name="tgWho" value="one"> 一社ずつ探す（自社、または顧客一社）＝いつもどおり「新着探索」を押します</label>' +
      '<label class="tgb-r"><input type="radio" name="tgWho" value="many"> 複数の会社をまとめて探す（顧問先・会員など）</label>' +
      '<div id="tgManyBox" style="display:none">' +
        '<div class="tgb-sub">探す会社に印を付けてください。会社は「企業基礎情報を追加」か「シートから読み込む」で先に登録しておきます。検索する語・発掘の目的は、上の欄で選んだものを全社に使います。</div>' +
        '<div id="tgCoList"></div>' +
        '<div style="font-size:13px;margin:2px 0 6px">地域：<label style="cursor:pointer"><input type="radio" name="tgArea" id="tgAreaOwn" checked> 各社の本店所在地で探す</label>　' +
        '<label style="cursor:pointer"><input type="radio" name="tgArea" id="tgAreaFix"> 上の「地域」で選んだものを全社に使う（新規展開地を探すとき）</label></div>' +
        '<div style="font-size:13px">一度に回す社数の上限：<select id="tgCap"><option value="3">3社</option><option value="5">5社</option><option value="10">10社</option><option value="20">20社</option></select>' +
        '　<label style="cursor:pointer"><input type="checkbox" id="tgGate"> 詳細AI判定まで通す</label></div>' +
        '<div class="tgb-sub">足切りと事業に照らした仕分けは、会社ごとにAIを使います（今月の使用量に入ります）。詳細AI判定まで通すと、会社ごと・案件ごとにさらにAIを使います。同じ地域の検索は一度だけ行い、同じ地域の二社目からは台帳に入った分を使います。</div>' +
        '<div style="margin-top:6px"><button type="button" class="rbtn" id="tgBulkGo">選んだ会社をまとめて探す</button> ' +
        '<button type="button" class="rc-toggle" id="tgBulkStop" disabled title="いま探している会社が終わったところで止めます">途中で止める</button></div>' +
        '<div id="tgBulkSt"></div>' +
      '</div>' +
      '<div id="tgBulkOut"></div></div>';
    anchor.parentNode.insertBefore(box, anchor);

    [].forEach.call(box.querySelectorAll('input[name=tgSrc]'), function (x) { x.onchange = function () { lsSet(K_SRC, x.value); syncModes(); }; });
    [].forEach.call(box.querySelectorAll('input[name=tgWho]'), function (x) { x.onchange = function () { lsSet(K_WHO, x.value); syncModes(); }; });
    $('tgCap').value = String(capOf());
    $('tgCap').onchange = function () { lsSet(K_CAP, $('tgCap').value); };
    $('tgListSample').onclick = function () { save('﻿' + SAMPLE_CSV, '助成金一覧_見本.csv'); };
    $('tgListClear').onclick = function () {
      if (!confirm('手元の助成金一覧を、この端末から消します。よろしいですか？')) return;
      try { localStorage.removeItem(K_LIST); } catch (e) {}
      renderListSt(); syncModes();
    };
    $('tgListFile').onchange = function (ev) {
      var f = ev.target.files && ev.target.files[0]; if (!f) return;
      var rd = new FileReader();
      rd.onload = function () {
        var el = $('tgListSt');
        try {
          var r = parseCsv(rd.result);
          if (!r.items.length) throw new Error('読み取れる制度の行がありませんでした。');
          if (!lsSet(K_LIST, JSON.stringify({ name: f.name, at: new Date().toISOString(), items: r.items }))) throw new Error('この端末に保存できませんでした。');
          cacheItems(r.items);
          renderListSt(); syncModes();
          if (el) el.textContent += (r.skip ? '（読めなかった行・重なった行 ' + r.skip + '件は外しました）' : '') + '　「新着探索」を押すと、この一覧も探します。';
        } catch (e) {
          if (el) el.textContent = '一覧を読み込めませんでした：' + (e.message || e);
        }
      };
      rd.readAsText(f, 'utf-8');
      ev.target.value = '';
    };
    $('tgBulkGo').onclick = runBulk;
    $('tgBulkStop').onclick = function () { stopReq = true; $('tgBulkStop').disabled = true; var el = $('tgBulkSt'); if (el) el.textContent += '　→ いま探している会社が終わったところで止めます。'; };
    /* 会社の登録が変わったら、まとめて探す会社の一覧も描き直す */
    var sel = $('digCompanySel');
    if (sel && window.MutationObserver) new MutationObserver(function () { if (lsGet(K_WHO, 'one') === 'many') renderCoList(); }).observe(sel, { childList: true });
    renderListSt(); syncModes(); render();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
  window.TriGateBulk = { version: VERSION, render: render, parseCsv: parseCsv };
})();
