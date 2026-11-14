# -*- coding: utf-8 -*-
"""対照表で予定の希望を入れる試験（2026-11-14・宏史さん「一人ひとりのアセスメント登録のような大げさなものではなく、簡単に入力できる」
「利用者登録画面にも週の回数や希望の時間帯、何名体制かの枠があれば一度で済む」「死亡した利用者の情報がいまだに記載されています」）
・対照表は、ふだん契約終了（死亡を含む）の人を出さない。「契約終了の人も出す」に印を付けたときだけ出る
・対照表で①曜日・②時刻と時間帯・⑤体制を入れると週の回数が出て、「入れた内容を保存する」で利用者登録と同じ欄に入る
・利用者登録の「予定の希望」は、電話番号・緊急連絡先のすぐ下（2段目）にあり、①の横に週の回数が出る"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

SEED = """(function(){ var up = Date.now();
  var ST = [ { id:'s1', name:'島 看護', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['6','0'], upd:up },
    { id:'s2', name:'渋谷 花', emp:'常勤', job:'事務局', dept:'経営企画事務職', off:['6','0'], upd:up } ];
  var PT = [ { no:'N0001', name:'試験 一郎', kana:'しけん いちろう', area:'本町', status:'利用中', wDays:['1'], wBand:'午前', upd:up },
    { no:'N0002', name:'試験 二郎', kana:'しけん じろう', area:'栄町', status:'利用中', upd:up },
    { no:'N0003', name:'試験 終了', kana:'しけん しゅうりょう', area:'本町', status:'契約終了', endWhy:'死亡', endDate:'2026-11-01', upd:up } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(PT)); localStorage.setItem('tritime_weekly', '[]'); localStorage.setItem('tritime_events', '[]');
  localStorage.setItem('tritime_settings', JSON.stringify({ work:{} })); localStorage.setItem('tritime_device', JSON.stringify({ me:'s2', share:true })); localStorage.setItem('tritime_dept', 'nurse');
})()"""

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1366, h=900)
    try:
        await pg.evaluate(SEED); await pg.reload(); await pg.wait_for_timeout(1500)
        if await pg.query_selector('#ogGo'):   # 開き直したときに入口が出たら、もう一度通す
            await pg.evaluate("document.getElementById('ogGo').click()"); await pg.wait_for_timeout(2500)
        await pg.evaluate("document.getElementById('kpTab').click()"); await pg.wait_for_timeout(500)
        body = ''
        for _ in range(16):   # 開き直した直後は、記録の読み込みが済むまで少し待つ
            body = await pg.inner_text('#kpBody')
            if '試験 一郎' in body: break
            await pg.wait_for_timeout(500); await pg.evaluate("window.kpRender && kpRender()")
        assert '試験 一郎' in body and '試験 二郎' in body, '対照表に利用中の人が出ません：' + body[:200]
        assert '試験 終了' not in body, '対照表に契約終了（死亡）の人が出ています'
        assert '契約終了の 1人は出していません' in body, '外した人数の断り書きが出ません'
        await pg.check('#kpEnd'); await pg.wait_for_timeout(300)
        assert '試験 終了' in await pg.inner_text('#kpBody'), '「契約終了の人も出す」に印を付けても出ません'
        await pg.uncheck('#kpEnd'); await pg.wait_for_timeout(300)
        # 試験 二郎に 火・金、14:00、2名 を入れる
        row = '#kpBody tr[data-kpno="N0002"]'
        await pg.check(row + ' [data-kpf=dow][value="2"]'); await pg.check(row + ' [data-kpf=dow][value="5"]')
        cnt = await pg.inner_text(row + ' [data-kpcnt]')
        assert cnt == '週2回', '印の数が週の回数になりません：' + cnt
        await pg.fill(row + ' [data-kpf=wish]', '14:00'); await pg.dispatch_event(row + ' [data-kpf=wish]', 'change')
        await pg.select_option(row + ' [data-kpf=team]', '2名')
        await s.shot('#kpPanel', 'TriTime_taishohyo.png')
        await pg.evaluate("document.querySelector('#kpBody [data-kpsave]').click()"); await pg.wait_for_timeout(1500)
        got = await pg.evaluate("(function(){ var p = JSON.parse(localStorage.getItem('tritime_patients')).filter(function(x){ return x.no === 'N0002'; })[0]; return [p.wDays, p.wish, p.team]; })()")
        assert got == [['2', '5'], '14:00', '2名'], '保存した内容が利用者登録の欄に入りません：' + str(got)
        assert '保存しました（1人）' in await pg.inner_text('#kpBody'), '保存の知らせが出ません'
        # 利用者登録：予定の希望が2段目、①の横に週の回数
        await pg.evaluate("document.getElementById('kpClose').click()"); await pg.wait_for_timeout(300)
        order = await pg.evaluate("[].map.call(document.querySelectorAll('#cardPt details.ptsec'), function(d){ return d.id; }).slice(0, 2)")
        assert order == ['ptsTel', 'ptsWish'], '予定の希望が電話番号・緊急連絡先のすぐ下にありません：' + str(order)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=pt]') && document.querySelector('#tabs button[data-tab=pt]').click()"); await pg.wait_for_timeout(400)
        await pg.evaluate("(function(){ var b = document.querySelectorAll('#pt_wDays input'); b[0].click(); b[2].click(); b[4].click(); })()"); await pg.wait_for_timeout(200)
        wc = await pg.inner_text('#pt_wCnt')
        assert wc == '週3回', '利用者登録の①の横に週の回数が出ません：' + wc
        await s.shot('#ptsWish', 'TriTime_yotei_kibou.png')
        assert not s.errs, '画面の中で誤り：' + str(s.errs)
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
