/*! ===========================================================================
 *  TriDevice.js — 端末の札（2026-11-12 新設）
 *  ---------------------------------------------------------------------------
 *  宏史さんの決定（2026-11-12）：登録していない端末からの使用を検知して知らせる。
 *  ・この端末で初めて開いたときに、推測できない札（24文字）を作り、この端末に覚えさせる。
 *  ・中継（trisight-relay）へ認証コード付きで送る通信に、札（x-trisight-device）を添える。
 *  ・中継は札が登録済みかを照らし、未登録なら宏史さんへ知らせる（止めはしない）。
 *  ・札は認証コードとは無関係（札からコードは分からない）。
 *  ・2026-11-12 改2（宏史さんの決定）：未登録の端末は中継が止める（403・device）。
 *    止められたら、この部品が画面全体に案内を出す（各画面は変えない）。
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
    var isRelay = false;
    try { isRelay = (typeof input === 'string' ? input : (input && input.url) || '').indexOf('trisight-relay.vercel.app') >= 0; } catch (e) {}
    var p = of.call(this, input, init);
    if (!isRelay) return p;
    return p.then(function (res) {
      try {
        if (res && res.status === 403) {
          res.clone().json().then(function (j) { if (j && (j.device === 'unregistered' || j.device === 'notag')) showBlocked(j); }, function () {});
        }
      } catch (e) {}
      return res;
    });
  };
  function showBlocked(j) {
    try {
      if (document.getElementById('triDeviceBlocked')) return;
      var w = document.createElement('div'); w.id = 'triDeviceBlocked';
      w.setAttribute('style', 'position:fixed;inset:0;background:rgba(15,29,58,.72);z-index:2147483647;display:flex;align-items:center;justify-content:center;padding:16px;box-sizing:border-box;font-family:inherit');
      var t = new Date(), hm = ('0' + t.getHours()).slice(-2) + ':' + ('0' + t.getMinutes()).slice(-2);
      var head = j.device === 'unregistered' ? 'この端末は登録されていません' : '画面を開き直してください';
      w.innerHTML = '<div style="background:#fff;border-radius:12px;max-width:440px;width:100%;padding:22px 20px 16px;box-sizing:border-box;color:#16213a;line-height:1.7">'
        + '<div style="font-weight:700;font-size:17px;margin-bottom:8px">' + head + '</div>'
        + '<div style="font-size:14px;color:#3d4660"></div>'
        + '<div style="font-size:12px;color:#5b6680;margin-top:8px">止められた時刻：' + hm + '</div>'
        + '<div style="text-align:right;margin-top:12px"><button type="button" style="font-family:inherit;font-size:14px;padding:7px 18px;border:0;background:#0f1d3a;color:#fff;border-radius:999px;cursor:pointer">開き直す</button></div></div>';
      w.querySelector('div div:nth-child(2)').textContent = j.error || '';
      w.querySelector('button').onclick = function () { location.reload(); };
      (document.body || document.documentElement).appendChild(w);
    } catch (e) {}
  }
  w.__triDev = 1;
  window.fetch = w;
})();
