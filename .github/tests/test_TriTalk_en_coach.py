# -*- coding: utf-8 -*-
"""TriTalk.html のEnglish（2026-11-28・宏史さんの指示）。中継（返答・声）は試験の側で答える。
① Englishで英語を送ると、秘書の英語の下に和訳、自分の英語の下に「和訳」「通常はこのように言います」「ひとこと」が出る
② Englishで日本語を打ち込むと、あずさが英語の手本を出して声で言い、リピーティングを求める。次に話した英語の指導に手本が渡る
③ 画面の中で誤りが起きない"""
import sys, os, json, threading, http.server, socketserver, functools
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, ROOT

async def test(p):
    s = Screen(); calls = []; tts = []
    async def ai(route):
        b = json.loads(route.request.post_data or '{}'); calls.append(b); m = json.dumps(b, ensure_ascii=False)
        if '英会話の先生' in m and '言いたかったこと' in m:
            txt = '{"en":"I want to go to Kyoto."}'
        elif '英会話の先生' in m:
            txt = '{"ja":"私は京都に行きたいです","better":"I want to go to Kyoto.","note":"goの後にtoが要ります。","unclear":false}'
        elif '翻訳者' in m:
            txt = '{"ja":["それはいいですね"]}'
        else:
            txt = 'That sounds great.'
        body = {'content': [{'type': 'text', 'text': txt}]} if 'anthropic' in route.request.url else {'choices': [{'message': {'content': txt}}]}
        await route.fulfill(status=200, content_type='application/json', body=json.dumps(body, ensure_ascii=False))
    async def tt(route):
        tts.append(json.loads(route.request.post_data or '{}')); await route.fulfill(status=200, content_type='audio/mpeg', body=b'', headers={'x-tts-route': 'vertex'})
    pg = await s.open(p, 'TriTalk.html')
    await pg.route('**/api/openai*', ai); await pg.route('**/api/anthropic*', ai); await pg.route('**/api/tts*', tt)
    H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); H.log_message = lambda *a, **k: None
    srv = socketserver.TCPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d/TriTalk.html' % srv.server_address[1]
    async def go(url):
        await pg.goto(url); await pg.wait_for_timeout(1200)
        if await pg.query_selector('#ogGo'):
            await pg.click('#ogGo'); await pg.wait_for_timeout(2000)
    try:
        await go(base + '?interp=on')
        assert await pg.is_visible('#langSw'), '「日本語｜English」が出ません'
        await pg.click('#langSw button[data-l="en"]'); await pg.wait_for_timeout(300)
        # ①
        await pg.fill('#txt', 'I want go Kyoto'); await pg.press('#txt', 'Enter'); await pg.wait_for_timeout(2500)
        t = await pg.inner_text('#log')
        assert 'That sounds great.' in t and 'それはいいですね' in t, '秘書の英語の和訳が出ません：' + t
        assert '私は京都に行きたいです' in t and '通常はこのように言います' in t and 'goの後にtoが要ります。' in t, '自分の英語の指導が出ません：' + t
        assert not any('京都' in x.get('text', '') or 'いいですね' in x.get('text', '') for x in tts), '和訳を声にしています'
        # ②
        await pg.fill('#txt', '京都に行きたい'); await pg.press('#txt', 'Enter'); await pg.wait_for_timeout(2000)
        t = await pg.inner_text('#log')
        assert 'I want to go to Kyoto.' in t and 'リピーティング' in t, 'リピーティングの手本が出ません：' + t
        assert tts and 'Kyoto' in tts[-1].get('text', ''), '手本の英語を声で言っていません'
        await pg.evaluate("TriTalk._handle('I want to go to Kyoto')"); await pg.wait_for_timeout(2500)
        coach = [c for c in calls if '英会話の先生' in json.dumps(c, ensure_ascii=False) and '話した英語' in json.dumps(c, ensure_ascii=False)]
        assert '手本（言ってほしかった英語）：I want to go to Kyoto.' in json.dumps(coach[-1], ensure_ascii=False), 'リピーティングの指導に手本が渡っていません'
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        srv.shutdown(); await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
