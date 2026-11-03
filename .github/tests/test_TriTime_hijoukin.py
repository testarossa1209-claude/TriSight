# -*- coding: utf-8 -*-
"""トライタイムの非常勤の勤め方・翌月の申告・仮スケジュール表で動かす試験（2026-11-03・宏史さんの指示）
・非常勤に「兼業先」「不定期」「待機」を入れられ、職員の表に印が出る
・待機の人は自動の振り分けに入らず、仮スケジュール表のいちばん下と待機者リストに出る
・翌月の申告：カレンダーで日を選んで保存すると、申告の無い日は仮スケジュール表で「申告外」の休みになる。メールの返信の○を読み込める
・仮スケジュール表の札を引っぱって別の人・別の日へ離すと、「この日だけ」なら組み換えの記録、「毎週」なら週間予定が書き換わり、移動の間と連絡が出る"""
import sys, os, datetime
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

ADD = """async (p) => {
  const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', {bubbles:true})); };
  set('st_name', p.name); set('st_dept', p.dept); set('st_emp', p.emp); set('st_job', p.job);
  await new Promise(r => setTimeout(r, 100));
  if(p.emp === '非常勤'){ document.getElementById('st_kengyo').value = p.kengyo || ''; document.getElementById('st_irreg').checked = !!p.irreg; document.getElementById('st_standby').checked = !!p.standby; }
  document.getElementById('st_add').click();
  await new Promise(r => setTimeout(r, 200));
}"""
WK = "JSON.parse(localStorage.getItem('tritime_weekly')).filter(function(v){ return !v.del; })"
EV = "JSON.parse(localStorage.getItem('tritime_events') || '[]').filter(function(v){ return !v.del; })"

