# -*- coding: utf-8 -*-
"""トライタイム 野木画面「システムの版」の試験（2026-11-27）
版の台帳（version.json）と変更の記録（GitHubのマージ済み申請）を試験の側で答え、
一覧表・「新」の印・変更の記録・システムでの絞り込みが出ることを確かめる（本物のGitHubへは出さない）。"""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html')
    today = datetime.date.today().strftime('%Y-%m-%d')
    ver = {'trisight': today + '-01', 'trigate': '2026-01-05-01', 'tritime': today + '-02', 'tritalk': '2026-01-01-01'}
    prs = [{'number': 301, 'title': 'トライタイム：野木画面にシステムの版', 'merged_at': '2026-11-27T01:00:00Z'},
           {'number': 300, 'title': 'トライゲイト：消えた補助金のアラート', 'merged_at': '2026-11-26T01:00:00Z'},
           {'number': 299, 'title': '閉じただけの申請', 'merged_at': None}]
    async def gh(route):
        await route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=json.dumps(prs))
    await pg.route('https://api.github.com/**', gh)
    await pg.evaluate("""(v)=>{ const of=window.fetch; window.fetch=function(u,o){ if(String(u).indexOf('version.json')===0) return Promise.resolve(new Response(JSON.stringify(v),{status:200})); return of.apply(this,arguments); }; }""", ver)
    try:
        await pg.evaluate("""()=>{ const d=document.createElement('div'); d.className='card'; d.innerHTML='<h2>システムの版と変更の記録</h2><div id="svBox"></div>'; document.body.appendChild(d); window.TT_SV.load(true); }""")
        await pg.wait_for_timeout(1200)
        txt = await pg.inner_text('#svBox')
        assert 'トライサイト本体' in txt and today + '-01' in txt, 'システムの版の一覧に、トライサイト本体の版が出ません'
        assert 'トライゲイト' in txt and '2026-01-05-01' in txt, 'システムの版の一覧に、トライゲイトの版が出ません'
        n_new = await pg.evaluate("[...document.querySelectorAll('#svBox table')[0].querySelectorAll('td span')].filter(x=>x.textContent==='新').length")
        assert n_new == 2, '直近3日以内の版にだけ「新」が付いていません（%d行）' % n_new
        assert '野木画面にシステムの版' in txt and '消えた補助金のアラート' in txt, '変更の記録にマージ済みの申請が出ません'
        assert '閉じただけの申請' not in txt, 'マージしていない申請まで変更の記録に出ています'
        await s.shot('#svBox', 'TriTime_sysver.png')
        await pg.select_option('#svFilter', 'trigate'); await pg.wait_for_timeout(300)
        txt2 = await pg.inner_text('#svBox')
        assert '消えた補助金のアラート' in txt2 and '野木画面にシステムの版' not in txt2, '「システムで絞る」でトライゲイトを選んでも絞り込まれません'
        assert await pg.evaluate("window.TT_SV.views.some(v=>v[0]==='sysver'&&v[1]==='システムの版')"), '野木画面のボタンに「システムの版」がありません'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
