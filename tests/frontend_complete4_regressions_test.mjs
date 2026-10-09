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
  has_co2:true, co2_ppm:null, co2_data_status:'unavailable',source_co2:'sensor.co2',
  temperature_inside:21,temperature_outside:16,source_temperature_inside:'sensor.temp_in',source_temperature_outside:'sensor.temp_out',
  humidity_inside:48,humidity_outside:72,source_humidity_inside:'sensor.humidity_in',source_humidity_outside:'sensor.humidity_out'};
const hass={language:'de',config:{unit_system:{temperature:'°C'},time_zone:'Europe/Berlin'},states:{'sensor.test':{state:'green',attributes:base}}};
function render(attrs,settings){
  hass.states['sensor.test']={state:'green',attributes:attrs};
  const card=new Card();card.setConfig({entity:'sensor.test',force_expanded:true,...(settings?{display_settings:settings}:{})});card.hass=hass;
  return card.shadowRoot.innerHTML;
}
function count(text,word){return text.split(word).length-1;}
for(const layout of ['classic','split']){
  let html=render(base,{layout,hidden:['co2_in']});
  assert.match(html,/CO₂-Sensor nicht verfügbar/,'hidden value must not suppress outage warning');
  assert.match(html,/class="fact data-warning"/,'outage has warning styling');
  assert.equal(count(html,'CO₂-Sensor nicht verfügbar'),1,'avoid duplicate error');
  html=render(base,{layout});
  assert.equal(count(html,'CO₂-Sensor nicht verfügbar'),1,'visible value includes outage warning once');
  const grace={...base,co2_ppm:750,co2_data_status:'grace'};
  html=render(grace,{layout,hidden:['co2_in']});
  assert.equal(count(html,'Sensor kurz nicht verfügbar'),1,'hidden CO2 still shows grace warning');
  assert.doesNotMatch(html,/750 ppm/,'hidden CO2 must not leak the value through warning');
  html=render(grace,{layout});
  assert.equal(count(html,'Sensor kurz nicht verfügbar'),1,'grace warning is not duplicated');
  html=render({...base,co2_ppm:680,co2_data_status:'current'}, {layout,hidden:['co2_in']});
  assert.doesNotMatch(html,/CO₂-Sensor nicht verfügbar|Sensor kurz nicht verfügbar/,'healthy hidden CO2 stays hidden');
}
const order={inside:['co2_in','humidity_in','temp_in'],outside:['humidity_out','temp_out']};
const sorted=render({...base,co2_ppm:630,co2_data_status:'current'}, {layout:'classic',order});
assert.match(sorted,/lb-classic/);
const end=sorted.indexOf('class="lb-classic');
const facts=sorted.slice(end, sorted.indexOf('</div></div>',end));
assert.ok(facts.indexOf('CO₂:') < facts.indexOf('Luftfeuchte:') && facts.indexOf('Luftfeuchte:') < facts.indexOf('Temperatur:'), 'classic rows follow saved drag order');
const legacy=render({...base,co2_ppm:630,co2_data_status:'current'});
assert.ok(legacy.indexOf('Temperatur:') < legacy.indexOf('Luftfeuchte:') && legacy.indexOf('Luftfeuchte:') < legacy.indexOf('CO₂:'),'existing default order unchanged');
const classicDefault=render({...base,co2_ppm:630,co2_data_status:'current'},{layout:'classic',hidden:['humidity_out']});
assert.ok(classicDefault.indexOf('Temperatur:') < classicDefault.indexOf('CO₂:'),'visibility-only changes preserve legacy grouping');
for(const density of ['compact','normal','detailed']){
  const html=render({...base,co2_ppm:630,co2_data_status:'current'}, {layout:'classic',density});
  if(density!=='normal') assert.match(html,new RegExp(`class="lb-classic lb-${density}"`));
  if(density!=='normal') assert.match(html,new RegExp(`\\.lb-classic\\.lb-${density}`), 'density has matching CSS');
}
console.log('PASS: COMPLETE(4) frontend CO2 warnings, order, density, compatibility (25 checks)');
