# -*- coding: utf-8 -*-
"""トライタイムの「一般の職員は自分の担当の札だけ動かせる」の試験（2026-11-05・宏史さんの決め(a)(b)）
架空の職員・利用者だけで確かめる。端末は共有あり・主に使う人＝常勤 一子（合言葉なし＝一般の職員）。
・本スケジュール表で、自分の担当の今日以降の札だけが動かせる（他の人の札は動かせない）
・他の人の升へ離すと「自分の担当の升にだけ動かせます」と出て動かない
・自分の別の日の升へ離すと小窓が出る。「毎週の予定を変える」は無く、理由の選択肢に「人情変更」が無い
・「この日だけ動かす」で組み換えの記録（type move・人情変更ではない）が残り、連絡板の知らせ（type note）の宛先に事務局の職員が入る
・画面の中で誤りが出ない"""
import sys, os, datetime
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(t){
  var up = Date.now();
  var ST = [
    { id:'s1', name:'常勤 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['4','0'], upd:up },
    { id:'s2', name:'常勤 二子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['6','0'], upd:up },
    { id:'s3', name:'非常勤 三子', emp:'非常勤', job:'准看護師', dept:'訪問看護部', off:['1','3','5','6','0'], upd:up },
    { id:'s9', name:'事務 五子', emp:'常勤', job:'事務局', dept:'経営企画事務職', off:['6','0'], upd:up },
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

async def drag(pg, chip_sel, td_sel):
    await pg.evaluate("""(function(cs, ts){
      var c = document.querySelector(cs), td = document.querySelector(ts); if(!c || !td) return 'none';
      td.scrollIntoView({ block:'center' }); var r1 = c.getBoundingClientRect(), r2 = td.getBoundingClientRect();
      c.dispatchEvent(new PointerEvent('pointerdown', { clientX:r1.x + 5, clientY:r1.y + 5, bubbles:true, pointerId:1 }));
      document.dispatchEvent(new PointerEvent('pointermove', { clientX:r1.x + 40, clientY:r1.y + 40, bubbles:true, pointerId:1 }));
      document.dispatchEvent(new PointerEvent('pointermove', { clientX:r2.x + 10, clientY:r2.y + 10, bubbles:true, pointerId:1 }));
      document.dispatchEvent(new PointerEvent('pointerup', { clientX:r2.x + 10, clientY:r2.y + 10, bubbles:true, pointerId:1 }));
      return 'ok';
    })(%s, %s)""" % (repr(chip_sel), repr(td_sel)))

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate(SEED)
        await pg.reload(); await pg.wait_for_timeout(1500)
        await pg.evaluate("window.ALERTS = []; window.alert = function(m){ window.ALERTS.push(String(m)); }; window.confirm = function(){ return true; }")
        await tap(pg, '#tabs button[data-tab=plan]'); await pg.wait_for_timeout(400)
        await pg.wait_for_selector('#td_week .ssChip', state='attached', timeout=15000); await pg.wait_for_timeout(300)
        if await pg.evaluate("!!document.querySelector('#td_staff option[value=\"*\"]')"):
            await pg.evaluate("var e = document.getElementById('td_staff'); e.value = '*'; e.dispatchEvent(new Event('change'));"); await pg.wait_for_timeout(600)
        assert not await pg.query_selector('#hb_open'), '一般の職員の端末に「空の表から組む」が出ています'
        txt = await pg.inner_text('#td_week')
        assert '自分の担当の今日以降の札' in txt, '一般の職員向けの説明文が出ません'
        # 今日以降の自分の札だけ dg
        own = await pg.evaluate("Array.from(document.querySelectorAll('#td_week td[data-sid=\"s1\"] .ssChip.dg')).length")
        other = await pg.evaluate("Array.from(document.querySelectorAll('#td_week td[data-sid=\"s2\"] .ssChip.dg')).length")
        assert own >= 1, '自分の担当の札が動かせる印（dg）になりません'
        assert other == 0, '他の人の担当の札まで動かせる印になっています：' + str(other)
        # 自分の札を取る（今日以降の最初の dg）
        info = await pg.evaluate("""(function(){ var c = document.querySelector('#td_week td[data-sid="s1"] .ssChip.dg'); var td = c.closest('td'); return { date: td.getAttribute('data-date') }; })()""")
        d0 = info['date']
        # 他の人の升へ → 動かない
        tds2 = await pg.evaluate("Array.from(document.querySelectorAll('#td_week td[data-sid=\"s2\"]')).map(t => t.getAttribute('data-date'))")
        if tds2:
            tgt2 = [d for d in tds2 if d != d0][0]
            r = await drag(pg, '#td_week td[data-sid="s1"] .ssChip.dg', '#td_week td[data-sid="s2"][data-date="%s"]' % tgt2); await pg.wait_for_timeout(300)
            assert r == 'ok'
            al = await pg.evaluate("window.ALERTS")
            assert any('自分の担当の升にだけ' in a for a in al), '他の人の升へ離しても止まりません：' + str(al)
            assert not await pg.query_selector('#ssMv'), '他の人の升へ離したのに小窓が出ています'
        else:
            print('（この端末では他の人の行が表に出ないため、他の人の升への確かめは無し）')
        # 自分の別の日の升へ → 小窓
        tds1 = await pg.evaluate("Array.from(document.querySelectorAll('#td_week td[data-sid=\"s1\"]')).map(t => t.getAttribute('data-date'))")
        today = datetime.date.today().strftime('%Y-%m-%d')
        tgt1 = [d for d in tds1 if d != d0 and d >= today][0]
        r = await drag(pg, '#td_week td[data-sid="s1"] .ssChip.dg', '#td_week td[data-sid="s1"][data-date="%s"]' % tgt1); await pg.wait_for_timeout(400)
        assert await pg.query_selector('#ssMv #mv_once'), '自分の別の日の升へ離しても小窓が出ません'
        assert not await pg.query_selector('#ssMv #mv_week'), '一般の職員の小窓に「毎週の予定を変える」が出ています'
        opts = await pg.eval_on_selector_all('#mv_why option', "os => os.map(o => o.value)")
        assert not any('人情' in o for o in opts), '一般の職員の小窓に人情変更の選択肢が出ています：' + str(opts)
        assert len(opts) >= 2, '普通の理由の選択肢がありません：' + str(opts)
        assert '事務局の連絡板に知らせ' in await pg.inner_text('#ssMv .card')
        await s.shot('#ssMv .card', 'TriTime_selfmove_1.png')
        await pg.select_option('#mv_why', opts[1])
        await tap(pg, '#mv_once'); await pg.wait_for_timeout(600)
        ev = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_events'))")
        mv = [e for e in ev if e.get('type') == 'move']
        assert len(mv) == 1 and not mv[0].get('hv') and mv[0].get('by') == 's1', '組み換えの記録が残りません／人情変更になっています：' + str(mv)
        nt = [e for e in ev if e.get('type') == 'note']
        assert len(nt) == 1 and 's9' in nt[0]['to'] and 's1' in nt[0]['to'], '連絡板の知らせの宛先に事務局が入りません：' + str([n.get('to') for n in nt])
        assert '動かしました' in await pg.inner_text('#ssMv .card')
        await s.shot('#ssMv .card', 'TriTime_selfmove_2.png')
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
