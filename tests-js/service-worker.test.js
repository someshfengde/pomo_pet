import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('../docs/sw.js', import.meta.url), 'utf8');
const scope = 'https://example.test/pomo_pet/';

function worker({ names = [], response, offline = false } = {}) {
  const handlers = {};
  const deleted = [];
  const writes = [];
  const cache = {
    match: async () => new Response('healthy cached content'),
    put: async (...args) => writes.push(args),
  };
  vm.runInNewContext(source, {
    self: {
      registration: { scope }, location: { origin: 'https://example.test' },
      addEventListener: (name, handler) => { handlers[name] = handler; },
      clients: { claim: async () => {} },
    },
    caches: {
      keys: async () => names,
      delete: async name => { deleted.push(name); },
      open: async () => cache,
    },
    fetch: async () => { if (offline) throw new Error('Network unavailable'); return response; },
    URL, Response,
  });
  return { handlers, deleted, writes };
}

async function dispatchFetch(instance, request) {
  let result;
  instance.handlers.fetch({ request, respondWith: promise => { result = promise; } });
  return result;
}

test('upgrades remove only this scoped app’s obsolete cache', async () => {
  const prefix = `pomo-pet-pwa:${scope}:`;
  const instance = worker({ names: [`${prefix}v19`, `${prefix}v20`, 'another-app', 'pomo-pet-pwa:https://example.test/other/:v19'] });
  let done;
  instance.handlers.activate({ waitUntil: promise => { done = promise; } });
  await done;
  assert.deepEqual(instance.deleted, [`${prefix}v19`]);
});

test('server errors and network outages preserve a healthy cached shell', async () => {
  for (const options of [{ response: new Response('Unavailable', { status: 503 }) }, { offline: true }]) {
    const instance = worker(options);
    const response = await dispatchFetch(instance, { method: 'GET', mode: 'navigate', url: scope });
    assert.equal(await response.text(), 'healthy cached content');
    assert.equal(instance.writes.length, 0);
  }
});

test('external requests and other apps are not intercepted', async () => {
  const instance = worker();
  for (const url of ['https://pets.example/sprite.webp', 'https://example.test/other/app.js']) {
    assert.equal(await dispatchFetch(instance, { method: 'GET', url, mode: 'cors' }), undefined);
  }
});
