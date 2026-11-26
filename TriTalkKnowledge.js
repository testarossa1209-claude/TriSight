/* ============================================================
   TriTalkKnowledge.js — トライトークの秘書が最初から持つ「基礎知識」（2026-11-26 宏史さんの指示）
   ------------------------------------------------------------
   ・「トライサイトシリーズは最初からすべてを知っておいてもらえませんか」
     「ちゃんと質問が来たら、トライロボ同様に秘書連中が説明できるようにしてください」
   ・二つでできている。
       ① CORE … 会社・生い立ち・考え方・秘書の役割・補助金と助成金の基本。毎回の返答に必ず添える（短く保つこと）
       ② 利用解説書（TriRobo.html）の元データ … システムの紹介・場面別の使い方・便利な使い方・システムをまたぐ流れ。
          画面を開くたびに TriRobo.html を読みに行く。解説書を直せば、秘書の知識も自動で新しくなる（二重に持たない）。
          トークンを抑えるため、毎回は全部を送らず、問いに関係する部分だけを選んで送る（chunks と pick）。
   ・ここに書くのは、対外的に話してよいことだけ。社内の事情・個人名・成果を約束する言い方は書かない。
   ============================================================ */
(function(global){
  'use strict';
  var CORE = [
    '【トライサイトの基礎知識（社内資料から作成。ここに無いことは推測で話さない）】',
    '・TriSight®（トライサイト）は、合同会社トライサイトの製品群（トライサイト ファミリー）。TriSight® は合同会社トライサイトの登録商標。各製品名（トライゲイト等）には®を付けない。',
    '・生い立ち：訪問看護・訪問介護・相談支援の現場で実際に起きた問題を、人とAIが一緒に解くところから生まれた。予想して作った問題ではなく、実際の問題を解いてきたことが土台。',
    '・考え方：①出口から逆算する（採択・受理・支給など、現場で決着がつく地点を先に置き、そこから工程を割り出す）。②大きな問題に正面から当たらず、分解して小さくし、解決を積み上げる。③途中の関所で、ずれの向きと量を確かめて直す。④決めるのは人間。AIは人間のパートナーで、判断の材料を出す。⑤Tri は「三」ではなく「トライ（挑戦）」。進化する頭脳・挑戦するサイトを目指す。⑥独占ではなく協業。',
    '・出口から組み立てる仕組みは特許出願中。採択や受給そのものを約束する言い方はしない。',
    '・トライサイトシステム本体では、あずさ（構想・理論AI）が起案を理論に組み立て、なぎさ（検証AI）が筋道と懸念を点検し、つかさ（評価AI）が実現できるかを判定する。最後に判断するのは起案者。',
    '・トライトーク（この画面）は、あずさ・なぎさ・つかさと声や文字で自由に話す画面。右の引き出し「学習資料」に読ませた資料も参考にして答える。',
    '・補助金と助成金は、申請の順番などの約束ごとが違うので、混同させずに分けて説明する。トライゲイトは、制度を探す・説明書を読む・申請書を探して書き方を説明する・申請書類の作成と提出に伴走する・交付決定の後も実施の時期を知らせる・実績報告書の作り方を案内する・支給決定通知書を確かめる、までの一連の流れを受け持つ。',
    '・個別の制度の金額・締切・要件は、年度や公募回で変わる。確かめていないものは「確かめていません」と言い、公募要領など公式の出所で確かめるよう案内する。'
  ].join('\n');

  var RULE = '【製品について聞かれたときの決まり】トライサイトの製品・画面・使い方を聞かれたら、上の基礎知識と、下に添える利用解説書の抜き出しだけを根拠に、トライロボと同じ内容で説明する。「」で囲まれたボタンや欄の名前はそのまま使う。抜き出しに書かれていない機能やボタンは、あると言わない。声で読み上げるので、箇条書きにせず話し言葉で、要点から短く話す。';

  var robo = null, roboErr = '';
  function clean(t){ return String(t == null ? '' : t).replace(/\s+/g, ' ').trim(); }
  /* TriRobo.html の元データ（FLOW〜TIPS）を切り出して読む。同じ配信元の自社のファイルだけを読む */
  function load(){
    if(robo) return Promise.resolve(robo);
    return fetch('TriRobo.html', { cache: 'no-store' }).then(function(r){ if(!r.ok) throw new Error('HTTP ' + r.status); return r.text(); }).then(function(s){
      var i = s.indexOf('var FLOW = '), j0 = s.indexOf('var TIPS = ['), j = j0 >= 0 ? s.indexOf('\n];', j0) : -1;
      if(i < 0 || j < 0) throw new Error('利用解説書の元データが見つかりません');
      var o = new Function(s.slice(i, j + 3) + ';return { FLOW: FLOW, INTRO: INTRO, SCENES: (typeof SCENES !== "undefined" ? SCENES : []), TIPS: (typeof TIPS !== "undefined" ? TIPS : []) };')();
      var names = {}, list = [], out = [];
      o.INTRO.forEach(function(g){
        g.items.forEach(function(it){
          if(it.scr) names[it.scr] = names[it.scr] || it.name;
          list.push(it.name);
          var t = '【システムの紹介】' + it.name + (it.yomi ? '（' + it.yomi + '）' : '') + '：' + clean(it.one) + ' ' + clean(it.what)
            + (it.when ? ' いつ使うか：' + clean(it.when) : '') + (it.inp ? ' 入れるもの：' + clean(it.inp) : '') + (it.out ? ' 出てくるもの：' + clean(it.out) : '') + (it.note ? ' ' + clean(it.note) : '');
          (it.sub || []).forEach(function(x){ t += ' ／' + clean(x.name) + '：' + clean(x.t); });
          out.push({ src: '利用解説書', title: it.name, text: t });
        });
      });
      (o.SCENES || []).forEach(function(sc){
        out.push({ src: '利用解説書', title: sc.title, text: '【場面別の使い方】' + sc.title + '：' + sc.steps.map(function(st, n){ return (n + 1) + '．' + (names[st.s] ? names[st.s] + 'で、' : '') + clean(st.t); }).join(' ') });
      });
      (o.TIPS || []).forEach(function(tp){ out.push({ src: '利用解説書', title: '便利な使い方', text: '【便利な使い方】' + (names[tp.s] ? names[tp.s] + '：' : '') + clean(tp.t) }); });
      if(o.FLOW) out.push({ src: '利用解説書', title: 'システムをまたぐ流れ', text: '【システムをまたぐ流れ】' + clean(o.FLOW) });
      robo = { chunks: out, list: list };
      return robo;
    }).catch(function(e){ roboErr = e.message; robo = null; return null; });
  }
  function status(){ return robo ? ('利用解説書 ' + robo.chunks.length + '項目') : (roboErr ? '利用解説書を読めませんでした（' + roboErr + '）' : '利用解説書を読み込み中'); }

  /* 問いに関係する部分を選ぶ：問いの2文字の並びが、どれだけ含まれるかで点を付ける（AIを使わないのでトークンはかからない） */
  function grams(t){ t = String(t || '').toLowerCase().replace(/[\s　、。，．！？!?「」『』（）()・…:：;；\-]/g, ''); var g = {}; for(var i = 0; i < t.length - 1; i++) g[t.substr(i, 2)] = 1; return g; }
  function pick(query, chunks, maxChars){
    var q = grams(query), keys = Object.keys(q); if(!keys.length) return [];
    var scored = chunks.map(function(c){ var tg = c._g || (c._g = grams(c.text)), n = 0; keys.forEach(function(k){ if(tg[k]) n++; }); return { c: c, n: n / Math.sqrt(1 + c.text.length / 400) }; })
      .filter(function(x){ return x.n > 0; }).sort(function(a, b){ return b.n - a.n; });
    var out = [], len = 0;
    for(var i = 0; i < scored.length; i++){ var t = scored[i].c.text; if(len + t.length > maxChars) continue; out.push(scored[i].c); len += t.length; if(len > maxChars * 0.9) break; }
    return out;
  }
  global.TriTalkKnowledge = { CORE: CORE, RULE: RULE, load: load, status: status, pick: pick, grams: grams, roboChunks: function(){ return robo ? robo.chunks : []; }, roboList: function(){ return robo ? robo.list : []; }, version: '1.0' };
})(typeof window !== 'undefined' ? window : this);
