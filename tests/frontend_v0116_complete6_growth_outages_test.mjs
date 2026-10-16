import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class Stub {
  attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}};return this.shadowRoot;}
}
const ctx={console,HTMLElement:Stub,customElements:{get(){},define(){}},
  window:{customCards:[],location:{pathname:'/'},localStorage:{getItem(){return null},setItem(){}},addEventListener(){},removeEventListener(){}},
  navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {textContent:''}},head:{appendChild(){}}},
  setTimeout(){return 1},clearTimeout(){},setInterval(){return 1},clearInterval(){},CustomEvent:class{}};
vm.createContext(ctx);vm.runInContext(`${source}\nglobalThis.CardClass=LueftungsberaterHistoryCard;`,ctx);
const Card=ctx.CardClass;
function card(){
  const c=new Card();c._config={entity:'sensor.room',hours:24,metrics:['temp_in','co2_in','co2_out'],colors:{}};
  c._metrics=[{key:'temp_in',unit:'°C',low:18,high:25},{key:'co2_in',unit:'ppm',low:null,high:1000},
    {key:'co2_out',unit:'ppm',low:null,high:null}];
  c._hass={language:'de',states:{'sensor.room':{state:'open_now',attributes:{room_name:'Wohnzimmer',display_mode:'room_air'}}}};
  c.getBoundingClientRect=()=>({width:390});return c;
}
const H=60*60*1000;const now=100*H;const beginning=now-24*H;
// A new, empty 24-hour recording starts now; it does not show 24 empty hours.
const c=card();c._series=new Map([['temp_in',[]],['co2_in',[]],['co2_out',[]]]);
assert.equal(c._updateGrowingWindow(beginning,now),now);
// Temperature has a four-hour head start, CO2 joins at its actual timestamp.
const first=now-4*H;
c._series.set('temp_in',[{t:first,v:23},{t:first+H,v:23.5},{t:now-2*H,v:23.8}]);
c._series.set('co2_in',[{t:now-H,v:650},{t:now,v:800}]);
assert.equal(c._updateGrowingWindow(beginning,now),first,'first real measurement defines one shared origin');
const width=300;
const x=t=>(t-c._start)/(c._end-c._start)*width;
assert.equal(x(first),0);assert.equal(x(now),300);
assert.ok(x(now-H)>200,'new CO2 source joins far to the right, never resets its own axis');
// Oldest value moves out only when the selected 24-hour history window catches it.
const future=first+25*H;
c._series.set('temp_in',[{t:future-24*H,v:22.5},{t:future-H,v:23}]);
c._series.set('co2_in',[{t:future-H/2,v:800}]);
assert.equal(c._updateGrowingWindow(future-24*H,future),future-24*H);
// A prior state carried in from before the queried window means the full
// requested window is already backed by a known HA state, not newly created.
c._series.set('temp_in',[{t:future-24*H,v:24,carriedFrom:future-40*H}]);
c._series.set('co2_in',[{t:future-H/2,v:800}]);
assert.equal(c._updateGrowingWindow(future-24*H,future),future-24*H,
  'a real state carried from before the window must retain the full 24-hour horizon even when a new CO2 source joins much later');
// The orange holding line starts at the first recorded outage; another
// unavailable event cannot move its start or its last-known value.
const t0=10_000,t1=20_000,t2=30_000,t3=40_000;
const recorded=[{t:t0,v:850},{t:t1,v:null},{t:t1+1000,v:null},{t:t2,v:1200},
  {t:t3,v:null}];
const runs=c._outageRuns(recorded,0,50_000);
assert.equal(runs.length,2);
assert.deepEqual([...runs.map(r=>[r.start,r.end,r.value])],[[t1,t2,850],[t3,50_000,1200]]);
const m=c._metrics[1],axis=c._axis(m,[850,1200]);
const html=c._outagePaths(recorded,m,axis,n=>n/1000,p=>p*300,'#3388dd',0,50_000);
assert.equal((html.match(/data-history-outage="co2_in"/g)||[]).length,2);
assert.match(html,/stroke="#ff9500"[^>]*stroke-opacity=".27"/);
assert.match(html,/M20\.0 .* L30\.0 /,'first outage ends precisely where sensor recovers');
assert.ok(!html.includes('L40.0') || html.includes('L50.0'),'last outage is held until now');
assert.equal(c._atOrBefore(recorded,25_000).v,null,'no fake valid number at cursor during outage');
// Keep the genuine measured series broken on recovery, distinct from stale
// orange holds, and preserve the previous step gap behavior.
const valid=c._plotSamples(recorded,0,50_000);
assert.notEqual(valid[0].segment,valid[1].segment);
// Check actual SVG uses the hold layer and the one shared growing X-axis.
c._series=new Map([['co2_in',recorded],['temp_in',[{t:t0,v:22},{t:t3,v:23}]],['co2_out',[]]]);
c._start=t0;c._end=50_000;c._cursor=45_000;c._history=[];
c._render();
assert.match(c.shadowRoot.innerHTML,/data-history-outage="co2_in"/);
assert.equal((c.shadowRoot.innerHTML.match(/class="reading"/g)||[]).length,3);
assert.match(c.shadowRoot.innerHTML,/data-room-status-row/);
// Frequent flapping may leave tens of thousands of state transitions. Outage
// rendering must be bounded to pixels instead of producing an unbounded DOM.
const many=[];for(let i=0;i<40000;i++)many.push({t:i*1000,v:i%2?null:800+i%5});
const time=performance.now();
const denseHtml=c._outagePaths(many,m,axis,n=>n/40000000*390,p=>p*300,'#3388dd',0,40000000);
const elapsed=performance.now()-time;
assert.ok(elapsed<3000,`40k outage transitions should render promptly: ${elapsed.toFixed(0)}ms`);
assert.ok(denseHtml.length<400000,'40k transitions should not create megabytes of SVG for a 390px chart');
console.log('PASS COMPLETE6: one growing time axis, late sensor joins, orange hold/recovery and cursor truth; dense outages '+elapsed.toFixed(1)+'ms');
