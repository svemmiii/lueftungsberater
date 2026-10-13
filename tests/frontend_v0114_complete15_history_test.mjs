import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class HTML {attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}};return this.shadowRoot;}dispatchEvent(){}}
const ctx={console,HTMLElement:HTML,customElements:{get(){},define(){}},window:{customCards:[],confirm(){},localStorage:{getItem(){return null},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},setTimeout,clearTimeout,setInterval,clearInterval,Event:class {},CustomEvent:class {}};
vm.createContext(ctx);vm.runInContext(`${source}\nglobalThis.HistoryCard=LueftungsberaterHistoryCard`,ctx);
const c=new ctx.HistoryCard();
c._config={entity:'sensor.room',metrics:['co2_out']};
const readings=Array.from({length:200000},(_,i)=>({t:i*1000,v:i===115000?10000:400+(i%150)}));
const axis=c._axis({high:1000,low:null},readings.map(p=>p.v));
assert.ok(Number.isFinite(axis.y(10000)));
const simplified=c._plotSamples(readings,0,200000000,1200);
assert.ok(simplified.length<=1200, 'rendered SVG samples should be capped');
assert.ok(simplified.some(p=>p.v===10000), 'brief extreme readings must be preserved');
assert.equal(readings.length,200000,'raw cursor samples must be retained');
let adminCalls=0;
c._metrics=[];
c._getHistory=async ids=>ids.map(id=>[{entity_id:id,state:'430',last_updated:new Date(Date.now()-1000).toISOString()}]);
c._hass={language:'de',states:{'sensor.room':{attributes:{room_name:'Wohnung'}},'sensor.existing_helper':{attributes:{history_room:'r',history_metric:'co2_out'}}},callWS:async request=>{
  if(request.type.endsWith('/history_metrics'))return [{key:'co2_out',source:'cams_air_quality_model',high:1000,low:null,unit:'ppm'}];
  if(request.type.endsWith('/history_recommendations'))return {};
  if(request.type.endsWith('/history_room_info'))return {room:'r',enabled:['co2_out','decision'],helpers:{co2_out:'sensor.existing_helper'}};
  if(request.type.endsWith('/history_enable')){adminCalls++;throw new Error('non-admin');}
  throw Error(request.type);
}};
await c._refresh();
assert.equal(adminCalls,0,'existing history can be viewed without requesting admin activation');
assert.equal(c._roomId,'r');
assert.equal(c._series.get('co2_out').length,1);
console.log('PASS: 200k points, spike retention, existing non-admin history');
