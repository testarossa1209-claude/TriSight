/*! ===========================================================================
 *  TriEngines.js — TriSight® コモンエンジンの窓口（台帳と呼び出し口）
 *  版：2026-09-25-01
 *  ---------------------------------------------------------------------------
 *  どの子システムからも、6つのコモンエンジンを同じ口で呼ぶための共通部品。
 *
 *  使い方（子システム側）：
 *    <script src="TriEngines.js"></script>
 *    TriEngines.list()                    … 6エンジンの台帳（配列）
 *    TriEngines.get('patriot')            … 1エンジンの台帳
 *    TriEngines.open('triform')           … そのエンジンの画面を開く
 *    TriEngines.read('tribase')           … そのエンジンが残した結果を読む（読むだけ）
 *    TriEngines.send('triform', payload)  … TriForm／TriTaskの受信箱へ案件を渡す
 *    TriEngines.patriot.fromText(会話ログ) … 会話ログから工程の形を取り出す
 *    TriEngines.patriot.check(工程列)      … 運びの形を照合し、逸脱量と減退量を返す
 *    TriEngines.patriot.compare({名前:工程列,…}) … 複数の処理部の報告を対比する
 *
 *  H&Nパトリオットの判定規則（版R1）は、この部品の中で凍結してある。
 *  画面からも呼び出し側からも書き換えられない。更新は、このファイルの版を
 *  差し替えることでしか入らない（特願2026-210277 請求項1・6の考え方）。
 *  照合の結果と人の評価（三計数）は記録するが、規則の更新には使わない。
 * ========================================================================= */
