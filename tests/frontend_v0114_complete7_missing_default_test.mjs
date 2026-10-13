import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class Stub {
  attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}};return this.shadowRoot;}
  dispatchEvent(){return true;}
}
const ctx={console,HTMLElement:Stub,customElements:{get(){},define(){}},
  window:{customCards:[],confirm(){return false},localStorage:{getItem(){return null},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},
  navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
  setTimeout,clearTimeout,CustomEvent:class{},Event:class{constructor(){this.detail={}}}};
vm.createContext(ctx);
vm.runInContext(`${source}\nglobalThis.CardClass=LueftungsberaterCard`,ctx);
const attrs={status:'green',room_name:'Wohnung',recommendation:'Alles gut',reason:'Gut',has_co2:false,
  temperature_inside:null,temperature_outside:11.5, humidity_inside:'unavailable',humidity_outside:69,
  source_temperature_inside:'sensor.indoor_temp',source_temperature_outside:'sensor.outdoor_temp',
  source_humidity_inside:'sensor.indoor_humidity',source_humidity_outside:'sensor.outdoor_humidity',
  source_pm25_inside:'sensor.pm25_indoor', air_quality_values:{pm2_5:5.2}, indoor_air_quality_values:{},
  source_pm25_outside:'cams_air_quality_model',night_ventilation_status:'unavailable'};
const hass={language:'de',config:{time_zone:'Europe/Berlin',unit_system:{temperature:'°C'}},states:{'sensor.room':{state:'green',attributes:attrs}, 'sensor.indoor_temp':{state:'unavailable',attributes:{}}, 'sensor.indoor_humidity':{state:'unavailable',attributes:{}}}};
function html(config={}){const card=new ctx.CardClass();card.setConfig({entity:'sensor.room',force_expanded:true,...config});card.hass=hass;return card.shadowRoot.innerHTML;}
const standard=html();
assert.match(standard, /Temperatur:.*?class="lb-missing".*?Nicht verfügbar innen.*?11[.,]5\s*°C außen/s);
assert.match(standard, /Luftfeuchte:.*?class="lb-missing".*?Nicht verfügbar innen.*?69[.,]0\s*% außen/s);
assert.match(standard, /PM2[,.]5:.*?lb-missing.*?Nicht verfügbar innen/s);
assert.match(standard, /text-decoration-style: dotted/);
assert.match(standard, /sensor\.indoor_temp/);
assert.match(standard, /sensor\.indoor_humidity/);
// A missing attribute without an explicitly configured source is NOT missing sensor.
const without={...attrs, source_temperature_inside:null,source_humidity_inside:null,source_pm25_inside:null};
hass.states['sensor.room']={state:'green',attributes:without};
const bare=html();
assert.doesNotMatch(bare, /Nicht verfügbar innen/);
assert.match(bare, /11[.,]5\s*°C außen/);
assert.match(bare, /69[.,]0\s*% außen/);
// Both alternative layouts keep the prior missing-value treatment.
hass.states['sensor.room']={state:'green',attributes:attrs};
assert.match(html({display_settings:{layout:'classic',hidden:['humidity_out']}}),/lb-missing/);
assert.match(html({display_settings:{layout:'split'}}),/lb-missing/);
console.log('PASS: default, classic, split unavailable sensors + unconfigured exclusions');