async def drag(pg, src, dst):
    a = await pg.eval_on_selector(src, "e => { e.scrollIntoView({block:'center', inline:'center'}); const r = e.getBoundingClientRect(); return [r.x + r.width/2, r.y + r.height/2]; }")
    b = await pg.eval_on_selector(dst, "e => { const r = e.getBoundingClientRect(); return [r.x + r.width/2, r.y + r.height - 6]; }")
    await pg.mouse.move(a[0], a[1]); await pg.mouse.down()
    for i in range(1, 11):
        await pg.mouse.move(a[0] + (b[0] - a[0]) * i / 10, a[1] + (b[1] - a[1]) * i / 10); await pg.wait_for_timeout(20)
    await pg.mouse.up(); await pg.wait_for_timeout(300)

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1500, h=1000)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        assert not await pg.is_visible('#st_hjBox'), '常勤を選んでいるのに、非常勤の勤め方の欄が出ています'
        for x in [{'name':'常勤 一子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'常勤'},
                  {'name':'不定 二子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'非常勤', 'kengyo':'○○病院', 'irreg':True},
                  {'name':'待機 三子', 'dept':'訪問看護部', 'job':'看護師（正看）', 'emp':'非常勤', 'kengyo':'△△病院', 'standby':True}]:
            await pg.evaluate(ADD, x)
        txt = await pg.inner_text('#stList')
        assert '不定期' in txt and '待機' in txt and '兼業：○○病院' in txt, '職員の表に 不定期・待機・兼業先 が出ません'
        await s.shot('#cardStaff', 'TriTime_hj_staff.png')

        today = datetime.date.today(); mon = today + datetime.timedelta(days=(7 - today.weekday()))   # 来週の月曜
        tue = mon + datetime.timedelta(days=1)
        await pg.evaluate("""(function(){
          var st = JSON.parse(localStorage.getItem('tritime_staff')), sid = st.filter(function(s){ return s.name === '常勤 一子'; })[0].id, t = Date.now();
          localStorage.setItem('tritime_patients', JSON.stringify([
            { no:'2010-01-看-9001', name:'試験 一', area:'東町', status:'利用中', upd:t }, { no:'2010-01-看-9002', name:'試験 二', area:'東町', status:'利用中', upd:t } ]));
          localStorage.setItem('tritime_weekly', JSON.stringify([
            { id:'w1', dow:'1', time:'09:15', min:30, no:'2010-01-看-9001', staffId:sid, withId:'', upd:t },
            { id:'w2', dow:'1', time:'10:15', min:30, no:'2010-01-看-9002', staffId:sid, withId:'', upd:t } ])); })()""")

        # 翌月の申告（来週の月曜だけ出られる）
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(300)
        await pg.evaluate("(m) => { const e = document.getElementById('av_ym'); e.value = m; e.dispatchEvent(new Event('change')); }", mon.strftime('%Y-%m'))
        opts = await pg.evaluate("[].slice.call(document.querySelectorAll('#av_staff option')).map(function(o){ return o.textContent; })")
        assert any('不定 二子' in o for o in opts) and any('待機 三子' in o for o in opts) and not any('常勤 一子' in o for o in opts), '申告の職員の選択に、非常勤だけが並びません：' + '、'.join(opts)
        sid2 = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_staff')).filter(function(s){ return s.name === '不定 二子'; })[0].id")
        await pg.select_option('#av_staff', sid2); await pg.wait_for_timeout(200)
        await pg.click('#av_cal button[data-avd="%s"]' % mon.isoformat())
        await pg.click('#av_save'); await pg.wait_for_timeout(300)
        av = await pg.evaluate(EV + ".filter(function(e){ return e.type === 'avail'; })")
        assert len(av) == 1 and av[0]['days'] == [mon.isoformat()], '申告が保存されません：' + str(av)
        lst = await pg.inner_text('#av_list')
        assert '済み（1日）' in lst and 'まだ' in lst, '申告の状況の表が 済み／まだ を出しません'
        await pg.click('#av_list [data-avask]'); await pg.wait_for_timeout(200)
        # 返信の読み込み
        await pg.evaluate("document.getElementById('av_replyBox').open = true")
        m, d1, d2 = mon.month, mon.day, tue.day
        await pg.fill('#av_reply', '%d/%d(月)：○\n%d/%d(火)：\n' % (m, d1, m, d2))
        await pg.click('#av_parse'); await pg.wait_for_timeout(200)
        on = await pg.evaluate("[].slice.call(document.querySelectorAll('#av_cal button.on')).map(function(b){ return b.getAttribute('data-avd'); })")
        assert on == [mon.isoformat()], '返信の○を読み込めません：' + str(on)
        await s.shot('#cardAvail', 'TriTime_hj_avail.png')

        # 自動の振り分けに待機の人が入らない
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(300)
        await pg.click('#au_make'); await pg.wait_for_timeout(600)
        out = await pg.inner_text('#au_out')
        assert '待機 三子' not in out and '常勤 一子' in out, '自動の振り分けの表に待機の人が入っています'

        # 仮スケジュール表：来週を出す
        await pg.evaluate("document.getElementById('ssTab').click()"); await pg.wait_for_timeout(400)
        await pg.click('#ssNext'); await pg.wait_for_timeout(400)
        rows = await pg.evaluate("[].slice.call(document.querySelectorAll('#ssBody > table tbody th.who')).map(function(t){ return t.firstChild.textContent; })")
        assert rows[-1] == '待機 三子', '待機の人が表のいちばん下に来ません：' + '、'.join(rows)
        cell_tue = await pg.inner_text('#ssBody td[data-sid="%s"][data-date="%s"]' % (sid2, tue.isoformat()))
        cell_mon = await pg.inner_text('#ssBody td[data-sid="%s"][data-date="%s"]' % (sid2, mon.isoformat()))
        assert '申告外' in cell_tue and '申告外' not in cell_mon, '申告の無い日が「申告外」の休みになりません'
        sb = await pg.inner_text('#ssBody')
        assert '待機者リスト' in sb and '△△病院' in sb, '待機者リストが出ません'

        # この日だけ動かす：9002 を 月曜の 不定 二子 へ
        await drag(pg, '#ssBody .ssChip.dg[data-vk="%s|2010-01-看-9002|10:15"]' % mon.isoformat(), '#ssBody td[data-sid="%s"][data-date="%s"]' % (sid2, mon.isoformat()))
        assert await pg.is_visible('#ssMv'), '札を引っぱって離しても、動かす小窓が出ません'
        await pg.check('#mv_ok'); await pg.click('#mv_once'); await pg.wait_for_timeout(400)
        res = await pg.inner_text('#mv_res')
        assert '動かしました' in res and '移動の間を計算し直しました' in res and '連絡板に' in res, '動かした後の知らせが出ません：' + res
        await s.shot('#ssMv .card', 'TriTime_hj_move.png')
        mv = await pg.evaluate(EV + ".filter(function(e){ return e.type === 'move'; })")
        assert len(mv) == 1 and mv[0]['toStaff'] == sid2 and mv[0]['consent'] is True and 'toDate' not in mv[0], '組み換えの記録が違います：' + str(mv)
        await pg.click('#mv_close'); await pg.wait_for_timeout(300)
        cell_mon = await pg.inner_text('#ssBody td[data-sid="%s"][data-date="%s"]' % (sid2, mon.isoformat()))
        assert '9002' in cell_mon, '動かした札が、動かした先の升に出ません'

        # この日だけ・別の日へ：9001 を 火曜の 常勤 一子 へ
        sid1 = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_staff')).filter(function(s){ return s.name === '常勤 一子'; })[0].id")
        await drag(pg, '#ssBody .ssChip.dg[data-vk="%s|2010-01-看-9001|09:15"]' % mon.isoformat(), '#ssBody td[data-sid="%s"][data-date="%s"]' % (sid1, tue.isoformat()))
        await pg.click('#mv_once'); await pg.wait_for_timeout(300); await pg.click('#mv_close'); await pg.wait_for_timeout(300)
        c_mon = await pg.inner_text('#ssBody td[data-sid="%s"][data-date="%s"]' % (sid1, mon.isoformat()))
        c_tue = await pg.inner_text('#ssBody td[data-sid="%s"][data-date="%s"]' % (sid1, tue.isoformat()))
        assert '9001' not in c_mon and '9001' in c_tue, '別の日へ動かした札が、元の日から消えて先の日に出ません'
        await s.shot('#ssPanel', 'TriTime_hj_karisuke.png')

        # 毎週の予定を変える：火曜へ動かした 9001 を、水曜の 常勤 一子 へ（週間予定ごと）
        wed = mon + datetime.timedelta(days=2)
        await drag(pg, '#ssBody .ssChip.dg[data-vk="%s|2010-01-看-9001|09:15"]' % tue.isoformat(), '#ssBody td[data-sid="%s"][data-date="%s"]' % (sid1, wed.isoformat()))
        await pg.click('#mv_week'); await pg.wait_for_timeout(300); await pg.click('#mv_close'); await pg.wait_for_timeout(300)
        wk = await pg.evaluate(WK + ".filter(function(v){ return v.no === '2010-01-看-9001'; })")
        assert len(wk) == 1 and wk[0]['dow'] == '3', '毎週の予定が水曜に書き換わりません：' + str(wk)
        mv = await pg.evaluate(EV + ".filter(function(e){ return e.type === 'move' && e.patientNo === '2010-01-看-9001'; })")
        assert not mv, '毎週を変えたのに、前の組み換えの記録が残っています'
        notes = await pg.evaluate(EV + ".filter(function(e){ return e.type === 'note' && e.kind === '予定の組み換え'; }).length")
        assert notes == 3, '連絡板への知らせが3件になりません：' + str(notes)
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
