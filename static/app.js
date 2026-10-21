const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const f=$('#f'),steps=$$('.step');let cur=0;
const W='279146358279';
function cnpOk(c){if(!/^\d{13}$/.test(c)||c[0]==='0')return false;let s=0;for(let i=0;i<12;i++)s+=+c[i]*+W[i];s%=11;if((s===10?1:s)!==+c[12])return false;
 const sec={1:1900,2:1900,3:1800,4:1800,5:2000,6:2000,7:1900,8:1900,9:1900}[c[0]];const y=sec+ +c.slice(1,3),m=+c.slice(3,5),d=+c.slice(5,7);
 const dt=new Date(y,m-1,d);return dt.getFullYear()===y&&dt.getMonth()===m-1&&dt.getDate()===d;}
function cnpUI(i){const v=i.value.trim(),sm=i.parentElement.querySelector('small.v');if(!v){i.classList.remove('bad','good');if(sm)sm.textContent='';return}
 const ok=cnpOk(v);i.classList.toggle('bad',!ok);i.classList.toggle('good',ok);if(sm){sm.textContent=ok?'✓ CNP valid':'✕ CNP invalid';sm.className='v '+(ok?'good':'bad')}}
document.addEventListener('input',e=>{if(e.target.classList.contains('cnp'))cnpUI(e.target);if(e.target.dataset.k==='cota')sumCote();if(['capital','valoare_parte'].includes(e.target.name))parti()});
$('#steps').innerHTML=steps.map((s,i)=>`<li>${i+1}. ${s.dataset.title}</li>`).join('');
function show(){steps.forEach((s,i)=>s.classList.toggle('on',i===cur));$$('#steps li').forEach((l,i)=>{l.className=i<cur?'done':i===cur?'on':''});
 $('#prev').style.visibility=cur?'visible':'hidden';$('#next').textContent=cur===steps.length-1?'Generează documentele':'Continuă →';if(cur===steps.length-1)rezumat();$$('#admini .pers').forEach(p=>p._refresh&&p._refresh());window.scrollTo({top:0,behavior:'smooth'})}
function persBox(container,title,extraHTML){const n=$('#tplPers').content.cloneNode(true).firstElementChild;n.querySelector('.extra').innerHTML=extraHTML||'';container.appendChild(n);
 n.querySelector('.x').onclick=()=>{if(container.children.length>1){n.remove();renum();sumCote()}};renum();return n}
function renum(){$$('#asociati .pers').forEach((p,i)=>p.querySelector('.ttl').textContent='Asociat '+(i+1));
 $$('#admini .pers').forEach((p,i)=>{p.querySelector('.ttl').textContent='Administrator '+(i+1);fillCopy(p)})}
function readPers(p){const o={};p.querySelectorAll('[data-k]').forEach(i=>o[i.dataset.k]=i.value.trim());return o}
function fillCopy(p){const box=p.querySelector('.copy-from');
 box.innerHTML='<label>Completează din asociat<select><option value="">— persoană din afara asociaților —</option></select></label>';
 const sel=box.querySelector('select');
 const refresh=()=>{const v=sel.value;const as=$$('#asociati .pers').map(readPers);sel.innerHTML='<option value="">— persoană din afara asociaților —</option>'+as.map((a,i)=>`<option value="${i}">${esc(a.nume||'Asociat '+(i+1))}</option>`).join('');sel.value=v};
 sel.addEventListener('focus',refresh);sel.addEventListener('mousedown',refresh);p._refresh=refresh;
 sel.onchange=e=>{if(e.target.value==='')return;const a=$$('#asociati .pers').map(readPers)[+e.target.value];p.querySelectorAll('[data-k]').forEach(i=>{if(i.dataset.k in a&&i.dataset.k!=='cota'){i.value=a[i.dataset.k];if(i.classList.contains('cnp'))cnpUI(i)}})}}
const cotaHTML='<label>Cota de participare (%)<input data-k="cota" type="number" step="any" min="0" max="100" required></label>';
const mandHTML='<label>Durata mandatului<input data-k="mandat" value="nelimitată"></label>';
$('#addAsoc').onclick=()=>persBox($('#asociati'),'',cotaHTML);$('#addAdm').onclick=()=>persBox($('#admini'),'',mandHTML);
persBox($('#asociati'),'',cotaHTML);persBox($('#admini'),'',mandHTML);
function sumCote(){const s=$$('#asociati [data-k=cota]').reduce((a,i)=>a+(+i.value||0),0);const el=$('#sumCote');el.textContent=`Total cote: ${+s.toFixed(4)}%`+(Math.abs(s-100)<1e-3?' ✓':' (trebuie 100%)');el.className='sum '+(Math.abs(s-100)<1e-3?'ok':'bad')}
function parti(){const c=+f.capital.value,v=+f.valoare_parte.value;$('#nrParti').textContent=c&&v?(Number.isInteger(c/v)?`→ ${c/v} părți sociale.`:'→ capitalul nu se împarte exact la valoarea părții.'):''}
f.durata.onchange=()=>{f.durata_ani.disabled=f.durata.value!=='limitata'};parti();
function data(){const g=n=>(f[n]?.value||'').trim();return{denumire:g('denumire'),alternative:[g('alt1'),g('alt2')],
 sediu:{judet:g('s_judet'),localitate:g('s_localitate'),strada:g('s_strada'),numar:g('s_numar'),bloc:g('s_bloc'),scara:g('s_scara'),etaj:g('s_etaj'),ap:g('s_ap'),carte_funciara:g('s_cf'),durata_comodat:g('s_durata'),activitate_la_sediu:f.s_activ.checked,
  proprietar:{nume:g('p_nume'),cnp:g('p_cnp'),ci_serie:g('p_ci_serie'),ci_numar:g('p_ci_numar'),domiciliu:g('p_domiciliu')}},
 asociati:$$('#asociati .pers').map(readPers),administratori:$$('#admini .pers').map(readPers),capital:g('capital'),valoare_parte:g('valoare_parte'),
 caen_principal:g('caen_principal'),caen_principal_desc:g('caen_desc'),caen_secundare:g('caen_sec').split(/[,;\s]+/).filter(Boolean),durata:g('durata'),durata_ani:g('durata_ani')}}
