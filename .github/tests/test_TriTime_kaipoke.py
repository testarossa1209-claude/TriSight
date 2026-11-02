# -*- coding: utf-8 -*-
"""トライタイムの「カイポケの一覧からまとめて登録」の試験（2026-11-02）
架空の利用者だけで作ったカイポケ形式のCSV（Shift-JIS・23列）を試験の中で作って読ませる（本物の利用者の情報は使わない）。
・登録済みの方（氏名が同じ）は一覧に出さず「すでに登録されている」に回り、書き換わらない
・地区は住所から町名＋丁目（全角の数字・「5丁目38番地」の形も）、保険は指示区分と介護度から見立てる
・生年月日・保険の番号は登録されない
・同じ契約書番号を二人に入れると止まり、何も登録されない
・番号を入れた方だけが登録され、番号の無い方は一覧に残る
・画面の中で誤りが出ない"""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, IPAD

HEAD = ['利用者名','利用者カナ','生年月日','年齢','電話番号','住所','介護度','被保険者番号','介護被保証適用期間(自)','介護被保証適用期間(至)',
        '居宅介護支援事業所','担当ケアマネ','居宅電話番号','医療保険種類','被保険者等記号・番号','医療被保証適用期間(自)','医療被保証適用期間(至)',
        '指示区分','指示書期間(自）','指示書期間(至）','医療機関名','主治医名','医療機関電話番号']
def row(name, kana, birth, tel, addr, care, cat, f, t, hosp, doc):
    return [name, kana, birth, '50歳 1ヶ月', tel, addr, care, '0000999999' if care != '-' else '-', '-', '-', '-', '-', '-', '-', '-', '-', '-',
            cat, f, t, hosp, doc, '042-000-0000']
ROWS = [
    row('試験　一郎', 'シケン　イチロウ', '昭和50年1月2日', '09011112222', '東京都東村山市本町2-3-4試験荘101', '-', '精神指示', '令和8年10月1日', '令和9年3月31日', '試験病院', '医師　一'),
    row('試験　二子', 'シケン　フタコ', '昭和12年4月1日', '042-000-1111', '東京都東村山市萩山町５丁目38番地22', '要介護１', '通常指示', '令和8年11月1日', '令和8年11月30日', '試験診療所', '医師　二'),
    row('試験　三郎', 'シケン　サブロウ', '平成元年5月6日', '-', '東京都清瀬市竹丘2-8-25-101', '-', '通常指示', '令和8年9月1日', '令和9年2月28日', '試験病院', '医師　一'),
    row('既存　花子', 'キゾン　ハナコ', '昭和40年1月1日', '080-0000-0000', '東京都東村山市青葉町1-2-3', '-', '精神指示', '令和8年8月1日', '令和9年1月31日', '試験病院', '医師　一'),
]

def make_csv():
    d = tempfile.mkdtemp()
    path = os.path.join(d, 'HNC09000P1.csv')
    lines = [','.join('"' + c + '"' for c in r) for r in [HEAD] + ROWS]
    with open(path, 'wb') as f: f.write(('\r\n'.join(lines) + '\r\n').encode('cp932'))
    return path

async def cells(pg):
    return await pg.eval_on_selector_all('#kpi_list tbody tr', """trs=>trs.map(tr=>{const td=tr.querySelectorAll('td');return {
      name: td[1].textContent, area: td[2].querySelector('input').value, ins: td[3].querySelector('select').value, tel: td[5].textContent, inst: td[6].textContent }})""")

