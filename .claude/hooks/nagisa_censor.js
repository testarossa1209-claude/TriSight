#!/usr/bin/env node
/*! ===========================================================================
 *  nagisa_censor.js — なぎさの外に置く検閲（返答を終える直前に照合する）
 *  版：2026-11-10-03
 *  ---------------------------------------------------------------------------
 *  Claude の「Stop」フックとして呼ばれる。なぎさが返答を終えようとした時点で、
 *  宏史さんの最後の発言以降の「なぎさが書いた文」と「なぎさが使った道具の順番」を
 *  記録から取り出し、NagisaRules.js の規則と照合する。
 *
 *  引っかかった場合：終了コード2で返答の終了を止め、理由をなぎさへ差し戻す。
 *                    なぎさは理由を読んで、やり直すか書き直すまで返答を終えられない。
 *  同じ返答で差し戻しが3回続いたら、それ以上は止めずに通す（無限の差し戻しを防ぐ）。
 *
 *  照合する条（文字の照合＝言葉、運びの照合＝道具の順番）
 *    第1条　仕切りの文／「ご指示をお待ちします」で締める／「やります」宣言だけで手を動かさない
 *    第2条　同じファイルを同じ会話で2度渡す（1）／英語の文（6）
 *    第3条　金額を、確かめた場所を書かずに出す
 *    第4条　画面の操作を、現物を開かずに案内する／確かめずに「確かめた・効く」と書く／雛形を見ずに申請を出す
 *    第5条　人に資料を出させる前に、自分で探していない
 *  第6条・第7条・第8条は文字や道具の順番では判定できないため、H&Nパトリオットの照合へ回す。
 * ========================================================================== */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const MAX_BLOCKS = 3;

/* 道具の種類（道具の名前から判定する） */
const T = {
  look: n => /^(Read|Grep|Glob|WebFetch)$/.test(n) || /Browser|chrome|read_page|get_page_text|screenshot|device_list_dir|device_stage_files/i.test(n),
  search: n => /conversation_search|recent_chats|read_conversation|memory_read|memory_list|^Grep$|^Glob$|^Read$|WebSearch/i.test(n),
  work: n => /^(Edit|Write|NotebookEdit|Bash)$/.test(n) || /device_commit_files|update_artifact|publish/i.test(n),
  send: n => /SendUserFile|present_files/i.test(n),
  web: n => /WebSearch|WebFetch/i.test(n)
};

function readStdin() {
  try { return fs.readFileSync(0, 'utf8'); } catch (e) { return ''; }
}

function loadRules() {
  require(path.join(__dirname, '..', '..', 'NagisaRules.js'));
  return globalThis.NagisaRules;
}

function readItems(p) {
  const out = [];
  for (const l of fs.readFileSync(p, 'utf8').split('\n')) {
    if (!l) continue;
    try { out.push(JSON.parse(l)); } catch (e) { /* 壊れた行は飛ばす */ }
  }
  return out;
}

function isHuman(it) {
  if (it.type !== 'user' || !it.message) return false;
  const c = it.message.content;
  return typeof c === 'string' || (Array.isArray(c) && c.some(b => b && b.type === 'text'));
}

/* 記録を「工程の列」にする。各工程＝{kind:'text'|'tool', text, name, input} */
function steps(items, from) {
  const out = [];
  for (let i = from; i < items.length; i++) {
    const it = items[i];
    if (it.type !== 'assistant' || !it.message || !Array.isArray(it.message.content)) continue;
    for (const b of it.message.content) {
      if (!b) continue;
      if (b.type === 'text' && b.text) out.push({ kind: 'text', text: b.text });
      if (b.type === 'tool_use') out.push({ kind: 'tool', name: b.name || '', input: b.input || {} });
    }
  }
  return out;
}

/* 照合の前に、英語であってよい部分（コード・URL・ファイル名）を外す */
function stripAllowed(text) {
  return text
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/https?:\/\/\S+/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[\w.\-\/]+\.(html|js|json|md|png|gif|pdf|zip|css|py|sh|xlsx|docx|pptx)\b/gi, ' ');
}

