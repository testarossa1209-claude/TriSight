# -*- coding: utf-8 -*-
"""トライタイムの「人情変更・H&Nパトリオット・予定表の比較・伝票」の試験（2026-11-04・宏史さんの要望と決定）
架空の職員・利用者だけで作った記録を試験の中で入れて確かめる（本物の情報は使わない）。
・本スケジュール表（「予定」の地図の下）でも、予定を組む人の端末では今日以降の札が動かせる（dg の印）
・週間予定の1件に人情変更の印が付いていると、本スケジュール表の札に点線と「人情」が出る
・「H&Nパトリオット」を押すと、条項表（17条）で確かめた指摘が根拠付きで出る。人情変更の札は、効率だけの条項（訪問の間が短い）では指摘されず、
  度が過ぎた条項（訪問の間が20分超）では「人情変更」の印付きで指摘される。指摘を押すと表の札が光る。押した記録（type patriot）が残る
・札を動かす小窓に「変更の理由」が出て、「人情変更（…）」を選んで動かすと、組み換えの記録に why・hv・note が残り、札が点線になる
・「伝票」タブ：架空の伝票CSV（Shift-JIS）を読むと見出しから列が当たり、氏名で利用者が合う。保管すると月ごとの記録（type slips）に残り、
  列の対応が決まりごとに残る。突き合わせで、伝票の無い過去の訪問が「伝票なし」と出る。今日より後の日は「なし」を出さない
・キャンセル受付の理由の分類に「事業所都合」があり、選ぶとキャンセル料なし・信用度に影響しない旨が出る
・画面の中で誤りが出ない"""
import sys, os, tempfile, datetime
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

def ymd(d): return d.strftime('%Y-%m-%d')

def make_csv(mon):
    d = tempfile.mkdtemp(); path = os.path.join(d, 'denpyo_test.csv')
    d1 = mon.strftime('%Y/%m/%d'); d2 = (mon + datetime.timedelta(days=1)).strftime('%Y/%m/%d')
    rows = [['サービス提供日', '利用者名', '開始時間', '終了時間', '担当者', 'サービス内容', '単位数'],
            [d1, '試験 太郎', '09:30', '10:00', '常勤 一子', '精神科訪問看護', '5550'],
            [d1, '試験 花子', '10:40', '11:10', '常勤 一子', '精神科訪問看護', '5550'],
            [d2, '試験 一郎', '09:00', '09:55', '常勤 二子', '精神科訪問看護', '5550'],
            [d2, '不明 四郎', '13:00', '13:30', '常勤 二子', '精神科訪問看護', '5550']]
    with open(path, 'wb') as f: f.write(('\r\n'.join(','.join(r) for r in rows) + '\r\n').encode('cp932'))
    return path

