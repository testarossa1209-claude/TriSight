# -*- coding: utf-8 -*-
"""トライタイムのキャンセルの空き時間と、付け替えの町名寄せの試験（2026-11-03・宏史さんの指示）
・「この日の訪問をまとめて付け替える」は、町名ごとに寄せて時刻を組み直す（東町・西町・東町 → 東町・東町・西町）
・「名簿・設定」の「事業所と取引先」で、事業所の地区と取引先を登録できる
・キャンセルの「空いた時間の案」の先頭に「空いた時間の使い方」（事務所に戻る・同じ町名の取引先へのご挨拶）が出る。ほかの利用者さんの時刻は動かさない"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

ADD = """async (p) => {
  const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', {bubbles:true})); };
  set('st_name', p.name); set('st_dept', p.dept); set('st_emp', p.emp); set('st_job', p.job);
  await new Promise(r => setTimeout(r, 100));
  document.getElementById('st_add').click();
  await new Promise(r => setTimeout(r, 200));
}"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        for x in [{'name':'看護 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'非常勤'},
                  {'name':'看護 二子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'非常勤'}]:
            await pg.evaluate(ADD, x)
        # 事業所と取引先
        await pg.fill('#pa_offArea', '本町'); await pg.click('#pa_offSave'); await pg.wait_for_timeout(200)
        await pg.fill('#pa_name', '東町地域包括支援センター'); await pg.select_option('#pa_kind', '地域包括支援センター'); await pg.fill('#pa_area', '東町')
        await pg.click('#pa_add'); await pg.wait_for_timeout(300)
        pl = await pg.inner_text('#paList')
        assert '東町地域包括支援センター' in pl, '取引先が登録できません：' + pl
        ids = await pg.evaluate("""(function(){ var t = Date.now(), st = JSON.parse(localStorage.getItem('tritime_staff')), dow = String(new Date().getDay());
          st.forEach(function(s){ s.off = []; s.holOff = false; }); localStorage.setItem('tritime_staff', JSON.stringify(st));
          var a = st.filter(function(s){ return s.name === '看護 一子'; })[0].id, b = st.filter(function(s){ return s.name === '看護 二子'; })[0].id;
          localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9801', name:'試験 東一', area:'東町', status:'利用中', upd:t },
            { no:'2010-01-看-9802', name:'試験 西', area:'西町', status:'利用中', upd:t },
            { no:'2010-01-看-9803', name:'試験 東二', area:'東町', status:'利用中', upd:t } ]));
          localStorage.setItem('tritime_weekly', JSON.stringify([
            { id:'w1', dow:dow, time:'09:15', min:30, no:'2010-01-看-9801', staffId:a, withId:'', upd:t },
            { id:'w2', dow:dow, time:'10:00', min:30, no:'2010-01-看-9802', staffId:b, withId:'', upd:t },
            { id:'w3', dow:dow, time:'10:45', min:30, no:'2010-01-看-9803', staffId:a, withId:'', upd:t } ]));
          localStorage.setItem('tritime_events', '[]'); return [a, b]; })()""")
        # まとめて付け替える → 町名で寄せて時刻を組み直す
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('ssTab').click()"); await pg.wait_for_timeout(600)
        await pg.evaluate("var b = document.getElementById('ssBulk'); if(b) b.open = true"); await pg.wait_for_timeout(200)
        await pg.select_option('#sb_staff', ids[0]); await pg.select_option('#sb_with', ids[1])
        await pg.evaluate("window.confirm = function(){ return true; }")
        await pg.click('#sb_go'); await pg.wait_for_timeout(600)
        mv = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_events')).filter(function(e){ return e.type === 'move' && !e.del; }).sort(function(a, b){ return a.toTime < b.toTime ? -1 : 1; }).map(function(e){ return e.patientNo.slice(-4) + ' ' + e.toTime; })")
        assert mv == ['9801 09:15', '9803 10:00', '9802 10:45'], '付け替えたとき、町名で寄せて時刻が組み直されません：' + str(mv)
        await pg.evaluate("document.body.classList.remove('ssOpen')")
        # キャンセル → 空いた時間の使い方
        await pg.evaluate("""(function(){ var d = new Date(), p2 = function(n){ return (n < 10 ? '0' : '') + n; }, dt = d.getFullYear() + '-' + p2(d.getMonth() + 1) + '-' + p2(d.getDate());
          var ev = JSON.parse(localStorage.getItem('tritime_events')); ev.push({ id:'cx1', type:'cancel', patientNo:'2010-01-看-9803', date:dt, time:'10:00', reason:'体調', upd:Date.now() });
          localStorage.setItem('tritime_events', JSON.stringify(ev)); })()""")
        await pg.evaluate("document.querySelector('#tabs button[data-tab=pt]').click()"); await pg.wait_for_timeout(200)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(500)
        await pg.evaluate("document.getElementById('plTab').click()"); await pg.wait_for_timeout(300)   # 2026-11-08：今週の訪問予定は左端の「今週の予定」の引き出しの中
        btn = await pg.query_selector('#planBody [data-gap]')
        assert btn, 'キャンセルの訪問に「空いた時間の案」のボタンが出ません'
        await btn.click(); await pg.wait_for_timeout(400)
        gp = await pg.evaluate("[].map.call(document.querySelectorAll('#planBody .gap, #planBody [id^=gap-]'), function(e){ return e.innerText; }).join(' ')")
        assert '空いた時間の使い方' in gp and 'ほかの利用者さんの予定は動かしません' in gp, '「空いた時間の使い方」が出ません：' + gp[:300]
        assert 'ご挨拶（営業）：東町地域包括支援センター' in gp, '同じ町名の取引先へのご挨拶の案が出ません：' + gp[:400]
        assert '事務所に戻る' in gp, '事務所に戻る案が出ません：' + gp[:400]
        await s.shot('#cardPlan', 'TriTime_aki.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
