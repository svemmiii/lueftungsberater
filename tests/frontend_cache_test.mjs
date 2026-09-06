import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const source = fs.readFileSync(
  "custom_components/lueftungsberater/frontend/lueftungsberater-card.js",
  "utf8",
);

class HTMLElementStub {
  attachShadow() {
    return {};
  }
}

const context = {
  console,
  HTMLElement: HTMLElementStub,
  customElements: { define() {}, get() { return undefined; } },
  window: {
    customCards: [],
    location: { pathname: "/" },
    addEventListener() {},
    removeEventListener() {},
  },
  navigator: { language: "en-US" },
  document: {
    documentElement: { lang: "en" },
    createElement() { return {}; },
    head: { appendChild() {} },
  },
  CustomEvent: class {},
  setTimeout,
  clearTimeout,
};
vm.createContext(context);
vm.runInContext(source, context, { filename: "lueftungsberater-card.js" });

for (let i = 0; i < 300; i += 1) {
  vm.runInContext(`lbTextCacheSet("key-${i}", { value: ${i} })`, context);
}

assert.equal(vm.runInContext("LB_TEXT_CACHE.size", context), 256);
assert.equal(vm.runInContext('LB_TEXT_CACHE.has("key-0")', context), false);
assert.equal(vm.runInContext('LB_TEXT_CACHE.has("key-44")', context), true);

// Access key-44 so it becomes the most recently used entry, then insert one
// more item. The next oldest key must be evicted instead of key-44.
assert.equal(vm.runInContext('lbTextCacheGet("key-44").value', context), 44);
vm.runInContext('lbTextCacheSet("key-300", { value: 300 })', context);
assert.equal(vm.runInContext('LB_TEXT_CACHE.has("key-44")', context), true);
assert.equal(vm.runInContext('LB_TEXT_CACHE.has("key-45")', context), false);
assert.equal(vm.runInContext("LB_TEXT_CACHE.size", context), 256);
