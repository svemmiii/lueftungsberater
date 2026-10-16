import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class Stub {
  attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null;},querySelectorAll(){return [];}};return this.shadowRoot;}
  dispatchEvent(){return true;}
}
const timers=new Map();let timerID=0;
const context={console,HTMLElement:Stub,customElements:{get(){},define(){}},
  window:{customCards:[],localStorage:{getItem(){return null;},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},
  navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
  setTimeout(cb,ms){const id=++timerID;timers.set(id,{cb,ms});return id;},clearTimeout(id){timers.delete(id);},setInterval(){return 1;},clearInterval(){},CustomEvent:class{},Event:class{}};
vm.createContext(context);
vm.runInContext(source+'\nglobalThis.HistoryCard=LueftungsberaterHistoryCard;',context);
const Card=context.HistoryCard;
const now=Date.now(), keys=['co2_in','co2_out','temp_in','temp_out','humidity_in','humidity_out','target_temp'];
const units={co2_in:'ppm',co2_out:'ppm',temp_in:'°C',temp_out:'°C',humidity_in:'%',humidity_out:'%',target_temp:'°C'};
const lows={temp_in:22,humidity_in:40};
const highs={co2_in:1000,temp_in:24,humidity_in:60};
const vals={co2_in:[850,1200],co2_out:[450,455],temp_in:[23,22],temp_out:[12,11],humidity_in:[58,64],humidity_out:[68,70],target_temp:[23,23]};
const card=new Card();
card._config={entity:'sensor.room',hours:24,metrics:keys,colors:{}};
card._metrics=keys.map(key=>({key,unit:units[key],low:lows[key]??null,high:highs[key]??null}));
card._series=new Map(keys.map(key=>[key,[{t:now-3600000,v:vals[key][0]},{t:now,v:vals[key][1]}]]));
card._start=now-3600000;card._end=now;card._history=[];
card._hass={language:'de',states:{'sensor.room':{attributes:{room_name:'Room',display_mode:'room_air'}}}};
for(const width of [320,390,600,900]){
  card.getBoundingClientRect=()=>({width});card._render();
  const html=card.shadowRoot.innerHTML;
  assert.equal((html.match(/data-inline-axis=/g)||[]).length,3);
  assert.match(html,/data-inline-axis="co2:ppm" data-axis-side="left"/);
  assert.match(html,/data-inline-axis="temp:°C" data-axis-side="right"/);
  assert.match(html,/data-inline-axis="humidity:%" data-axis-side="right"/);
  const hit=html.match(/<rect x="([\d.]+)" y="0" width="([\d.]+)" height="398" fill="transparent" data-hit\/>/);
  const left=Number(hit?.[1]),right=left+Number(hit?.[2]);
  assert.ok(left>0&&right<width&&right-left>=60,`plot stays between 2-sided outer scales at width ${width}`);
  const position=key=>Number(html.match(new RegExp(`data-axis-zone="${key}"[^>]*>[\\s\\S]*?<rect x="([\\d.]+)"`))?.[1]);
  assert.ok(position('co2_in')<left,`CO₂ border is on the left at ${width}`);
  assert.ok(position('humidity_in')>right,`humidity border is on the right at ${width}`);
  assert.ok(html.includes('fill="#df1717"'),'strong alert red used in boundary bands');
  assert.equal((html.match(/class="reading"/g)||[]).length,7,'single values list preserved');
}
const red=card._curvePaths([{t:0,v:900},{t:1,v:1200}],{key:'co2_in',low:null,high:1000},{y:x=>x},x=>x,x=>x,'#123abc');
assert.ok(red.includes('stroke="#df1717"')&&red.includes('stroke="#123abc"'));
assert.doesNotMatch(red,/var\(--error-color|#d35b5b/i);
// Changing the period must reuse a wider cache when navigating back to 6h.
const history=new Card();history._config={entity:'sensor.room',hours:24};
let calls=[];
history._hass={callApi:async(_method,url)=>{
  calls.push(url);
  return [[{entity_id:'sensor.co2',state:'700',last_updated:new Date(now-25*60000).toISOString(),attributes:{unit_of_measurement:'ppm'}}]];
}};
const day=new Date(now-86400000), end=new Date(now);
await history._getHistory(['sensor.co2'],day,end);
assert.equal(calls.length,1);
history._config.hours=6;
const six=await history._getHistory(['sensor.co2'],new Date(now-6*3600000),end);
assert.equal(calls.length,1,'switching 24h -> 6h reuses the covered Recorder interval');
assert.equal(six[0].length,1);
history._config.hours=168;
await history._getHistory(['sensor.co2'],new Date(now-7*86400000),end);
assert.equal(calls.length,2,'larger range needs one additional historical request');
history._config.hours=24;
await history._getHistory(['sensor.co2'],day,end);
assert.equal(calls.length,2,'switch back to 24h must be instant from retained cache');
assert.ok(history._historyCache.get('sensor.co2').from<=now-7*86400000);
// An incremental follow-up fetch keeps the earlier cache coverage.
await history._getHistory(['sensor.co2'],new Date(now-6*3600000),new Date(now+65000));
assert.equal(calls.length,3);
assert.ok(history._historyCache.get('sensor.co2').from<=now-7*86400000);
// Switching to a DIFFERENT room cannot inherit the old cache.
history._config.entity='sensor.other';
await history._getHistory(['sensor.co2'],new Date(now-6*3600000),end);
assert.equal(calls.length,4,'different room requires fresh source lookup');
// An old, slow metadata response must not repaint the old window after
// the user selected another period while its request was in flight.
const race=new Card();race._config={entity:'sensor.room',hours:24,metrics:[],colors:{}};
let resolveOld,metricsCalls=0;
race._hass={language:'de',user:{is_admin:false},states:{'sensor.room':{attributes:{room_name:'Room'}}},
  callWS:message=>{
    if(message.type.endsWith('/history_metrics')){
      metricsCalls++;
      return metricsCalls===1?new Promise(resolve=>{resolveOld=resolve;}):Promise.resolve([]);
    }
    if(message.type.endsWith('/history_recommendations'))return Promise.resolve({});
    if(message.type.endsWith('/history_room_info'))return Promise.resolve({room:'r',enabled:[],helpers:{}});
    throw new Error(message.type);
  },
  callApi:async()=>[]};
const oldRequest=race._refresh();
race._config={...race._config,hours:6};race._configRevision++;
await race._refresh(); // queued until the old in-flight request has ended
resolveOld([]);
await oldRequest;
for(let i=0;i<30;i++){
  await new Promise(resolve=>setImmediate(resolve));
  if(metricsCalls>=2&&!race._loading)break;
}
assert.equal(metricsCalls,2,'old and new window requested exactly once');
assert.equal(race._visibleScope,'sensor.room:6');
assert.equal(race._start,race._end,'without any recorded samples the new window starts at now, never shows an artificial 6h timeline');
console.log('PASS v0.11.6 COMPLETE(2): strong red, split axes, cache reuse, room isolation and stale-range cancellation');
