import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class HTMLStub {
  attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null;},querySelectorAll(){return [];}};return this.shadowRoot;}
  dispatchEvent(){return true;}
}
const ctx={console,HTMLElement:HTMLStub,customElements:{get(){},define(){}},window:{customCards:[],confirm(){},localStorage:{getItem(){return null},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},setTimeout,clearTimeout,setInterval,clearInterval,Event:class{},CustomEvent:class{}};
vm.createContext(ctx);
vm.runInContext(`${source}\nglobalThis.HistoryCard=LueftungsberaterHistoryCard;globalThis.HistoryEditor=LueftungsberaterHistoryCardEditor`,ctx);
const card=new ctx.HistoryCard();
const at=Date.parse('2026-10-13T12:00:00Z');
const rows=[
 {state:'500',last_updated:new Date(at).toISOString()},
 {state:'unavailable',last_updated:new Date(at+10*60000).toISOString()},
 {state:'700',last_updated:new Date(at+20*60000).toISOString()},
];
// Real _refresh parsing path, including out-of-range filter and missing state.
const samples=card._parseHistorySamples(rows,at,at+20*60000);
assert.equal(samples.length,3);
assert.equal(samples[1].v,null);
assert.equal(new Set(card._plotSamples(samples,at,at+20*60000,100).map(p=>p.segment)).size,2,'explicit unavailable splits actual curve');
for(const state of ['', ' ', '\t', 'unknown','unavailable','nan','inf','n/a']){
  assert.equal(card._historyNumber(state),null,`${JSON.stringify(state)} must not turn into zero`);
}
assert.equal(card._historyNumber('0'),0,'real zero remains valid');
const empty=card._parseHistorySamples([{state:' ',last_changed:new Date(at).toISOString()}],at,at);
assert.equal(empty[0].v,null);
const second=card._plotSamples(card._parseHistorySamples([
  {state:'500',last_changed:new Date(at).toISOString()},
  {state:' ',last_changed:new Date(at+2*60000).toISOString()},
  {state:'700',last_changed:new Date(at+5*60000).toISOString()},
],at,at+5*60000),at,at+5*60000);
assert.equal(new Set(second.map(p=>p.segment)).size,2);

card._config={entity:'sensor.room',perspective:'room_air',metrics:['co2_in']};
card._metrics=[{key:'co2_in',unit:'ppm',source:'sensor.co2',high:1000,low:null}];
card._series=new Map([['co2_in',samples]]);
card._hass={language:'de',states:{'sensor.room':{attributes:{room_name:'Room'}}}};
card._history=[{t:at,kind:'decision',key:'open_now',attrs:{room_status:'red',room_recommendation_key:'open_now',ventilation_status:'orange'}},{t:at+7000,kind:'advisor',key:'open_now',attrs:{}}];
card._decisionEvents=card._history.filter(e=>e.kind==='decision');
assert.equal(card._historicalDecision(at+9000).color,'red','matching advisor should keep actual recorded color beyond 5s');
assert.equal(card._historicalDecision(at+9000).key,'open_now');
card._history.push({t:at+10000,kind:'advisor',key:'close_window',attrs:{}});
assert.equal(card._historicalDecision(at+11000).color,null,'different recorded recommendation must NOT borrow old color');
assert.match(card._cursorDetail(card._metrics,at+10*60000,()=>''),/—/,'outage must have no numeric cursor value');
card._config.perspective='ventilation';
assert.equal(card._historicalDecision(at+9000).color,'orange','perspective retains recorded ventilation palette');

// Editor is driven by the backend allowlist, including derived values that do
// not have distinct configured sensor entity IDs in the room advisor.
const editor=new ctx.HistoryEditor();
editor.setConfig({entity:'sensor.room',metrics:['co2_in','absolute_in'],hours:720});
const attrs={instance_id:'entry',room_name:'Wohnung',recommendation_key:'open_now',source_co2:'sensor.co2',co2_ppm:800};
editor.hass={language:'de',states:{'sensor.room':{entity_id:'sensor.room',attributes:attrs}},callWS:async ({type})=>{
  assert.equal(type,'lueftungsberater/history_metrics');
  return [{key:'co2_in',source:'sensor.co2',unit:'ppm',high:1000,low:null},{key:'absolute_in',source:null,unit:'g/m³',high:null,low:null},{key:'wind_out',source:null,unit:'km/h',high:null,low:null}];
}};
await new Promise(resolve=>setImmediate(resolve));
const markup=editor.shadowRoot.innerHTML;
assert.match(markup,/data-metric="absolute_in"/,'computed absolute humidity must be offered');
assert.match(markup,/data-metric="wind_out"/,'provider wind without source entity must be offered');
assert.match(markup,/data-default-range/,'persisted default time range is editable');
assert.match(markup,/value="720" selected/,'saved range is reflected');
assert.match(markup,/data-color="co2_in" value="#3c90df"/,'default color for first curve matches real palette');
assert.match(markup,/data-color="absolute_in" value="#2eaa8b"/,'default color for second curve matches real palette');
assert.match(source,/temporär/,'runtime range is clearly marked temporary');
console.log('PASS: explicit recorder outages, blank states, matching decision colors, derived metrics, palette and persisted editor period');

// Integration-like frontend trace: Recorder rows -> _refresh() -> graph and cursor,
// including an asynchronous decision update and an explicit sensor outage.
const trace=new ctx.HistoryCard();
trace._config={entity:'sensor.trace',metrics:['co2_in'],hours:24,perspective:'room_air',colors:{}};
const base=Date.now()-30*60000;
const date=t=>new Date(t).toISOString();
trace._hass={language:'de',states:{'sensor.trace':{entity_id:'sensor.trace',state:'open_now',attributes:{room_name:'Wohnzimmer',source_co2:'sensor.co2_live',display_mode:'room_air'}},'sensor.co2_live':{entity_id:'sensor.co2_live',state:'700',attributes:{unit_of_measurement:'ppm'}},'sensor.trace_decision':{entity_id:'sensor.trace_decision',attributes:{history_metric:'decision',history_room:'r'}}},callWS:async ({type})=>{
 if(type.endsWith('/history_metrics'))return [{key:'co2_in',source:'sensor.co2_live',unit:'ppm',high:1000,low:null}];
 if(type.endsWith('/history_recommendations'))return {open_now:'Jetzt lüften'};
 if(type.endsWith('/history_room_info'))return {room:'r',enabled:['co2_in','decision'],helpers:{decision:'sensor.trace_decision'}};
 throw Error(type);
}};
trace._getHistory=async ids=>ids.map(id=>id==='sensor.co2_live' ? [
 {entity_id:id,state:'500',attributes:{unit_of_measurement:'ppm'},last_updated:date(base)},
 {entity_id:id,state:'unavailable',last_updated:date(base+10*60000)},
 {entity_id:id,state:'700',attributes:{unit_of_measurement:'ppm'},last_updated:date(base+20*60000)},
] : id==='sensor.trace_decision' ? [
 {entity_id:id,state:'open_now',attributes:{room_recommendation_key:'open_now',room_status:'red',ventilation_status:'orange'},last_updated:date(base)},
] : [
 {entity_id:id,state:'open_now',last_updated:date(base+7000)},
]);
await trace._refresh();
assert.equal(trace._series.get('co2_in').length,3);
assert.equal(trace._series.get('co2_in')[1].v,null);
assert.equal(new Set(trace._plotSamples(trace._series.get('co2_in'),base,base+20*60000).map(x=>x.segment)).size,2);
assert.equal(trace._historicalDecision(base+9000).color,'red');
assert.match(trace._cursorDetail(trace._metrics,base+11*60000,()=>''),/—/);
const html=trace.shadowRoot.innerHTML;
assert.match(html,/Jetzt lüften/);
console.log('PASS: _refresh end-to-end mocked Recorder unavailable and decision colors');

// COMPLETE(24): Recorder remains readable with a registered but currently
// absent advisor; room discovery retries after HA startup and notices new rooms.
{
  const offline=new ctx.HistoryCard();
  offline._config={entity:'sensor.offline_room',metrics:['co2_in'],hours:24,colors:{}};
  offline._hass={language:'de',states:{},callWS:async({type})=>{
    if(type.endsWith('/history_metrics'))return [{key:'co2_in',source:'sensor.old_co2',unit:'ppm',low:null,high:1000}];
    if(type.endsWith('/history_recommendations'))return {open_now:'Jetzt lüften'};
    if(type.endsWith('/history_room_info'))return {room:'offline',room_name:'Wohnzimmer',enabled:['co2_in','decision'],helpers:{decision:'sensor.offline_decision'}};
    throw Error(type);
  }};
  offline._getHistory=async ids=>ids.map(id=>id==='sensor.old_co2'?[
    {entity_id:id,state:'840',attributes:{unit_of_measurement:'ppm'},last_updated:new Date(Date.now()-120000).toISOString()},
  ]:id==='sensor.offline_decision'?[
    {entity_id:id,state:'open_now',attributes:{room_status:'red'},last_updated:new Date(Date.now()-120000).toISOString()},
  ]:[]);
  await offline._refresh();
  assert.equal(offline._series.get('co2_in')?.[0]?.v,840);
  assert.equal(offline._decisionEvents.length,1);
  assert.match(offline.shadowRoot.innerHTML,/Wohnzimmer/);
  assert.equal(offline._notice,null);
  const e=new ctx.HistoryEditor();e.setConfig({type:'custom:lueftungsberater-history-card'});
  let requests=0,extended=false;
  e.hass={language:'de',states:{},callWS:async({type})=>{
    if(type.endsWith('/history_rooms')){
      if(++requests===1)throw Error('Home Assistant starting');
      const rooms=[{instance_id:'one',instance_name:'Meine Wohnung',room_id:'r',room_name:'Wohnzimmer',entity:'sensor.offline_room',available:false}];
      if(extended)rooms.push({instance_id:'one',instance_name:'Meine Wohnung',room_id:'new',room_name:'Schlafzimmer',entity:'sensor.new_room',available:true});
      return rooms;
    }
    if(type.endsWith('/history_metrics'))return [];
    throw Error(type);
  }};
  await new Promise(r=>setImmediate(r));
  assert.equal(e._roomsRequested,false);
  assert.equal(e._roomsRequestFailed,true);
  e._roomsLastRequest=Date.now()-6000;e._loadRooms();
  await new Promise(r=>setImmediate(r));
  assert.equal(e._rooms.length,1);
  e._loadRooms();assert.equal(requests,2,'do not poll once per HA state');
  extended=true;e._roomsLastRequest=Date.now()-20001;e._loadRooms();
  await new Promise(r=>setImmediate(r));
  assert.equal(e._rooms.length,2);
  assert.match(e.shadowRoot.innerHTML,/Schlafzimmer/);
}
console.log('PASS: recorder without live advisor, room-list WS retry and later room additions');

// COMPLETE(28) Recorder -> display: index and parts scales must survive while
// old incompatible mass values remain gaps, never a continuous false graph.
const variantCard=new ctx.HistoryCard();
const t=Date.now();
const readings=[
  {state:'15',attributes:{unit_of_measurement:'µg/m³'},last_updated:new Date(t-60_000).toISOString()},
  {state:'151',attributes:{unit_of_measurement:'Index'},last_updated:new Date(t).toISOString()},
];
const indexPoints=variantCard._parseHistorySamples(readings,t-120_000,t+1_000,{key:'voc_out',unit:'Index'});
assert.equal(indexPoints[0].v,null,'old mass cannot silently turn into index');
assert.equal(indexPoints[1].v,151,'VOC index is visible on the correct scale');
assert.equal(indexPoints[1].invalidUnit,false);
const no2Points=variantCard._parseHistorySamples([
  {state:'35',attributes:{unit_of_measurement:'ppb'},last_updated:new Date(t).toISOString()},
],t-1000,t+1000,{key:'no2_out',unit:'ppb',high:16});
assert.equal(no2Points[0].v,35);
assert.equal(variantCard._convertHistoryUnit(35,'ppb','µg/m³'),null,'parts must not become mass by guess');
// Unitless direct Recorder readings are only accepted with proven index metadata.
const unitless=[{state:'151',attributes:{},last_updated:new Date(t).toISOString()}];
const rawIndex=variantCard._parseHistorySamples(unitless,t-1000,t+1000,{key:'voc_out',unit:'Index'});
assert.equal(rawIndex[0].v,151,'a proven unitless VOC index must remain visible');
assert.equal(rawIndex[0].rawUnit,'');
const rawMass=variantCard._parseHistorySamples(unitless,t-1000,t+1000,{key:'voc_out',unit:'µg/m³'});
assert.equal(rawMass[0].v,null,'unknown unit must not be interpreted as mass');
const rawCo2=variantCard._parseHistorySamples(unitless,t-1000,t+1000,{key:'co2_in',unit:'Index'});
assert.equal(rawCo2[0].v,null,'unitless arbitrary sensors must not be treated as VOC index');
console.log('PASS: VOC index and NO2 parts are displayed with correct Recorder units');

assert.equal(variantCard._convertHistoryUnit(151,'VOC Index','Index'),151,'ordinal VOC index aliases use one scale');

// COMPLETE(30): unknown-to-unknown units are NOT proof of a common scale.
assert.equal(variantCard._convertHistoryUnit(42,'',''),null,
  'two missing units cannot establish that values are comparable');
const unknownSamples=variantCard._parseHistorySamples([
  {state:'42',attributes:{},last_updated:new Date(t).toISOString()}
],t-1000,t+1000,{key:'voc_out',unit:''});
assert.equal(unknownSamples[0].v,null,'unknown-unit history is a data gap');
assert.equal(unknownSamples[0].invalidUnit,true);
assert.equal(variantCard._convertHistoryUnit(42,'','Index','voc_out'),42,
  'a proven VOC index may still be truly unitless');
console.log('PASS: unknown Recorder units do not silently become comparable');
assert.equal(variantCard._convertHistoryUnit(42,'unknown','unknown'),null,
  'explicitly unknown Recorder unit tokens are not comparable either');

// COMPLETE(31): existing opt-ins must be retried if the platform never created
// their entities. A wrong-unit numeric state cannot block helper activation.
{
 const retry=new ctx.HistoryCard();
 retry._config={entity:'sensor.retryroom',metrics:['co2_in'],hours:24,colors:{}};
 let attempts=0;
 retry._hass={language:'de',user:{is_admin:true},states:{'sensor.retryroom':{entity_id:'sensor.retryroom',state:'open_now',attributes:{room_name:'Wohnzimmer'}}},callWS:async ({type,metrics})=>{
   if(type.endsWith('/history_metrics'))return [{key:'co2_in',source:'sensor.co2_wrong_unit',unit:'ppm',high:1000,low:null}];
   if(type.endsWith('/history_recommendations'))return {};
   if(type.endsWith('/history_room_info'))return {room:'r',enabled:['co2_in','decision'],helpers:{}};
   if(type.endsWith('/history_enable')){attempts++;assert.ok(metrics.includes('co2_in'));return {room:'r',enabled:['co2_in','decision']};}
   throw Error(type);
 }};
 retry._getHistory=async ids=>ids.map(id=>id==='sensor.co2_wrong_unit'?[{
   entity_id:id,state:'43',attributes:{unit_of_measurement:'µg/m³'},last_updated:new Date(Date.now()-60000).toISOString()
 }]:[]);
 await retry._refresh();
 assert.equal(attempts,1,'a wrong-unit numeric state does not count as usable history');
 await retry._refresh();
 assert.equal(attempts,1,'recent submitted registration is debounced');
 retry._enableRequested.set('sensor.retryroom:r:co2_in',Date.now()-91000);
 await retry._refresh();
 assert.equal(attempts,2,'persisted opt-in without a helper must be retryable');
 // Even if HA created a registry row, the corresponding live entity can fail
 // to materialize. After the grace period a privileged card may repair it.
 retry._hass.callWS=async ({type,metrics})=>{
   if(type.endsWith('/history_metrics'))return [{key:'co2_in',source:'sensor.co2_wrong_unit',unit:'ppm',high:1000,low:null}];
   if(type.endsWith('/history_recommendations'))return {};
   if(type.endsWith('/history_room_info'))return {room:'r',enabled:['co2_in','decision'],helpers:{co2_in:'sensor.registered_but_not_live'}};
   if(type.endsWith('/history_enable')){attempts++;return {room:'r',enabled:metrics};}
   throw Error(type);
 };
 retry._helperMissingSince.set('sensor.retryroom:r:co2_in', Date.now()-91000);
 retry._enableRequested.set('sensor.retryroom:r:co2_in', Date.now()-91000);
 await retry._refresh();
 assert.equal(attempts,3,'registered-but-not-live helper can be reconciled');
}

// COMPLETE(32): The last Recorder state immediately before the requested
// window is a known boundary state, unless a later outage invalidated it.
{
  const start=Date.parse('2026-10-13T12:00:00Z');
  const metric={key:'co2_in',unit:'ppm'};
  const row=(delta,state,unit='ppm')=>({
    last_updated:new Date(start+delta).toISOString(),state,
    attributes:{unit_of_measurement:unit},
  });
  const card=new ctx.HistoryCard();
  const steady=card._parseHistorySamples([row(-2000,'740')],start,start+3600000,metric);
  assert.equal(steady.length,1);
  assert.equal(steady[0].v,740);
  assert.equal(steady[0].t,start);
  assert.equal(steady[0].carriedFrom,start-2000);
  const outage=card._parseHistorySamples([row(-60000,'740'),row(-2000,'unavailable')],start,start+3600000,metric);
  assert.equal(outage.length,0,'last pre-window outage must break carry-forward');
  const wrongUnit=card._parseHistorySamples([row(-2000,'740','µg/m³')],start,start+3600000,metric);
  assert.equal(wrongUnit.length,0,'incompatible unit must not become boundary value');
  const restored=card._parseHistorySamples([row(-2000,'unavailable'),row(60000,'760')],start,start+3600000,metric);
  assert.equal(restored.length,1);
  assert.equal(restored[0].t,start+60000);
  console.log('PASS COMPLETE32: Recorder initial-state carry-forward, real outage and unit safety');
}

// A deliberately disabled helper stays readable in Recorder, but must never
// trigger an admin repair call despite an absent current HA state.
{
  const card=new ctx.HistoryCard();
  card._config={entity:'sensor.room',hours:6,metrics:['co2_in'],colors:{}};
  const ws=[];
  card._hass={language:'de',user:{is_admin:true},states:{},callWS:async(msg)=>{
    ws.push(msg.type);
    if(msg.type.endsWith('/history_metrics'))return [{key:'co2_in',source:null,unit:'ppm',high:1000,low:null}];
    if(msg.type.endsWith('/history_recommendations'))return {};
    if(msg.type.endsWith('/history_room_info'))return {
      room:'r',room_name:'Wohnzimmer',enabled:['co2_in','decision'],
      helpers:{co2_in:'sensor.disabled_co2',decision:'sensor.disabled_decision'},
      disabled:['co2_in','decision'],
    };
    throw new Error(`unexpected write ${msg.type}`);
  }};
  card._getHistory=async(ids)=>ids.map(id=>[]);
  await card._refresh();
  assert.ok(!ws.some(x=>x.endsWith('/history_enable')),'disabled helpers must not trigger repair');
  console.log('PASS COMPLETE32: deliberately disabled history entities cause no repair requests');
}

// COMPLETE(35): prefer the durable helper even when a raw sensor still has
// one old valid point, and keep the early raw prefix as its own source era.
{
  const c35=new ctx.HistoryCard();
  const now=Date.now();
  const stamp=offset=>new Date(now+offset).toISOString();
  const recordings={
    'sensor.co2_raw':[{entity_id:'sensor.co2_raw',state:'900',last_updated:stamp(-20*3600000),attributes:{unit_of_measurement:'ppm'}}],
    'sensor.history_co2':[
      {entity_id:'sensor.history_co2',state:'1200',last_updated:stamp(-3600000),attributes:{unit_of_measurement:'ppm'}},
      {entity_id:'sensor.history_co2',state:'1250',last_updated:stamp(-1800000),attributes:{unit_of_measurement:'ppm'}},
    ],
  };
  c35._config={entity:'sensor.room',hours:24,metrics:['co2_in'],perspective:'room_air'};
  c35._hass={language:'de',user:{is_admin:true},states:{
    'sensor.room':{attributes:{room_name:'Room'}},
    'sensor.history_co2':{entity_id:'sensor.history_co2',state:'1250',attributes:{history_room:'r',history_metric:'co2_in'}}
  },callWS:async msg=>{
    if(msg.type.endsWith('/history_metrics'))return [{key:'co2_in',source:'sensor.co2_raw',unit:'ppm',low:null,high:1000}];
    if(msg.type.endsWith('/history_room_info'))return {room:'r',enabled:['co2_in','decision'],helpers:{co2_in:'sensor.history_co2'}};
    if(msg.type.endsWith('/history_recommendations'))return {};
    if(msg.type.endsWith('/history_enable'))throw new Error('No activation needed');
    throw Error(msg.type);
  }};
  c35._getHistory=async ids=>ids.map(id=>recordings[id]??[]);
  await c35._refresh();
  const points=c35._series.get('co2_in')||[];
  assert.equal(JSON.stringify(points.map(p=>p.v)),JSON.stringify([900,1200,1250]),'recent helper Recorder history must not be displaced by one old raw value');
  const plotted=c35._plotSamples(points,now-24*3600000,now);
  assert.equal(plotted.at(-1).v,1250,'last valid state remains visible at the right edge');
}
// COMPLETE(35): raw sources marked for daily purge always need opted-in helper.
{
  const c35=new ctx.HistoryCard();
  c35._config={entity:'sensor.room',hours:24,metrics:['co2_in']};
  let requested=[];
  c35._hass={language:'de',user:{is_admin:true},states:{'sensor.room':{attributes:{room_name:'Room'}}},callWS:async msg=>{
    if(msg.type.endsWith('/history_metrics'))return [{key:'co2_in',source:'sensor.raw',unit:'ppm',helper_required:true}];
    if(msg.type.endsWith('/history_room_info'))return {room:'r',enabled:[],helpers:{}};
    if(msg.type.endsWith('/history_recommendations'))return {};
    if(msg.type.endsWith('/history_enable')){requested=msg.metrics;return {room:'r'};}
    throw Error(msg.type);
  }};
  c35._getHistory=async ids=>ids.map(id=>id==='sensor.raw'?[{entity_id:id,state:'750',last_updated:new Date().toISOString(),attributes:{unit_of_measurement:'ppm'}}]:[]);
  await c35._refresh();
  assert.ok(requested.includes('co2_in'),'transient raw Recorder state must not disable durable helper opt-in');
}
{
  const c35=new ctx.HistoryCard();
  c35._config={entity:'sensor.room',perspective:'room_air'};
  c35._hass={language:'de',states:{}};
  c35._history=[{t:100,kind:'decision',key:'keep_closed',attrs:{safety_lock:true,
    room_status:'green',room_recommendation_key:'room_good',ventilation_recommendation_key:'keep_closed'}}];
  c35._decisionEvents=c35._history;
  assert.equal(c35._historicalDecision(200).key,'keep_closed','safety lock overrides indoor-air advice in history');
  assert.equal(c35._historicalDecision(200).color,'locked');
  const stable=c35._plotSamples([{t:0,v:21},{t:3*3600000,v:22}],0,4*3600000);
  assert.equal(new Set(stable.map(x=>x.segment)).size,1,'no changes for 3h is not an outage');
  assert.equal(stable.at(-1).t,4*3600000,'last state is drawn to the right edge');
  const interrupted=c35._plotSamples([{t:0,v:21},{t:60000,v:null},{t:3*3600000,v:22}],0,4*3600000);
  assert.equal(new Set(interrupted.map(x=>x.segment)).size,2,'explicit unavailable still separates segments');
}
console.log('PASS COMPLETE35: durable helper, purge-aware activation, steady-state duration and locked recommendation');

// COMPLETE(36): A known unavailable state is a real recorded helper event,
// even when its timeline contains no numeric samples. Older raw readings
// cannot conceal the outage or be projected through it.
{
  const start=Date.now()-24*3600000;
  const iso=t=>new Date(t).toISOString();
  const raw=[{entity_id:'sensor.old_co2',state:'900',last_updated:iso(start+4*3600000),attributes:{unit_of_measurement:'ppm'}}];
  const helper=[
    {entity_id:'sensor.helper_co2',state:'unavailable',last_updated:iso(start+22*3600000),attributes:{}},
    {entity_id:'sensor.helper_co2',state:'unavailable',last_updated:iso(start+24*3600000-10000),attributes:{}},
  ];
  const card36=new ctx.HistoryCard();
  card36._config={entity:'sensor.room',metrics:['co2_in'],hours:24,colors:{},perspective:'room_air'};
  card36._hass={language:'de',user:{is_admin:true},states:{
    'sensor.room':{attributes:{room_name:'Room'}},
    'sensor.helper_co2':{entity_id:'sensor.helper_co2',state:'unavailable',attributes:{history_room:'r',history_metric:'co2_in'}},
  },callWS:async msg=>{
    if(msg.type.endsWith('/history_metrics'))return [{key:'co2_in',source:'sensor.old_co2',unit:'ppm'}];
    if(msg.type.endsWith('/history_room_info'))return {room:'r',enabled:['co2_in','decision'],helpers:{co2_in:'sensor.helper_co2'}};
    if(msg.type.endsWith('/history_recommendations'))return {};
    if(msg.type.endsWith('/history_enable'))throw Error('Helper already enabled');
    throw Error(`unexpected websocket call ${msg.type}`);
  }};
  card36._getHistory=async ids=>ids.map(id=>id==='sensor.old_co2'?raw:id==='sensor.helper_co2'?helper:[]);
  await card36._refresh();
  const combined=card36._series.get('co2_in');
  assert.equal(combined[0].v,900,'raw reading predates helper recording');
  assert.equal(combined.at(-1).v,null,'explicit helper outage must survive merging');
  const plotted=card36._plotSamples(combined,start,Date.now());
  assert.ok(plotted.every(p=>p.t<start+22*3600000),
    'old raw CO2 must never be extended through a confirmed helper outage');

  // If helper was unavailable *before* the selected chart window, preserve
  // that recorded outage at the left edge too (not only visible events).
  const left=new ctx.HistoryCard();
  const rows=[{state:'unavailable',last_updated:iso(start-3600000),attributes:{}}];
  const initial=left._parseHistorySamples(rows,start,start+3600000,
    {key:'co2_in',unit:'ppm'},true);
  assert.equal(initial.length,1);
  assert.equal(initial[0].v,null);
  assert.equal(initial[0].t,start);
  console.log('PASS COMPLETE36: helper-only outages and pre-window outage boundaries');
}

// COMPLETE(36): Target/setpoint history is a piecewise constant HA state, not
// a physical temperature ramp. Keep every step through duration filtering.
{
  const start=Date.now()-4*3600000;
  const hour=3600000;
  const card36=new ctx.HistoryCard();
  card36._config={entity:'sensor.room',metrics:['target_temp'],colors:{target_temp:'#123abc'},hours:6};
  card36._metrics=[{key:'target_temp',unit:'°C',low:null,high:25}];
  card36._series=new Map([['target_temp',[{t:start,v:21},{t:start+2*hour,v:22}]]]);
  card36._start=start;card36._end=start+4*hour;card36._cursor=start+hour;
  card36._history=[];
  card36._hass={language:'de',states:{'sensor.room':{attributes:{room_name:'Wohnzimmer'}}}};
  card36._render();
  const path=card36.shadowRoot.innerHTML.match(/<path d="([^"]+)" fill="none" stroke="#123abc"/);
  assert.ok(path,'target curve must be visible');
  const steps=[...path[1].matchAll(/[ML]([\d.]+),([\d.]+)/g)];
  assert.ok(steps.length>=4,`expected horizontal/vertical step commands: ${path[1]}`);
  assert.equal(steps[0][2],steps[1][2],'21°C stays horizontal until the actual state change');
  assert.equal(steps[1][1],steps[2][1],'state jumps vertically at the change timestamp');
  assert.notEqual(steps[1][2],steps[2][2],'22°C must not appear as a gradual ramp');
  const dense=Array.from({length:300},(_,i)=>({t:start+i*20000,v:i<200?21:22}));
  const compressed=card36._plotSamples(dense,start,start+4*hour,10,true);
  assert.ok(compressed.some(p=>p.v===21)&&compressed.some(p=>p.v===22));
  const split=card36._plotSamples([{t:start,v:21},{t:start+hour,v:null},{t:start+3*hour,v:22}],start,start+4*hour,1200,true);
  assert.ok(new Set(split.map(p=>p.segment)).size===2,'actual outage remains a separate segment');
  assert.ok(split.some(p=>p.t===start+hour && p.v===21),'old setpoint ends exactly at the outage');
  console.log('PASS COMPLETE36: true step curve, duration anchors, gap and transition preservation');
}

