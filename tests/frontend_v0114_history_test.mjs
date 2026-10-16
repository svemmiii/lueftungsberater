import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class HTMLElementStub {
  attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}};return this.shadowRoot;}
  dispatchEvent() {return true;}
}
const ctx={console,HTMLElement:HTMLElementStub,customElements:{get(){},define(){}},
window:{customCards:[],confirm(){return false},localStorage:{getItem(){return null},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},
navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
setTimeout,clearTimeout,setInterval,clearInterval,CustomEvent:class{},Event:class {constructor(){this.detail={}}}};
vm.createContext(ctx);
vm.runInContext(`${source}\nglobalThis.HistoryCard=LueftungsberaterHistoryCard`,ctx);
const Card=ctx.HistoryCard;
const card=new Card();
card.setConfig({entity:'sensor.room',metrics:['co2_in','humidity_in'],colors:{co2_in:'#123abc',humidity_in:'#00ee00'}});
card._metrics=[{key:'co2_in',label:'CO₂ innen',unit:'ppm',low:null,high:1000},{key:'humidity_in',label:'Feuchte innen',unit:'%',low:40,high:60}];
card._series=new Map([['co2_in',[{t:0,v:600},{t:3600000,v:1400}]],['humidity_in',[{t:0,v:38},{t:3600000,v:70}]]]);
card._start=0;card._end=3600000;card._cursor=3600000;
card._history=[{t:0,key:'open_now',attrs:{room_status:'red',ventilation_status:'orange'},kind:'decision'}];
card._hass={language:'de',states:{'sensor.room':{state:'open_now',attributes:{room_name:'Wohnung',display_mode:'room_air'}}}};
card._render();
const html=card.shadowRoot.innerHTML;
assert.match(html,/Lüftungsassistent|Historie/);
assert.match(html,/#123abc/);
assert.match(html,/#00ee00/);
assert.match(html,/1400|1.400/);
assert.match(html,/70 %/);
assert.match(html,/data-axis-zone="humidity_in"/);
// COMPLETE(3): red zone stripes must be identified with their own physical
// measurement (name, unit, exact low/high limit) instead of generic red bars.
assert.match(html,/data-axis-zone="co2_in" data-axis-zone-kind="upper"/);
assert.match(html,/data-axis-zone="humidity_in" data-axis-zone-kind="upper"/);
assert.match(html,/data-axis-zone="humidity_in" data-axis-zone-kind="lower"/);
assert.match(html,/data-inline-axis="co2:ppm"/);
assert.match(html,/data-inline-axis="humidity:%"/);
assert.match(html,/CO₂ innen: &gt; 1\.000 ppm/);
assert.match(html,/Luftfeuchte innen: &lt; 40 %/);
assert.match(html,/data-axis-zone="co2_in"[^>]*>[\s\S]*?stroke="#123abc"/);
assert.match(html,/data-axis-zone="humidity_in"[^>]*>[\s\S]*?stroke="#00ee00"/);
assert.doesNotMatch(html,/data-metric-scales|class="legend"/,'there is only one value list, no duplicate legend and cards');
assert.match(html,/Jetzt lüften/);
const axes=card._axis(card._metrics[0],[600,1400],true);
const humid=card._axis(card._metrics[1],[38,70],true);
assert.ok(axes.y(600)<.72,'one-sided CO2 is outside the lower red humidity-only zone');
assert.ok(axes.y(1400)<.4,'high CO2 enters upper red zone');
assert.ok(humid.y(38)>.72&&humid.y(70)<.38,'humidity traverses both red zones');
assert.ok(card._historicalDecision(3600000)?.color==='red');
console.log('PASS: v0.11.4 history axes, fixed zones, raw cursor values, colors');

// COMPLETE(41): for a single high-only metric, the FULL red field must end
// at the metric's .40 high boundary (not the .38 used by dual-limit axes).
// The mismatch was ~0.02 * (271 - 24) = 4.94 SVG pixels.
function historyChartWith(metrics) {
  const test=new Card();
  test.setConfig({entity:'sensor.room',metrics:metrics.map(m=>m.key),hours:24,colors:{}});
  test._metrics=metrics;
  test._series=new Map(metrics.map(m=>[m.key,[{t:0,v:(m.high??100)/2},{t:3600000,v:(m.high??100)*1.2}]]));
  test._start=0;test._end=3600000;test._cursor=3600000;
  test._history=[];
  test._hass={language:'de',states:{'sensor.room':{state:'open_now',attributes:{room_name:'Room'}}}};
  test._render();
  return test.shadowRoot.innerHTML;
}
function upperRedField(html) {
  const match=html.match(/<rect x="[^"]+" y="([\d.]+)" width="[^"]+" height="([\d.]+)" fill="#df1717" fill-opacity="0\.12"\/>/);
  return match?{top:Number(match[1]),bottom:Number(match[1])+Number(match[2])}:null;
}
// COMPLETE(3): the separate room-status lane pushes the measurement plot down.
const chartTop=86,chartBottom=398-48;
const yAt=relative=>chartTop+relative*(chartBottom-chartTop);
const co2Only=historyChartWith([{key:'co2_in',unit:'ppm',low:null,high:1000}]);
const highOnlyField=upperRedField(co2Only);
assert.ok(highOnlyField,'CO2-only chart has a red upper-limit field');
assert.ok(Math.abs(highOnlyField.top-yAt(.04))<1e-8);
assert.ok(Math.abs(highOnlyField.bottom-yAt(.40))<1e-8,
 'high-only red field must touch the exact CO2 threshold position');
assert.match(co2Only,/font-size="12"[^>]*>[^<]*<\/text>/,
 'axis values remain legible in a responsive mobile chart');
const humidityOnly=historyChartWith([{key:'humidity_in',unit:'%',low:40,high:60}]);
const dualField=upperRedField(humidityOnly);
assert.ok(dualField);
assert.ok(Math.abs(dualField.bottom-yAt(.38))<1e-8,
 'dual-limit red field must touch its distinct humidity high boundary');
assert.match(humidityOnly,/fill-opacity="0\.10"/,'dual-limit lower red field remains present');
const combined=historyChartWith([
 {key:'co2_in',unit:'ppm',low:null,high:1000},
 {key:'humidity_in',unit:'%',low:40,high:60},
]);
assert.equal(upperRedField(combined),null,'do not shade multiple independent scales');
assert.match(combined,/data-axis-zone="co2_in"/);
assert.match(combined,/data-axis-zone="humidity_in"/);
// Per-metric red bands must match their on-screen labeled scale entries.
for (const key of ['co2_in','humidity_in']) {
  assert.match(combined,new RegExp(`data-axis-zone="${key}"`));
  assert.match(combined,new RegExp(`data-inline-axis="${key.split('_')[0]}:`));
}
const borderCo2=combined.match(/data-axis-zone="co2_in"[^>]*>[\s\S]*?<rect[^>]*stroke="([^"]+)"/);
assert.ok(borderCo2);
assert.equal(borderCo2[1],(new Card())._color('co2_in',0),'CO2 zone retains its curve color');
assert.match(combined,/CO₂ innen: &gt; 1\.000 ppm/);
console.log('PASS: high-only and dual-limit red bounds precisely meet their own high threshold; mobile axis labels');



// v0.11.5 – responsive geometry, stable colors and same physical temperature scale.
const manyKeys=['co2_in','co2_out','temp_in','temp_out','humidity_in','humidity_out','target_temp','absolute_in','wind_out'];
const distinct=new Card();
distinct._config={entity:'sensor.room',hours:24,metrics:manyKeys,colors:{}};
distinct._hass={language:'de',states:{'sensor.room':{attributes:{room_name:'Room',display_mode:'room_air'}}}};
distinct._metrics=manyKeys.map(key=>({key,unit:key.includes('temp')?'°C':'ppm',low:null,high:null}));
distinct._series=new Map(manyKeys.map((key,i)=>[key,[{t:100,v:i===2||i===6?23:700+i},{t:1000,v:i===2||i===6?23:800+i}]]));
distinct._start=0;distinct._end=2000;distinct._cursor=1000;
// v0.11.6 COMPLETE(4): paired indoor/outdoor traces intentionally share
// their base color; solid/dashed strokes distinguish them. Different
// physical families still use distinct default colors.
assert.equal(distinct._color('co2_in',0),distinct._color('co2_out',1));
assert.equal(distinct._color('temp_in',2),distinct._color('temp_out',3));
assert.equal(distinct._color('temp_in',2),distinct._color('target_temp',6));
assert.equal(distinct._color('humidity_in',4),distinct._color('humidity_out',5));
assert.equal(new Set(['co2_in','temp_in','humidity_in','absolute_in','wind_out'].map((key,i)=>distinct._color(key,i))).size,5,
  'independent physical families retain distinct colors');
const co2Color=distinct._color('co2_in',0);
distinct._config.metrics=[...manyKeys].reverse();
assert.equal(distinct._color('co2_in',8),co2Color,'reordering cannot change a metric color');
for(const cardWidth of [360,600,900,1400]){
  distinct._chartWidth=cardWidth;
  distinct._plotCache.clear();distinct._stripCache=null;distinct._render();
  const expected=cardWidth-24;
  assert.match(distinct.shadowRoot.innerHTML,new RegExp(`viewBox="0 0 ${expected} 398"`),
    `all nine curves stay within a ${cardWidth}px dashboard column`);
  assert.doesNotMatch(distinct.shadowRoot.innerHTML,/history-scrubber|overflow-x:auto/);
}
const axisIndoor=distinct._plotCache.get('temp_in').axis;
const axisTarget=distinct._plotCache.get('target_temp').axis;
assert.equal(axisIndoor.y(23),axisTarget.y(23),'target and indoor physical temperature must share Y coordinate');
distinct._series.set('target_temp',[]);
distinct._plotCache.clear();distinct._render();
assert.equal(distinct._plotCache.get('temp_in').axis.y(23),distinct._plotCache.get('target_temp').axis.y(23),
 'missing target history must not create a fake independent 0–1 scale');
// Only the unhealthy portion crosses the backend supplied high limit.
const humidity={key:'humidity_in',low:40,high:60};
const good='#3189d0';
const coordinates=t=>t, position=v=>v;
const colored=distinct._curvePaths([{t:0,v:58},{t:100,v:62},{t:200,v:59}],humidity,
 {y:position},coordinates,position,good);
assert.ok(colored.includes(`stroke="${good}"`) && colored.includes('stroke="#df1717'),
  'same curve must contain normal and red sections');
assert.match(colored,/50\.0,60\.0/,'first crossing at 60% must be split exactly');
assert.match(colored,/166\.7,60\.0/,'return below 60% must be split exactly');
assert.equal((colored.match(/stroke="#df1717/g)||[]).length,1,
 'only the out-of-band span is red (and not the entire curve)');
// Technical state update is NOT an updated room decision.
const status=new Card();
status._config={entity:'sensor.room',hours:24};
status._hass={states:{'sensor.room':{attributes:{display_mode:'room_air'}}}};
status._history=[{t:10,kind:'decision',key:'room_good',attrs:{room_status:'green',room_recommendation_key:'room_good'}},
 {t:15,kind:'advisor',key:'optional',attrs:{}}];
status._decisionEvents=status._history.filter(e=>e.kind==='decision');
assert.equal(status._historicalDecision(16).key,'room_good');
assert.equal(status._historicalDecision(16).color,'green');
status._hass.states['sensor.room'].attributes.display_mode='ventilation';
assert.equal(status._historicalDecision(16).key,'room_good',
 'without recorded ventilation key the decision timeline still stays authoritative');
// The editor no longer has a second perspective selector.
assert.doesNotMatch(source,/data-perspective/);
// A failed first websocket request leaves a valid time window and no Invalid Date.
const unavailable=new Card();
unavailable._config={entity:'sensor.room',hours:24,metrics:['co2_in']};
unavailable._hass={language:'de',states:{'sensor.room':{attributes:{room_name:'Room'}}},
 callWS:async()=>{throw Error('simulate history_room_info outage');}};
await unavailable._refresh();
assert.ok(Number.isFinite(unavailable._start)&&Number.isFinite(unavailable._end));
assert.doesNotMatch(unavailable.shadowRoot.innerHTML,/Invalid Date/);
// One bad Recorder source must not prevent another curve loading.
const partial=new Card();
partial._config={entity:'sensor.room',hours:24,metrics:['co2_in','humidity_in']};
partial._hass={language:'de',user:{is_admin:false},states:{'sensor.room':{attributes:{room_name:'R'}}},
 callWS:async msg=>msg.type.endsWith('/history_metrics')?[
  {key:'co2_in',source:'sensor.good',unit:'ppm',low:null,high:1000},
  {key:'humidity_in',source:'sensor.bad',unit:'%',low:40,high:60}]:
  msg.type.endsWith('/history_room_info')?{room:'r',enabled:['decision'],helpers:{}}:{},
 callApi:async(_method,url)=>{
  const entities=decodeURIComponent(url.match(/filter_entity_id=([^&]+)/)[1]).split(',');
  if(entities.includes('sensor.bad'))throw Error('one Recorder source failed');
  return entities.includes('sensor.good')?[[{entity_id:'sensor.good',state:'780',
    attributes:{unit_of_measurement:'ppm'},last_updated:new Date(Date.now()-10000).toISOString()}]]:[];
 }};
await partial._refresh();
assert.equal(partial._series.get('co2_in').at(-1).v,780);
assert.match(partial._notice,/Verlaufsquelle/);
console.log('PASS v0.11.5: responsive 9+ curves, shared temperature scale, isolated red crossings, authoritative status, partial load and valid cursor');
// Editor's live `hass` updates keep picker/list nodes stable unless the
// configured source/availability signature genuinely changes.
const editor115=vm.runInContext('new LueftungsberaterHistoryCardEditor()',ctx);
editor115._config={entity:'sensor.room',metrics:['co2_in']};
editor115.shadowRoot.querySelector=sel=>sel==='[data-entity]'?{}:null;
let editorRenders=0;
editor115._render=()=>{editorRenders++;};
const editorStates={
 'sensor.room':{attributes:{source_co2:'sensor.co2',co2_ppm:800,room_name:'Room'}}
};
editor115.hass={states:editorStates};
assert.equal(editorRenders,1);
editorStates['sensor.room'].attributes.co2_ppm=950;
editor115.hass={states:editorStates};
assert.equal(editorRenders,1,'unrelated sensor readings must not close editor controls');
editorStates['sensor.room'].attributes.source_co2='sensor.new_sensor';
editor115.hass={states:editorStates};
assert.equal(editorRenders,2,'a genuinely changed configured source updates editor choices');
console.log('PASS v0.11.5: editor controls persist through HA state reports');

// v0.11.5 COMPLETE(2): test the live edge, large status timelines, mixed
// scales, empty history refetch, and the confirmed Recorder exclusion notice.
{
  const follow=new Card();
  follow._config={entity:'sensor.room',metrics:['co2_in'],hours:24};
  const sampleTime=new Date(Date.now()-3*3600000).toISOString();
  follow._hass={language:'de',user:{is_admin:false},states:{'sensor.room':{attributes:{display_mode:'room_air'}}},
    callWS:async msg=>msg.type.endsWith('history_metrics')?
      [{key:'co2_in',source:'sensor.co2',unit:'ppm',low:null,high:1000}]:
      msg.type.endsWith('history_room_info')?{room:'r',enabled:[],helpers:{}}:{},
    callApi:async()=>[[{entity_id:'sensor.co2',state:'730',last_updated:sampleTime,
      attributes:{unit_of_measurement:'ppm'}}]]};
  follow._end=Date.now()-61000;
  follow._start=follow._end-86400000;
  follow._cursor=follow._end;
  await follow._refresh();
  assert.equal(follow._cursor,follow._end,'live cursor follows the moving right edge');
  const frozen=follow._end-3600000;
  follow._cursor=frozen;
  await follow._refresh();
  assert.equal(follow._cursor,frozen,'user-selected historical cursor stays pinned');
}
{
  const fast=new Card();
  fast._config={entity:'sensor.room',hours:24};
  fast._hass={states:{'sensor.room':{attributes:{display_mode:'room_air'}}}};
  const count=40000;
  fast._start=0;fast._end=count*1000;
  fast._history=Array.from({length:count},(_,i)=>({t:i*1000,key:'room_good',
    attrs:{room_status:i%2===0?'green':'orange',room_recommendation_key:'room_good'},kind:'decision'}));
  fast._decisionEvents=fast._history;
  fast._advisorEvents=[];
  const now=performance.now();
  const statusSvg=fast._statusStrips(50,450);
  const elapsed=performance.now()-now;
  assert.ok(statusSvg.includes('<rect'),'long decision history still renders a status strip');
  assert.ok(elapsed<3000,`40k decision events should render in under 3s, took ${elapsed.toFixed(0)}ms`);
  console.log(`PASS: 40k decision events status strip ${elapsed.toFixed(1)}ms`);
}
{
  const scales=historyChartWith([
    {key:'co2_in',unit:'ppm',low:null,high:1000},
    {key:'humidity_in',unit:'%',low:35,high:60},
  ]);
  assert.match(scales,/data-inline-axis="co2:ppm"/);
  assert.match(scales,/data-inline-axis="humidity:%"/);
  assert.match(scales,/CO₂ innen: &gt; 1\.000 ppm/);
  assert.match(scales,/ppm/);
  assert.match(scales,/%/);
}
{
  const cache=new Card();
  cache._config={entity:'sensor.room',hours:24};
  const requests=[];
  cache._hass={callApi:async (_method,url)=>{requests.push(url);return requests.length===1?[]:
    [[{entity_id:'sensor.new',state:'123',last_updated:new Date(end.getTime()-250).toISOString()}]];}};
  const end=new Date(),start=new Date(end.getTime()-86400000);
  await cache._getHistory(['sensor.new'],start,end);
  assert.equal(requests.length,1);
  const record=cache._historyCache.get('sensor.new');
  assert.equal(record.rows.length,0);
  record.to-=1600;
  await cache._getHistory(['sensor.new'],start,end);
  assert.equal(requests.length,2,'empty history must be retried before the 55-second cache expires');
  assert.equal(cache._historyCache.get('sensor.new').rows.length,1);
}
{
  const excluded=new Card();
  excluded._config={entity:'sensor.room',metrics:[],hours:24};
  excluded._hass={language:'de',user:{is_admin:false},states:{'sensor.room':{attributes:{display_mode:'room_air'}}},
    callWS:async msg=>msg.type.endsWith('history_metrics')?[]:
      msg.type.endsWith('history_room_info')?{room:'r',enabled:['co2_in'],helpers:{co2_in:'sensor.history_co2'},recorder_excluded:['sensor.history_co2']}:{},
    callApi:async()=>[]};
  await excluded._refresh();
  assert.match(excluded.shadowRoot.innerHTML,/data-recorder-excluded/);
  assert.match(excluded.shadowRoot.innerHTML,/sensor.history_co2/);
  assert.match(excluded.shadowRoot.innerHTML,/include\/exclude/);
}
console.log('PASS: v0.11.5 COMPLETE(2) live cursor, 40k-event status speed, mixed scales, early empty-cache refresh and Recorder exclusions');
{
  const delayed=new Card();
  delayed._config={entity:'sensor.room',metrics:['co2_in'],hours:24};
  delayed.isConnected=true;
  delayed._hass={language:'de',user:{is_admin:false},states:{'sensor.room':{attributes:{display_mode:'room_air'}}},
    callWS:async msg=>msg.type.endsWith('history_metrics')?[{key:'co2_in',source:'sensor.raw',unit:'ppm',low:null,high:1000}]:
      msg.type.endsWith('history_room_info')?{room:'r',enabled:['co2_in','decision'],helpers:{co2_in:'sensor.helper_co2'}}:{},
    callApi:async()=>[]};
  await delayed._refresh();
  assert.equal(delayed._emptyHistoryRetryCount,1,'empty newly registered helper gets a bounded follow-up');
  assert.ok(delayed._emptyHistoryRetryTimer,'fresh helper must not wait a full refresh interval');
  clearTimeout(delayed._emptyHistoryRetryTimer);
  delayed._emptyHistoryRetryTimer=null;
  delayed._hass.callWS=async msg=>msg.type.endsWith('history_metrics')?[{key:'co2_in',source:'sensor.raw',unit:'ppm',low:null,high:1000}]:
    msg.type.endsWith('history_room_info')?{room:'r',enabled:['co2_in','decision'],helpers:{co2_in:'sensor.helper_co2'},recorder_excluded:['sensor.helper_co2']}:{},
  await delayed._refresh();
  assert.equal(delayed._emptyHistoryRetryTimer,null,'Recorder-excluded helper is not polled repeatedly');
  delayed.disconnectedCallback();
}
console.log('PASS: bounded first-helper rechecks are canceled for Recorder-excluded entities');
