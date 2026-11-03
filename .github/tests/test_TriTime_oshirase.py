# -*- coding: utf-8 -*-
"""トライタイムの利用者さんへのお知らせの試験（2026-11-03・宏史さん「サービス当日に、本日は訪問看護のお伺い予定日です、と定型文を送る。とりあえずは一押し形式」）
・右端のつまみ「お知らせ」で、今日の訪問の利用者さんが時刻順に1人1行で出る（キャンセルの入った訪問は出ない）
・携帯番号のある人には「送る」が出て、押すと宛先と定型文（時刻入り）の入ったメッセージが開く。押すと「送った」になる
・携帯番号の無い人は「携帯番号なし」
・つまみに、今日まだ知らせていない人数が「残◯」と赤く出て、送ると消える（宏史さん「横の引き出しに一押し情報もつけてもらえれば忘れずに一押しできる」）"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

ADD = """async (p) => {
  const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', {bubbles:true})); };
  set('st_name', p.name); set('st_dept', p.dept); set('st_emp', p.emp); set('st_job', p.job);
  await new Promise(r => setTimeout(r, 100));
  document.getElementById('st_add').click();
  await new Promise(r => setTimeout(r, 200));
}"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        await pg.evaluate(ADD, {'name':'看護 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'非常勤'})
        await pg.evaluate("""(function(){ var t = Date.now(), st = JSON.parse(localStorage.getItem('tritime_staff')), dow = String(new Date().getDay()), a = st[0].id;
          var d = new Date(), p2 = function(n){ return (n < 10 ? '0' : '') + n; }, dt = d.getFullYear() + '-' + p2(d.getMonth() + 1) + '-' + p2(d.getDate());
          localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9901', name:'試験 携帯', area:'東町', status:'利用中', telMobile:'090-1111-2222', upd:t },
            { no:'2010-01-看-9902', name:'試験 無し', area:'東町', status:'利用中', upd:t },
            { no:'2010-01-看-9903', name:'試験 休み', area:'東町', status:'利用中', telMobile:'090-3333-4444', upd:t } ]));
          localStorage.setItem('tritime_weekly', JSON.stringify([
            { id:'w1', dow:dow, time:'10:00', min:30, no:'2010-01-看-9901', staffId:a, withId:'', upd:t },
            { id:'w2', dow:dow, time:'09:15', min:30, no:'2010-01-看-9902', staffId:a, withId:'', upd:t },
            { id:'w3', dow:dow, time:'10:45', min:30, no:'2010-01-看-9903', staffId:a, withId:'', upd:t } ]));
          localStorage.setItem('tritime_events', JSON.stringify([{ id:'c1', type:'cancel', patientNo:'2010-01-看-9903', date:dt, time:'10:45', upd:t }])); })()""")
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(300)
        assert await pg.is_visible('#osTab'), '右端に「お知らせ」のつまみが出ません'
        bd = await pg.inner_text('#osTab')
        assert '残1' in bd, 'つまみに、今日まだ知らせていない人数（携帯のある1人）が出ません：' + bd
        await pg.click('#osTab'); await pg.wait_for_timeout(400)
        ob = await pg.inner_text('#osBody')
        assert '試験 携帯' in ob and '試験 無し' in ob and '試験 休み' not in ob, '今日の訪問の利用者さん（キャンセルを除く）が出ません：' + ob[:300]
        assert ob.index('試験 無し') < ob.index('試験 携帯'), '時刻順に並びません'
        assert '携帯番号なし' in ob, '携帯番号の無い人に「携帯番号なし」が出ません'
        href = await pg.get_attribute('#osBody [data-ossend]', 'href')
        assert href.startswith('sms:09011112222') and '10%3A00' in href and '%E8%A8%AA%E5%95%8F%E7%9C%8B%E8%AD%B7' in href, '「送る」の宛先と文面（時刻入り）が正しくありません：' + href
        await pg.evaluate("document.querySelector('#osBody [data-ossend]').addEventListener('click', function(e){ e.preventDefault(); }, true)")
        await pg.click('#osBody [data-ossend]'); await pg.wait_for_timeout(700)
        ob2 = await pg.inner_text('#osBody')
        assert '送った' in ob2, '「送る」を押しても「送った」になりません'
        bd2 = await pg.evaluate("(document.querySelector('#osTab .osCnt') || {}).textContent || ''")
        assert '残' not in bd2, '送った後も、つまみの残りの人数が消えません：' + bd2
        await s.shot('#osPanel', 'TriTime_oshirase.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
