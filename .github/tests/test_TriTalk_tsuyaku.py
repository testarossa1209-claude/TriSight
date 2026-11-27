# -*- coding: utf-8 -*-
"""TriTalk.html の同時通訳の引き出し（2026-11-27・宏史さんのトライサイトラップトップだけ）の動かす試験。中継（返答・声）は試験の側で答える。
① 合図の無い端末では「同時通訳」のつまみが出ない。?interp=on で開くと出て、合図はアドレスから消える
② 通訳：日本語を送ると、あずさの英語と日本語訳が出て、英語向けの話し方で声の窓口を呼ぶ
③ リピーティング：聞き取った英語を渡すと、点数・良かった点・直す点が出る
④ 英語で会話：前の会話が履歴として渡る
⑥ 通訳・英語で会話のどちらでも、トライサイトの基礎知識と利用解説書の抜き出しがあずさに渡る
⑤ 画面の中で誤りが起きない"""
import sys, os, json, threading, http.server, socketserver, functools
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, ROOT

async def test(p):
    s = Screen(); calls = []; tts = []
    async def ai(route):
        b = json.loads(route.request.post_data or '{}'); calls.append(b)
        sysm = json.dumps(b, ensure_ascii=False)
        if 'リピーティングの先生' in sysm:
            txt = '{"score":80,"good":"文の流れは手本どおりです","points":["weather の発音を見直してください"]}'
        elif '英語で会話' in sysm:
            txt = '{"en":"I am fine, thank you.","ja":"元気です、ありがとう。"}'
        else:
            txt = '{"en":"The weather is nice today.","ja":"今日は天気が良いです。"}'
        if 'anthropic' in route.request.url:
            body = {'content': [{'type': 'text', 'text': txt}]}
        else:
            body = {'choices': [{'message': {'content': txt}}]}
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
        await go(base)
        await pg.evaluate("localStorage.removeItem('tritalk_interp');localStorage.removeItem('tritalk_interp_v1')")
        await go(base)
        # ①
        assert not await pg.is_visible('#gkTabInt'), '合図の無い端末に「同時通訳」のつまみが出ています'
        await go(base + '?interp=on')
        assert await pg.is_visible('#gkTabInt'), '?interp=on で開いても「同時通訳」のつまみが出ません'
        assert 'interp' not in pg.url, '合図がアドレスに残っています：' + pg.url
        await go(base)
        assert await pg.is_visible('#gkTabInt'), '合図を覚えた端末で、開き直すとつまみが消えます'
        await pg.click('#gkTabInt'); await pg.wait_for_timeout(400)
        # ②
        await pg.fill('#itTxt', '今日は天気がいいですね'); await pg.press('#itTxt', 'Enter'); await pg.wait_for_timeout(1500)
        t = await pg.inner_text('#itList')
        assert 'The weather is nice today.' in t and '今日は天気が良いです。' in t and '今日は天気がいいですね' in t, '通訳の結果が出ません：' + t
        assert '通訳です' in json.dumps(calls[-1], ensure_ascii=False), '通訳の添え書きが渡っていません'
        assert tts and 'English' in tts[-1].get('instructions', '') and 'weather' in tts[-1].get('text', ''), '英語の声を英語向けの話し方で頼んでいません：' + str(tts[-1:])
        # ③
        await pg.evaluate("TriTalk._iScore('The wether is nice today.')"); await pg.wait_for_timeout(1000)
        t = await pg.inner_text('#itList')
        assert '80点' in t and 'weather の発音を見直してください' in t and '文の流れは手本どおりです' in t, '採点が出ません：' + t
        assert 'The weather is nice today.' in json.dumps(calls[-1], ensure_ascii=False), '採点に手本が渡っていません'
        # ④
        await pg.click('#itMode button[data-m="cv"]')
        await pg.evaluate("TriTalk._iJa('元気ですか')"); await pg.wait_for_timeout(1000)
        await pg.evaluate("TriTalk._iJa('それはよかった')"); await pg.wait_for_timeout(1000)
        msgs = calls[-1]['messages']
        assert any('元気ですか' in m.get('content', '') for m in msgs), '英語で会話の前の話が渡っていません'
        assert 'I am fine, thank you.' in await pg.inner_text('#itList'), '英語で会話の答えが出ません'
        # ⑥
        await pg.evaluate("TriTalk._iJa('トライゲイトでは何ができますか')"); await pg.wait_for_timeout(1500)
        body = json.dumps(calls[-1], ensure_ascii=False)
        assert 'トライサイトの基礎知識' in body and '【システムの紹介】トライゲイト' in body, '英語で会話にトライサイトの知識が渡っていません'
        await pg.click('#itMode button[data-m="tr"]')
        await pg.evaluate("TriTalk._iJa('トライゲイトで補助金を探します')"); await pg.wait_for_timeout(1500)
        body = json.dumps(calls[-1], ensure_ascii=False)
        assert '通訳です' in body and 'トライサイトの基礎知識' in body, '通訳にトライサイトの知識が渡っていません'
        await s.shot('#gk_int', 'TriTalk_tsuyaku.png')
        # ⑤
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        srv.shutdown(); await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
