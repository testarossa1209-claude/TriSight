# -*- coding: utf-8 -*-
"""トライタイムの1日の予定と地図の「全員」の試験（2026-11-03・宏史さん「看護師でないと出ないの？管理者はすべての画面を見れるようにするはず」）
・この端末を使う人が決まっていない端末では、「1日の予定と地図」の職員の欄が最初から「全員」になり、全員のこの日の予定が担当つきで出る
・地図に出せる位置がある訪問先は、地図に出る"""
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
        await pg.evaluate("""(function(){ var t = Date.now(), st = JSON.parse(localStorage.getItem('tritime_staff')), dow = String(new Date().getDay());
          var a = st.filter(function(s){ return s.name === '看護 一子'; })[0].id, b = st.filter(function(s){ return s.name === '看護 二子'; })[0].id;
          st.forEach(function(s){ s.off = []; s.holOff = false; }); localStorage.setItem('tritime_staff', JSON.stringify(st));
          localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9701', name:'試験 一', area:'東町', status:'利用中', lat:35.70, lng:139.41, upd:t },
            { no:'2010-01-看-9702', name:'試験 二', area:'西町', status:'利用中', lat:35.71, lng:139.42, upd:t } ]));
          localStorage.setItem('tritime_weekly', JSON.stringify([
            { id:'w1', dow:dow, time:'09:15', min:30, no:'2010-01-看-9701', staffId:a, withId:'', upd:t },
            { id:'w2', dow:dow, time:'10:00', min:30, no:'2010-01-看-9702', staffId:b, withId:'', upd:t } ]));
          /* この端末を使う人が看護師でない（事務所のPC）形にする */
          var d = JSON.parse(localStorage.getItem('tritime_device') || '{}'); d.me = 'jimu-no-hito'; localStorage.setItem('tritime_device', JSON.stringify(d));
          var sel = document.getElementById('td_staff'); if(sel) sel.value = ''; })()""")
        await pg.evaluate("document.querySelector('#tabs button[data-tab=pt]').click()"); await pg.wait_for_timeout(200)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(600)
        v = await pg.evaluate("document.getElementById('td_staff').value")
        assert v == '*', '1日の予定と地図の職員の欄が、最初から「全員」になりません：' + v
        tl = await pg.inner_text('#td_list')
        assert '看護 一子' in tl and '看護 二子' in tl and '試験 一' in tl and '試験 二' in tl, '「全員」で、全員のこの日の予定が担当つきで出ません：' + tl[:300]
        shown = await pg.evaluate("document.getElementById('td_map').style.display")
        assert shown != 'none', '「全員」で、地図が出ません'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
