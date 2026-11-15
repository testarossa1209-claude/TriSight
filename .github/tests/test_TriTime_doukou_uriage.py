# -*- coding: utf-8 -*-
"""同行の加算を同行した職員の売上に付ける（2026-11-15・宏史さん「それでは稼働した職員の売り上げ成績にはなりません。同行者はかわいそう」）の試験
・モデルコースの稼働率の表で、同行した看護師の行に「うち同行 ◯件（加算 ◯円）」が出て、見込みの売上が0円にならない
・いまの週間予定の売上の合計は、加算をどちらの行に付けても変わらない（担当の行から同じ額が減る）"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

def seed(with_id):
    return """(function(){ var t = Date.now();
  var ST = [ { id:'s1', name:'看護 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['0','6'], upd:t },
    { id:'s2', name:'看護 二子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['0','6'], upd:t },
    { id:'s3', name:'看護 三子', emp:'非常勤', standby:true, job:'看護師（正看）', dept:'訪問看護部', off:['0','6'], upd:t } ];
  var P = [ { no:'2010-01-看-9901', name:'試験 一', area:'東町', status:'利用中', ins:'介護保険', team:'2名', freq:'週1回', wDays:['3'], upd:t } ];
  var W = [ { id:'w1', dow:'3', time:'10:00', min:60, no:'2010-01-看-9901', staffId:'s1', withId:'""" + with_id + """', upd:t } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P));
  localStorage.setItem('tritime_weekly', JSON.stringify(W)); localStorage.setItem('tritime_events', '[]');
  localStorage.setItem('tritime_settings', JSON.stringify({ work:{} })); localStorage.setItem('tritime_dept', 'nurse');
})()"""

async def rate(pg, sd):
    await pg.evaluate(sd); await pg.reload(); await pg.wait_for_timeout(2000)
    await pg.evaluate("document.querySelector('#tabs button[data-tab=model]').click()")
    await pg.wait_for_function("(document.getElementById('md_rate')||{}).innerText && document.getElementById('md_rate').innerText.indexOf('合計') >= 0 && document.getElementById('md_judge').innerText.indexOf('いまの週間予定') >= 0", timeout=30000)
    return (await pg.inner_text('#md_rate')), (await pg.inner_text('#md_judge'))

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        t, j1 = await rate(pg, seed('s2'))
        rows = [l for l in t.split('\n') if l.strip()]
        assert 'うち同行 ' in t and '（加算 ' in t, '同行した看護師の行に、同行の加算が出ません：' + t[:500]
        pl = lambda j: re.findall(r'([\d,]+)円', [l for l in j.split('\n') if 'いまの週間予定' in l][0])
        tot1 = pl(j1)
        t2, j2 = await rate(pg, seed('s3'))   # 同じ看護師の加算で、表にいない人（待機）が同行＝加算は担当に残る
        tot2 = pl(j2)
        assert tot1 and tot2 and tot1[-1] == tot2[-1], '加算を付け替えると、合計の見込みの売上が変わってしまいます：' + str(tot1) + ' / ' + str(tot2)
        await pg.evaluate(seed('s2')); await pg.reload(); await pg.wait_for_timeout(2000)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=model]').click()"); await pg.wait_for_timeout(800)
        await s.shot('#md_rate', 'TriTime_doukou_uriage.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
