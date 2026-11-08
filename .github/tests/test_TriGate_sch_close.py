# -*- coding: utf-8 -*-
"""トライゲイトの獲得スケジュールの引き出しを閉じられることの試験（2026-11-09・宏史さん「右上にいまの状況ボタンがでて獲得スケジュールを消せなくなりますよ」）
・「いまの状況」の枠が開いている広い画面で、引き出しを開いたとき、右上の「閉じる」の真上に他の物が乗っていない
・「閉じる」を押すと引き出しが閉じ、右端のつまみが戻る
トライゲイトは file:// で開くと本番へ飛ぶ作りのため、最初から手元の http で開く（入口の通し方は tt_helper.py と同じ）。"""
import sys, os, json, threading, http.server, socketserver, functools
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import run, ROOT, SHOTS

async def test(p):
    H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    H.log_message = lambda *a, **k: None
    srv = socketserver.TCPServer(('127.0.0.1', 0), H); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    b = await p.chromium.launch(channel='chrome', args=['--no-sandbox'])
    try:
        ctx = await b.new_context(viewport={'width': 1600, 'height': 900}, service_workers='block')  # 手元の http では sw.js が問い合わせを横取りし、試験の入口の通しが効かなくなるため止める
        pg = await ctx.new_page()
        async def gate(route):  # 手元の http から中継へは別の場所への問い合わせになるため、許可の印を付けて答える
            await route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS'}, body=json.dumps({'portal': True, 'ok': True, 'items': [], 'records': []}))
        await pg.route('**/api/gate', gate)
        # 入口は「この端末で確かめ済み」の印を置いて通す（製品の画面は変えない）
        await pg.add_init_script("localStorage.setItem('trisight_access_code','TEST');localStorage.setItem('trisight_open_trigate','1');localStorage.setItem('trisight_open_trigate_code','TEST');window.prompt=()=>'TEST';")
        await pg.goto('http://127.0.0.1:%d/TriGate.html' % port); await pg.wait_for_timeout(1500)
        if await pg.query_selector('#ogGo'):
            await pg.click('#ogGo'); await pg.wait_for_timeout(2500)
        assert await pg.evaluate("(function(){ var e = document.querySelector('#tsBoard .tsbBody'); return !!e && e.offsetHeight > 0; })()"), '広い画面なのに「いまの状況」の枠が開いていません（試験の前提が崩れています）'
        await pg.click('#tgSchTab', force=True); await pg.wait_for_timeout(500)
        top = await pg.evaluate("(function(){ var r = document.getElementById('tgSchClose').getBoundingClientRect(); var e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return e ? (e.id || String(e.className) || e.tagName) : ''; })()")
        assert top == 'tgSchClose', '引き出しの「閉じる」の上に別の物が乗っています：' + str(top)
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True); await pg.screenshot(path=os.path.join(SHOTS, 'TriGate_sch_close.png'))
        await pg.click('#tgSchClose'); await pg.wait_for_timeout(400)
        assert not await pg.evaluate("document.getElementById('tgSch').classList.contains('open')"), '「閉じる」を押しても引き出しが閉じません'
        assert await pg.is_visible('#tgSchTab'), '閉じた後に右端の「獲得スケジュール」のつまみが戻りません'
    finally:
        await b.close(); srv.shutdown()

if __name__ == '__main__':
    sys.exit(run(test))
