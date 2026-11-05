# -*- coding: utf-8 -*-
"""トライタイムの「死亡・入院による契約終了・休止」（2026-11-06・宏史さんの指示）の試験
端末＝事務局（卜部 五子）。利用者2人（太郎＝週間予定あり、花子＝週間予定あり）。
・利用者経過で太郎に「契約終了（死亡）」を記録すると、太郎の状態が契約終了・終了日＝その日・理由＝死亡になり、週間予定（本スケジュール表）から消える。一覧に「残務あり」の札
・花子に「入院」を記録すると休止中になり予定表から消える。「退院」（3か月以上あと）を記録すると利用中に戻り予定表に戻る。初回加算の札が出る
・利用者登録で理由「死亡」を選んで登録すると、状態が契約終了・終了日が今日になる
・画面の中で誤りが出ない"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(t){
  var up = Date.now();
  var ST = [ { id:'s1', name:'常勤 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['4','0'], upd:up },
    { id:'s9', name:'卜部 五子', emp:'常勤', job:'事務局', dept:'経営企画事務職', off:['6','0'], upd:up } ];
  var P = [ { no:'2010-01-看-9001', name:'試験 太郎', area:'東町', status:'利用中', ins:'精神科訪問看護（医療）', freq:'週2回', upd:up },
    { no:'2010-01-看-9002', name:'試験 花子', area:'東町', status:'利用中', ins:'精神科訪問看護（医療）', freq:'週2回', upd:up },
    { no:'2010-01-看-9003', name:'試験 三郎', area:'西町', status:'利用中', ins:'精神科訪問看護（医療）', freq:'週1回', upd:up } ];
  var W = [ { id:'w1', dow:'1', time:'09:30', min:30, no:'2010-01-看-9001', staffId:'s1', upd:up },
    { id:'w2', dow:'2', time:'10:00', min:30, no:'2010-01-看-9002', staffId:'s1', upd:up },
    { id:'w3', dow:'3', time:'10:00', min:30, no:'2010-01-看-9003', staffId:'s1', upd:up } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P)); localStorage.setItem('tritime_weekly', JSON.stringify(W));
  localStorage.setItem('tritime_events', '[]'); localStorage.setItem('tritime_settings', JSON.stringify({ work:{} }));
  localStorage.setItem('tritime_device', JSON.stringify({ me:'s9', share:true })); localStorage.setItem('tritime_dept', 'nurse');
})()"""

async def pt(pg, no):
    return await pg.evaluate("JSON.parse(localStorage.getItem('tritime_patients')).filter(function(p){ return p.no===%r; })[0]" % no)

