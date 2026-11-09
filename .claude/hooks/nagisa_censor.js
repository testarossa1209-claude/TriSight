#!/usr/bin/env node
/*! ===========================================================================
 *  nagisa_censor.js — なぎさの外に置く検閲（返答を終える直前に照合する）
 *  版：2026-11-10-01
 *  ---------------------------------------------------------------------------
 *  Claude の「Stop」フックとして呼ばれる。なぎさが返答を終えようとした時点で、
 *  宏史さんの最後の発言以降になぎさが書いた文章をすべて取り出し、
 *  NagisaRules.js の規則と照合する。
 *
 *  引っかかった場合：終了コード2で返答の終了を止め、理由をなぎさへ差し戻す。
 *                    なぎさは理由を読んで書き直す。
 *  第1段の照合：①第1条の出力禁止句 ②第2条6（英語の文）
 *  同じ返答で差し戻しが3回続いたら、それ以上は止めずに通す（無限の差し戻しを防ぐ）。
 * ========================================================================== */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const MAX_BLOCKS = 3;

function readStdin() {
  try { return fs.readFileSync(0, 'utf8'); } catch (e) { return ''; }
}

function loadRules() {
  require(path.join(__dirname, '..', '..', 'NagisaRules.js'));
  return globalThis.NagisaRules;
}

/* 記録（1行1件のJSON）から、宏史さんの最後の発言以降のなぎさの文章を集める */
function lastTurnText(transcriptPath) {
  const lines = fs.readFileSync(transcriptPath, 'utf8').split('\n').filter(Boolean);
  const items = [];
  for (const l of lines) { try { items.push(JSON.parse(l)); } catch (e) { /* 壊れた行は飛ばす */ } }
  let start = 0;
  for (let i = items.length - 1; i >= 0; i--) {
    const it = items[i];
    if (it.type !== 'user' || !it.message) continue;
    const c = it.message.content;
    const isHuman = typeof c === 'string' ||
      (Array.isArray(c) && c.some(b => b && b.type === 'text'));
    if (isHuman) { start = i + 1; break; }
  }
  const out = [];
  for (let i = start; i < items.length; i++) {
    const it = items[i];
    if (it.type !== 'assistant' || !it.message || !Array.isArray(it.message.content)) continue;
    for (const b of it.message.content) if (b && b.type === 'text' && b.text) out.push(b.text);
  }
  return out.join('\n');
}

/* 照合の前に、英語であってよい部分（コード・URL・ファイル名）を外す */
function stripAllowed(text) {
  return text
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/https?:\/\/\S+/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[\w.\-\/]+\.(html|js|json|md|png|gif|pdf|zip|css|py|sh)\b/gi, ' ');
}

const JP = /[぀-ヿ㐀-鿿]/;

function findEnglish(text) {
  const hits = [];
  for (const raw of stripAllowed(text).split(/\n|(?<=[。！？])/)) {
    const line = raw.trim();
    if (!line) continue;
    const words = line.match(/[A-Za-z][A-Za-z'’\-]*/g) || [];
    /* 日本語を含まず英単語が4語以上の行、または英単語が6語以上続く箇所を英語の文とみなす */
    const run = line.match(/([A-Za-z][A-Za-z'’\-]*[\s,.:;!?]+){5,}[A-Za-z]/);
    if ((!JP.test(line) && words.length >= 4) || run) hits.push(line.slice(0, 60));
  }
  return hits;
}

function findForbidden(text, phrases) {
  const hits = [];
  for (const p of phrases) {
    const core = p.replace(/（[^）]*）/g, '').trim();
    if (core && text.includes(core)) hits.push(core);
  }
  return hits;
}

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
  const text = lastTurnText(input.transcript_path);
  const forbidden = findForbidden(text, R.forbiddenPhrases);
  const english = findEnglish(text);
  if (!forbidden.length && !english.length) { try { fs.unlinkSync(cf); } catch (e) {} return 0; }

  const msg = ['【検閲】この返答はなぎさ実行規則（' + R.version + '）に反しています。書き直してください。'];
  if (forbidden.length) {
    msg.push('■ 第1条（仕切らない）の出力禁止句：' + forbidden.join('／'));
    msg.push('  区切りを促したいときは「' + R.closingQuestion + '」と問う。');
  }
  if (english.length) {
    msg.push('■ 第2条6（すべて日本語で書く）に反する英語の文：');
    english.slice(0, 5).forEach(e => msg.push('  ・' + e));
  }
  process.stderr.write(msg.join('\n') + '\n');
  try { fs.writeFileSync(cf, String(count + 1)); } catch (e) {}
  return 2;
}

let code = 0;
try { code = main(); } catch (e) { code = 0; /* 検閲側の故障でなぎさを止めない */ }
process.exit(code);
