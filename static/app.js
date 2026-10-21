const f=$('#f'),steps=$$('.step');let cur=0,PERS=[],FIRME=[],DOSAR_ID=window.DOSAR_ID||null;
const W='279146358279';
function cnpOk(c){if(!/^\d{13}$/.test(c)||c[0]==='0')return false;let s=0;for(let i=0;i<12;i++)s+=+c[i]*+W[i];s%=11;if((s===10?1:s)!==+c[12])return false;
 const sec={1:1900,2:1900,3:1800,4:1800,5:2000,6:2000,7:1900,8:1900,9:1900}[c[0]];const y=sec+ +c.slice(1,3),m=+c.slice(3,5),d=+c.slice(5,7);
 const dt=new Date(y,m-1,d);return dt.getFullYear()===y&&dt.getMonth()===m-1&&dt.getDate()===d;}
function cnpUI(i){const v=i.value.trim(),sm=i.parentElement.querySelector('small.v');if(!v){i.classList.remove('bad','good');if(sm)sm.textContent='';return}
 const ok=cnpOk(v);i.classList.toggle('bad',!ok);i.classList.toggle('good',ok);if(sm){sm.textContent=ok?'✓ CNP valid':'✕ CNP invalid';sm.className='v '+(ok?'good':'bad')}}
document.addEventListener('input',e=>{e.target.classList.remove('prefilled');if(e.target.classList.contains('cnp'))cnpUI(e.target);if(e.target.dataset.k==='cota')sumCote();if(['capital','valoare_parte'].includes(e.target.name))parti()});
$('#steps').innerHTML=steps.map((s,i)=>`<li data-i="${i}">${i+1}. ${s.dataset.title}</li>`).join('');
$$('#steps li').forEach(li=>li.onclick=()=>{if(DOSAR_ID||+li.dataset.i<cur){cur=+li.dataset.i;errs([]);show()}});
function show(){steps.forEach((s,i)=>s.classList.toggle('on',i===cur));$$('#steps li').forEach((l,i)=>{l.className=i<cur?'done':i===cur?'on':''});
 $('#prev').style.visibility=cur?'visible':'hidden';$('#next').textContent=cur===steps.length-1?(DOSAR_ID?'Salvează și regenerează':'Generează documentele'):'Continuă →';
 if(cur===steps.length-1)rezumat();$$('#admini .pers').forEach(p=>p._refresh&&p._refresh());window.scrollTo({top:0,behavior:'smooth'})}
// ---- persoane salvate + scanare CI
function fillPerson(box,o,mark){box.querySelectorAll('[data-k]').forEach(i=>{const k=i.dataset.k;if(k==='cota'||k==='mandat')return;if(o[k]!==undefined&&o[k]!==''&&o[k]!==null){i.value=o[k];if(mark)i.classList.add('prefilled');if(i.classList.contains('cnp'))cnpUI(i)}})}
function persOptions(){return '<option value="">— alegeți —</option>'+PERS.map((p,i)=>`<option value="${i}">${esc(p.nume)} · ${esc(p.cnp)}</option>`).join('')}
function setupTools(box){const sel=box.querySelector('.pickPers');if(sel){sel.innerHTML=persOptions();sel.onchange=()=>{if(sel.value==='')return;const p=PERS[+sel.value];fillPerson(box,{...p.data,nume:p.nume,cnp:p.cnp},false)}}
 const sc=box.querySelector('.scan');if(sc)sc.onchange=async()=>{const res=box.querySelector('.scanres');const files=[...sc.files].slice(0,2);if(!files.length)return;
  res.hidden=false;res.className='scanres';res.textContent='⏳ Se citește actul de identitate… (prima scanare după pornire poate dura ~20 s)';
  const fd=new FormData();files.forEach(x=>fd.append('imagini',x));sc.value='';
  try{const j=await api('/api/ci',{method:'POST',body:fd});if(!j.ok){res.className='scanres warn';res.textContent=(j.erori||[]).join(' ');return}
   const r=j.rezultat;fillPerson(box,r,true);const v=r.mrz?r.mrz.verificari:null;const allok=v&&Object.values(v).every(Boolean);
   res.className='scanres '+(allok&&!r.avertismente.length?'ok':'warn');
   res.innerHTML=`<b>${esc(r.tip_document)}</b> · MRZ: ${v?(allok?'✓ toate cifrele de control valide':'⚠ '+Object.entries(v).filter(x=>!x[1]).map(x=>x[0]).join(', ')+' invalide'):'negăsit'}${r.cnp_confirmat_mrz?' · CNP confirmat de MRZ':''}`+
    (r.avertismente.length?'<br>'+r.avertismente.map(esc).join('<br>'):'')+'<br><small>Câmpurile completate automat sunt evidențiate cu galben – verificați-le înainte de salvare. Imaginea nu a fost stocată.</small>'}
  catch(e){res.className='scanres warn';res.textContent='Eroare: '+e}}}
