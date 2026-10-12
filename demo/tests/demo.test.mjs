import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import { LEVELS, SCENARIO, validateSlot, inspectWriting, eligibleDelayedReview, SAMPLE_DRAFT, REVISED_DRAFT } from '../dist/model.mjs';

test('the route contains 12 stages and no invented A3 level', () => {
  assert.equal(LEVELS.length, 12);
  assert.equal(new Set(LEVELS.map((level) => level.id)).size, 12);
  assert.ok(!LEVELS.some((level) => /a3/i.test(level.id)));
  assert.equal(LEVELS.find((level) => level.id === 'pre-b1').status, 'Internal bridge to B1');
});

test('the appointment has exactly one code-validated solution', () => {
  assert.deepEqual(SCENARIO.offers.filter((offer) => validateSlot(offer.id).valid).map((offer) => offer.id), ['wed-14']);
});

test('a start before a conflict still fails when the full duration overlaps', () => {
  const result = validateSlot('tue-14');
  assert.equal(result.valid, false);
  assert.equal(result.reason, 'overlap');
  assert.equal(result.end, 870);
});

test('a start at closing time does not make a valid appointment', () => {
  assert.equal(validateSlot('wed-16').reason, 'closed');
});

test('unknown appointment identifiers are refused', () => {
  assert.deepEqual(validateSlot('model-invented-slot'), { valid: false, reason: 'unknown' });
});

test('touching interval boundaries do not count as overlap', () => {
  const fixture = structuredClone(SCENARIO);
  fixture.offers.push({ id: 'ends-at-work', day: '2026-10-06', start: 825 });
  assert.equal(validateSlot('ends-at-work', fixture).valid, true);
});

test('correct appointment day labels match the actual calendar', () => {
  assert.equal(new Date('2026-10-06T12:00:00Z').getUTCDay(), 2);
  assert.equal(new Date('2026-10-07T12:00:00Z').getUTCDay(), 3);
});

test('fixed writing rules identify the intentional verb mistake', () => {
  assert.equal(inspectWriting(SAMPLE_DRAFT).issues[0].after, 'kom ik');
  assert.equal(inspectWriting(REVISED_DRAFT).issues.length, 0);
  assert.equal(inspectWriting(REVISED_DRAFT).timePresent, true);
});

test('writing feedback is always labelled a fixture rather than a complete assessment', () => {
  assert.equal(inspectWriting('onbekende tekst').fixtureOnly, true);
  assert.equal(inspectWriting('onbekende tekst').timePresent, false);
});

test('a later independent first attempt needs a new session and meaningful delay', () => {
  const fixture = { firstTry: true, assisted: false, overridden: false, originalSession: 'one', currentSession: 'two', observedAt: 1000, reviewAt: 1000 + 4 * 60 * 60 * 1000 };
  assert.equal(eligibleDelayedReview(fixture), true);
  assert.equal(eligibleDelayedReview({ ...fixture, assisted: true }), false);
  assert.equal(eligibleDelayedReview({ ...fixture, overridden: true }), false);
  assert.equal(eligibleDelayedReview({ ...fixture, firstTry: false }), false);
  assert.equal(eligibleDelayedReview({ ...fixture, currentSession: 'one' }), false);
  assert.equal(eligibleDelayedReview({ ...fixture, reviewAt: fixture.reviewAt - 1 }), false);
});

test('the static entry uses relative assets and has an explicit demo boundary', async () => {
  const html = await readFile(new URL('../dist/index.html', import.meta.url), 'utf8');
  assert.match(html, /INTERACTIVE DEMO/);
  assert.match(html, /No live model, Azure connection or certified assessment/);
  assert.match(html, /src="\.\/app\.mjs"/);
  assert.match(html, /href="\.\/styles\.css"/);
  assert.match(html, /id="workspace" tabindex="-1"/);
});

// Exercise the actual module event handlers against a small document stub.
// This verifies rendering and transitions; it is explicitly not browser or visual QA.
test('the actual demo render supports a connected assisted mission and language switch', async () => {
  const listeners = new Map();
  const nodes = new Map();
  function node(id) {
    if (!nodes.has(id)) nodes.set(id, { value: '', innerHTML: '', textContent: '', hidden: true, addEventListener(type, callback) { listeners.set(`${id}:${type}`, callback); }, focus() {}, showModal() {}, close() {} });
    return nodes.get(id);
  }
  const navigation = ['today', 'mission', 'stories', 'path', 'exam'].map((view) => ({ dataset: { view }, classList: { toggle() {} }, setAttribute() {}, removeAttribute() {} }));
  globalThis.document = { querySelector: node, querySelectorAll: (selector) => selector === '[data-view]' ? navigation : [], addEventListener(type, callback) { listeners.set(`document:${type}`, callback); } };
  globalThis.window = { scrollTo() {}, location: { reload() {} } };
  await import('../dist/app.mjs');
  const click = (dataset) => listeners.get('document:click')({ target: { closest: () => ({ dataset, disabled: false }) } });
  const content = () => node('#workspace').innerHTML;
  assert.match(content(), /Wat wil je vandaag kunnen/);
  click({ action: 'start-mission' });
  assert.match(content(), /dinsdag 6 oktober om 10.00 uur/);
  click({ readingAnswer: 'class' }); click({ action: 'check-reading' });
  assert.match(content(), /Je les en je afspraak vallen samen/);
  click({ action: 'to-listening' });
  assert.doesNotMatch(content(), /Beste Sam/);
  click({ action: 'transcript' });
  assert.match(content(), /1 help action recorded/);
  click({ action: 'to-speaking' });
  click({ slot: 'tue-14' }); click({ action: 'check-slot' });
  assert.match(content(), /overlappen met je werk/);
  click({ slot: 'wed-14' }); click({ action: 'check-slot' });
  assert.match(content(), /14.00–14.30 uur/);
  click({ action: 'hint' });
  assert.match(content(), /2 help actions recorded/);
  click({ action: 'to-writing' }); click({ action: 'check-writing' });
  assert.match(content(), /kom ik/);
  listeners.get('document:input')({ target: { id: 'writing-draft', value: REVISED_DRAFT } });
  click({ action: 'submit-revision' });
  assert.match(content(), /ondersteunde oefening/);
  assert.match(content(), /Bekijk mijn eerste versie/);
  assert.match(content(), /komt ik/);
  listeners.get('#language-select:change')({ target: { value: 'all' } });
  assert.match(content(), /lang="fa" dir="rtl"/);
  click({ view: 'path' });
  assert.match(content(), /Een brug is geen nieuw officieel niveau/);
  click({ view: 'stories' });
  assert.match(content(), /De tas op de trein/);
});
