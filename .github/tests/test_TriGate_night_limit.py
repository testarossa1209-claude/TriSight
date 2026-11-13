# -*- coding: utf-8 -*-
"""自動発掘（TriGate.html?night=1）が、途中の待ちが返ってこなくても持ち時間で必ず「中止」になることの試験
（2026-11-13・10/24〜25に表題が「実行中」のまま5時間変わらず、毎時やり直されて止まらなかった件の再発防止）
・入口ページの読み取りが返ってこない状態を作り、持ち時間を3秒に縮めて開く
・持ち時間を過ぎると表題が「TriGate 自動発掘 中止」になり、帯に「持ち時間」の理由が出る"""
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
        ctx = await b.new_context(viewport={'width': 1600, 'height': 900}, service_workers='block')
        pg = await ctx.new_page()
        async def relay(route):
            await route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS'}, body=json.dumps({'portal': True, 'ok': True, 'items': [], 'records': []}))
        await pg.route('**/api/**', relay)
        comp = json.dumps({'会社名': '試験', '機械足切り条件': {'業種': 'タクシー'}}, ensure_ascii=False)
        # 入口は「この端末で確かめ済み」の印で通す。入口ページの読み取りは返ってこない形に差し替え、持ち時間は3秒にする
        await pg.add_init_script("""
          localStorage.setItem('trisight_access_code','TEST');localStorage.setItem('trisight_open_trigate','1');localStorage.setItem('trisight_open_trigate_code','TEST');
          localStorage.setItem('trisight_dig_company', %s);
          window.prompt=()=>'TEST'; window.__tsNightLimitMs = 3000;
          Object.defineProperty(window, 'tsNightReadEntries', { configurable: true, get: function(){ return function(){ return new Promise(function(){}); }; }, set: function(){} });
        """ % json.dumps(comp))
        await pg.goto('http://127.0.0.1:%d/TriGate.html?night=1' % port)
        # 地域が空だと持ち時間より前に止まるため、都道府県を選んでおく
        await pg.wait_for_function("document.getElementById('digPref') && document.getElementById('digPref').options.length > 1", timeout=15000)
        await pg.evaluate("(function(){ var s = document.getElementById('digPref'); for (var i = 0; i < s.options.length; i++) { if (s.options[i].value) { s.value = s.options[i].value; break; } } })()")
        await pg.wait_for_function("document.title === 'TriGate 自動発掘 実行中'", timeout=70000)
        await pg.wait_for_function("document.title === 'TriGate 自動発掘 中止'", timeout=15000)
        txt = await pg.evaluate("(document.getElementById('nightBanner') || {}).textContent || ''")
        assert '持ち時間' in txt, '帯に持ち時間の理由が出ていません：' + txt
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True); await pg.screenshot(path=os.path.join(SHOTS, 'TriGate_night_limit.png'))
    finally:
        await b.close(); srv.shutdown()

if __name__ == '__main__':
    sys.exit(run(test))
