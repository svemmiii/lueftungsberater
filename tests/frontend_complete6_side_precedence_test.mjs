import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js', 'utf8');
class Stub {
  attachShadow() { this.shadowRoot = {innerHTML:'',querySelector(){return null},querySelectorAll(){return []}}; return this.shadowRoot; }
  dispatchEvent() { return true; }
}
const ctx = {console, HTMLElement:Stub, customElements:{get(){},define(){}},
  window:{customCards:[],confirm(){return false},localStorage:{getItem(){return null},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},
  navigator:{language:'de-DE'}, document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
  setTimeout,clearTimeout,CustomEvent:class{},Event:class{constructor(){this.detail={}}}};
vm.createContext(ctx);
vm.runInContext(`${source}\nglobalThis.CardClass=LueftungsberaterCard`,ctx);

// All fixture fields are configured, so this test can check visibility,
// duplicates and the precedence of all three independent order settings.
const all = {
  general:['last_airing','target','humidity_delta','window_state'],
  inside:['temp_in','humidity_in','absolute_in','co2_in','pm25_in','pm10_in','voc_in','no2_in','formaldehyde_in','surface_temp','surface_humidity','mold_risk'],
  outside:['temp_out','humidity_out','absolute_out','co2_out','pm25_out','pm10_out','voc_out','no2_out','o3_out','wind','gust','rain'],
};
const optional = new Set(['surface_temp','surface_humidity','mold_risk','co2_out','wind','gust','rain']);
const attrs = {
  status:'green', room_name:'Prüfraum', recommendation:'Okay',
  temperature_inside:22, temperature_outside:14, humidity_inside:57, humidity_outside:73,
  absolute_humidity_inside:9.1, absolute_humidity_outside:6.7, absolute_humidity_difference:2.4,
  target_temperature:21, has_window_contacts:true, last_confirmed_airing:'2026-10-09T09:00:00+02:00',
  has_co2:true,co2_ppm:850,co2_data_status:'current',outdoor_co2_ppm:420,
  surface_temperature:19,surface_relative_humidity:65,mold_risk:false,mold_persistent:false,
  wind_speed_kmh:14,wind_gust_kmh:25,rain_minutes_until:80,
  indoor_air_quality_values:{pm2_5:5,pm10:9,voc_index:88,no2_index:12,formaldehyde:0.03},
  air_quality_values:{pm2_5:7,pm10:13,voc_index:42,no2_index:11,o3:27},
  source_surface_temperature:'sensor.surface',
};
const hass={language:'de',config:{unit_system:{temperature:'°C'},time_zone:'Europe/Berlin'},states:{}};
const card=new ctx.CardClass(); card._hass=hass;
const labels=Object.fromEntries(Object.values(all).flat().map(id=>[id,`QQ_${id}_QQ`]));
const idsInText = html => [...html.matchAll(/QQ_([a-z0-9_]+)_QQ:/g)].map(x=>x[1]);
const expectedIds = (section,settings) => {
  const order = settings.order?.[section] || [];
  return all[section]
    .filter(id=>!(settings.hidden||[]).includes(id) && (!optional.has(id)||(settings.extra||[]).includes(id)))
    .sort((a,b) => {const ai=order.indexOf(a),bi=order.indexOf(b);return (ai<0?999:ai)-(bi<0?999:bi);});
};
function check(settings, label) {
  const config={layout:'classic',labels, ...settings};
  const result=card._classicFacts(attrs,'°C',config);
  assert.match(result,/lb-classic/,`${label}: must remain classic`);
  const actual=idsInText(result);
  const known=new Set(Object.values(all).flat());
  const expected=Object.keys(all).flatMap(side=>expectedIds(side,config));
  assert.equal(new Set(actual).size,actual.length,`${label}: no duplicates`);
  assert.deepEqual([...actual].filter(id=>known.has(id)).sort(),[...expected].sort(),`${label}: exactly the requested fields appear`);
  const sections=(config.sides?.join(',')==='outside,inside')?['outside','inside']:['inside','outside'];
  const sideCustomization=sections[0]==='outside' || sections.some(side=>(config.order?.[side]||[]).length>0);
  if (sideCustomization) {
    const sides=new Set([...all.inside,...all.outside]);
    assert.deepEqual(actual.filter(id=>sides.has(id)),sections.flatMap(side=>expectedIds(side,config)),`${label}: side precedence and each side order`);
  }
  if ((config.order?.general||[]).length) {
    const g=new Set(all.general);
    assert.deepEqual(actual.filter(id=>g.has(id)),expectedIds('general',config),`${label}: independent general order`);
  }
}

// The three cases reported by the reviewer must remain fixed.
check({sides:['outside','inside']},'outside first, no metric reorder');
check({sides:['outside','inside'],order:{inside:['co2_in','humidity_in','temp_in']}},'outside first, inside-only metric reorder');
check({sides:['inside','outside'],order:{outside:['humidity_out','temp_out']}},'inside first, outside-only metric reorder');
check({sides:['outside','inside'],order:{outside:['humidity_out','temp_out']}},'outside first with outside-only reorder');
check({sides:['outside','inside'],order:{inside:['humidity_in','temp_in'],outside:['pm25_out','humidity_out','temp_out'],general:['humidity_delta','target','last_airing']}},'all three orders combined');

// The real card rendering path must choose the customized layout when
// only the side order was changed (no per-metric order at all).
hass.states['sensor.test']={state:'green',attributes:{...attrs,night_ventilation_status:'unavailable'}};
const liveCard=new ctx.CardClass();
liveCard.setConfig({entity:'sensor.test',force_expanded:true,display_settings:{layout:'classic',sides:['outside','inside'],labels}});
liveCard.hass=hass;
const liveHtml=liveCard.shadowRoot.innerHTML;
assert.ok(liveHtml.includes('class="lb-classic'),'swapped sections must render with classic layout');
assert.ok(liveHtml.indexOf('QQ_temp_out_QQ:') < liveHtml.indexOf('QQ_temp_in_QQ:'),'real card must render outside first');

// No reorder means the old consolidated classic rows are retained.
const legacy=card._classicFacts(attrs,'°C',{layout:'classic',labels});
assert.ok(legacy.includes('Temperatur:') && legacy.includes('Luftfeuchte:'),'legacy temperature/humidity groups preserved');
assert.ok(legacy.indexOf('Temperatur:') < legacy.indexOf('Luftfeuchte:'),'legacy group order preserved');

// Deterministic 3,000-case stress test: hidden fields, optional fields,
// partial and full order arrays, both side arrangements, general reorders.
let state=0x11132026;
const rnd=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)/4294967296;};
const shuffled = list => {const x=[...list];for(let i=x.length-1;i>0;i--){const j=Math.floor(rnd()*(i+1));[x[i],x[j]]=[x[j],x[i]];}return x;};
for(let i=0;i<3000;i++) {
  const s={sides:rnd()<.5?['inside','outside']:['outside','inside'],order:{},hidden:[],extra:[],labels};
  for(const section of ['inside','outside','general']){
    if(rnd()<.8) s.order[section]=shuffled(all[section]).filter(()=>rnd()<.65);
  }
  s.hidden=Object.values(all).flat().filter(()=>rnd()<.25);
  s.extra=[...optional].filter(()=>rnd()<.5);
  check(s,`stress #${i+1}`);
}
console.log('PASS: COMPLETE(6) three reported regressions, backwards compatibility and 3000 ordering/visibility stress cases');
