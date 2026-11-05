# -*- coding: utf-8 -*-
"""トライタイムの「免許の無い職員の移動と遠方の利用者」（2026-11-06・宏史さんの指示）の試験
・職員登録に「車の運転免許あり」の印。印が無いと「移動の手段」（徒歩／自転車／バス電車）が出て保存される
・利用者登録に「遠方」の印が保存される
・自動の振り分け：遠方の利用者は免許のある看護師（二子）に当たる
・免許のある看護師が出られない週は、免許の無い看護師（一子）に当て、同行に運転手（免許のある看護補助者＝四子）が付く。「希望どおりに組めなかった人」に理由が出る
・画面の中で誤りが出ない"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

def seed(s2off):
    return """(function(){
  var up = Date.now();
  var ST = [ { id:'s1', name:'常勤 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['6','0'], drive:false, move:'自転車', upd:up },
    { id:'s2', name:'常勤 二子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:%s, drive:true, upd:up },
    { id:'s4', name:'補助 四子', emp:'常勤', job:'看護補助者', dept:'訪問看護部', off:['6','0'], drive:true, upd:up },
    { id:'s9', name:'卜部 五子', emp:'常勤', job:'事務局', dept:'経営企画事務職', off:['6','0'], upd:up } ];
  var P = [ { no:'2010-01-看-9001', name:'川越 太郎', area:'ひばりが丘', addr:'西東京市ひばりが丘1-1-1', status:'利用中', ins:'精神科訪問看護（医療）', freq:'週1回', far:true, upd:up },
    { no:'2010-01-看-9002', name:'試験 花子', area:'本町', status:'利用中', ins:'精神科訪問看護（医療）', freq:'週1回', upd:up } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P)); localStorage.setItem('tritime_weekly', '[]');
  localStorage.setItem('tritime_events', '[]'); localStorage.setItem('tritime_settings', JSON.stringify({ work:{ mv20:1, mvMin:10, mvMax:20 } }));
  localStorage.setItem('tritime_device', JSON.stringify({ me:'s9', share:true })); localStorage.setItem('tritime_dept', 'nurse');
})()""" % s2off

async def rowsOf(pg):
    await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(300)
    await pg.click('#au_make'); await pg.wait_for_timeout(1500)
    return await pg.evaluate("(function(){ var rows=[]; document.querySelectorAll('#au_out .ssChip').forEach(function(c){ rows.push(c.textContent); }); return rows; })()")

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate(seed("['6','0']")); await pg.reload(); await pg.wait_for_timeout(1500)
        await pg.evaluate("window.alert = function(m){ window.AL = String(m); };")
        # 職員登録の欄
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(300)
        assert await pg.evaluate("getComputedStyle(document.getElementById('st_moveBox')).display") != 'none', '免許の印が無いのに移動の手段が出ません'
        await pg.evaluate("document.getElementById('st_drive').checked = true; document.getElementById('st_drive').dispatchEvent(new Event('change'));")
        assert await pg.evaluate("getComputedStyle(document.getElementById('st_moveBox')).display") == 'none', '免許の印を付けても移動の手段が消えません'
        await pg.evaluate("document.getElementById('st_drive').checked = false; document.getElementById('st_drive').dispatchEvent(new Event('change'));")
        await pg.fill('#st_name', '非常勤 六子'); await pg.select_option('#st_emp', '非常勤'); await pg.select_option('#st_move', '徒歩・バス電車'); await pg.click('#st_add'); await pg.wait_for_timeout(500)
        st = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_staff')).filter(function(x){ return x.name==='非常勤 六子'; })[0]")
        assert st and st['drive'] is False and st['move'] == '徒歩・バス電車', '免許・移動の手段が保存されません：' + str(st)
        # 利用者登録の遠方の印
        await pg.evaluate("document.querySelector('#tabs button[data-tab=pt]').click()"); await pg.wait_for_timeout(300)
        await pg.fill('#pt_no', '2010-01-看-9002'); await pg.click('#pt_load'); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('pt_far').checked = true"); await pg.click('#pt_add'); await pg.wait_for_timeout(500)
        pt = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_patients')).filter(function(x){ return x.no==='2010-01-看-9002'; })[0]")
        assert pt['far'] is True, '遠方の印が保存されません'
        await pg.evaluate("var a=JSON.parse(localStorage.getItem('tritime_patients')); a.forEach(function(x){ if(x.no==='2010-01-看-9002') x.far=false; }); localStorage.setItem('tritime_patients', JSON.stringify(a));")
        await pg.reload(); await pg.wait_for_timeout(1200)
        # 振り分け①：遠方は免許のある二子へ
        rows = await rowsOf(pg)
        far = [r for r in rows if '9001' in r and '同行' not in r]
        assert far and all('二子' in r for r in [await pg.evaluate("(function(){ var o=null; document.querySelectorAll('#au_out tr').forEach(function(tr){ if(tr.textContent.indexOf('9001')>=0 && tr.textContent.indexOf('同行')<0) o=tr.querySelector('th.who').textContent; }); return o||''; })()")]), '遠方の利用者が免許のある人に当たりません：' + str(rows)
        await s.shot('#au_out', 'TriTime_idou_1.png')
        # 振り分け②：二子が出られない週 → 一子＋運転手（四子）
        await pg.evaluate(seed("['1','2','3','4','5','6','0']")); await pg.reload(); await pg.wait_for_timeout(1500)
        rows = await rowsOf(pg)
        who = await pg.evaluate("(function(){ var o=''; document.querySelectorAll('#au_out tr').forEach(function(tr){ if(tr.textContent.indexOf('9001')>=0 && tr.querySelector('th.who')) o += tr.querySelector('th.who').textContent + '|' + tr.textContent.replace(/\\s+/g,' ') + '\\n'; }); return o; })()")
        assert '一子' in who and '同行' in who and '四子' in who, '免許の無い人に運転手の同行が付きません：' + who[:300]
        judge = await pg.inner_text('#au_out')
        assert '遠方（運転手つきの2名体制）' in judge, '理由が出ません'
        await s.shot('#au_out', 'TriTime_idou_2.png')
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
