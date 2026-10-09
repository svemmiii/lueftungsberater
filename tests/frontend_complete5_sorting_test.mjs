import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class Stub {
  attachShadow(){ this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}}; return this.shadowRoot; }
  dispatchEvent(){return true;}
}
const ctx={console,HTMLElement:Stub,customElements:{get(){},define(){}},
  window:{customCards:[],confirm(){return false},localStorage:{getItem(){return null},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},
  navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
  setTimeout,clearTimeout,CustomEvent:class{},Event:class {constructor(){this.detail={}}}};
vm.createContext(ctx);
vm.runInContext(`${source}\nglobalThis.CardClass=LueftungsberaterCard`,ctx);
const Card=ctx.CardClass;
const base={status:'green',room_name:'Testzimmer',recommendation:'Alles gut',reason:'Luft ist gut',night_ventilation_status:'unavailable',
  has_co2:true,co2_ppm:635,co2_data_status:'current',source_co2:'sensor.co2',
  temperature_inside:21,temperature_outside:16,source_temperature_inside:'sensor.temp_in',source_temperature_outside:'sensor.temp_out',
  humidity_inside:48,humidity_outside:72,source_humidity_inside:'sensor.humidity_in',source_humidity_outside:'sensor.humidity_out',
  target_temperature:22,absolute_humidity_difference:1.4,
  source_target_temperature:'climate.test',source_absolute_humidity_difference:'sensor.diff',
  has_window_contacts:true,last_confirmed_airing:'2026-10-09T10:00:00+02:00',
  surface_temperature:19,surface_relative_humidity:64,source_surface_temperature:'sensor.surface',
  mold_risk:false};
const hass={language:'de',config:{unit_system:{temperature:'°C'},time_zone:'Europe/Berlin'},states:{'sensor.test':{state:'green',attributes:base}}};
function html(settings, attrs=base){
  hass.states['sensor.test']={state:'green',attributes:attrs};
  const card=new Card();card.setConfig({entity:'sensor.test',force_expanded:true,...(settings?{display_settings:settings}:{})});card.hass=hass;
  return card.shadowRoot.innerHTML;
}
function facts(settings,attrs=base){
  const full=html(settings,attrs), index=full.indexOf('class="lb-classic');
  assert.ok(index > -1,'expected classic layout');
  return full.slice(index,full.indexOf('</div></div>',index));
}
function inOrder(content, tokens, what){
  const offsets=tokens.map(token=>content.indexOf(token));
  assert.ok(offsets.every(n=>n>=0),`${what}: missing item in ${JSON.stringify(offsets)}: ${tokens.join(', ')}`);
  assert.ok(offsets.every((n,i)=>i===0||n>offsets[i-1]),`${what}: incorrect order of ${tokens.join(', ')}`);
}

// Within OUTSIDE, an explicit sort wins; section priority remains inside then outside by default.
let result=facts({layout:'classic',order:{outside:['humidity_out','temp_out']}});
inOrder(result,['Außen Relative Feuchte:','Außen Temperatur:'],'outside reorder');
assert.ok(result.indexOf('Innen Temperatur:') < result.indexOf('Außen Relative Feuchte:'),'default inside-first section order must not be overridden by an outside-only sort');

// Inside-only drag has the same priority, and changes family order as requested.
result=facts({layout:'classic',order:{inside:['co2_in','humidity_in','temp_in']}});
inOrder(result,['Innen CO₂:','Innen Relative Feuchte:','Innen Temperatur:'],'inside reorder');

// Both sides have opposing orders: each side must keep its own sequence.
result=facts({layout:'classic',order:{inside:['temp_in','humidity_in','co2_in'],outside:['humidity_out','temp_out']}});
inOrder(result,['Innen Temperatur:','Innen Relative Feuchte:','Innen CO₂:'],'inside conflict');
inOrder(result,['Außen Relative Feuchte:','Außen Temperatur:'],'outside conflict');

// The GENERAL order includes target and delta instead of forcibly moving them
// back to the temperature/humidity families.
result=facts({layout:'classic',order:{general:['humidity_delta','target','last_airing','window_state']}});
inOrder(result,['Feuchtedifferenz:','Solltemperatur:','Zuletzt gelüftet:'],'general reorder');
assert.equal(result.split('Feuchtedifferenz:').length-1,1,'delta must appear only once');
assert.equal(result.split('Solltemperatur:').length-1,1,'target must appear only once');
assert.match(result,/Temperatur:.*Innen Temperatur:.*Außen Temperatur:/,'side families stay grouped for general-only order');

// Both general and side orders may be set, but each remains respected.
result=facts({layout:'classic',order:{general:['humidity_delta','target','last_airing'],outside:['humidity_out','temp_out']}});
inOrder(result,['Feuchtedifferenz:','Solltemperatur:','Zuletzt gelüftet:'],'combined general');
inOrder(result,['Außen Relative Feuchte:','Außen Temperatur:'],'combined outside');
assert.equal(result.split('Feuchtedifferenz:').length-1,1);

// Unsorted cards still preserve the original consolidated rows and group order.
result=facts({layout:'classic',hidden:['humidity_out']});
inOrder(result,['Temperatur:','Luftfeuchte:','CO₂:'],'legacy classic group order');
assert.ok(result.includes('Temperatur: Solltemperatur:') && result.includes('Innen Temperatur:') && result.includes('Außen Temperatur:'),'legacy temperature row still combined');
assert.ok(result.includes('Luftfeuchte: Feuchtedifferenz:') && result.includes('Innen Relative Feuchte:'),'legacy humidity row still combined');

// Unrelated optional measurements remain standalone instead of being merged.
result=facts({layout:'classic',extra:['surface_temp','surface_humidity','mold_risk'],order:{inside:['surface_temp','surface_humidity','mold_risk','temp_in']}});
assert.ok(result.split('class="fact"').length-1 >= 4,'optional fields retain separate rows');
assert.ok(result.indexOf('Oberflächentemperatur') < result.indexOf('Oberflächenfeuchte'),'optional order followed');

// No regression: outage notice still visible independently of the CO2 field.
result=html({layout:'classic',hidden:['co2_in'],order:{outside:['humidity_out','temp_out']}},{...base,co2_ppm:null,co2_data_status:'unavailable'});
assert.match(result,/CO₂-Sensor nicht verfügbar/,'CO2 outage must be visible');
assert.equal(result.split('CO₂-Sensor nicht verfügbar').length-1,1,'no duplicated CO2 notices');
console.log('PASS: COMPLETE(5) classic order regression scenarios (outside, inside, conflicting, general, legacy, optional, CO₂)');
