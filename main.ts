// gta6-meme-x-01 entry program (Node 22, standard library only).
//
// The entry is the X post itself: meme.png, posted from a public account with the caption in POSTING.md.
// This program's one job is to hand the grader the post's address: it validates POST.json at the repository
// root and copies it, byte for byte, to POST.json in the output directory, where the gate reads it.
//
// Validation, in order, each failure printing a clear error and exiting 1:
//   1. POST.json must exist and be readable in MAKEFUN_BOT_DIR.
//   2. It must parse as JSON.
//   3. The parsed value must be a plain object (not null, not an array, not a bare string or number).
//   4. Its "url" must be a string naming an X post address of the shape
//      https://x.com/<handle>/status/<digits> : https scheme, host x.com, exactly three path
//      segments <handle> / "status" / <post id>, and no query string or fragment.
// On success nothing is printed and the exit code is 0.
//
// Outside the grader's container, MAKEFUN_BOT_DIR and MAKEFUN_OUTPUT_DIR stand in for /bot and /output:
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const BOT_DIR = process.env.MAKEFUN_BOT_DIR ?? '/bot';
const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
const SHAPE = 'https://x.com/<handle>/status/<digits>';

function fail(message: string): never {
  console.error(`main.ts: ${message}`);
  process.exit(1);
}

// 1 + 2: read and parse POST.json.
const postPath = join(BOT_DIR, 'POST.json');
let raw: string;
try {
  raw = readFileSync(postPath, 'utf8');
} catch (err) {
  fail(`POST.json could not be read from ${postPath}: ${(err as Error).message}`);
}
let data: unknown;
try {
  data = JSON.parse(raw!);
} catch (err) {
  fail(`POST.json is not valid JSON: ${(err as Error).message}`);
}

// 3: the parsed value must be a plain object.
if (typeof data !== 'object' || data === null || Array.isArray(data)) {
  fail(`POST.json must be a JSON object like {"url": "${SHAPE}"}.`);
}

// 4: "url" must be a string naming an X post address.
const url = (data as Record<string, unknown>).url;
if (typeof url !== 'string' || url.length === 0) {
  fail(`POST.json must carry a non-empty string "url" naming the X post, of the shape ${SHAPE}.`);
}
if (/\s/.test(url!)) {
  fail(`POST.json "url" must not contain whitespace: ${JSON.stringify(url)}`);
}
let parsed: URL;
try {
  parsed = new URL(url!);
} catch {
  fail(`POST.json "url" is not a URL at all: ${JSON.stringify(url)}`);
}
if (parsed.protocol !== 'https:') {
  fail(`POST.json "url" must start with https:// : got ${JSON.stringify(url)}`);
}
if (parsed.hostname !== 'x.com') {
  fail(`POST.json "url" must be on x.com: got host ${JSON.stringify(parsed.hostname)}`);
}
if (parsed.search !== '' || parsed.hash !== '') {
  fail(`POST.json "url" must be a bare post address, with no query string or fragment: ${JSON.stringify(url)}`);
}
const segments = parsed.pathname.split('/').filter((s) => s.length > 0);
if (segments.length !== 3 || segments[1] !== 'status') {
  fail(`POST.json "url" must have the shape ${SHAPE}: got path ${JSON.stringify(parsed.pathname)}`);
}
const [handle, , postId] = segments;
if (handle.length > 50 || postId.length > 30) {
  fail(`POST.json "url" has an implausibly long handle or post id: ${JSON.stringify(url)}`);
}
// A real post address is nothing but scheme, host and those three segments: no embedded
// credentials, no port, and no trailing or doubled slashes for the segment filter to forgive.
if (parsed.username !== '' || parsed.password !== '' || parsed.port !== '') {
  fail(`POST.json "url" must not carry credentials or a port: ${JSON.stringify(url)}`);
}
if (parsed.pathname !== `/${handle}/status/${postId}`) {
  fail(`POST.json "url" must be exactly ${SHAPE}, with no extra slashes: ${JSON.stringify(url)}`);
}

// Hand the validated file to the gate, byte for byte.
mkdirSync(OUTPUT_DIR, { recursive: true });
try {
  copyFileSync(postPath, join(OUTPUT_DIR, 'POST.json'));
} catch (err) {
  fail(`POST.json could not be copied to ${OUTPUT_DIR}: ${(err as Error).message}`);
}
