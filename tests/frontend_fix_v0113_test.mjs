import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class Stub {
 attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}};return this.shadowRoot;}
 dispatchEvent(){return true;}
}
const RealDate=Date;
const fakeNow='2026-03-29T22:30:00Z'; // 00:30 local on Monday after DST jump
const FakeDate=class extends RealDate {constructor(...a){super(...(a.length?a:[fakeNow]));} static now(){return +new RealDate(fakeNow)}};
const ctx={console,Date:FakeDate,HTMLElement:Stub, customElements:{define(){},get(){return undefined}},
 window:{customCards:[],confirm(){return false},localStorage:{getItem(){return null},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},navigator:{language:'de-DE'},
 document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
 setTimeout,clearTimeout,CustomEvent:class{},Event:class {constructor(){this.detail={}}}};
vm.createContext(ctx);
vm.runInContext(`${source}\nglobalThis.CardClass=LueftungsberaterCard`,ctx);
const Card=ctx.CardClass;
const attrs={status:'green',room_name:'Raum', recommendation:'Alles gut',reason:'Kein Lüftungsbedarf',has_co2:false,
 temperature_inside:22,temperature_outside:18,humidity_inside:51.2,humidity_outside:70,
 source_temperature_inside:'sensor.in',source_temperature_outside:'sensor.out',source_humidity_inside:'sensor.hin',source_humidity_outside:'sensor.hout',
 night_ventilation_status:'unavailable',warning_notice_kind:'all_clear', warning_notice_text:'ALTE-ENTWARNUNG', source_surface_temperature:'sensor.surface',surface_temperature:null,surface_relative_humidity:null,mold_risk:false,mold_persistent:false};
const hass={language:'de',config:{time_zone:'Europe/Berlin',unit_system:{temperature:'°C'}},states:{'sensor.test':{state:'green',attributes:attrs}}};
const classic=new Card();classic.setConfig({entity:'sensor.test',force_expanded:true,display_settings:{layout:'classic',show_reason:false}});classic.hass=hass;
assert.match(classic.shadowRoot.innerHTML,/Temperatur:/);
assert.doesNotMatch(classic.shadowRoot.innerHTML,/class="lb-sides"/);
assert.doesNotMatch(classic.shadowRoot.innerHTML,/Warum diese Empfehlung\?/);
const customized=new Card();customized.setConfig({entity:'sensor.test',force_expanded:true,display_settings:{layout:'classic',hidden:['humidity_in']}});customized.hass=hass;
assert.match(customized.shadowRoot.innerHTML,/lb-classic/);
assert.match(customized.shadowRoot.innerHTML,/Temperatur:/);
assert.doesNotMatch(customized.shadowRoot.innerHTML,/51[.,]2/);
assert.doesNotMatch(customized.shadowRoot.innerHTML,/class="lb-sides"/);
const mold=new Card();mold.setConfig({entity:'sensor.test',force_expanded:true,display_settings:{layout:'split',extra:['mold_risk']}});mold.hass=hass;
assert.match(mold.shadowRoot.innerHTML,/Schimmelrisiko/);
assert.match(mold.shadowRoot.innerHTML,/Nicht bewertbar/);
const remote=new Card();remote.setConfig({force_expanded:true,remote_stale:true,remote_snapshot:{state:'green',attributes:attrs}});remote.hass=hass;
assert.doesNotMatch(remote.shadowRoot.innerHTML,/ALTE-ENTWARNUNG/);
assert.match(remote.shadowRoot.innerHTML,/Verbindung unterbrochen/);
const active=new Card();active.setConfig({entity:'sensor.test',force_expanded:true});active.hass=hass;
assert.match(active.shadowRoot.innerHTML,/ALTE-ENTWARNUNG/);
assert.match(active._airingDateLabel('2026-03-29T10:00:00+02:00'),/Gestern/);
console.log('PASS: 12 added frontend repair assertions');
