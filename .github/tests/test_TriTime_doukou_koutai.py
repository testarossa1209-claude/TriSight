# -*- coding: utf-8 -*-
"""トライタイムの同行の交代（2026-11-15・宏史さん「事務所を通過点にしたコース取りで、看護補助者の入れ替えを予定に入れる」）の試験
・同じ担当の同じ日に、週1回の人（同行＝看護補助者）と週2回の人（同行＝看護師）が続くと、同行が替わる
・組み方を出すと、替わる所は「事務所に戻って同行交代（戻り・交代・出発）」と出て、時間が足りないという赤い文字は出ない
・組み方の上に「事務所を通って同行を替える所」が出る"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(){ var t = Date.now();
  var ST = [ { id:'s1', name:'看護 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['0','6'], upd:t },
    { id:'s2', name:'看護 二子', emp:'非常勤', job:'看護師（正看）', dept:'訪問看護部', off:['0','6','1','2','4','5'], upd:t },
    { id:'s3', name:'補助 三郎', emp:'常勤', job:'看護補助者', dept:'訪問看護部', off:['0','6'], upd:t } ];
  var P = [ { no:'2010-01-看-9501', name:'試験 一回', area:'東町', status:'利用中', team:'2名', freq:'週1回', wDays:['3'], upd:t },
    { no:'2010-01-看-9502', name:'試験 二回', area:'東町', status:'利用中', team:'2名', freq:'週2回', wDays:['3','5'], upd:t } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P));
  localStorage.setItem('tritime_weekly', '[]'); localStorage.removeItem('tritime_weekly_backup');
  localStorage.setItem('tritime_events', '[]'); localStorage.setItem('tritime_settings', JSON.stringify({ work:{} }));
  localStorage.setItem('tritime_dept', 'nurse');
})()"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate(SEED); await pg.reload(); await pg.wait_for_timeout(2000)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(400)
        await pg.evaluate("document.getElementById('ssTab').click(); document.getElementById('ssAi').open = true"); await pg.wait_for_timeout(300)
        try: await pg.wait_for_selector('#au_make', state='visible', timeout=8000)
        except Exception:
            await pg.evaluate("document.getElementById('ssTab').click(); document.getElementById('ssAi').open = true"); await pg.wait_for_timeout(500)
        await pg.evaluate("document.getElementById('au_part').value = '1'")   # 非常勤の看護師は1日1件まで＝同じ同行者を続けて付けられず、同行が替わる日を作る
        await pg.click('#au_make'); await pg.wait_for_timeout(1000)
        au = await pg.inner_text('#au_out')
        assert '足りません' not in au, '同行の交代の所に、時間が足りないという文字が出ています：' + au[:300]
        assert '事務所に戻って同行交代' in au, '同行が替わる所に、事務所に戻って交代する時間が入っていません：' + au[:600]
        assert '事務所を通って同行を替える所：1か所' in au, '組み方の上に、事務所を通って同行を替える所の数が出ません：' + au[:300]
        await s.shot('#cardAuto', 'TriTime_doukou_koutai.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
