import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class Stub {
 attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null;},querySelectorAll(){return [];}};return this.shadowRoot;}
 dispatchEvent(){return true;}
}
const ctx={console,HTMLElement:Stub,customElements:{get(){},define(){}},
 window:{customCards:[],location:{pathname:'/'},localStorage:{getItem(){return null},setItem(){}},addEventListener(){},removeEventListener(){}},
 navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value||''}}},head:{appendChild(){}}},
 setTimeout(){return 1},clearTimeout(){},setInterval(){return 1},clearInterval(){},CustomEvent:class{},Event:class{}};
vm.createContext(ctx);vm.runInContext(source+'\nglobalThis.Card=LueftungsberaterHistoryCard;',ctx);
const Card=ctx.Card;
const start=100000,end=200000;
const keys=['co2_in','co2_out','temp_in','temp_out','humidity_in','humidity_out','target_temp','pm25_in'];
const units={co2_in:'ppm',co2_out:'ppm',temp_in:'°C',temp_out:'°C',humidity_in:'%',humidity_out:'%',target_temp:'°C',pm25_in:'µg/m³'};
const limits={co2_in:{high:1000},temp_in:{low:18,high:25},temp_out:{high:24},humidity_in:{low:40,high:65},pm25_in:{high:15}};
function make(chosen=keys){
 const c=new Card();c._config={entity:'sensor.room',hours:6,metrics:chosen,colors:{}};
 c._metrics=chosen.map(key=>({key,unit:units[key],low:limits[key]?.low??null,high:limits[key]?.high??null}));
 const readings={co2_in:[900,1100],co2_out:[450,460],temp_in:[21,22],temp_out:[23,28],humidity_in:[61,68],humidity_out:[70,72],target_temp:[22,22],pm25_in:[8,20]};
 c._series=new Map(chosen.map(key=>[key,[{t:start,v:readings[key][0]},{t:end,v:readings[key][1]}]]));
 c._start=start;c._end=end;c._cursor=end;c._history=[{t:start,kind:'decision',key:'room_good',attrs:{room_status:'green',room_recommendation_key:'room_good'}}];c._decisionEvents=c._history;c._advisorEvents=[];
 c._hass={language:'de',states:{'sensor.room':{state:'open_now',attributes:{room_name:'Wohnzimmer',display_mode:'room_air'}}}};
 c.getBoundingClientRect=()=>({width:390});return c;
}
const c=make();c._render();let html=c.shadowRoot.innerHTML;
assert.deepEqual([...html.matchAll(/data-history-focus="([^"]*)"/g)].map(match=>match[1]),['','co2','temp','humidity','pm25']);
assert.equal(c._color('co2_in',0),c._color('co2_out',1));
assert.equal(c._color('humidity_in',4),c._color('humidity_out',5));
assert.equal(c._color('temp_in',2),c._color('temp_out',3));
assert.match(html,/data-history-curve="co2_out"[^>]*>[^<]*<path[^>]+stroke-dasharray="6 4"/);
assert.match(html,/data-history-curve="temp_out"[^>]*>[\s\S]*?stroke="#df1717"[^>]+stroke-dasharray="6 4"/);
assert.match(html,/data-history-curve="target_temp"[^>]*>[\s\S]*?stroke-dasharray="2 4"/);
assert.equal((html.match(/data-instrument-lane=/g)||[]).length,4,'one compact indoor limit instrument per bounded family');
assert.doesNotMatch(html,/data-axis-zone="(?:co2_out|temp_out|humidity_out)"/,'outdoors have no visual limit instrument');
assert.match(html,/data-axis-marker="co2_in"/);
assert.doesNotMatch(html,/data-axis-marker="co2_out"/);
assert.match(html,/data-room-status-row/);
assert.equal((html.match(/class="reading"/g)||[]).length,8,'one shared reading per selected curve');
c._focusFamily='pm25';c._render();html=c.shadowRoot.innerHTML;
assert.match(html,/data-history-curve="pm25_in" opacity="1"/);
assert.match(html,/data-history-curve="co2_in" opacity=".12"/);
assert.equal((html.match(/class="reading"/g)||[]).length,8,'focus does not dim or hide numeric readings');
c._focusFamily='humidity';c._render();html=c.shadowRoot.innerHTML;
assert.match(html,/data-history-curve="humidity_in" opacity="1"/);
assert.match(html,/data-history-curve="humidity_out" opacity="1"/);
assert.match(html,/data-history-curve="temp_in" opacity=".12"/);
c._config.colors={co2_out:'#778899'};
assert.notEqual(c._color('co2_in',0),c._color('co2_out',1),'user override detaches only outdoor member');
const live=c._render();
const markerY=(html,key)=>Number(html.match(new RegExp(`data-axis-marker="${key}"[^>]*cy="([0-9.]+)"`))?.[1]);
c._cursor=start;c._render();const olderY=markerY(c.shadowRoot.innerHTML,'co2_in');
c._cursor=end;c._render();const newerY=markerY(c.shadowRoot.innerHTML,'co2_in');
assert.ok(Number.isFinite(olderY)&&Number.isFinite(newerY)&&newerY<olderY,'white instrument marker follows historical value');
const noPM=make(keys.filter(key=>key!=='pm25_in'));noPM._render();
assert.doesNotMatch(noPM.shadowRoot.innerHTML,/data-history-focus="pm25"/,'unconfigured curve groups are absent from toolbar');
const onlyOutdoor=make(['co2_out']);onlyOutdoor._render();
assert.equal((onlyOutdoor.shadowRoot.innerHTML.match(/data-instrument-lane=/g)||[]).length,0,'outside-only measurement has no side instrument');
console.log('PASS COMPLETE4: paired colors, split override, dynamic focus, inside-only instrument, outdoor red dashes, synchronized markers');
