import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js', 'utf8');
class Stub {
  attachShadow() { this.shadowRoot = {innerHTML:'', querySelector(){return null}, querySelectorAll(){return []}}; return this.shadowRoot; }
  dispatchEvent() { return true; }
}
const ctx = {console, HTMLElement:Stub, customElements:{get(){}, define(){}},
  window:{customCards:[],location:{pathname:'/'},addEventListener(){},removeEventListener(){},localStorage:{getItem(){return null},setItem(){}}},
  navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
  setTimeout,clearTimeout,setInterval,clearInterval,Event:class{},CustomEvent:class{}};
vm.createContext(ctx);
vm.runInContext(source+'\nglobalThis.Room=LueftungsberaterCard;globalThis.Overview=LueftungsberaterOverviewCard;globalThis.History=LueftungsberaterHistoryCard;globalThis.perspectiveStatus=lbPerspectiveStatus;',ctx);
// The room-facing colour expresses an action, while the ventilation colour
// expresses the suitability of outside conditions. They MUST remain distinct.
for (const Card of [ctx.Room, ctx.Overview]) {
  const card = new Card();
  assert.match(card._statusMeta('green', 'room_air').icon, /check-circle/);
  assert.match(card._statusMeta('orange', 'room_air').icon, /alert/);
  assert.match(card._statusMeta('green', 'ventilation').icon, /window-open/);
  assert.match(card._statusMeta('orange', 'ventilation').icon, /window-closed/);
  assert.equal(card._statusMeta('locked','ventilation').icon,'mdi:lock');
  assert.equal(card._statusMeta('unknown','room_air').icon,'mdi:help-circle-outline');
}
for (const mode of ['room_air','ventilation']) {
  const attrs={display_mode:mode,status:'green',room_status:'green',
    ventilation_status:'orange',room_recommendation_key:'better_close',
    ventilation_recommendation_key:'better_close'};
  assert.equal(ctx.perspectiveStatus(attrs),mode==='room_air'?'green':'orange');
}
// A v0.12.0 COMPLETE(15) remote snapshot stored its native suitability here.
assert.equal(ctx.perspectiveStatus({display_mode:'ventilation',status:'green',
  action_semantics_version:1,ventilation_status:'green',
  ventilation_suitability_status:'red'}),'red');
assert.equal(ctx.perspectiveStatus({display_mode:'room_air',status:'orange',
  room_status:'orange',ventilation_status:'green'}),'orange');
assert.equal(ctx.perspectiveStatus({display_mode:'ventilation',status:'locked',
  ventilation_status:'green',safety_lock:true}),'locked');
const history=new ctx.History();
const date=Date.parse('2026-11-05T10:00:00Z');
history._start=date;history._end=date+300000;
history._hass={language:'de',states:{'sensor.test':{attributes:{display_mode:'ventilation'}}}};
history._config={entity:'sensor.test'};
history._history=[{t:date,kind:'decision',key:'better_close',attrs:{
  display_mode:'room_air',room_status:'yellow',ventilation_status:'orange',
  room_recommendation_key:'better_close',ventilation_recommendation_key:'better_close'}}];
history._decisionEvents=history._history;
assert.equal(history._historicalDecision(date+1000).color,'yellow',
  'historic room colour must not be repainted green by current action semantics');
assert.equal(history._historicalDecision(date+1000).key,'better_close');
history._history=[{t:date,kind:'decision',key:'open_now',attrs:{
  display_mode:'ventilation',room_status:'green',ventilation_status:'green',
  room_recommendation_key:'can_close',ventilation_recommendation_key:'open_now'}}];
history._decisionEvents=history._history;
assert.equal(history._historicalDecision(date+1000).color,'green',
  'historic green ventilation means the outside air was suitable');
assert.equal(history._historicalDecision(date+1000).key,'open_now');
history._history=[{t:date,kind:'decision',key:'open_now',attrs:{
  display_mode:'ventilation',room_status:'green',ventilation_status:'green',
  ventilation_suitability_status:'orange',action_semantics_version:1}}];
history._decisionEvents=history._history;
assert.equal(history._historicalDecision(date+1000).color,'orange',
  'recover the archived suitability from the COMPLETE(15) compatibility field');
const overview = new ctx.Overview();
overview._hass = { language: 'de', states: {} };
overview._config = {};
for (const mode of ['room_air', 'ventilation']) {
  const attrs = { display_mode: mode, room_status: 'green', ventilation_status: 'red',
    status: mode === 'room_air' ? 'green' : 'red', room_name: 'Wohnung',
    recommendation: 'Auswertung', mode: 'test' };
  const local = overview._roomFromLocal({entity_id:'sensor.room',state:'open_now',attributes:attrs},0);
  const remote = overview._remoteRoom({id:'remote-1'}, {id:'room-1',name:'Wohnung',
    state:'open_now',attributes:attrs},0);
  for (const entry of [local, remote]) {
    assert.equal(entry.status,mode === 'room_air' ? 'green' : 'red');
    assert.equal(entry.icon,mode === 'room_air' ? 'mdi:check-circle-outline' : 'mdi:window-closed-variant');
  }
}
// A missing OPTIONAL window contact appears as yellow warning text; it is not
// allowed to recolour an otherwise orange room.
const roomCard = new ctx.Room();
roomCard._hass={language:'de',config:{unit_system:{temperature:'°C'}}};
const metrics=roomCard._metricItems({window_data_status:'unavailable',has_window_contacts:true},'°C');
assert.match(String(metrics.window_state),/lb-missing/);
console.log('PASS: dual perspectives, overview, remote, missing-contact hint and Recorder');
