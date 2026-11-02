# -*- coding: utf-8 -*-
"""試し版を作る（2026-11-02・宏史さんの了承「公開前に試すこと」）
申請中の画面を、本番（github.io）とは別の住所＝中継の住所の下（https://trisight-relay.vercel.app/preview/枝の名前/）に置くための一式を作る。
・住所が本番と違うので、端末の中の記録（localStorage など）は本番と混ざらない
・中継と同じ住所なので、開くときの認証（portal）や書類の読み取りは、中継の許可を足さずに通る
・本番の共有記録へ書き込む用件（task が tritime のもの＝共有・開いている人・利用者ごとの鍵）は、試し版の先頭に入れた囲いで止める
・画面の上に「試し版」の赤い帯を出す
使い方：python3 .github/scripts/preview_build.py 枝の名前 出力先 画面.html [画面.html ...]
  画面が読む付属のファイル（同じ階層の .js .json .png）も一緒に写す。サービスワーカー（sw.js）は写さない"""
import os, re, shutil, sys

GUARD = '''<script>/* 試し版の囲い（.github/scripts/preview_build.py が入れたもの。本番の画面には入っていない） */
(function(){
  var of = window.fetch;
  window.fetch = function(u, o){
    try{ var b = o && o.body; if(typeof b === 'string' && /"task"\\s*:\\s*"tritime"/.test(b)){
      return Promise.resolve(new Response(JSON.stringify({ error:'試し版では、本番の共有記録への書き込みを止めています' }), { status:503, headers:{ 'Content-Type':'application/json' } }));
    } }catch(e){}
    return of.apply(this, arguments);
  };
  try{ if(navigator.serviceWorker) navigator.serviceWorker.register = function(){ return Promise.reject(new Error('試し版ではサービスワーカーを使いません')); }; }catch(e){}
  document.addEventListener('DOMContentLoaded', function(){
    var d = document.createElement('div');
    d.textContent = '試し版（申請中：__BRANCH__）— 本番とは別の記録です。ここで入れた内容は本番には届かず、ほかの端末とも共有されません。';
    d.style.cssText = 'position:sticky;top:0;z-index:2147483647;background:#b0402f;color:#fff;padding:8px 12px;font:bold 14px/1.5 sans-serif;text-align:center';
    document.body.insertBefore(d, document.body.firstChild);
  });
})();
</script>
'''

def main():
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(2)
    branch, out, pages = sys.argv[1], sys.argv[2], sys.argv[3:]
    os.makedirs(out, exist_ok=True)
    deps = set()
    for page in pages:
        s = open(page, encoding='utf-8').read()
        g = GUARD.replace('__BRANCH__', branch)
        m = re.search(r'<head[^>]*>', s, re.I)
        s = (s[:m.end()] + '\n' + g + s[m.end():]) if m else g + s
        open(os.path.join(out, os.path.basename(page)), 'w', encoding='utf-8').write(s)
        for ref in re.findall(r'(?:src|href)="([^"#?:]+\.(?:js|json|png|ico|css))"', s):
            if '/' not in ref and ref != 'sw.js':
                deps.add(ref)
    for f in sorted(deps):
        if os.path.exists(f):
            shutil.copy(f, os.path.join(out, f))
    print('試し版を作りました：%s（画面 %d・付属 %d）' % (out, len(pages), len(deps)))

if __name__ == '__main__':
    main()
