import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js', 'utf8');
class Element {
  attachShadow() {
    this.shadowRoot = {innerHTML: '', querySelector() {return null;}, querySelectorAll() {return [];}};
    return this.shadowRoot;
  }
  dispatchEvent() {return true;}
}
const escape = (s) => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const context = {console, HTMLElement: Element, customElements: {get() {}, define() {}},
  window: {customCards: [], localStorage: {getItem() {return null;}, setItem() {}},
    location: {pathname: '/'}, addEventListener() {}, removeEventListener() {}},
  navigator: {language: 'de-DE'},
  document: {documentElement: {lang: 'de'}, createElement() {
    return {set textContent(v) {this.value = String(v);}, get innerHTML() {return escape(this.value ?? '');}};
  }, head: {appendChild() {}}}, setTimeout, clearTimeout, Event: class {}, CustomEvent: class {}};
vm.createContext(context);
vm.runInContext(`${source}\nglobalThis.Card = LueftungsberaterCard`, context);
const official = {
  id: 'dwd.1', provider: 'nina_auto_dwd', relevant: true, headline: 'Schwere Sturmböen',
  wind: true, phase: 'prelock', hard_lock: true, level: 'lock', gust_min_kmh: 90, gust_max_kmh: 100,
  onset: '2026-10-23T13:00:00+00:00', lock_from: '2026-10-23T12:30:00+00:00',
  ends: '2026-10-23T20:00:00+00:00', official_instruction: 'Sichern Sie Gegenstände.',
};
function render(attributes, {expanded = false, language = 'de', stale = false} = {}) {
  const card = new context.Card();
  card.setConfig({entity: 'sensor.test', force_expanded: expanded, remote_stale: stale});
  card.hass = {language, config: {time_zone: 'Europe/Berlin', unit_system: {temperature: '°C'}},
    states: {'sensor.test': {state: 'wait', attributes: {
      status: 'yellow', room_name: 'Wohnung', temperature_inside: 22, temperature_outside: 11,
      humidity_inside: 59, humidity_outside: 82, ...attributes,
    }}}};
  return card.shadowRoot.innerHTML;
}
let cases = 0;
for (const language of ['de', 'en', 'tr']) for (const expanded of [false, true]) {
  const html = render({warning_notices: [official]}, {expanded, language});
  assert.match(html, /Schwere Sturmböen/);
  assert.match(html, /90–100 km\/h/);
  assert.match(html, /15:00/);
  assert.match(html, /14:30/);
  assert.match(html, /22:00/);
  assert.match(html, /DWD \/ NINA/);
  assert.match(html, /Sichern Sie Gegenstände/);
  assert.doesNotMatch(html, /Invalid Date|undefined|\[object Object\]/);
  cases++;
}
const cancelled = {warning_notice_kind: 'all_clear', warning_notice_text: 'Entwarnung-Test'};
assert.doesNotMatch(render(cancelled), /Entwarnung-Test/);
assert.match(render(cancelled, {expanded: true}), /Entwarnung-Test/);
assert.doesNotMatch(render({warning_notices: [official]}, {stale: true}), /Schwere Sturmböen/);
const broken = {...official, onset: 'not-a-date', ends: {}, lock_from: '2026-10-23T12:30', official_instruction: {bogus: 1}, headline: '<img src=x onerror=alert(1)>'};
const html = render({warning_notices: [broken]});
assert.match(html, /&lt;img/);
assert.doesNotMatch(html, /<img|Invalid Date|undefined|\[object Object\]/);
assert.doesNotMatch(render({warning_notices: [{...official, relevant: false}]}), /Schwere Sturmböen/);
assert.doesNotMatch(render({warning_notices: [official], ...cancelled}, {expanded: true}), /Entwarnung-Test/);
const exclusive = render({warning_notices: [{...official, hard_lock: false, level: 'strong',
  gust_min_kmh: 89.99999999999, gust_max_kmh: 89.99999999999, gust_original_text: '<90 [km/h]'}]});
