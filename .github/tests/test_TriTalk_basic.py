# -*- coding: utf-8 -*-
"""TriTalk.html（トライトーク・2026-11-26）の動かす試験。中継（返答・声）は試験の側で答える。
① 一人を指名して文字で送ると、その秘書の名前付きで返答が出る
② 「みんな、〜」で あずさ→なぎさ→つかさ の順に3人が答え、後の人には前の人の発言が［名前の発言］付きの user で渡る
③ 声で答えるを外すと、声の窓口（/api/tts）を呼ばない
④ 会話がこの端末に残り、読み直しても続きが出る。新しい会話・過去の会話を開く
⑤ 名前・「みんな」の後に助詞が続く文は切り取らない
⑦ ほかの秘書も意見を出す：指名した秘書のあとに残りが続き、「パス」の秘書は出さない
⑨ 基礎知識（トライロボの元データ）が渡り、会話は考える段階を飛ばす設定で呼ぶ
⑩ 学習資料を読ませる・貼り付ける・一覧に出る・外せる。問いに関係する部分が渡る
⑪ 画面の中で誤りが起きない"""
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
        await pg.uncheck('#chimeOn')
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
        # ④
        await pg.reload(); await pg.wait_for_timeout(2500)
        if await pg.query_selector('#ogGo'):
            await pg.click('#ogGo'); await pg.wait_for_timeout(2000)
        t = await pg.inner_text('#log')
        assert '来年の目標を考えたい' in t, '読み直すと会話が消えています：' + t[:200] + ' / ' + str(await pg.evaluate("localStorage.getItem('tritalk_convs_v1')"))[:300]
        await pg.click('#newConv'); await pg.wait_for_timeout(300)
        assert '話したい秘書を上から選んで' in await pg.inner_text('#log'), '新しい会話になりません'
        await pg.click('.gkTab[data-k="log"]'); await pg.wait_for_timeout(400)
        items = await pg.query_selector_all('#logList .logItem')
        assert len(items) >= 1, '会話の記録の引き出しに過去の会話が出ません'
        await items[0].click(); await pg.wait_for_timeout(300)
        assert 'この施策は通用しますか' in await pg.inner_text('#log'), '過去の会話が開けません'
        # 声を戻すと声の窓口を呼ぶ
        await pg.click('#sec_azusa'); await pg.fill('#txt', 'あずさに聞きます'); await pg.click('#send'); await pg.wait_for_timeout(1000)
        assert tts, '声で答えるのに声の窓口を呼んでいません'
        assert 'あずさに聞きます' in await pg.inner_text('#log'), '名前の後に助詞が続く文が切り取られています'
        await pg.fill('#txt', 'みんなに聞きたい'); await pg.click('#send'); await pg.wait_for_timeout(1500)
        assert 'みんなに聞きたい' in await pg.inner_text('#log'), '「みんなに〜」が切り取られています'
        names = await pg.eval_on_selector_all('#log .ai b', 'els=>els.map(e=>e.textContent)')
        assert names[-3:] == ['あずさ（構想）', 'なぎさ（検証）', 'つかさ（評価）'], '「みんなに〜」で3人が答えていません'
        # ⑦ ほかの秘書も意見を出す：あずさを指名→あずさが答え、なぎさ・つかさが続く。「パス」の秘書は出さない
        PASS_WHO.append('つかさ')
        await pg.check('#chimeOn')
        await pg.fill('#txt', 'ねえ、あずさ、新しい事業の案は？'); await pg.click('#send'); await pg.wait_for_timeout(1800)
        names = await pg.eval_on_selector_all('#log .ai b', 'els=>els.map(e=>e.textContent)')
        assert names[-2:] == ['あずさ（構想）', 'なぎさ（検証）'], '指名のあとに他の秘書の意見が続きません（パスの秘書が出ていないか）：' + str(names[-4:])
        assert '新しい事業の案は？' in await pg.inner_text('#log') and 'ねえ、あずさ' not in await pg.inner_text('#log'), '呼びかけ付きの指名が受けられていません'
        nag = [c for c in calls if '「なぎさ」' in json.dumps(c, ensure_ascii=False)][-1]
        assert 'なぎさはこのように考えます' in json.dumps(nag, ensure_ascii=False), '後の秘書に「別の意見を出す」添え書きが渡っていません'
        # ⑨ 基礎知識：トライゲイトのことを聞くと、基礎知識と利用解説書のトライゲイトの紹介が渡る。会話は考える段階を飛ばす設定で呼ぶ
        await pg.uncheck('#chimeOn'); await pg.click('#sec_tsukasa')
        await pg.fill('#txt', 'トライゲイトでは何ができますか'); await pg.click('#send'); await pg.wait_for_timeout(1500)
        body = json.dumps(calls[-1], ensure_ascii=False)
        assert 'トライサイトの基礎知識' in body, '基礎知識が渡っていません'
        assert '【システムの紹介】トライゲイト' in body, '利用解説書のトライゲイトの紹介が渡っていません'
        assert calls[-1].get('reasoning_effort') == 'none', '考える段階を飛ばす設定が渡っていません'
        # ⑩ 学習資料：引き出しを開いて、テキストの資料と貼り付けを覚えさせ、一覧に出る。問いに関係する部分が渡る
        await pg.click('.gkTab[data-k="win"]'); await pg.wait_for_timeout(400)
        assert await pg.evaluate("document.body.classList.contains('gk_winOpen')"), '学習窓の引き出しが開きません'
        open('/tmp/tt_doc.txt', 'w').write('当社の訪問看護の営業時間は午前8時30分から午後5時30分までです。緊急時は24時間対応します。' * 3)
        await pg.set_input_files('#gkFile', '/tmp/tt_doc.txt'); await pg.wait_for_timeout(800)
        await pg.fill('#gkTitle', '休日の決まり'); await pg.fill('#gkPaste', '年末年始の休みは12月30日から1月3日までです。祝日は通常どおり営業します。'); await pg.click('#gkPasteAdd'); await pg.wait_for_timeout(300)
        await pg.click('#gk_win .gkClose'); await pg.click('.gkTab[data-k="lst"]'); await pg.wait_for_timeout(400)
        lst = await pg.inner_text('#gkList')
        assert 'tt_doc' in lst and '休日の決まり' in lst, '学習科目の一覧に出ません：' + lst
        assert await pg.inner_text('#gkCount') == '2', '引き出しのつまみの数が合いません'
        await pg.click('#gk_lst .gkClose')
        await pg.fill('#txt', '年末年始の休みはいつですか'); await pg.click('#send'); await pg.wait_for_timeout(1200)
        body = json.dumps(calls[-1], ensure_ascii=False)
        assert '学習資料「休日の決まり」' in body and '12月30日' in body, '問いに関係する学習資料が渡っていません'
        # 外すと渡らない
        await pg.click('.gkTab[data-k="lst"]'); await pg.wait_for_timeout(300)
        await pg.evaluate("window.confirm=()=>true")
        await pg.click('button[data-del="0"]'); await pg.wait_for_timeout(300)
        assert '休日の決まり' not in await pg.inner_text('#gkList'), '外した科目が一覧に残っています'
        await pg.click('#gk_lst .gkClose')
        # ⑫ シリーズ質問：システムのボタンで選び、聞き取った質問が会話へ送られ、選んでいる秘書が基礎知識付きで声で答える（打ち込む欄は無い）
        await pg.click('.gkTab[data-k="qa"]'); await pg.wait_for_timeout(400)
        n0 = len(tts)
        assert not await pg.query_selector('#qaText'), 'シリーズ質問に打ち込む欄が残っています'
        await pg.click('#qaSys .qaSysB[data-s="トライタイム"]'); await pg.wait_for_timeout(200)
        assert 'トライタイム' in await pg.inner_text('#qaSt'), 'システムのボタンで選べません'
        await pg.evaluate("TriTalk._qaAsk('何ができますか')"); await pg.wait_for_timeout(1500)   # 声の聞き取りの代わりに、聞き取った文を渡す
        assert 'トライタイムについて：何ができますか' in await pg.inner_text('#log'), 'シリーズ質問が会話に入りません'
        assert len(tts) > n0, 'シリーズ質問の答えを声にしていません'
        assert '【システムの紹介】トライタイム' in json.dumps(calls[-1], ensure_ascii=False), 'シリーズ質問に利用解説書が渡っていません'
        await s.shot('body', 'TriTalk.png')
        assert not s.errs, '画面の中で誤り：' + ' / '.join(s.errs)
    finally:
        await s.close(); srv.shutdown()

if __name__ == '__main__':
    sys.exit(run(test))
