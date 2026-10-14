// Run with node --test tests/test_example_security_alerts.js.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const monitorPath = path.join(root, 'examples/claude-code-sovereign-runtime/monitoring/behavioral-monitor.js');
const source = fs.readFileSync(monitorPath, 'utf8').split('const args = process.argv.slice(2);')[0];

function monitor(overrides = {}) {
  const context = { require: name => name === 'fs' ? Object.assign({}, fs, overrides) : require(name),
    process, console, Buffer };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context;
}

test('monitor handles initial read, append, truncation, replacement, deletion and recreation', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'safe2-monitor-test-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const file = path.join(dir, 'events.log');
  const read = monitor().readLogSnapshot;
  assert.equal(read(file), null);
  fs.writeFileSync(file, 'first\n');
  let state = read(file);
  assert.equal(state.content, 'first\n');
  fs.appendFileSync(file, 'second\n');
  state = read(file, state);
  assert.equal(state.content, 'second\n');
  fs.writeFileSync(file, 'new\n');
  state = read(file, state);
  assert.equal(state.content, 'new\n');
  fs.renameSync(file, path.join(dir, 'old.log'));
  fs.writeFileSync(file, 'replacement\n');
  state = read(file, state);
  assert.equal(state.content, 'replacement\n');
  fs.unlinkSync(file);
  assert.equal(read(file, state), null);
  fs.writeFileSync(file, 'recreated\n');
  assert.equal(read(file, null).content, 'recreated\n');
});

test('monitor reads the opened file even if pathname is replaced before metadata access', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'safe2-monitor-race-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const file = path.join(dir, 'events.log');
  fs.writeFileSync(file, 'original\n');
  const staged = path.join(dir, 'staged.log');
  fs.writeFileSync(staged, 'replacement\n');
  let closed = false;
  const context = monitor({
    openSync(name, flags) {
      // Simulate rename rotation landing between open() and any metadata call:
      // the replacement is staged elsewhere and atomically renamed into place.
      const fd = fs.openSync(name, flags);
      fs.renameSync(name, path.join(dir, 'moved.log'));
      fs.renameSync(staged, name);
      return fd;
    },
    statSync() { throw new Error('Path metadata must not be used'); },
    closeSync(fd) { closed = true; fs.closeSync(fd); },
  });
  assert.equal(context.readLogSnapshot(file).content, 'original\n');
  assert.equal(closed, true);
});

test('monitor closes descriptor when a read fails', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'safe2-monitor-fail-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const file = path.join(dir, 'events.log');
  fs.writeFileSync(file, 'data');
  let closed = false;
  const context = monitor({ readSync() { throw new Error('Read failure'); },
    closeSync(fd) { closed = true; fs.closeSync(fd); } });
  assert.throws(() => context.readLogSnapshot(file), /Read failure/);
  assert.equal(closed, true);
});

test('guide search displays hostile markup as text and preserves normal results', () => {
  const html = fs.readFileSync(path.join(root, 'guides/claude-code-velocity-and-governance.html'), 'utf8');
  const start = html.indexOf('const IDX');
  const end = html.indexOf("document.addEventListener('click'", start);
  assert.ok(start >= 0 && end > start);
  function element() {
    return { children: [], handlers: {}, value: '', classList: { add() {}, remove() {} },
      appendChild(child) { this.children.push(child); },
      addEventListener(name, fn) { this.handlers[name] = fn; },
      set innerHTML(value) { assert.equal(value, ''); this.children = []; },
    };
  }
  const input = element(), results = element();
  const context = { document: { getElementById: id => id === 's-inp' ? input : results,
    createElement: element } };
  vm.createContext(context);
  vm.runInContext(html.slice(start, end), context);
  input.value = '<img src=x onerror=alert(1)>';
  input.handlers.input.call(input);
  assert.equal(results.children.length, 1);
  assert.equal(results.children[0].textContent, 'No results for "<img src=x onerror=alert(1)>"');
  input.value = 'security';
  input.handlers.input.call(input);
  assert.ok(results.children.length > 0);
  assert.equal(results.children[0].children.length, 3);
  assert.ok(results.children[0].children[0].textContent);
});

test('monitor alerts once on a symlinked log path, keeps its offset, and recovers', t => {
  if (!fs.constants.O_NOFOLLOW) return t.skip('O_NOFOLLOW unavailable on this platform');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'safe2-monitor-link-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const file = path.join(dir, 'events.log');
  const context = monitor();
  const alerts = [];
  context.sendAlert = (type, message, details) => { alerts.push({ type, details }); return Promise.resolve(); };
  const seen = [];
  const handler = (_parsed, line) => seen.push(line);
  fs.writeFileSync(file, 'first\n');
  let state = context.pollLogFile(file, 'events.log', null, String, handler);
  fs.renameSync(file, path.join(dir, 'real.log'));
  fs.symlinkSync(path.join(dir, 'real.log'), file);
  const kept = context.pollLogFile(file, 'events.log', state, String, handler);
  context.pollLogFile(file, 'events.log', kept, String, handler);
  assert.equal(kept, state);
  assert.equal(alerts.length, 1);
  assert.equal(alerts[0].type, 'log_integrity');
  assert.equal(alerts[0].details.code, 'ELOOP');
  fs.unlinkSync(file);
  fs.writeFileSync(file, 'second\n');
  state = context.pollLogFile(file, 'events.log', kept, String, handler);
  assert.deepEqual(seen, ['first', 'second']);
  fs.unlinkSync(file);
  fs.symlinkSync(path.join(dir, 'real.log'), file);
  context.pollLogFile(file, 'events.log', state, String, handler);
  assert.equal(alerts.length, 2, 'a good read re-arms the alert');
});

test('monitor alerts instead of crashing when a log read fails', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'safe2-monitor-eio-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const file = path.join(dir, 'events.log');
  fs.writeFileSync(file, 'data\n');
  const context = monitor({ readSync() { throw Object.assign(new Error('I/O'), { code: 'EIO' }); } });
  const alerts = [];
  context.sendAlert = (type, message, details) => { alerts.push(details.code); return Promise.resolve(); };
  assert.equal(context.pollLogFile(file, 'events.log', null, String, () => {}), null);
  assert.deepEqual(alerts, ['EIO']);
});
