# -*- coding: utf-8 -*-
"""トライタイムの引き出しの並びの試験（2026-11-03・宏史さん「ラップトップだと横の引き出しの使い方が見えなくなる。左にも引き出しを作っていい。ご要望は引き出しへ」）
・ラップトップの画面の高さ（1366×700）でも、右のつまみ（仮スケジュール表・対照表・2名体制・お知らせ）が全部画面の中に収まる
・「使い方」「ご要望」のつまみは左端にあり、押すと左から開く
・上のタブから「ご要望」が無くなり、左の引き出しの「ご要望」で残せる
・使い方は仕事の順番の章（1〜10）に分かれ、目次の章を押すとその章だけが開く"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1366, h=700)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(400)
        bot = await pg.evaluate("Math.max.apply(null, ['ssTab','kpTab','nmTab','osTab'].map(function(id){ var e = document.getElementById(id); return e && e.offsetParent ? e.getBoundingClientRect().bottom : 0; }))")
        assert bot <= 700, '右のつまみが画面の下にはみ出します（いちばん下 %d）' % bot
        lx = await pg.evaluate("[document.getElementById('mnTab').getBoundingClientRect().left, document.getElementById('rqTab').getBoundingClientRect().left]")
        assert lx[0] < 5 and lx[1] < 5, '「使い方」「ご要望」のつまみが左端にありません：' + str(lx)
        rq = await pg.evaluate("getComputedStyle(document.querySelector('#tabs button[data-tab=req]')).display")
        assert rq == 'none', '上のタブに「ご要望」が残っています'
        await pg.click('#rqTab'); await pg.wait_for_timeout(500)
        box = await pg.evaluate("(function(){ var r = document.getElementById('rqPanel').getBoundingClientRect(); return [r.left, r.width]; })()")
        assert box[0] < 5, '「ご要望」が左から開きません：' + str(box)
        assert await pg.is_visible('#rq_words') and await pg.is_visible('#rq_save'), '左の引き出しに、ご要望を残す欄が出ません'
        await s.shot('body', 'TriTime_hikidashi.png')
        await pg.click('#rqClose'); await pg.wait_for_timeout(300)
        await pg.click('#mnTab'); await pg.wait_for_timeout(500)
        mx = await pg.evaluate("document.getElementById('mnPanel').getBoundingClientRect().left")
        assert mx < 5, '「使い方」が左から開きません'
        # 使い方は、仕事の順番の章に分かれ、目次の章を押すとその章が開く（宏史さん「体系的に分類して、知りたいことを捜索しなくて済むように」）
        mb = await pg.inner_text('#mnBody')
        assert '1. はじめに（使い始めの順番）' in mb and '4. 週間予定を組む' in mb and '10. 画面に出る印の意味' in mb, '使い方が章に分かれていません：' + mb[:300]
        await pg.click('#mnBody [data-mnch="5"]'); await pg.wait_for_timeout(300)
        op = await pg.evaluate("[].map.call(document.querySelectorAll('#mnBody details.mnCh'), function(d){ return d.open ? d.id : ''; }).filter(Boolean)")
        assert op == ['mnch5'], '目次の章を押しても、その章だけが開きません：' + str(op)
        await s.shot('#mnPanel', 'TriTime_tsukaikata.png')
        await pg.fill('#mnFind', '取引先'); await pg.wait_for_timeout(300)
        mf = await pg.inner_text('#mnBody')
        assert '取引先の登録' in mf, '言葉で探すと、当たる項目が出ません'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
