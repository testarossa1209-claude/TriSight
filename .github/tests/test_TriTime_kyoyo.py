# -*- coding: utf-8 -*-
"""トライタイムの「共用端末」（2026-11-06・宏史さんの指示）の試験
出勤が週3日以下の非常勤が使いまわす会社のタブレット。主に使う人＝共用端末。
・開くと「今日この端末を使う人」の画面が出て、並ぶのは週3日以下の非常勤（三子）だけ（四子＝週5日、一子＝常勤は出ない）
・名前を押すと、その人の端末として動く：「1日の予定と地図」の職員の欄が本人だけ（「全員」が無い）、仮スケジュール表のつまみが出ない
・上の帯に「今日この端末を使う人：非常勤 三子さん」と「使う人を替える」が出る
・選んだ人は翌日には消える（日付が違う記録は使わない）
・画面の中で誤りが出ない"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(t){
  var up = Date.now();
  var ST = [
    { id:'s1', name:'常勤 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['4','0'], upd:up },
    { id:'s2', name:'常勤 二子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', mgr:true, off:['6','0'], upd:up },
    { id:'s3', name:'非常勤 三子', emp:'非常勤', job:'准看護師', dept:'訪問看護部', off:['1','3','5','6','0'], upd:up },
    { id:'s4', name:'補助 四子', emp:'非常勤', job:'看護補助者', dept:'訪問看護部', off:['6','0'], upd:up } ];
  var P = [ { no:'2010-01-看-9001', name:'試験 太郎', area:'東町', status:'利用中', ins:'精神科訪問看護（医療）', freq:'週2回', upd:up } ];
  var W = [ { id:'w1', dow:'2', time:'09:30', min:30, no:'2010-01-看-9001', staffId:'s3', upd:up } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P)); localStorage.setItem('tritime_weekly', JSON.stringify(W));
  localStorage.setItem('tritime_events', '[]'); localStorage.setItem('tritime_settings', JSON.stringify({ work:{} }));
  localStorage.setItem('tritime_device', JSON.stringify({ me:'__shared', share:true })); localStorage.setItem('tritime_dept', 'nurse');
  localStorage.removeItem('tritime_shared_user');
})()"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1100, h=900)
    try:
        await pg.evaluate(SEED)
        await pg.reload(); await pg.wait_for_timeout(1500)
        await pg.wait_for_selector('#shPick', timeout=15000)
        names = await pg.evaluate("[].map.call(document.querySelectorAll('#shPick .who'), function(b){ return b.textContent; })")
        assert len(names) == 1 and '非常勤 三子' in names[0], '選べる人が週3日以下の非常勤だけになっていません：' + str(names)
        await s.shot('#shPick .box', 'TriTime_kyoyo_1.png')
        await pg.evaluate("document.querySelector('#shPick .who').click()"); await pg.wait_for_timeout(800)
        assert not await pg.query_selector('#shPick'), '選んだあとも選ぶ画面が残っています'
        u = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_shared_user'))")
        assert u and u['id'] == 's3' and u.get('date'), '今日使う人の記録が残りません：' + str(u)
        bar = await pg.inner_text('#shBar')
        assert '非常勤 三子さん' in bar and '使う人を替える' in bar, '上の帯が違います：' + bar
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(500)
        opts = await pg.evaluate("[].map.call(document.querySelectorAll('#td_staff option'), function(o){ return o.value; })")
        assert '*' not in opts and 's1' not in opts and 's3' in opts, '職員の欄が本人だけになっていません：' + str(opts)
        assert await pg.evaluate("getComputedStyle(document.getElementById('ssTab')).display") == 'none', '仮スケジュール表のつまみが出ています'
        assert await pg.evaluate("getComputedStyle(document.querySelector('#tabs button[data-tab=admin]')).display") == 'none', '管理者の窓が出ています'
        await s.shot('body', 'TriTime_kyoyo_2.png')
        # 替える
        await pg.evaluate("document.getElementById('shChange').click()"); await pg.wait_for_timeout(300)
        assert await pg.query_selector('#shPick') and await pg.query_selector('#shPickClose'), '「使う人を替える」で選ぶ画面が出ません'
        await pg.evaluate("document.getElementById('shPickClose').click()"); await pg.wait_for_timeout(200)
        # 翌日：日付の違う記録は使わない
        await pg.evaluate("localStorage.setItem('tritime_shared_user', JSON.stringify({ id:'s3', date:'2000-01-01' }))")
        await pg.reload(); await pg.wait_for_timeout(1500)
        assert await pg.query_selector('#shPick'), '日付の違う記録なのに、選ぶ画面が出ません'
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
