# -*- coding: utf-8 -*-
"""トライサイト 関所の点検（2026-10-15 作成／同日 改め）
二の関所＝機械の点検：版番号・戻るボタン・同じ中身のファイル・画面の書き込みの文法
三の関所＝宏史さんの確認：申請の本文の印3つ（一行はやめた）
止まった理由は、申請の画面の点検一覧に「関所の理由（…）」として出す（メールは出さない）。
三の点検が通ったとき（二も通っているとき）だけ、申請に「通りました」と書き込む。
使い方：python3 sekisho_check.py machine   /   python3 sekisho_check.py approval
"""
import glob, hashlib, json, os, re, subprocess, sys, tempfile, urllib.request

SUCCESS_MARK = '<!-- sekisho-tsuuka -->'

def gh(method, path, data=None):
    token = os.environ.get('GITHUB_TOKEN'); repo = os.environ.get('REPO')
    if not token or not repo:
        return None
    req = urllib.request.Request('https://api.github.com/repos/%s%s' % (repo, path), method=method,
        data=(json.dumps(data).encode('utf-8') if data is not None else None),
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'Content-Type': 'application/json', 'User-Agent': 'trisight-sekisho'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode('utf-8') or 'null')
    except Exception as e:
        print('（知らせの書き込みに失敗：%s）' % e)
        return None

def show_reason(label, msgs):
    """止まった理由を、申請の画面の点検一覧に1行で出す（メールは出ない）"""
    sha = os.environ.get('HEAD_SHA')
    if not sha:
        return
    ok = not msgs
    title = 'すべて通りました' if ok else msgs[0] + ('（ほか%d件）' % (len(msgs) - 1) if len(msgs) > 1 else '')
    summary = '\n'.join('・' + m for m in msgs) if msgs else 'すべて通りました。'
    gh('POST', '/check-runs', {'name': '関所の理由（%s）' % label, 'head_sha': sha, 'status': 'completed',
        'conclusion': 'success' if ok else 'failure', 'output': {'title': title[:250], 'summary': summary}})

def notify_pass():
    """二と三がそろって通ったときだけ、申請に「通りました」と書き込む（同じ版には一度だけ）"""
    n = os.environ.get('PR_NUMBER'); sha = os.environ.get('HEAD_SHA', '')
    if not n:
        return
    mark = SUCCESS_MARK + '<!-- %s -->' % sha
    for c in (gh('GET', '/issues/%s/comments?per_page=100' % n) or []):
        if mark in (c.get('body') or ''):
            return
    gh('POST', '/issues/%s/comments' % n, {'body': mark + '\n関所を通りました。「Merge pull request」を押せます。'})

def fail(msgs, label):
    for m in msgs:
        print('NG：' + m)
    show_reason(label, msgs)
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

def machine_ng():
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
    return ng

def machine():
    ng = machine_ng()
    if ng: fail(ng, '機械の点検')
    show_reason('機械の点検', [])
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
    for sec in ('何を直したか', 'どの画面のどこが変わるか', '何を確かめたか', '確かめていないこと'):
        mm = re.search(r'##[^\n]*' + sec + r'[^\n]*\n(.*?)(?=\n##|\Z)', body_nc, re.S)
        if not mm or not mm.group(1).strip():
            ng.append('なぎさの欄「%s」が空です' % sec)
    if owner and actor and actor.lower() != owner.lower():
        ng.append('この点検を最後に動かしたのが宏史さん（%s）ではなく「%s」です。宏史さんが「三」の印を1つ外して付け直すと、もう一度点検されます' % (owner, actor))
    if ng: fail(ng, '宏史さんの確認')
    # 三が通っても、二（機械の点検）が通っていなければ「通りました」は出さない
    mng = machine_ng()
    if mng: fail(['機械の点検が通っていません：' + mng[0]], '宏史さんの確認')
    show_reason('宏史さんの確認', [])
    notify_pass()
    print('OK：宏史さんの確認がそろいました')

if __name__ == '__main__':
    {'machine': machine, 'approval': approval}[sys.argv[1]]()
