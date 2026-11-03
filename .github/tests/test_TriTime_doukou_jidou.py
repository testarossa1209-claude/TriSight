# -*- coding: utf-8 -*-
"""トライタイムの同行者の自動の付け方の試験（2026-11-03・宏史さん「加藤かんじは2名だろ、同行者は誰なんだよ」）
・体制が「2名」で同行が決まっていない人は、自動の振り分けで同行者が付く
・その患者さんの週の1回目は看護補助者、2回目以降は担当とは別の看護師
・「この組み方を週間予定に入れる」で、付いた同行者が週間予定に入る"""
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
        for x in [{'name':'看護 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
                  {'name':'看護 二子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
                  {'name':'補助 三郎', 'dept':'訪問看護部', 'job':'看護補助者', 'emp':'常勤'}]:
            await pg.evaluate(ADD, x)
        await pg.evaluate("""(function(){ var t = Date.now();
          localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9401', name:'試験 二名', area:'東町', status:'利用中', team:'2名', freq:'週2回', wDays:['2','4'], upd:t } ]));
          localStorage.setItem('tritime_weekly', '[]'); localStorage.removeItem('tritime_weekly_backup'); })()""")
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(400)
        await pg.wait_for_selector('#au_make', state='visible', timeout=15000)
        await pg.click('#au_make'); await pg.wait_for_timeout(800)
        au = await pg.inner_text('#au_out')
        assert '2名・同行 補助 三郎' in au, '週の1回目に、看護補助者が同行に付きません'
        assert '2名・同行 看護' in au, '週の2回目に、看護師が同行に付きません'
        assert '2名・同行未定' not in au, '同行者を付けられる人がいるのに「同行未定」が残っています'
        await s.shot('#cardAuto', 'TriTime_doukou_jidou.png')
        await pg.evaluate("window.confirm = function(){ return true; }")
        await pg.click('#au_apply'); await pg.wait_for_timeout(500)
        wk = await pg.evaluate("""(function(){ var st = JSON.parse(localStorage.getItem('tritime_staff')); var nm = function(id){ var x = st.filter(function(s){ return s.id === id; })[0]; return x ? x.name : ''; };
          return JSON.parse(localStorage.getItem('tritime_weekly')).filter(function(v){ return !v.del; }).sort(function(a, b){ return +a.dow - +b.dow; }).map(function(v){ return [String(v.dow), nm(v.staffId), nm(v.withId)]; }); })()""")
        assert len(wk) == 2, '週2回で入りません：' + str(wk)
        assert wk[0][2] == '補助 三郎', '週の1回目（火）の同行が看護補助者になりません：' + str(wk)
        assert wk[1][2].startswith('看護') and wk[1][2] != wk[1][1], '週の2回目（木）の同行が、担当と別の看護師になりません：' + str(wk)
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
