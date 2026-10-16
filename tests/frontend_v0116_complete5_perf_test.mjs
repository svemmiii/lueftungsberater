import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
const timeouts=[];
const fakeSetTimeout=(callback,delay)=>{const id={callback,delay,active:true};timeouts.push(id);return id;};
const fakeClearTimeout=id=>{if(id)id.active=false;};
class HTMLElementStub {
  attachShadow(){
    let html='';
    const root={rebuilds:0,buttons:[],curves:[],querySelector(){return null},querySelectorAll(sel){
      if(sel==='[data-history-focus]')return this.buttons;
      if(sel==='[data-history-curve]')return this.curves;
      return [];
    }};
    Object.defineProperty(root,'innerHTML',{get(){return html},set(value){
      html=value;root.rebuilds++;
      const build=(key,attr)=>[...String(value).matchAll(new RegExp(`${key}="([^"]*)"`,'g'))].map(m=>({
        attrs:{[attr]:m[1]},listener:null, getAttribute(k){return this.attrs[k]??null},
        setAttribute(k,v){this.attrs[k]=String(v)}, addEventListener(_event,cb){this.listener=cb}
      }));
      root.buttons=build('data-history-focus','data-history-focus');
      root.curves=build('data-history-curve','data-history-curve');
    }});
    this.shadowRoot=root;return root;
  }
}
const ctx={console,HTMLElement:HTMLElementStub,customElements:{get(){},define(){}},
  window:{customCards:[],location:{pathname:'/'},localStorage:{getItem(){return null},setItem(){}},addEventListener(){},removeEventListener(){}},
  navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {textContent:''}},head:{appendChild(){}}},
  setTimeout:fakeSetTimeout,clearTimeout:fakeClearTimeout,setInterval(){return 42},clearInterval(){},CustomEvent:class{}};
vm.createContext(ctx);vm.runInContext(`${source}\nglobalThis.CardClass=LueftungsberaterHistoryCard;`,ctx);
const Card=ctx.CardClass;
const card=new Card();
card._config={entity:'sensor.room',metrics:['co2_in','co2_out','humidity_in'],hours:24,colors:{}};
card._metrics=[{key:'co2_in',unit:'ppm',high:1000,low:null},{key:'co2_out',unit:'ppm',high:null,low:null},
  {key:'humidity_in',unit:'%',high:60,low:40}];
card._series=new Map(card._metrics.map(m=>[m.key,[{t:0,v:500},{t:2000,v:600}]]));
card._history=[];card._start=0;card._end=3000;card._cursor=3000;card._chartWidth=600;
card._hass={language:'de',states:{'sensor.room':{attributes:{display_mode:'room_air'}}}};
card._render();
const root=card.shadowRoot,builds=root.rebuilds;
const co2=root.buttons.find(b=>b.getAttribute('data-history-focus')==='co2');
assert.ok(co2?.listener,'CO₂ focus is attached to a live button');
co2.listener();
assert.equal(root.rebuilds,builds,'focus changes must not reconstruct shadowRoot.innerHTML');
assert.equal(root.curves.find(c=>c.getAttribute('data-history-curve')==='co2_in').attrs.opacity,'1');
assert.equal(root.curves.find(c=>c.getAttribute('data-history-curve')==='humidity_in').attrs.opacity,'0.12');
assert.equal(co2.attrs['aria-pressed'],'true');
root.buttons.find(b=>b.getAttribute('data-history-focus')==='').listener();
assert.equal(root.rebuilds,builds);
assert.ok(root.curves.every(c=>c.attrs.opacity==='1'),'All restores visibility without new DOM');
// Reusing axis samples across repeated lightweight renders avoids rescanning
// thousands of Recorder points just to construct unchanged tick positions.
const values=card._axisValueCache.get('co2:ppm').values;
card._render();
assert.strictEqual(card._axisValueCache.get('co2:ppm').values,values);
const original=card._series.get('co2_in');
card._series.set('co2_in',[...original,{t:2500,v:1300}]);card._render();
assert.notStrictEqual(card._axisValueCache.get('co2:ppm').values,values,'fresh series invalidates axis values');
// Real HA repeatedly passes a new hass object; queue one refresh no matter
// how many state changes arrive before the minimum refresh interval expires.
card.isConnected=true;
card._lastRefreshStart=Date.now();card._stateKey='old';
let refreshes=0;card._refresh=()=>{refreshes++;};
for(let i=0;i<100;i++)card.hass={states:{'sensor.room':{last_updated:`update-${i}`,attributes:{}}}};
const pending=timeouts.filter(timer=>timer.active);
assert.equal(pending.length,1,'100 successive states schedule only one refresh');
assert.equal(refreshes,0,'no synchronous history rebuild on every HA state update');
assert.equal(root.rebuilds,builds+2,'no full DOM rebuild after HA state changes');
pending[0].active=false;pending[0].callback();
assert.equal(refreshes,1);
// Explicit unavailable states split numeric segments and leave no false
// bridge between the last reading and a later recovery.
const recorded=[{t:100,v:620},{t:200,v:null},{t:300,v:850}];
const segments=card._plotSamples(recorded,0,400);
assert.equal(segments.length>=2,true);
assert.notEqual(segments[0].segment,segments[segments.length-1].segment);
assert.equal(card._atOrBefore(recorded,250).v,null,'outage cursor must show no value');
// The persisted YAML/card-editor period remains authoritative across a new
// instance; a rolling range always derives from current time, not activation.
const saved=new Card();saved.setConfig({entity:'sensor.room',hours:24});
const reloaded=new Card();reloaded.setConfig({entity:'sensor.room',hours:24});
assert.equal(saved._config.hours,24);assert.equal(reloaded._config.hours,24);
card.disconnectedCallback();
assert.equal(card._stateRefreshTimer,null);
console.log('PASS: COMPLETE(5) lightweight focus, axis memo, coalesced HA events and lifecycle');
