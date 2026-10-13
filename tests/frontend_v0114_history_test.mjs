import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class HTMLElementStub {
  attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null},querySelectorAll(){return []}};return this.shadowRoot;}
  dispatchEvent() {return true;}
}
const ctx={console,HTMLElement:HTMLElementStub,customElements:{get(){},define(){}},
window:{customCards:[],confirm(){return false},localStorage:{getItem(){return null},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},
navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
setTimeout,clearTimeout,setInterval,clearInterval,CustomEvent:class{},Event:class {constructor(){this.detail={}}}};
vm.createContext(ctx);
vm.runInContext(`${source}\nglobalThis.HistoryCard=LueftungsberaterHistoryCard`,ctx);
const Card=ctx.HistoryCard;
const card=new Card();
card.setConfig({entity:'sensor.room',metrics:['co2_in','humidity_in'],colors:{co2_in:'#123abc',humidity_in:'#00ee00'}});
card._metrics=[{key:'co2_in',label:'CO₂ innen',unit:'ppm',low:null,high:1000},{key:'humidity_in',label:'Feuchte innen',unit:'%',low:40,high:60}];
card._series=new Map([['co2_in',[{t:0,v:600},{t:3600000,v:1400}]],['humidity_in',[{t:0,v:38},{t:3600000,v:70}]]]);
card._start=0;card._end=3600000;card._cursor=3600000;
card._history=[{t:0,key:'open_now',attrs:{room_status:'red',ventilation_status:'orange'},kind:'decision'}];
card._hass={language:'de',states:{'sensor.room':{state:'open_now',attributes:{room_name:'Wohnung',display_mode:'room_air'}}}};
card._render();
const html=card.shadowRoot.innerHTML;
assert.match(html,/Lüftungsassistent|Historie/);
assert.match(html,/#123abc/);
assert.match(html,/#00ee00/);
assert.match(html,/1400|1.400/);
assert.match(html,/70 %/);
assert.match(html,/data-axis-zone="humidity_in"/);
assert.match(html,/Rote Markierungen gelten nur/);
assert.match(html,/Jetzt lüften/);
const axes=card._axis(card._metrics[0],[600,1400],true);
const humid=card._axis(card._metrics[1],[38,70],true);
assert.ok(axes.y(600)<.72,'one-sided CO2 is outside the lower red humidity-only zone');
assert.ok(axes.y(1400)<.4,'high CO2 enters upper red zone');
assert.ok(humid.y(38)>.72&&humid.y(70)<.38,'humidity traverses both red zones');
assert.ok(card._historicalDecision(3600000)?.color==='red');
console.log('PASS: v0.11.4 history axes, fixed zones, raw cursor values, colors');
