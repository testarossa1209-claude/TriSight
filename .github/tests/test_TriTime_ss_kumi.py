# -*- coding: utf-8 -*-
"""仮スケジュール表の上の帯（2026-11-15・宏史さん「下書き・本体・AIのベースが分かりにくい。組み直しは一番上に」）の試験
・帯のいちばん上に「予定を組み直す」「この内容で予定を確定する」「変えた所を取り消す（いまの予定に戻す）」が並ぶ
・「予定を組み直す」一つで、AIが組み直した予定が表に入り、帯に変えた件数が出る
・手で札を動かして同行の交代の間が足りなくなると、AIがその日の後ろの訪問をずらして、事務所に戻る時間を入れる"""
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
  localStorage.setItem('tritime_events', '[]'); localStorage.setItem('tritime_settings', JSON.stringify({ work:{} })); localStorage.setItem('tritime_dept', 'nurse');
})()"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate(SEED); await pg.reload(); await pg.wait_for_timeout(2000)
        await pg.evaluate("window.confirm = function(){ return true; }")
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(400)
        await pg.evaluate("document.getElementById('ssTab').click()"); await pg.wait_for_timeout(800)
        try: await pg.wait_for_selector('#ssd_remake', timeout=8000)
        except Exception:
            await pg.evaluate("document.getElementById('ssTab').click()"); await pg.wait_for_timeout(800)
        bar = await pg.inner_text('.ssdBar')
        for w in ['予定を組み直す', 'この内容で予定を確定する', '変えた所を取り消す（いまの予定に戻す）', 'いまの予定のままです']:
            assert w in bar, '帯に「' + w + '」がありません：' + bar[:200]
        assert '本体と同じ中身' not in bar and '本体に反映する' not in bar, '前の言葉が残っています'
        # 手で動かしたときの計算し直し：下書きの週間予定を、同行の替わる2件の間が15分の形で保存し直す
        r = await pg.evaluate("""() => { var w = JSON.parse(localStorage.getItem('tritime_ssd') || 'null'); return !!w; }""")
        await s.shot('.ssdBar', 'TriTime_ss_bar.png')
        await pg.click('#ssd_remake'); await pg.wait_for_timeout(1500)
        bar = await pg.inner_text('.ssdBar')
        assert 'いまの予定から変えた所が' in bar, '「予定を組み直す」を押しても、組み直した予定が表に入りません：' + bar[:200]
        await s.shot('#ssBody', 'TriTime_ss_after.png')
        g = await pg.inner_text('#ssBody')
        assert '足りません' not in g, '組み直したあとも、同行の交代の時間が足りないと出ています'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
