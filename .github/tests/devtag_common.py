# -*- coding: utf-8 -*-
"""端末の札（TriDevice.js）の試験の共通部（2026-11-12・未登録端末の見張り。改2で、止められたときの案内も確かめる）
中継あてで認証コードを付けた通信にだけ、札（x-trisight-device）が付くことを確かめる。
中継への問い合わせは試験の側で受けて答える（本物の中継へは出さない）。"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

def make(name):
    async def test(p):
        s = Screen(); pg = await s.open(p, name)
        seen = []
        async def catch(route):
            seen.append(dict(route.request.headers))
            await route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=json.dumps({'ok': True}))
        await pg.route('**/api/devtagtest', catch)
        try:
            dev = await pg.evaluate("window.TriDeviceId||''")
            assert re.match(r'^[a-z0-9]{16,40}$', dev), '端末の札が作られていません'
            await pg.evaluate("fetch('https://trisight-relay.vercel.app/api/devtagtest',{method:'POST',headers:{'Content-Type':'application/json','x-trisight-code':'TEST'},body:'{}'}).catch(function(){})")
            await pg.wait_for_timeout(500)
            await pg.evaluate("fetch('https://trisight-relay.vercel.app/api/devtagtest',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).catch(function(){})")
            await pg.wait_for_timeout(500)
            assert len(seen) == 2, '中継あての通信が届いていません（%d件）' % len(seen)
            assert seen[0].get('x-trisight-device') == dev, '認証コード付きの通信に札が付いていません'
            assert 'x-trisight-device' not in seen[1], '認証コードの無い通信にまで札が付いています'
            again = await pg.evaluate("localStorage.getItem('trisight_device_id')")
            assert again == dev, '札がこの端末に覚えられていません'
            # 2026-11-12 改2：未登録で止められたら、画面全体に案内が出る
            async def deny(route):
                await route.fulfill(status=403, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'},
                                    body=json.dumps({'error': 'この端末は登録されていません。', 'device': 'unregistered'}))
            await pg.route('**/api/devblocktest', deny)
            await pg.evaluate("fetch('https://trisight-relay.vercel.app/api/devblocktest',{method:'POST',headers:{'x-trisight-code':'TEST'},body:'{}'}).catch(function(){})")
            await pg.wait_for_timeout(800)
            txt = await pg.evaluate("(document.getElementById('triDeviceBlocked')||{}).innerText||''")
            assert 'この端末は登録されていません' in txt, '止められたのに、案内が出ていません'
        finally:
            await s.close()
    return test

def main(name):
    return run(make(name))