function persBox(container,extraHTML){const n=$('#tplPers').content.cloneNode(true).firstElementChild;n.querySelector('.extra').innerHTML=extraHTML||'';container.appendChild(n);
 n.querySelector('.x').onclick=()=>{if(container.children.length>1){n.remove();renum();sumCote()}};setupTools(n);renum();return n}
function renum(){$$('#asociati .pers').forEach((p,i)=>p.querySelector('.ttl').textContent='Asociat '+(i+1));
 $$('#admini .pers').forEach((p,i)=>{p.querySelector('.ttl').textContent='Administrator '+(i+1);if(!p._refresh)fillCopy(p)})}
function readPers(p){const o={};p.querySelectorAll('[data-k]').forEach(i=>o[i.dataset.k]=i.value.trim());return o}
function fillCopy(p){const box=p.querySelector('.copy-from');
 box.innerHTML='<label>Completează din asociat<select><option value="">— persoană din afara asociaților —</option></select></label>';
 const sel=box.querySelector('select');
 const refresh=()=>{const v=sel.value;const as=$$('#asociati .pers').map(readPers);sel.innerHTML='<option value="">— persoană din afara asociaților —</option>'+as.map((a,i)=>`<option value="${i}">${esc(a.nume||'Asociat '+(i+1))}</option>`).join('');sel.value=v};
 sel.addEventListener('focus',refresh);sel.addEventListener('mousedown',refresh);p._refresh=refresh;
 sel.onchange=e=>{if(e.target.value==='')return;fillPerson(p,$$('#asociati .pers').map(readPers)[+e.target.value],false)}}
const cotaHTML='<label>Cota de participare (%)<input data-k="cota" type="number" step="any" min="0" max="100" required></label>';
const mandHTML='<label>Durata mandatului<input data-k="mandat" value="nelimitată"></label>';
$('#addAsoc').onclick=()=>persBox($('#asociati'),cotaHTML);$('#addAdm').onclick=()=>persBox($('#admini'),mandHTML);
function sumCote(){const s=$$('#asociati [data-k=cota]').reduce((a,i)=>a+(+i.value||0),0);const el=$('#sumCote');el.textContent=`Total cote: ${+s.toFixed(4)}%`+(Math.abs(s-100)<1e-3?' ✓':' (trebuie 100%)');el.className='sum '+(Math.abs(s-100)<1e-3?'ok':'bad')}
function parti(){const c=+f.capital.value,v=+f.valoare_parte.value;$('#nrParti').textContent=c&&v?(Number.isInteger(c/v)?`→ ${c/v} părți sociale.`:'→ capitalul nu se împarte exact la valoarea părții.'):''}
f.durata.onchange=()=>{f.durata_ani.disabled=f.durata.value!=='limitata'};
function data(){const g=n=>(f[n]?.value||'').trim();return{denumire:g('denumire'),alternative:[g('alt1'),g('alt2')],
 sediu:{judet:g('s_judet'),localitate:g('s_localitate'),strada:g('s_strada'),numar:g('s_numar'),bloc:g('s_bloc'),scara:g('s_scara'),etaj:g('s_etaj'),ap:g('s_ap'),carte_funciara:g('s_cf'),durata_comodat:g('s_durata'),activitate_la_sediu:f.s_activ.checked,
  proprietar:readPers($('#propBox'))},
 asociati:$$('#asociati .pers').map(readPers),administratori:$$('#admini .pers').map(readPers),capital:g('capital'),valoare_parte:g('valoare_parte'),
 caen_principal:g('caen_principal'),caen_principal_desc:g('caen_desc'),caen_secundare:g('caen_sec').split(/[,;\s]+/).filter(Boolean),durata:g('durata'),durata_ani:g('durata_ani')}}
