const assert = require('node:assert/strict');
const { test } = require('node:test');
const advisory = require('../assets/miss_advisory.js');
const now = Date.parse('2027-02-01T00:00:00Z');
const dates = ['2026-10-16', '2026-11-01', '2026-11-16', '2026-12-01', '2026-12-16', '2027-01-01'];
const draws = new Map(dates.map(date => [date, '123456']));
const history = dates.map(date => ({
  target_date: date, draw_date_used: '2026-10-01',
  logged_at: date + 'T12:00:00', actual_result: '123456',
  candidates: [{ number: '000000' }],
}));
const predict = { ensemble_weights: { a: 0.4, b: 0.6 }, meta: { params: { top: 5, beam: 5, window: 50 } } };

test('six verified misses count six distinct draws', () => {
  assert.equal(advisory.evaluate(history, draws, '2026-10-01', now).misses, 6);
});
test('an exact win resets the streak; a subsequent miss starts at one', () => {
  const winning = history.map(entry => ({ ...entry }));
  winning[4] = { ...winning[4], candidates: [{ number: '123456' }] };
  assert.equal(advisory.evaluate(winning, draws, '2026-10-01', now).misses, 1);
  winning[5] = { ...winning[5], candidates: [{ number: '123456' }] };
  assert.equal(advisory.evaluate(winning, draws, '2026-10-01', now).misses, 0);
});
test('duplicate runs for the same draw are counted once, latest pre-draw run wins', () => {
  const first = history[0];
  const win = { ...first, logged_at: first.target_date + 'T13:00:00', candidates: [{ number: '123456' }] };
  const result = advisory.evaluate([first, first, win], new Map([[dates[0], '123456']]), '2026-10-01', now);
  assert.equal(result.misses, 0);
  assert.equal(result.evaluated, 1);
});
test('future or post-draw predictions cannot prove a miss', () => {
  const future = advisory.evaluate(history, draws, '2026-10-01', Date.parse('2026-10-05'));
  assert.equal(future.status, 'waiting');
  const late = history.map(entry => ({ ...entry, logged_at: entry.target_date + 'T14:30:00+07:00' }));
  assert.equal(advisory.evaluate(late, draws, '2026-10-01', now).status, 'insufficient');
});
test('mismatched actuals and malformed candidates are not evaluated', () => {
  for (const bad of [
    { ...history.at(-1), actual_result: '999999' },
    { ...history.at(-1), candidates: [{ number: '<img>' }] },
    { ...history.at(-1), logged_at: 'invalid' },
  ]) {
    assert.equal(advisory.evaluate([...history.slice(0, -1), bad], draws, '2026-10-01', now).misses, null);
  }
});
test('an unlogged latest draw breaks consecutive evidence', () => {
  assert.equal(advisory.evaluate(history.slice(0, -1), draws, '2026-10-01', now).status, 'insufficient');
});
test('policy reset keeps history and awaits new evaluated draws', () => {
  const oldDraws = new Map([['2026-10-01', '402701']]);
  const checkpoint = advisory.checkpoint(null, predict, oldDraws);
  const result = advisory.evaluate(history, oldDraws, checkpoint.afterDraw, now);
  assert.equal(result.status, 'waiting');
  assert.equal(result.misses, 0);
  assert.equal(history.length, 6);
});
test('refresh timestamps and candidate changes do not reset; weight/param changes do', () => {
  const checkpoint = advisory.checkpoint(null, predict, draws);
  const refresh = { ...predict, candidates: [{ number: '111111' }], generated_at: 'new' };
  assert.equal(advisory.checkpoint(checkpoint, refresh, draws).afterDraw, '2026-10-01');
  const changed = { ...predict, ensemble_weights: { a: 0.5, b: 0.5 } };
  const updated = advisory.checkpoint(checkpoint, changed, draws);
  assert.equal(updated.afterDraw, '2027-01-01');
  assert.equal(updated.reason, 'model-changed');
  assert.equal(advisory.checkpoint(updated, changed, draws).afterDraw, updated.afterDraw);
  const params = { ...predict, meta: { params: { top: 5, beam: 6, window: 50 } } };
  assert.equal(advisory.checkpoint(checkpoint, params, draws).reason, 'model-changed');
});
test('weight key ordering and missing configuration do not reset', () => {
  const checkpoint = advisory.checkpoint(null, predict, draws);
  const reordered = { ...predict, ensemble_weights: { b: 0.6, a: 0.4 } };
  assert.equal(advisory.checkpoint(checkpoint, reordered, draws).afterDraw, checkpoint.afterDraw);
  assert.equal(advisory.checkpoint(checkpoint, {}, draws).afterDraw, checkpoint.afterDraw);
});
test('CSV validation preserves leading zeros and rejects conflicts', () => {
  assert.equal(advisory.parseDraws('draw_date,first_prize\n2026-10-01,012345').get('2026-10-01'), '012345');
  assert.throws(() => advisory.parseDraws('wrong,columns\n2026-10-01,123456'));
  assert.throws(() => advisory.parseDraws('draw_date,first_prize\n2026-10-01,123456\n2026-10-01,654321'));
});
test('fetch failure displays unavailable instead of a synthetic miss count', async () => {
  const result = await advisory.load(async () => ({ ok: false }), predict, null);
  assert.equal(result.status, 'unavailable');
  assert.equal(result.misses, null);
});
test('monitoring requests bypass cached historical snapshots', async () => {
  const requests = [];
  const fetch = async (url, options) => {
    requests.push(options);
    return url.includes('.json')
      ? { ok: true, json: async () => [] }
      : { ok: true, text: async () => 'draw_date,first_prize\n2026-10-01,402701' };
  };
  assert.equal((await advisory.load(fetch, predict, null)).status, 'waiting');
  assert(requests.every(options => options.cache === 'no-store'));
});
test('unavailable localStorage does not prevent tracking', async () => {
  const storage = { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); } };
  const fetch = async url => url.includes('.json')
    ? { ok: true, json: async () => [] }
    : { ok: true, text: async () => 'draw_date,first_prize\n2026-10-01,402701' };
  assert.equal((await advisory.load(fetch, predict, storage)).status, 'waiting');
});
