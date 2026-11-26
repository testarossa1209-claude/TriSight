# -*- coding: utf-8 -*-
"""TriTalk.html（トライトーク・2026-11-26）の動かす試験。中継（返答・声）は試験の側で答える。
① 一人を指名して文字で送ると、その秘書の名前付きで返答が出る
② 「みんな、〜」で あずさ→なぎさ→つかさ の順に3人が答え、後の人には前の人の発言が［名前の発言］付きの user で渡る
③ 声で答えるを外すと、声の窓口（/api/tts）を呼ばない
④ 会話がこの端末に残り、読み直しても続きが出る。新しい会話・過去の会話を開く
⑤ 名前・「みんな」の後に助詞が続く文は切り取らない
⑦ ほかの秘書も意見を出す：指名した秘書のあとに残りが続き、「パス」の秘書は出さない
⑧ 画面の中で誤りが起きない"""
import sys, os, json, threading, http.server, socketserver, functools
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, ROOT

async def test(p):
    s = Screen(); calls = []; tts = []; PASS_WHO = []
    async def ai(route):
        b = json.loads(route.request.post_data or '{}'); calls.append(b)
        sysm = b.get('system') or (b.get('messages') or [{}])[0].get('content', '')
        who = 'あずさ' if '「あずさ」' in sysm else ('なぎさ' if '「なぎさ」' in sysm else 'つかさ')
        txt = 'パス' if (who in PASS_WHO and 'はこのように考えます' in json.dumps(b, ensure_ascii=False)) else who + 'の答えです'
        if 'anthropic' in route.request.url:
            body = {'content': [{'type': 'text', 'text': txt}]}
        else:
            body = {'choices': [{'message': {'content': txt}}]}
        await route.fulfill(status=200, content_type='application/json', body=json.dumps(body, ensure_ascii=False))
    async def tt(route):
        tts.append(1); await route.fulfill(status=200, content_type='audio/mpeg', body=b'', headers={'x-tts-route': 'vertex'})
    pg = await s.open(p, 'TriTalk.html')
    await pg.route('**/api/openai*', ai); await pg.route('**/api/anthropic*', ai); await pg.route('**/api/tts*', tt)
    # 保存（localStorage）を確かめるため、file:// ではなく手元の http で開く
    H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); H.log_message = lambda *a, **k: None
    srv = socketserver.TCPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    await pg.goto('http://127.0.0.1:%d/TriTalk.html' % srv.server_address[1]); await pg.wait_for_timeout(1200)
    await pg.evaluate("localStorage.removeItem('tritalk_convs_v1')"); await pg.reload(); await pg.wait_for_timeout(1200)
    if await pg.query_selector('#ogGo'):
        await pg.click('#ogGo'); await pg.wait_for_timeout(2000)
    try:
        # ③ 声を切ってから試す（自動の意見は⑦で試すので、まず切る）
        await pg.uncheck('#voiceOn'); await pg.uncheck('#chimeOn')
        # ①
        await pg.click('#sec_tsukasa'); await pg.fill('#txt', 'この施策は通用しますか'); await pg.click('#send'); await pg.wait_for_timeout(800)
        t = await pg.inner_text('#log')
        assert 'つかさ（評価）' in t and 'つかさの答えです' in t, '指名した秘書の返答が出ません：' + t
        # ②
        await pg.fill('#txt', 'みんな、来年の目標を考えたい'); await pg.click('#send'); await pg.wait_for_timeout(1500)
        names = await pg.eval_on_selector_all('#log .ai b', 'els=>els.map(e=>e.textContent)')
        assert names[-3:] == ['あずさ（構想）', 'なぎさ（検証）', 'つかさ（評価）'], '「みんな」の順が違います：' + str(names)
        last = calls[-1]; msgs = last['messages']
        assert any(m['role'] == 'user' and m['content'].startswith('［なぎさ（検証）の発言］') for m in msgs), '後の人に前の人の発言が渡っていません'
        assert msgs[-1]['role'] == 'user', '最後の発言が user になっていません'
        assert 'みんな' in json.dumps(last, ensure_ascii=False), '「みんな」の添え書きが渡っていません'
        assert not tts, '声を切ったのに声の窓口を呼んでいます'
        # ④
        await pg.reload(); await pg.wait_for_timeout(2500)
        if await pg.query_selector('#ogGo'):
            await pg.click('#ogGo'); await pg.wait_for_timeout(2000)
        t = await pg.inner_text('#log')
        assert '来年の目標を考えたい' in t, '読み直すと会話が消えています：' + t[:200] + ' / ' + str(await pg.evaluate("localStorage.getItem('tritalk_convs_v1')"))[:300]
        await pg.click('#newConv'); await pg.wait_for_timeout(300)
        assert '話したい秘書を上から選んで' in await pg.inner_text('#log'), '新しい会話になりません'
        opts = await pg.eval_on_selector_all('#past option', 'els=>els.map(e=>e.value)')
        await pg.select_option('#past', opts[1]); await pg.wait_for_timeout(300)
        assert 'この施策は通用しますか' in await pg.inner_text('#log'), '過去の会話が開けません'
        # 声を戻すと声の窓口を呼ぶ
        await pg.check('#voiceOn'); await pg.click('#sec_azusa'); await pg.fill('#txt', 'あずさに聞きます'); await pg.click('#send'); await pg.wait_for_timeout(1000)
        assert tts, '声で答えるのに声の窓口を呼んでいません'
        assert 'あずさに聞きます' in await pg.inner_text('#log'), '名前の後に助詞が続く文が切り取られています'
        await pg.fill('#txt', 'みんなに聞きたい'); await pg.click('#send'); await pg.wait_for_timeout(1500)
        assert 'みんなに聞きたい' in await pg.inner_text('#log'), '「みんなに〜」が切り取られています'
        names = await pg.eval_on_selector_all('#log .ai b', 'els=>els.map(e=>e.textContent)')
        assert names[-3:] == ['あずさ（構想）', 'なぎさ（検証）', 'つかさ（評価）'], '「みんなに〜」で3人が答えていません'
        # ⑦ ほかの秘書も意見を出す：あずさを指名→あずさが答え、なぎさ・つかさが続く。「パス」の秘書は出さない
        PASS_WHO.append('つかさ')
        await pg.check('#chimeOn'); await pg.uncheck('#voiceOn')
        await pg.fill('#txt', 'ねえ、あずさ、新しい事業の案は？'); await pg.click('#send'); await pg.wait_for_timeout(1800)
        names = await pg.eval_on_selector_all('#log .ai b', 'els=>els.map(e=>e.textContent)')
        assert names[-2:] == ['あずさ（構想）', 'なぎさ（検証）'], '指名のあとに他の秘書の意見が続きません（パスの秘書が出ていないか）：' + str(names[-4:])
        assert '新しい事業の案は？' in await pg.inner_text('#log') and 'ねえ、あずさ' not in await pg.inner_text('#log'), '呼びかけ付きの指名が受けられていません'
        nag = [c for c in calls if '「なぎさ」' in json.dumps(c, ensure_ascii=False)][-1]
        assert 'なぎさはこのように考えます' in json.dumps(nag, ensure_ascii=False), '後の秘書に「別の意見を出す」添え書きが渡っていません'
        await s.shot('body', 'TriTalk.png')
        assert not s.errs, '画面の中で誤り：' + ' / '.join(s.errs)
    finally:
        await s.close(); srv.shutdown()

if __name__ == '__main__':
    sys.exit(run(test))