function setF(n,v){if(f[n]!==undefined&&v!==undefined&&v!==null)f[n].value=v}
function fillSediu(s){if(!s)return;setF('s_judet',s.judet);setF('s_localitate',s.localitate);setF('s_strada',s.strada);setF('s_numar',s.numar);setF('s_bloc',s.bloc);setF('s_scara',s.scara);setF('s_etaj',s.etaj);setF('s_ap',s.ap);setF('s_cf',s.carte_funciara);setF('s_durata',s.durata_comodat||5);f.s_activ.checked=!!s.activitate_la_sediu;if(s.proprietar)fillPerson($('#propBox'),s.proprietar)}
function loadData(d){setF('denumire',d.denumire);setF('alt1',(d.alternative||[])[0]);setF('alt2',(d.alternative||[])[1]);fillSediu(d.sediu);
 $('#asociati').innerHTML='';(d.asociati||[{}]).forEach(a=>{const b=persBox($('#asociati'),cotaHTML);fillPerson(b,a);b.querySelector('[data-k=cota]').value=a.cota||''});
 $('#admini').innerHTML='';(d.administratori||[{}]).forEach(a=>{const b=persBox($('#admini'),mandHTML);fillPerson(b,a);b.querySelector('[data-k=mandat]').value=a.mandat||'nelimitată'});
 setF('capital',d.capital);setF('valoare_parte',d.valoare_parte);setF('caen_principal',d.caen_principal);setF('caen_desc',d.caen_principal_desc);setF('caen_sec',(d.caen_secundare||[]).join(', '));setF('durata',d.durata||'nelimitata');setF('durata_ani',d.durata_ani);f.durata.onchange();sumCote();parti()}
function checkStep(i){const e=[];const st=steps[i];st.querySelectorAll('input[required]').forEach(inp=>{const bad=!inp.value.trim();inp.classList.toggle('bad',bad);if(bad)e.push((inp.closest('label')?.childNodes[0].textContent||'Câmp').trim()+' este obligatoriu.')});
 st.querySelectorAll('input.cnp').forEach(inp=>{if(inp.value&&!cnpOk(inp.value.trim()))e.push('CNP invalid: '+inp.value)});
 if(i===2){const s=$$('#asociati [data-k=cota]').reduce((a,x)=>a+(+x.value||0),0);if(Math.abs(s-100)>1e-3)e.push(`Suma cotelor este ${s}%, trebuie 100%.`)}
 if(i===4){if(+f.capital.value<+f.capital.min)e.push(`Capitalul minim este ${f.capital.min} lei.`);if(!/^\d{4}$/.test(f.caen_principal.value))e.push('CAEN principal: 4 cifre.')}
 if(i===5&&!$('#acord').checked)e.push('Bifați confirmarea.');return[...new Set(e)]}