const JP = /[぀-ヿ㐀-鿿]/;

function sentences(text) {
  return stripAllowed(text).split(/\n|(?<=[。！？])/).map(s => s.trim()).filter(Boolean);
}

/* ---------- 各条の照合 ---------- */

function art1(text, tools, R) {
  const ng = [];
  for (const p of R.forbiddenPhrases) {
    const core = p.replace(/（[^）]*）/g, '').trim();
    if (core && text.includes(core)) ng.push('出力禁止句「' + core + '」');
  }
  const tail = text.trim().slice(-40);
  if (/ご指示(を|が)?(お待ち|いただければ|があれば)/.test(tail)) ng.push('返答を「ご指示をお待ちします」の形で締めている');
  const declares = /(着手します|直します|作ります|やります|取りかかります|修正します)[。！]?\s*$/m.test(text);
  if (declares && !tools.some(t => T.work(t.name))) ng.push('「やります」と宣言しただけで、手を動かしていない（編集・作成の道具を一度も使っていない）');
  return ng;
}

function sentFiles(list) {
  const sent = {};
  for (const s of list) {
    if (s.kind !== 'tool' || !T.send(s.name)) continue;
    const files = [].concat(s.input.files || s.input.paths || s.input.filepaths || []);
    for (const f of files) { const k = path.basename(String(f)); sent[k] = (sent[k] || 0) + 1; }
  }
  return sent;
}

