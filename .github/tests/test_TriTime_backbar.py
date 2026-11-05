# -*- coding: utf-8 -*-
"""「前のページに戻る」のボタン（全画面共通）：前の画面が無いときは出さない（2026-11-06・宏史さんの指示）
・トライタイムを直接開くと、ボタンが出ない
・同じ場所の別の画面（index.html）から開くと、ボタンが出る"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

import threading, http.server, socketserver, functools
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

async def test(p):
    # file:// では前の画面（referrer）が付かないため、手元の http で開く
    H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    srv = socketserver.TCPServer(('127.0.0.1', 0), H); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1000, h=700)
    try:
        base = 'http://127.0.0.1:%d/' % port
        await pg.context.add_init_script("localStorage.setItem('trisight_open_tritime','1');")   # 開くときの関所は通した状態で見る
        await pg.goto(base + 'TriTime.html'); await pg.wait_for_timeout(1000)
        assert await pg.evaluate("getComputedStyle(document.getElementById('tsBackBar')).display") == 'none', '直接開いたのに「前のページに戻る」が出ています'
        await pg.goto(base + 'index.html'); await pg.wait_for_timeout(500)
        await pg.evaluate("location.href='TriTime.html'"); await pg.wait_for_timeout(1500)
        assert await pg.evaluate("getComputedStyle(document.getElementById('tsBackBar')).display") != 'none', '前の画面があるのに「前のページに戻る」が出ません'
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close(); srv.shutdown()

if __name__ == '__main__':
    sys.exit(run(test))