async def weeklyNos(pg):
    # 本スケジュール表（予定タブ・職員＝全員）に出ている札の番号で見る
    await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(300)
    await pg.evaluate("var e=document.getElementById('td_staff'); e.value='s1'; e.dispatchEvent(new Event('change'));"); await pg.wait_for_timeout(800)
    a = await pg.evaluate("[].map.call(document.querySelectorAll('#td_week .ssChip'), function(c){ var m = c.textContent.match(/看-(\\d{4})/); return m ? '2010-01-看-' + m[1] : ''; }).filter(Boolean)")
    return sorted(set(a))

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1200, h=900)
    try:
        await pg.evaluate(SEED); await pg.reload(); await pg.wait_for_timeout(1500)
        await pg.evaluate("window.alert = function(m){ window.AL = String(m); };")
        assert await weeklyNos(pg) == ['2010-01-看-9001', '2010-01-看-9002', '2010-01-看-9003'], '最初の札：' + str(await weeklyNos(pg))
        # 経過：太郎＝契約終了（死亡）
        await pg.evaluate("document.querySelector('#tabs button[data-tab=course]').click()"); await pg.wait_for_timeout(300)
        await pg.select_option('#k_no', '2010-01-看-9001'); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('dContract').open = true")
        await pg.fill('#ct_date', '2026-11-05'); await pg.select_option('#ct_kind', '契約終了（死亡）'); await pg.fill('#ct_note', '原因は不明')
        await pg.click('#ct_save'); await pg.wait_for_timeout(500)
        t = await pt(pg, '2010-01-看-9001')
        assert t['status'] == '契約終了' and t['endWhy'] == '死亡' and t['endDate'] == '2026-11-05', '死亡の記録で契約終了になりません：' + str(t)
        assert '2010-01-看-9001' not in await weeklyNos(pg), '契約終了の人が予定表に残っています'
        await pg.evaluate("document.querySelector('#tabs button[data-tab=course]').click()"); await pg.wait_for_timeout(300)
        head = await pg.inner_text('#courseHead'); assert '契約終了' in head and '死亡' in head and '残務あり' in head, '経過の見出しの札が違います：' + head
        line = await pg.inner_text('#courseLine'); assert '入院・退院・契約' in line and '契約終了（死亡）' in line and '原因は不明' in line, '経過の線に残りません：' + line[:120]
        await s.shot('#tab-course .card', 'TriTime_keiyaku_1.png')
        # 経過：花子＝入院→退院（3か月以上）
        await pg.evaluate("document.querySelector('#tabs button[data-tab=course]').click()"); await pg.wait_for_timeout(300)
        await pg.select_option('#k_no', '2010-01-看-9002'); await pg.wait_for_timeout(300)
        await pg.fill('#ct_date', '2026-07-01'); await pg.select_option('#ct_kind', '入院'); await pg.click('#ct_save'); await pg.wait_for_timeout(400)
        h = await pt(pg, '2010-01-看-9002'); assert h['status'] == '休止中' and h['hospFrom'] == '2026-07-01', '入院で休止中になりません：' + str(h)
        assert '2010-01-看-9002' not in await weeklyNos(pg), '休止中の人が予定表に残っています'
        await pg.evaluate("document.querySelector('#tabs button[data-tab=course]').click()"); await pg.wait_for_timeout(300)
        await pg.select_option('#k_no', '2010-01-看-9002'); await pg.wait_for_timeout(300)
        assert await pg.evaluate("document.getElementById('k_no').value") != '', '休止中の人を経過で選べません'
        await pg.evaluate("document.getElementById('dContract').open = true")
        await pg.fill('#ct_date', '2026-10-02'); await pg.select_option('#ct_kind', '退院'); await pg.click('#ct_save'); await pg.wait_for_timeout(400)
        h = await pt(pg, '2010-01-看-9002'); assert h['status'] == '利用中' and h['hospTo'] == '2026-10-02', '退院で利用中に戻りません：' + str(h) + ' AL=' + str(await pg.evaluate("window.AL")) + ' kind=' + str(await pg.evaluate("document.getElementById('ct_kind').value")) + ' date=' + str(await pg.evaluate("document.getElementById('ct_date').value")) + ' kno=' + str(await pg.evaluate("document.getElementById('k_no').value"))
        assert '2010-01-看-9002' in await weeklyNos(pg), '退院後に予定表へ戻りません'
        await pg.evaluate("document.querySelector('#tabs button[data-tab=course]').click()"); await pg.wait_for_timeout(300)
        head = await pg.inner_text('#courseHead'); assert '初回加算' in head, '初回加算の札が出ません：' + head
        # 一覧
        await pg.evaluate("document.querySelector('#tabs button[data-tab=pt]').click()"); await pg.wait_for_timeout(300)
        await pg.select_option('#ptFilter', 'all'); await pg.wait_for_timeout(300)
        lst = await pg.inner_text('#ptList'); assert '残務あり' in lst and '初回加算' in lst, '一覧の札が違います'
        # 利用者登録で死亡を選ぶ（三郎）
        await pg.fill('#pt_no', '2010-01-看-9003'); await pg.click('#pt_load'); await pg.wait_for_timeout(300)
        await pg.select_option('#pt_endWhy', '死亡'); await pg.wait_for_timeout(200)
        assert '一律で契約終了' in await pg.inner_text('#ptEndNote')
        await pg.click('#pt_add'); await pg.wait_for_timeout(500)
        import datetime; today = datetime.date.today().isoformat()
        u = await pt(pg, '2010-01-看-9003'); assert u['status'] == '契約終了' and u['endDate'] == today, '登録画面の死亡で契約終了になりません：' + str(u)
        assert await weeklyNos(pg) == ['2010-01-看-9002'], '予定表に残る人が違います：' + str(await weeklyNos(pg))
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
