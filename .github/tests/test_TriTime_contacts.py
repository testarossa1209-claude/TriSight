# -*- coding: utf-8 -*-
"""トライタイムの連絡先の試験（2026-11-02・申請#84の中身）
・全角で入れた携帯番号・メールアドレスが、090-1234-5678 と半角にそろって職員の表に出る
・桁の足りない番号は保存のときに止まる
・連絡板で全員あてに出すと、連絡先のある職員あてに「携帯へSMSを送る」「メールで送る」が出る（出した本人は宛先に入らない）
・Windows のパソコンでは SMS のボタンが出ず、メールだけになる"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, IPAD

WIN = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

async def one(p, ua, shots):
    s = Screen(); pg = await s.open(p, 'TriTime.html', ua=ua)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=setup]').click()"); await pg.wait_for_timeout(400)
        for name, tel, mail in [('試験 花子', '０９０１２３４５６７８', 'ｈａｎａｋｏ＠ｎｏａ．ｊｐ'), ('試験 太郎', '', '')]:
            await pg.fill('#st_name', name); await pg.fill('#st_tel', tel); await pg.fill('#st_mail', mail)
            await pg.click('#st_add'); await pg.wait_for_timeout(300)
        txt = await pg.inner_text('#stList')
        assert '090-1234-5678' in txt and 'hanako@noa.jp' in txt, '全角で入れた連絡先が、半角にそろって職員の表に出ません'
        await pg.fill('#st_name', '試験 次郎'); await pg.fill('#st_tel', '0901'); await pg.click('#st_add'); await pg.wait_for_timeout(300)
        assert any('桁が合いません' in d for d in s.dialogs), '桁の足りない携帯番号で止まりません'
        assert '試験 次郎' not in await pg.inner_text('#stList'), '桁の足りない携帯番号の職員が保存されました'
        await pg.fill('#st_tel', ''); await pg.fill('#st_name', '')
        if shots: await s.shot('#stList', 'TriTime_contacts_list.png')
        await pg.evaluate("document.querySelector('#tabs button[data-tab=plan]').click()"); await pg.wait_for_timeout(400)
        await pg.click('#nbNew summary'); await pg.wait_for_timeout(300)
        await pg.select_option('#nb_from', label=[o for o in await pg.eval_on_selector_all('#nb_from option', 'o=>o.map(x=>x.textContent)') if o.startswith('試験 太郎')][0])
        await pg.select_option('#nb_to', 'all'); await pg.fill('#nb_title', '試験の周知'); await pg.fill('#nb_body', '本日17時に会議')
        await pg.click('#nb_send'); await pg.wait_for_timeout(500)
        hrefs = await pg.eval_on_selector_all('#nb_pn a', 'a=>a.map(x=>decodeURIComponent(x.href))')
        if shots: await s.shot('#nb_pn', 'TriTime_contacts_board.png')
        return s, hrefs, await pg.inner_text('#nb_pn')
    except Exception:
        await s.close(); raise

async def test(p):
    s, hrefs, txt = await one(p, IPAD, True)
    try:
        assert any(h.startswith('sms:09012345678') for h in hrefs), 'iPad で「携帯へSMSを送る」の宛先が正しくありません：' + str(hrefs)
        assert any(h.startswith('mailto:hanako@noa.jp') for h in hrefs), '「メールで送る」の宛先が正しくありません：' + str(hrefs)
        assert all('試験 太郎より' in h for h in hrefs), '文面に出した人の名前が入っていません'
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()
    s, hrefs, txt = await one(p, WIN, False)
    try:
        assert not any(h.startswith('sms:') for h in hrefs), 'Windows で SMS のボタンが出ています'
        assert any(h.startswith('mailto:') for h in hrefs), 'Windows でメールのボタンが出ません'
        assert 'このパソコンからはSMSを送れません' in txt, 'Windows で SMS は iPad・iPhone から、という案内が出ません'
    finally:
        await s.close()

sys.exit(run(test))
