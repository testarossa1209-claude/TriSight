# -*- coding: utf-8 -*-
"""受給計画書（TriPlan）の試験（2026-11-21・宏史さん「受給計画で決裁が取れた最終的な助成金で獲得スケジュールを組む」）
・受給計画データを読み込むと、一覧（1ページ目）・時系列・制度ごと・確認待ちのページが出る
・「進める」を押すと、受け渡し箱（tritask_inbox）に宛先の会社名で入り、決裁の印（tg_kessai）が go になる
・「見送る」を押すと、決裁の印が stop になる
・2026-11-22-01：1ページ目に「AIの判定」の欄があり、「支給の決まり方」の欄は無い。［この制度の詳細］を押すと、判断材料と支給の決まり方が出る
試験の計画データは架空の会社（実在の会社の情報は使わない）。"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run

PLAN = {
  "様式": "受給計画データ", "計画番号": "TEST-01", "作成日": "2026-11-21",
  "宛先": {"会社名": "試験交通株式会社", "代表者": "代表取締役 試験 太郎 様"},
  "前提": ["試験用"], "当社の受け持ち": "試験", "当社が受け持たないこと": "試験",
  "制度": [
    {"id": "a", "名称": "試験の助成金A", "発出元": "厚生労働省", "使い道": "試験", "締切": "2026-12-25", "支給の決まり方": "試験の先着",
     "判断材料": {"誰が": "試験の講師", "費用": "試験の費用"}, "AIの判定": {"判定": "取るべき", "理由": "試験の理由"},
     "時系列": [{"時期": "2026-12-25", "内容": "締切"}], "出所": [{"名": "試験", "確認日": "2026-11-21"}]},
    {"id": "b", "名称": "試験の補助金B", "発出元": "国土交通省", "使い道": "試験", "獲得スケジュールの締切": "2027-09-30",
     "時系列": [{"時期": "2027-09-30", "内容": "申請"}]}
  ],
  "確認待ち": [{"項目": "試験の確認", "決まること": "試験", "確認先": "試験"}],
  "見送り": [{"名称": "試験の見送り", "理由": "試験", "次の機会": "—"}],
  "約束ごと": ["試験"]
}

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriPlan.html')
    try:
        await pg.evaluate("localStorage.setItem('triplan_last', %s); localStorage.removeItem('tritask_inbox'); localStorage.removeItem('tg_kessai'); localStorage.removeItem('triplan_decisions');" % json.dumps(json.dumps(PLAN, ensure_ascii=False)))
        await pg.reload(); await pg.wait_for_timeout(800)
        n = await pg.evaluate("document.querySelectorAll('#out section.page').length")
        assert n == 5, '計画書のページ数が合いません（一覧・時系列・制度2件・確認待ちの5ページのはず）：%s' % n
        h1 = await pg.evaluate("document.querySelector('#out section.page table').rows[0].innerText")
        assert 'AIの判定' in h1 and '支給の決まり方' not in h1, '1ページ目の欄が「AIの判定」に替わっていません：' + h1
        assert '試験の理由' in await pg.evaluate("document.querySelector('#out section.page').innerText"), 'AIの判定の理由が1ページ目に出ていません'
        await pg.click('button[data-dt="a"]'); await pg.wait_for_timeout(300)
        dt = await pg.evaluate("(document.querySelector('#out tr.dt')||{}).innerText||''")
        assert '試験の講師' in dt and '試験の先着' in dt, '［この制度の詳細］を押しても、判断材料と支給の決まり方が出ません'
        await pg.click('button[data-id="a"][data-v="go"]'); await pg.wait_for_timeout(300)
        inbox = json.loads(await pg.evaluate("localStorage.getItem('tritask_inbox')") or '[]')
        card = [x for x in inbox if x.get('id') == 'TP-TEST-01-a']
        assert card, '「進める」を押しても受け渡し箱に入りません'
        assert card[0]['company_name'] == '試験交通株式会社', '受け渡し箱の会社名が宛先と違います'
        assert card[0]['deadlines'] == ['2026-12-25'], '受け渡し箱の締切が計画データと違います'
        assert 'TriGate' in card[0]['source_product'], '獲得スケジュールが読む印（TriGate）が付いていません'
        ks = json.loads(await pg.evaluate("localStorage.getItem('tg_kessai')") or '{}')
        assert ks.get('TP-TEST-01-a') == 'go', '「進める」を押しても決裁の印が go になりません'
        await pg.click('button[data-id="b"][data-v="go"]'); await pg.wait_for_timeout(300)
        inbox = json.loads(await pg.evaluate("localStorage.getItem('tritask_inbox')") or '[]')
        cb = [x for x in inbox if x.get('id') == 'TP-TEST-01-b']
        assert cb and cb[0]['deadlines'] == ['2027-09-30'], '締切の無い制度で、獲得スケジュール用の締切が使われていません'
        await pg.click('button[data-id="b"][data-v="stop"]'); await pg.wait_for_timeout(300)
        ks = json.loads(await pg.evaluate("localStorage.getItem('tg_kessai')") or '{}')
        assert ks.get('TP-TEST-01-b') == 'stop', '「見送る」を押しても決裁の印が stop になりません'
        assert not s.errs, '画面の中で誤りが出ています：' + ' / '.join(s.errs)
        await s.shot('#out', 'TriPlan_kessai.png')
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
