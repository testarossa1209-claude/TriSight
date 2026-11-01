# -*- coding: utf-8 -*-
"""関所の動かす試験の共通部品（2026-11-02 なぎさ作成）
画面を試し用のブラウザで開く。認証コードの入口は、中継への問い合わせを試験の側で「認証済み」と答えて通す
（製品の画面は一切変えない）。画面の中で起きた誤り（pageerror）は errs に集める。
写し（screenshot）は SHOTS（環境変数）があればそこへ保存する。"""
import json, os, asyncio
from playwright.async_api import async_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SHOTS = os.environ.get('SHOTS', '')
IPAD = 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'

class Screen:
    async def open(self, p, name, ua=None, w=1100, h=900):
        self.b = await p.chromium.launch(channel='chrome', args=['--no-sandbox'])
        ctx = await self.b.new_context(viewport={'width': w, 'height': h}, **({'user_agent': ua} if ua else {}))
        self.pg = pg = await ctx.new_page()
        self.errs = []; pg.on('pageerror', lambda e: self.errs.append(str(e)))
        self.dialogs = []
        def on_dialog(d):
            self.dialogs.append(d.message); asyncio.ensure_future(d.dismiss())
        pg.on('dialog', on_dialog)
        async def gate(route):
            await route.fulfill(status=200, content_type='application/json',
                                body=json.dumps({'portal': True, 'ok': True, 'items': [], 'records': []}))
        await pg.route('**/api/gate', gate)
        await pg.add_init_script("localStorage.setItem('trisight_access_code','TEST');window.prompt=()=>'TEST';")
        await pg.goto('file://' + os.path.join(ROOT, name)); await pg.wait_for_timeout(800)
        if await pg.query_selector('#ogGo'):
            await pg.click('#ogGo'); await pg.wait_for_timeout(2500)
        return pg
    async def shot(self, sel, fname):
        if not SHOTS: return
        os.makedirs(SHOTS, exist_ok=True)
        el = await self.pg.query_selector(sel)
        if el:
            await el.scroll_into_view_if_needed(); await el.screenshot(path=os.path.join(SHOTS, fname))
    async def close(self):
        await self.b.close()

def run(test):
    """試験の本体（async def test(p)）を動かす。誤りがあれば終了コード1"""
    async def main():
        async with async_playwright() as p:
            await test(p)
    try:
        asyncio.run(main()); print('OK'); return 0
    except AssertionError as e:
        print('NG：' + str(e)); return 1