// COMPLETE(37): a repeated unknown/unavailable report must never extend the
// preceding setpoint beyond the FIRST outage. The cursor and SVG must agree.
{
  const h=3600000,start=Date.now()-4*h;
  const c=new ctx.HistoryCard();
  const values=[{t:start,v:21},{t:start+h,v:null},{t:start+2*h,v:null},{t:start+3*h,v:22}];
  const plotted=c._plotSamples(values,start,start+4*h,1200,true);
  const first=plotted.filter(p=>p.segment===0);
  assert.equal(first.at(-1).t,start+h,'old 21°C plateau must end at first invalid report');
  assert.equal(first.at(-1).v,21);
  assert.ok(!first.some(p=>p.t>start+h),'later unavailable must never extend the old plateau');
  c._config={entity:'sensor.room',metrics:['target_temp'],hours:4,colors:{target_temp:'#123abc'}};
  c._metrics=[{key:'target_temp',unit:'°C',low:null,high:25}];
  c._series=new Map([['target_temp',values]]);
  c._start=start;c._end=start+4*h;c._cursor=start+1.5*h;
  c._hass={language:'de',states:{'sensor.room':{attributes:{room_name:'Room'}}}};
  c._history=[];c._render();
  const drawn=c.shadowRoot.innerHTML.match(/<path d="([^"]+)" fill="none" stroke="#123abc"/);
  assert.ok(drawn,'setpoint SVG should render');
  assert.equal(c._plotSamples(values,start,start+4*h,1200,true).filter(p=>p.segment===0).at(-1).t,start+h);
}

