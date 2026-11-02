# -*- coding: utf-8 -*-
"""関所の決まりの試験（2026-11-02・公開前／公開後に分けた改め）
・公開前に試すことの結果が空なら、確認待ちで止まる（古い書き方「実機で試すこと」も同じ）
・公開後に試すことの結果が空でも、Merge は止めない
・画面を変えた申請で、公開前に試すことに試し版の住所が無ければ止める（画面を変えない申請は「無し」で通る）
・すべてそろえば止まらない
・試し版の囲い：本番の共有記録への書き込み（task が tritime）は止まり、開くときの認証（portal）は通り、赤い帯が出る"""
import sys, os, tempfile, subprocess
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
sys.path.insert(0, HERE)
import sekisho_check as K
from tt_helper import Screen, run, IPAD

OK3 = '\n## 三　宏史さんの確認\n- [x] 変わる画面を開いて見た\n- [x] 「確かめていないこと」を読んだ\n- [x] 今、本番に出してよい時期だ\n'
BASE = ('## 一　何を直したか\nあ\n## 一　どの画面のどこが変わるか\nい\n## 一　何を確かめたか\nう\n## 一　確かめていないこと\n無し（理由）\n'
        '## 一　画面の写し\n![a](https://raw.githubusercontent.com/x/y/sekisho-shots/a.png)\n')
URL = 'https://trisight-relay.vercel.app/preview/nagisa-x/TriTime.html'

def rules():
    ng, wt = K.judge_body(BASE + '## 一　公開前に試すこと\n' + URL + '\n・ノアPCで試す（渋谷さん）結果：\n## 一　公開後に試すこと\n・iPadに届くか（島さん）結果：\n' + OK3, ['TriTime.html'])
    assert not ng and any('公開前に試すことの結果' in w for w in wt), '公開前の結果が空なのに確認待ちになりません：%s %s' % (ng, wt)
    assert not any('公開後' in w for w in wt), '公開後の結果が空なだけで止まっています：%s' % wt
    ng, wt = K.judge_body(BASE + '## 一　公開前に試すこと\n' + URL + '\n・ノアPCで試す（渋谷さん）結果：並んだ\n## 一　公開後に試すこと\n・iPadに届くか（島さん）結果：\n' + OK3, ['TriTime.html'])
    assert not ng and not wt, '公開前がそろい、公開後だけ空の申請が止まっています：%s %s' % (ng, wt)
    ng, wt = K.judge_body(BASE + '## 一　公開前に試すこと\n・ノアPCで試す（渋谷さん）結果：並んだ\n' + OK3, ['TriTime.html'])
    assert any('試し版の住所' in n for n in ng), '画面を変えたのに試し版の住所が無い申請が通っています'
    ng, wt = K.judge_body(BASE + '## 一　公開前に試すこと\n無し（画面を変えない申請）\n' + OK3, [])
    assert not ng and not wt, '画面を変えない申請が「無し」で通りません：%s %s' % (ng, wt)
    ng, wt = K.judge_body(BASE + '## 一　実機で試すこと\n・iPadで試す（島さん）結果：\n' + OK3, [])
    assert any('公開前に試すことの結果' in w for w in wt), '古い書き方「実機で試すこと」の空欄で止まりません'
    ng, wt = K.judge_body(BASE + OK3, [])
    assert any('公開前に試すこと」が空' in n for n in ng), '公開前に試すことの欄が無い申請が通っています'

async def test(p):
    rules()
    root = os.path.abspath(os.path.join(HERE, '..', '..'))
    out = tempfile.mkdtemp()
    subprocess.run([sys.executable, os.path.join(root, '.github', 'scripts', 'preview_build.py'), 'nagisa-test', out, 'TriTime.html'], cwd=root, check=True, capture_output=True)
    assert os.path.exists(os.path.join(out, 'TriVoiceEngine.js')) and not os.path.exists(os.path.join(out, 'sw.js')), '試し版に付属のファイルが揃っていない、またはサービスワーカーが写っています'
    s = Screen(); pg = await s.open(p, os.path.join(out, 'TriTime.html'), ua=IPAD)
    try:
        assert '試し版' in await pg.inner_text('body'), '試し版の赤い帯が出ません'
        r = await pg.evaluate("""Promise.all([
          fetch('https://trisight-relay.vercel.app/api/gate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:'tritime',payload:{op:'push',items:[]}})}).then(r=>r.status),
          fetch('https://trisight-relay.vercel.app/api/gate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:'portal',payload:{product:'tritime'}})}).then(r=>r.status)])""")
        assert r[0] == 503, '試し版で、本番の共有記録への書き込みが止まりません（%s）' % r[0]
        assert r[1] == 200, '試し版で、開くときの認証まで止まっています（%s）' % r[1]
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
