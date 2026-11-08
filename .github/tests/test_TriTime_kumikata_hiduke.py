# -*- coding: utf-8 -*-
"""トライタイムの自動の振り分けの表の日付の試験（2026-11-03・宏史さん「仮スケジュールが正規の表記ならば本体スケジュールも更新してください。2つあると混乱する」）
・自動の振り分けの表の見出しに、仮スケジュール表と同じく今週の日付が出る
・その日に休み（ここでは休みの届け）の人の升には「休（理由）」が出て、その日に組まれた訪問は「要調整」になる
・仮スケジュール表で付け替えた日は、見出しに「付け替え済み」と出て、要調整にしない"""
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
        await pg.evaluate(ADD, {'name':'看護 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'})
        info = await pg.evaluate("""(function(){ var t = Date.now(), st = JSON.parse(localStorage.getItem('tritime_staff')), a = st[0].id;
          var d = new Date(), w = d.getDay(), mon = new Date(d.getFullYear(), d.getMonth(), d.getDate() + (w === 0 ? -6 : 1 - w));
          var wed = new Date(mon.getFullYear(), mon.getMonth(), mon.getDate() + 2), p2 = function(n){ return (n < 10 ? '0' : '') + n; };
          var wd = wed.getFullYear() + '-' + p2(wed.getMonth() + 1) + '-' + p2(wed.getDate());
          localStorage.setItem('tritime_patients', JSON.stringify([{ no:'2010-01-看-9601', name:'試験 水', area:'東町', status:'利用中', wDays:['3'], upd:t }]));
          localStorage.setItem('tritime_weekly', '[]');
          /* 今週の水曜に休みの届け */
          localStorage.setItem('tritime_events', JSON.stringify([{ id:'lv1', type:'leave', staffId:a, date:wd, kind:'有給', upd:t }]));
          return [(mon.getMonth() + 1) + '/' + mon.getDate(), (wed.getMonth() + 1) + '/' + wed.getDate(), wd, a]; })()""")
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(400)
        await pg.evaluate("document.getElementById('auTab').click()"); await pg.wait_for_timeout(300)   # 2026-11-08：自動の振り分けは右端の「自動組み」の引き出しの中
        await pg.wait_for_selector('#au_make', state='visible', timeout=15000)
        await pg.evaluate("document.getElementById('auTab').click()"); await pg.wait_for_timeout(300)   # 2026-11-08：自動の振り分けは右端の「自動組み」の引き出しの中
        await pg.click('#au_make'); await pg.wait_for_timeout(800)
        th = await pg.inner_text('#au_out table tr')
        assert info[0] in th and info[1] in th, '自動の振り分けの表の見出しに、今週の日付が出ません：' + th
        tb = await pg.inner_text('#au_out table')
        assert '休（有給）' in tb and '要調整' in tb, '休みの届けの日の升に「休（有給）」と「要調整」が出ません：' + tb[:300]
        await s.shot('#cardAuto', 'TriTime_kumikata_hiduke.png')
        # 仮スケジュール表で付け替えた日は「付け替え済み」で、要調整にしない
        await pg.evaluate("""(a) => { var ev = JSON.parse(localStorage.getItem('tritime_events'));
          ev.push({ id:'m1', type:'move', patientNo:'2010-01-看-9601', date:a[2], fromTime:'09:15', toTime:'09:15', toStaff:a[3], toWith:'', rec:true, bulk:'b1', upd:Date.now() });
          localStorage.setItem('tritime_events', JSON.stringify(ev)); }""", info)
        await pg.evaluate("document.getElementById('auTab').click()"); await pg.wait_for_timeout(300)   # 2026-11-08：自動の振り分けは右端の「自動組み」の引き出しの中
        await pg.click('#au_make'); await pg.wait_for_timeout(800)
        tb2 = await pg.inner_text('#au_out table')
        assert '付け替え済み' in tb2 and '要調整' not in tb2, '付け替えた日が「付け替え済み」にならず、要調整が残ります：' + tb2[:300]
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
