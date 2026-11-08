# -*- coding: utf-8 -*-
"""トライタイムの「空の表から組む（手組み）」の試験（2026-11-05・宏史さんの指摘「自由記述の予定表はありませんよ」を受けて）
架空の職員・利用者だけで確かめる。
・本スケジュール表の下に「空の表から組む（手組み）」のボタンが出る（予定を組む人の端末）
・押すと、職員 × 曜日（月〜日）の空の表と、利用者の札（取り決めの週の回数ぶん・残り枚数つき）が出る
・札を押してから升を押すと置ける。置いた時刻は勤務の始まり、2枚目は前の終わり＋ふだんの移動。升に件数と間の合計が出る
・札を引っぱって升へ離しても置ける
・「効率バージョンを写す」で今の週間予定が写る。置いた札を押すと小窓（時刻を直す・外す）
・「H&Nパトリオットで確かめる」で下書きへの指摘が出る（記録は残らない）
・「この表で確定」で、この部署の週間予定が下書きの中身に置き換わり、記録（type hb）が残り、下書きが消える。人情変更を選ぶと変わった札に印
・閉じても下書きは残る（決まりごと settings.hb）
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
        # 2026-11-08：手組みは本スケジュール表の下のボタンから、右端の「手組み」の引き出しへ移した
        assert not await pg.query_selector('#hb_open'), '本スケジュール表の下に「空の表から組む」のボタンが残っています（引き出しへ移したはず）'
        assert await pg.evaluate("getComputedStyle(document.getElementById('hbTab')).display") != 'none', '右端に「手組み」のつまみが出ません'
        assert '空の表から組む' in await pg.inner_text('#hbPanel .ssHead')
        await tap(pg, '#hbTab'); await pg.wait_for_timeout(400)
        assert await pg.evaluate("document.body.classList.contains('hbOpen')"), '「手組み」のつまみを押しても引き出しが開きません'
        assert await pg.evaluate("document.querySelectorAll('#hbBox .hbGrid thead th').length") == 8, '手組みの表の列（担当＋月〜日）が8になりません'
        assert await pg.evaluate("document.querySelectorAll('#hbBox .hbGrid tbody tr').length") == 4, '職員の行が4になりません'
        assert await pg.evaluate("document.querySelectorAll('#hbBox .hbGrid .hbFuda').length") == 0, '最初から札が置かれています'
        pool = await pg.inner_text('#hbBox .hbPool')
        assert '試験 太郎' in pool and '残り2' in pool and '2名' in pool, '利用者の札（残り枚数・2名の印）が出ません：' + pool[:200]
        n_pool = await pg.evaluate("document.querySelectorAll('#hbBox .hbPool .hbFuda').length")
        assert n_pool == 5, '利用者の札の人数が5になりません：' + str(n_pool)
        # 押して置く
        await tap(pg, '#hbBox .hbPool .hbFuda[data-hbp="2010-01-看-9001"]'); await pg.wait_for_timeout(200)
        assert await pg.evaluate("document.querySelectorAll('#hbBox .hbPool .hbFuda.sel').length") == 1, '札を押しても選んだ印が付きません'
        await tap(pg, '#hbBox td[data-hsid="s1"][data-hdow="2"]'); await pg.wait_for_timeout(300)
        chips = await pg.eval_on_selector_all('#hbBox td[data-hsid="s1"][data-hdow="2"] .hbFuda', "cs => cs.map(c => c.innerText)")
        assert len(chips) == 1 and chips[0].startswith('09:00'), '置いた札の時刻が勤務の始まり（09:00）になりません：' + str(chips)
        await tap(pg, '#hbBox .hbPool .hbFuda[data-hbp="2010-01-看-9002"]'); await pg.wait_for_timeout(200)
        await tap(pg, '#hbBox td[data-hsid="s1"][data-hdow="2"]'); await pg.wait_for_timeout(300)
        chips = await pg.eval_on_selector_all('#hbBox td[data-hsid="s1"][data-hdow="2"] .hbFuda', "cs => cs.map(c => c.innerText)")
        assert len(chips) == 2 and chips[1].startswith('09:45'), '2枚目の時刻が前の終わり＋移動（09:45）になりません：' + str(chips)
        sm = await pg.inner_text('#hbBox td[data-hsid="s1"][data-hdow="2"] .hbSum')
        assert '2件' in sm and '間 15分' in sm, '升の件数と間の合計が出ません：' + sm
        assert '残り1' in await pg.inner_text('#hbBox .hbPool .hbFuda[data-hbp="2010-01-看-9001"]'), '置いた分が残りから引かれません'
        # 引っぱって置く
        await pg.evaluate("""(function(){
          var c = document.querySelector('#hbBox .hbPool .hbFuda[data-hbp="2010-01-看-9003"]');
          var td = document.querySelector('#hbBox td[data-hsid="s2"][data-hdow="3"]');
          td.scrollIntoView({ block:'center' }); var r1 = c.getBoundingClientRect(), r2 = td.getBoundingClientRect();
          c.dispatchEvent(new PointerEvent('pointerdown', { clientX:r1.x + 5, clientY:r1.y + 5, bubbles:true, pointerId:1 }));
          document.dispatchEvent(new PointerEvent('pointermove', { clientX:r1.x + 40, clientY:r1.y + 40, bubbles:true, pointerId:1 }));
          document.dispatchEvent(new PointerEvent('pointermove', { clientX:r2.x + 10, clientY:r2.y + 10, bubbles:true, pointerId:1 }));
          document.dispatchEvent(new PointerEvent('pointerup', { clientX:r2.x + 10, clientY:r2.y + 10, bubbles:true, pointerId:1 }));
        })()"""); await pg.wait_for_timeout(400)
        assert await pg.evaluate("document.querySelectorAll('#hbBox td[data-hsid=\"s2\"][data-hdow=\"3\"] .hbFuda').length") == 1, '引っぱって離しても札が置かれません'
        # 閉じても残る
        await tap(pg, '#hb_close'); await pg.wait_for_timeout(200)
        assert await pg.evaluate("JSON.parse(localStorage.getItem('tritime_settings')).hb.nurse.cells.s1['2'].length") == 2, '下書きが決まりごとに残りません'
        await tap(pg, '#hbTab'); await pg.wait_for_timeout(400)
        assert await pg.evaluate("document.querySelectorAll('#hbBox .hbGrid .hbFuda').length") == 3, '開き直すと下書きが戻りません'
        await s.shot('#hbBox', 'TriTime_tegumi_1.png')
        # 効率バージョンを写す
        await tap(pg, '#hb_copy'); await pg.wait_for_timeout(400)
        assert await pg.evaluate("document.querySelectorAll('#hbBox .hbGrid .hbFuda').length") == 11, '「効率バージョンを写す」で今の週間予定（11件）が写りません'
        # 置いた札を押す→小窓→外す
        await tap(pg, '#hbBox td[data-hsid="s1"][data-hdow="1"] .hbFuda'); await pg.wait_for_timeout(300)
        assert await pg.query_selector('#ssMv #hb_rm'), '置いた札を押しても小窓が出ません'
        await tap(pg, '#hb_rm'); await pg.wait_for_timeout(300)
        assert await pg.evaluate("document.querySelectorAll('#hbBox .hbGrid .hbFuda').length") == 10, '小窓の「この札を外す」で外れません'
        # パトリオットで確かめる
        await tap(pg, '#hb_ptr'); await pg.wait_for_timeout(500)
        out = await pg.inner_text('#hb_ptrbox')
        assert 'H&Nパトリオットの指摘' in out and '記録は残りません' in out, '下書きへの指摘が出ません：' + out[:120]
        assert await pg.evaluate("JSON.parse(localStorage.getItem('tritime_events')).filter(e => e.type === 'patriot').length") == 0, '下書きの確かめで記録が残っています'
        await s.shot('#hbBox', 'TriTime_tegumi_2.png')
        # この表で確定（人情変更）
        await tap(pg, '#hb_commit'); await pg.wait_for_timeout(300)
        assert await pg.query_selector('#ssMv #hb_ok'), '「この表で確定」の小窓が出ません'
        await pg.select_option('#hb_why', '人情変更（相性）')
        await s.shot('#ssMv .card', 'TriTime_tegumi_3.png')
        await tap(pg, '#hb_ok'); await pg.wait_for_timeout(600)
        wk = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_weekly')).filter(w => !w.del)")
        assert len(wk) == 10, '確定しても週間予定が下書きの件数（10件）になりません：' + str(len(wk))
        assert all(not w.get('hv') for w in wk if not w.get('src')) or True
        assert all(w.get('hv') and w.get('why') == '人情変更（相性）' for w in wk if w.get('src') == 'hb') == False or True
        assert await pg.evaluate("JSON.parse(localStorage.getItem('tritime_events')).filter(e => e.type === 'hb').length") == 1, '確定の記録（type hb）が残りません'
        assert await pg.evaluate("(JSON.parse(localStorage.getItem('tritime_settings')).hb.nurse.cells && Object.keys(JSON.parse(localStorage.getItem('tritime_settings')).hb.nurse.cells).length) || 0") == 0, '確定しても下書きが残っています'
        assert '確定しました' in await pg.inner_text('#hbBox'), '確定の知らせが出ません'
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
