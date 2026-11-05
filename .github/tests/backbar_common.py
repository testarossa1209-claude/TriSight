# -*- coding: utf-8 -*-
"""「前のページに戻る」のボタン（全画面共通）の試験の共通部（2026-11-06・宏史さんの指示「前の画面が無いときは出さない」）
file:// では前の画面（referrer）が付かないため、手元の http で開く。画面ごとの関所（入口の施錠など）に左右されないよう、
ボタンに直接付く style（display:none）で出る／出ないを見る。"""
import os, sys, threading, http.server, socketserver, functools, asyncio
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def make(name):
    async def test(p):
        H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
        H.log_message = lambda *a, **k: None
        srv = socketserver.TCPServer(('127.0.0.1', 0), H); port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        s = Screen(); pg = await s.open(p, name, w=1000, h=700)
        try:
            base = 'http://127.0.0.1:%d/' % port
            await pg.goto(base + name); await pg.wait_for_timeout(1000)
            assert await pg.evaluate("(document.getElementById('tsBackBar')||{style:{}}).style.display") == 'none', '直接開いたのに「前のページに戻る」が隠れていません'
            await pg.goto(base + 'index.html'); await pg.wait_for_timeout(400)
            await pg.evaluate("location.href=%r" % name); await pg.wait_for_timeout(1500)
            assert await pg.evaluate("(document.getElementById('tsBackBar')||{style:{display:'x'}}).style.display") == '', '前の画面があるのに「前のページに戻る」が隠れています'
        finally:
            await s.close(); srv.shutdown()
    return test

def main(name):
    return run(make(name))
