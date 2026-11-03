# -*- coding: utf-8 -*-
"""トライタイムの部署ごとの表示の試験（2026-11-03・宏史さんの指示「一般職員が部門内で使うとき、他の部署の職員リストは基本的にいらない。全員のリストは押したときだけ」）
・「名簿・設定」の職員の表は、いま使っている部署の職員（兼務で入る人を含む）だけを出し、「全部署の職員を表示する」を押すと全員を出す
・休みの届けの職員の選択も同じ範囲
・対照表は、いま使っている部署の利用者だけを出し、ほかの部署は「○○の一覧」のボタンを押したときだけ出す"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

ADD = """async (p) => {
  const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', {bubbles:true})); };
  set('st_name', p.name); set('st_dept', p.dept); set('st_emp', p.emp); set('st_job', p.job);
  await new Promise(r => setTimeout(r, 100));
  if(p.sub){ const c = document.querySelector('#st_sub [data-stsub="' + p.sub + '"]'); if(c){ c.checked = true; c.dispatchEvent(new Event('change', {bubbles:true})); } }
  document.getElementById('st_add').click();
  await new Promise(r => setTimeout(r, 200));
}"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html')
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        for x in [{'name':'看護 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
                  {'name':'介護 二郎', 'dept':'訪問介護部', 'job':'介護福祉士', 'emp':'常勤'},
                  {'name':'兼務 三郎', 'dept':'訪問介護部', 'job':'介護福祉士', 'emp':'常勤', 'sub':'訪問看護部'}]:
            await pg.evaluate(ADD, x)
        t = await pg.inner_text('#stList')
        assert '看護 一子' in t and '兼務 三郎' in t and '介護 二郎' not in t, '職員の表に、ほかの部署の職員が出ています：' + t[:200]
        opts = await pg.evaluate("[].slice.call(document.querySelectorAll('#lv_staff option')).map(function(o){ return o.textContent; }).join('、')")
        assert '介護 二郎' not in opts and '看護 一子' in opts, '休みの届けの職員の選択に、ほかの部署の職員が出ています：' + opts
        await s.shot('#cardStaff', 'TriTime_bumon_staff.png')
        await pg.click('#st_allBtn'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#stList')
        assert '介護 二郎' in t, '「全部署の職員を表示する」を押しても、全員が出ません'
        assert '訪問看護部の職員だけにする' in await pg.inner_text('#st_allBtn'), 'ボタンの文字が戻す形に変わりません'
        await pg.click('#st_allBtn'); await pg.wait_for_timeout(300)
        assert '介護 二郎' not in await pg.inner_text('#stList'), '部署の職員だけに戻りません'

        await pg.evaluate("""(function(){ var t = Date.now(); localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9001', name:'看護 利用者', kana:'かんご', area:'東町', status:'利用中', upd:t },
            { no:'kaigo:2020-01-総合-0001', name:'介護 利用者', kana:'かいご', area:'西町', status:'利用中', upd:t } ])); })()""")
        await pg.evaluate("document.getElementById('kpTab').click()"); await pg.wait_for_timeout(400)
        kb = await pg.inner_text('#kpBody')
        assert '看護 利用者' in kb and '介護 利用者' not in kb, '対照表に、ほかの部署の利用者が出ています'
        await pg.click('#kpDepts [data-kpd="kaigo"]'); await pg.wait_for_timeout(300)
        kb = await pg.inner_text('#kpBody')
        assert '介護 利用者' in kb and '看護 利用者' not in kb, '「訪問介護部の一覧」を押しても、介護部の利用者が出ません'
        await s.shot('#kpPanel', 'TriTime_bumon_kp.png')
        await pg.evaluate("document.getElementById('kpClose').click()"); await pg.wait_for_timeout(200)
        await pg.evaluate("document.getElementById('kpTab').click()"); await pg.wait_for_timeout(300)
        assert '看護 利用者' in await pg.inner_text('#kpBody'), '対照表を開き直しても、いま使っている部署に戻りません'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
