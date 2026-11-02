# -*- coding: utf-8 -*-
"""トライタイムの訪問回数の試験（2026-11-03・宏史さんの指摘「週2回の人の、2回目の曜日はどうやって入れるの」）
・利用者登録の「訪問の回数・時間帯の取り決め」に「週2回」とあれば、週間予定に1件しか入っていなくても、自動の振り分けは週2回で組む
・「この組み方を週間予定に入れる」を押すと、週間予定が2件になり、仮スケジュール表にも2件出る
・回数の欄が空の人は、これまでどおり週間予定の回数（無ければ週1回）で組む"""
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
    s = Screen(); pg = await s.open(p, 'TriTime.html')
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        for x in [{'name':'常勤 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
                  {'name':'常勤 二子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'}]:
            await pg.evaluate(ADD, x)
        await pg.evaluate("""(function(){
          var st = JSON.parse(localStorage.getItem('tritime_staff') || '[]'), sid = st.filter(function(s){ return s.name === '常勤 二子'; })[0].id, t = Date.now();
          localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9001', name:'試験 二回', area:'東町', status:'利用中', freq:'週2回', wDays:['2','4'], upd:t },
            { no:'2010-01-看-9002', name:'試験 一回', area:'東町', status:'利用中', upd:t } ]));
          localStorage.setItem('tritime_weekly', JSON.stringify([ { id:'w1', dow:'2', time:'09:15', min:30, no:'2010-01-看-9001', staffId:sid, withId:'', upd:t } ])); })()""")
        # 画面は記録を毎回 localStorage から読むので、開き直さずにそのまま使う
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(400)
        await pg.wait_for_selector('#au_make', state='visible', timeout=15000)
        await pg.click('#au_make'); await pg.wait_for_timeout(800)
        if not await pg.is_visible('#au_apply'):
            info = await pg.evaluate("[document.getElementById('au_out').innerText.slice(0,200), localStorage.getItem('tritime_patients'), (localStorage.getItem('tritime_staff')||'').slice(0,300)]")
            assert False, '組み方が出ません：' + ' ｜ '.join(str(x) for x in info)
        await s.shot('#cardAuto', 'TriTime_kaisuu_kumikata.png')
        await pg.evaluate("window.confirm = function(){ return true; }")
        await pg.click('#au_apply', timeout=15000); await pg.wait_for_timeout(400)
        wk = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_weekly')).filter(function(v){ return !v.del; }).map(function(v){ return [v.no, String(v.dow)]; })")
        two = sorted(d for n, d in wk if n == '2010-01-看-9001'); one = [d for n, d in wk if n == '2010-01-看-9002']
        assert len(two) == 2, '「週2回」と登録した人が、週間予定の1件に引っぱられて週' + str(len(two)) + '回で組まれます'
        assert two == ['2', '4'], '希望の曜日（火・木）で組まれません：' + '、'.join(two)
        assert len(one) == 1, '回数の欄が空の人が週1回で組まれません：' + str(len(one))
        await pg.evaluate("document.getElementById('ssTab').click()"); await pg.wait_for_timeout(500)
        chips = await pg.evaluate("[].slice.call(document.querySelectorAll('#ssBody .ssChip')).filter(function(e){ return e.textContent.indexOf('看-9001') >= 0; }).length")
        assert chips == 2, '仮スケジュール表に週2回の2件が出ません：' + str(chips)
        await s.shot('#ssBody', 'TriTime_kaisuu_karisuke.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
