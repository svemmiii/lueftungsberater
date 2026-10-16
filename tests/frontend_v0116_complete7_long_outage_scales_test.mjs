import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class Stub{attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}};return this.shadowRoot;}}
const ctx={console,HTMLElement:Stub,customElements:{get(){},define(){}},
 window:{customCards:[],location:{pathname:'/'},localStorage:{getItem(){return null},setItem(){}},addEventListener(){},removeEventListener(){}},
 navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {textContent:''}},head:{appendChild(){}}},
 setTimeout(){return 1},clearTimeout(){},setInterval(){return 1},clearInterval(){},CustomEvent:class{}};
vm.createContext(ctx);vm.runInContext(`${source}\nglobalThis.CardClass=LueftungsberaterHistoryCard;`,ctx);
const Card=ctx.CardClass;
const H=3600000,now=1000*H,from24=now-24*H,id='sensor.test_co2';
const point=(t,state,unit='ppm')=>({entity_id:id,state:String(state),last_updated:new Date(t).toISOString(),attributes:{unit_of_measurement:unit}});
const raw=[point(now-26*H,650),point(now-25*H,'unavailable'),point(now-23*H,'unavailable')];
function makeCard(records=raw){
 const c=new Card();c._config={entity:'sensor.room',hours:24,metrics:['co2_in'],colors:{}};
 c._metrics=[{key:'co2_in',unit:'ppm',high:1200,low:null}];
 let calls=0;
 c._hass={language:'de',states:{'sensor.room':{state:'open_now',attributes:{room_name:'Wohnzimmer',display_mode:'room_air'}}},
  async callApi(method,url){
    calls++;
    const start=Date.parse(decodeURIComponent(url.split('/period/')[1].split('?')[0]));
    const until=Date.parse(decodeURIComponent(new URLSearchParams(url.split('?')[1]).get('end_time')));
    const ordered=records.filter(r=>Date.parse(r.last_updated)<=until);
    const prior=ordered.filter(r=>Date.parse(r.last_updated)<start).at(-1);
    const visible=ordered.filter(r=>Date.parse(r.last_updated)>=start);
    return prior||visible.length?[[...prior?[prior]:[],...visible]]:[];
  }};
 c.getBoundingClientRect=()=>({width:390});
 return {c,get calls(){return calls;}};
}
const {c,getCalls}=(()=>{const m=makeCard();return {c:m.c,getCalls:()=>m.calls};})();
const recovered=await c._getHistory([id],new Date(from24),new Date(now),new Set([id]));
assert.equal(recovered.length,1);
assert.ok(recovered[0].some(row=>row.state==='650'),'bounded Recorder cold-start backfill restores the actual earlier number');
const parsed=c._parseHistorySamples(recovered[0],from24,now,c._metrics[0],true);
assert.ok(parsed.outageContext,'pre-window outage has its own separate last-good context');
assert.equal(parsed.outageContext.value,650);
assert.equal(parsed.outageContext.start,now-25*H);
assert.equal(parsed.some(p=>Number.isFinite(p.v)),false,'no old numeric state is inserted as a valid sample');
let runs=c._outageRuns(parsed,from24,now);
assert.equal(runs.length,1);assert.equal(runs[0].value,650);
assert.equal(runs[0].start,now-25*H);
c._series=new Map([['co2_in',parsed]]);
assert.equal(c._updateGrowingWindow(from24,now),from24,'an ongoing known outage preserves the configured rolling window');
c._cursor=now;c._render();
assert.match(c.shadowRoot.innerHTML,/data-history-outage="co2_in"/);
assert.match(c.shadowRoot.innerHTML,/data-axis-marker="co2_in"[^>]*visibility="hidden"/);
assert.doesNotMatch(c.shadowRoot.innerHTML,/>Noch kein Verlauf für diese Auswahl</);
assert.match(c.shadowRoot.innerHTML,/class="reading"[\s\S]*?—/,'cursor shows missing rather than last-good value');
const totalRequests=c._historyCache.get(id).outageSeed;
assert.ok(totalRequests);
// Moving to 6h and back to 24h reuses cached recovered context.
for(const hours of [6,24]){
  const start=now-hours*H;
  const rows=(await c._getHistory([id],new Date(start),new Date(now),new Set([id])))[0];
  const p=c._parseHistorySamples(rows,start,now,c._metrics[0],true);
  assert.equal(p.outageContext?.value,650);
  c._series=new Map([['co2_in',p]]);
  assert.equal(c._updateGrowingWindow(start,now),start);
  assert.equal(c._outageRuns(p,start,now).length,1);
}
// Recovery must terminate the orange hold exactly at its own measured time.
const resumed=[...raw,point(now-H,800)];
const d=makeCard(resumed).c;
const loaded=(await d._getHistory([id],new Date(from24),new Date(now),new Set([id])))[0];
const rp=d._parseHistorySamples(loaded,from24,now,d._metrics[0],true);
const ended=d._outageRuns(rp,from24,now);
assert.equal(ended.length,1);assert.equal(ended[0].end,now-H);
assert.equal(d._atOrBefore(rp,now-2*H).v,null);
assert.equal(d._atOrBefore(rp,now).v,800);
// The same rendering works even when the older recorded good value is no
// longer retained. Never invent one if Recorder has purged it.
const lost=makeCard(raw.slice(1)).c;
const lostRows=(await lost._getHistory([id],new Date(from24),new Date(now),new Set([id])))[0];
const lostParsed=lost._parseHistorySamples(lostRows,from24,now,lost._metrics[0],true);
assert.equal(lostParsed.outageContext,undefined);
assert.equal(lost._outageRuns(lostParsed,from24,now).length,0);
// Axes and threshold instruments are intentionally two independent concepts.
function renderAxes(metrics){
  const card=makeCard().c;card._config.metrics=metrics.map(m=>m.key);card._metrics=metrics;
  card._series=new Map(metrics.map((m,i)=>[m.key,[{t:from24,v:m.key==='target_temp'?23:20+i}]]));
  card._start=from24;card._end=now;card._cursor=now;card._render();return card.shadowRoot.innerHTML;
}
const outerOnly=renderAxes([{key:'co2_out',unit:'ppm',low:null,high:null},
  {key:'temp_out',unit:'°C',low:null,high:null},{key:'humidity_out',unit:'%',low:null,high:null}]);