function checkStep(i){const e=[];const st=steps[i];st.querySelectorAll('input[required]').forEach(inp=>{const bad=!inp.value.trim();inp.classList.toggle('bad',bad);if(bad)e.push((inp.closest('label')?.childNodes[0].textContent||'Câmp').trim()+' este obligatoriu.')});
 st.querySelectorAll('input.cnp').forEach(inp=>{if(inp.value&&!cnpOk(inp.value.trim()))e.push('CNP invalid: '+inp.value)});
 if(i===2){const s=$$('#asociati [data-k=cota]').reduce((a,x)=>a+(+x.value||0),0);if(Math.abs(s-100)>1e-3)e.push(`Suma cotelor este ${s}%, trebuie 100%.`)}
 if(i===4){if(+f.capital.value<+f.capital.min)e.push(`Capitalul minim este ${f.capital.min} lei.`);if(!/^\d{4}$/.test(f.caen_principal.value))e.push('CAEN principal: 4 cifre.')}
 if(i===5&&!$('#acord').checked)e.push('Bifați confirmarea.');return[...new Set(e)]}
function errs(e){const b=$('#erori');if(!e.length){b.hidden=true;return}b.hidden=false;b.innerHTML='<b>Corectați:</b><ul>'+e.map(x=>`<li>${x}</li>`).join('')+'</ul>'}
function rezumat(){const d=data();$('#rezumat').innerHTML=`<dl><dt>Denumire</dt><dd>${esc(d.denumire)} S.R.L. (alternative: ${esc(d.alternative.join(', '))})</dd>
 <dt>Sediu</dt><dd>${esc([d.sediu.localitate,'str. '+d.sediu.strada+' nr. '+d.sediu.numar,'jud. '+d.sediu.judet].join(', '))} – proprietar ${esc(d.sediu.proprietar.nume)}</dd>
 <dt>Asociați</dt><dd>${d.asociati.map(a=>esc(a.nume)+' – '+esc(a.cota)+'%').join('<br>')}</dd><dt>Administratori</dt><dd>${d.administratori.map(a=>esc(a.nume)).join(', ')}</dd>
 <dt>Capital</dt><dd>${esc(d.capital)} lei, părți de ${esc(d.valoare_parte)} lei</dd><dt>CAEN</dt><dd>${esc(d.caen_principal)} ${esc(d.caen_principal_desc)}${d.caen_secundare.length?'; secundare: '+esc(d.caen_secundare.join(', ')):''}</dd>
 <dt>Durată</dt><dd>${d.durata==='nelimitata'?'nelimitată':esc(d.durata_ani)+' ani'}</dd></dl>`}
$('#prev').onclick=()=>{if(cur>0){cur--;errs([]);show()}};
$('#next').onclick=async()=>{const e=checkStep(cur);errs(e);if(e.length)return;if(cur<steps.length-1){cur++;show();return}
 const btn=$('#next');btn.disabled=true;btn.textContent='Se generează…';
 try{const r=await fetch('/api/genereaza',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data())});const j=await r.json();
  if(!j.ok){errs(j.erori||['Eroare necunoscută']);return}
  const T={act:'Act constitutiv',declaratie:'Declarație pe propria răspundere',specimen:'Specimen de semnătură',contract:'Contract de comodat – sediu social',checklist:'Checklist și pașii următori'};const nice=n=>{const k=n.replace(/^\d+_/,'').split('_')[0];const rest=n.replace(/\.pdf$/,'').split('_').slice(k==='specimen'?4:3).join(' ');return (T[k]||n)+(rest&&k!=='contract'&&k!=='checklist'&&k!=='act'?' – '+rest:'')};
  $('#rezultat').hidden=false;f.hidden=true;$('#steps').hidden=true;
  $('#rezultat').innerHTML=`<h2>✅ Dosarul a fost generat</h2><p>Documentele de mai jos sunt <b>proiecte</b> și trebuie validate de avocatul partener. Consultați checklist-ul pentru actele pe care trebuie să le furnizați și pentru pașii următori (semnătură electronică calificată, depunere prin avocat).</p>
  <ul class="files">${j.fisiere.map(n=>`<li><span>📄 ${esc(nice(n))}</span><span><a href="/dosar/${j.id}/${n}" target="_blank">Vezi</a> · <a href="/dosar/${j.id}/${n}?dl=1">Descarcă</a></span></li>`).join('')}</ul>
  <p><a class="btn" href="/dosar/${j.id}.zip">⬇ Descarcă tot dosarul (ZIP)</a> <button class="btn ghost" onclick="location.reload()">Dosar nou</button></p>
  <p class="hint">Linkurile sunt valabile aproximativ o oră.</p>`;window.scrollTo({top:0,behavior:'smooth'})}
 catch(x){errs(['Eroare de rețea: '+x])}finally{btn.disabled=false;if(cur===steps.length-1)btn.textContent='Generează documentele'}};
show();
