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
