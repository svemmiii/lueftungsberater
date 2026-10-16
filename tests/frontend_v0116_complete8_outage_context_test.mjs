import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class Stub {attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}};return this.shadowRoot;}}
const ctx={console,HTMLElement:Stub,customElements:{get(){},define(){}},
 window:{customCards:[],location:{pathname:'/'},localStorage:{getItem(){return null},setItem(){}},addEventListener(){},removeEventListener(){}},
 navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {textContent:''}},head:{appendChild(){}}},
 setTimeout(){return 1},clearTimeout(){},setInterval(){return 1},clearInterval(){},CustomEvent:class{}};
vm.createContext(ctx);vm.runInContext(`${source}\nglobalThis.CardClass=LueftungsberaterHistoryCard;`,ctx);
const H=3600000, T=1000*H, id='sensor.test', room='sensor.room';
const row=(t,state,unit='ppm')=>({entity_id:id,state:String(state),last_updated:new Date(t).toISOString(),attributes:{unit_of_measurement:unit}});
function buildCard(data,metric={key:'co2_in',unit:'ppm',source:id}){
  const card=new ctx.CardClass();
  card._config={entity:room,hours:24,metrics:[metric.key],colors:{}};
  card._metrics=[metric];
  let requests=0;
  card._hass={language:'de',states:{[room]:{state:'open_now',attributes:{display_mode:'room_air'}}},
    async callApi(_verb,url){
      requests++;
      const parts=url.split('?');
      const since=Date.parse(decodeURIComponent(parts[0].split('/period/')[1]));
      const to=Date.parse(new URLSearchParams(parts[1]).get('end_time'));
      const available=data.rows.filter(p=>Date.parse(p.last_updated)<=to).sort((a,b)=>Date.parse(a.last_updated)-Date.parse(b.last_updated));
      const preceding=available.filter(p=>Date.parse(p.last_updated)<since).at(-1);
      const visible=available.filter(p=>Date.parse(p.last_updated)>=since);
      return preceding||visible.length ? [[...preceding?[preceding]:[],...visible]] : [];
    }};
  return {card,get requests(){return requests;}};
}
async function load(card,start,end){
  const metric=card._metrics[0];
  const rows=(await card._getHistory([id],new Date(start),new Date(end),new Set([id]),new Map([[id,metric]])))[0];
  return card._parseHistorySamples(rows,start,end,metric,true);
}
// Exactly the review's regression: a second, later outage must supersede the
// previous cached 650 ppm seed without waiting for 30-day cache rollover.
const timeline={rows:[row(T-26*H,650),row(T-25*H,'unavailable'),row(T-23*H,'unavailable'),row(T-H,800)]};
const {card:history}=buildCard(timeline);
let first=await load(history,T-24*H,T);
assert.equal(history._outageRuns(first,T-24*H,T).at(-1)?.end,T-H,'initial outage ends at actual recovery');
// The next failure occurs after the first query, while 800 ppm remains in
// Recorder cache at the time of the second (later) 24h query.
timeline.rows.push(row(T+H,'unavailable'));
const later=T+26*H, from=later-24*H;
const active=await load(history,from,later);
assert.equal(active.outageContext?.value,800,'latest recovered ppm value anchors the second outage');
assert.equal(active.outageContext?.start,T+H);
let holds=history._outageRuns(active,from,later);
assert.equal(holds.length,1);assert.equal(holds[0].value,800);
assert.equal(history._atOrBefore(active,later)?.v,null,'an orange overlay never becomes a live cursor reading');
for(const h of [6,24]){
  const from=later-h*H;
  const data=await load(history,from,later);
  assert.equal(data.outageContext?.value,800,`after ${h}h switch must keep the newer context`);
  assert.equal(history._outageRuns(data,from,later)[0]?.value,800);
}
// Older time ranges must still use their OWN older context, not the recently
// cached future outage or its value.
const historical=await load(history,T-24*H,T-2*H);
assert.equal(historical.outageContext?.value,650,'older viewport retains older outage context');
// The cold-start lookback must treat a numeric state carrying a physically
// INCOMPATIBLE unit as an outage, not a successful measurement.
const incompatible={rows:[row(T-26*H,650),row(T-25*H,900,'mg/m³'),row(T-23*H,975,'mg/m³')]};
const {card:units}=buildCard(incompatible);
const unitSeries=await load(units,T-24*H,T);
assert.equal(unitSeries.outageContext?.value,650);
assert.equal(unitSeries.outageContext?.start,T-25*H);
assert.equal(units._outageRuns(unitSeries,T-24*H,T)[0]?.value,650);
assert.equal(units._atOrBefore(unitSeries,T)?.v,null);
assert.equal(unitSeries.some(p=>Number.isFinite(p.v)),false,'incompatible numbers stay invalid');
// A unit change after a valid reading is also an interruption within the window;
// a later valid recovery must end the stale hold, not leak a fake value.
const dynamic={rows:[row(T-20*H,650),row(T-10*H,0.9,'mg/m³'),row(T-5*H,800),row(T-2*H,3,'mg/m³')]};
const {card:swapped}=buildCard(dynamic);
const mixed=await load(swapped,T-24*H,T);
const runs=swapped._outageRuns(mixed,T-24*H,T);
assert.equal(runs.length,2);assert.equal(runs[0].value,650);assert.equal(runs[0].end,T-5*H);
assert.equal(runs[1].value,800);assert.equal(swapped._atOrBefore(mixed,T)?.v,null);
// Convertible temperature values must NOT trigger an orange outage. Fahrenheit
// is correctly normalized into the selected Celsius scale.
const fahrenheit={rows:[row(T-3*H,68,'°F'),row(T-2*H,21,'°C'),row(T-H,69.8,'°F')]};
const {card:temp}=buildCard(fahrenheit,{key:'temp_in',unit:'°C',source:id});
const temperature=await load(temp,T-6*H,T);
assert.equal(temperature.length,3);
assert.equal(temp._outageRuns(temperature,T-6*H,T).length,0);
assert.ok(Math.abs(temperature[0].v-20)<1e-8);
assert.ok(Math.abs(temperature[2].v-21)<1e-8);
console.log('PASS COMPLETE8: newest seed, historical window, incompatible units, valid conversion and cursor safety');
