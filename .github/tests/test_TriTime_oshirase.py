# -*- coding: utf-8 -*-
"""トライタイムの利用者さんへのお知らせの試験（2026-11-03・宏史さん「サービス当日に、本日は訪問看護のお伺い予定日です、と定型文を送る。とりあえずは一押し形式」）
・右端のつまみ「お知らせ」で、今日の訪問の利用者さんが時刻順に1人1行で出る（キャンセルの入った訪問は出ない）
・携帯番号のある人には「送る」が出て、押すと宛先と定型文（時刻入り）の入ったメッセージが開く。押すと「送った」になる
・携帯番号の無い人は「携帯番号なし」
・つまみの角に、今日まだ知らせていない人数が赤い丸の数字で出て、送ると消える。丸でつまみの幅は変わらない（宏史さん「横の引き出しに一押し情報もつけてもらえれば忘れずに一押しできる」）"""
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
            { no:'2010-01-看-9903', name:'試験 休み', area:'東町', status:'利用中', telMobile:'090-3333-4444', upd:t },
            { no:'2010-01-看-9904', name:'試験 自宅欄', area:'東町', status:'利用中', telHome:'０８０－５５５５－６６６６', upd:t },
            { no:'2010-01-看-9905', name:'試験 家族', area:'東町', status:'利用中', telHome:'042-111-2222', em1Name:'試験 花子', em1Rel:'長女', em1Tel:'070-7777-8888', em1Contact:'連絡してよい', upd:t },
            { no:'2010-01-看-9906', name:'試験 固定', area:'東町', status:'利用中', telHome:'042-333-4444', em1Tel:'090-9999-0000', em1Contact:'緊急時のみ', upd:t } ]));
          localStorage.setItem('tritime_weekly', JSON.stringify([
            { id:'w1', dow:dow, time:'10:00', min:30, no:'2010-01-看-9901', staffId:a, withId:'', upd:t },
            { id:'w2', dow:dow, time:'09:15', min:30, no:'2010-01-看-9902', staffId:a, withId:'', upd:t },
            { id:'w3', dow:dow, time:'10:45', min:30, no:'2010-01-看-9903', staffId:a, withId:'', upd:t },
            { id:'w4', dow:dow, time:'13:00', min:30, no:'2010-01-看-9904', staffId:a, withId:'', upd:t },
            { id:'w5', dow:dow, time:'14:00', min:30, no:'2010-01-看-9905', staffId:a, withId:'', upd:t },
            { id:'w6', dow:dow, time:'15:00', min:30, no:'2010-01-看-9906', staffId:a, withId:'', upd:t } ]));
          localStorage.setItem('tritime_events', JSON.stringify([{ id:'c1', type:'cancel', patientNo:'2010-01-看-9903', date:dt, time:'10:45', upd:t }])); })()""")
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(300)
        assert await pg.is_visible('#osTab'), '右端に「お知らせ」のつまみが出ません'
        bd = await pg.evaluate("(document.querySelector('#osTab .osCnt') || {}).textContent || ''")
        assert bd == '3', 'つまみに、今日まだ知らせていない人数（携帯の番号のある3人）が出ません：' + bd
        # 2026-11-03 改め（宏史さん「お知らせだけファットで並びが悪い」）：人数の丸でつまみの幅が変わらない
        wd = await pg.evaluate("['mnTab','osTab','rqTab'].map(function(id){ return Math.round(document.getElementById(id).getBoundingClientRect().width); })")
        assert wd[1] == wd[0] == wd[2], '「お知らせ」のつまみだけ幅が違います：' + str(wd)
        await s.shot('.sideTabs.lft', 'TriTime_oshirase_tsumami.png')
        await pg.click('#osTab'); await pg.wait_for_timeout(400)
        ob = await pg.inner_text('#osBody')
        assert '試験 携帯' in ob and '試験 無し' in ob and '試験 休み' not in ob, '今日の訪問の利用者さん（キャンセルを除く）が出ません：' + ob[:300]
        assert ob.index('試験 無し') < ob.index('試験 携帯'), '時刻順に並びません'
        assert '携帯番号なし' in ob, '携帯番号の無い人に「携帯番号なし」が出ません'
        href = await pg.get_attribute('#osBody [data-ossend]', 'href')
        assert href.startswith('sms:09011112222') and '10%3A00' in href and '%E8%A8%AA%E5%95%8F%E7%9C%8B%E8%AD%B7' in href, '「送る」の宛先と文面（時刻入り）が正しくありません：' + href
        # 2026-11-03（宏史さん「ラップトップのお知らせ画面は、携帯番号がすべてなし」）：自宅の欄の携帯・ご家族の携帯にも送れる
        hs = await pg.evaluate("[...document.querySelectorAll('#osBody [data-ossend]')].map(a => a.getAttribute('data-ossend') + '=' + a.getAttribute('href').split('?')[0])")
        assert 'sms:08055556666' in ' '.join(hs), '本人の自宅の欄に入っている携帯（全角）へ送れません：' + str(hs)
        assert 'sms:07077778888' in ' '.join(hs), 'ご家族の連絡先の携帯へ送れません：' + str(hs)
        assert '長女 試験 花子さん' in ob, 'ご家族へ送るとき、誰あてかが出ません'
        assert '試験 固定' in ob and '登録の電話 042-333-4444' in ob, '携帯の無い人に、登録の電話が添えて出ません'
        assert len(hs) == 3, '「緊急時のみ」の連絡先に送る形になっています：' + str(hs)
        await pg.evaluate("document.querySelector('#osBody [data-ossend]').addEventListener('click', function(e){ e.preventDefault(); }, true)")
        await pg.click('#osBody [data-ossend]'); await pg.wait_for_timeout(700)
        ob2 = await pg.inner_text('#osBody')
        assert '送った' in ob2, '「送る」を押しても「送った」になりません'
        bd2 = await pg.evaluate("(document.querySelector('#osTab .osCnt') || {}).textContent || ''")
        assert bd2 == '2', '送った後に、つまみの残りの人数が減りません：' + bd2
        await s.shot('#osPanel', 'TriTime_oshirase.png')
        # 2026-11-03（宏史さん「お知らせは一括送信ボタンを作ってください」）：まとめて送る＝1人目が開き、画面へ戻るたびに次の人が開く
        bt = await pg.inner_text('#osBulk')
        assert 'まだの 2人' in bt, '「まとめて送る」のボタンに、まだの人数が出ません：' + bt
        await pg.evaluate("document.addEventListener('click', function(e){ var a = e.target && e.target.closest && e.target.closest('a[href^=\"sms:\"]'); if(a){ e.preventDefault(); window.__sms = (window.__sms || []).concat([a.getAttribute('href')]); } }, true)")
        await pg.click('#osBulk'); await pg.wait_for_timeout(500)
        ob4 = await pg.inner_text('#osBody')
        assert '残り 1人' in ob4, '「まとめて送る」を押しても、1人目を送って残りの人数が出ません：' + ob4[:300]
        await s.shot('#osPanel', 'TriTime_oshirase_matome.png')
        await pg.evaluate("window.dispatchEvent(new Event('focus'))"); await pg.wait_for_timeout(1400)
        await pg.evaluate("window.dispatchEvent(new Event('focus'))"); await pg.wait_for_timeout(1400)
        ob5 = await pg.inner_text('#osBody')
        sms = await pg.evaluate("window.__sms || []")
        assert len(sms) == 2 and sms[0].startswith('sms:08055556666') and sms[1].startswith('sms:07077778888'), 'まとめて送るで開くメッセージの宛先が正しくありません：' + str(sms)
        assert ob5.count('送った') >= 3 and 'まとめて送る' not in ob5 and '残り' not in ob5, '画面へ戻っても、次の人へ進みません：' + ob5[:400]
        # 2026-11-03（宏史さん「看護部だけが携帯番号を持っていて、その他の部門はすべて携帯番号なし。各部統一が必須」）：どの部署で開いても同じ中身
        for dk in ['office', 'kaigo', 'soudan']:
            await pg.click('#osClose'); await pg.wait_for_timeout(200)
            await pg.click('#deptBar [data-dept=' + dk + ']'); await pg.wait_for_timeout(500)
            await pg.click('#osTab'); await pg.wait_for_timeout(400)
            ob3 = await pg.inner_text('#osBody')
            n3 = await pg.evaluate("document.querySelectorAll('#osBody [data-ossend]').length")
            assert '試験 携帯' in ob3 and '試験 家族' in ob3 and n3 == 3, dk + ' の部署で開くと、お知らせの中身が看護部と違います：' + str(n3) + ' ' + ob3[:200]
            if dk == 'office': await s.shot('#osPanel', 'TriTime_oshirase_bumon.png')
            bd3 = await pg.evaluate("(document.querySelector('#osTab .osCnt') || {}).textContent || ''")
            assert bd3 == '', dk + ' の部署で、つまみの残りの人数が看護部と違います：' + bd3
        await pg.click('#osClose'); await pg.wait_for_timeout(200)
        await pg.click('#deptBar [data-dept=office]'); await pg.wait_for_timeout(500)
        await pg.click('#ssTab'); await pg.wait_for_timeout(500)
        # 2026-11-03（宏史さん「仮スケジュール表を開くと同時に、左の使い方が何も記載されない形で開く。両サイドから一遍に開く」）
        lft = await pg.evaluate("['mnPanel','osPanel','rqPanel','kpPanel','nmPanel'].filter(function(id){ var r = document.getElementById(id).getBoundingClientRect(); return r.right > 0 && r.left < innerWidth; })")
        assert lft == [], '仮スケジュール表を開くと、ほかの引き出しも一緒に開きます：' + str(lft)
        sb = await pg.inner_text('#ssBody')
        assert '訪問看護部' in sb and '試験 携帯' in sb, '経営企画事務職で開くと、仮スケジュール表に訪問看護部の表が出ません：' + sb[:200]
        await pg.click('#ssClose'); await pg.wait_for_timeout(300)
        await pg.click('#kpTab'); await pg.wait_for_timeout(500)
        kb = await pg.inner_text('#kpBody')
        assert '試験 携帯' in kb, '経営企画事務職で開くと、対照表に訪問看護部の利用者さんが出ません：' + kb[:200]
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
