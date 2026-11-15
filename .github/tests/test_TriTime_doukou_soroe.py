# -*- coding: utf-8 -*-
"""同行を1日通しでそろえる組み方（2026-11-15・宏史さん「なるべく、同行の交代はないような組み方は出来ないのですか？」）の試験
・同じ担当の同じ日に、週1回の人と週2回の人（どちらも2名体制）がいると、その日は看護師が通しで同行し、同行の交代が出ない
・前の予定で同行がばらばら（看護補助者と看護師）でも、組み直すと1人にそろう"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(){ var t = Date.now();
  var ST = [ { id:'s1', name:'看護 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['0','6'], upd:t },
    { id:'s2', name:'看護 二子', emp:'非常勤', job:'看護師（正看）', dept:'訪問看護部', off:['0','6','1','2','4','5'], upd:t },
    { id:'s3', name:'補助 三郎', emp:'常勤', job:'看護補助者', dept:'訪問看護部', off:['0','6'], upd:t } ];
  var P = [ { no:'2010-01-看-9701', name:'試験 一回', area:'東町', status:'利用中', team:'2名', freq:'週1回', wDays:['3'], upd:t },
    { no:'2010-01-看-9702', name:'試験 二回', area:'東町', status:'利用中', team:'2名', freq:'週2回', wDays:['3','5'], upd:t } ];
  var W = [ { id:'w1', dow:'3', time:'09:15', min:30, no:'2010-01-看-9701', staffId:'s1', withId:'s3', upd:t },
    { id:'w2', dow:'3', time:'10:00', min:30, no:'2010-01-看-9702', staffId:'s1', withId:'s2', upd:t } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P));
  localStorage.setItem('tritime_weekly', JSON.stringify(W)); localStorage.removeItem('tritime_weekly_backup');
  localStorage.setItem('tritime_events', '[]'); localStorage.setItem('tritime_settings', JSON.stringify({ work:{} })); localStorage.setItem('tritime_dept', 'nurse');
  localStorage.setItem('tritime_au_caps', JSON.stringify({ f:9, p:5, m:70, n9:1 }));   /* ほかの試験が残した上限を初めの値に戻す */
})()"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate(SEED); await pg.reload(); await pg.wait_for_timeout(2000)
        await pg.evaluate("window.confirm = function(){ return true; }")
        for _ in range(3):
            if not await pg.evaluate("document.body.classList.contains('ssOpen')"):
                await pg.evaluate("document.getElementById('ssTab').click()")
            try:
                await pg.wait_for_selector('#ssd_remake', timeout=15000); break
            except Exception:
                pass
        await pg.click('#ssd_remake')
        await pg.wait_for_function("(document.querySelector('.ssdBar')||{}).innerText && document.querySelector('.ssdBar').innerText.indexOf('いまの予定から変えた所が') >= 0", timeout=20000)
        wk = await pg.evaluate("""() => { var d = JSON.parse(localStorage.getItem('tritime_ss_draft') || 'null'); return d ? d.weekly.filter(function(v){ return v.staffId === 's1' && v.dow === '3'; }).map(function(v){ return [v.time, v.no, v.withId]; }) : null; }""")
        assert wk and len(wk) == 2, '水曜の看護 一子さんの訪問が2件入りません：' + str(wk)
        assert wk[0][2] == wk[1][2], '同じ日に同行が替わっています（そろっていません）：' + str(wk)
        assert wk[0][2] == 's2', '週2回の人がいる日に、看護師が通しで同行していません：' + str(wk)
        g = await pg.inner_text('#ssBody')
        assert '事務所に戻って同行交代' not in g and '足りません' not in g, '同行がそろっているのに、同行交代の印が出ています'
        await s.shot('#ssBody', 'TriTime_doukou_soroe.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
