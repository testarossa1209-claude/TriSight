# -*- coding: utf-8 -*-
"""トライタイムの職員の並びの試験（2026-11-02・宏史さんの決まり「常勤と非常勤、事務局の人間は下の方に」）
・名簿に入れた順がばらばらでも、部署の職員は 看護師の常勤 → 看護師の非常勤 → ほかの職種（常勤でも）→ 事務局 の順に並ぶ
・仮スケジュール表の行も同じ順に並ぶ
・基本情報シートの無い端末（iPad）でも、共有で届いた名簿の順（ord）で並ぶ"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, IPAD

ADD = """async (p) => {
  const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', {bubbles:true})); };
  set('st_name', p.name); set('st_dept', p.dept); set('st_emp', p.emp); if(p.job) set('st_job', p.job);
  await new Promise(r => setTimeout(r, 100));
  if(p.sub){ const c = document.querySelector('#st_sub [data-stsub="' + p.sub + '"]'); if(c){ c.checked = true; c.dispatchEvent(new Event('change', {bubbles:true})); } }
  document.getElementById('st_add').click();
  await new Promise(r => setTimeout(r, 200));
}"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', ua=IPAD)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        for x in [
            {'name':'事務 一郎', 'dept':'経営企画事務職', 'job':'事務局', 'emp':'常勤', 'sub':'訪問看護部'},
            {'name':'介護 六郎', 'dept':'訪問介護部', 'job':'介護福祉士', 'emp':'常勤', 'sub':'訪問看護部'},
            {'name':'非常勤 二子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'非常勤'},
            {'name':'常勤 三子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
            {'name':'非常勤 四子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'非常勤'},
            {'name':'常勤 五子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
        ]:
            await pg.evaluate(ADD, x)
        ROWS = "[].slice.call(document.querySelectorAll('#ssBody tbody th.who')).map(function(t){ return t.firstChild.textContent; })"
        async def ss_rows():
            await pg.evaluate("document.body.classList.remove('ssOpen')")
            await pg.evaluate("document.getElementById('ssTab').click()"); await pg.wait_for_timeout(500)
            return (await pg.evaluate(ROWS))[:6]
        want = ['常勤 三子', '常勤 五子', '非常勤 二子', '非常勤 四子', '介護 六郎', '事務 一郎']
        rows = await ss_rows()
        assert rows == want, '仮スケジュール表の行が 看護師の常勤→看護師の非常勤→ほかの職種→事務局 の順に並びません：' + '、'.join(rows)
        await s.shot('#ssBody', 'TriTime_staff_order.png')
        # 基本情報シートの無い端末：共有で届いた名簿の順（ord）で並ぶ（同じ組の中）
        n = await pg.evaluate("""(function(){
          var ord = {'常勤 五子':0, '常勤 三子':1, '非常勤 四子':2, '非常勤 二子':3, '介護 六郎':4, '事務 一郎':5}, n = 0;
          for(var i = 0; i < localStorage.length; i++){ var k = localStorage.key(i), v = localStorage.getItem(k);
            if(!v || v.indexOf('常勤 三子') < 0 || v.charAt(0) !== '[') continue;
            try{ var a = JSON.parse(v); a.forEach(function(x){ if(x && ord[x.name] != null){ x.ord = ord[x.name]; n++; } }); localStorage.setItem(k, JSON.stringify(a)); }catch(e){} }
          return n; })()""")
        assert n >= 6, '職員の記録が見つかりません'
        await pg.reload(); await pg.wait_for_timeout(1200)
        want2 = ['常勤 五子', '常勤 三子', '非常勤 四子', '非常勤 二子', '介護 六郎', '事務 一郎']
        rows2 = await ss_rows()
        assert rows2 == want2, '共有で届いた名簿の順で並びません：' + '、'.join(rows2)
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
