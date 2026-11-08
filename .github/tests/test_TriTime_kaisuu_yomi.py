# -*- coding: utf-8 -*-
"""トライタイムの回数の読み取りの試験（2026-11-03・宏史さん「サービス提供回数を増やしても週間回数の数が変わらないのはなぜ」）
・取り決めの欄が「週二回」（漢数字）でも週2回で組む
・取り決めの欄が読めない人の枠は出さない（取り決めの欄には計画書の文が入っている人が多い。宏史さん「出来ない理由ばかり並んでいる」）
・患者さんごとの週の回数と、どこから取ったかが一覧で見られる"""
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
        await pg.evaluate(ADD, {'name':'常勤 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'})
        await pg.evaluate("""(function(){ var t = Date.now();
          localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9101', name:'試験 漢数字', area:'東町', status:'利用中', freq:'週二回・午前', upd:t },
            { no:'2010-01-看-9102', name:'試験 読めない', area:'東町', status:'利用中', freq:'2回', upd:t },
            { no:'2010-01-看-9103', name:'試験 月', area:'東町', status:'利用中', freq:'月12回', upd:t } ]));
          localStorage.setItem('tritime_weekly', '[]'); localStorage.removeItem('tritime_weekly_backup'); })()""")
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(400)
        await pg.evaluate("sideOpen('au', true)"); await pg.wait_for_timeout(300)   # 2026-11-08：自動の振り分けは右端の「自動組み」の引き出しの中
        await pg.wait_for_selector('#au_make', state='visible', timeout=15000)
        await pg.evaluate("sideOpen('au', true)"); await pg.wait_for_timeout(300)   # 2026-11-08：自動の振り分けは右端の「自動組み」の引き出しの中
        await pg.click('#au_make'); await pg.wait_for_timeout(800)
        out = await pg.inner_text('#au_out')
        assert '週 6回' in out, '「週二回」「2回（読めない→週1回）」「月12回（週3回）」で、合わせて週6回になりません：' + out[:200]
        assert '回数に使えなかった人' not in out, '取り決めの欄が読めなかった人の枠が、まだ出ています（宏史さん「出来ない理由ばかり並んでいる」）'
        await pg.click('#au_out summary:has-text("患者さんごとの週の回数")'); await pg.wait_for_timeout(200)
        out = await pg.inner_text('#au_out')
        assert '試験 漢数字：週2回（取り決め「週二回・午前」）' in out, '患者さんごとの回数と出どころが出ません'
        assert '試験 月：週3回（取り決め「月12回」）' in out, '「月12回」が週3回として読まれません'
        await s.shot('#cardAuto', 'TriTime_kaisuu_yomi.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
