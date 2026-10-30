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

test('reportDate uses report filename', () => {
  const code = script.match(/function reportDate\(c\)[\s\S]*?\n\}/)?.[0];
  assert.ok(code);
  const fn = vm.runInNewContext(code + '\nreportDate');
  assert.equal(fn({report:'A-2026-08-13.md'}), '2026-08-13');
  assert.equal(fn({report:'A.md'}), '未知');
  assert.equal(fn({report:'A.md',as_of_date:'2026-10-29'}), '2026-10-29');
});
test('catalog text is escaped before HTML rendering', () => {
  const sanitizeCode = script.match(/function sanitizeCompany\(c\)[\s\S]*?(?=\nfunction reportDate)/)?.[0];
  const escapeCode = script.match(/function escapeHtml\(str\)[\s\S]*?\n\}/)?.[0];
  assert.ok(sanitizeCode && escapeCode);
  const sanitize = vm.runInNewContext(escapeCode + '\n' + sanitizeCode + '\nsanitizeCompany');
  const record = {id:'example',report:'example.md',radar:'example.svg',
    name:'<img src=x onerror=alert(1)>',nameEn:'Example',ticker:'" onmouseover="alert(1)',
    ind1:'Industry',ind2:'Sector',oneLine:'Sample',gradeLabel:'优秀',employees:'10',revenue:'0'};
  const clean = sanitize(record);
  assert.match(clean.name, /&lt;img/);
  assert.doesNotMatch(clean.name, /<img/);
  assert.match(clean.ticker, /&quot;/);
  assert.throws(() => sanitize({...record,id:"x' onclick='alert(1)"}), /不安全/);
  assert.throws(() => sanitize({...record,radar:'x" onerror="alert(1).svg'}), /不安全/);
  assert.throws(() => sanitize({...record,as_of_date:'<img src=x>'}), /不安全/);
});
test('reviewed evaluation uses its recorded date and review label', () => {
  const dateCode = script.match(/function reportDate\(c\)[\s\S]*?\n\}/)?.[0];
  const noteCode = script.match(/function evaluationNote\(c\)[\s\S]*?\n\}/)?.[0];
  const escapeCode = script.match(/function escapeHtml\(str\)[\s\S]*?\n\}/)?.[0];
  assert.ok(dateCode && noteCode && escapeCode);
  const note = vm.runInNewContext(escapeCode + '\n' + dateCode + '\n' + noteCode + '\nevaluationNote');
  const value = note({report:'example-abcdef.md',as_of_date:'2026-10-29',
    rubric_version:'financial-health-v1',verification_status:'reviewer_attested'});
  assert.match(value, /审核记录：2026-10-29/);
  assert.doesNotMatch(value, /原始指标输入未完整归档/);
});
test('legacyGradeNote warns on score boundary', () => {
  const code = script.match(/function legacyGradeNote\(c\)[\s\S]*?\n\}/)?.[0];
  assert.ok(code);
  const fn = vm.runInNewContext(code + '\nlegacyGradeNote');
  assert.match(fn({grade:'Moderate',total:70}), /历史等级/);
  assert.equal(fn({grade:'Excellent',total:89}), '');
});
test('missing material review baseline never blocks catalog rendering', async () => {
  const code = script.match(/async function loadMaterialIssues\(fetcher\)[\s\S]*?\n\}/)?.[0];
  assert.ok(code, 'loadMaterialIssues must remain discoverable');
  const load = vm.runInNewContext(code + '\nloadMaterialIssues',
    {console: {warn() {}}});
  const notFound = async () => ({ok: false, status: 404, json: async () => ({})});
  assert.equal((await load(notFound)).length, 0);
  const offline = async () => { throw new Error('network down'); };
  assert.equal((await load(offline)).length, 0);
  const malformed = async () => ({ok: true, status: 200, json: async () => '{"not":"a list"}'});
  assert.equal((await load(malformed)).length, 0);
});

