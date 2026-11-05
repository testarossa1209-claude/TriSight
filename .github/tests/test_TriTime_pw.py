# -*- coding: utf-8 -*-
"""トライタイムの「予定表の作り方を選ぶ（二択）」「ベースの自動投入」「管理者の窓の効率バージョンと比べる・パトリオット」「ご要望の枠」の試験（2026-11-05 昼・宏史さんの指示）
・本スケジュール表の上にオレンジの「予定表の作り方を選ぶ」が出る（予定を組む人の端末）
・押すと小窓に「このままAIの表で使う」「ベースに手を入れて完成させる」の二つのボタン（三択は無い）
・「ベースに手を入れて完成させる」→ いまの週間予定（11件）が手組みの表に写って開き、表の上に「担当者からのご要望（上申）」の枠（未対応の上申が出る・対応済みにできる）
・「このままAIの表で使う」→ 週間予定がAIの表に置き換わり、記録に src ai が付く
・週間予定が空の部署では、本スケジュール表を開くとAIのベースが自動で入り、知らせが出る
・管理者の窓：「効率バージョンと比べる」で日付ごと・職員ごとの表とアドバイス、「H&Nパトリオット（全体の評価）」で全体の評価が出る
・使い方に説明がある／画面の中で誤りが出ない"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(t){
  var up = Date.now();
  var ST = [
    { id:'s1', name:'常勤 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['4','0'], upd:up },
    { id:'s2', name:'常勤 二子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['6','0'], upd:up },
    { id:'s3', name:'非常勤 三子', emp:'非常勤', job:'准看護師', dept:'訪問看護部', off:['1','3','5','6','0'], upd:up },
    { id:'s4', name:'補助 四子', emp:'非常勤', job:'看護補助者', dept:'訪問看護部', off:['6','0'], upd:up } ];
  var P = [
    { no:'2010-01-看-9001', name:'試験 太郎', area:'東町', status:'利用中', ins:'精神科訪問看護（医療）', wDays:['1','3'], wish:'09:30', freq:'週2回', upd:up },
    { no:'2010-01-看-9002', name:'試験 花子', area:'東町', status:'利用中', ins:'精神科訪問看護（医療）', ngDays:['2'], freq:'週2回', upd:up },
    { no:'2010-01-看-9003', name:'試験 一郎', area:'西町', status:'利用中', ins:'精神科訪問看護（医療）', team:'2名', freq:'週3回', upd:up },
    { no:'2010-01-看-9004', name:'試験 次郎', area:'南町', status:'利用中', ins:'精神科訪問看護（医療）', wBand:'午前', freq:'週1回', upd:up },
    { no:'2010-01-看-9005', name:'試験 三郎', area:'北町', status:'利用中', ins:'精神科訪問看護（医療）', freq:'週2回', upd:up } ];
  var W = [
    { id:'w1', dow:'1', time:'09:30', min:30, no:'2010-01-看-9001', staffId:'s1', upd:up },
    { id:'w2', dow:'2', time:'10:00', min:30, no:'2010-01-看-9001', staffId:'s1', upd:up },
    { id:'w3', dow:'1', time:'10:40', min:30, no:'2010-01-看-9002', staffId:'s1', upd:up },
    { id:'w4', dow:'2', time:'11:30', min:30, no:'2010-01-看-9002', staffId:'s2', upd:up },
    { id:'w5', dow:'2', time:'09:00', min:30, no:'2010-01-看-9003', staffId:'s2', upd:up },
    { id:'w6', dow:'3', time:'09:00', min:30, no:'2010-01-看-9003', staffId:'s2', withId:'s4', upd:up },
    { id:'w7', dow:'5', time:'09:00', min:30, no:'2010-01-看-9003', staffId:'s2', withId:'s4', upd:up },
    { id:'w8', dow:'1', time:'14:00', min:30, no:'2010-01-看-9004', staffId:'s2', upd:up },
    { id:'w9', dow:'1', time:'11:00', min:30, no:'2010-01-看-9005', staffId:'s2', upd:up },
    { id:'w10', dow:'4', time:'09:00', min:30, no:'2010-01-看-9005', staffId:'s1', upd:up },
    { id:'w11', dow:'1', time:'11:40', min:30, no:'2010-01-看-9001', staffId:'s1', hv:true, why:'人情変更（相性）', note:'本人の希望', upd:up } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P)); localStorage.setItem('tritime_weekly', JSON.stringify(W));
  localStorage.setItem('tritime_events', '[]'); localStorage.setItem('tritime_settings', JSON.stringify({ work:{ mv20:1, mvMin:10, mvMax:20 } }));
  localStorage.setItem('tritime_device', JSON.stringify({ me:'s1', share:false })); localStorage.setItem('tritime_dept', 'nurse');
})()"""

