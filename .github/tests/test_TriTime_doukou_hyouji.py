# -*- coding: utf-8 -*-
"""トライタイムの同行の表示の試験（2026-11-03・宏史さん「同行者の予定なども表示されていないよね」）
・仮スケジュール表：担当の札に「2名・同行 ◯◯」「2名・同行未定（看護師）」「2名・同行未定」が出る。同行の職員の行には「同行」の札が出る
・自動の振り分けの表：担当の札に同行が出て、同行の職員の升に「同行」の札が出る
・1日の予定：担当の行に「2名・同行 ◯◯」、同行の職員の行に「同行（担当 ◯◯さん）」が出る"""
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
        for x in [{'name':'担当 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
                  {'name':'同行 二子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'}]:
            await pg.evaluate(ADD, x)
        ids = await pg.evaluate("(function(){ var st = JSON.parse(localStorage.getItem('tritime_staff')); return ['担当 一子','同行 二子'].map(function(n){ return st.filter(function(s){ return s.name === n; })[0].id; }); })()")
        await pg.evaluate("""(a) => { var t = Date.now(), d = new Date(), dow = String(d.getDay());
          localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9201', name:'試験 同行あり', area:'東町', status:'利用中', team:'2名', upd:t },
            { no:'2010-01-看-9202', name:'試験 職種未定', area:'東町', status:'利用中', team:'2名', upd:t },
            { no:'2010-01-看-9203', name:'試験 空', area:'東町', status:'利用中', team:'2名', upd:t } ]));
          localStorage.setItem('tritime_weekly', JSON.stringify([
            { id:'w1', dow:dow, time:'09:15', min:30, no:'2010-01-看-9201', staffId:a[0], withId:a[1], upd:t },
            { id:'w2', dow:dow, time:'10:45', min:30, no:'2010-01-看-9202', staffId:a[0], withId:'tbd:n', upd:t },
            { id:'w3', dow:dow, time:'13:15', min:30, no:'2010-01-看-9203', staffId:a[0], withId:'', upd:t } ])); }""", ids)
        # 仮スケジュール表
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('ssTab').click()"); await pg.wait_for_timeout(600)
        ss = await pg.inner_text('#ssBody')
        for w in ['2名・同行 同行 二子', '2名・同行未定（看護師）', '2名・同行未定']:
            assert w in ss, '仮スケジュール表の担当の札に「%s」が出ません' % w
        assert '担当 担当 一子' in ss, '仮スケジュール表の同行の職員の行に、同行の札（担当 ◯◯）が出ません'
        await s.shot('#ssBody', 'TriTime_doukou_karisuke.png')
        await pg.evaluate("document.body.classList.remove('ssOpen')")
        # 自動の振り分けの表
        await pg.evaluate("document.getElementById('auTab').click()"); await pg.wait_for_timeout(300)   # 2026-11-08：自動の振り分けは右端の「自動組み」の引き出しの中
        await pg.wait_for_selector('#au_make', state='visible', timeout=15000)
        await pg.evaluate("document.getElementById('auTab').click()"); await pg.wait_for_timeout(300)   # 2026-11-08：自動の振り分けは右端の「自動組み」の引き出しの中
        await pg.click('#au_make'); await pg.wait_for_timeout(800)
        au = await pg.inner_text('#au_out')
        # 2026-11-03-20 から、職種だけの同行（看護師・未定）と、体制2名で同行が空の訪問にも、自動の振り分けで人が付く
        assert au.count('2名・同行 同行 二子') == 3 and '同行未定' not in au.split('職員')[-1], '自動の振り分けの表の札に同行が出ません'
        assert '同行 2010-01-看-9201' in au, '自動の振り分けの表で、同行の職員の升に「同行」の札が出ません'
        # 1日の予定（担当の職員）
        await pg.select_option('#td_staff', ids[0]); await pg.wait_for_timeout(500)
        dp = await pg.evaluate("document.getElementById('tab-plan').innerText")
        assert '2名・同行 同行 二子' in dp, '1日の予定の担当の行に同行が出ません'
        await pg.select_option('#td_staff', ids[1]); await pg.wait_for_timeout(500)
        wk2 = await pg.evaluate("document.getElementById('td_week').innerText")
        assert '同行' in wk2 and '担当 担当 一子' in wk2, '本スケジュール表の同行の職員の行に「同行」の札が出ません：' + wk2[:300]
        await pg.evaluate("document.getElementById('td_dayBox').open = true"); await pg.wait_for_timeout(100)
        dp2 = await pg.evaluate("document.getElementById('tab-plan').innerText")
        assert '同行（担当 担当 一子さん）' in dp2, '1日の予定の同行の職員の行に「同行（担当 ◯◯さん）」が出ません'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
