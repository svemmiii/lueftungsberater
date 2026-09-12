import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const source = fs.readFileSync(
  "custom_components/lueftungsberater/frontend/lueftungsberater-card.js",
  "utf8",
);

class HTMLElementStub {
  attachShadow() {
    const root = {
      innerHTML: "",
      querySelector() { return null; },
      querySelectorAll() { return []; },
    };
    this.shadowRoot = root;
    return root;
  }

  dispatchEvent() {
    return true;
  }
}

const storage = new Map();

const context = {
  console,
  HTMLElement: HTMLElementStub,
  customElements: { define() {}, get() { return undefined; } },
  window: {
    customCards: [],
    location: { pathname: "/" },
    addEventListener() {},
    removeEventListener() {},
    localStorage: {
      getItem(key) { return storage.has(key) ? storage.get(key) : null; },
      setItem(key, value) { storage.set(key, String(value)); },
    },
  },
  navigator: { language: "en-US" },
  document: {
    documentElement: { lang: "en" },
    createElement() {
      return {
        set textContent(value) { this._value = String(value); },
        get innerHTML() { return this._value ?? ""; },
      };
    },
    head: { appendChild() {} },
  },
  CustomEvent: class {},
  Event: class { constructor() { this.detail = {}; } },
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


// Compact/full room-card behavior is intentionally browser-persistent. The
// status header/recommendation always stays visible; ordinary details collapse,
// while night advice and an active hard window lock remain visible.
vm.runInContext("globalThis.__LBCard = LueftungsberaterCard", context);
const Card = context.__LBCard;

function localHass(entity, attributes, state = "open_now") {
  return {
    language: "de",
    config: { unit_system: { temperature: "°C" } },
    states: {
      [entity]: { state, last_updated: "2026-09-11T20:00:00+00:00", attributes },
    },
  };
}

const compact = new Card();
compact.setConfig({ entity: "sensor.compact_room" });
compact.hass = localHass("sensor.compact_room", {
  status: "green",
  room_name: "Wohnzimmer",
  recommendation: "Jetzt lüften",
  reason: "CO₂ ist erhöht",
  duration: "5–10 Minuten",
  duration_key: "minutes",
});
assert.equal(compact._isExpanded(), false);
assert.match(compact.shadowRoot.innerHTML, /Jetzt lüften/);
assert.doesNotMatch(compact.shadowRoot.innerHTML, /CO₂ ist erhöht/);
assert.doesNotMatch(compact.shadowRoot.innerHTML, /5–10 Minuten/);

compact._setExpanded(true);
assert.equal(
  storage.get("lueftungsberater-card:expanded:sensor.compact_room"),
  "1",
);
assert.match(compact.shadowRoot.innerHTML, /CO₂ ist erhöht/);
assert.match(compact.shadowRoot.innerHTML, /5–10 Minuten/);

const restored = new Card();
restored.setConfig({ entity: "sensor.compact_room" });
restored.hass = localHass("sensor.compact_room", {
  status: "green",
  room_name: "Wohnzimmer",
  recommendation: "Jetzt lüften",
  reason: "CO₂ ist erhöht",
});
assert.equal(restored._isExpanded(), true);

storage.set("lueftungsberater-card:expanded:sensor.locked_room", "0");
const locked = new Card();
locked.setConfig({ entity: "sensor.locked_room" });
locked.hass = localHass(
  "sensor.locked_room",
  {
    status: "locked",
    safety_lock: true,
    room_name: "Küche",
    recommendation: "Geschlossen lassen",
    reason: "Amtliche Warnung: Fenster und Türen geschlossen halten",
  },
  "keep_closed",
);
assert.equal(locked._isExpanded(), false);
assert.match(locked.shadowRoot.innerHTML, /Amtliche Warnung/);
assert.equal(
  storage.get("lueftungsberater-card:expanded:sensor.locked_room"),
  "0",
);

const night = new Card();
night.setConfig({ entity: "sensor.night_room" });
night.hass = localHass(
  "sensor.night_room",
  {
    status: "green",
    room_name: "Schlafzimmer",
    recommendation: "Aktuell kein Lüftungsgrund",
    reason: "Normale Bedingungen",
    night_ventilation: "Ab 23:00 Uhr voraussichtlich günstig.",
    night_ventilation_status: "later",
  },
  "room_good",
);
assert.match(night.shadowRoot.innerHTML, /Ab 23:00 Uhr/);
assert.doesNotMatch(night.shadowRoot.innerHTML, /Normale Bedingungen/);

const allClear = new Card();
allClear.setConfig({ entity: "sensor.clear_room" });
allClear.hass = localHass(
  "sensor.clear_room",
  {
    status: "green",
    room_name: "Bad",
    recommendation: "Aktuell kein Lüftungsgrund",
    warning_notice_kind: "all_clear",
    warning_notice_text: "Die amtliche Warnung wurde aufgehoben.",
  },
  "room_good",
);
assert.doesNotMatch(allClear.shadowRoot.innerHTML, /aufgehoben/);
allClear._setExpanded(true);
assert.match(allClear.shadowRoot.innerHTML, /aufgehoben/);

const forced = new Card();
forced.setConfig({ entity: "sensor.compact_room", force_expanded: true });
forced.hass = localHass("sensor.compact_room", {
  status: "green",
  room_name: "Wohnzimmer",
  recommendation: "Jetzt lüften",
  reason: "CO₂ ist erhöht",
});
assert.equal(forced._isExpanded(), true);
assert.match(forced.shadowRoot.innerHTML, /CO₂ ist erhöht/);

// Advisor discovery must react when an existing state becomes a complete room
// sensor without changing the total number of Home Assistant states.
vm.runInContext("globalThis.__LBOverview = LueftungsberaterOverviewCard", context);
const Overview = context.__LBOverview;
const overview = new Overview();
const incompleteStates = {
  "sensor.room": {
    entity_id: "sensor.room",
    state: "unknown",
    last_updated: "a",
    attributes: { friendly_name: "Wohnzimmer" },
  },
};
const completeStates = {
  "sensor.room": {
    entity_id: "sensor.room",
    state: "open_now",
    last_updated: "b",
    attributes: {
      status: "green",
      mode: "co2_lueften",
      recommendation: "Jetzt lüften",
      reason: "CO₂ ist erhöht",
      room_name: "Wohnzimmer",
    },
  },
};
const before = overview._localSignatureFor({ language: "de", states: incompleteStates });
const after = overview._localSignatureFor({ language: "de", states: completeStates }, true);
assert.notEqual(before, after);
assert.equal(Array.from(overview._localAdvisorIds).join(","), "sensor.room");

// Remote room preferences use the stable room id; renaming the room must not
// change the key. Name remains the fallback for old peers that expose no id.
assert.equal(
  overview._remoteRoomKey({ id: "remote:a" }, { id: "room-123", name: "Küche" }, 0),
  overview._remoteRoomKey({ id: "remote:a" }, { id: "room-123", name: "Wohnküche" }, 0),
);
assert.notEqual(
  overview._remoteRoomKey({ id: "remote:a" }, { name: "Küche" }, 0),
  overview._remoteRoomKey({ id: "remote:a" }, { name: "Wohnküche" }, 0),
);

// Shared localization requests must wake every card waiting on the same cache
// key, not only the first caller that created the WebSocket request.
vm.runInContext(`
  globalThis.__lbReadyA = 0;
  globalThis.__lbReadyB = 0;
  globalThis.__lbResolve = null;
  globalThis.__lbSharedHass = {
    language: "de",
    config: { unit_system: { temperature: "°C" } },
    callWS() {
      return new Promise((resolve) => { globalThis.__lbResolve = resolve; });
    },
  };
  globalThis.__lbSharedAttrs = {
    recommendation_key: "shared_pending_test",
    reason_key: "shared_pending_reason",
    reason_args: {},
    duration_key: "incomplete_data",
    night_ventilation_args: {},
  };
  lbLocalizedEntityTexts(__lbSharedHass, __lbSharedAttrs, () => { __lbReadyA += 1; });
  lbLocalizedEntityTexts(__lbSharedHass, __lbSharedAttrs, () => { __lbReadyB += 1; });
`, context);
assert.equal(vm.runInContext("LB_TEXT_PENDING.size", context), 1);
vm.runInContext('__lbResolve({ recommendation: "LOKALISIERT" })', context);
await new Promise((resolve) => setTimeout(resolve, 0));
assert.equal(vm.runInContext("__lbReadyA", context), 1);
assert.equal(vm.runInContext("__lbReadyB", context), 1);
assert.equal(vm.runInContext("LB_TEXT_PENDING.size", context), 0);

// The overview localization callback must rerender through its own render path;
// LueftungsberaterOverviewCard intentionally has no room-card _render() method.
const localizedOverview = new Overview();
let overviewRenders = 0;
localizedOverview._renderOverview = () => { overviewRenders += 1; };
localizedOverview._localizedTextsReady();
localizedOverview._localizedTextsReady();
await Promise.resolve();
assert.equal(overviewRenders, 1);
assert.equal(typeof localizedOverview._render, "undefined");


// A failed localization request must schedule a bounded retry instead of
// leaving cards on fallback text forever. Trigger the retry timer manually so
// the test stays fast, then verify the second request can complete normally.
vm.runInContext(`
  globalThis.__lbRetryReady = 0;
  globalThis.__lbRetryCalls = 0;
  globalThis.__lbRetryHass = {
    language: "de",
    config: { unit_system: { temperature: "°C" } },
    callWS() {
      __lbRetryCalls += 1;
      if (__lbRetryCalls === 1) return Promise.reject(new Error("temporary websocket failure"));
      return Promise.resolve({ recommendation: "RETRY-OK" });
    },
  };
  globalThis.__lbRetryAttrs = {
    recommendation_key: "retry_pending_test",
    reason_key: "retry_pending_reason",
    reason_args: {},
    duration_key: "incomplete_data",
    night_ventilation_args: {},
  };
  globalThis.__lbRetryCallback = () => {
    __lbRetryReady += 1;
    lbLocalizedEntityTexts(__lbRetryHass, __lbRetryAttrs, __lbRetryCallback);
  };
  lbLocalizedEntityTexts(__lbRetryHass, __lbRetryAttrs, __lbRetryCallback);
`, context);
await new Promise((resolve) => setTimeout(resolve, 0));
assert.equal(vm.runInContext("__lbRetryCalls", context), 1);
assert.equal(vm.runInContext("LB_TEXT_RETRY.size", context), 1);
vm.runInContext(`
  {
    const key = lbTextCacheKey(__lbRetryHass, __lbRetryAttrs);
    const retry = LB_TEXT_RETRY.get(key);
    clearTimeout(retry.timer);
    retry.timer = null;
    const waiting = [...retry.callbacks];
    retry.callbacks.clear();
    for (const callback of waiting) callback();
  }
`, context);
await new Promise((resolve) => setTimeout(resolve, 0));
assert.equal(vm.runInContext("__lbRetryCalls", context), 2);
assert.equal(vm.runInContext("__lbRetryReady", context), 2);
assert.equal(vm.runInContext("LB_TEXT_RETRY.size", context), 0);

// Advisor discovery must no longer scan every Home Assistant update. Known
// advisors are cheap to validate, while a full scan is scheduled and bounded so
// an existing sensor that becomes an advisor is still discovered shortly after.
const efficientOverview = new Overview();
const ordinary = {
  entity_id: "sensor.ordinary",
  state: "1",
  last_updated: "a",
  attributes: { friendly_name: "Ordinary" },
};
const advisor = {
  entity_id: "sensor.advisor",
  state: "open_now",
  last_updated: "a",
  attributes: {
    status: "green",
    mode: "co2_lueften",
    recommendation: "Jetzt lüften",
    reason: "CO₂ ist erhöht",
    room_name: "Wohnzimmer",
  },
};
const perfHass = { language: "de", states: { "sensor.ordinary": ordinary, "sensor.advisor": advisor } };
let discoveryScans = 0;
const originalDiscover = efficientOverview._discoverLocalAdvisors.bind(efficientOverview);
efficientOverview._discoverLocalAdvisors = (hass) => { discoveryScans += 1; originalDiscover(hass); };
efficientOverview._localSignatureFor(perfHass);
assert.equal(discoveryScans, 1);
// A repeated signature calculation inside the discovery window must validate
// only the known advisors and avoid another full scan.
efficientOverview._localSignatureFor(perfHass);
assert.equal(discoveryScans, 1);

const upgradedOrdinary = {
  ...ordinary,
  state: "open_now",
  last_updated: "b",
  attributes: {
    status: "yellow",
    mode: "feuchte_warten",
    recommendation: "Besser warten",
    reason: "Draußen ist es feuchter",
    room_name: "Küche",
  },
};
efficientOverview._hass = {
  language: "de",
  states: { "sensor.ordinary": upgradedOrdinary, "sensor.advisor": advisor },
};
efficientOverview._advisorDiscoveryDue = Date.now() + 5;
efficientOverview._localRenderSignature = efficientOverview._localSignatureFor(efficientOverview._hass);
efficientOverview._renderOverview = () => {};
await new Promise((resolve) => setTimeout(resolve, 15));
assert.ok(discoveryScans >= 2);
assert.equal(Array.from(efficientOverview._localAdvisorIds).sort().join(","), "sensor.advisor,sensor.ordinary");
