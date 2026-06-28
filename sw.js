// TriGate Service Worker（最小構成）
// 目的：PWAとしてインストール可能にし、File Handling を有効にするための最低限。
// キャッシュは持たず、ネットワークへ素通しする（API・PDF処理は常に最新で動かす）。
const VERSION = 'trigate-v0.2.0';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (e) => {
  // 素通し。オフライン対応は持たない（補助金処理はオンライン前提）。
  e.respondWith(fetch(e.request).catch(() => new Response('オフラインです。接続を確認してください。', {
    status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' }
  })));
});
