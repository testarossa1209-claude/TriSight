# -*- coding: utf-8 -*-
"""トライタイムの休日に出た日の付け替えの試験（2026-11-03・宏史さん「本日（祭日）は全部の利用者を島さんと佐野（夫）さんが回った。全部複数名。要確認の直し方は」）
・仮スケジュール表の下の「この日の訪問を、まとめて担当・同行に付け替える」で、その日の訪問が全部、選んだ担当と同行に替わる
・担当と同行の人は、公休の日でも「要調整」が消える（その日を出勤にする）。今日の付け替えは連絡の対象（赤）にしない
・「選んだ日の付け替えと出勤を取り消す」で元の予定に戻る"""
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
        for x in [{'name':'元担当 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
                  {'name':'島 試験', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
                  {'name':'佐野 試験', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'}]:
            await pg.evaluate(ADD, x)
        ids = await pg.evaluate("""(function(){ var dow = String(new Date().getDay()), st = JSON.parse(localStorage.getItem('tritime_staff'));
          /* 3人とも今日の曜日を公休にする（今日の訪問は全部「要調整」になる） */
          st.forEach(function(s){ s.off = [dow]; }); localStorage.setItem('tritime_staff', JSON.stringify(st));
          return ['元担当 一子','島 試験','佐野 試験'].map(function(n){ return st.filter(function(s){ return s.name === n; })[0].id; }); })()""")
        await pg.evaluate("""(a) => { var t = Date.now(), dow = String(new Date().getDay());
          localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9301', name:'試験 一', area:'東町', status:'利用中', upd:t },
            { no:'2010-01-看-9302', name:'試験 二', area:'東町', status:'利用中', upd:t } ]));
          localStorage.setItem('tritime_weekly', JSON.stringify([
            { id:'w1', dow:dow, time:'09:15', min:30, no:'2010-01-看-9301', staffId:a[0], withId:'', upd:t },
            { id:'w2', dow:dow, time:'10:45', min:30, no:'2010-01-看-9302', staffId:a[0], withId:'', upd:t } ]));
          localStorage.setItem('tritime_events', '[]'); }""", ids)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('ssTab').click()"); await pg.wait_for_timeout(600)
        tb = await pg.inner_text('#ssBody table')
        assert tb.count('要調整') >= 2, '試験の前提：公休の日の訪問に「要調整」が出ていません'
        await pg.click('#ssBulk summary'); await pg.wait_for_timeout(200)
        await pg.select_option('#sb_staff', ids[1]); await pg.select_option('#sb_with', ids[2])
        await pg.evaluate("window.confirm = function(){ return true; }")
        await pg.click('#sb_go'); await pg.wait_for_timeout(600)
        ss = await pg.inner_text('#ssBody'); tb = await pg.inner_text('#ssBody table')
        assert '要調整' not in tb, '付け替えた後も「要調整」が残っています'
        assert ss.count('2名・同行 佐野 試験') == 2, '付け替えた訪問の札に「2名・同行 佐野 試験」が出ません'
        assert ss.count('担当 島 試験') == 2, '同行の佐野さんの行に、同行の札（担当 島 試験）が出ません'
        assert 'この週の「出勤」' in ss and '島 試験' in ss, '出勤にした人が枠に出ません'
        await s.shot('#ssBody', 'TriTime_kyujitsu.png')
        # 付け替えた後に、週間予定の時刻・担当を組み直しても（今日の分の訪問の時刻が変わっても）、今日の付け替えは動かない
        await pg.evaluate("(function(){ var a = JSON.parse(localStorage.getItem('tritime_weekly')); a.forEach(function(v){ v.time = v.time === '09:15' ? '11:00' : '14:00'; v.upd = Date.now(); }); localStorage.setItem('tritime_weekly', JSON.stringify(a)); })()")
        await pg.evaluate("document.getElementById('ssThis').click()"); await pg.wait_for_timeout(600)
        ss3 = await pg.inner_text('#ssBody table')
        assert ss3.count('2名・同行 佐野 試験') == 2 and '要調整' not in ss3, '週間予定を組み直すと、今日の付け替えが外れます'
        # 予定タブの「今週の訪問予定」にも、付け替えた担当と同行が出る
        await pg.evaluate("document.body.classList.remove('ssOpen')")
        pb = await pg.inner_text('#planBody')
        assert pb.count('2名・同行 佐野 試験') >= 2, '予定タブの「今週の訪問予定」に、付け替えた同行が出ません'
        await pg.evaluate("document.getElementById('ssTab').click()"); await pg.wait_for_timeout(600)
        await pg.evaluate("var b = document.getElementById('ssBulk'); if(b && !b.open) b.open = true"); await pg.wait_for_timeout(200)
        await pg.click('#sb_undo'); await pg.wait_for_timeout(600)
        ss2 = await pg.inner_text('#ssBody table')
        assert ss2.count('要調整') >= 2 and '2名・同行 佐野 試験' not in ss2, '取り消しても元の予定に戻りません'
        ev = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_events')).filter(function(e){ return !e.del && (e.type === 'move' || e.type === 'work'); }).length")
        assert ev == 0, '取り消した後も、付け替えと出勤の記録が残っています：' + str(ev)
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
