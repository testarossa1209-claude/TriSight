# -*- coding: utf-8 -*-
"""管理者の端末の「予定」タブのいちばん上に、今月の売上と目標までの残り（2026-11-15・宏史さん「新規利用者週２回であと何人」）の試験
・管理者の端末では「今月の売上と目標」が出て、見込みの売上・目標・達成の見込みが並ぶ
・目標に足りないときは「あと ◯円」と「週2回の新規の利用者さんで、あと ◯人」が出る"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(){ var t = Date.now();
  var ST = [ { id:'s1', name:'看護 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['0','6'], upd:t } ];
  var P = [ { no:'2010-01-看-9801', name:'試験 一', area:'東町', status:'利用中', ins:'介護保険', freq:'週2回', wDays:['1','3'], upd:t },
    { no:'2010-01-看-9802', name:'試験 二', area:'東町', status:'利用中', ins:'介護保険', freq:'週2回', wDays:['2','4'], upd:t } ];
  var W = [ { id:'w1', dow:'1', time:'10:00', min:30, no:'2010-01-看-9801', staffId:'s1', upd:t }, { id:'w2', dow:'3', time:'10:00', min:30, no:'2010-01-看-9801', staffId:'s1', upd:t },
    { id:'w3', dow:'2', time:'10:00', min:30, no:'2010-01-看-9802', staffId:'s1', upd:t }, { id:'w4', dow:'4', time:'10:00', min:30, no:'2010-01-看-9802', staffId:'s1', upd:t } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P));
  localStorage.setItem('tritime_weekly', JSON.stringify(W)); localStorage.setItem('tritime_events', '[]');
  localStorage.setItem('tritime_settings', JSON.stringify({ work:{} })); localStorage.setItem('tritime_dept', 'nurse');
})()"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate(SEED); await pg.reload(); await pg.wait_for_timeout(2000)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=model]').click()"); await pg.wait_for_timeout(600)
        await pg.fill('#md_goal', '10000000'); await pg.click('#md_save'); await pg.wait_for_timeout(600)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(800)
        await pg.wait_for_selector('#cardGoalNow', state='visible', timeout=15000)
        t = await pg.inner_text('#cardGoalNow')
        for w in ['今月の売上と目標', '今月の見込みの売上', '目標の売上', '達成の見込み', '足りません', '週2回の新規の利用者さんで', '人']:
            assert w in t, '「' + w + '」が出ません：' + t[:300]
        await s.shot('#cardGoalNow', 'TriTime_mokuhyo_nokori.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
