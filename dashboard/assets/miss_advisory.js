/* Shared Manager advisory policy. Resetting monitoring never rewrites results. */
(function (root) {
  'use strict';
  const POLICY = '2026-10-05-v1';
  const RESET_AFTER_DRAW = '2026-10-01';
  const STORAGE_KEY = 'lottery-miss-advisory';
  const datePattern = /^\d{4}-\d{2}-\d{2}$/;
  const numberPattern = /^\d{6}$/;

  function parseDraws(csv) {
    const lines = csv.trim().split(/\r?\n/);
    const headers = lines.shift().replace(/^\uFEFF/, '').split(',');
    const dateIndex = headers.indexOf('draw_date');
    const prizeIndex = headers.indexOf('first_prize');
    if (dateIndex < 0 || prizeIndex < 0) throw new Error('Invalid draw history columns');
    const draws = new Map();
    for (const line of lines) {
      const fields = line.split(',').map(value => value.trim());
      const date = fields[dateIndex];
      const prize = fields[prizeIndex];
      if (datePattern.test(date) && numberPattern.test(prize)) {
        if (draws.has(date) && draws.get(date) !== prize) throw new Error('Conflicting draw results');
        draws.set(date, prize);
      }
    }
    if (!draws.size) throw new Error('No verified draws');
    return draws;
  }

  function signature(predict) {
    const weights = predict?.ensemble_weights;
    const params = predict?.meta?.params || {};
    if (!weights || !Object.keys(weights).length) return null;
    return JSON.stringify([
      Object.keys(weights).sort().map(key => [key, weights[key]]),
      ['top', 'beam', 'window'].map(key => params[key] ?? null),
    ]);
  }

  function checkpoint(previous, predict, draws) {
    const model = signature(predict);
    const dates = [...draws.keys()].sort();
    const latest = dates.at(-1);
    const validPrevious = previous && previous.policy === POLICY &&
      datePattern.test(previous.afterDraw) && previous.afterDraw >= RESET_AFTER_DRAW;
    let afterDraw = validPrevious ? previous.afterDraw : RESET_AFTER_DRAW;
    let reason = validPrevious ? previous.reason : 'policy-reset';
    if (validPrevious && previous.model && model && previous.model !== model) {
      afterDraw = latest > afterDraw ? latest : afterDraw;
      reason = 'model-changed';
    }
    return { policy: POLICY, model: model || (validPrevious ? previous.model : null), afterDraw, reason };
  }

  function evaluate(history, draws, afterDraw, now = Date.now()) {
    if (!Array.isArray(history)) throw new Error('Invalid prediction history');
    const predictions = new Map();
    for (const entry of history) {
      const date = entry?.target_date;
      const actual = draws.get(date);
      if (!datePattern.test(date) || !actual || date <= afterDraw) continue;
      const cutoff = Date.parse(date + 'T14:30:00+07:00');
      const rawLogged = entry.logged_at;
      const logged = typeof rawLogged === 'string'
        ? Date.parse(/[zZ]$|[+-]\d{2}:?\d{2}$/.test(rawLogged) ? rawLogged : rawLogged + '+07:00')
        : NaN;
      const candidates = entry.candidates;
      if (!Number.isFinite(logged) || logged >= cutoff || cutoff > now ||
          !datePattern.test(entry.draw_date_used) || entry.draw_date_used >= date ||
          !Array.isArray(candidates) || !candidates.length ||
          candidates.some(candidate => typeof candidate?.number !== 'string' || !numberPattern.test(candidate.number)) ||
          (entry.actual_result && entry.actual_result !== actual)) continue;
      const current = predictions.get(date);
      if (!current || logged > current.logged) {
        predictions.set(date, {
          logged, hit: candidates.some(candidate => candidate.number === actual),
        });
      }
    }
    const dates = [...draws.keys()].filter(date =>
      date > afterDraw && Date.parse(date + 'T14:30:00+07:00') <= now).sort().reverse();
    let misses = 0;
    let evaluated = 0;
    for (const date of dates) {
      const prediction = predictions.get(date);
      // An unobserved draw breaks evidence of a consecutive streak.
      if (!prediction) {
        return { misses: null, evaluated, status: 'insufficient', afterDraw };
      }
      evaluated++;
      if (prediction.hit) return { misses, evaluated, status: 'ready', afterDraw };
      misses++;
    }
    return { misses, evaluated, status: evaluated ? 'ready' : 'waiting', afterDraw };
  }

  async function load(fetchFile, predict, storage) {
    try {
      const [historyResponse, drawResponse] = await Promise.all([
        fetchFile('database/predictions/prediction_history.json?ts=' + Date.now(), { cache: 'no-store' }),
        fetchFile('database/dataset/lottery_history.csv?ts=' + Date.now(), { cache: 'no-store' }),
      ]);
      if (!historyResponse?.ok || !drawResponse?.ok) throw new Error('Advisory data unavailable');
      const [history, csv] = await Promise.all([historyResponse.json(), drawResponse.text()]);
      const draws = parseDraws(csv);
      let previous = null;
      try { previous = JSON.parse(storage?.getItem(STORAGE_KEY) || 'null'); } catch { /* storage unavailable */ }
      const state = checkpoint(previous, predict, draws);
      try { storage?.setItem(STORAGE_KEY, JSON.stringify(state)); } catch { /* keep tracking from shared policy */ }
      return { ...evaluate(history, draws, state.afterDraw), reason: state.reason };
    } catch {
      return { misses: null, evaluated: 0, status: 'unavailable', afterDraw: null };
    }
  }

  const advisory = { parseDraws, signature, checkpoint, evaluate, load };
  root.LotteryMissAdvisory = advisory;
  if (typeof module !== 'undefined' && module.exports) module.exports = advisory;
})(typeof window !== 'undefined' ? window : globalThis);
