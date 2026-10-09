import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js', 'utf8');
class HTMLElementStub {
  attachShadow() {
    this.shadowRoot = {innerHTML:'',querySelector(){return null;},querySelectorAll(){return [];}};
    return this.shadowRoot;
  }
  dispatchEvent() {return true;}
}
const ctx = {
  console, HTMLElement:HTMLElementStub,
  customElements:{define(){},get(){return undefined;}},
  window:{customCards:[],confirm(){return false;},localStorage:{getItem(){return null;},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},
  navigator:{language:'de-DE'},
  document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??'';}}},head:{appendChild(){}}},
  setTimeout,clearTimeout,CustomEvent:class {},Event:class {constructor(){this.detail={}}},
};
vm.createContext(ctx);
vm.runInContext(`${source}\nglobalThis.helpers={lbConfiguredFields,lbFieldVisible,lbDisplaySettings,lbViewEditorHtml,lbBindViewEditor,Card:LueftungsberaterCard,Overview:LueftungsberaterOverviewCard,OverviewEditor:LueftungsberaterOverviewCardEditor,CardEditor:LueftungsberaterCardEditor}`,ctx);
const {lbConfiguredFields,lbFieldVisible,lbViewEditorHtml,lbBindViewEditor,Card,OverviewEditor,Overview,CardEditor} = ctx.helpers;
const hass={language:'de',config:{unit_system:{temperature:'°C'},time_zone:'Europe/Berlin'},states:{}};
const attrs={
  status:'green', recommendation:'Aktuell kein Lüftungsgrund',reason:'Alles in Ordnung.',
  room_name:'Testzimmer',has_co2:true,co2_ppm:null,source_co2:'sensor.co2',
  temperature_inside:21.8,source_temperature_inside:'sensor.indoor_temp',
  humidity_inside:51.2,source_humidity_inside:'sensor.indoor_humidity',
  temperature_outside:null,source_temperature_outside:'sensor.outdoor_temp',
  absolute_humidity_inside:9.1, absolute_humidity_outside:null,
  indoor_air_quality_values:{pm2_5:7.2},source_pm25_inside:'sensor.pm25',
  has_window_contacts:false,
  night_ventilation_status:'unavailable',
};
hass.states['sensor.test']={state:'green',attributes:attrs};
const ids = lbConfiguredFields(attrs).map(f=>f[0]);
assert.ok(ids.includes('co2_in'), 'configured but offline CO2 remains offered');
assert.ok(ids.includes('temp_out'), 'offline but configured outdoor temp remains offered');
assert.ok(ids.includes('pm25_in'), 'configured PM2.5 is shown');
assert.ok(!ids.includes('pm10_in'), 'not configured PM10 is not offered');
assert.ok(!ids.includes('mold_risk'), 'unused optional mold risk is absent');
const markup = lbViewEditorHtml(hass,{display_settings:{layout:'split'}},lbConfiguredFields(attrs),v=>v);
assert.match(markup,/data-lb-layout/);
assert.match(markup,/data-lb-reset/);
assert.doesNotMatch(markup,/data-lb-visible="pm10_in"/);
const card = new Card();
card.setConfig({entity:'sensor.test',force_expanded:true,display_settings:{layout:'split',sides:['outside','inside'],show_reason:false,hidden:['humidity_in']}});
card.hass=hass;
assert.match(card.shadowRoot.innerHTML,/lb-split/);
assert.ok(card.shadowRoot.innerHTML.indexOf('<h4>Außen<\/h4>')<card.shadowRoot.innerHTML.indexOf('<h4>Innen<\/h4>'),'right/left swapping works');
assert.match(card.shadowRoot.innerHTML,/Nicht verfügbar/, 'missing configured readings are indicated');
assert.doesNotMatch(card.shadowRoot.innerHTML,/Relative Feuchte/, 'hidden reading does not appear');
assert.doesNotMatch(card.shadowRoot.innerHTML,/Warum diese Empfehlung\?/, 'reason can be hidden');
assert.match(card.shadowRoot.innerHTML,/CO₂-Sensor nicht verfügbar/,'CO2 special error message remains');
card.setConfig({entity:'sensor.test',force_expanded:true}); card.hass=hass;
assert.match(card.shadowRoot.innerHTML,/Temperatur:/, 'legacy layout remains default');
assert.doesNotMatch(card.shadowRoot.innerHTML,/null[^<]*g\/m³/, 'partial abs humidity never prints null');
const locked = {...attrs, status:'locked', safety_lock:true, reason:'Offizielle Warnung – Fenster geschlossen halten.'};
hass.states['sensor.test']={state:'locked',attributes:locked};
card.setConfig({entity:'sensor.test',force_expanded:true,display_settings:{layout:'split',show_reason:false}});card.hass=hass;
assert.match(card.shadowRoot.innerHTML,/Warum diese Empfehlung\?/, 'hard lock cannot hide safety explanation');
const remoteCard = new Card();
remoteCard.setConfig({force_expanded:true,remote_stale:true,remote_snapshot:{state:'green',attributes:attrs}, display_settings:{layout:'split'}});
remoteCard.hass=hass;
assert.match(remoteCard.shadowRoot.innerHTML,/Verbindung unterbrochen/);
assert.match(remoteCard.shadowRoot.innerHTML,/Letzte bekannte Messwerte/);
const missing=new Card();missing.setConfig({entity:'sensor.missing'}); missing.hass=hass;
assert.match(missing.shadowRoot.innerHTML,/Prüfe die Raumauswahl im Karteneditor/);
const overview = new OverviewEditor();overview._hass=hass;
overview._remoteGroups=[{id:'remote:123',name:'peer',rooms:[{id:'bed',name:'Schlafzimmer',attributes:attrs}]}];
assert.ok(overview._remoteEditorGroups()[0].rooms[0].attributes.has_co2,'remote editor inherits peer capabilities');
// The reset needs confirmation; cancelling must leave configuration untouched.
let handler=null;let didUpdate='untouched';
const resetRoot={querySelector(sel){return sel==='[data-lb-reset]'?{addEventListener(_name,cb){handler=cb}}:null},querySelectorAll(){return []}};
lbBindViewEditor(resetRoot,hass,{display_settings:{layout:'split'}},lbConfiguredFields(attrs),value=>{didUpdate=value});
assert.equal(typeof handler,'function');handler();assert.equal(didUpdate,'untouched');
ctx.window.confirm=()=>true;handler();assert.equal(didUpdate,null,'confirmed reset clears display only');
// New card setup automatically selects the only locally configured room.
const single = new CardEditor();
single._config = {};
single._hass = { ...hass, states:{'sensor.only':{entity_id:'sensor.only',state:'green',attributes:{...attrs,mode:'ok',reason:'Alles gut.'}}} };
single._render();
assert.equal(single._config.entity,'sensor.only');
// A disconnected peer must not automatically dismiss the open room dialog.
const remoteOverview = new Overview();remoteOverview._hass = hass;
remoteOverview._dialogMode = 'room';
remoteOverview._openRoomRef = {remote:true,groupId:'remote:gone',roomKey:'x'};
remoteOverview._popupCard = {_config:{remote_snapshot:{state:'green',attributes:attrs}},setConfig(next){this._config=next},set hass(next) {this._hass=next}};
remoteOverview._remoteGroups=[];
remoteOverview._refreshRemoteDialog();
assert.equal(remoteOverview._dialogMode,'room');
assert.equal(remoteOverview._popupCard._config.remote_stale,true);
console.log('PASS: 21 frontend QoL checks for v0.11.3');