(function (global) {
  'use strict';

  var VERSION = '2026-09-25-01';

  /* ---- 保存領域（file:// 等で localStorage が使えなくても止めない） ---- */
  var store;
  try { var t = '__trieng__'; global.localStorage.setItem(t, '1'); global.localStorage.removeItem(t); store = global.localStorage; }
  catch (e) { var mem = {}; store = { getItem: function (k) { return (k in mem) ? mem[k] : null; }, setItem: function (k, v) { mem[k] = String(v); }, removeItem: function (k) { delete mem[k]; } }; }
  function readJSON(k, fb) { try { var r = store.getItem(k); return r ? JSON.parse(r) : fb; } catch (e) { return fb; } }
  function writeJSON(k, v) { try { store.setItem(k, JSON.stringify(v)); } catch (e) {} }

  /* ======================================================================
     1. 台帳（6エンジン）
     ====================================================================== */
  var REGISTRY = Object.freeze([
    Object.freeze({ id: 'tribase', name: 'TriBase', kind: '画面', status: '稼働',
      role: '法人と事業所を一度だけ登録し、ファミリー各システムが同じ内容を読む',
      page: 'TriBase.html', script: null, outKey: 'trisight_office_master_v1', inKey: null,
      calledBy: 'トライリワード・トライゲイト・トライサイトシステム本体' }),
    Object.freeze({ id: 'triform', name: 'TriForm', kind: '画面', status: '稼働',
      role: '制度の言葉を、手の動く工程へ開く（必要書類・手順・期限を用意する）',
      page: 'TriForm.html', script: 'triform-send.js', outKey: 'tritask_inbox', inKey: 'tritask_inbox',
      calledBy: 'トライグラント・トライゲイト・トライリワード' }),
    Object.freeze({ id: 'tritask', name: 'TriTask', kind: '画面', status: '稼働',
      role: '理論を現場の作業に分け、AIが伴走して完遂まで見届ける',
      page: 'TriTask.html', script: 'triform-send.js', outKey: 'tritask_results', inKey: 'tritask_inbox',
      calledBy: 'すべてのシステム' }),
    Object.freeze({ id: 'trivoice', name: 'TriVoice', kind: '部品（画面なし）', status: '稼働',
      role: '話した内容を文字に起こし、各帳票の欄へ振り分ける共通音声エンジン',
      page: null, script: 'TriVoiceEngine.js', outKey: null, inKey: null,
      usedIn: 'TriVoice.html（看護メモ・トライケア簡易版）',
      calledBy: 'トライケア・トライサイトシステム本体' }),
    Object.freeze({ id: 'numeric', name: '数値解析ロボ', kind: '画面', status: '稼働',
      role: '生の試算表から数値を判断せずに抜き出し、構造化する',
      page: 'TriSight_NumericParser_v3.html', script: null, outKey: 'trisight_parser_output', inKey: null,
      calledBy: 'トライリワード・トライサイトシステム本体' }),
    Object.freeze({ id: 'patriot', name: 'H&Nパトリオット', kind: '画面＋部品', status: '実験機（版R1）',
      role: '理論が作られた運びの形を外側から照合し、逸脱の大きさに応じて効力を削る',
      page: 'TriPatriot.html', script: 'TriEngines.js', outKey: 'trisight_patriot_log_v1', inKey: null,
      calledBy: 'すべてのシステム（自分の理論に撃ち込む）' })
  ]);

  function list() { return REGISTRY.slice(); }
  function get(id) { for (var i = 0; i < REGISTRY.length; i++) if (REGISTRY[i].id === id) return REGISTRY[i]; return null; }
  function need(id) { var e = get(id); if (!e) throw new Error('コモンエンジン「' + id + '」は台帳にありません'); return e; }

  function open(id) {
    var e = need(id);
    if (!e.page) throw new Error(e.name + ' は画面を持たない部品です。' + (e.usedIn ? '使用例：' + e.usedIn : ''));
    global.location.href = e.page;
  }
  function read(id) {
    var e = need(id);
    if (!e.outKey) return null;
    return readJSON(e.outKey, null);
  }
  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = global.document.createElement('script');
      s.src = src; s.onload = resolve; s.onerror = function () { reject(new Error(src + ' を読み込めませんでした')); };
      global.document.head.appendChild(s);
    });
  }
  /* TriForm／TriTaskへ渡す。送り方は triform-send.js に一本化してあるので、それに任せる */
  function send(id, payload) {
    var e = need(id);
    if (e.id !== 'triform' && e.id !== 'tritask') {
      return Promise.reject(new Error(e.name + ' は案件を受け取る口を持っていません（受け取れるのはTriForm・TriTask）'));
    }
    var go = function () { return global.TriSightSend.send(payload); };
    if (global.TriSightSend && global.TriSightSend.send) return Promise.resolve(go());
    return loadScript('triform-send.js').then(go);
  }

  /* ======================================================================
     2. H&Nパトリオット（実験機・版R1）
        出典：特願2026-210277 明細書【0027】〜【0041】、図2・図3
     ====================================================================== */

  /* 工程の種別（内容語を除いた「何をしたか」だけの語彙） */
  var STEP = Object.freeze({
    SEARCH: '記録検索', ASK_PROVIDE: '人への提供要求', GET_OBJ: '対象物取得', OUT_OBJ: '対象物に関する出力',
    SELF_GEN: '自己生成', GET_REAL: '実物取得', FIX_ORDER: '修正指示', LIST_OPT: '選択肢列挙',
    SELF_DECIDE: '自己決定', ASK_CHOOSE: '人への選択要求', POINTED: '指摘受領', RETHINK: '再検討',
    KEEP: '維持', TOPIC: '主題切替', RETURN: '主題復帰', OUTPUT: '出力'
  });

  /* 判定規則群（版R1）— 凍結。重みと段階表は2026-09-19の決定値 */
  var RULES = Object.freeze({
    version: 'R1',
    weights: Object.freeze({ A: 2, B: 2, C: 3, D: 1, E: 2, F: 3, G: 1 }),
    names: Object.freeze({ A: '再要求型', B: '現物不参照型', C: '手元計算の実物視型', D: '選択転嫁型', E: '本題逸脱型', F: '自己防御型', G: '膨張型' }),
    conditions: Object.freeze({
      A: '「人への提供要求」の直前に「記録検索」が無い',
      B: '「対象物に関する出力」の前方に「対象物取得」が無い',
      C: '「修正指示」の根拠が「自己生成」で、「実物取得」を経ていない',
      D: '「選択肢列挙」の後に「自己決定」が無く、「人への選択要求」がある',
      E: 'AIが主題を切り替えた後、元の主題へ戻らない',
      F: '「指摘受領」の直後が「維持」で、「再検討」を経ない',
      G: '一回の出力の分量が、同じ記録の中央値の所定倍以上'
    }),
    gRatio: 2,          /* 膨張型の所定倍：版R1の設定値（実験で見直す） */
    gMinSamples: 3,     /* 中央値を取るのに要る出力の数 */
    stages: Object.freeze([
      Object.freeze({ upTo: 1, rate: 0 }),     /* D＜1    → 0％ */
      Object.freeze({ upTo: 3, rate: 25 }),    /* 1≦D＜3 → 25％ */
      Object.freeze({ upTo: 6, rate: 50 }),    /* 3≦D＜6 → 50％ */
      Object.freeze({ upTo: Infinity, rate: 100 }) /* D≧6 → 100％ */
    ])
  });

  function stageOf(D) {
    for (var i = 0; i < RULES.stages.length; i++) if (D < RULES.stages[i].upTo) return RULES.stages[i].rate;
    return 100;
  }
  function median(a) {
    var s = a.slice().sort(function (x, y) { return x - y; }); var n = s.length;
    if (!n) return 0; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2;
  }

  /* 照合部：工程列（{k:種別, by:'ai'|'human', len?:数}の配列）を型と突き合わせる。決定論的 */
  function check(steps) {
    if (!Array.isArray(steps)) throw new Error('工程列は配列で渡してください');
    var S = STEP, hits = {}, i, j;
    function hit(type, at) { (hits[type] = hits[type] || []).push(at); }
    for (i = 0; i < steps.length; i++) {
      var k = steps[i].k;
      /* A 再要求型 */
      if (k === S.ASK_PROVIDE && !(i > 0 && steps[i - 1].k === S.SEARCH)) hit('A', i);
      /* B 現物不参照型 */
      if (k === S.OUT_OBJ) {
        var got = false; for (j = 0; j < i; j++) if (steps[j].k === S.GET_OBJ) { got = true; break; }
        if (!got) hit('B', i);
      }
      /* C 手元計算の実物視型 */
      if (k === S.FIX_ORDER) {
        var lastSelf = -1, lastReal = -1;
        for (j = 0; j < i; j++) { if (steps[j].k === S.SELF_GEN) lastSelf = j; if (steps[j].k === S.GET_REAL) lastReal = j; }
        if (lastSelf >= 0 && lastReal < lastSelf) hit('C', i);
      }
      /* D 選択転嫁型 */
      if (k === S.ASK_CHOOSE) {
        var lastList = -1; for (j = i - 1; j >= 0; j--) if (steps[j].k === S.LIST_OPT) { lastList = j; break; }
        if (lastList >= 0) {
          var decided = false; for (j = lastList + 1; j < i; j++) if (steps[j].k === S.SELF_DECIDE) { decided = true; break; }
          if (!decided) hit('D', i);
        }
      }
      /* E 本題逸脱型：AIが切り替えた後、以後に主題復帰が無い */
      if (k === S.TOPIC && steps[i].by === 'ai') {
        var back = false; for (j = i + 1; j < steps.length; j++) if (steps[j].k === S.RETURN) { back = true; break; }
        if (!back) hit('E', i);
      }
      /* F 自己防御型：指摘の直後（人の工程を除く最初のAIの工程）が維持 */
      if (k === S.POINTED) {
        for (j = i + 1; j < steps.length; j++) {
          if (steps[j].by === 'human') continue;
          if (steps[j].k === S.KEEP) hit('F', j);
          break;
        }
      }
    }
    /* G 膨張型 */
    var lens = [], lenAt = [];
    for (i = 0; i < steps.length; i++) if (typeof steps[i].len === 'number' && steps[i].len > 0) { lens.push(steps[i].len); lenAt.push(i); }
    var med = 0;
    if (lens.length >= RULES.gMinSamples) {
      med = median(lens);
      for (i = 0; i < lens.length; i++) if (lens[i] >= RULES.gRatio * med) hit('G', lenAt[i]);
    }
    /* 逸脱量＝該当した型ごとに重みを加算（同じ型は何度出ても一回） */
    var D = 0, types = [];
    'ABCDEFG'.split('').forEach(function (t) { if (hits[t]) { D += RULES.weights[t]; types.push(t); } });
    return {
      version: RULES.version, D: D, rate: stageOf(D), types: types,
      hits: types.map(function (t) { return { type: t, name: RULES.names[t], weight: RULES.weights[t], condition: RULES.conditions[t], at: hits[t].slice() }; }),
      median: med, steps: steps.length
    };
  }

  /* 過程取得部（実験機）：会話ログから、内容語を除いた工程の形を取り出す。
     手掛かりは「何をしたか」を表す言い回しだけを使い、題材の語は見ない。 */
  var CUE = Object.freeze({
    search:   /(過去ログ|記録|履歴|会話).{0,6}(検索|当た|確か|見|読)|検索し(ま|た)|当たりま|当たります|記録を(見|読)/,
    getObj:   /(取得し|取ってき|取り寄せ|開いて(確|見|読)|読み込|現物|実物を|中身を(確|見|読)|読み直)/,
    askProv:  /(アップロードして|添付して|貼り付けて|送って|提供して|共有して|入れて|出して|用意して|入力して|教えて)(ください|下さい|いただけ|もらえ)|ご提供(ください|をお願い)|ご教示(ください|をお願い)|お送りください/,
    outObj:   /(ボタン|画面|欄|セル|メニュー|タブ|ファイル|リンク|列|行).{0,14}(押して|開いて|選んで|クリック|入力して|入れて|書き換え|貼って)/,
    selfGen:  /(試算|手元で|私の計算|推定|見込ん|仮に置|計算すると|計算し(ま|た))/,
    fixOrd:   /(直して|修正して|変更して|打ち替えて|書き換えて|入れ直して|差し替えて)(ください|下さい)/,
    listOpt:  /(案[ＡＢCＣA-B１-３1-3]|選択肢|方法は[二三2-3]つ|次のいずれか|①.{1,40}②)/,
    askCh:    /(どちら|どれ|いずれ)(に|を|が|で)?.{0,10}(しますか|しましょうか|よいですか|いいですか|でしょうか|お選び)|ご判断(ください|をお願い)|選んでください/,
    decide:   /(私の判断|と判断します|で進めます|を採ります|にします(?!か)|で決めます|こちらで決め)/,
    keep:     /(誤りではありません|問題はありません|問題ありません|正しいです|そのままで(よい|問題)|守れています|変わりません)(?!か)/,
    rethink:  /(見直し|取り下げ|誤りでした|訂正|当たり直|調べ直|確かめ直|私の誤り|間違えていました)/,
    pointed:  /(違う|違います|ちがう|おかしい|間違|誤り|なぜ|なんで|だめ|ダメ|何度も|いちいち)/,
    aiTopic:  /(ところで|ついでに|別件ですが|話は変わ|あわせて別の)/,
    humTopic: /^(続いて|次に|では次|話を変え|別件)/,
    back:     /(本題に戻|元の話|先ほどの件に戻|さっきの|戻って)/
  });

  function splitTurns(text) {
    var lines = String(text || '').replace(/\r/g, '').split('\n'), turns = [], cur = null;
    var head = /^\s*(H|A|人|AI|User|Assistant|宏史|なぎさ|あずさ|つかさ|ユーザー|アシスタント)\s*[:：]\s*/;
    var aiNames = /^(A|AI|Assistant|なぎさ|あずさ|つかさ|アシスタント)$/;
    lines.forEach(function (ln) {
      var m = ln.match(head);
      if (m) { cur = { by: aiNames.test(m[1]) ? 'ai' : 'human', text: ln.replace(head, '') }; turns.push(cur); }
      else if (cur) cur.text += '\n' + ln;
    });
    return turns;
  }

  function fromText(text) {
    var turns = splitTurns(text), steps = [], S = STEP, C = CUE;
    if (!turns.length) throw new Error('話者の区切り（「H:」「A:」など）が見つかりません');
    turns.forEach(function (t, ti) {
      var body = t.text.trim();
      if (t.by === 'human') {
        if (C.humTopic.test(body)) steps.push({ k: S.TOPIC, by: 'human', turn: ti });
        if (C.back.test(body)) steps.push({ k: S.RETURN, by: 'human', turn: ti });
        if (C.pointed.test(body)) steps.push({ k: S.POINTED, by: 'human', turn: ti });
        return;
      }
      /* AIの発話：文ごとに工程を取り出す */
      var sentences = body.replace(/([。！？\n])/g, '$1\u0000').split('\u0000');
      sentences.forEach(function (s) {
        s = s.trim(); if (!s) return;
        if (C.rethink.test(s)) steps.push({ k: S.RETHINK, by: 'ai', turn: ti });
        if (C.keep.test(s) && !/[？?]\s*$/.test(s)) steps.push({ k: S.KEEP, by: 'ai', turn: ti });
        if (C.search.test(s)) steps.push({ k: S.SEARCH, by: 'ai', turn: ti });
        if (C.getObj.test(s)) { steps.push({ k: S.GET_OBJ, by: 'ai', turn: ti }); steps.push({ k: S.GET_REAL, by: 'ai', turn: ti }); }
        if (C.selfGen.test(s)) steps.push({ k: S.SELF_GEN, by: 'ai', turn: ti });
        if (C.aiTopic.test(s)) steps.push({ k: S.TOPIC, by: 'ai', turn: ti });
        if (C.back.test(s)) steps.push({ k: S.RETURN, by: 'ai', turn: ti });
        if (C.listOpt.test(s)) steps.push({ k: S.LIST_OPT, by: 'ai', turn: ti });
        var asking = C.askCh.test(s) || /[？?]\s*$/.test(s);
        if (C.decide.test(s) && !asking) steps.push({ k: S.SELF_DECIDE, by: 'ai', turn: ti });
        if (C.askProv.test(s)) steps.push({ k: S.ASK_PROVIDE, by: 'ai', turn: ti });
        if (C.outObj.test(s)) steps.push({ k: S.OUT_OBJ, by: 'ai', turn: ti });
        if (C.fixOrd.test(s)) steps.push({ k: S.FIX_ORDER, by: 'ai', turn: ti });
        if (C.askCh.test(s)) steps.push({ k: S.ASK_CHOOSE, by: 'ai', turn: ti });
      });
      steps.push({ k: S.OUTPUT, by: 'ai', turn: ti, len: body.length });
    });
    return steps;
  }

  /* 工程列を1行1工程の文字で受ける（「記録検索」「主題切替 ai」「出力 350」など） */
  function fromLines(text) {
    var names = {}; Object.keys(STEP).forEach(function (k) { names[STEP[k]] = true; });
    var steps = [], bad = [];
    String(text || '').split(/\r?\n/).forEach(function (ln, i) {
      var p = ln.trim().split(/\s+/); if (!p[0]) return;
      if (!names[p[0]]) { bad.push((i + 1) + '行目「' + p[0] + '」'); return; }
      var st = { k: p[0], by: (p[1] === 'human' || p[1] === '人') ? 'human' : 'ai' };
      var n = Number(p[1] && /^\d+$/.test(p[1]) ? p[1] : p[2]); if (n > 0) st.len = n;
      steps.push(st);
    });
    if (bad.length) throw new Error('工程の種別として読めない行があります：' + bad.join('、'));
    return steps;
  }

  /* 対比部：複数の処理部の報告を並べ、一者にのみ現れる型＝その処理部に固有の逸脱 */
  function compare(reports) {
    var names = Object.keys(reports || {}); if (names.length < 2) throw new Error('対比には2つ以上の報告が要ります');
    var res = {}, count = {};
    names.forEach(function (n) { res[n] = check(reports[n]); res[n].types.forEach(function (t) { count[t] = (count[t] || 0) + 1; }); });
    var own = {}, common = [];
    names.forEach(function (n) {
      var ownTypes = res[n].types.filter(function (t) { return count[t] === 1; });
      var D = 0; ownTypes.forEach(function (t) { D += RULES.weights[t]; });
      own[n] = { types: ownTypes, D: D, rate: stageOf(D) };
    });
    Object.keys(count).forEach(function (t) { if (count[t] === names.length) common.push(t); });
    return { version: RULES.version, each: res, own: own, common: common };
  }

  /* 記録部：照合結果と人の評価（三計数）を残す。規則の更新には使わない */
  var LOG_KEY = 'trisight_patriot_log_v1';
  function logs() { return readJSON(LOG_KEY, []); }
  function record(result, meta) {
    var a = logs();
    var row = { id: 'p' + Date.now().toString(36), at: new Date().toISOString(), version: result.version,
      D: result.D, rate: result.rate, types: result.types.slice(), source: (meta && meta.source) || '', verdict: '' };
    a.push(row); writeJSON(LOG_KEY, a); return row.id;
  }
  function judge(id, verdict) {
    if (['stopped', 'missed', 'over'].indexOf(verdict) < 0) throw new Error('評価は stopped／missed／over のいずれかです');
    var a = logs(); for (var i = 0; i < a.length; i++) if (a[i].id === id) { a[i].verdict = verdict; writeJSON(LOG_KEY, a); return true; }
    return false;
  }
  function counts() {
    var c = { stopped: 0, missed: 0, over: 0, pending: 0, total: 0 };
    logs().forEach(function (r) { c.total++; if (c[r.verdict] !== undefined && r.verdict) c[r.verdict]++; else c.pending++; });
    return c;
  }
  function clearLogs() { writeJSON(LOG_KEY, []); }

  global.TriEngines = Object.freeze({
    version: VERSION, list: list, get: get, open: open, read: read, send: send,
    patriot: Object.freeze({
      STEP: STEP, rulesVersion: RULES.version,
      rulesView: function () { return JSON.parse(JSON.stringify(RULES, function (k, v) { return v === Infinity ? '∞' : v; })); },
      fromText: fromText, fromLines: fromLines, check: check, compare: compare,
      record: record, judge: judge, counts: counts, logs: logs, clearLogs: clearLogs
    })
  });
})(typeof window !== 'undefined' ? window : this);