test('material review baseline drops entries without company_id or code', async () => {
  const code = script.match(/async function loadMaterialIssues\(fetcher\)[\s\S]*?\n\}/)?.[0];
  const load = vm.runInNewContext(code + '\nloadMaterialIssues', {console: {warn() {}}});
  const fetcher = async () => ({ok: true, status: 200, json: async () => ([
    {company_id: 'jinyafu', code: 'report_conclusion_score_differs_from_catalog'},
    {code: 'missing_company_id'},
    {company_id: 'no_code'},
    null,
  ])});
  const kept = await load(fetcher);
  assert.equal(kept.length, 1);
  assert.equal(kept[0].company_id, 'jinyafu');
  assert.equal(kept[0].code, 'report_conclusion_score_differs_from_catalog');
});

test('site init treats the material ledger as advisory only', () => {
  const initBlock = html.match(/\(async function init\(\)[\s\S]*?\}\)\(\);/)?.[0];
  assert.ok(initBlock, 'init must remain discoverable');
  assert.match(initBlock, /loadMaterialIssues\(fetch\)/);
  assert.doesNotMatch(initBlock, /reviewResp\.ok/);
  assert.match(initBlock, /if \(!resp\.ok\)/);
});
test('sidebar industry order is derived from the catalog, not hard-coded', () => {
  const code = html.match(/const IND_PRIORITY = \[[\s\S]*?\n\}/)?.[0];
  assert.ok(code, 'industryOrder must remain discoverable');
  const industryOrder = vm.runInNewContext(code + '\nindustryOrder');
  const catalog = JSON.parse(readFileSync(new URL('../docs/companies.json', import.meta.url), 'utf8'));
  const order = industryOrder(catalog);
  const present = [...new Set(catalog.map(c => c.ind1))];
  assert.equal(order.length, present.length, 'every catalog industry must be navigable');
  assert.deepEqual([...order].sort(), [...present].sort());
  assert.equal(new Set(order).size, order.length, 'no duplicated industry groups');
  assert.equal(order[0], '人工智能', 'preferred order is respected first');
  // A brand-new industry that nobody added to the priority list still shows up.
  const withNew = industryOrder([{ind1: '新赛道'}, ...catalog]);
  assert.ok(withNew.includes('新赛道'));
});
test('every catalog company is reachable through the sidebar tree', () => {
  const code = html.match(/const IND_PRIORITY = \[[\s\S]*?\n\}/)?.[0];
  const industryOrder = vm.runInNewContext(code + '\nindustryOrder');
  const catalog = JSON.parse(readFileSync(new URL('../docs/companies.json', import.meta.url), 'utf8'));
  const tree = {};
  for (const c of catalog) {
    ((tree[c.ind1] ??= {})[c.ind2] ??= []).push(c);
  }
  let reachable = 0;
  for (const ind1 of industryOrder(catalog)) {
    if (!tree[ind1]) continue;
    for (const ind2 of Object.keys(tree[ind1])) reachable += tree[ind1][ind2].length;
  }
  assert.equal(reachable, catalog.length);
});
test('document title reflects the current route', () => {
  const code = html.match(/const SITE_TITLE = [\s\S]*?\n\}\nfunction syncDocumentTitle/)?.[0];
  assert.ok(code, 'titleForRoute must remain discoverable');
  const titleForRoute = vm.runInNewContext(
    code.replace(/\nfunction syncDocumentTitle$/, '') + '\ntitleForRoute');
  const lookup = id => ({minghong: {name: '明汯投资', total: 89, gradeLabel: '优秀'},
                          tencent: {name: '腾讯', total: 77, gradeLabel: '中等偏上'}})[id];
  assert.match(titleForRoute(['company', 'minghong'], lookup), /明汯投资 89 分 · 优秀/);
  assert.match(titleForRoute(['compare', 'minghong', 'tencent'], lookup), /明汯投资 vs 腾讯/);
  assert.equal(titleForRoute([], lookup), '企业健康度评估 · Company Health Evaluation');
  assert.equal(titleForRoute(['company', 'missing'], lookup), '企业健康度评估 · Company Health Evaluation');
});