assert.equal((outerOnly.match(/data-inline-axis=/g)||[]).length,3,'three physically distinct numeric axes are shown');
assert.ok(outerOnly.includes('ppm')&&outerOnly.includes('°C')&&outerOnly.includes('%'));
assert.doesNotMatch(outerOnly,/data-instrument-lane=|data-axis-marker=|data-axis-zone=/,'no invented outside limit instrument');
const onlyTarget=renderAxes([{key:'target_temp',unit:'°C',low:null,high:null}]);
assert.equal((onlyTarget.match(/data-inline-axis=/g)||[]).length,1,'target-only curve receives a numeric axis');
assert.doesNotMatch(onlyTarget,/data-instrument-lane=|data-axis-zone=/);
// A second, newer outage must replace a previously cached older stale seed
// when its final good value has passed the 30-day trimming boundary.
const rotating=makeCard([point(now-32*24*H,800),point(now-31*24*H,'unavailable')]).c;
rotating._historyCacheScope='sensor.room';
rotating._historyCache.set(id,{
  from:now-40*24*H,to:now-36*24*H,
  rows:[point(now-32*24*H,800),point(now-31*24*H,'unavailable')],
  outageSeed:{good:point(now-80*24*H,650),outage:point(now-79*24*H,'unavailable')},
  outageProbeBefore:null
});
const rotated=(await rotating._getHistory([id],new Date(from24),new Date(now),new Set([id])))[0];
const rotatedParsed=rotating._parseHistorySamples(rotated,from24,now,rotating._metrics[0],true);
assert.equal(rotatedParsed.outageContext?.value,800,'cache trimming replaces obsolete earlier 650 ppm hold with the last genuine 800 ppm');

console.log('PASS COMPLETE7: older long outage retained without invented values; cached lookback, recovery, outdoor-only and target-only axes');
