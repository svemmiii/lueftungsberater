import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js', 'utf8');
class ElementStub {
  attachShadow() {
    this.shadowRoot = { innerHTML: '', querySelector() { return null; }, querySelectorAll() { return []; } };
    return this.shadowRoot;
  }
  dispatchEvent() { return true; }
}
const context = {
  console, HTMLElement: ElementStub, customElements: { get() {}, define() {} },
  window: {
    customCards: [], location: { pathname: '/' }, addEventListener() {}, removeEventListener() {},
    localStorage: { getItem() { return null; }, setItem() {} },
  },
  navigator: { language: 'de-DE' },
  document: {
    documentElement: { lang: 'de' },
    createElement() {
      return {
        set textContent(value) { this.value = String(value); },
        get innerHTML() { return this.value ?? ''; },
      };
    },
    head: { appendChild() {} },
  },
  setTimeout, clearTimeout, setInterval, clearInterval,
  Event: class {}, CustomEvent: class {},
};
vm.createContext(context);
vm.runInContext(source + '\nglobalThis.Room = LueftungsberaterCard; globalThis.textCache = LB_TEXT_CACHE; globalThis.textCacheKey = lbTextCacheKey;', context);

const hass = {
  language: 'de', states: {},
  config: { unit_system: { temperature: '°C' }, time_zone: 'Europe/Berlin' },
};
const room = new context.Room();
room._hass = hass;
room._config = { entity: 'sensor.test', force_expanded: true };

// Both custom modes must describe a stale contact as unconfirmed, not as a
// window continuously open since the last valid observation.
for (const state of ['grace', 'unknown', 'unavailable']) {
  const attrs = {
    has_window_contacts: true, window_open: true, open_minutes: 9,
    window_data_status: state, last_confirmed_airing: '2026-11-01T15:00:00Z',
  };
  const values = room._metricItems(attrs, '°C');
  assert.match(values.last_airing, /Fensterzustand derzeit nicht verfügbar/);
  assert.match(values.last_airing, /lb-missing/);
  assert.doesNotMatch(values.last_airing, /gerade offen|seit 9 Minuten|Zuletzt gelüftet/);
  assert.match(values.window_state, /Fensterzustand derzeit nicht verfügbar/);
  // The underlying last-known state must not be altered by rendering.
  assert.equal(attrs.window_open, true);
  assert.equal(attrs.open_minutes, 9);
}
const normal = room._metricItems({
  has_window_contacts: true, window_open: true, open_minutes: 9,
  window_data_status: 'current',
}, '°C');
assert.match(normal.last_airing, /seit 9 Minuten/);
const noContact = room._metricItems({
  has_window_contacts: false, window_open: false,
  window_data_status: 'not_configured',
}, '°C');
assert.doesNotMatch(noContact.last_airing, /Fensterzustand derzeit nicht verfügbar/);

function render(attrs, config = {}) {
  room._config = { entity: 'sensor.test', force_expanded: true, ...config };
  room._renderSignature = null;
  const state = {
    state: attrs.recommendation_key || 'open_now',
    attributes: { room_name: 'Wohnzimmer', display_mode: 'room_air', status: 'orange',
      room_status: 'orange', ventilation_status: 'green', ...attrs },
  };
  if (config.remote_snapshot) room._config.remote_snapshot = state;
  else hass.states['sensor.test'] = state;
  room._render();
  return room.shadowRoot.innerHTML;
}
for (const settings of [
  { layout: 'split', hidden: ['window_state'] },
  { layout: 'classic', hidden: ['window_state'] },
]) {
  const html = render({
    has_window_contacts: true, window_open: true, open_minutes: 9,
    window_data_status: 'unavailable',
  }, { display_settings: settings });
  assert.match(html, /Fensterzustand derzeit nicht verfügbar/);
  assert.doesNotMatch(html, /Fenster\/Tür gerade offen/);
  assert.doesNotMatch(html, /seit 9 Minuten/);
}

const old = {
  display_mode: 'ventilation', action_semantics_version: 1,
  status: 'green', ventilation_status: 'green',
  ventilation_suitability_status: 'green',
  room_status: 'green', recommendation_key: 'keep_closed',
  native_ventilation_recommendation_key: 'open_now',
  recommendation: 'Fenster geschlossen lassen',
  reason_key: 'outside_too_cold',
  reason: 'Draußen zu kalt zum Lüften',
  warning_notice_kind: 'info', warning_notice_text: 'Amtlicher Hinweis aus dem Wetterdienst',
};
const legacyConfig = { remote_snapshot: true };
let html = render(old, legacyConfig);
assert.match(html, /Jetzt lüften/);
assert.doesNotMatch(html, /Fenster geschlossen lassen|Draußen zu kalt zum Lüften/);
assert.match(html, /Amtlicher Hinweis aus dem Wetterdienst/);

// Even a delayed/cached localization result must not reintroduce the wrong
// room-side reason into an older ventilation remote view.
const localizeAttrs = { ...old, recommendation_key: 'open_now' };
context.textCache.set(context.textCacheKey(hass, localizeAttrs), {
  recommendation: 'Jetzt lüften', reason: 'Draußen zu kalt zum Lüften',
});
html = render(old, legacyConfig);
assert.match(html, /Jetzt lüften/);
assert.doesNotMatch(html, /Draußen zu kalt zum Lüften/);

// Only the affected intermediate schema is filtered: modern remote snapshots
// and old room-air perspectives keep their genuine reasons.
// The test-localized fixture above must not leak into the modern example.
context.textCache.clear();
html = render({ ...old, action_semantics_version: undefined,
  perspective_semantics_version: 2, recommendation_key: 'open_now',
  recommendation: 'Jetzt lüften', reason: 'Lüftungsbedingungen sind gut',
}, legacyConfig);
assert.match(html, /Lüftungsbedingungen sind gut/);
html = render({ ...old, display_mode: 'room_air',
  reason: 'Draußen zu kalt zum Lüften',
}, legacyConfig);
assert.match(html, /Draußen zu kalt zum Lüften/);
html = render({ ...old, safety_lock: true, status: 'locked',
  reason: 'Amtliche Sicherheitssperre aktiv',
}, legacyConfig);
assert.match(html, /Amtliche Sicherheitssperre aktiv/);
console.log('PASS: stale window-contact fields and untrusted v0.12.0 remote explanations');
