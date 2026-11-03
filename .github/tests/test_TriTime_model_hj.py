# -*- coding: utf-8 -*-
"""トライタイムのモデルコースの非常勤の出る曜日の試験（2026-11-03・宏史さんの指示「職員の出勤体制を入れたので、これを反映したモデルコースを」）
・非常勤の人に名簿で公休の曜日が入っていれば、「モデルコース」タブの条件の表の初めの値は、公休以外の曜日になる（週間予定が無くても1日3件）
・公休が入っていない非常勤は、これまでどおり週間予定から取る
・待機の人は条件の表に出ない"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

ADD = """async (p) => {
  const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', {bubbles:true})); };
  set('st_name', p.name); set('st_dept', p.dept); set('st_emp', p.emp); set('st_job', p.job);
  await new Promise(r => setTimeout(r, 100));
  (p.off || []).forEach(function(w){ const c = document.querySelector('#st_off [data-stoff="' + w + '"]'); if(c){ c.checked = true; c.dispatchEvent(new Event('change', {bubbles:true})); } });
  if(p.emp === '非常勤'){ document.getElementById('st_standby').checked = !!p.standby; }
  document.getElementById('st_add').click();
  await new Promise(r => setTimeout(r, 200));
}"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        for x in [{'name':'常勤 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤', 'off':['0','6']},
                  {'name':'非常勤 二子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'非常勤', 'off':['1','3','5','6','0']},
                  {'name':'非常勤 四子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'非常勤'},
                  {'name':'待機 三子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'非常勤', 'standby':True}]:
            await pg.evaluate(ADD, x)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=model]').click()"); await pg.wait_for_timeout(600)
        info = await pg.evaluate("""(function(){
          var st = JSON.parse(localStorage.getItem('tritime_staff')), out = {};
          st.forEach(function(s){ var n = document.querySelector('[data-mdn="' + s.id + '"]');
            out[s.name] = n ? { n:n.value, days:[].slice.call(document.querySelectorAll('[data-mdd="' + s.id + '"]:checked')).map(function(c){ return c.value; }) } : null; });
          return out; })()""")
        assert info['非常勤 二子'] and info['非常勤 二子']['days'] == ['2', '4'] and info['非常勤 二子']['n'] == '3', '公休の入った非常勤の出る曜日が、公休以外（火・木）・1日3件になりません：' + str(info['非常勤 二子'])
        assert info['非常勤 四子'] and info['非常勤 四子']['days'] == [] , '公休の入っていない非常勤が、週間予定から取る形のままになりません：' + str(info['非常勤 四子'])
        assert info['待機 三子'] is None, '待機の人がモデルコースの条件の表に出ています'
        assert info['常勤 一子'] and info['常勤 一子']['days'] == ['1', '2', '3', '4', '5'], '常勤の出る曜日が変わっています：' + str(info['常勤 一子'])
        await s.shot('#md_staff', 'TriTime_model_hj.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
