import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script, 'inline application script must exist');
new vm.Script(script); // Syntax checking: do not run browser init.

const snippet = script.match(
  /function renderMarkdown\(md\)([\s\S]*?)(?=\n\/\/ ============================================================\n\/\/ COMPARE VIEW)/
)?.[0];
assert.ok(snippet, 'Markdown renderer must remain discoverable');
const renderer = vm.runInNewContext(
  snippet + '\n({renderMarkdown,inlineMarkdown})',
  { URL, window: {location: {href: 'https://example.com/'}} },
);

test('consecutive Markdown list items retain a list wrapper', () => {
  const value = renderer.renderMarkdown('- First\n- Second\n\nParagraph');
  assert.match(value, /<ul><li>First<\/li><li>Second<\/li><\/ul>/);
  assert.match(value, /<p>Paragraph<\/p>/);
});

test('script URLs in Markdown are never linked', () => {
  const value = renderer.inlineMarkdown('[bad](javascript:alert)');
  assert.doesNotMatch(value, /href=/);
  assert.match(value, /bad/);
});

test('safe HTTPS links have noopener noreferrer', () => {
  const value = renderer.inlineMarkdown('[source](https://example.com/a)');
  assert.match(value, /href="https:\/\/example.com\/a"/);
  assert.match(value, /rel="noopener noreferrer"/);
});

test('Markdown is HTML-escaped', () => {
  const value = renderer.inlineMarkdown('<img src=x>');
  assert.doesNotMatch(value, /<img/);
  assert.match(value, /&lt;img/);
});
