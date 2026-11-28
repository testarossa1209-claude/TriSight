# -*- coding: utf-8 -*-
"""TriTalk.html：ノアメインPCだけに出る「同時通訳を出す／しまう」の切り替え（2026-11-27）。端末の名前は試験の側で答える。
① 登録名「ノアメインPC」：画面下に切り替えが出る。最初はつまみが出ず、押すと出て、もう一度押すと消える
② 登録名「ノア看護タブレット」：切り替えもつまみも出ない
③ 登録名「トライサイトメインPC」：切り替えは出ず、つまみが自動で出る
④ 画面の中で誤りが起きない"""
import sys, os, json, threading, http.server, socketserver, functools
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, ROOT

async def test(p):
    s = Screen(); name = {'v': ''}
    async def gate(route):
        b = json.loads(route.request.post_data or '{}')
        if b.get('task') == 'whoami':
            await route.fulfill(status=200, content_type='application/json', body=json.dumps({'dev': {'name': name['v']}}, ensure_ascii=False))
        else:
            await route.continue_()
    pg = await s.open(p, 'TriTalk.html')
    await pg.route('**/api/gate*', gate)
    H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); H.log_message = lambda *a, **k: None
    srv = socketserver.TCPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d/TriTalk.html' % srv.server_address[1]
    async def go(n):
        name['v'] = n
        await pg.goto(base); await pg.wait_for_timeout(300)
        await pg.evaluate("localStorage.removeItem('tritalk_interp');localStorage.setItem('trisight_access_code','TEST-CODE')")
        await pg.goto(base); await pg.wait_for_timeout(1500)
        if await pg.query_selector('#ogGo'):
            await pg.click('#ogGo'); await pg.wait_for_timeout(1000)
    try:
        await go('ノアメインPC')
        assert await pg.is_visible('#itSwitch'), 'ノアメインPCに切り替えが出ません'
        assert not await pg.is_visible('#gkTabInt'), 'ノアメインPCで、押す前からつまみが出ています'
        await pg.click('#itSwitch'); await pg.wait_for_timeout(300)
        assert await pg.is_visible('#gkTabInt') and 'しまう' in await pg.inner_text('#itSwitch'), '押してもつまみが出ません'
        await pg.click('#itSwitch'); await pg.wait_for_timeout(300)
        assert not await pg.is_visible('#gkTabInt') and '出す' in await pg.inner_text('#itSwitch'), 'もう一度押してもつまみが消えません'
        await go('ノア看護タブレット')
        assert not await pg.is_visible('#itSwitch') and not await pg.is_visible('#gkTabInt'), 'ノアのほかの端末に切り替えかつまみが出ています'
        await go('トライサイトメインPC')
        assert not await pg.is_visible('#itSwitch'), 'トライサイトメインPCに切り替えが出ています'
        assert await pg.is_visible('#gkTabInt'), 'トライサイトメインPCにつまみが自動で出ません'
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        srv.shutdown(); await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
