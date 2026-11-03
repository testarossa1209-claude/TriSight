# -*- coding: utf-8 -*-
"""トライタイムの「合言葉の入っていない端末」の知らせの試験（2026-11-03・宏史さん「ラップトップのお知らせ画面は携帯番号がすべてなし。共有の問題ですかね」）
・共有していない端末：お知らせの引き出しの中に「共有していません」が出る（画面の上には出さない）
・共有していて合言葉の無い端末：画面の上に「合言葉が入っていません」が出て、ボタンで「記録の鍵（合言葉）」の欄へ行ける"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        top = await pg.inner_text('#shWarn')
        assert top.strip() == '', '共有していない端末の画面の上に、知らせが出ています：' + top
        await pg.click('#osTab'); await pg.wait_for_timeout(400)
        ob = await pg.inner_text('#osBody')
        assert 'ほかの端末と記録を共有していません' in ob, 'お知らせの中に「共有していません」が出ません'
        await pg.click('#osClose'); await pg.wait_for_timeout(300)
        await pg.add_init_script("""(function(){ try{ var d = JSON.parse(localStorage.getItem('tritime_device') || '{}'); d.share = true; localStorage.setItem('tritime_device', JSON.stringify(d));
          localStorage.removeItem('tritime_key'); localStorage.setItem('tritime_locked', JSON.stringify([{ col:'patients', id:'x1', enc:'aaa' }])); }catch(e){} })()""")

        await pg.reload(); await pg.wait_for_timeout(1500)
        if await pg.query_selector('#ogGo'):
            await pg.click('#ogGo'); await pg.wait_for_timeout(2500)
        try: await pg.wait_for_function("(document.getElementById('shWarn') || {}).textContent && document.getElementById('shWarn').textContent.indexOf('合言葉') >= 0", timeout=8000)
        except Exception: pass
        top = await pg.inner_text('#shWarn')
        assert '合言葉が入っていません' in top and '1件' in top, '合言葉の無い端末の画面の上に、知らせが出ません：' + top
        await s.shot('#shWarn', 'TriTime_aikotoba_chuui.png')
        await pg.click('#shWarn [data-shgo]'); await pg.wait_for_timeout(600)
        on = await pg.evaluate("document.getElementById('tab-setup').classList.contains('on')")
        assert on, 'ボタンを押しても「名簿・設定」タブに移りません'
        assert await pg.is_visible('#cardKey'), '「記録の鍵（合言葉）」の欄が出ません'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
