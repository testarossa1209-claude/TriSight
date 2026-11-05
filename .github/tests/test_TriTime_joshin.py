# -*- coding: utf-8 -*-
"""トライタイムの「一般の職員は予定を変えず、管理者へ上申する」の試験（2026-11-05 昼・渋谷さんのヒアリングを受けた宏史さんの決め）
端末＝共有あり・主に使う人＝常勤 一子（合言葉なし＝一般の職員）。常勤 二子は管理者。
・本スケジュール表の札が動かせる印（dg）にならない（予定の変更は管理者・事務局だけ）
・「空の表から組む」「予定表の作り方を選ぶ」「H&Nパトリオット」のボタンが出ない
・「管理者へ上申する」のボタンが出て、窓に利用者・種類・内容が入る。宛先が部門の管理者（常勤 二子）
・「上申する」で連絡板の知らせ（type note・kind 上申）が管理者あてで残る。内容が空なら止まる
・画面の中で誤りが出ない"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(t){
  var up = Date.now();
  var ST = [
    { id:'s1', name:'常勤 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['4','0'], upd:up },
    { id:'s2', name:'常勤 二子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', mgr:true, off:['6','0'], upd:up },
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
  localStorage.setItem('tritime_device', JSON.stringify({ me:'s1', share:true })); localStorage.setItem('tritime_dept', 'nurse');
})()"""

async def tap(pg, sel):
    await pg.evaluate("document.querySelector(%s).click()" % repr(sel))

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate(SEED)
        await pg.reload(); await pg.wait_for_timeout(1500)
        await pg.evaluate("window.ALERTS = []; window.alert = function(m){ window.ALERTS.push(String(m)); };")
        await tap(pg, '#tabs button[data-tab=plan]'); await pg.wait_for_timeout(400)
        await pg.wait_for_selector('#td_week .ssChip', state='attached', timeout=15000); await pg.wait_for_timeout(300)
        assert await pg.evaluate("document.querySelectorAll('#td_week .ssChip.dg').length") == 0, '一般の職員の端末で札が動かせる印になっています'
        for i in ['hb_open', 'pw_open', 'ptr_td']:
            assert not await pg.query_selector('#' + i), '一般の職員の端末に ' + i + ' が出ています'
        assert await pg.query_selector('#js_open'), '「管理者へ上申する」のボタンがありません'
        await tap(pg, '#js_open'); await pg.wait_for_timeout(300)
        card = await pg.inner_text('#ssMv .card')
        assert '常勤 二子さん' in card, '宛先に部門の管理者が出ません：' + card[:120]
        opts = await pg.eval_on_selector_all('#js_pt option', "os => os.map(o => o.textContent)")
        assert any('試験 太郎' in o for o in opts), '利用者さんの選択肢が出ません'
        kinds = await pg.eval_on_selector_all('#js_kind option', "os => os.map(o => o.value)")
        assert any('出禁' in k for k in kinds) and any('相性' in k for k in kinds), '上申の種類が足りません：' + str(kinds)
        await tap(pg, '#js_ok'); await pg.wait_for_timeout(200)
        assert any('内容を入れて' in a for a in await pg.evaluate("window.ALERTS")), '内容が空でも通ってしまいます'
        await pg.select_option('#js_pt', '2010-01-看-9001')
        await pg.select_option('#js_kind', index=1)
        await pg.fill('#js_body', '11/4の訪問で「次から男性の看護師は来ないでほしい」と本人から言われました。担当の変更をお願いします。')
        await s.shot('#ssMv .card', 'TriTime_joshin_1.png')
        await tap(pg, '#js_ok'); await pg.wait_for_timeout(500)
        assert '上申しました' in await pg.inner_text('#js_res')
        ev = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_events'))")
        nt = [e for e in ev if e.get('type') == 'note' and e.get('kind') == '上申']
        assert len(nt) == 1 and nt[0]['to'] == ['s2'] and nt[0]['from'] == 's1' and nt[0]['patientNo'] == '2010-01-看-9001' and '出禁' in nt[0]['jsKind'], '上申の記録が残りません：' + str(nt)
        assert '【上申】' in nt[0]['title'] and '試験 太郎' in nt[0]['title']
        await s.shot('#ssMv .card', 'TriTime_joshin_2.png')
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
