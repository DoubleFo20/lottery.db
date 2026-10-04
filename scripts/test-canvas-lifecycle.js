// Execute the actual TSX with controlled browser dependencies to check effect
// replay, unmount cancellation, and late image completion without a route fixture.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ts = require('../next-app/node_modules/typescript');

const effects = [];
const queue = new Map();
const listeners = new Map();
const images = [];
let nextId = 1;
let draws = 0;
let top = 0;
const canvas = {
  width: 0, height: 0,
  getBoundingClientRect: () => ({ width: 390, height: 844 }),
  getContext: () => ({ fillRect: () => draws++, drawImage: () => draws++ }),
};
const element = () => ({
  style: {}, textContent: '',
  getBoundingClientRect: () => ({ top, height: 3798 }),
});
const react = {
  useRef: current => ({ current }),
  useCallback: fn => fn,
  useEffect: setup => effects.push(setup),
};
const jsx = (tag, props) => {
  if (props.ref) props.ref.current = tag === 'canvas' ? canvas : element();
  return { tag, props };
};
const window = {
  innerHeight: 844, innerWidth: 390, devicePixelRatio: 2,
  matchMedia: () => ({
    matches: false, addEventListener() {}, removeEventListener() {},
  }),
  addEventListener: (event, callback) => listeners.set(event, callback),
  removeEventListener: (event, callback) => {
    if (listeners.get(event) === callback) listeners.delete(event);
  },
};
const document = {
  hidden: false, documentElement: { clientHeight: 844 },
  addEventListener: window.addEventListener,
  removeEventListener: window.removeEventListener,
};
const context = {
  exports: {}, window, document,
  Image: class {
    constructor() {
      this.complete = true;
      this.naturalWidth = 72;
      this.naturalHeight = 128;
      images.push(this);
    }
    decode() { return Promise.resolve(); }
  },
  requestAnimationFrame: callback => {
    const id = nextId++;
    queue.set(id, callback);
    return id;
  },
  cancelAnimationFrame: id => queue.delete(id),
  setTimeout, clearTimeout,
  require: name => {
    if (name === 'react') return react;
    if (name === 'react/jsx-runtime') return { jsx, jsxs: jsx };
    throw new Error('Unexpected dependency: ' + name);
  },
};
const source = fs.readFileSync(path.join(__dirname, '../next-app/src/components/StickyScrollCanvas.tsx'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    jsx: ts.JsxEmit.ReactJSX,
    target: ts.ScriptTarget.ES2020,
    esModuleInterop: true,
  },
}).outputText;
vm.runInNewContext(compiled, context);
context.exports.default({});

function settle() {
  for (let i = 0; queue.size && i < 200; i++) {
    const pending = [...queue];
    queue.clear();
    for (const [, callback] of pending) callback(i * 1000 / 60);
  }
  assert.equal(queue.size, 0, 'Animation did not settle');
}

(async () => {
  let cleanups = effects.map(setup => setup());
  settle();
  const placeholderDraws = draws;
  assert(placeholderDraws > 0);
  top = -1477;
  listeners.get('scroll')();
  settle();
  assert.equal(draws, placeholderDraws, 'Unchanged placeholder repainted');
  listeners.get('scroll')();
  assert(queue.size > 0);
  cleanups.forEach(cleanup => cleanup());
  assert.equal(queue.size, 0, 'Unmount left pending rAF');
  assert.equal(listeners.size, 0, 'Unmount left browser listeners');
  await images[0].onload();
  assert.equal(queue.size, 0, 'Late completion woke an unmounted effect');

  // Strict Mode setup -> cleanup -> setup uses the same ref objects.
  cleanups = effects.map(setup => setup());
  settle();
  await images.at(-1).onload();
  await Promise.resolve();
  assert(queue.size > 0, 'Image completion did not wake replayed effect');
  settle();
  assert(draws > placeholderDraws, 'Loaded image did not replace placeholder');
  top = -2000;
  listeners.get('scroll')();
  document.hidden = true;
  listeners.get('visibilitychange')();
  assert.equal(queue.size, 0, 'Hidden document retained rAF');
  document.hidden = false;
  listeners.get('visibilitychange')();
  assert(queue.size > 0, 'Visible document did not resume');
  settle();
  cleanups.forEach(cleanup => cleanup());
  console.log('PASS: TSX lifecycle, idle fallback, late completion, effect replay, visibility');
})().catch(error => { console.error(error); process.exitCode = 1; });