assert.match(exclusive, /&lt;90 km\/h/);
assert.doesNotMatch(exclusive, /Angekündigte Böen: 90 km\/h/);
for (const original of ['unter 90 km/h', 'less than 90 km/h', 'inférieures à 90 km/h',
  'inferiores a 90 km/h', 'minder dan 90 km/h', '<=90 km/h', '≤90 km/h']) {
  for (const expanded of [false, true]) {
    const bounded = render({warning_notices: [{...official, hard_lock: false, level: 'strong',
      gust_min_kmh: 89.99999999999, gust_max_kmh: 89.99999999999,
      gust_original_text: original}]}, {expanded});
    assert.ok(bounded.includes(escape(original)), `Missing original bound: ${original}`);
    assert.doesNotMatch(bounded, /Angekündigte Böen: 90 km\/h/);
  }
}
for (const expanded of [false, true]) {
  const restricted = 'Böen bis 120 km/h in exponierten Lagen.';
  const advisory = render({warning_notices: [{...official, hard_lock: false, level: 'caution',
    gust_min_kmh: null, gust_max_kmh: null, description: restricted}]}, {expanded});
  assert.ok(advisory.includes(restricted));
}
for (const language of ['de', 'en', 'tr']) for (const expanded of [false, true]) {
  const conflict = render({warning_notices: [{...official, gust_min_kmh: 110, gust_max_kmh: 110,
    gust_original_text: '110 km/h', gust_conflict: true, gust_evidence: [
      {source: 'description', statement: 'Böen 110 km/h.'},
      {source: 'parameter', statement: 'gusts 70 km/h'},
    ]}]}, {language, expanded});
  assert.match(conflict, /110 km\/h/);
  assert.match(conflict, /70 km\/h/);
  assert.match(conflict, /Widersprüchliche|Conflicting|çelişiyor/);
  assert.doesNotMatch(conflict, /warning\.[a-z_]+|undefined|\[object Object\]/);
  const scoped = render({warning_notices: [{...official, hard_lock: false, level: 'caution',
    gust_max_kmh: null, gust_min_kmh: null, gust_scope_uncertain: true, gust_time_uncertain: true,
    description: 'Böen 110 km/h ausschließlich in den Bergen, später.', phase: 'time_uncertain'}]}, {language, expanded});
  assert.match(scoped, /ausschließlich in den Bergen/);
  assert.doesNotMatch(scoped, /warning\.[a-z_]+|undefined|\[object Object\]/);
  const polarity = render({warning_notices: [{...official, hard_lock: false, level: 'caution',
    gust_max_kmh: null, gust_min_kmh: null, headline: 'Keine Böen 110 km/h erwartet',
    description: 'Böen 110 km/h werden erwartet.', gust_conflict: true, gust_polarity_conflict: true,
    gust_evidence: [
      {source: 'headline', statement: 'Keine Böen 110 km/h erwartet'},
      {source: 'event', statement: 'Keine Böen 110 km/h erwartet (Ereignis)'},
      {source: 'description', statement: 'Böen 110 km/h werden erwartet.'},
      {source: 'parameter', statement: 'gusts 110 km/h'},
    ]}]}, {language, expanded});
  assert.match(polarity, /Keine Böen 110 km\/h erwartet/);
  assert.match(polarity, /Böen 110 km\/h werden erwartet/);
  assert.match(polarity, /Ereignis|Event|Olay/);
  assert.match(polarity, /Böenprognose unklar|gust forecast is uncertain|rüzgâr tahmini belirsiz/);
  assert.doesNotMatch(polarity, /warning\.[a-z_]+|undefined|\[object Object\]/);
  cases += 3;
}
const unsafeEvidence = render({warning_notices: [{...official, gust_conflict: true,
  gust_evidence: [null, {}, {source: 'parameter', statement: '<img src=x onerror=alert(1)>'}]}]});
assert.match(unsafeEvidence, /&lt;img/);
assert.doesNotMatch(unsafeEvidence, /<img|\[object Object\]/);
for (const language of ['de', 'en', 'tr']) for (const expanded of [false, true]) {
  const timeConflict = render({warning_notices: [{...official, headline: 'Böen ab 18:00 UTC',
    gust_conflict: true, gust_time_conflict: true, gust_onset: '2026-10-23T14:00:00+00:00',
    lock_from: '2026-10-23T13:30:00+00:00', gust_evidence: [
      {source: 'headline', statement: 'Böen 110 km/h ab 18:00 UTC.'},
      {source: 'description', statement: 'Böen 110 km/h ab 14:00 UTC.'},
    ]}]}, {language, expanded});
  assert.match(timeConflict, /Zeitangaben|time statements|zaman bilgileri/);
  assert.match(timeConflict, /ab 18:00 UTC/);
  assert.match(timeConflict, /ab 14:00 UTC/);
  assert.match(timeConflict, /15:30/);
  assert.doesNotMatch(timeConflict, /warning\.[a-z_]+|undefined|\[object Object\]/);
  const combined = render({warning_notices: [{...official, gust_conflict: true,
    gust_time_conflict: true, gust_polarity_conflict: true}]}, {language, expanded});
  assert.match(combined, /Zeitangaben|time statements|zaman bilgileri/);
  assert.match(combined, /Böenprognose unklar|gust forecast is uncertain|rüzgâr tahmini belirsiz/);
  cases += 2;
}
for (const language of ['de', 'en', 'tr']) for (const expanded of [false, true]) {
  for (const summaryFlag of [false, true]) for (const polarityConflict of [false, true]) {
    const notice = {...official, gust_conflict: true, gust_time_conflict: true,
      gust_polarity_conflict: polarityConflict, gust_evidence: [
        null,
        {source: 'headline', statement: 'Böen 110 km/h ab 14:00 UTC.', value_conflict: true, time_conflict: true},
        {source: 'description', statement: 'Böen 110 km/h ab 18:00 UTC.', value_conflict: true, time_conflict: true},
        {source: 'parameter', statement: 'Böen 70 km/h', value_conflict: true},
      ]};
    if (summaryFlag) notice.gust_value_conflict = true;
    const allConflicts = render({warning_notices: [notice]}, {language, expanded});
    assert.match(allConflicts, /Widersprüchliche amtliche Böenangaben|Conflicting official gust values|Resmî rüzgâr hamlesi değerleri çelişiyor/);
    assert.match(allConflicts, /Zeitangaben|time statements|zaman bilgileri/);
    assert.match(allConflicts, /ab 14:00 UTC/);
    assert.match(allConflicts, /ab 18:00 UTC/);
    assert.match(allConflicts, /70 km\/h/);
    if (polarityConflict) assert.match(allConflicts, /Böenprognose unklar|gust forecast is uncertain|rüzgâr tahmini belirsiz/);
    assert.doesNotMatch(allConflicts, /warning\.[a-z_]+|undefined|\[object Object\]/);
    cases++;
  }
}
console.log(`PASS: ${cases} warning language/expansion cases plus conflicts, scoped notices, cancellation, dates, stale remote, escaping and relevance`);
