import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync('custom_components/lueftungsberater/frontend/lueftungsberater-card.js','utf8');
class Stub {
  attachShadow(){this.shadowRoot={innerHTML:'',querySelector(){return null;},querySelectorAll(){return [];}};return this.shadowRoot;}
  dispatchEvent(){return true;}
}
const ctx={console,HTMLElement:Stub,customElements:{get(){},define(){}},
  window:{customCards:[],localStorage:{getItem(){return null;},setItem(){}},location:{pathname:'/'},addEventListener(){},removeEventListener(){}},
  navigator:{language:'de-DE'},document:{documentElement:{lang:'de'},createElement(){return {set textContent(v){this.value=String(v)},get innerHTML(){return this.value??''}}},head:{appendChild(){}}},
  setTimeout(){return 1;},clearTimeout(){},setInterval(){return 1;},clearInterval(){},CustomEvent:class{},Event:class{}};
vm.createContext(ctx);
vm.runInContext(source+'\nglobalThis.HistoryCard=LueftungsberaterHistoryCard;',ctx);
const Card=ctx.HistoryCard;
const start=100_000,end=200_000;
function make(language='de') {
  const card=new Card();
  card._config={entity:'sensor.raum',hours:24,metrics:['co2_in','temp_in','humidity_in'],colors:{}};
  card._metrics=[{key:'co2_in',unit:'ppm',low:null,high:1000},
    {key:'temp_in',unit:'°C',low:24,high:24.4},
    {key:'humidity_in',unit:'%',low:40,high:60}];
  card._series=new Map([
    ['co2_in',[{t:start,v:750},{t:end,v:1100}]],
    ['temp_in',[{t:start,v:24.1},{t:end,v:24.6}]],
    ['humidity_in',[{t:start,v:48},{t:end,v:62}]],
  ]);
  card._history=[{t:start,kind:'decision',key:'room_good',attrs:{room_status:'green',room_recommendation_key:'room_good'}}];
  card._decisionEvents=card._history;card._advisorEvents=[];
  card._start=start;card._end=end;card._cursor=end;
  card._hass={language,states:{'sensor.raum':{state:'open_now',attributes:{display_mode:'room_air',room_name:'Wohnzimmer'}}}};
  card.getBoundingClientRect=()=>({width:390});
  return card;
}
for(const [lang,title,recommendation] of [
  ['de','Raumbewertung','Aktuell kein Lüftungsgrund'],
  ['en','Room assessment','No current reason to ventilate'],
  ['tr','Oda değerlendirmesi','Şu anda havalandırma nedeni yok'],
]) {
  const card=make(lang);card._recommendationLabels=null;card._render();
  const html=card.shadowRoot.innerHTML;
  assert.match(html,/data-room-status-row/);
  assert.ok(html.includes(title),`${lang}: room status has own heading`);
  assert.ok(html.includes(recommendation),`${lang}: historical recommendation translated without WS dictionary`);
  assert.doesNotMatch(html,/recommendation\.room_good/);
  const band=html.match(/<rect x="([\d.]+)" y="(\d+)" width="([\d.]+)" height="(\d+)" fill="var\(--success-color,#43a047\)"\/?>/);
  assert.ok(band,`${lang}: recorded green status band`);
  assert.equal(Number(band[2]),28);
  assert.equal(Number(band[4]),12);
  const hit=html.match(/<rect x="([\d.]+)" y="0" width="([\d.]+)" height="398" fill="transparent" data-hit\/?>/);
  assert.ok(hit,`${lang}: time-hit region`);
  assert.equal(Number(band[1]),Number(hit[1]),'room status uses same plot left as curves');
  assert.ok(Number(band[3])<=Number(hit[2]),'room status stays on graph timeline');
  assert.match(html,/data-inline-axis="co2:ppm" data-axis-side="left"/);
  assert.match(html,/data-inline-axis="temp:°C" data-axis-side="right"/);
  assert.equal((html.match(/class="reading"/g)||[]).length,3,'exactly one shared values list');
  assert.match(html,/<line x1="[\d.]+" x2="[\d.]+" y1="24" y2="350"[^>]*data-cursor-line\/>/);
}
const card=make('de');
const ticks=card._axisTickLabels([{v:24,p:.72},{v:24.4,p:.38},{v:25,p:.04}]);
assert.equal(JSON.stringify(ticks.map(t=>t.label)),JSON.stringify(['24','24,4','25']),'tick precision distinguishes 24 from 24.4 °C');
assert.equal(card._axisTickLabels([{v:100,p:.72},{v:100,p:.38}]).length,1,'equal physical ticks are not repeated');
// Backend-provided localized strings remain authoritative when available.
card._recommendationLabels={room_good:'Serverübersetzung'};
assert.ok(card._cursorDetail(card._metrics,end,()=>'?').includes('Serverübersetzung'));
console.log('PASS COMPLETE(3): room-status lane, timeline alignment, tick precision, fallback languages and unique values');
