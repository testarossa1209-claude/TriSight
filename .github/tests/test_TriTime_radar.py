# -*- coding: utf-8 -*-
"""トライタイムの会社評価のレーダーチャートの試験（2026-11-03・宏史さん「野木画面の職員評価にはレーダーチャートなども入れてほしい」）
野木画面はゼウスキーが無いと開けないため、画面の中の描く部品（ceAxes・ceRadarSVG・ceRadarHTML）を取り出して、見本の基準と点で描かせて確かめる。
・区分（業績・専門性・行動・姿勢・組織への貢献）ごとに、重み付きの平均が軸に出る
・この職員の形（塗り）・平均の点線・「3 期待どおり」の線が出る
・区分が3つ未満のときは項目ごとの軸になる"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, ROOT

def grab(src, name):
    i = src.index('function ' + name + '(')
    depth = 0; j = src.index('{', i)
    for k in range(j, len(src)):
        if src[k] == '{': depth += 1
        elif src[k] == '}':
            depth -= 1
            if depth == 0: return src[i:k + 1]
    raise Exception(name)

async def test(p):
    src = open(os.path.join(ROOT, 'TriTime.html'), encoding='utf-8').read()
    m = re.search(r'var CE_DEF = \{.*?\] \};', src, re.S)
    assert m, '評価の基準の見本（CE_DEF）が見つかりません'
    code = m.group(0) + '\nvar evCfgCache = null, CE_AVG = null;\nfunction ceCfg(){ return evCfgCache || CE_DEF; }\n' + \
        'function esc(s){ return String(s == null ? "" : s).replace(/[&<>"]/g, function(c){ return { "&":"&amp;", "<":"&lt;", ">":"&gt;", \'"\':"&quot;" }[c]; }); }\n' + \
        '\n'.join(grab(src, n) for n in ['ceAxes', 'ceRadarSVG', 'ceRadarHTML']) + '\nwindow.__r = { ceAxes:ceAxes, ceRadarHTML:ceRadarHTML, set:function(c, a){ evCfgCache = c; CE_AVG = a; } };'
    s = Screen(); pg = await s.open(p, 'TriTime.html', w=1100, h=900)
    try:
        await pg.add_script_tag(content=code)
        ax = await pg.evaluate("__r.ceAxes({ scores:{ a1:5, a2:3, a3:4, b1:4, c1:2, c2:2, d1:5 } }).map(function(a){ return a.t + '=' + (a.v == null ? '-' : a.v.toFixed(2)); })")
        assert ax == ['業績=4.25', '専門性=4.00', '行動・姿勢=2.00', '組織への貢献=5.00'], '区分ごとの重み付きの平均が正しくありません：' + str(ax)
        await pg.evaluate("__r.set(null, { v:{ '業績':3.5, '専門性':3, '行動・姿勢':3.2, '組織への貢献':2.5 }, n:6 })")
        await pg.evaluate("(function(){ var d = document.createElement('div'); d.id = 'rdT'; d.style.cssText = 'background:#fff;padding:12px;width:720px;position:relative;z-index:99999'; d.innerHTML = '<h3>会社評価をつける（レーダーチャート）</h3>' + __r.ceRadarHTML({ scores:{ a1:5, a2:3, a3:4, b1:4, b2:3, b3:4, c1:2, c2:2, c3:3, c4:5, d1:5, d2:4, d3:4 } }); document.body.prepend(d); })()")
        n = await pg.evaluate("document.querySelectorAll('#rdT svg polygon').length")
        assert n == 7, 'レーダーチャートの線（目盛り5本・平均・この職員）が出ません：' + str(n)
        tx = await pg.inner_text('#rdT')
        assert '業績' in tx and '組織への貢献' in tx and '平均（同じ期間に点のある 6人）' in tx, '軸の名前や平均の説明が出ません：' + tx[:200]
        await s.shot('#rdT', 'TriTime_radar.png')
        k = await pg.evaluate("(function(){ __r.set({ items:[{ id:'q1', g:'A', t:'一', w:1 }, { id:'q2', g:'A', t:'二', w:1 }, { id:'q3', g:'B', t:'三', w:1 }], classes:[{ n:'A', min:0 }] }, null); return __r.ceAxes({ scores:{ q1:4 } }).map(function(a){ return a.t; }); })()")
        assert k == ['一', '二', '三'], '区分が3つ未満のとき、項目ごとの軸になりません：' + str(k)
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