function errs(e){const b=$('#erori');if(!e.length){b.hidden=true;return}b.hidden=false;b.innerHTML='<b>Corectați:</b><ul>'+e.map(x=>`<li>${esc(x)}</li>`).join('')+'</ul>'}
function rezumat(){const d=data();$('#rezumat').innerHTML=`<dl><dt>Denumire</dt><dd>${esc(d.denumire)} S.R.L. (alternative: ${esc(d.alternative.join(', '))})</dd>
 <dt>Sediu</dt><dd>${esc([d.sediu.localitate,'str. '+d.sediu.strada+' nr. '+d.sediu.numar,'jud. '+d.sediu.judet].join(', '))} – proprietar ${esc(d.sediu.proprietar.nume)}</dd>
 <dt>Asociați</dt><dd>${d.asociati.map(a=>esc(a.nume)+' – '+esc(a.cota)+'%').join('<br>')}</dd><dt>Administratori</dt><dd>${d.administratori.map(a=>esc(a.nume)).join(', ')}</dd>
 <dt>Capital</dt><dd>${esc(d.capital)} lei, părți de ${esc(d.valoare_parte)} lei</dd><dt>CAEN</dt><dd>${esc(d.caen_principal)} ${esc(d.caen_principal_desc)}${d.caen_secundare.length?'; secundare: '+esc(d.caen_secundare.join(', ')):''}</dd>
 <dt>Durată</dt><dd>${d.durata==='nelimitata'?'nelimitată':esc(d.durata_ani)+' ani'}</dd></dl>`}
$('#prev').onclick=()=>{if(cur>0){cur--;errs([]);show()}};
$('#next').onclick=async()=>{const e=checkStep(cur);errs(e);if(e.length)return;if(cur<steps.length-1){cur++;show();return}
 const btn=$('#next');btn.disabled=true;btn.textContent='Se generează…';
 try{const j=await api('/api/genereaza',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({data:data(),dosar_id:DOSAR_ID})});
  if(!j.ok){errs(j.erori||['Eroare necunoscută']);return}
  DOSAR_ID=j.dosar_id;history.replaceState(null,'','/?dosar='+j.dosar_id);
  $('#rezultat').hidden=false;f.hidden=true;$('#steps').hidden=true;
  $('#rezultat').innerHTML=`<h2>✅ Dosarul #${j.dosar_id} a fost salvat și generat</h2><p>Documentele sunt <b>proiecte</b> – validați-le cu avocatul partener. Persoanele și firma au fost salvate pentru reutilizare.</p>`+filesHTML(j)+
   `<p><button class="btn ghost" id="edit">✎ Editează dosarul</button> <a class="btn ghost" href="/">Dosar nou</a> <a class="btn ghost" href="/dosare">Toate dosarele</a></p><p class="hint">Linkurile către PDF-uri sunt valabile ~1 oră; le puteți regenera oricând din lista de dosare.</p>`;
  $('#edit').onclick=()=>{$('#rezultat').hidden=true;f.hidden=false;$('#steps').hidden=false;cur=0;show()};window.scrollTo({top:0,behavior:'smooth'})}
 catch(x){errs(['Eroare de rețea: '+x])}finally{btn.disabled=false;show()}};
(async()=>{
 try{[PERS,FIRME]=await Promise.all([api('/api/persoane'),api('/api/firme')])}catch(e){}
 setupTools($('#propBox'));
 $('#pickFirma').innerHTML='<option value="">— alegeți pentru a precompleta denumirea și sediul —</option>'+FIRME.map((c,i)=>`<option value="${i}">${esc(c.data.denumire)} S.R.L.</option>`).join('');
 $('#pickFirma').onchange=e=>{if(e.target.value==='')return;const c=FIRME[+e.target.value].data;setF('denumire',c.denumire);fillSediu(c.sediu)};
 if(DOSAR_ID){const d=await api('/api/dosare/'+DOSAR_ID);if(d&&d.data){loadData(d.data);$('#titlu').textContent=`Dosar #${DOSAR_ID} – ${d.data.denumire} S.R.L.`;$('#acord').checked=false}}
 else{persBox($('#asociati'),cotaHTML);persBox($('#admini'),mandHTML)}
 parti();show()})();
