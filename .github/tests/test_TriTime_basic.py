# -*- coding: utf-8 -*-
"""トライタイムの基本の試験（2026-11-02）：開ける・職員を足せる・画面の中で誤りが出ない"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html')
    try:
        assert not await pg.query_selector('#openGate'), '認証コードの入口を通れません'
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        await pg.fill('#st_name', '試験 花子'); await pg.click('#st_add'); await pg.wait_for_timeout(300)
        txt = await pg.inner_text('#stList')
        assert '試験 花子' in txt, '「名簿・設定」で職員を足しても、職員の表に出ません'
        await s.shot('#cardStaff', 'TriTime_staff.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
