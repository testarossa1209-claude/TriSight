# -*- coding: utf-8 -*-
"""TriTalk.html の同時通訳の引き出し（2026-11-27・宏史さんのトライサイトラップトップだけ）の動かす試験。中継（返答・声）は試験の側で答える。
① 最初は「同時通訳」のつまみが出ない。「同時通訳を使う」のチェックを入れると出て、開き直しても覚えている（2026-11-28改め）
② 通訳：日本語を送ると、あずさの英語が出て、英語向けの話し方で声の窓口を呼ぶ。和訳はボタンを押さなくても自動で出て、声にはしない（2026-11-28・宏史さんの指示で改め）
③ リピーティング：聞き取った英語を渡すと、点数・良かった点・直す点が出る
④ 英語で会話（最初から選ばれている）：前の会話が履歴として渡る。意見のある秘書だけが英語で意見を足す（PASSの秘書は出ない）
⑧ 🧹 Clear で、この画面のやり取りが消える（2026-11-27・宏史さんの指示で②④⑧を改め・追加）
⑥ 通訳・英語で会話のどちらでも、トライサイトの基礎知識と利用解説書の抜き出しがあずさに渡る
⑦ 画面が知識を添えずに聞いても、なぎさ・つかさ・あずさの誰にでも共通部品（TriSecretaries.ask）が知識を添える。二重には添えない
⑤ 画面の中で誤りが起きない"""
import sys, os, json, threading, http.server, socketserver, functools
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, ROOT

async def test(p):
    s = Screen(); calls = []; tts = []
    async def ai(route):
        b = json.loads(route.request.post_data or '{}'); calls.append(b)
        sysm = json.dumps(b, ensure_ascii=False)
        if '翻訳者' in sysm:
            txt = '{"ja":["今日は天気がいいですね","今日は天気が良いです。"]}'
        elif 'リピーティングの先生' in sysm:
            txt = '{"score":80,"good":"The flow matches the model.","points":["Check how you say weather."]}'
        elif '会話に加わっています' in sysm:
            txt = 'PASS' if 'Tsukasa thinks' in sysm else 'Nagisa thinks you should take a walk.'
        elif '英語で会話' in sysm:
            txt = '{"en":"I am fine, thank you.","help":""}'
        else:
            txt = '{"en":"The weather is nice today.","help":""}'
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
        assert not await pg.is_checked('#itUse'), '「同時通訳を使う」が最初から入っています'
        await pg.check('#itUse'); await pg.wait_for_timeout(300)
        assert await pg.is_visible('#gkTabInt'), 'チェックを入れても「同時通訳」のつまみが出ません'
        await go(base)
        assert await pg.is_visible('#gkTabInt') and await pg.is_checked('#itUse'), '開き直すとチェック・つまみが消えます'
        await pg.click('#gkTabInt'); await pg.wait_for_timeout(400)
        assert 'on' in (await pg.get_attribute('#itMode button[data-m="cv"]', 'class') or ''), '最初から「Conversation」が選ばれていません'
        # ②
        await pg.click('#itMode button[data-m="tr"]')
        await pg.fill('#itTxt', '今日は天気がいいですね'); await pg.press('#itTxt', 'Enter'); await pg.wait_for_timeout(1500)
        t = await pg.inner_text('#itList')
        assert 'The weather is nice today.' in t and '今日は天気がいいですね' in t, '通訳の結果が出ません：' + t
        assert any('通訳です' in json.dumps(c, ensure_ascii=False) for c in calls), '通訳の添え書きが渡っていません'
        assert tts and 'English' in tts[-1].get('instructions', '') and 'weather' in tts[-1].get('text', ''), '英語の声を英語向けの話し方で頼んでいません：' + str(tts[-1:])
        assert '今日は天気が良いです。' in t and any('翻訳者' in json.dumps(c, ensure_ascii=False) for c in calls), 'ボタンを押さなくても和訳が出る決まりなのに、和訳が出ません：' + t
        assert not any('天気が良い' in x.get('text', '') for x in tts), '和訳を声にしています：' + str(tts)
        # ③
        await pg.evaluate("TriTalk._iScore('The wether is nice today.')"); await pg.wait_for_timeout(1000)
        t = await pg.inner_text('#itList')
        assert '80 / 100' in t and 'Check how you say weather.' in t and 'The flow matches the model.' in t, '採点が出ません：' + t
        assert 'The weather is nice today.' in json.dumps(calls[-1], ensure_ascii=False), '採点に手本が渡っていません'
        # ④
        await pg.click('#itMode button[data-m="cv"]')
        await pg.evaluate("TriTalk._iJa('元気ですか')"); await pg.wait_for_timeout(1000)
        await pg.evaluate("TriTalk._iJa('それはよかった')"); await pg.wait_for_timeout(1000)
        az = [c for c in calls if '英語で会話しています' in json.dumps(c, ensure_ascii=False)]
        msgs = az[-1]['messages']
        assert any('元気ですか' in m.get('content', '') for m in msgs), '英語で会話の前の話が渡っていません'
        t = await pg.inner_text('#itList')
        assert 'I am fine, thank you.' in t, '英語で会話の答えが出ません'
        assert 'Nagisa thinks you should take a walk.' in t and 'Tsukasa' not in t, '意見のある秘書だけが出ていません：' + t
        # ⑥
        await pg.evaluate("TriTalk._iJa('トライゲイトでは何ができますか')"); await pg.wait_for_timeout(1500)
        body = json.dumps([c for c in calls if '英語で会話しています' in json.dumps(c, ensure_ascii=False)][-1], ensure_ascii=False)
        assert 'トライサイトの基礎知識' in body and '【システムの紹介】トライゲイト' in body, '英語で会話にトライサイトの知識が渡っていません'
        await pg.click('#itMode button[data-m="tr"]')
        await pg.evaluate("TriTalk._iJa('トライゲイトで補助金を探します')"); await pg.wait_for_timeout(1500)
        body = json.dumps([c for c in calls if '通訳です' in json.dumps(c, ensure_ascii=False)][-1], ensure_ascii=False)   # 自動の和訳の呼び出しは除く
        assert '通訳です' in body and 'トライサイトの基礎知識' in body, '通訳にトライサイトの知識が渡っていません'
        # ⑦
        for who in ('nagisa', 'tsukasa', 'azusa'):
            await pg.evaluate("TriSecretaries.ask('%s', [{role:'user', content:'トライゲイトでは何ができますか'}], {})" % who); await pg.wait_for_timeout(300)
            body = json.dumps(calls[-1], ensure_ascii=False)
            assert 'トライサイトの基礎知識' in body and '【システムの紹介】トライゲイト' in body, who + 'に知識が渡っていません'
            assert body.count('【トライサイトの基礎知識') == 1, who + 'に知識が二重に渡っています'
        await s.shot('#gk_int', 'TriTalk_tsuyaku.png')
        # ⑧
        await pg.evaluate("window.confirm = function(){ return true; }")   # 共通部品は確認窓を「いいえ」で閉じるため、ここでは「はい」にする
        await pg.click('#itClear'); await pg.wait_for_timeout(500)
        assert 'No exchanges yet' in await pg.inner_text('#itList'), '🧹 Clear でやり取りが消えません'
        # ⑤
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        srv.shutdown(); await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
