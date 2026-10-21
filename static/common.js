const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function api(url,opt={}){opt.headers=Object.assign({'X-Requested-With':'fetch'},opt.headers||{});const r=await fetch(url,opt);
 if(r.status===401){location.href='/login?next='+encodeURIComponent(location.pathname+location.search);throw new Error('401')}
 try{return await r.json()}catch(e){return{ok:false,erori:['Eroare server ('+r.status+')']}}}
const T={act:'Act constitutiv',declaratie:'Declarație pe propria răspundere',specimen:'Specimen de semnătură',contract:'Contract de comodat – sediu social',checklist:'Checklist și pașii următori'};
const nice=n=>{const k=n.replace(/^\d+_/,'').split('_')[0];const rest=n.replace(/\.pdf$/,'').split('_').slice(k==='specimen'?4:3).join(' ');return (T[k]||n)+(rest&&!['contract','checklist','act'].includes(k)?' – '+rest:'')};
function filesHTML(j){if(!j.ok)return '<div class="err">'+esc((j.erori||[]).join(' '))+'</div>';
 return `<ul class="files">${j.fisiere.map(n=>`<li><span>📄 ${esc(nice(n))}</span><span><a href="/dosar/${j.id}/${n}" target="_blank">Vezi</a> · <a href="/dosar/${j.id}/${n}?dl=1">Descarcă</a></span></li>`).join('')}</ul><p><a class="btn" href="/dosar/${j.id}.zip">⬇ Tot dosarul (ZIP)</a></p>`}