async def tap(pg, sel):
    await pg.evaluate("document.querySelector(%s).click()" % repr(sel))

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1300, h=1000)
    try:
        await pg.evaluate(SEED)
        await pg.reload(); await pg.wait_for_timeout(1200)
        await pg.evaluate("window.confirm = function(){ return true; }")
        await tap(pg, '#tabs button[data-tab=plan]'); await pg.wait_for_timeout(300)
        await pg.wait_for_selector('#td_staff option[value="*"]', state='attached', timeout=15000)
        await pg.evaluate("var e = document.getElementById('td_staff'); e.value = '*'; e.dispatchEvent(new Event('change'));")
        await pg.wait_for_selector('#td_week .ssChip', state='attached', timeout=15000); await pg.wait_for_timeout(300)
        assert await pg.query_selector('#pw_open'), '「予定表の作り方を選ぶ」のボタンがありません'
        # 上申を1件入れておく（職員からのご要望の枠に出るか）
        await pg.evaluate("""(function(){ var ev = JSON.parse(localStorage.getItem('tritime_events') || '[]'); ev.push({ id:'js1', type:'note', kind:'上申', from:'s2', to:['s1'], title:'【上申】相性に問題がある　看-9001 試験 太郎（常勤 二子）', body:'試験の上申です', patientNo:'2010-01-看-9001', jsKind:'相性に問題がある', dept:'nurse', created:'2026-11-05T10:00' }); localStorage.setItem('tritime_events', JSON.stringify(ev)); })()""")
        await tap(pg, '#pw_open'); await pg.wait_for_timeout(300)
        for i in ['pw_ai', 'pw_mix']:
            assert await pg.query_selector('#ssMv #' + i), '小窓に ' + i + ' がありません'
        assert not await pg.query_selector('#ssMv #pw_hand'), '三択の「自分で作る」が残っています'
        txt = await pg.inner_text('#ssMv .card')
        for w in ['このままAIの表で使う', 'ベースに手を入れて完成させる', '11件']:
            assert w in txt, '小窓に「' + w + '」がありません'
        await s.shot('#ssMv .card', 'TriTime_pw_1.png')
        # ベースに手を入れる → 写る＋ご要望の枠
        await tap(pg, '#pw_mix'); await pg.wait_for_timeout(600)
        assert not await pg.query_selector('#ssMv'), '小窓が閉じません'
        assert await pg.evaluate("document.querySelectorAll('#hbBox .hbGrid .hbFuda').length") == 11, '「ベースに手を入れて完成させる」で週間予定（11件）が写りません'
        yb = await pg.inner_text('#hbBox details.mnCh')
        assert '担当者からのご要望' in yb and '未対応 1件' in yb and '試験の上申です' in yb and '常勤 二子さん' in yb, 'ご要望の枠に上申が出ません：' + yb[:200]
        await s.shot('#hbBox', 'TriTime_pw_2.png')
        await tap(pg, '#hbBox [data-jsdone="js1"]'); await pg.wait_for_timeout(400)
        yb = await pg.inner_text('#hbBox details.mnCh')
        assert '未対応なし' in yb and '対応済み 1件' in yb, '「対応済みにする」が効きません：' + yb[:120]
        # このままAIの表で使う → 置き換わる
        await tap(pg, '#pw_open'); await pg.wait_for_timeout(300)
        await tap(pg, '#pw_ai'); await pg.wait_for_timeout(800)
        wk = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_weekly')).filter(w => !w.del)")
        assert len(wk) >= 1 and all(w.get('src') == 'ai' for w in wk), 'AIの表に置き換わりません：' + str([(w.get('src'), w.get('no')) for w in wk][:5])
        assert '2026-11-05' not in '' and (await pg.evaluate("JSON.parse(localStorage.getItem('tritime_settings')).base.nurse.how")) == 'ai', 'ベースの記録（how ai）が残りません'
        # 管理者の窓：効率バージョンと比べる／パトリオット
        await tap(pg, '#tabs button[data-tab=admin]'); await pg.wait_for_timeout(500)
        assert await pg.evaluate("getComputedStyle(document.getElementById('cardEff')).display") != 'none', '管理者の窓に「効率バージョンと比べる」の枠が出ません'
        assert await pg.evaluate("!!document.getElementById('ef_month').value"), '月が入りません'
        await tap(pg, '#ef_run'); await pg.wait_for_timeout(1200)
        out = await pg.inner_text('#ef_out')
        assert '月の合計' in out and '今の表' in out and '効率版' in out and 'すべての日を見る' in out, '効率バージョンとの比べが出ません：' + out[:200]
        await s.shot('#cardEff', 'TriTime_pw_3.png')
        await tap(pg, '#ef_ptr'); await pg.wait_for_timeout(1200)
        out = await pg.inner_text('#ef_out')
        assert '全体の評価' in out and '移動に使う時間' in out and ('効率化の余地' in out), 'パトリオットの全体の評価が出ません：' + out[:200]
        assert '問題なし' not in out and '大丈夫です' not in out, '安全宣言が出ています'
        await s.shot('#cardEff', 'TriTime_pw_4.png')
        # ベースの自動投入：週間予定を空にして予定タブを開き直す
        await pg.evaluate("localStorage.setItem('tritime_weekly', '[]'); var st = JSON.parse(localStorage.getItem('tritime_settings')); delete st.base; localStorage.setItem('tritime_settings', JSON.stringify(st));")
        await pg.reload(); await pg.wait_for_timeout(1500)
        await pg.evaluate("window.confirm = function(){ return true; }")
        await tap(pg, '#tabs button[data-tab=plan]'); await pg.wait_for_timeout(300)
        await pg.evaluate("var e = document.getElementById('td_staff'); e.value = '*'; e.dispatchEvent(new Event('change'));"); await pg.wait_for_timeout(1500)
        wk = await pg.evaluate("JSON.parse(localStorage.getItem('tritime_weekly')).filter(w => !w.del)")
        assert len(wk) >= 1 and all(w.get('src') == 'base' for w in wk), '空の部署にAIのベースが自動で入りません：' + str(len(wk))
        assert 'AIが' in await pg.inner_text('#td_week') and 'ベース' in await pg.inner_text('#td_week'), 'ベースを入れた知らせが出ません'
        await s.shot('#td_week', 'TriTime_pw_5.png')
        # 使い方
        found = await pg.evaluate("Array.from(document.scripts).some(function(sc){ return sc.textContent.indexOf(\"['最初はAIのベースが自動で入る'\") >= 0 && sc.textContent.indexOf(\"['効率バージョンと比べる・パトリオット（管理者の窓）'\") >= 0; })")
        assert found, '使い方に説明がありません'
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
