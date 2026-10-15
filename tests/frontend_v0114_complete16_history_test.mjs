import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class HTML {attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}};return this.shadowRoot;}dispatchEvent(){}}
const ctx={console,HTMLElement:HTML,customElements:{get(){},define(){}},window:{customCards:[],confirm(){},localStorage:{getItem(){return null},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},setTimeout,clearTimeout,setInterval,clearInterval,Event:class{},CustomEvent:class{}};
vm.createContext(ctx);
vm.runInContext(`${source}\nglobalThis.HistoryCard=LueftungsberaterHistoryCard`,ctx);
const C=ctx.HistoryCard;
const c=new C();c._config={entity:'sensor.r1',hours:720,metrics:['co2_in']};
// 30 days of uninterrupted measurements must NOT inherit 354 fake gaps.
for(const minutes of [5,10,15,30]){
  const step=minutes*60_000;
  const raw=Array.from({length:Math.round(30*24*60/minutes)+1},(_,i)=>({t:i*step,v:500}));
  const sampled=c._plotSamples(raw,0,30*24*3600_000,1200);
  assert.equal(new Set(sampled.map(p=>p.segment)).size,1,`${minutes}min series must remain continuous`);
  assert.ok(sampled.length<=1200);
}
const gap=[...Array.from({length:300},(_,i)=>({t:i*300_000,v:500})),...Array.from({length:300},(_,i)=>({t:(i+330)*300_000,v:500}))];
const sampled=c._plotSamples(gap,0,gap.at(-1).t,100);
assert.equal(new Set(sampled.map(p=>p.segment)).size,1,'a long interval with no state changes is not proof of an outage');
// Event strip must be cached across cursor changes and compressed to pixels.
c._start=0;c._end=40_000_000;
c._history=Array.from({length:40000},(_,i)=>({t:i*1000,kind:'decision',key:'open_now',attrs:{room_status:i%2?'red':'green'}}));
c._decisionEvents=c._history;
c._hass={language:'de',states:{'sensor.r1':{attributes:{room_name:'Room1'}}}};
const first=c._statusStrips(70,950);const cached=c._stripCache;
assert.ok(first.includes('<rect'));assert.ok((first.match(/<rect/g)||[]).length<=880);
assert.equal(c._statusStrips(70,950),first);assert.equal(c._stripCache,cached);
// Requests are scoped to room IDs (A -> B -> A cannot hide B's opt-in).
let activations=[];
c._metrics=[];
c._history=[];
c._config={entity:'sensor.r1',hours:24,metrics:['co2_out']};
c._hass={language:'de',states:{'sensor.r1':{attributes:{room_name:'Room1'}},'sensor.r2':{attributes:{room_name:'Room2'}}},callWS:async msg=>{
 if(msg.type.endsWith('/history_metrics'))return [{key:'co2_out',source:'unrecorded_model',high:1000,low:null,unit:'ppm'}];
 if(msg.type.endsWith('/history_recommendations'))return {};
 if(msg.type.endsWith('/history_room_info'))return {room:msg.entity.endsWith('r1')?'room1':'room2',enabled:[],helpers:{}};
 if(msg.type.endsWith('/history_enable')){activations.push(msg.entity);return {room:msg.entity.endsWith('r1')?'room1':'room2'};}
 throw Error(msg.type);
}};
c._getHistory=async ids=>ids.map(id=>[{entity_id:id,state:'not-a-number',last_updated:new Date().toISOString()}]);
await c._refresh();c._config.entity='sensor.r2';await c._refresh();c._config.entity='sensor.r1';await c._refresh();
assert.deepEqual(activations,['sensor.r1','sensor.r2']);
// v0.11.5: direct touch pointer capture, natural vertical page scroll, no scrubber.
assert.match(source,/touch-action:pan-y;user-select:none;cursor:crosshair/);
assert.match(source,/setPointerCapture/);
assert.doesNotMatch(source,/data-cursor-scrubber/);
// Full initial fetch followed by a small incremental window, not 30 days again.
const h=new C();h._config={entity:'sensor.r1',hours:720};
const requests=[];
h._hass={callApi:async(type,url)=>{requests.push(url);const matches=/filter_entity_id=([^&]+)/.exec(url);const entity=decodeURIComponent(matches[1]);return [[{entity_id:entity,state:'432',last_changed:new Date(Date.now()-120_000).toISOString()}]]}};
const now=Date.now(),start=new Date(now-30*86400_000);
await h._getHistory(['sensor.ppm'],start,new Date(now));
await h._getHistory(['sensor.ppm'],new Date(start.getTime()+60_000),new Date(now+60_000));
assert.equal(requests.length,2);
assert.ok(requests.every(url=>url.includes('significant_changes_only=0')), 'attribute-only decision transitions must be returned by HA REST');
const secondStart=Date.parse(decodeURIComponent(requests[1].split('history/period/')[1].split('?')[0]));
assert.ok(secondStart>now-10*60_000,'incremental fetch must start close to last fetch');
console.log('PASS: gap fidelity, decision cache/40k events, multi-room, mobile gestures and incremental Recorder');

// A bounded background recovery failure must be visible, not endlessly retried.
const failedCard=new C();
failedCard._config={entity:'sensor.r1',hours:24,metrics:['co2_in']};
let failedCardWrites=0;
failedCard._hass={language:'de',user:{is_admin:true},states:{'sensor.r1':{attributes:{room_name:'Raum'}}},callWS:async msg=>{
 if(msg.type.endsWith('/history_metrics'))return [{key:'co2_in',source:null,unit:'ppm',high:1000,low:null}];
 if(msg.type.endsWith('/history_recommendations'))return {};
 if(msg.type.endsWith('/history_room_info'))return {room:'r',room_name:'Raum',enabled:['co2_in','decision'],helpers:{},failed:['co2_in','decision'],failure_reason:'helpers_missing'};
 if(msg.type.endsWith('/history_enable')){failedCardWrites++;return {room:'r'};}
 throw Error(msg.type);
}};
failedCard._getHistory=async ids=>[];
await failedCard._refresh();
assert.equal(failedCardWrites,0,'exhausted retries must not spam history_enable');
assert.match(failedCard._notice,/fehlgeschlagen/,'card must display the exhausted retry status');

// COMPLETE(34): terminal repair errors must be actionable by an admin, never
// automatically retried, and a read-only damaged Store must block writes.
assert.match(failedCard.shadowRoot.innerHTML,/data-history-retry/);
await failedCard._retryHistoryRecording();
assert.equal(failedCardWrites,1,'explicit admin click may send exactly one retry');
const ordinaryReader=new C();
ordinaryReader._config={entity:'sensor.r1',hours:24,metrics:['co2_in']};
let readerWrites=0;
ordinaryReader._hass={language:'de',user:{is_admin:false},states:{'sensor.r1':{attributes:{room_name:'R'}}},callWS:async msg=>{
 if(msg.type.endsWith('/history_metrics'))return [{key:'co2_in',source:null,unit:'ppm'}];
 if(msg.type.endsWith('/history_recommendations'))return {};
 if(msg.type.endsWith('/history_room_info'))return {room:'r',enabled:['co2_in'],failed:['co2_in'],failure_reason:'registry_unavailable'};
 if(msg.type.endsWith('/history_enable')){readerWrites++;throw Error('forbidden');}
}};
ordinaryReader._getHistory=async()=>[];
await ordinaryReader._refresh();
assert.equal(readerWrites,0);
assert.match(ordinaryReader._notice,/konnte nicht überprüft werden/);
assert.doesNotMatch(ordinaryReader.shadowRoot.innerHTML,/data-history-retry/);

const protectedCard=new C();
protectedCard._config={entity:'sensor.r1',hours:24,metrics:['co2_in']};
let protectedWrites=0;
protectedCard._hass={language:'de',user:{is_admin:true},states:{'sensor.r1':{attributes:{room_name:'R'}}},callWS:async msg=>{
 if(msg.type.endsWith('/history_metrics'))return [{key:'co2_in',source:null,unit:'ppm'}];
 if(msg.type.endsWith('/history_recommendations'))return {};
 if(msg.type.endsWith('/history_room_info'))return {room:'r',enabled:['co2_in'],helpers:{},failed:[],history_store_readonly:true};
 if(msg.type.endsWith('/history_enable')){protectedWrites++;throw Error('must not write');}
}};
protectedCard._getHistory=async()=>[];
await protectedCard._refresh();
assert.equal(protectedWrites,0);
assert.match(protectedCard._notice,/schreibgeschützt/);
assert.doesNotMatch(protectedCard.shadowRoot.innerHTML,/data-history-retry/);
console.log('PASS: manual admin recovery, unavailable registry and protected history storage');
