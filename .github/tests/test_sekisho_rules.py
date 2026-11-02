# -*- coding: utf-8 -*-
"""関所の決まりの試験（2026-11-02）
・Merge前に人が実機で試す欄はやめた：その欄が無くても、結果が空でも止まらない
・なぎさの欄が空なら止まる／写しが無ければ止まる／印が3つそろわなければ確認待ち"""
import sys, os
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import sekisho_check as K

OK3 = '\n## 三　宏史さんの確認\n- [x] 変わる画面を開いて見た\n- [x] 「確かめていないこと」を読んだ\n- [x] 今、本番に出してよい時期だ\n'
BASE = ('## 一　何を直したか\nあ\n## 一　どの画面のどこが変わるか\nい\n## 一　何を確かめたか\nう\n## 一　確かめていないこと\n無し（理由）\n'
        '## 一　画面の写し\n![a](https://raw.githubusercontent.com/x/y/sekisho-shots/a.png)\n')

def main():
    ng, wt = K.judge_body(BASE + '## 一　公開後に試すこと\n・iPadに届くか（島さん）結果：\n' + OK3, ['TriTime.html'])
    assert not ng and not wt, '公開後だけ空の申請が止まっています：%s %s' % (ng, wt)
    ng, wt = K.judge_body(BASE + '## 一　実機で試すこと\n・iPadで試す（島さん）結果：\n' + OK3, ['TriTime.html'])
    assert not ng and not wt, '古い「実機で試すこと」の空欄で止まっています：%s %s' % (ng, wt)
    ng, wt = K.judge_body(BASE.replace('う\n', '\n') + OK3, [])
    assert any('何を確かめたか' in n for n in ng), 'なぎさの欄が空なのに止まりません'
    ng, wt = K.judge_body(BASE.replace('![a](https://raw.githubusercontent.com/x/y/sekisho-shots/a.png)', '写しです') + OK3, [])
    assert any('画面の写し' in n for n in ng), '写しが無いのに止まりません'
    ng, wt = K.judge_body(BASE + OK3.replace('- [x] 今', '- [ ] 今'), [])
    assert any('印' in w for w in wt), '印がそろっていないのに確認待ちになりません'
    print('OK')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except AssertionError as e:
        print('NG：' + str(e)); sys.exit(1)
