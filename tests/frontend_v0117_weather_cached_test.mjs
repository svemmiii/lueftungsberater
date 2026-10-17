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
const context = {console, HTMLElement: Element, customElements: {get() {}, define() {}},
  window: {customCards: [], localStorage: {getItem() {return null;}, setItem() {}},
    location: {pathname: '/'}, addEventListener() {}, removeEventListener() {}},
  navigator: {language: 'de-DE'},
  document: {documentElement: {lang: 'de'}, createElement() {
    return {set textContent(v) {this.value = String(v);}, get innerHTML() {return this.value ?? '';}};
  }, head: {appendChild() {}}}, setTimeout, clearTimeout, Event: class {}, CustomEvent: class {}};
vm.createContext(context);
vm.runInContext(`${source}\nglobalThis.Card = LueftungsberaterCard`, context);
const wording = {
  de: ['Letzte gültige Wetterprognose wird verwendet', 'Wetterprognose nicht verfügbar', 'wird nicht verwendet'],
  en: ['Using the last valid weather forecast', 'Weather forecast unavailable', 'not being used'],
  tr: ['Son geçerli hava tahmini kullanılıyor', 'Hava tahmini kullanılamıyor', 'kullanılmıyor'],
};
let scenarios = 0;
for (const language of ['de', 'en', 'tr']) for (const layout of ['classic', 'split']) {
  for (const [status, cached] of [['fresh', false], ['stale', true], ['stale', false], ['unavailable', false]]) {
    const card = new context.Card();
    card.setConfig({entity: 'sensor.test', force_expanded: true, display_settings: {layout}});
    card.hass = {language, config: {time_zone: 'Europe/Berlin', unit_system: {temperature: '°C'}},
      states: {'sensor.test': {state: 'can_close', attributes: {
        status: 'green', display_mode: 'room_air', room_name: 'Wohnung',
        recommendation_key: 'can_close', recommendation: 'Du kannst schließen',
        temperature_inside: 22.7, humidity_inside: 59,
        temperature_outside: 13, humidity_outside: 77,
        forecast_data_status: status, forecast_using_cached_data: cached,
      }}}};
    const html = card.shadowRoot.innerHTML;
    if (cached) {
      assert.ok(html.includes(wording[language][0]), `${language}/${layout}: retained forecast explained`);
      assert.ok(!html.includes(wording[language][2]), 'usable cached forecast must not claim it is unused');
    } else if (status === 'stale') {
      assert.ok(html.includes(wording[language][2]), 'unusable manual cache retains its existing warning');
    } else if (status === 'unavailable') {
      assert.ok(html.includes(wording[language][1]));
    } else {
      assert.ok(!html.includes(wording[language][0]) && !html.includes(wording[language][1]));
    }
    scenarios++;
  }
}
console.log(`PASS: ${scenarios} forecast-warning cases across DE/EN/TR and classic/split cards`);
