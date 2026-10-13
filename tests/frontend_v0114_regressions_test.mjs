import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class HTMLElementStub {
  attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}}; return this.shadowRoot;}
  dispatchEvent(){return true;}
}
const ctx={console,HTMLElement:HTMLElementStub,customElements:{get(){},define(){}},
window:{customCards:[],confirm(){return false},localStorage:{getItem(){return null},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},
navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
setTimeout,clearTimeout,CustomEvent:class{},Event:class {constructor(){this.detail={}}}};
vm.createContext(ctx);
vm.runInContext(`${source}\nglobalThis.CardClass=LueftungsberaterCard`,ctx);
const attrs={status:'green',room_name:'Wohnung',recommendation:'Alles gut',reason:'Gut',night_ventilation_status:'unavailable',
  has_window_contacts:true,window_open:true,open_minutes:60*48+9,window_data_status:'current',
  last_confirmed_airing:'2026-10-08T08:00:00+02:00',source_airing:'sensor.airing',source_last_airing:'sensor.airing_last',
  temperature_inside:20,temperature_outside:null,source_temperature_outside:'sensor.outside',
  has_co2:true,co2_ppm:null,source_co2:'sensor.co2',co2_data_status:'unavailable'};
const hass={language:'de',config:{unit_system:{temperature:'°C'},time_zone:'Europe/Berlin'},states:{'sensor.room':{state:'green',attributes:attrs}}};
for(const layout of ['classic','split']) {
  const card=new ctx.CardClass();card.setConfig({entity:'sensor.room',force_expanded:true,display_settings:{layout,hidden:[]}});card.hass=hass;
  const html=card.shadowRoot.innerHTML;
  assert.match(html,/48 Stunden/,'an ongoing 48-hour airing must not disappear');
  assert.match(html,/Fenster\/Tür gerade offen|Fenster offen|Fenster\/Tür offen/);
  assert.match(html,/lb-missing/,'unavailable sensors are highlighted');
  assert.match(html,/text-decoration-style: dotted/,'missing sensor marking has dotted underline');
  assert.doesNotMatch(html,/Gestern zuletzt gelüftet/,'current airing must not be replaced by historical text');
}
const manual = new ctx.CardClass();manual.setConfig({entity:'sensor.room',force_expanded:true});
manual.hass=hass;
assert.match(manual.shadowRoot.innerHTML,/data-warning/,'legacy card keeps CO2 outage indication');
let info={...attrs,has_co2:false,co2_ppm:null,warning_notice_kind:'info',warning_notice_text:'Trinkwasserhinweis'};
hass.states['sensor.room']={state:'green',attributes:info};
const notice = new ctx.CardClass();notice.setConfig({entity:'sensor.room',force_expanded:true});notice.hass=hass;
assert.match(notice.shadowRoot.innerHTML,/Amtlicher Hinweis: Trinkwasserhinweis/);
assert.doesNotMatch(notice.shadowRoot.innerHTML,/Entwarnung eingegangen: Trinkwasserhinweis/);
console.log('PASS: 0.11.4 ongoing airing, missing readings, and optional general notices');
