# -*- coding: utf-8 -*-
"""トライタイムの「間違いの修正のお願い（事務局へ送る）」の試験（2026-11-15・宏史さんの指示）
・左端の「ご要望」のいちばん上に、どこの間違いか・何が違うか・修正案・「事務局へ送る」がある
・何が違うか／修正案が空なら送らない。入れて送ると一覧に「届いた」で出て、共有の記録（type fix）に残る
・事務局・全部署を見る端末では状態を「直した」に変えられ、まだ直していない件数がつまみの赤い丸に出る"""
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
FIXES = "() => JSON.parse(localStorage.getItem('tritime_events') || '[]').filter(e => e && e.type === 'fix')"

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1000, h=1000)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        await pg.evaluate(ADD, {'name':'試験 花子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'})
        await pg.click('#rqTab'); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#fxCard')
        for w in ['間違いの修正のお願い', 'どこの間違いか', '何が違うか', '修正案', '事務局へ送る']:
            assert w in t, '修正のお願いの窓に「' + w + '」がありません'
        # 空のままでは送らない
        await pg.click('#fx_send'); await pg.wait_for_timeout(300)
        assert len(await pg.evaluate(FIXES)) == 0, '何が違うかが空なのに送られました'
        assert s.dialogs and '何が違うか' in s.dialogs[-1], '空のときの知らせが出ません'
        await pg.select_option('#fx_by', label=await pg.evaluate("() => [...document.getElementById('fx_by').options].find(o => o.text.indexOf('試験 花子') === 0).text"))
        await pg.fill('#fx_target', '契約書番号12の方'); await pg.fill('#fx_wrong', '住所の番地が「3-5」になっている'); await pg.fill('#fx_fix', '正しくは「3-15」')
        await s.shot('#fxCard', 'TriTime_shusei_form.png')
        await pg.click('#fx_send'); await pg.wait_for_timeout(500)
        f = await pg.evaluate(FIXES)
        assert len(f) == 1 and f[0]['st'] == '届いた' and f[0]['fix'] == '正しくは「3-15」', '送った修正のお願いが記録に残りません：' + str(f)
        lst = await pg.inner_text('#fxList')
        assert '届いた' in lst and '住所の番地' in lst and '3-15' in lst, '一覧に送った内容が出ません：' + lst[:200]
        # この端末（共有前＝すべて見える）では状態を変えられ、赤い丸に件数が出る
        assert await pg.evaluate("() => (document.getElementById('fxDot') || {}).textContent") == '1', 'つまみに件数の赤い丸が出ません'
        await s.shot('#fxCard', 'TriTime_shusei_list.png')
        await pg.select_option('[data-fxst]', '直した'); await pg.wait_for_timeout(400)
        assert (await pg.evaluate(FIXES))[0]['st'] == '直した', '「直した」に変わりません'
        assert not await pg.query_selector('#fxDot'), '直したあとも赤い丸が残っています'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
