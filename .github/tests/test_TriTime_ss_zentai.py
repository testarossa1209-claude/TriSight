# -*- coding: utf-8 -*-
"""仮スケジュール表を「全体（経営企画事務職）」で開いたとき（2026-11-15・宏史さん「仮スケジュール表の一番上に３つのボタンがならんでいません」）の試験
・いちばん上に「訪問看護部の予定を組み直す・確定する」が出る
・押すと訪問看護部の表に切り替わり、いちばん上に「予定を組み直す」「この内容で予定を確定する」が出る"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(){ var t = Date.now();
  var ST = [ { id:'s1', name:'看護 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['0','6'], upd:t },
    { id:'s2', name:'看護 二子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['0','6'], upd:t },
    { id:'s3', name:'補助 三郎', emp:'常勤', job:'看護補助者', dept:'訪問看護部', off:['0','6'], upd:t } ];
  var P = [ { no:'2010-01-看-9601', name:'試験 一', area:'東町', status:'利用中', team:'2名', freq:'週1回', wDays:['3'], upd:t },
    { no:'2010-01-看-9602', name:'試験 二', area:'東町', status:'利用中', team:'2名', freq:'週1回', wDays:['3'], upd:t } ];
  var W = [ { id:'w1', dow:'3', time:'09:15', min:30, no:'2010-01-看-9601', staffId:'s1', withId:'s3', upd:t },
    { id:'w2', dow:'3', time:'10:00', min:30, no:'2010-01-看-9602', staffId:'s1', withId:'s2', upd:t } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P));
  localStorage.setItem('tritime_weekly', JSON.stringify(W)); localStorage.removeItem('tritime_weekly_backup');
  localStorage.setItem('tritime_events', '[]'); localStorage.setItem('tritime_settings', JSON.stringify({ work:{} })); localStorage.setItem('tritime_dept', 'office');
})()"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate(SEED); await pg.reload(); await pg.wait_for_timeout(2000)
        await pg.evaluate("""() => { localStorage.setItem('tritime_dept', 'office'); var b = document.querySelector('#deptBar [data-dept=office]'); if(b){ b.click(); return; }
          var sl = document.getElementById('deptSel'); if(sl){ sl.value = 'office'; sl.dispatchEvent(new Event('change')); } }""")
        await pg.wait_for_timeout(500)
        for _ in range(3):
            if not await pg.evaluate("document.body.classList.contains('ssOpen')"):
                await pg.evaluate("document.getElementById('ssTab').click()")
            try:
                await pg.wait_for_selector('[data-ssgo=nurse]', timeout=15000); break
            except Exception:
                pass
        t = await pg.inner_text('#ssGrid')
        assert '訪問看護部の予定を組み直す・確定する' in t, '全体で開いたとき、いちばん上に部署の入口がありません：' + t[:200]
        await s.shot('#ssBody', 'TriTime_ss_office.png')
        await pg.click('[data-ssgo=nurse]')
        await pg.wait_for_selector('#ssd_remake', timeout=15000)
        bar = await pg.inner_text('.ssdBar')
        assert '予定を組み直す' in bar and 'この内容で予定を確定する' in bar, '切り替えた後に3つのボタンが出ません：' + bar[:200]
        assert await pg.evaluate("localStorage.getItem('tritime_dept')") == 'nurse', '部署が訪問看護部に切り替わっていません'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
