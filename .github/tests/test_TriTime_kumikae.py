# -*- coding: utf-8 -*-
"""トライタイムの組み直しの試験（2026-11-03・宏史さん「なんで新しい予定表で島看護師の訪問が1回減ったのか」「分からないから聞いてんだよ」）
・いまの週間予定と同じ職員・同じ曜日で組める訪問は、組み方を出し直してもそのまま残る
・組み方を出すと、いまの週間予定から曜日・担当の変わる訪問と、職員ごとの曜日別の件数の増減が出る
・週間予定に入れた後も、控え（入れ替える前）と今の週間予定の違いが「元に戻す」の下に出る
・入れた直後にもう一度組み方を出すと、変わる訪問は無い（押し直すたびにずれない）"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

ADD = """async (p) => {
  const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', {bubbles:true})); };
  set('st_name', p.name); set('st_dept', p.dept); set('st_emp', p.emp); set('st_job', p.job);
  await new Promise(r => setTimeout(r, 100));
  document.getElementById('st_add').click();
  await new Promise(r => setTimeout(r, 200));
}"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        for x in [{'name':'常勤 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
                  {'name':'常勤 二子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'}]:
            await pg.evaluate(ADD, x)
        await pg.evaluate("""(function(){
          var st = JSON.parse(localStorage.getItem('tritime_staff') || '[]'), a = st.filter(function(s){ return s.name === '常勤 一子'; })[0].id, b = st.filter(function(s){ return s.name === '常勤 二子'; })[0].id, t = Date.now();
          var P = [], W = [];
          for(var i = 1; i <= 8; i++){ var no = '2010-01-看-90' + (i < 10 ? '0' : '') + i; P.push({ no:no, name:'試験 ' + i, area:i <= 5 ? '東町' : '西町', status:'利用中', upd:t }); }
          /* いまの週間予定：二子が 1番を水曜、一子が 6番を金曜に訪問している */
          W.push({ id:'w1', dow:'3', time:'09:15', min:30, no:'2010-01-看-9001', staffId:b, withId:'', upd:t });
          W.push({ id:'w2', dow:'5', time:'09:15', min:30, no:'2010-01-看-9006', staffId:a, withId:'', upd:t });
          localStorage.setItem('tritime_patients', JSON.stringify(P)); localStorage.setItem('tritime_weekly', JSON.stringify(W)); localStorage.removeItem('tritime_weekly_backup'); })()""")
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(400)
        await pg.wait_for_selector('#au_make', state='visible', timeout=15000)
        await pg.click('#au_make'); await pg.wait_for_timeout(800)
        out = await pg.inner_text('#au_out')
        assert 'いまの週間予定から変わる訪問' in out, '組み方を出しても、いまの週間予定から変わる訪問が出ません'
        await pg.evaluate("window.confirm = function(){ return true; }")
        await pg.click('#au_apply'); await pg.wait_for_timeout(500)
        wk = await pg.evaluate("""(function(){ var st = JSON.parse(localStorage.getItem('tritime_staff')); var nm = function(id){ return st.filter(function(s){ return s.id === id; })[0].name; };
          return JSON.parse(localStorage.getItem('tritime_weekly')).filter(function(v){ return !v.del; }).map(function(v){ return [v.no, String(v.dow), nm(v.staffId)]; }); })()""")
        assert ['2010-01-看-9001', '3', '常勤 二子'] in wk, 'いまと同じ職員・同じ曜日（二子・水曜）で組める1番が、組み直しで動きました：' + str([w for w in wk if w[0] == '2010-01-看-9001'])
        assert ['2010-01-看-9006', '5', '常勤 一子'] in wk, 'いまと同じ職員・同じ曜日（一子・金曜）で組める6番が、組み直しで動きました：' + str([w for w in wk if w[0] == '2010-01-看-9006'])
        assert not await pg.query_selector('#au_pdiff'), '入れた後も、入れる前の「いまの週間予定から変わる訪問」が残っています'
        df = await pg.inner_text('#au_diff')
        assert '入れ替える前の週間予定から、今の週間予定で変わった訪問' in df and '週 ' in df, '入れた後に、控えと今の週間予定の違いが出ません：' + df[:200]
        await pg.click('#au_diff summary'); await pg.wait_for_timeout(200)
        await s.shot('#cardAuto', 'TriTime_kumikae_sa.png')
        await pg.click('#au_make'); await pg.wait_for_timeout(800)
        out2 = await pg.inner_text('#au_out')
        assert 'いまの週間予定から、曜日と担当の変わる訪問はありません' in out2, '入れた直後に組み方を出し直すと、訪問がずれます：' + out2[:300]
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
