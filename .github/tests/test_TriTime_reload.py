# -*- coding: utf-8 -*-
"""トライタイムの「最新の版に更新」ボタンの試験（2026-11-02）
・版の行に「最新の版に更新」ボタンがある
・押すと確かめの問いが出て、「いいえ」なら何も起きない
・「はい」なら、控えを使わない形（?v=）で開き直す
・version.json の版が画面より新しいとき、知らせの帯にも同じボタンが出る"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, IPAD

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', ua=IPAD)
    try:
        vl = await pg.inner_text('.verline')
        assert '最新の版に更新' in vl, '版の行に「最新の版に更新」ボタンがありません'
        if os.environ.get('SHOTS'): await s.shot('.verline', 'TriTime_reload_button.png')
        url0 = pg.url
        await pg.click('#verReload'); await pg.wait_for_timeout(500)
        assert any('最新の版に更新します' in d for d in s.dialogs), '押しても確かめの問いが出ません'
        assert pg.url == url0, '「いいえ」なのに開き直しています'
        await pg.evaluate("window.confirm = () => true")
        await pg.click('#verReload'); await pg.wait_for_timeout(1500)
        assert '?v=' in pg.url, '「はい」で開き直していません：' + pg.url
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()
    # 新しい版がある知らせの帯にも同じボタン
    s = Screen()
    async def newer(route):
        await route.fulfill(status=200, content_type='application/json', body=json.dumps({'tritime': '2099-01-01-01'}))
    pg = await s.open(p, 'TriTime.html', ua=IPAD)
    try:
        await pg.route('**/version.json*', newer)
        await pg.reload(); await pg.wait_for_timeout(1500)
        if await pg.query_selector('#ogGo'):
            await pg.click('#ogGo'); await pg.wait_for_timeout(2000)
        txt = await pg.inner_text('#verNotice')
        assert '新しい版が公開されています' in txt and await pg.query_selector('#verNoticeGo'), '新しい版の知らせの帯に更新ボタンが出ません：' + txt
    finally:
        await s.close()
    # 開いたあとに新しい版が出ても、画面に戻ったときに知らせが出る（2026-11-02：iPadが開き直さず古い版のまま残った件）
    s = Screen()
    pg = await s.open(p, 'TriTime.html', ua=IPAD)
    try:
        if await pg.query_selector('#ogGo'):
            await pg.click('#ogGo'); await pg.wait_for_timeout(1500)
        assert '新しい版が公開されています' not in await pg.inner_text('#verNotice'), '同じ版なのに知らせが出ています'
        await pg.route('**/version.json*', newer)
        await pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); await pg.wait_for_timeout(1500)
        txt = await pg.inner_text('#verNotice')
        assert '2099-01-01-01' in txt and await pg.query_selector('#verNoticeGo'), '開いたあとに出た新しい版を、画面に戻ったときに知らせていません：' + txt
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