async def test(p):
    csv = make_csv()
    s = Screen(); pg = await s.open(p, 'TriTime.html', ua=IPAD)
    try:
        await pg.evaluate("document.querySelector('#tabs button[data-tab=pt]').click()"); await pg.wait_for_timeout(400)
        # 先に「既存 花子」をふつうの登録画面で入れておく
        await pg.fill('#pt_no', 'T-0001'); await pg.fill('#pt_name', '既存 花子'); await pg.fill('#pt_area', '青葉町一丁目')
        await pg.click('#pt_add'); await pg.wait_for_timeout(500)
        assert 'T-0001' in await pg.inner_text('#ptList'), '前置きの登録（既存 花子）ができません'

        await pg.set_input_files('#kpi_file', csv); await pg.wait_for_timeout(800)
        msg = await pg.inner_text('#kpi_msg')
        assert '4人のうち' in msg and '3人' in msg, '読み込みの知らせが違います：' + msg
        c = await cells(pg)
        names = [x['name'] for x in c]
        assert len(c) == 3 and not any('既存' in n for n in names), '登録済みの方が一覧に出ています：' + str(names)
        assert '既存 花子' in await pg.text_content('#kpi_done') and 'T-0001' in await pg.text_content('#kpi_done'), '登録済みの方の知らせが出ません'
        a1, a2, a3 = c[0], c[1], c[2]
        assert a1['area'] == '本町二丁目' and a2['area'] == '萩山町五丁目' and a3['area'] == '竹丘二丁目', '地区の見立てが違います：' + str([x['area'] for x in c])
        assert a1['ins'] == '精神科訪問看護（医療）' and a2['ins'] == '介護保険' and a3['ins'] == '医療保険', '保険の見立てが違います：' + str([x['ins'] for x in c])
        assert a1['tel'] == '090-1111-2222' and a2['tel'] == '042-000-1111' and a3['tel'] == '', '電話番号のそろえ方が違います：' + str([x['tel'] for x in c])
        assert a1['inst'] == '2026年10月1日〜2027年3月31日', '指示書の期間（和暦→西暦）が違います：' + a1['inst']
        if os.environ.get('SHOTS'): await s.shot('#cardKpi', 'TriTime_kaipoke_list.png')

        # 番号を一人も入れずに押す → 止まる
        await pg.click('#kpi_go'); await pg.wait_for_timeout(300)
        assert '契約書番号が入っている方がいません' in await pg.inner_text('#kpi_msg'), '番号なしで押したときの知らせが出ません'
        # 同じ番号を二人に入れる → 止まり、何も登録されない
        await pg.fill('#kpi_no0', 'T-0101'); await pg.fill('#kpi_no1', 'T-0101'); await pg.click('#kpi_go'); await pg.wait_for_timeout(400)
        assert '二人に入っています' in await pg.inner_text('#kpi_msg'), '同じ番号の二重入力で止まりません'
        assert 'T-0101' not in await pg.inner_text('#ptList'), '止まったはずなのに登録されています'
        # 既存の番号を入れる → 止まる
        await pg.fill('#kpi_no1', 'T-0001'); await pg.click('#kpi_go'); await pg.wait_for_timeout(400)
        assert 'すでに別の方' in await pg.inner_text('#kpi_msg'), '使用済みの番号で止まりません'
        # 一人目と二人目だけ番号を入れて登録（三人目は空のまま）
        await pg.fill('#kpi_no1', 'T-0102'); await pg.click('#kpi_go'); await pg.wait_for_timeout(800)
        msg = await pg.inner_text('#kpi_msg')
        assert '登録しました：2人' in msg and '番号の入っていない方 1人' in msg, '登録の知らせが違います：' + msg
        left = await cells(pg)
        assert len(left) == 1 and '試験 三郎' in left[0]['name'], '番号の無い方が一覧に残っていません'
        lst = await pg.inner_text('#ptList')
        assert 'T-0101' in lst and 'T-0102' in lst and 'T-0001' in lst, '登録した方が患者さんの一覧に出ません'
        # 呼び出して中身を確かめる（生年月日・保険の番号は入らない）
        await pg.fill('#pt_no', 'T-0102'); await pg.click('#pt_load'); await pg.wait_for_timeout(400)
        v = await pg.evaluate("['pt_name','pt_kana','pt_area','pt_addr','pt_ins','pt_telHome','pt_telMobile','pt_hosp','pt_doc','pt_inst','pt_instEnd','pt_status'].map(i=>document.getElementById(i).value)")
        assert v == ['試験 二子', 'しけん ふたこ', '萩山町五丁目', '東京都東村山市萩山町5丁目38番地22', '介護保険', '042-000-1111', '', '試験診療所', '医師 二', '2026-11-01', '2026-11-30', '利用中'], '登録された中身が違います：' + str(v)
        raw = await pg.evaluate("Object.keys(localStorage).map(k=>localStorage.getItem(k)).join('|')")
        assert '1937-04-01' not in raw and '0000999999' not in raw and '昭和12年' not in raw, '生年月日・保険の番号が保存されています'
        if os.environ.get('SHOTS'): await s.shot('#cardKpi', 'TriTime_kaipoke_done.png')
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
