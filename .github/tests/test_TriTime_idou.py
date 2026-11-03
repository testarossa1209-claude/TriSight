# -*- coding: utf-8 -*-
"""トライタイムの移動の時間の試験（2026-11-03・宏史さん「移動の時間を最長でも20分にしてください。通常は10分〜15分です」）
・移動の目安は最短10分・最長20分（前に最短5分・最長15分で保存してあっても、10分・20分になる）
・自動の振り分けは、訪問と訪問の間を ふだんの移動（最短と最長の真ん中＝15分）で詰めて組む（9:15 → 10:00 → 10:45）
・勤務の決まりで保存し直した値は、そのまま使う"""
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
        await pg.evaluate("""(function(){ var t = Date.now();
          /* 前の決まり（最短5分・最長15分）で保存してあった形 */
          var keys = []; for(var i = 0; i < localStorage.length; i++) keys.push(localStorage.key(i));
          var k = keys.filter(function(x){ return /settings/.test(x) && x.indexOf('tritime') === 0; })[0] || 'tritime_settings';
          var st = JSON.parse(localStorage.getItem(k) || '{}'); st.work = Object.assign({}, st.work || {}, { mvMin:5, mvMax:15 }); localStorage.setItem(k, JSON.stringify(st));
          localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9501', name:'試験 一', area:'東町', status:'利用中', wDays:['1'], upd:t },
            { no:'2010-01-看-9502', name:'試験 二', area:'東町', status:'利用中', wDays:['1'], upd:t },
            { no:'2010-01-看-9503', name:'試験 三', area:'東町', status:'利用中', wDays:['1'], upd:t } ]));
          localStorage.setItem('tritime_weekly', '[]'); })()""")
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(200)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        mv = await pg.evaluate("[document.getElementById('wr_mvmin').value, document.getElementById('wr_mvmax').value]")
        assert mv == ['10', '20'], '移動の目安が最短10分・最長20分になりません：' + str(mv)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(400)
        await pg.wait_for_selector('#au_make', state='visible', timeout=15000)
        await pg.click('#au_make'); await pg.wait_for_timeout(800)
        au = await pg.inner_text('#au_out table')
        for t in ['09:15', '10:00', '10:45']:
            assert t in au.replace('\n', ' '), '訪問の間が15分で詰めて組まれません（%s が無い）：%s' % (t, au[:300])
        await s.shot('#cardAuto', 'TriTime_idou.png')
        # 勤務の決まりで保存し直した値（最短10・最長30）は、そのまま使う
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        await pg.fill('#wr_mvmax', '30'); await pg.click('#wr_save'); await pg.wait_for_timeout(300)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(200)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        mv2 = await pg.evaluate("document.getElementById('wr_mvmax').value")
        assert mv2 == '30', '勤務の決まりで保存し直した移動の最長が残りません：' + mv2
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
