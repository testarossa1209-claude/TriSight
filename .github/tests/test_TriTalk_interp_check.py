# -*- coding: utf-8 -*-
"""TriTalk.html の「同時通訳を使う」チェック欄（2026-11-28・宏史さんの決定）。どの端末でも同じ動き。
① 最初はチェックが外れていて、「同時通訳」のつまみも「日本語｜English」も出ない
② 入れると、つまみがつまみの列のいちばん下に出て、「日本語｜English」も出る。開き直しても覚えている
③ 外すと、つまみと「日本語｜English」が消え、引き出しが開いていれば閉じる
④ 端末の名前を問い合わせない（whoami を呼ばない）。画面の中で誤りが起きない"""
import sys, os, json, threading, http.server, socketserver, functools
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, ROOT

async def test(p):
    s = Screen(); who = []
    async def gate(route):
        b = json.loads(route.request.post_data or '{}')
        if b.get('task') == 'whoami': who.append(1)
        await route.continue_()
    pg = await s.open(p, 'TriTalk.html')
    await pg.route('**/api/gate*', gate)
    H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); H.log_message = lambda *a, **k: None
    srv = socketserver.TCPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d/TriTalk.html' % srv.server_address[1]
    async def go():
        await pg.goto(base); await pg.wait_for_timeout(1200)
        if await pg.query_selector('#ogGo'):
            await pg.click('#ogGo'); await pg.wait_for_timeout(1000)
    try:
        await go(); await pg.evaluate("localStorage.removeItem('tritalk_interp');localStorage.setItem('trisight_access_code','TEST-CODE')"); await go()
        # ①
        assert not await pg.is_checked('#itUse'), '最初からチェックが入っています'
        assert not await pg.is_visible('#gkTabInt') and not await pg.is_visible('#langSw'), '最初からつまみか「日本語｜English」が出ています'
        # ②
        await pg.check('#itUse'); await pg.wait_for_timeout(300)
        assert await pg.is_visible('#gkTabInt') and await pg.is_visible('#langSw'), 'チェックを入れてもつまみか「日本語｜English」が出ません'
        last = await pg.evaluate("(function(){ var t = [].filter.call(document.querySelectorAll('.gkTabs > *'), function(e){ return e.offsetParent !== null; }); return t[t.length-1].id; })()")
        assert last == 'gkTabInt', '「同時通訳」がつまみの列のいちばん下にありません：' + last
        await go()
        assert await pg.is_checked('#itUse') and await pg.is_visible('#gkTabInt'), '開き直すと覚えていません'
        # ③
        await pg.click('#gkTabInt'); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('itUse').click()"); await pg.wait_for_timeout(300)
        assert not await pg.is_visible('#gkTabInt') and not await pg.is_visible('#langSw'), '外してもつまみか「日本語｜English」が残ります'
        assert not await pg.evaluate("document.body.classList.contains('gk_intOpen')"), '外しても引き出しが開いたままです'
        # ④
        assert not who, '端末の名前を問い合わせています'
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        srv.shutdown(); await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