test('company cards are keyboard reachable and the entry animation is capped', () => {
  const browse = script.match(/function renderBrowse\(\)[\s\S]*?(?=\n\/\/ ============================================================\n\/\/ SINGLE COMPANY VIEW)/)?.[0];
  assert.ok(browse, 'renderBrowse must remain discoverable');
  assert.match(browse, /role="link" tabindex="0"/);
  assert.match(browse, /onkeydown="if\(event\.key==='Enter'/);
  assert.match(browse, /Math\.min\(i,\s*12\)\*0\.04/);
  assert.doesNotMatch(browse, /animation-delay:\$\{i\*0\.04\}/);
});

test('back buttons use history-aware navigation, never a bare hash reset', () => {
  assert.equal((html.match(/goHome\(\)/g) || []).length >= 4, true);
  assert.doesNotMatch(html, /onclick="location\.hash=''"/);
  const goHome = script.match(/function goHome\(\)[\s\S]*?\n\}/)?.[0];
  assert.ok(goHome);
  assert.match(goHome, /history\.back\(\)/);
});

test('sidebar keeps its open branches and exposes aria-expanded', () => {
  const sidebar = script.match(/function renderSidebar\(\)[\s\S]*?(?=\nfunction toggleIndustry)/)?.[0];
  assert.ok(sidebar, 'renderSidebar must remain discoverable');
  assert.match(sidebar, /openGroups\.has\(ind1\)/);
  assert.match(sidebar, /openGroups\.has\(subKey\)/);
  assert.match(sidebar, /aria-expanded=/);
  const toggle = script.match(/function toggleIndustry[\s\S]*?\n\}/)?.[0];
  assert.match(toggle, /openGroups\.add/);
});

test('report content is cached and stale responses cannot overwrite fresh ones', () => {
  const loader = script.match(/async function loadReportContent\([\s\S]*?\n\}/)?.[0];
  assert.ok(loader, 'loadReportContent must remain discoverable');
  assert.match(loader, /reportCache\.get\(version\.report\)/);
  assert.match(loader, /reportCache\.set\(version\.report/);
  assert.match(loader, /if \(token !== reportLoadToken\) return;/);
});
test('method route resolves to the published methodology document', () => {
  const doc = script.match(/const METHOD_DOC = '([^']+)'/)?.[1];
  assert.equal(doc, 'docs/企业健康度评估体系/00-评估框架总览.md');
  assert.ok(readFileSync(new URL('../' + doc, import.meta.url), 'utf8').length > 1000,
    'the methodology document referenced by the site must exist and be substantive');
  const fetchText = script.match(/async function fetchText\(path\)[\s\S]*?\n\}/)?.[0];
  assert.ok(fetchText, 'fetchText must remain discoverable');
  assert.match(fetchText, /encodeURIComponent/);
});
test('table header cells are th and the first data row is not', () => {
  const value = renderer.renderMarkdown('前言\n\n| A | B |\n|---|---|\n| 1 | 2 |\n');
  assert.match(value, /<th>A<\/th><th>B<\/th>/);
  assert.match(value, /<td>1<\/td><td>2<\/td>/);
  assert.doesNotMatch(value, /<th>1<\/th>/);
  assert.doesNotMatch(value, /---/);
});

test('empty table cells keep their column position', () => {
  const value = renderer.renderMarkdown('| A | B | C |\n|---|:-:|---|\n| 1 |  | 3 |\n');
  assert.match(value, /<td>1<\/td><td><\/td><td>3<\/td>/);
});

test('a pipe block without a separator row is data, not a header', () => {
  const value = renderer.renderMarkdown('| 主体 | x |\n| 主营 | y |\n');
  assert.match(value, /<td>主体<\/td><td>x<\/td>/);
  assert.doesNotMatch(value, /<th>/);
});
