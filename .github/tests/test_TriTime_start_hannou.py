# -*- coding: utf-8 -*-
"""トライタイムの「事務所から始める」の反応の試験（2026-11-15・宏史さん「押しても反応がない。レスポンス悪すぎ」）
・ログイン画面のボタンを押したその瞬間に、ログイン画面が消え「トライタイムを開いています…」が出る（重い描き直しは後に回す）
・「あとで始める」のあと上の帯に出るボタンも同じで、押した瞬間に帯が消える
・押した記録（その日の始まり）は残り、少し待つと「開いています…」が消える"""
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
PRESS = """(id) => { document.getElementById(id).click();
  return { busy: !!document.getElementById('stBusy'), login: !!document.getElementById('ttLogin'), win: !!document.getElementById('stStart') }; }"""
STARTS = "() => JSON.parse(localStorage.getItem('tritime_events') || '[]').filter(e => e && e.type === 'start' && !e.del).length"

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=900, h=1000)
    try:
        await pg.clock.set_fixed_time('2026-11-16T08:20:00+09:00')   # 月曜の朝（仕事の日）
        await pg.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false })")   # 人が使う端末と同じ動きにする
        await pg.reload(); await pg.wait_for_timeout(1500)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        await pg.evaluate(ADD, {'name':'試験 花子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'})
        # ① ログイン画面（専用の端末）
        await pg.evaluate("""(function(){ var st = JSON.parse(localStorage.getItem('tritime_staff')); var a = st.filter(function(x){ return x.name === '試験 花子'; })[0].id;
          localStorage.setItem('tritime_device', JSON.stringify({ me:a, share:true })); localStorage.setItem('tritime_login_test', '1'); })()""")
        await pg.reload()
        try: await pg.wait_for_selector('#lgOffice', timeout=15000)   # 混んでいる機械でも待てるように
        except Exception: pass
        assert await pg.query_selector('#lgOffice'), 'ログイン画面に「事務所から始める」が出ません'
        await s.shot('#ttLogin .lgCard', 'TriTime_start_login.png')
        r = await pg.evaluate(PRESS, 'lgOffice')
        assert not r['login'], '押した瞬間にログイン画面が消えません'
        assert r['busy'], '押した瞬間に「トライタイムを開いています…」が出ません'
        await pg.wait_for_timeout(1500)
        assert not await pg.query_selector('#stBusy'), '「開いています…」が消えません'
        assert await pg.evaluate(STARTS) == 1, 'その日の始まりの記録が残っていません'
        # ② 「あとで始める」を押したあと、上の帯の「事務所から始める」
        await pg.evaluate("() => { localStorage.setItem('tritime_events', '[]'); localStorage.removeItem('tritime_start_skip'); }")
        await pg.reload()
        try: await pg.wait_for_selector('#lgLater', timeout=15000)
        except Exception: pass
        assert await pg.query_selector('#lgLater'), 'ログイン画面に「あとで始める」が出ません'
        r = await pg.evaluate(PRESS, 'lgLater')
        assert not r['login'], '「あとで始める」を押した瞬間にログイン画面が消えません'
        await pg.wait_for_timeout(1500)
        assert await pg.query_selector('#stBarOffice'), '上の帯に「事務所から始める」が出ません'
        r = await pg.evaluate("""() => { document.getElementById('stBarOffice').click();
          var bar = document.getElementById('stBar'); return { busy: !!document.getElementById('stBusy'), bar: !!(bar && bar.style.display !== 'none' && bar.innerHTML) }; }""")
        assert not r['bar'], '帯のボタンを押した瞬間に帯が消えません'
        assert r['busy'], '帯のボタンを押した瞬間に「トライタイムを開いています…」が出ません'
        await pg.wait_for_timeout(1500)
        assert not await pg.query_selector('#stBusy'), '「開いています…」が消えません'
        assert await pg.evaluate(STARTS) == 1, '帯で押した記録が残っていません'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
