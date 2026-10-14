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
  let closed = false;
  const context = monitor({
    openSync(name, flags) {
      const fd = fs.openSync(name, flags);
      fs.renameSync(name, path.join(dir, 'moved.log'));
      fs.writeFileSync(name, 'replacement\n');
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
