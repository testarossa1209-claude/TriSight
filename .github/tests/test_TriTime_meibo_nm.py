# -*- coding: utf-8 -*-
"""職員名簿の呼び名は折り返さない（2026-11-06・宏史さん「漢字5文字の人が2行になるのは見にくい」）
狭い画面幅でも、漢字5文字の呼び名の升が1行（高さが1行分）のまま。野木画面の人物情報表の氏名のボタンも折り返さない（white-space:nowrap が付いている）"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(){ var up = Date.now();
  var ST = [ { id:'s1', name:'野木宏史郎', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['6','0'], mgr:true, sub:['訪問介護部'], tel:'090-1234-5678', mail:'name@example.jp', upd:up },
    { id:'s2', name:'渋谷 花', emp:'常勤', job:'事務局', dept:'経営企画事務職', off:['6','0'], upd:up } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', '[]'); localStorage.setItem('tritime_weekly', '[]'); localStorage.setItem('tritime_events', '[]');
  localStorage.setItem('tritime_settings', JSON.stringify({ work:{} })); localStorage.setItem('tritime_device', JSON.stringify({ me:'s2', share:true })); localStorage.setItem('tritime_dept', 'nurse');
})()"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=760, h=900)
    try:
        await pg.evaluate(SEED); await pg.reload(); await pg.wait_for_timeout(1500)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        r = await pg.evaluate("(function(){ var sp=[].filter.call(document.querySelectorAll('#stList td.stNm .stNmT'), function(x){ return x.textContent==='野木宏史郎'; })[0]; if(!sp) return null; var td=sp.parentNode, lh=parseFloat(getComputedStyle(td).lineHeight)||20; return { h: sp.getBoundingClientRect().height, lh: lh, ws: getComputedStyle(td).whiteSpace }; })()")
        assert r, '職員名簿に呼び名の升がありません'
        assert r['ws'] == 'nowrap' and r['h'] < r['lh'] * 1.5, '呼び名が2行になっています：' + str(r)
        # 野木画面の人物情報表（鍵の無い端末では画面は出ないため、作りの中の文字で確かめる）
        html = open(os.path.join(os.path.dirname(__file__), '..', '..', 'TriTime.html'), encoding='utf-8').read()
        assert 'data-ngp="\' + esc(s.id) + \'" style="padding:2px 10px;white-space:nowrap"' in html and '#tab-nogi td.ngNm{white-space:nowrap' in html, '野木画面の氏名のボタンが折り返す作りのままです'
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
