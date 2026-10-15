# -*- coding: utf-8 -*-
"""トライサイト 関所の点検（2026-10-15）
二の関所＝機械の点検：版番号・戻るボタン・同じ中身のファイル・画面の書き込みの文法
三の関所＝宏史さんの確認：申請の本文の印3つと一行
使い方：python3 sekisho_check.py machine   /   python3 sekisho_check.py approval
"""
import glob, hashlib, json, os, re, subprocess, sys, tempfile

def fail(msgs):
    for m in msgs:
        print('NG：' + m)
    sys.exit(1)

# version.json の欄と画面ファイルの対応表。欄を足したらここにも足す（足さないと点検で止まる）
VERSION_MAP = {
    'trigate': 'TriGate.html', 'triform': 'TriForm.html', 'tritask': 'TriTask.html',
    'trisight': 'TriSight_v5.html', 'trisheet': 'TriSheet.html', 'trisight_auto': 'TriSight_v5_auto.html',
    'trirobo': 'TriRobo.html', 'report_business': 'TriSight_Report_Business.html',
    'tritime': 'TriTime.html', 'tricare_asm': 'TriCare_Assessment.html',
}
# 戻るボタンを付けない画面（表札そのものと、使っていない古い控え）
BACK_SKIP = {'index.html', 'TriBase_20260802.html', 'TriReward_kourei_20260802.html'}

def machine():
    ng = []
    # 1 版番号：version.json の版が、対応する画面の版表示と一致しているか
    v = json.load(open('version.json', encoding='utf-8'))
    for k, ver in v.items():
        f = VERSION_MAP.get(k)
        if not f:
            ng.append('version.json の「%s」に対応する画面が、点検の対応表にありません（.github/scripts/sekisho_check.py の VERSION_MAP に足してください）' % k); continue
        if not os.path.exists(f):
            ng.append('version.json の「%s」の画面 %s がありません' % (k, f)); continue
        s = open(f, encoding='utf-8').read()
        # 画面ごとに版の書き方が違う（版の表示欄・変数・画面の下の行）ので、版の文字そのものが画面に入っているかで見る
        if ver not in s:
            ng.append('%s に version.json の版「%s」が入っていません（画面の版を上げ忘れたか、version.json の書き換え忘れ）' % (f, ver))
    # 2 戻るボタン：表札以外の画面すべてにあるか
    for f in sorted(glob.glob('*.html')):
        if f in BACK_SKIP: continue
        if 'id="tsBackBar"' not in open(f, encoding='utf-8').read():
            ng.append('%s に「前のページに戻る」ボタンがありません' % f)
    # 3 同じ中身のファイルが2つないか（数値解析ロボ v2/v3 の再発防止）
    seen = {}
    for f in sorted(glob.glob('*.html') + glob.glob('*.js')):
        h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
        if h in seen:
            ng.append('%s と %s は中身が同じです。片方を直すともう片方と食い違うので、1つにまとめてください' % (seen[h], f))
        else:
            seen[h] = f
    # 4 画面の書き込みの文法：画面の中のプログラムと .js が、文法として読めるか
    tmp = tempfile.mkdtemp()
    for f in sorted(glob.glob('*.html')):
        s = open(f, encoding='utf-8').read()
        for i, (attrs, body) in enumerate(re.findall(r'<script([^>]*)>(.*?)</script>', s, re.S)):
            if 'src=' in attrs or not body.strip(): continue
            t = re.search(r'type="([^"]*)"', attrs)
            if t and t.group(1) not in ('text/javascript', 'application/javascript'): continue
            p = os.path.join(tmp, '%s_%d.js' % (f, i))
            open(p, 'w', encoding='utf-8').write(body)
            r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
            if r.returncode:
                ng.append('%s の中の %d 番目のプログラムに文法の誤りがあります：%s' % (f, i + 1, (r.stderr.strip().splitlines() or [''])[-1]))
    for f in sorted(glob.glob('*.js')):
        r = subprocess.run(['node', '--check', f], capture_output=True, text=True)
        if r.returncode:
            ng.append('%s に文法の誤りがあります：%s' % (f, (r.stderr.strip().splitlines() or [''])[-1]))
    if ng: fail(ng)
    print('OK：機械の点検はすべて通りました（版番号・戻るボタン・同じ中身のファイル・文法）')

def approval():
    body = os.environ.get('PR_BODY', '') or ''
    actor = os.environ.get('ACTOR', '')
    owner = os.environ.get('OWNER', '')
    ng = []
    body_nc = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    if re.search(r'^\s*- \[ \]', body_nc, re.M):
        ng.append('宏史さんの確認の印に、まだ付いていないものがあります')
    if len(re.findall(r'^\s*- \[[xX]\]', body_nc, re.M)) < 3:
        ng.append('宏史さんの確認の印が3つそろっていません')
    m = re.search(r'###\s*宏史さんの一行[^\n]*\n(.*)', body_nc, re.S)
    line = (m.group(1).strip() if m else '')
    if len(line) < 10:
        ng.append('「宏史さんの一行」が空か、短すぎます（何が変わるかを10文字以上で）')
    for sec in ('何を直したか', 'どの画面のどこが変わるか', '何を確かめたか', '確かめていないこと'):
        mm = re.search(r'##[^\n]*' + sec + r'[^\n]*\n(.*?)(?=\n##|\Z)', body_nc, re.S)
        if not mm or not mm.group(1).strip():
            ng.append('なぎさの欄「%s」が空です' % sec)
    if owner and actor and actor.lower() != owner.lower():
        ng.append('この点検を最後に動かしたのが宏史さん（%s）ではなく「%s」です。宏史さんが申請の本文を開いて保存し直すと、もう一度点検されます' % (owner, actor))
    if ng: fail(ng)
    print('OK：宏史さんの確認がそろいました')

if __name__ == '__main__':
    {'machine': machine, 'approval': approval}[sys.argv[1]]()
