# -*- coding: utf-8 -*-
"""トライタイムの緊急連絡先の種別の試験（2026-11-03・宏史さんの指示）
・種別が空（これまでの登録）や「家族・親族」のときは、氏名・同居/別居・主介護者が出て、所属は出ない
・「行政（生活保護・保健師など）」を選ぶと、所属と担当者名が出て、同居/別居・主介護者は隠れる
・種別・所属・電話の補足・関わり方が登録され、呼び出すと元どおり戻り、出し方も種別どおりになる
・書類の読み込みの答え（中継が返す形）に種別・所属が入っていれば、欄に入り、出し方も切り替わる"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, IPAD

VIS = "n=>{const b=document.getElementById('pt_em'+n+'Box');return {fam:getComputedStyle(b.querySelector('.emFam')).display!=='none',org:getComputedStyle(b.querySelector('.emOrg')).display!=='none',lab:b.querySelector('label[for=\"pt_em'+n+'Name\"]').textContent}}"

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriTime.html', ua=IPAD)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=pt]').click()"); await pg.wait_for_timeout(400)
        v = await pg.evaluate(VIS, 1)
        assert v['fam'] and not v['org'] and v['lab'] == '氏名', '種別が空のときの出し方が違います：' + str(v)
        await pg.select_option('#pt_em1Kind', '行政（生活保護・保健師など）'); await pg.wait_for_timeout(200)
        v = await pg.evaluate(VIS, 1)
        assert v['org'] and not v['fam'] and v['lab'] == '担当者名', '行政を選んだときの出し方が違います：' + str(v)
        await pg.fill('#pt_em1Org', '試験市役所 生活福祉課'); await pg.fill('#pt_em1Name', '試験'); await pg.fill('#pt_em1Rel', 'ケースワーカー')
        await pg.fill('#pt_em1Tel', '042-000-0000'); await pg.fill('#pt_em1TelNote', '代表番号'); await pg.select_option('#pt_em1Contact', '連絡してよい')
        await pg.select_option('#pt_em2Kind', '家族・親族'); await pg.fill('#pt_em2Name', '試験 一郎'); await pg.fill('#pt_em2Rel', '兄')
        await pg.select_option('#pt_em2Contact', '関わりを拒んでいる（連絡しない）'); await pg.select_option('#pt_em2Main', '主介護者ではない')
        await pg.fill('#pt_no', 'T-0901'); await pg.fill('#pt_name', '試験 花子'); await pg.fill('#pt_area', '青葉町一丁目')
        await pg.evaluate("document.getElementById('pt_anyTime').checked = true"); await pg.click('#pt_add'); await pg.wait_for_timeout(600)
        await pg.click('#pt_clear'); await pg.wait_for_timeout(200)
        await pg.fill('#pt_no', 'T-0901'); await pg.click('#pt_load'); await pg.wait_for_timeout(400)
        got = await pg.evaluate("['pt_em1Kind','pt_em1Org','pt_em1Name','pt_em1Rel','pt_em1TelNote','pt_em1Contact','pt_em2Kind','pt_em2Contact','pt_em2Main'].map(i=>document.getElementById(i).value)")
        assert got == ['行政（生活保護・保健師など）', '試験市役所 生活福祉課', '試験', 'ケースワーカー', '代表番号', '連絡してよい', '家族・親族', '関わりを拒んでいる（連絡しない）', '主介護者ではない'], '登録した緊急連絡先が呼び出しで戻りません：' + str(got)
        v1, v2 = await pg.evaluate(VIS, 1), await pg.evaluate(VIS, 2)
        assert v1['org'] and not v1['fam'] and v2['fam'] and not v2['org'], '呼び出した後の出し方が種別どおりになりません：' + str([v1, v2])
        await s.shot('#ptsTel', 'TriTime_emergency.png')
        await pg.click('#pt_clear'); await pg.wait_for_timeout(200)
        # 中継の答えを差し替え、実際に「読み込ませる」を押す（AIは呼ばない）
        async def doc(route):
            body = route.request.post_data or ''
            if 'tritime_doc' in body:
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({'ok': True, 'kind': 'base', 'contractNo': '', 'warn': [],
                    'fields': {'em1Kind': '相談支援・地域包括', 'em1Org': '試験包括支援センター', 'em1Name': '試験', 'em1Rel': '相談員'}}))
            else:
                await route.fallback()
        await pg.route('**/api/gate', doc)
        await pg.set_input_files('#rd_file', files=[{'name': 'face.pdf', 'mimeType': 'application/pdf', 'buffer': b'%PDF-1.4 test'}])
        await pg.click('#rd_go'); await pg.wait_for_timeout(800)
        v = await pg.evaluate(VIS, 1)
        msg = await pg.inner_text('#rd_msg')
        assert await pg.input_value('#pt_em1Org') == '試験包括支援センター' and v['org'] and not v['fam'] and v['lab'] == '担当者名', '読み込みの答えで種別・所属が入らない、または出し方が変わりません：' + msg + str(v)
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
