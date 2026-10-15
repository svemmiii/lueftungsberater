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

// COMPLETE(41): for a single high-only metric, the FULL red field must end
// at the metric's .40 high boundary (not the .38 used by dual-limit axes).
// The mismatch was ~0.02 * (271 - 24) = 4.94 SVG pixels.
function historyChartWith(metrics) {
  const test=new Card();
  test.setConfig({entity:'sensor.room',metrics:metrics.map(m=>m.key),hours:24,colors:{}});
  test._metrics=metrics;
  test._series=new Map(metrics.map(m=>[m.key,[{t:0,v:(m.high??100)/2},{t:3600000,v:(m.high??100)*1.2}]]));
  test._start=0;test._end=3600000;test._cursor=3600000;
  test._history=[];
  test._hass={language:'de',states:{'sensor.room':{state:'open_now',attributes:{room_name:'Room'}}}};
  test._render();
  return test.shadowRoot.innerHTML;
}
function upperRedField(html) {
  const match=html.match(/<rect x="[^"]+" y="([\d.]+)" width="[^"]+" height="([\d.]+)" fill="var\(--error-color,#d35b5b\)" fill-opacity="0\.13"\/>/);
  return match?{top:Number(match[1]),bottom:Number(match[1])+Number(match[2])}:null;
}
const chartTop=24,chartBottom=310-39;
const yAt=relative=>chartTop+relative*(chartBottom-chartTop);
const co2Only=historyChartWith([{key:'co2_in',unit:'ppm',low:null,high:1000}]);
const highOnlyField=upperRedField(co2Only);
assert.ok(highOnlyField,'CO2-only chart has a red upper-limit field');
assert.ok(Math.abs(highOnlyField.top-yAt(.04))<1e-8);
assert.ok(Math.abs(highOnlyField.bottom-yAt(.40))<1e-8,
 'high-only red field must touch the exact CO2 threshold position');
assert.match(co2Only,/font-size="12"[^>]*>[^<]*<\/text>/,
 'axis values remain legible in a horizontally scrollable mobile chart');
const humidityOnly=historyChartWith([{key:'humidity_in',unit:'%',low:40,high:60}]);
const dualField=upperRedField(humidityOnly);
assert.ok(dualField);
assert.ok(Math.abs(dualField.bottom-yAt(.38))<1e-8,
 'dual-limit red field must touch its distinct humidity high boundary');
assert.match(humidityOnly,/fill-opacity="0\.10"/,'dual-limit lower red field remains present');
const combined=historyChartWith([
 {key:'co2_in',unit:'ppm',low:null,high:1000},
 {key:'humidity_in',unit:'%',low:40,high:60},
]);
assert.equal(upperRedField(combined),null,'do not shade multiple independent scales');
assert.match(combined,/data-axis-zone="co2_in"/);
assert.match(combined,/data-axis-zone="humidity_in"/);
console.log('PASS: high-only and dual-limit red bounds precisely meet their own high threshold; mobile axis labels');

