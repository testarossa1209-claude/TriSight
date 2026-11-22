# -*- coding: utf-8 -*-
"""受給計画書（TriPlan）の試験（2026-11-21・宏史さん「受給計画で決裁が取れた最終的な助成金で獲得スケジュールを組む」）
・受給計画データを読み込むと、一覧（1ページ目）・時系列・制度ごと・確認待ちのページが出る
・「進める」を押すと、受け渡し箱（tritask_inbox）に宛先の会社名で入り、決裁の印（tg_kessai）が go になる
・「見送る」を押すと、決裁の印が stop になる
・2026-11-22-12：制度の欄に、おすすめの印（◎○△）と背中を押す一言
・2026-11-22-11：「ひとことで」は制度の欄（左端）の余白へ移した
・2026-11-22-10：AIアドバイスの欄の一番下に「ひとことで：」の札
・2026-11-22-09：判定の札は出さず、AIアドバイスの欄の頭に「取るために整えること」
・2026-11-22-08：判断は計画データの中（判断）にも書き込まれる
・2026-11-22-08：進めるを見送る等に変えたら、手付かずのカードは受け渡し箱から消える
・2026-11-22-07：次の一手は進める前は出さず、「進める」を押すと判定の欄に出る。詳しいご案内には常に「進めた場合の役割分担」
・2026-11-22-06：来期候補があると「来期に取りにいく候補」のページが増え、事前準備が簡易詳細に出て、「進める」で受け渡し箱に入る
・2026-11-22-04：「保留」「再検討」は計画書の記録だけで区別し、決裁の印は空（トライゲイトでは決裁待ち）
・2026-11-22-01：1ページ目に「AIアドバイス判定」の欄があり（11-22-03で改名）、「支給の決まり方」の欄は無い。［この制度の詳細］を押すと、判断材料と支給の決まり方が出る
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
     "判断材料": {"誰が": "試験の講師", "費用": "試験の費用"}, "AIアドバイス": {"整えること": ["試験の整えること"], "評価": [{"語": "試験の取りやすい", "良否": "良"}, {"語": "試験の負担大", "良否": "注意"}], "ひとこと": {"印": "◎", "見出し": "AIのイチオシ", "文": "試験の背中を押す一言"}, "札": ["期間が長い"], "項目": [{"名": "取りやすさ", "値": "高"}], "理由": "試験の理由", "次の一手": {"当社AI": ["試験のAI作業"], "御社": ["試験の御社作業"], "いつまでに": "試験の期限"}},
     "時系列": [{"時期": "2026-12-25", "内容": "締切"}], "出所": [{"名": "試験", "確認日": "2026-11-21"}]},
    {"id": "b", "名称": "試験の補助金B", "発出元": "国土交通省", "使い道": "試験", "獲得スケジュールの締切": "2027-09-30",
     "時系列": [{"時期": "2027-09-30", "内容": "申請"}]}
  ],
  "確認待ち": [{"項目": "試験の確認", "決まること": "試験", "確認先": "試験"}],
  "見送り": [{"名称": "試験の見送り", "理由": "試験", "次の機会": "—"}],
  "約束ごと": ["試験"]
}

async def drawn(pg):
    # 計画書のページが描かれるまで待つ（画面の描き替えの合図を待つ方式はヘッドレスで来ないことがあるため、一定間隔で数える）
    for _ in range(50):
        if await pg.evaluate("document.querySelectorAll('#out section.page').length") > 0: return
        await pg.wait_for_timeout(300)

async def load(pg, plan):
    # 計画データを、利用者と同じく「受給計画データを読み込む」からファイルとして読み込ませる
    import tempfile
    f = os.path.join(tempfile.mkdtemp(), 'test_受給計画.json')
    with open(f, 'w', encoding='utf-8') as w: json.dump(plan, w, ensure_ascii=False)
    await pg.set_input_files('#file', f); await drawn(pg)

async def test(p):
    s = Screen(); pg = await s.open(p, 'TriPlan.html')
    try:
        await pg.evaluate("localStorage.removeItem('triplan_last'); localStorage.removeItem('tritask_inbox'); localStorage.removeItem('tg_kessai'); localStorage.removeItem('triplan_decisions');")
        await load(pg, PLAN)
        n = await pg.evaluate("document.querySelectorAll('#out section.page').length")
        assert n == 5, '計画書のページ数が合いません（一覧・時系列・制度2件・確認待ちの5ページのはず）：%s' % n
        h1 = await pg.evaluate("document.querySelector('#out section.page table').rows[0].innerText")
        assert 'AIアドバイス（取るために整えること）' in h1 and '支給の決まり方' not in h1, '1ページ目の欄の見出しが「AIアドバイス（取るために整えること）」になっていません：' + h1
        t1 = await pg.evaluate("document.querySelector('#out section.page').innerText")
        assert '試験のAI作業' not in t1, '進める前なのに、判定の欄に次の一手が出ています'
        c0 = await pg.evaluate("document.querySelector('#out section.page table').rows[1].cells[0].innerText")
        c4 = await pg.evaluate("document.querySelector('#out section.page table').rows[1].cells[4].innerText")
        assert '試験の取りやすい' in c0 and '試験の負担大' in c0, '制度の欄の余白に「ひとことで」の札が出ていません'
        assert 'ひとことで' not in c4, 'AIアドバイスの欄に「ひとことで」が残っています'
        assert '◎' in c0 and 'AIのイチオシ' in c0 and '試験の背中を押す一言' in c0, '制度の欄に、おすすめの印と一言が出ていません'
        assert '試験の整えること' in t1 and 'お勧めします' not in t1, '取るために整えることが出ていない、または判定の札が残っています'
        assert '試験の理由' in t1 and '期間が長い' in t1 and '取りやすさ' in t1, 'AIアドバイス判定の結論・札・項目・理由が1ページ目に出ていません'
        await pg.click('button[data-dt="a"]'); await pg.wait_for_timeout(300)
        dt = await pg.evaluate("(document.querySelector('#out tr.dt')||{}).innerText||''")
        assert '試験の講師' in dt and '試験の先着' in dt, '［この制度の簡易詳細］を押しても、判断材料と支給の決まり方が出ません'
        assert '3ページ目' in dt, '簡易詳細に、詳しいご案内のページ番号が出ていません'
        await pg.click('button[data-id="a"][data-v="go"]'); await pg.wait_for_timeout(300)
        t1 = await pg.evaluate("document.querySelector('#out section.page').innerText")
        assert '試験のAI作業' in t1 and '試験の御社作業' in t1, '「進める」を押しても、次の一手（当社AI／御社）が出ません'
        assert '進めた場合の役割分担' in await pg.evaluate("document.getElementById('out').innerText"), '詳しいご案内に「進めた場合の役割分担」が出ていません'
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
        inbox = json.loads(await pg.evaluate("localStorage.getItem('tritask_inbox')") or '[]')
        assert not [x for x in inbox if x.get('id') == 'TP-TEST-01-b'], '進めるから見送るに変えても、手付かずのカードが受け渡し箱に残っています'
        tp = json.loads(await pg.evaluate("localStorage.getItem('triplan_last')") or '{}')
        assert tp.get('判断', {}).get('a') == 'go' and tp['判断'].get('b') == 'stop', '判断が計画データの中（判断）に書き込まれていません'
        await pg.click('button[data-id="b"][data-v="hold"]'); await pg.wait_for_timeout(300)
        ks = json.loads(await pg.evaluate("localStorage.getItem('tg_kessai')") or '{}')
        dc = json.loads(await pg.evaluate("localStorage.getItem('triplan_decisions')") or '{}')
        assert ks.get('TP-TEST-01-b') == '' and dc['試験交通株式会社']['b'] == 'hold', '「保留」で、計画書の記録が hold・決裁の印が空（決裁待ち）になりません'
        await pg.click('button[data-id="b"][data-v="rethink"]'); await pg.wait_for_timeout(300)
        dc = json.loads(await pg.evaluate("localStorage.getItem('triplan_decisions')") or '{}')
        assert dc['試験交通株式会社']['b'] == 'rethink', '「再検討」が計画書の記録に残りません'
        # 来期候補（2026-11-22-06）
        P2 = dict(PLAN); P2['来期候補'] = [{"id": "k", "名称": "試験の来期補助金", "発出元": "国土交通省", "使い道": "試験", "締切表示": "今期は終了",
            "獲得スケジュールの締切": "2027-02-12", "事前準備": [{"時期": "2027年1月", "内容": "試験の事前準備", "誰が": "御社"}],
            "AIアドバイス": {"整えること": ["試験の来期の整えること"], "理由": "試験"}}]
        await load(pg, P2)
        n = await pg.evaluate("document.querySelectorAll('#out section.page').length")
        assert n == 7, '来期候補があるときのページ数が合いません（来期の一覧と詳しいご案内で2ページ増えて7のはず）：%s' % n
        p2 = await pg.evaluate("document.querySelectorAll('#out section.page')[1].innerText")
        assert '来期に取りにいく候補' in p2 and '試験の来期補助金' in p2, '2ページ目に来期に取りにいく候補が出ていません'
        assert '試験の来期の整えること' in p2, '来期の候補に、取るために整えることが出ていません'
        await pg.click('button[data-dt="k"]'); await pg.wait_for_timeout(300)
        dt = await pg.evaluate("[].map.call(document.querySelectorAll('#out tr.dt'), function(e){ return e.innerText; }).join(' / ')")
        assert '試験の事前準備' in dt and '6ページ目' in dt, '来期候補の簡易詳細に事前準備、または正しいページ番号が出ていません：' + dt
        await pg.click('button[data-id="k"][data-v="go"]'); await pg.wait_for_timeout(300)
        inbox = json.loads(await pg.evaluate("localStorage.getItem('tritask_inbox')") or '[]')
        ck = [x for x in inbox if x.get('id') == 'TP-TEST-01-k']
        assert ck and ck[0]['deadlines'] == ['2027-02-12'], '来期候補の「進める」で受け渡し箱に入りません'
        assert not s.errs, '画面の中で誤りが出ています：' + ' / '.join(s.errs)
        await s.shot('#out', 'TriPlan_kessai.png')
    finally:
        await s.close()

if __name__ == '__main__':
    sys.exit(run(test))
