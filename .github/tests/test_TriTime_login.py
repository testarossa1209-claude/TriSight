# -*- coding: utf-8 -*-
"""トライタイムのログイン画面の試験（2026-11-09・宏史さんの提案）
・認証コードの画面（端末ごとに初回だけ）が、トライタイムの顔（アイコン・名前・「トライタイムを開く」のボタン）で出る
・開くたびのログイン画面に、この端末の「主に使う人」の名前だけが出て、ボタンで開ける（他の職員の名前は選べない）"""
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
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=900, h=1000)
    try:
        # ① 認証コードの画面（初回）
        await pg.evaluate("localStorage.removeItem('trisight_open_tritime')"); await pg.reload(); await pg.wait_for_timeout(800)
        g = await pg.inner_text('#openGate')
        assert 'TriTime' in g and 'トライタイムを開く' in g and '認証コード' in g, '認証コードの画面がトライタイムの顔で出ません：' + g[:200]
        await s.shot('#openGate', 'TriTime_login_code.png')
        await pg.click('#ogGo'); await pg.wait_for_timeout(2000)
        assert not await pg.query_selector('#openGate'), '認証コードを確かめても開きません'
        # ② 職員を2人入れ、この端末の主に使う人を1人目にする
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        await pg.evaluate(ADD, {'name':'試験 花子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'})
        await pg.evaluate(ADD, {'name':'試験 管理', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'})
        await pg.evaluate("""(function(){ var st = JSON.parse(localStorage.getItem('tritime_staff')); var a = st.filter(function(x){ return x.name === '試験 花子'; })[0].id;
          var d = JSON.parse(localStorage.getItem('tritime_device') || '{}'); d.me = a; d.share = true; localStorage.setItem('tritime_device', JSON.stringify(d));
          localStorage.setItem('tritime_login_test', '1'); })()""")
        await pg.reload(); await pg.wait_for_timeout(2500)
        lg = await pg.query_selector('#ttLogin')
        assert lg, '開いてもログイン画面が出ません'
        t = await pg.inner_text('#ttLogin')
        assert '試験 花子さん' in t and '試験 管理' not in t, 'ログイン画面に、主に使う人以外の名前が出ています：' + t[:200]
        await s.shot('#ttLogin .lgCard', 'TriTime_login_name.png')
        b = await pg.query_selector('#lgOpen') or await pg.query_selector('#lgOffice')
        assert b, 'ログイン画面に開くボタンがありません'
        await b.click(); await pg.wait_for_timeout(800)
        assert not await pg.query_selector('#ttLogin'), 'ボタンを押してもログイン画面が閉じません'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
