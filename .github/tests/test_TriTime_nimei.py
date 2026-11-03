# -*- coding: utf-8 -*-
"""トライタイムの2名体制の売上の数え方の試験（2026-11-03・宏史さんの指示「同行者が決まらない場合でも指示書では2名体制なので、売上は2名で計算。同行者に看護師を指定していれば看護師料金、指定がなければ看護助手で計算」）
・「モデルコースの見本」の「選んだコースに届くまでの道のり」の上振れの行で、体制が2名で同行者の決まっていない訪問は、週の1回目を看護補助者の加算（3,000円）、2回目以降を看護師の加算（4,500円）で数える（2026-11-03 宏史さんの指示「残りの回は看護師料金が加算されない」）
・同行者に看護師を入れた訪問は、看護師どうしの加算（4,500円）で数える"""
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
        for x in [{'name':'看護 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
                  {'name':'看護 二子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'}]:
            await pg.evaluate(ADD, x)
        ids = await pg.evaluate("(function(){ var st = JSON.parse(localStorage.getItem('tritime_staff')); return ['看護 一子','看護 二子'].map(function(n){ return st.filter(function(s){ return s.name === n; })[0].id; }); })()")
        async def setup(withNurse):
            await pg.evaluate("""(a) => { var t = Date.now(), ins = '精神科訪問看護（医療）';
              localStorage.setItem('tritime_patients', JSON.stringify([{ no:'2010-01-看-9001', name:'試験 二名', area:'東町', status:'利用中', ins:ins, team:'2名', upd:t }]));
              localStorage.setItem('tritime_weekly', JSON.stringify([
                { id:'w1', dow:'1', time:'09:15', min:30, no:'2010-01-看-9001', staffId:a[0], withId:a[2] ? a[1] : '', upd:t },
                { id:'w2', dow:'3', time:'09:15', min:30, no:'2010-01-看-9001', staffId:a[0], withId:a[2] ? a[1] : '', upd:t } ])); }""", [ids[0], ids[1], withNurse])
            await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(200)
            await pg.evaluate("document.querySelector('#tabs button[data-tab=mihon]').click()"); await pg.wait_for_timeout(300)
            await pg.click('[data-mh="3000000"]'); await pg.wait_for_timeout(200)
            await pg.click('#mh_make'); await pg.wait_for_timeout(500)
            t = await pg.evaluate("document.getElementById('tab-mihon').innerText")
            line = [l for l in t.split('\n') if '上振れ：2名体制の加算' in l]
            return line[0] if line else ''
        l1 = await setup(False)
        assert '週 2回' in l1 and '7,500' in l1, '同行者の決まっていない2名体制の週2回が、1回目は看護補助者3,000円・2回目は看護師4,500円（計7,500円）で数えられません：' + l1
        await s.shot('#tab-mihon', 'TriTime_nimei_hojo.png')
        l2 = await setup(True)
        assert '週 2回' in l2 and '9,000' in l2, '看護師を同行者にした2名体制が、看護師の加算（4,500円×2回）で数えられません：' + l2
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
