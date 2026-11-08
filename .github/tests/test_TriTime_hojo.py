# -*- coding: utf-8 -*-
"""トライタイムの看護補助者・同行の試験（2026-11-03・宏史さんの指示「看護補助は単独では訪問看護に行けない。2名体制の同行のみ。看護助手の依頼で介護部の職員を同行させる場合がある」）
・職種に「看護補助者」があり、看護補助者は訪問看護部の職員として扱われる
・週間予定の「担当」には看護師・准看護師だけが出て、看護補助者は出ない。「同行する職員」には看護補助者と、介護部の職員（部署名付き）も出る
・モデルコースの条件の表に看護補助者は出ない
・仮スケジュール表で、札を看護補助者の升へ離すと「単独では訪問できません」と出て、同行として付けられる。付けると看護補助者の行に「同行」の札が出る"""
import sys, os, datetime
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

ADD = """async (p) => {
  const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', {bubbles:true})); };
  set('st_name', p.name); set('st_dept', p.dept); set('st_emp', p.emp); set('st_job', p.job);
  await new Promise(r => setTimeout(r, 100));
  document.getElementById('st_add').click();
  await new Promise(r => setTimeout(r, 200));
}"""

async def drag(pg, src, dst):
    a = await pg.eval_on_selector(src, "e => { e.scrollIntoView({block:'center', inline:'center'}); const r = e.getBoundingClientRect(); return [r.x + r.width/2, r.y + r.height/2]; }")
    b = await pg.eval_on_selector(dst, "e => { const r = e.getBoundingClientRect(); return [r.x + r.width/2, r.y + r.height - 6]; }")
    await pg.mouse.move(a[0], a[1]); await pg.mouse.down()
    for i in range(1, 11):
        await pg.mouse.move(a[0] + (b[0] - a[0]) * i / 10, a[1] + (b[1] - a[1]) * i / 10); await pg.wait_for_timeout(20)
    await pg.mouse.up(); await pg.wait_for_timeout(300)

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1500, h=1000)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        jobs = await pg.evaluate("[].slice.call(document.querySelectorAll('#st_job option')).map(function(o){ return o.textContent; })")
        assert '看護補助者' in jobs, '職種に「看護補助者」がありません'
        for x in [{'name':'看護 一子', 'dept':'', 'job':'看護師（正看）', 'emp':'常勤'},
                  {'name':'補助 二郎', 'dept':'', 'job':'看護補助者', 'emp':'常勤'},
                  {'name':'介護 三郎', 'dept':'訪問介護部', 'job':'介護福祉士', 'emp':'常勤'}]:
            await pg.evaluate(ADD, x)
        assert '補助 二郎' in await pg.inner_text('#stList'), '看護補助者が訪問看護部の職員として出ません'
        ws = await pg.evaluate("[].slice.call(document.querySelectorAll('#wk_staff option')).map(function(o){ return o.textContent; }).join('、')")
        ww = await pg.evaluate("[].slice.call(document.querySelectorAll('#wk_with option')).map(function(o){ return o.textContent; }).join('、')")
        assert '看護 一子' in ws and '補助 二郎' not in ws, '週間予定の担当に看護補助者が出ています：' + ws
        assert '補助 二郎' in ww and '介護 三郎（訪問介護部）' in ww, '同行の選択に看護補助者・介護部の職員が出ません：' + ww
        await s.shot('#cardWk', 'TriTime_hojo_wk.png')

        await pg.evaluate("document.querySelector('#tabs button[data-tab=model]').click()"); await pg.wait_for_timeout(500)
        md = await pg.inner_text('#md_staff')
        assert '看護 一子' in md and '補助 二郎' not in md, 'モデルコースの条件の表に看護補助者が出ています'

        today = datetime.date.today(); mon = today + datetime.timedelta(days=(7 - today.weekday()))
        sid1, sid2 = await pg.evaluate("(function(){ var st = JSON.parse(localStorage.getItem('tritime_staff')); return ['看護 一子','補助 二郎'].map(function(n){ return st.filter(function(s){ return s.name === n; })[0].id; }); })()")
        await pg.evaluate("""(sid) => { var t = Date.now();
          localStorage.setItem('tritime_patients', JSON.stringify([{ no:'2010-01-看-9001', name:'試験 一', area:'東町', status:'利用中', upd:t }]));
          localStorage.setItem('tritime_weekly', JSON.stringify([{ id:'w1', dow:'1', time:'09:15', min:30, no:'2010-01-看-9001', staffId:sid, withId:'', upd:t }])); }""", sid1)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('ssTab').click()"); await pg.wait_for_timeout(400)
        await pg.evaluate("(d) => { var e = document.getElementById('ssFrom'); e.value = d; e.dispatchEvent(new Event('change')); }", mon.isoformat()); await pg.wait_for_timeout(400)   # 2026-11-08：表は開いた日から7日分。来週の月曜から出す
        await drag(pg, '#ssBody .ssChip.dg[data-vk="%s|2010-01-看-9001|09:15"]' % mon.isoformat(), '#ssBody td[data-sid="%s"][data-date="%s"]' % (sid2, mon.isoformat()))
        t = await pg.inner_text('#ssMv')
        assert '単独では訪問できません' in t, '看護補助者の升へ離しても「単独では訪問できません」が出ません'
        assert not await pg.query_selector('#mv_once'), '看護補助者の升へ離したのに、単独で動かすボタンが出ています'
        await pg.click('#mv_with'); await pg.wait_for_timeout(300)
        await pg.evaluate("window.confirm = function(){ return true; }; var b = document.getElementById('ssd_commit'); if(b && !b.disabled) b.click();"); await pg.wait_for_timeout(500)   # 2026-11-08：仮スケジュール表の下書きを本体に反映する
        await s.shot('#ssMv .card', 'TriTime_hojo_with.png')
        await pg.click('#mv_close'); await pg.wait_for_timeout(300)
        wk = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_weekly')).filter(function(v){ return !v.del; })")
        assert wk[0]['staffId'] == sid1 and wk[0]['withId'] == sid2, '同行として付きません：' + str(wk)
        c = await pg.inner_text('#ssBody td[data-sid="%s"][data-date="%s"]' % (sid2, mon.isoformat()))
        assert '同行' in c and '9001' in c, '看護補助者の行に「同行」の札が出ません：' + c
        await s.shot('#ssPanel', 'TriTime_hojo_karisuke.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
