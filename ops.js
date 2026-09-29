// ============================================================
// TriSight リレー ― トライサイト オペレーションシステムの口　ファイル名: api/ops.js（2026-09-29 改2）
// ------------------------------------------------------------
// 当社専用。管理用コード（TRISIGHT_ADMIN_CODE）でだけ通る。画面は TriOps.html。
// 画面は公開しない（トライサイトPC・ラップトップ・SSDにだけ置き、ファイルを直接開く）。
//   → ファイルを直接開いた画面からの呼び出し（出どころ "null"）にだけ応じる。
//     GitHub Pages など公開の場所からの呼び出しには応じない（2026-09-29 宏史さんの決定）。
// 契約先・認証コード・AI構成・トークン利用・自動発掘の登録を、1か所で見て操作する。
// 操作（op）：
//   all            … 一覧をまとめて返す（契約先・コード・使用量・上限・AI構成・自動発掘）
//   saveContract   … 契約先を登録／更新（契約管理番号は空なら自動で振る）
//   issueCode      … 契約先に新しい認証コードを発行（消去コードも同時に発行）
//   attachCode     … Vercelの設定にある既存のコードを契約先に紐づける
//   setCodeStatus  … コードを停止／再開（管理用コードは止められない）
//   reissueErase   … 消去コードを再発行
//   setLimit       … 月間トークン上限（空欄で上限なし）
//   setPicks / delPicks … AIの組み合わせ（プロバージョン）
// ============================================================
import { isAdminCode, envCodes, listContracts, listCodeRecords, saveContract, issueCode, attachCode,
         setCodeStatus, reissueErase, redis } from '../lib/codes.js';
import { readCode, setLimit } from '../lib/usageStore.js';
import { aiPicks, setPicks, delPicks } from '../lib/plan.js';

// ファイルを直接開いた画面は、ブラウザが出どころを "null" として送ってくる
const ALLOWED_ORIGIN = 'null';

async function nightOf(code) {
  const name = await redis(['HGET', 'box:' + code, 'trisight_dig_company_name']);
  if (!name) return null;
  let hour = 3, at = '';
  try {
    const c = JSON.parse((await redis(['HGET', 'box:' + code, 'trisight_dig_company'])) || 'null');
    const m = c && (c['自動発掘用の写し'] || c['夜の発掘用の写し']);
    if (m) { at = m['作成日時'] || ''; if (m['実行時刻'] != null && !isNaN(Number(m['実行時刻']))) hour = Number(m['実行時刻']); }
  } catch (_) {}
  let last = '';
  try { const sv = JSON.parse((await redis(['HGET', 'box:' + code, 'trisight_dig_saved'])) || 'null'); last = (sv && sv.nightAt) || ''; } catch (_) {}
  return { company: name, hour, registeredAt: at, lastRun: last };
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', ALLOWED_ORIGIN);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-trisight-code');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }
  if (req.method !== 'POST') { res.status(405).json({ error: 'POSTのみ受け付けます' }); return; }

  const code = req.headers['x-trisight-code'] || '';
  if (!process.env.TRISIGHT_ADMIN_CODE) { res.status(500).json({ error: 'サーバーに管理用コード（TRISIGHT_ADMIN_CODE）が設定されていません' }); return; }
  if (!isAdminCode(code)) { res.status(403).json({ error: 'この画面は管理用コードでのみ使えます' }); return; }
  if (!process.env.UPSTASH_REDIS_REST_URL) { res.status(503).json({ error: '保管場所（Upstash）が設定されていません' }); return; }

  let body = req.body || {};
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (_) { body = {}; } }
  const op = String(body.op || '');

  try {
    if (op === 'all') {
      const contracts = await listContracts();
      const recs = await listCodeRecords();
      const byCode = {};
      recs.forEach(r => { byCode[r.code] = r; });
      envCodes().forEach(e => { if (!byCode[e.code]) byCode[e.code] = { code: e.code, status: 'active', contractId: '', source: 'Vercelの設定（' + e.from + '）' }; else byCode[e.code].env = e.from; });
      const codes = [];
      for (const c of Object.keys(byCode)) {
        const r = byCode[c];
        const u = await readCode(c);
        codes.push(Object.assign({}, r, {
          env: r.env || (envCodes().find(e => e.code === c) || {}).from || '',
          usage: { current: u.current, previous: u.previous, month: u.month, limit: u.limit },
          picks: await aiPicks(c),
          night: await nightOf(c)
        }));
      }
      res.status(200).json({ ok: true, contracts, codes });
      return;
    }
    if (op === 'saveContract') { const r = await saveContract(body.contract || {}); res.status(r.ok ? 200 : 400).json(r.ok ? r : { error: r.why }); return; }
    if (op === 'issueCode') { const r = await issueCode(String(body.contractId || '')); res.status(r.ok ? 200 : 400).json(r.ok ? r : { error: r.why }); return; }
    if (op === 'attachCode') { const r = await attachCode(String(body.contractId || ''), body.code); res.status(r.ok ? 200 : 400).json(r.ok ? r : { error: r.why }); return; }
    if (op === 'setCodeStatus') { const r = await setCodeStatus(String(body.code || ''), body.status); res.status(r.ok ? 200 : 400).json(r.ok ? r : { error: r.why }); return; }
    if (op === 'reissueErase') { const r = await reissueErase(String(body.code || '')); res.status(r.ok ? 200 : 400).json(r.ok ? r : { error: r.why }); return; }
    if (op === 'setLimit') {
      const lim = body.limit;
      await setLimit(String(body.code || ''), (lim == null || lim === '') ? null : Math.max(0, Math.floor(Number(lim))));
      res.status(200).json({ ok: true }); return;
    }
    if (op === 'setPicks') { const ok = await setPicks(String(body.code || ''), body.picks); res.status(ok ? 200 : 400).json(ok ? { ok: true } : { error: '組み合わせの指定が正しくありません' }); return; }
    if (op === 'delPicks') { await delPicks(String(body.code || '')); res.status(200).json({ ok: true }); return; }
    res.status(400).json({ error: '操作の指定が正しくありません' });
  } catch (e) {
    res.status(500).json({ error: 'オペレーションの処理でエラー：' + e.message });
  }
}
