# -*- coding: utf-8 -*-
"""実験機の合言葉の画面の試験（2026-11-09・宏史さん「ログイン画面の反応が悪い件は直ってませんね」＝デモ機の野木タブレット・実験機）
・実験機の合言葉の画面は、本体の中身（名簿・設定の「保存」のボタンなど）を読み込む前に出る（本体を全部読み終えるまで空白にしない）
・違う合言葉では開かず「合言葉が違います。」と出る。正しい合言葉で開き、本体の画面が見える"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import run, ROOT, SHOTS

SALT, PW = 'shiken', 'lab-pass'
HASH = hashlib.sha256(('tritime-lab:%s:%s' % (SALT, PW)).encode()).hexdigest()

async def test(p):
    b = await p.chromium.launch(channel='chrome', args=['--no-sandbox'])
    try:
        pg = await (await b.new_context(viewport={'width': 1024, 'height': 768})).new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script("""localStorage.setItem('trisight_access_code','TEST');localStorage.setItem('trisight_open_tritime','1');localStorage.setItem('trisight_open_tritime_code','TEST');
          localStorage.setItem('tritime_devmode', %s);
          new MutationObserver(function(){ if(window.__lab == null && document.getElementById('labLock')) window.__lab = !!document.getElementById('dv_save'); }).observe(document, {childList:true, subtree:true});"""
          % json.dumps(json.dumps({'mode': 'lab', 'salt': SALT, 'hash': HASH})))
        await pg.goto('file://' + os.path.join(ROOT, 'TriTime.html')); await pg.wait_for_timeout(1500)
        early = await pg.evaluate('window.__lab')
        assert early is False, '実験機の合言葉の画面が、本体の中身を読み込んだ後に出ています（出るまで空白になります）：' + str(early)
        assert await pg.is_visible('#labLockPw'), '実験機の合言葉の欄が見えません'
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True); await pg.screenshot(path=os.path.join(SHOTS, 'TriTime_lablock.png'))
        await pg.fill('#labLockPw', 'chigau'); await pg.click('#labLockGo'); await pg.wait_for_timeout(400)
        assert '合言葉が違います' in await pg.inner_text('#labLockMsg'), '違う合言葉で「合言葉が違います。」が出ません'
        assert await pg.query_selector('#labLock'), '違う合言葉で開いてしまいます'
        await pg.fill('#labLockPw', PW); await pg.press('#labLockPw', 'Enter'); await pg.wait_for_timeout(600)
        assert not await pg.query_selector('#labLock'), '正しい合言葉で開きません'
        assert await pg.is_visible('#tabs'), '開いた後に本体の画面（上のタブ）が見えません'
        assert not errs, '画面の中で誤りが出ました：' + errs[0]
    finally:
        await b.close()

if __name__ == '__main__':
    sys.exit(run(test))