// COMPLETE(37): a 30-day request needs a helper when the integration purges
// a retained 20-day raw timeline; a 24-hour request alone does not.
for(const hours of [24,720]) {
  const c=new ctx.HistoryCard();
  c._config={entity:'sensor.room',hours,metrics:['absolute_in']};
  let requests=[];
  c._hass={language:'de',user:{is_admin:true},states:{'sensor.room':{attributes:{room_name:'Room'}}},callWS:async msg=>{
    if(msg.type.endsWith('/history_metrics'))return [{key:'absolute_in',source:'sensor.absolute',unit:'g/m³',raw_retention_days:20,helper_required:false}];
    if(msg.type.endsWith('/history_room_info'))return {room:'r',enabled:[],helpers:{}};
    if(msg.type.endsWith('/history_recommendations'))return {};
    if(msg.type.endsWith('/history_enable')){requests.push(...msg.metrics);return {room:'r'};}
    throw Error(msg.type);
  }};
  c._getHistory=async ids=>ids.map(id=>id==='sensor.absolute'?[{entity_id:id,state:'9.1',last_updated:new Date().toISOString(),attributes:{unit_of_measurement:'g/m³'}}]:[]);
  await c._refresh();
  assert.equal(requests.includes('absolute_in'),hours===720,
    `helper for 20-day raw absolute humidity at ${hours}h`);
}
console.log('PASS COMPLETE37: repeated outage, setpoint SVG and 20/30-day helper selection');
