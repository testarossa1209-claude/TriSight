# -*- coding: utf-8 -*-
"""出勤日の最初に押す「今日のスタート」（2026-11-06・宏史さんの指示）
①出勤日に端末を開くと窓が出て「出勤（事務所から）」「直行（利用者さんのお宅へ）」が並ぶ
②「出勤」を押すと events に type "start" の記録（日付・時刻・種別・遅刻の印）が入り、窓が消え、開き直しても出ない
③「あとで押す」を押すと窓は消えるが上に帯が残り、帯の「直行」で記録できる（直行は最初の訪問の時刻で遅刻を見る）
④公休の日は窓も帯も出ない
⑤野木画面の出勤状況の作りに「スタート（出勤時刻の厳守）」の列がある（鍵の無い端末では画面が出ないため、作りの中の文字で確かめる）"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(dow){ var up = Date.now();
  var ST = [ { id:'s1', name:'島 花子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:[String(dow)], upd:up } ];
  var PT = [ { no:'P1', name:'利用者 一', area:'柴崎町', upd:up } ];
  var WK = [ { id:'w1', no:'P1', dow:(new Date()).getDay(), time:'10:30', min:30, staffId:'s1', upd:up } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(PT)); localStorage.setItem('tritime_weekly', JSON.stringify(WK)); localStorage.setItem('tritime_events', '[]');
  localStorage.setItem('tritime_settings', JSON.stringify({ work:{ mv20:1, start:'09:00', end:'18:00' } })); localStorage.setItem('tritime_device', JSON.stringify({ me:'s1', share:false })); localStorage.setItem('tritime_dept', 'nurse');
  localStorage.removeItem('tritime_start_skip');
})(%d)"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=900, h=900)
    try:
        # ① 今日が出勤日（公休は今日と別の曜日）
        import datetime
        today_dow = (datetime.date.today().weekday() + 1) % 7
        await pg.evaluate(SEED % ((today_dow + 3) % 7)); await pg.reload(); await pg.wait_for_selector('#stStart', timeout=20000)
        r = await pg.evaluate("(function(){ var b=document.getElementById('stStart'); if(!b) return null; return { t:b.querySelector('h2').textContent, o:!!document.getElementById('stGoOffice'), d:!!document.getElementById('stGoDirect'), l:!!document.getElementById('stLater'), p:b.querySelector('p.muted').textContent }; })()")
        assert r and r['o'] and r['d'] and r['l'], '今日のスタートの窓が出ていません：' + str(r)
        assert '出勤時刻 09:00' in r['p'] and '最初の訪問 10:30' in r['p'], '窓の説明に出勤時刻と最初の訪問が無い：' + r['p']
        await s.shot('#stStart .box', 'TriTime_start_1.png')
        # ② 出勤を押す → 記録が入り、窓が消え、開き直しても出ない
        await pg.click('#stGoOffice'); await pg.wait_for_timeout(600)
        r = await pg.evaluate("(function(){ var ev=JSON.parse(localStorage.getItem('tritime_events')||'[]').filter(function(e){ return e.type==='start'; }); return { n:ev.length, e:ev[0]||null, win:!!document.getElementById('stStart'), bar:document.getElementById('stBar').style.display }; })()")
        assert r['n'] == 1 and r['e']['kind'] == 'office' and r['e']['staffId'] == 'st'.replace('st','s1') and r['e']['due'] == '09:00', '出勤の記録が入っていません：' + str(r)
        hm = r['e']['at']; mins = int(hm[:2]) * 60 + int(hm[3:5])
        assert r['e']['late'] == (mins > 9 * 60), '遅刻の判定が時刻と合いません：' + str(r['e'])
        assert not r['win'] and r['bar'] == 'none', '押したあとに窓か帯が残っています：' + str(r)
        await pg.reload(); await pg.wait_for_timeout(2500)
        assert not await pg.evaluate("!!document.getElementById('stStart')"), '押したあとに開き直すと窓がまた出ます'
        # ③ あとで押す → 帯が残る → 帯の「直行」で記録（最初の訪問 10:30 で遅刻を見る）
        await pg.evaluate("localStorage.setItem('tritime_events','[]'); localStorage.removeItem('tritime_start_skip')"); await pg.reload(); await pg.wait_for_selector('#stLater', timeout=20000)
        await pg.click('#stLater'); await pg.wait_for_timeout(400)
        r = await pg.evaluate("(function(){ return { win:!!document.getElementById('stStart'), bar:document.getElementById('stBar').style.display, txt:document.getElementById('stBar').textContent }; })()")
        assert not r['win'] and r['bar'] == '' and 'まだ押していません' in r['txt'], 'あとで押す のあとの帯が出ていません：' + str(r)
        await s.shot('#stBar', 'TriTime_start_2.png')
        await pg.reload(); await pg.wait_for_selector('#stBarDirect', timeout=20000)
        assert not await pg.evaluate("!!document.getElementById('stStart')") and await pg.evaluate("document.getElementById('stBar').style.display===''"), 'あとで押す の日に開き直すと窓がまた出る、または帯が消えています'
        await pg.click('#stBarDirect'); await pg.wait_for_timeout(600)
        r = await pg.evaluate("(function(){ var ev=JSON.parse(localStorage.getItem('tritime_events')||'[]').filter(function(e){ return e.type==='start'; }); return { n:ev.length, e:ev[0]||null, bar:document.getElementById('stBar').style.display }; })()")
        assert r['n'] == 1 and r['e']['kind'] == 'direct' and r['e']['due'] == '10:30' and r['bar'] == 'none', '帯の直行の記録が入っていません：' + str(r)
        # ④ 公休の日は窓も帯も出ない
        await pg.evaluate(SEED % today_dow); await pg.reload(); await pg.wait_for_timeout(2500)
        r = await pg.evaluate("(function(){ return { win:!!document.getElementById('stStart'), bar:document.getElementById('stBar').style.display }; })()")
        assert not r['win'] and r['bar'] == 'none', '公休の日に窓か帯が出ています：' + str(r)
        # ⑤ 野木画面の列
        html = open(os.path.join(os.path.dirname(__file__), '..', '..', 'TriTime.html'), encoding='utf-8').read()
        assert '<th>スタート（出勤時刻の厳守）</th>' in html and 'function stMonth(' in html, '野木画面の出勤状況にスタートの列がありません'
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
