# -*- coding: utf-8 -*-
"""トライタイムの「予定表の作り方を選ぶ」の試験（2026-11-05・宏史さんの指示「作り方を選ばせる引き出しが必要」）
・本スケジュール表の上にオレンジの「予定表の作り方を選ぶ」が出る（予定を組む人の端末）
・押すと小窓に「AIが作る」「AIがベースを作って自分で直す」「自分で作る」の三つのボタンが出る
・「自分で作る」→ 空の手組みの表が開く
・「AIがベースを作って自分で直す」→ いまの週間予定（11件）が手組みの表に写って開く
・「AIが作る」→ 自動の振り分けの枠が表示される
・使い方（右の引き出し）に「予定表の作り方を選ぶ」の説明がある
・画面の中で誤りが出ない"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(t){
  var up = Date.now();
  var ST = [
    { id:'s1', name:'常勤 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['4','0'], upd:up },
    { id:'s2', name:'常勤 二子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['6','0'], upd:up },
    { id:'s3', name:'非常勤 三子', emp:'非常勤', job:'准看護師', dept:'訪問看護部', off:['1','3','5','6','0'], upd:up },
    { id:'s4', name:'補助 四子', emp:'非常勤', job:'看護補助者', dept:'訪問看護部', off:['6','0'], upd:up } ];
  var P = [
    { no:'2010-01-看-9001', name:'試験 太郎', area:'東町', status:'利用中', ins:'精神科訪問看護（医療）', wDays:['1','3'], wish:'09:30', freq:'週2回', upd:up },
    { no:'2010-01-看-9002', name:'試験 花子', area:'東町', status:'利用中', ins:'精神科訪問看護（医療）', ngDays:['2'], freq:'週2回', upd:up },
    { no:'2010-01-看-9003', name:'試験 一郎', area:'西町', status:'利用中', ins:'精神科訪問看護（医療）', team:'2名', freq:'週3回', upd:up },
    { no:'2010-01-看-9004', name:'試験 次郎', area:'南町', status:'利用中', ins:'精神科訪問看護（医療）', wBand:'午前', freq:'週1回', upd:up },
    { no:'2010-01-看-9005', name:'試験 三郎', area:'北町', status:'利用中', ins:'精神科訪問看護（医療）', freq:'週2回', upd:up } ];
  var W = [
    { id:'w1', dow:'1', time:'09:30', min:30, no:'2010-01-看-9001', staffId:'s1', upd:up },
    { id:'w2', dow:'2', time:'10:00', min:30, no:'2010-01-看-9001', staffId:'s1', upd:up },
    { id:'w3', dow:'1', time:'10:40', min:30, no:'2010-01-看-9002', staffId:'s1', upd:up },
    { id:'w4', dow:'2', time:'11:30', min:30, no:'2010-01-看-9002', staffId:'s2', upd:up },
    { id:'w5', dow:'2', time:'09:00', min:30, no:'2010-01-看-9003', staffId:'s2', upd:up },
    { id:'w6', dow:'3', time:'09:00', min:30, no:'2010-01-看-9003', staffId:'s2', withId:'s4', upd:up },
    { id:'w7', dow:'5', time:'09:00', min:30, no:'2010-01-看-9003', staffId:'s2', withId:'s4', upd:up },
    { id:'w8', dow:'1', time:'14:00', min:30, no:'2010-01-看-9004', staffId:'s2', upd:up },
    { id:'w9', dow:'1', time:'11:00', min:30, no:'2010-01-看-9005', staffId:'s2', upd:up },
    { id:'w10', dow:'4', time:'09:00', min:30, no:'2010-01-看-9005', staffId:'s1', upd:up },
    { id:'w11', dow:'1', time:'11:40', min:30, no:'2010-01-看-9001', staffId:'s1', hv:true, why:'人情変更（相性）', note:'本人の希望', upd:up } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P)); localStorage.setItem('tritime_weekly', JSON.stringify(W));
  localStorage.setItem('tritime_events', '[]'); localStorage.setItem('tritime_settings', JSON.stringify({ work:{ mv20:1, mvMin:10, mvMax:20 } }));
  localStorage.setItem('tritime_device', JSON.stringify({ me:'s1', share:false })); localStorage.setItem('tritime_dept', 'nurse');
})()"""

async def tap(pg, sel):
    await pg.evaluate("document.querySelector(%s).click()" % repr(sel))

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate(SEED)
        await pg.reload(); await pg.wait_for_timeout(1200)
        await pg.evaluate("window.confirm = function(){ return true; }")
        await tap(pg, '#tabs button[data-tab=plan]'); await pg.wait_for_timeout(300)
        await pg.wait_for_selector('#td_staff option[value="*"]', state='attached', timeout=15000)
        await pg.evaluate("var e = document.getElementById('td_staff'); e.value = '*'; e.dispatchEvent(new Event('change'));")
        await pg.wait_for_selector('#td_week .ssChip', state='attached', timeout=15000); await pg.wait_for_timeout(300)
        assert await pg.query_selector('#pw_open'), '「予定表の作り方を選ぶ」のボタンがありません'
        await tap(pg, '#pw_open'); await pg.wait_for_timeout(300)
        for i in ['pw_ai', 'pw_mix', 'pw_hand']:
            assert await pg.query_selector('#ssMv #' + i), '小窓に ' + i + ' がありません'
        txt = await pg.inner_text('#ssMv .card')
        for w in ['AIが作る', 'AIがベースを作って自分で直す', '自分で作る', '11件']:
            assert w in txt, '小窓に「' + w + '」がありません'
        await s.shot('#ssMv .card', 'TriTime_pw_1.png')
        # 自分で作る → 空の表
        await tap(pg, '#pw_hand'); await pg.wait_for_timeout(500)
        assert not await pg.query_selector('#ssMv'), '小窓が閉じません'
        assert await pg.evaluate("document.querySelectorAll('#hbBox .hbGrid').length") == 1, '「自分で作る」で手組みの表が開きません'
        assert await pg.evaluate("document.querySelectorAll('#hbBox .hbGrid .hbFuda').length") == 0, '「自分で作る」なのに札が置かれています'
        # AIがベース → 写る
        await tap(pg, '#pw_open'); await pg.wait_for_timeout(300)
        await tap(pg, '#pw_mix'); await pg.wait_for_timeout(600)
        assert await pg.evaluate("document.querySelectorAll('#hbBox .hbGrid .hbFuda').length") == 11, '「AIがベースを作って自分で直す」で週間予定（11件）が写りません'
        assert '写しました' in await pg.inner_text('#hb_msg')
        await s.shot('#hbBox', 'TriTime_pw_2.png')
        # AIが作る → 枠へ
        await tap(pg, '#pw_open'); await pg.wait_for_timeout(300)
        await tap(pg, '#pw_ai'); await pg.wait_for_timeout(400)
        assert await pg.evaluate("getComputedStyle(document.getElementById('cardAuto')).display") != 'none', '「AIが作る」で自動の振り分けの枠が出ません'
        # 使い方
        found = await pg.evaluate("Array.from(document.scripts).some(function(sc){ return sc.textContent.indexOf(\"['まず「予定表の作り方を選ぶ」'\") >= 0; })")
        assert found, '使い方に「予定表の作り方を選ぶ」の説明がありません'
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
