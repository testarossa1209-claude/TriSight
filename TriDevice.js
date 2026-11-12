/*! ===========================================================================
 *  TriDevice.js — 端末の札（2026-11-12 新設）
 *  ---------------------------------------------------------------------------
 *  宏史さんの決定（2026-11-12）：登録していない端末からの使用を検知して知らせる。
 *  ・この端末で初めて開いたときに、推測できない札（24文字）を作り、この端末に覚えさせる。
 *  ・中継（trisight-relay）へ認証コード付きで送る通信に、札（x-trisight-device）を添える。
 *  ・中継は札が登録済みかを照らし、未登録なら宏史さんへ知らせる（止めはしない）。
 *  ・札は認証コードとは無関係（札からコードは分からない）。
 *  各画面の <head> の最初の <script> として読み込む。
 * ========================================================================== */
(function () {
  'use strict';
  var K = 'trisight_device_id', id = '';
  try {
    id = localStorage.getItem(K) || '';
    if (!/^[a-z0-9]{16,40}$/.test(id)) {
      var a = 'abcdefghijkmnpqrstuvwxyz23456789', b = new Uint8Array(24);
      (window.crypto || window.msCrypto).getRandomValues(b);
      id = ''; for (var i = 0; i < b.length; i++) id += a[b[i] % a.length];
      localStorage.setItem(K, id);
    }
  } catch (e) { return; }
  window.TriDeviceId = id;
  var of = window.fetch;
  if (!of || of.__triDev) return;
  function hasCode(h) {
    if (!h) return false;
    if (typeof Headers !== 'undefined' && h instanceof Headers) return h.has('x-trisight-code');
    if (Array.isArray(h)) return h.some(function (p) { return String(p[0]).toLowerCase() === 'x-trisight-code'; });
    return Object.keys(h).some(function (k) { return k.toLowerCase() === 'x-trisight-code'; });
  }
  var w = function (input, init) {
    try {
      var url = typeof input === 'string' ? input : (input && input.url) || String(input || '');
      if (url.indexOf('trisight-relay.vercel.app') >= 0 && init && hasCode(init.headers)) {
        var h = init.headers, nh;
        if (typeof Headers !== 'undefined' && h instanceof Headers) { nh = new Headers(h); nh.set('x-trisight-device', id); }
        else if (Array.isArray(h)) { nh = h.concat([['x-trisight-device', id]]); }
        else { nh = {}; for (var k in h) nh[k] = h[k]; nh['x-trisight-device'] = id; }
        var ni = {}; for (var j in init) ni[j] = init[j]; ni.headers = nh;
        init = ni;
      }
    } catch (e) {}
    return of.call(this, input, init);
  };
  w.__triDev = 1;
  window.fetch = w;
})();
