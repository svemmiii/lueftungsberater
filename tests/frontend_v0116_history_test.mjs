import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
const timers=new Map();let nextTimer=1;
const fakeTimeout=(callback,delay)=>{const id=nextTimer++;timers.set(id,{callback,delay});return id;};
const fakeClear=id=>timers.delete(id);
class Element {
  attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null;},querySelectorAll(){return [];}};return this.shadowRoot;}
  dispatchEvent(){return true;}
}
const context={console,HTMLElement:Element,customElements:{get(){},define(){}},
  window:{customCards:[],localStorage:{getItem(){return null;},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},
  navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
  setTimeout:fakeTimeout,clearTimeout:fakeClear,setInterval(){return 1;},clearInterval(){},Event:class{},CustomEvent:class{}};
vm.createContext(context);
vm.runInContext(`${source}\nglobalThis.HistoryCard=LueftungsberaterHistoryCard`,context);
const Card=context.HistoryCard;
const keys=['co2_in','co2_out','temp_in','temp_out','humidity_in','humidity_out','target_temp'];
const units={co2_in:'ppm',co2_out:'ppm',temp_in:'°C',temp_out:'°C',humidity_in:'%',humidity_out:'%',target_temp:'°C'};
const ranges={co2_in:{high:1000},co2_out:{},temp_in:{low:22,high:24},temp_out:{},humidity_in:{low:40,high:60},humidity_out:{},target_temp:{}};
const values={co2_in:630,co2_out:450,temp_in:23,temp_out:13,humidity_in:60,humidity_out:67,target_temp:23};
const now=Date.now(),start=now-60*60*1000;
const card=new Card();
card._config={entity:'sensor.room',hours:24,metrics:keys,colors:{}};
card._metrics=keys.map(key=>({key,unit:units[key],low:ranges[key].low??null,high:ranges[key].high??null}));
card._series=new Map(keys.map(key=>[key,[{t:start,v:values[key]},{t:now,v:key==='co2_in'?750:values[key]}]]));
card._start=start;card._end=now;card._cursor=null;card._history=[];
card._hass={language:'de',states:{'sensor.room':{attributes:{room_name:'Wohnzimmer',display_mode:'room_air'}}}};
const listeners={};const cursorLine={setAttribute(){}};const detail={innerHTML:''};
const hit={addEventListener:(name,callback)=>listeners[name]=callback,
  getBoundingClientRect:()=>({left:100,width:200}),setPointerCapture(){},hasPointerCapture(){return false;}};
card.shadowRoot.querySelector=selector=>selector==='[data-hit]'?hit:selector==='[data-cursor-line]'?cursorLine:
  selector==='[data-cursor-detail]'?detail:null;
card._render();
let html=card.shadowRoot.innerHTML;
assert.equal((html.match(/data-inline-axis=/g)||[]).length,3,'seven selected curves share three physical y-axes');
for(const unit of ['°C','ppm','%'])assert.match(html,new RegExp(`font-weight="600">${unit.replace('%','%')}`));
assert.equal(card._plotCache.get('temp_in').axis,card._plotCache.get('target_temp').axis);
assert.equal(card._plotCache.get('temp_out').axis,card._plotCache.get('temp_in').axis);
assert.equal(card._plotCache.get('co2_in').axis,card._plotCache.get('co2_out').axis);
assert.equal(card._plotCache.get('humidity_in').axis,card._plotCache.get('humidity_out').axis);
assert.equal(card._plotCache.get('temp_in').axis.y(23),card._plotCache.get('target_temp').axis.y(23));
assert.ok(!html.includes('data-metric-scales')&&!html.includes('class="legend"'),'no duplicate scale cards or palette list');
assert.equal((html.match(/class="values"/g)||[]).length,1);
assert.equal((html.match(/class="reading"/g)||[]).length,7,'one entry per metric, no repeats');
for(const outdoor of ['temp_out','humidity_out','co2_out'])
  assert.doesNotMatch(html,new RegExp(`data-axis-zone="${outdoor}"`),'outdoor measurements do not inherit room comfort bands');
assert.match(html,/data-axis-zone="co2_in"/);
assert.match(html,/data-axis-zone="humidity_in"/);
assert.match(html,/data-inline-axis="temp:°C"/);
assert.match(html,/data-inline-axis="co2:ppm"/);
assert.match(html,/data-inline-axis="humidity:%"/);
assert.match(html,/750 ppm/,'live readout shows the latest recorded measurement');
assert.match(html,/Jetzt ·/,'current cursor is clearly identified');

const evt=clientX=>({clientX,pointerType:'mouse',buttons:0});
listeners.pointermove(evt(150)); // 25% of the selected period
assert.ok(Math.abs(card._cursor-(start+.25*(now-start)))<1);
assert.match(detail.innerHTML,/630 ppm/,'the historical cursor determines the only values list');
assert.doesNotMatch(detail.innerHTML,/750 ppm/);
assert.ok(!detail.innerHTML.includes('Invalid Date'));
assert.equal([...timers.values()].filter(t=>t.delay===300000).length,1);
const firstTimer=[...timers.entries()].find(([id,t])=>t.delay===300000)[0];
card._end=now+1000;card._render(); // automatic updates are NOT user activity
assert.ok(timers.has(firstTimer));
listeners.pointermove(evt(180)); // 40% user hover restarts exactly 5 minutes
assert.ok(!timers.has(firstTimer));
const pending=[...timers.entries()].filter(([id,t])=>t.delay===300000);
assert.equal(pending.length,1);
let refreshed=0;
card.isConnected=true;
card._refresh=async()=>{refreshed++;card._start=start;card._end=now+5000;card._cursor=card._end;card._render();};
timers.delete(pending[0][0]); // browser removes a one-shot timer when it fires
pending[0][1].callback();
assert.equal(refreshed,1,'idle deadline returns to now by fetching fresh data');
assert.equal(card._cursor,card._end);
assert.match(card.shadowRoot.innerHTML,/750 ppm/,'after five minutes the readout returns to current values');
assert.match(card.shadowRoot.innerHTML,/Jetzt ·/);
assert.equal(timers.size,0,'idle callback is one-shot and not rescheduled by render');
console.log('PASS v0.11.6: seven curves/three inline axes; one cursor-driven value list; outdoor limits; five-minute idle to live');
