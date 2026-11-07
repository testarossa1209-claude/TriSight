# -*- coding: utf-8 -*-
"""トライタイムの「時間の希望は必ず」「空いている曜日と時間帯」「同じ升の中の入れ替え」「地図の矢印」の試験（2026-11-07・宏史さんの指示）
・利用者登録で、希望時刻・希望の時間帯・「何時でも可」のどれも無いと登録できない。「何時でも可」に印を付ければ登録できる
・「空いている曜日と時間帯を見る」を押すと、曜日 × 午前・午後 の空きの表が出る
・本スケジュール表の同じ升の中で札の順番を入れ替えると、札の時刻が、動かした位置の時刻に変わる
・地図の線に、回る向きの矢印が付く（地図の部品が読み込めたときだけ確かめる）"""
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
        await pg.evaluate("""(function(){ var t = Date.now(), st = JSON.parse(localStorage.getItem('tritime_staff')), dow = String(new Date().getDay());
          var a = st.filter(function(s){ return s.name === '常勤 一子'; })[0].id;
          st.forEach(function(s){ s.off = []; s.holOff = false; }); localStorage.setItem('tritime_staff', JSON.stringify(st));
          var se = JSON.parse(localStorage.getItem('tritime_settings') || '{}'); se.office = { lat:35.700, lng:139.400 }; localStorage.setItem('tritime_settings', JSON.stringify(se));
          localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9801', name:'試験 一', area:'東町', status:'利用中', lat:35.710, lng:139.410, anyTime:true, upd:t },
            { no:'2010-01-看-9802', name:'試験 二', area:'東町', status:'利用中', lat:35.720, lng:139.420, anyTime:true, upd:t } ]));
          localStorage.setItem('tritime_weekly', JSON.stringify([
            { id:'w1', dow:dow, time:'09:15', min:30, no:'2010-01-看-9801', staffId:a, withId:'', upd:t },
            { id:'w2', dow:dow, time:'10:15', min:30, no:'2010-01-看-9802', staffId:a, withId:'', upd:t } ]));
          var d = JSON.parse(localStorage.getItem('tritime_device') || '{}'); d.me = 'jimu-no-hito'; localStorage.setItem('tritime_device', JSON.stringify(d)); })()""")

        # ① 時間の希望が無いと登録できない
        await pg.evaluate("document.querySelector('#tabs button[data-tab=pt]').click()"); await pg.wait_for_timeout(400)
        await pg.fill('#pt_no', 'T-0801'); await pg.fill('#pt_name', '試験 三'); await pg.fill('#pt_area', '東町')
        n0 = len(s.dialogs)
        await pg.click('#pt_add'); await pg.wait_for_timeout(500)
        saved = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_patients')).some(function(p){ return p.no === 'T-0801'; })")
        assert not saved and len(s.dialogs) > n0 and '何時でも可' in s.dialogs[-1], '時間の希望が無くても登録できてしまいます：' + str(s.dialogs[n0:])
        await pg.evaluate("document.getElementById('pt_anyTime').checked = true"); await pg.click('#pt_add'); await pg.wait_for_timeout(500)
        p3 = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_patients')).filter(function(p){ return p.no === 'T-0801'; })[0] || null")
        assert p3 and p3.get('anyTime') is True, '「何時でも可」に印を付けても登録できません：' + str(p3)

        # ② 空いている曜日と時間帯
        await pg.evaluate("document.getElementById('pt_avBtn').click()"); await pg.wait_for_timeout(300)
        box = await pg.inner_text('#pt_avBox')
        assert '午前' in box and '午後' in box and ('入れます' in box or '少し空き' in box), '空いている曜日と時間帯の表が出ません：' + box[:300]

        # ④ 同じ升の中の入れ替え（試験 一 を 試験 二 の後ろへ）
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(800)
        await pg.evaluate("document.getElementById('td_staff').value = '*'; document.getElementById('td_staff').dispatchEvent(new Event('change', {bubbles:true}))"); await pg.wait_for_timeout(600)
        r = await pg.evaluate("""(function(){ var cs = [].slice.call(document.querySelectorAll('#td_week .ssChip.dg'));
          var c1 = cs.filter(function(c){ return c.textContent.indexOf('試験 一') >= 0; })[0], c2 = cs.filter(function(c){ return c.textContent.indexOf('試験 二') >= 0; })[0];
          if(!c1 || !c2) return 'no chip:' + cs.length;
          c1.scrollIntoView({ block:'center' });
          var r1 = c1.getBoundingClientRect(), r2 = c2.getBoundingClientRect(), y = r2.bottom - 2;
          c1.dispatchEvent(new PointerEvent('pointerdown', { clientX:r1.x + 5, clientY:r1.y + 5, bubbles:true, pointerId:1 }));
          document.dispatchEvent(new PointerEvent('pointermove', { clientX:r1.x + 5, clientY:r1.y + 30, bubbles:true, pointerId:1 }));
          document.dispatchEvent(new PointerEvent('pointermove', { clientX:r2.x + 5, clientY:y, bubbles:true, pointerId:1 }));
          document.dispatchEvent(new PointerEvent('pointerup', { clientX:r2.x + 5, clientY:y, bubbles:true, pointerId:1 }));
          return document.getElementById('ssMv') ? 'ok' : 'no dialog'; })()""")
        assert r == 'ok', '同じ升の中で動かしても、入れ替えの確かめが出ません：' + r
        dlg = await pg.inner_text('#ssMv')
        assert '09:15 → 10:15' in dlg and '10:15 → 09:15' in dlg, '入れ替えの確かめに、新しい時刻が出ません：' + dlg[:300]
        await s.shot('#ssMv .card', 'TriTime_irekae.png')
        await pg.click('#mv_once'); await pg.wait_for_timeout(600)
        mv = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_events')).filter(function(e){ return e.type === 'move'; }).map(function(e){ return e.patientNo + ' ' + e.fromTime + '>' + e.toTime; }).sort()")
        assert mv == ['2010-01-看-9801 09:15>10:15', '2010-01-看-9802 10:15>09:15'], '入れ替えたあと、時刻が動かした位置の時刻になりません：' + str(mv)
        await pg.evaluate("var b = document.getElementById('ssMv'); if(b) b.remove();")
        wk = await pg.inner_text('#td_week')
        i1, i2 = wk.find('試験 一'), wk.find('試験 二')
        assert 0 <= i2 < i1, '入れ替えたあと、本スケジュール表の札の並びが変わりません：' + wk[:300]

        # 地図の矢印（地図の部品が読み込めたときだけ）
        await pg.wait_for_timeout(3000)
        has = await pg.evaluate("typeof L !== 'undefined'")
        if has:
            n = await pg.evaluate("document.querySelectorAll('#td_map .tdArrow').length")
            assert n >= 3, '地図の線に、回る向きの矢印が付きません：' + str(n)
        else:
            print('（地図の部品が読み込めない所なので、矢印は確かめていません）')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