SEED = """(function(t){
  var up = Date.now();
  var ST = [
    { id:'s1', name:'常勤 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['4','0'], upd:up },
    { id:'s2', name:'常勤 二子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:[], upd:up },
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

async def test(p):
    today = datetime.date.today(); mon = today - datetime.timedelta(days=today.weekday())
    csv = make_csv(mon)
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate(SEED)
        await pg.reload(); await pg.wait_for_timeout(1200)
        await pg.evaluate("window.confirm = function(){ return true; }")
        # 本スケジュール表（全員）：札が動かせる・人情の札
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(300)
        await pg.wait_for_selector('#td_staff option[value="*"]', state='attached', timeout=15000)
        await pg.evaluate("var e = document.getElementById('td_staff'); e.value = '*'; e.dispatchEvent(new Event('change'));")
        await pg.wait_for_selector('#td_week .ssChip', state='attached', timeout=15000); await pg.wait_for_timeout(300)
        n_chip = await pg.evaluate("document.querySelectorAll('#td_week .ssChip').length")
        assert n_chip >= 10, '本スケジュール表に札が出ません：' + str(n_chip)
        assert await pg.evaluate("document.querySelectorAll('#td_week .ssChip.dg').length") >= 1, '本スケジュール表の札が動かせる印（dg）になっていません'
        assert await pg.evaluate("document.querySelectorAll('#td_week .ssChip.hv').length") == 1, '週間予定の人情変更の札が点線（hv）で出ません'
        assert '人情' in await pg.inner_text('#td_week .ssChip.hv'), '人情変更の札に「人情」の印が出ません'
        assert await pg.evaluate("document.querySelectorAll('#td_week .ssChip[data-pk]').length") == n_chip, '札に鍵（data-pk）が付いていません'
        # H&Nパトリオット
        assert await pg.query_selector('#ptr_td'), '本スケジュール表の下に「H&Nパトリオット」のボタンがありません'
        await pg.evaluate("document.getElementById('ptr_td').click()"); await pg.wait_for_timeout(600)
        out = await pg.inner_text('#ptr_tdbox')
        assert 'H&Nパトリオットの指摘（条項表の 17条で確かめました）' in out, '指摘の見出しが出ません：' + out[:120]
        assert '問題なし' not in out and '大丈夫' not in out, '安全宣言が出ています'
        assert '2名体制の指示ですが、同行が組まれていません' in out, '2名体制の同行なしの指摘が出ません'
        assert '訪問できない曜日（火）に入っています' in out, '訪問できない曜日の指摘が出ません'
        assert '条項：' in out and '根拠：' in out, '指摘に条項と根拠が付いていません'
        # 人情変更の札：効率だけの条項では指摘されず、度が過ぎた条項（20分超）では印付きで指摘
        items = await pg.eval_on_selector_all('#ptr_tdbox li', "ls => ls.map(l => l.innerText)")
        hv_items = [x for x in items if x.startswith('人情変更')]
        assert hv_items and all('20分超' in x for x in hv_items), '人情変更の札への指摘が、度が過ぎた条項（20分超）だけになっていません：' + str(hv_items)
        assert all('思いやりから来ている' in x for x in hv_items), '人情変更への指摘に、理由を認める一文がありません'
        await pg.evaluate("document.querySelector('#ptr_tdbox .ptrRow').click()"); await pg.wait_for_timeout(200)
        assert await pg.evaluate("document.querySelectorAll('#td_week .ssChip.ptrHit').length") >= 1, '指摘を押しても表の札が光りません'
        assert await pg.evaluate("JSON.parse(localStorage.getItem('tritime_events')).filter(e => e.type === 'patriot').length") == 1, 'パトリオットを押した記録が残りません'
        await s.shot('#cardToday', 'TriTime_patriot_td.png')
        # 仮スケジュール表にもボタン
        await pg.evaluate("document.getElementById('ssTab').click()"); await pg.wait_for_timeout(600)
        assert await pg.query_selector('#ptr_ss'), '仮スケジュール表に「H&Nパトリオット」のボタンがありません'
        # 札を動かす小窓：変更の理由（人情変更）
        tgt = ymd(today + datetime.timedelta(days=1))
        await pg.evaluate("""(function(ds){
          var c = [].filter.call(document.querySelectorAll('#ssBody .ssChip.dg'), function(x){ return true; })[0];
          var td = [].filter.call(document.querySelectorAll('#ssBody td[data-sid]'), function(t){ return t.getAttribute('data-sid') === 's2' && t.getAttribute('data-date') === ds; })[0];
          var r1 = c.getBoundingClientRect(), r2 = td.getBoundingClientRect();
          c.dispatchEvent(new PointerEvent('pointerdown', { clientX:r1.x + 5, clientY:r1.y + 5, bubbles:true, pointerId:1 }));
          document.dispatchEvent(new PointerEvent('pointermove', { clientX:r1.x + 40, clientY:r1.y + 40, bubbles:true, pointerId:1 }));
          document.dispatchEvent(new PointerEvent('pointermove', { clientX:r2.x + 10, clientY:r2.y + 10, bubbles:true, pointerId:1 }));
          document.dispatchEvent(new PointerEvent('pointerup', { clientX:r2.x + 10, clientY:r2.y + 10, bubbles:true, pointerId:1 }));
        })('%s')""" % tgt); await pg.wait_for_timeout(400)
        assert await pg.query_selector('#ssMv #mv_why'), '札を動かす小窓に「変更の理由」が出ません'
        opts = await pg.eval_on_selector_all('#mv_why option', "os => os.map(o => o.value)")
        assert '人情変更（相性）' in opts and '事業所の都合（職員の休み・調整）' in opts, '変更の理由の選択肢が違います：' + str(opts)
        await pg.select_option('#mv_why', '人情変更（体調への配慮）'); await pg.fill('#mv_note', '試験のひとこと'); await pg.check('#mv_ok')
        await s.shot('#ssMv .card', 'TriTime_patriot_mv.png')
        await pg.evaluate("document.getElementById('mv_once').click()"); await pg.wait_for_timeout(500)
        mv = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_events')).filter(e => e.type === 'move').map(e => [e.why, e.hv, e.note])")
        assert mv == [['人情変更（体調への配慮）', True, '試験のひとこと']], '組み換えの記録に理由・人情変更の印が残りません：' + str(mv)
        await pg.evaluate("document.getElementById('mv_close').click()"); await pg.wait_for_timeout(500)
        assert await pg.evaluate("document.querySelectorAll('#ssBody .ssChip.hv').length") == 2, '動かした札が点線（人情変更）になりません'
        # 伝票
        await pg.evaluate("document.querySelector('#tabs button[data-tab=slip]').click()"); await pg.wait_for_timeout(400)
        await pg.set_input_files('#slp_file', csv); await pg.wait_for_timeout(900)
        assert '見出し 7列・4行' in await pg.inner_text('#slp_msg'), '伝票CSVの読み込みの知らせが違います：' + await pg.inner_text('#slp_msg')
        mp = await pg.eval_on_selector_all('#slp_prev [data-slpf]', "ss => ss.map(x => x.getAttribute('data-slpf') + '=' + x.value).join(' ')")
        assert mp == 'date=0 name=1 no=-1 start=2 end=3 who=4 kind=5 amt=6', '見出しから列が当たりません：' + mp
        pv = await pg.inner_text('#slp_prev')
        assert '読めた行：3件' in pv and '利用者が登録と合わなかった行 1件' in pv, '読めた行・合わなかった行の数が違います：' + pv[:200]
        await s.shot('#tab-slip', 'TriTime_patriot_denpyo.png')
        await pg.evaluate("document.getElementById('slp_go').click()"); await pg.wait_for_timeout(800)
        sl = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_events')).filter(e => e.type === 'slips').map(e => [e.ym, e.rows.length, e.src])")
        assert sl == [[mon.strftime('%Y-%m'), 3, 'denpyo_test.csv']], '伝票の記録が残りません：' + str(sl)
        assert (await pg.evaluate("JSON.parse(localStorage.getItem('tritime_settings')).slipMap")) == { 'date':0, 'name':1, 'no':-1, 'start':2, 'end':3, 'who':4, 'kind':5, 'amt':6 }, '列の対応が決まりごとに残りません'
        assert await pg.inner_text('#slp_list') and mon.strftime('%Y') in await pg.inner_text('#slp_list'), '保管した伝票の一覧に出ません'
        mt = await pg.inner_text('#slp_match')
        assert '合わないもの' in mt and ('伝票なし' in mt or '看護記録なし' in mt), '突き合わせが出ません：' + mt[:200]
        rows = await pg.eval_on_selector_all('#slp_match table tr', "trs => trs.slice(1).map(tr => tr.querySelectorAll('td')[0].innerText)")
        fut = ymd(today + datetime.timedelta(days=7))
        assert all(not r.startswith(str(int(fut[5:7])) + '月' + str(int(fut[8:10])) + '日') for r in rows), '今日より後の日に「なし」の指摘が出ています'
        # キャンセル受付：事業所都合
        await pg.evaluate("document.querySelector('#tabs button[data-tab=intake]').click()"); await pg.wait_for_timeout(300)
        opts2 = await pg.eval_on_selector_all('#c_cat option', "os => os.map(o => o.value)")
        assert '事業所都合' in opts2, '理由の分類に「事業所都合」がありません：' + str(opts2)
        await pg.evaluate("""(function(ds){ var set = function(id, v){ var e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', { bubbles:true })); };
          set('c_date', ds); set('c_recv', ds + 'T09:00'); set('c_cat', '事業所都合'); })('%s')""" % tgt); await pg.wait_for_timeout(300)
        jd = await pg.inner_text('#c_judge')
        assert 'キャンセル料はかからず、信用度も下がりません' in jd, '事業所都合の判定の文が出ません：' + jd[:120]
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
