import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js', 'utf8');
const timers = new Map();
let nextTimer = 1;
class Stub {
  isConnected = false;
  attachShadow() { this.shadowRoot = {innerHTML:'', querySelector(){return null},querySelectorAll(){return []}}; return this.shadowRoot; }
  dispatchEvent() { return true; }
}
const context = {
  console, HTMLElement:Stub, customElements:{get(){return undefined},define(){}},
  window:{customCards:[], location:{pathname:'/'}, addEventListener(){}, removeEventListener(){}, localStorage:{getItem(){return null},setItem(){}}},
  navigator:{language:'de'},
  document:{documentElement:{lang:'de'}, createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}}, head:{appendChild(){}}},
  setInterval(fn, delay) { const n=nextTimer++; timers.set(n, {fn,delay}); return n; },
  clearInterval(id) { timers.delete(id); },
  setTimeout, clearTimeout, Promise, Event:class{constructor(){this.detail={}}}, CustomEvent:class{},
};
vm.createContext(context);
vm.runInContext(`${source}\nglobalThis.Overview = LueftungsberaterOverviewCard; globalThis.Editor = LueftungsberaterOverviewCardEditor;`, context);
const flush = async () => { for (let i=0; i<8; i++) await Promise.resolve(); };

for (const [name, Card] of [['Overview',context.Overview],['Editor',context.Editor]]) {
  const before=timers.size;
  let result=[];
  let wsCalls=0;
  let subscribeCalls=0;
  let cancelCalls=0;
  let events;
  let rendering=0;
  const connection={subscribeMessage(callback, message) {
    assert.equal(message.type,'config_entries/subscribe');
    events=callback;
    subscribeCalls++;
    return Promise.resolve(() => { cancelCalls++; });
  }};
  const hass={language:'de',states:{},connection,callWS:async msg=>{
    assert.equal(msg.type,'lueftungsberater/remote_overview');
    wsCalls++;
    return result;
  }};
  const card=new Card();
  if (name==='Overview') {
    card._ensureShell=()=>{};
    card._renderOverview=()=>{rendering++};
    card._refreshRemoteDialog=()=>{};
  } else {
    card._requestRender=()=>{rendering++};
  }
  card._hass=hass;
  card._config={};
  card.isConnected=true;
  card.connectedCallback();
  await flush();
  assert.equal(wsCalls,1, `${name}: initial remote detection`);
  assert.equal(timers.size,before, `${name}: no timer for local-only`);
  assert.equal(subscribeCalls,1,`${name}: event subscription`);
  events([{type:'updated',entry:{domain:'sun'}}]);
  await flush();
  assert.equal(wsCalls,1,`${name}: unrelated config event ignored`);
  result=[{id:'remote:abc',name:'Remote',available:true,rooms:[{id:'r',name:'Raum',state:'green',attributes:{}}]}];
  events([{type:'added',entry:{domain:'lueftungsberater'}}]);
  await flush();
  assert.equal(wsCalls,2,`${name}: newly added remote discovered`);
  assert.equal(timers.size,before+1,`${name}: timer started only for real remote`);
  const id=card._remoteTimer;
  await timers.get(id).fn();
  await flush();
  assert.equal(wsCalls,3,`${name}: remote polling runs`);
  result=[{id:'remote:abc',name:'Remote',available:false,rooms:[]}];
  await timers.get(id).fn();
  await flush();
  assert.equal(timers.size,before+1,`${name}: short remote outage retains polling`);
  assert.equal(card._remoteGroups.length,1);
  result=[];
  events([{type:'removed',entry:{domain:'lueftungsberater'}}]);
  await flush();
  assert.equal(timers.size,before,`${name}: timer stops after removal`);
  // Unrelated HA entities may change frequently without requiring a new
  // remote snapshot or needless overview/editor rendering.
  card.hass = hass; // Warm up the normal local-state signature.
  await flush();
  const beforeUnrelatedRender = rendering;
  const beforeUnrelatedCalls = wsCalls;
  const unrelatedStates = Object.fromEntries(Array.from({length:3000}, (_, i) =>
    [`sensor.other_${i}`, {entity_id:`sensor.other_${i}`,state:String(i),attributes:{friendly_name:'Other'}}]));
  card.hass = {...hass, states:unrelatedStates};
  await flush();
  assert.equal(wsCalls, beforeUnrelatedCalls, `${name}: irrelevant HA state updates do not poll`);
  assert.equal(rendering, beforeUnrelatedRender, `${name}: irrelevant HA states do not rerender`);
  const callsBeforeDisconnect=wsCalls;
  card.isConnected=false;
  card.disconnectedCallback();
  assert.equal(cancelCalls,1,`${name}: websocket subscription released`);
  events([{type:'added',entry:{domain:'lueftungsberater'}}]);
  await flush();
  assert.equal(wsCalls,callsBeforeDisconnect,`${name}: no fetch after detach`);
  assert.equal(timers.size,before,`${name}: no leaked timer`);
  assert.ok(rendering>=0);
}
console.log('PASS: v0.12.0 local/remote overview + editor (on-demand, new peers, outages, removal, cleanup)');
