# -*- coding: utf-8 -*-
"""トライタイムの「目次」の引き出し（2026-11-06・宏史さんの指示「最初のページに両サイド引き出しを。下にスクロールすると出てくる項目へ、引き出しボタンを押せば飛ぶ」）の試験
端末＝一般の職員（常勤 一子）。
・右端と左端に「目次」のつまみが出る
・右の「目次」を開くと、いま開いている「予定」タブの見えている枠の見出し（1日の予定と地図／あなたの今月の稼働率／今週の訪問予定／連絡板…）がボタンで並ぶ。見えていない枠（週間予定を地区で寄せて組む）は並ばない
・押すと引き出しが閉じ、その枠まで画面が動く
・左の「目次」も同じ中身
・画面の中で誤りが出ない"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(t){
  var up = Date.now();
  var ST = [ { id:'s1', name:'常勤 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['4','0'], upd:up },
    { id:'s2', name:'常勤 二子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', mgr:true, off:['6','0'], upd:up } ];
  var P = [ { no:'2010-01-看-9001', name:'試験 太郎', area:'東町', status:'利用中', ins:'精神科訪問看護（医療）', freq:'週2回', upd:up } ];
  var W = [ { id:'w1', dow:'1', time:'09:30', min:30, no:'2010-01-看-9001', staffId:'s1', upd:up } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P)); localStorage.setItem('tritime_weekly', JSON.stringify(W));
  localStorage.setItem('tritime_events', '[]'); localStorage.setItem('tritime_settings', JSON.stringify({ work:{} }));
  localStorage.setItem('tritime_device', JSON.stringify({ me:'s1', share:true })); localStorage.setItem('tritime_dept', 'nurse');
})()"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1100, h=800)
    try:
        await pg.evaluate(SEED)
        await pg.reload(); await pg.wait_for_timeout(1500)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(500)
        for i in ['jmTab', 'jlTab']:
            assert await pg.evaluate("getComputedStyle(document.getElementById('%s')).display" % i) != 'none', i + ' が出ていません'
        await pg.evaluate("document.getElementById('jmTab').click()"); await pg.wait_for_timeout(400)
        assert await pg.evaluate("document.body.classList.contains('jmOpen')"), '右の目次が開きません'
        names = await pg.evaluate("[].map.call(document.querySelectorAll('#jmBody .jmGo'), function(b){ return b.textContent; })")
        for t in ['1日の予定と地図', 'あなたの今月の稼働率', '今週の訪問予定']:
            assert any(t in n for n in names), t + ' が目次にありません：' + str(names)
        assert not any('地区で寄せて組む' in n for n in names), '見えていない枠が目次に出ています：' + str(names)
        await s.shot('#jmPanel', 'TriTime_mokuji_1.png')
        y0 = await pg.evaluate("window.scrollY")
        idx = [i for i, n in enumerate(names) if '今週の訪問予定' in n][0]
        await pg.evaluate("document.querySelectorAll('#jmBody .jmGo')[%d].click()" % idx); await pg.wait_for_timeout(900)
        assert not await pg.evaluate("document.body.classList.contains('jmOpen')"), '押しても引き出しが閉じません'
        assert await pg.evaluate("window.scrollY") > y0, '押しても画面が動きません'
        await pg.evaluate("document.getElementById('jlTab').click()"); await pg.wait_for_timeout(400)
        names2 = await pg.evaluate("[].map.call(document.querySelectorAll('#jlBody .jmGo'), function(b){ return b.textContent; })")
        assert names2 == names, '左の目次の中身が右と違います'
        await s.shot('body', 'TriTime_mokuji_2.png')
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
