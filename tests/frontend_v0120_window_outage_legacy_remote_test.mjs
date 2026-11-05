import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class Stub {
  attachShadow() {
    this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}};
    return this.shadowRoot;
  }
  dispatchEvent(){return true;}
}
const ctx={console,HTMLElement:Stub, customElements:{get(){},define(){}},
  window:{customCards:[],location:{pathname:'/'},addEventListener(){},removeEventListener(){},localStorage:{getItem(){return null},setItem(){}}},
  navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
  setTimeout,clearTimeout,setInterval,clearInterval,Event:class{},CustomEvent:class{}};
vm.createContext(ctx);
vm.runInContext(source+'\nglobalThis.Room=LueftungsberaterCard;globalThis.Overview=LueftungsberaterOverviewCard;globalThis.perspectiveStatus=lbPerspectiveStatus;',ctx);
const hass={language:'de',states:{},config:{unit_system:{temperature:'°C'}, time_zone:'Europe/Berlin'}};
function makeRoom(attributes,config={}) {
  const room=new ctx.Room();
  room._hass=hass;
  room._config={entity:'sensor.test',force_expanded:true, ...config};
  room._renderSignature=null;
  const state={state:'open_now',attributes:{room_name:'Wohnzimmer',display_mode:'room_air',room_status:'orange',
    ventilation_status:'green',status:'orange',recommendation:'Weiter lüften',has_window_contacts:true,
    window_open:false,window_data_status:'unavailable',...attributes}};
  if(config.remote_snapshot) room._config.remote_snapshot=state;
  else hass.states['sensor.test']=state;
  room._render();
  return room.shadowRoot.innerHTML;
}
const missing=makeRoom({window_data_status:'unavailable',last_confirmed_airing:'2026-11-01T15:00:00Z'});
assert.match(missing,/Fensterzustand derzeit nicht verfügbar/);
assert.match(missing,/fact data-warning/);
assert.doesNotMatch(missing,/Letzte bestätigte Lüftung/);
assert.doesNotMatch(missing,/Fenster\/Tür gerade offen/);
for(const value of ['grace','unknown']) {
  const html=makeRoom({window_data_status:value,window_open:true});
  assert.match(html,/Fensterzustand derzeit nicht verfügbar/);
  assert.doesNotMatch(html,/Fenster\/Tür gerade offen/);
}
const custom=makeRoom({window_data_status:'unavailable'},
  {display_settings:{layout:'split',hidden:['window_state']}});
assert.match(custom,/Fensterzustand derzeit nicht verfügbar/);
assert.match(custom,/fact data-warning/);
const healthy=makeRoom({window_data_status:'current',window_open:false,last_confirmed_airing:'2026-11-01T15:00:00Z'});
assert.doesNotMatch(healthy,/Fensterzustand derzeit nicht verfügbar/);
const absent=makeRoom({has_window_contacts:false,window_data_status:'not_configured'});
assert.doesNotMatch(absent,/Fensterzustand derzeit nicht verfügbar/);

const legacy=makeRoom({display_mode:'ventilation',action_semantics_version:1,
  status:'green',room_status:'green',ventilation_status:'green',
  ventilation_suitability_status:'green',native_ventilation_recommendation_key:'open_now',
  recommendation_key:'keep_closed',recommendation:'Fenster geschlossen lassen'},
  {remote_snapshot:true});
assert.match(legacy,/mdi:window-open-variant/);
assert.match(legacy,/>Jetzt lüften</);
assert.doesNotMatch(legacy,/>Fenster geschlossen lassen</);
const modern=makeRoom({display_mode:'ventilation',perspective_semantics_version:2,
  status:'green',ventilation_status:'green',recommendation_key:'wait',
  recommendation:'Warten empfohlen'}, {remote_snapshot:true});
assert.match(modern,/>Warten empfohlen</);
const olderRoom=makeRoom({display_mode:'room_air',action_semantics_version:1,
  recommendation:'Geschlossen lassen', native_ventilation_recommendation_key:'open_now',
  status:'green',room_status:'green'}, {remote_snapshot:true});
assert.match(olderRoom,/>Geschlossen lassen</);
assert.doesNotMatch(olderRoom,/>Jetzt lüften</);
// The compact overview and the detail dialog must agree for legacy remotes.
const overview=new ctx.Overview();
overview._hass=hass;
overview._config={};
const legacyAttrs={display_mode:'ventilation',action_semantics_version:1,
  status:'green',room_status:'green',ventilation_status:'green',
  ventilation_suitability_status:'green',
  native_ventilation_recommendation_key:'open_now',
  recommendation:'Fenster geschlossen lassen',recommendation_key:'keep_closed',
  window_open:true,window_data_status:'unavailable'};
const remoteRow=overview._remoteRoom({id:'remote-house'},
  {id:'r1',name:'Schlafzimmer',state:'keep_closed',attributes:legacyAttrs},0);
assert.equal(remoteRow.status,'green');
assert.match(remoteRow.icon,/window-open/);
assert.equal(remoteRow.recommendation,'Jetzt lüften');
assert.equal(remoteRow.windowOpen,false,'unknown contact cannot prove physical open');
const recentRow=overview._remoteRoom({id:'remote-house'},
  {id:'r2',name:'Schlafzimmer',state:'open_now',attributes:{...legacyAttrs,
    action_semantics_version:undefined,perspective_semantics_version:2,
    ventilation_status:'orange',recommendation:'Warten empfohlen'}},1);
assert.equal(recentRow.recommendation,'Warten empfohlen');
assert.equal(recentRow.status,'orange');
console.log('PASS: classic/custom contact outage, grace, absent contact, legacy & modern remote');
