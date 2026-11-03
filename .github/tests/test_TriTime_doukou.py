# -*- coding: utf-8 -*-
"""トライタイムの同行の「未定」の試験（2026-11-03・宏史さん「決まっていない場合の選ぶ選択肢が無い。2名（看護師）とか2名（准看護師）とか2名（看護助手）とかの選択肢も付けてほしい」）
・週間予定の「同行する職員」の欄に「2名（看護師・未定）」「2名（准看護師・未定）」「2名（看護補助者・未定）」が出る
・登録した後でも、一覧の各行の同行の欄で選ぶとすぐ残る
・「2名（准看護師・未定）」にした週2回は、見本の上振れで准看護師の加算（3,800円×2回＝7,600円）で数える"""
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
        sid = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_staff')).filter(function(s){ return s.name === '看護 一子'; })[0].id")
        await pg.evaluate("""(sid) => { var t = Date.now();
          localStorage.setItem('tritime_patients', JSON.stringify([{ no:'2010-01-看-9002', name:'試験 未定', area:'東町', status:'利用中', ins:'精神科訪問看護（医療）', team:'2名', upd:t }]));
          localStorage.setItem('tritime_weekly', JSON.stringify([
            { id:'w1', dow:'1', time:'09:15', min:30, no:'2010-01-看-9002', staffId:sid, withId:'', upd:t },
            { id:'w2', dow:'3', time:'09:15', min:30, no:'2010-01-看-9002', staffId:sid, withId:'', upd:t } ])); }""", sid)
        # 画面を描き直させる（職員をもう1人入れると、名簿・設定の画面が全部描き直される）
        await pg.evaluate(ADD, {'name':'看護 二子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'})
        opts = await pg.evaluate("[].map.call(document.getElementById('wk_with').options, function(o){ return o.textContent; })")
        for w in ['2名（看護師・未定）', '2名（准看護師・未定）', '2名（看護補助者・未定）']:
            assert w in opts, '週間予定の「同行する職員」に「%s」がありません：%s' % (w, '、'.join(opts))
        n = await pg.evaluate("document.querySelectorAll('#wkList select[data-wkwith]').length")
        assert n == 2, '週間予定の一覧の各行に同行の欄がありません（%d）' % n
        for wid in ['w1', 'w2']:
            await pg.select_option('#wkList select[data-wkwith="%s"]' % wid, 'tbd:j'); await pg.wait_for_timeout(300)
        got = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_weekly')).map(function(v){ return v.withId; })")
        assert got == ['tbd:j', 'tbd:j'], '一覧の同行の欄で選んだものが残りません：' + str(got)
        txt = await pg.evaluate("document.getElementById('wkList').innerText")
        await s.shot('#cardWk', 'TriTime_doukou_ichiran.png')
        await pg.evaluate("document.querySelector('#tabs button[data-tab=mihon]').click()"); await pg.wait_for_timeout(300)
        await pg.click('[data-mh="3000000"]'); await pg.wait_for_timeout(200)
        await pg.click('#mh_make'); await pg.wait_for_timeout(500)
        t = await pg.evaluate("document.getElementById('tab-mihon').innerText")
        line = ([l for l in t.split('\n') if '2名体制の加算（いまの週間予定で' in l] or [''])[0]
        assert '週 2回' in line and '7,600' in line, '「2名（准看護師・未定）」の週2回が、准看護師の加算（3,800円×2回＝7,600円）で数えられません：' + line
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
