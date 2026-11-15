# -*- coding: utf-8 -*-
"""トライタイムの音声メモと、録音の取り消し3つの試験（2026-11-15・宏史さんの指示）
・利用者経過の「音声メモを残す」に、運転中は使わない注意と「🎤 話して入力」がある。話した文字が欄に入り、「音声メモとして残す」で残る
・録音中は「取り消す」が出る。押すと文字は入らず、「元に戻す」を押すと入る
・文字が入ると「今入れた分を取り消す」が出て、押すと直前に入った分だけ消える
・「要約して振り分ける」でAIの要約が「今日やったこと・次回の約束」に下書きされ、「記録する」でメモが振り分け済みになる
（試し用のブラウザの作り物のマイクを使い、文字起こしとAIの返事は試験の側で決まった答えを返す）"""
import sys, os, json, asyncio
sys.path.insert(0, os.path.dirname(__file__))
from tt_helper import Screen, run, ROOT, SHOTS

SEED = """(function(){
  var up = Date.now();
  var ST = [ { id:'s1', name:'常勤 一子', emp:'常勤', job:'看護師（正看）', dept:'訪問看護部', off:['0'], upd:up },
    { id:'s9', name:'卜部 五子', emp:'常勤', job:'事務局', dept:'経営企画事務職', off:['0'], upd:up } ];
  var P = [ { no:'2010-01-看-9001', name:'試験 太郎', area:'東町', status:'利用中', ins:'精神科訪問看護（医療）', freq:'週2回', upd:up } ];
  localStorage.setItem('tritime_staff', JSON.stringify(ST)); localStorage.setItem('tritime_patients', JSON.stringify(P)); localStorage.setItem('tritime_weekly', '[]');
  localStorage.setItem('tritime_events', '[]'); localStorage.setItem('tritime_settings', JSON.stringify({ work:{} }));
  localStorage.setItem('tritime_device', JSON.stringify({ me:'s9', share:true })); localStorage.setItem('tritime_dept', 'nurse');
})()"""
SAID = '血圧は130の80。足のむくみが少しあり。次回は爪切りをする。'
AI = {'did': '・血圧130/80\n・足のむくみが少しある', 'next': '爪切りをする'}
VMS = "() => JSON.parse(localStorage.getItem('tritime_events') || '[]').filter(e => e && e.type === 'vmemo')"

class MicScreen(Screen):
    async def open(self, p, name, w=1200, h=1000):
        self.b = await p.chromium.launch(channel='chrome', args=['--no-sandbox', '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        ctx = await self.b.new_context(viewport={'width': w, 'height': h})
        await ctx.grant_permissions(['microphone'])
        self.pg = pg = await ctx.new_page()
        self.errs = []; pg.on('pageerror', lambda e: self.errs.append(str(e)))
        self.dialogs = []
        def on_dialog(d):
            self.dialogs.append(d.message); asyncio.ensure_future(d.accept())
        pg.on('dialog', on_dialog)
        async def gate(route):
            await route.fulfill(status=200, content_type='application/json', body=json.dumps({'portal': True, 'ok': True, 'items': [], 'records': []}))
        async def stt(route):
            await route.fulfill(status=200, content_type='application/json', body=json.dumps({'text': SAID}))
        async def ai(route):
            await route.fulfill(status=200, content_type='application/json', body=json.dumps({'content': [{'type': 'text', 'text': json.dumps(AI, ensure_ascii=False)}]}))
        await pg.route('**/api/gate', gate); await pg.route('**/api/transcribe', stt); await pg.route('**/api/anthropic', ai)
        await pg.add_init_script("localStorage.setItem('trisight_access_code','TEST');window.prompt=()=>'TEST';")
        await pg.goto('file://' + os.path.join(ROOT, name)); await pg.wait_for_timeout(800)
        if await pg.query_selector('#ogGo'):
            await pg.click('#ogGo'); await pg.wait_for_timeout(2500)
        return pg

async def mic(pg):
    return await pg.query_selector('#vmCard .tv-fm-btn')

async def test(p):
    s = MicScreen(); pg = await s.open(p, 'TriTime.html')
    try:
        await pg.evaluate(SEED); await pg.reload(); await pg.wait_for_timeout(2000)
        await pg.evaluate("document.querySelector('#tabs button[data-tab=course]').click()"); await pg.wait_for_timeout(400)
        await pg.select_option('#k_no', '2010-01-看-9001'); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('vmCard').open = true"); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#vmCard')
        assert '走っている間はトライタイムを使わないでください' in t, '運転中は使わない注意が出ません'
        b = await mic(pg); assert b, '音声メモの欄に「話して入力」がありません'
        # ① 録音中の「取り消す」→ 入らない → 「元に戻す」で入る
        await b.click(); await pg.wait_for_timeout(1200)
        assert await pg.query_selector('#tvCancel'), '録音中に「取り消す」が出ません'
        await s.shot('.tv-act', 'TriTime_onsei_cancel.png')
        await pg.click('#tvCancel'); await pg.wait_for_timeout(1000)
        assert await pg.input_value('#vm_text') == '', '取り消したのに文字が入りました'
        assert await pg.query_selector('#tvRedo'), '取り消したあとに「元に戻す」が出ません'
        await pg.click('#tvRedo'); await pg.wait_for_timeout(1200)
        assert SAID in await pg.input_value('#vm_text'), '「元に戻す」で取り消した録音が入りません'
        # ② 今入れた分を取り消す（2回目に入れた分だけ消える）
        b = await mic(pg); await b.click(); await pg.wait_for_timeout(1000); b = await mic(pg); await b.click(); await pg.wait_for_timeout(1500)
        v2 = await pg.input_value('#vm_text'); assert v2.count(SAID) == 2, '2回目の分が入りません：' + v2
        assert await pg.query_selector('#tvUndoIns'), '「今入れた分を取り消す」が出ません'
        await s.shot('.tv-act', 'TriTime_onsei_undo.png')
        await pg.click('#tvUndoIns'); await pg.wait_for_timeout(400)
        assert (await pg.input_value('#vm_text')).count(SAID) == 1, '直前に入った分だけが消えません'
        # ③ 残す → 要約して振り分ける → 記録する
        await pg.select_option('#vm_by', 's1')
        await pg.click('#vm_save'); await pg.wait_for_timeout(500)
        v = await pg.evaluate(VMS); assert len(v) == 1 and v[0]['st'] == '未振り分け', '音声メモが残りません：' + str(v)
        await pg.evaluate("document.getElementById('vmSort').open = true"); await pg.wait_for_timeout(300)
        await s.shot('#vmCard', 'TriTime_onsei_memo.png')
        await pg.click('[data-vmgo]'); await pg.wait_for_timeout(1500)
        assert await pg.input_value('#p_did') == AI['did'] and await pg.input_value('#p_next') == AI['next'], '要約が「今日やったこと・次回の約束」に入りません'
        await s.shot('#dPromise', 'TriTime_onsei_furiwake.png')
        await pg.click('#p_save'); await pg.wait_for_timeout(600)
        v = await pg.evaluate(VMS); assert v[0]['st'] == '振り分け済み', '記録してもメモが振り分け済みになりません：' + str(v)
        ev = await pg.evaluate("() => JSON.parse(localStorage.getItem('tritime_events')).filter(e => e.type === 'promise')")
        assert len(ev) == 1 and ev[0]['next'] == AI['next'], '経過に記録されません：' + str(ev)
        assert not s.errs, '画面の中で誤りが出ました：' + s.errs[0]
    finally:
        await s.close()

sys.exit(run(test))