function art2(text, allItems, start) {
  const ng = [];
  /* 1：同じファイルを同じ会話で2度渡す（このターンで渡したファイルが、会話全体で2度目以上なら止める） */
  const now = sentFiles(steps(allItems, start));
  const all = sentFiles(steps(allItems, 0));
  const twice = Object.keys(now).filter(k => all[k] >= 2);
  if (twice.length) ng.push('第2条1：同じファイルをこの会話で2度以上渡している（' + twice.join('、') + '）。画面で見せるにとどめる');
  /* 6：英語の文 */
  const eng = [];
  for (const line of sentences(text)) {
    const words = line.match(/[A-Za-z][A-Za-z'’\-]*/g) || [];
    const run = /([A-Za-z][A-Za-z'’\-]*[\s,.:;!?]+){5,}[A-Za-z]/.test(line);
    if ((!JP.test(line) && words.length >= 4) || run) eng.push(line.slice(0, 60));
  }
  if (eng.length) ng.push('第2条6：英語の文 → ' + eng.slice(0, 5).join(' ／ '));
  return ng;
}

function art3(text) {
  const ng = [];
  for (const s of sentences(text)) {
    if (!/[0-9０-９][0-9０-９,，.]*\s*(万|千|億)?円/.test(s)) continue;
    const sourced = /出典|出所|確認|確かめ|調べ|によると|によれば|記載|見積書|請求書|要領|公報|[［\[]\d+[］\]]/.test(s);
    if (!sourced) ng.push('金額を、確かめた場所を書かずに出している → ' + s.slice(0, 50));
  }
  return ng.length ? ['第3条：' + ng.slice(0, 3).join(' ／ ')] : [];
}

function art4(text, steps_) {
  /* 画面の操作を案内する文が出る前に、現物を見る道具を一度も使っていなければ止める */
  let looked = false;
  for (const s of steps_) {
    if (s.kind === 'tool' && T.look(s.name)) looked = true;
    if (s.kind !== 'text') continue;
    for (const line of sentences(s.text)) {
      if (/(ボタン|リンク|タブ|メニュー|欄|カード).{0,20}(押して|クリックして|開いて|選んで|タップして)/.test(line) && !looked) {
        return ['第4条：画面の操作を、現物（ファイルや画面）を開かずに案内している → ' + line.slice(0, 50)];
      }
    }
  }
  return [];
}

function art4b(steps_) {
  /* やっていないのにやった風に書く：確かめる道具（ファイル・画面を開く／動かす）を使う前に「確かめた・効く・通った」と書いたら止める */
  let checked = false;
  for (const s of steps_) {
    if (s.kind === 'tool' && (T.look(s.name) || s.name === 'Bash')) checked = true;
    if (s.kind !== 'text') continue;
    for (const line of sentences(s.text)) {
      if (/(確かめました|確認しました|確認済み|動きました|効きます|通りました|止まりました|完了しました|問題ありません)/.test(line) && !checked) {
        return ['第4条：確かめる道具を一度も使わずに、確かめた・効く・通ったと書いている（やっていないのにやった風）→ ' + line.slice(0, 50)];
      }
    }
  }
  return [];
}

function art4c(allItems, start) {
  /* 作業を端折る：申請（プルリクエスト）を出す前に、この会話で申請の雛形を一度も読んでいなければ止める */
  const all = steps(allItems, 0);
  const now = steps(allItems, start);
  const isPR = s => s.kind === 'tool' && /(\/pulls\b[\s\S]*-f title|gh pr create)/.test(String(s.input.command || ''));
  if (!now.some(isPR)) return [];
  const readTemplate = all.some(s => s.kind === 'tool' &&
    /pull_request_template|pulls\?state/.test(String(s.input.command || s.input.file_path || '')));
  return readTemplate ? [] : ['第4条：申請の雛形（.github/pull_request_template.md）も前の申請も見ずに、申請を出している（作業を端折っている）'];
}

function art5(steps_) {
  /* 人に資料を出させる文が出る前に、自分で探す道具（過去ログ・記憶・GitHubの現物）を使っていなければ止める */
  let searched = false;
  for (const s of steps_) {
    if (s.kind === 'tool' && T.search(s.name)) searched = true;
    if (s.kind !== 'text') continue;
    for (const line of sentences(s.text)) {
      if (/((アップロード|添付|提供|送付|貼り付け|共有)(して|を)?|送って|貼って|出して|見せて)(ください|いただけ|もらえ|お願い)/.test(line) && !searched) {
        return ['第5条：自分で探す前に、人に資料を出させている → ' + line.slice(0, 50)];
      }
    }
  }
  return [];
}

/* ---------- 本体 ---------- */

function counterFile(sessionId) {
  return path.join(os.tmpdir(), 'nagisa_censor_' + String(sessionId || 'x').replace(/[^\w-]/g, '') + '.cnt');
}

function main() {
  let input = {};
  try { input = JSON.parse(readStdin() || '{}'); } catch (e) { return 0; }
  if (!input.transcript_path || !fs.existsSync(input.transcript_path)) return 0;

  const cf = counterFile(input.session_id);
  let count = 0;
  if (input.stop_hook_active) { try { count = parseInt(fs.readFileSync(cf, 'utf8'), 10) || 0; } catch (e) { count = 0; } }
  if (count >= MAX_BLOCKS) { try { fs.unlinkSync(cf); } catch (e) {} return 0; }

  const R = loadRules();
  const items = readItems(input.transcript_path);
  let start = 0;
  for (let i = items.length - 1; i >= 0; i--) if (isHuman(items[i])) { start = i + 1; break; }
  const turn = steps(items, start);
  const text = turn.filter(s => s.kind === 'text').map(s => s.text).join('\n');
  const tools = turn.filter(s => s.kind === 'tool');

  const ng = [].concat(
    art1(text, tools, R).map(x => '第1条：' + x),
    art2(text, items, start),
    art3(text),
    art4(text, turn),
    art4b(turn),
    art4c(items, start),
    art5(turn)
  );
  if (!ng.length) { try { fs.unlinkSync(cf); } catch (e) {} return 0; }

  const msg = ['【検閲】この返答はなぎさ実行規則（' + R.version + '）に反しています。やり直すか書き直すまで、返答は終えられません。'];
  ng.forEach(x => msg.push('■ ' + x));
  if (ng.some(x => x.indexOf('出力禁止句') >= 0)) msg.push('  区切りを促したいときは「' + R.closingQuestion + '」と問う。');
  process.stderr.write(msg.join('\n') + '\n');
  try { fs.writeFileSync(cf, String(count + 1)); } catch (e) {}
  return 2;
}

let code = 0;
try { code = main(); } catch (e) { code = 0; /* 検閲側の故障でなぎさを止めない */ }
process.exit(code);
