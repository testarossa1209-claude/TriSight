// TriGate Service Worker
// 目的：PWAとしてインストール可能にし、File Handling を有効にするための最低限。
// キャッシュは持たず、ネットワークへ素通しする（API・PDF処理は常に最新で動かす）。
//
// 2026-07-27 変更：VERSIONの手動更新を不要にした。
//   旧版は「TriGate.htmlを更新するたびにこのVERSIONを書き換えること」を人の記憶に頼っており、
//   書き換えを忘れると鳥居アイコンが古い版のまま固定される（2026-07-22に一度発生、07-27に再発）。
//   忘れたら黙って壊れる仕組みそのものが誤りだったため、
//   当アプリ自身のHTML・JS・JSONについてはHTTPキャッシュを迂回して常に取り直す方式へ変更する。
//   これにより、GitHubへ上げた内容が次回起動時に必ず反映される。VERSIONは識別用に残すのみ。
const VERSION = 'trigate-v0.3.0-20260727';

// キャッシュを迂回して取り直す対象（同一オリジンの、このアプリ自身のファイル）
function mustBeFresh(request){
  if(request.method !== 'GET') return false;
  if(request.mode === 'navigate') return true;          // ページそのもの
  try{
    const url = new URL(request.url);
    if(url.origin !== self.location.origin) return false; // 外部CDN等は対象外
    return /\.(html|js|json)$/i.test(url.pathname);
  }catch(e){ return false; }
}

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const offline = () => new Response('オフラインです。接続を確認してください。', {
    status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' }
  });

  if(mustBeFresh(req)){
    // cache:'reload' ＝ HTTPキャッシュを読まずネットワークへ取りに行き、結果でキャッシュを更新する
    e.respondWith(
      fetch(req, { cache: 'reload' })
        .catch(() => fetch(req).catch(offline))   // 取り直しに失敗したら通常取得、それも駄目ならオフライン表示
    );
    return;
  }

  e.respondWith(fetch(req).catch(offline));
});
