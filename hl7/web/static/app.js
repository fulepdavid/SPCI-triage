'use strict';
const $ = id => document.getElementById(id);
const fields = [['spo2','SpO₂'],['pulse_rate','Pulse'],['nibp_sys','NIBP / SYS'],['nibp_dia','NIBP / DIA'],['nibp_mean','NIBP / MAP'],['temperature','Temperature'],['respiration_rate','Respiration rate'],['nibp_pulse','NIBP Pulse'],['ecg_heart_rate','ECG Heart Rate']];
let tab = 'live';
for(const [i,[key,label]] of fields.entries()){
  const card=document.createElement('article'); card.className='card'+(i<2?' primary':''); card.id='card-'+key;
  const title=document.createElement('h2'); title.textContent=label;
  const value=document.createElement('span'); value.className='value'; value.id='value-'+key; value.textContent='—';
  const unit=document.createElement('span'); unit.className='unit'; unit.id='unit-'+key;
  card.append(title,value,unit); $('cards').append(card);
}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
  tab=b.dataset.tab; document.querySelectorAll('.panel').forEach(p=>p.hidden=p.id!==tab);
  document.querySelectorAll('nav button').forEach(x=>x.classList.toggle('active',x===b));
});
async function get(path){const r=await fetch(path,{cache:'no-store',signal:AbortSignal.timeout(5000)});if(!r.ok)throw Error(r.status);return r.json();}
function time(t){return t?new Date(t).toLocaleString('hu-HU'):'—';}
async function refresh(){
  try{
    const selected=$('device').value;
    const devices=await get('/api/devices');
    for(const d of devices){if(!Array.from($('device').options).some(o=>o.value===d.device_id)){
      const o=document.createElement('option');o.value=d.device_id;o.textContent=d.device_id;$('device').append(o);
    }}
    const query=selected?'?device_id='+encodeURIComponent(selected):'';
    const d=await get('/api/latest'+query);
    $('status').textContent=d.fresh?'Connected · friss adat':d.connected?'Connected · régi adat':'Disconnected';
    $('status').className='badge '+(d.fresh?'fresh':d.connected?'stale':'');
    $('connection').textContent=`IP: ${d.device_ip||'—'}    •    Eszköz: ${d.device_id||'—'}    •    HL7: ${d.hl7_version||'—'}\nUtolsó üzenet: ${time(d.received_at)}    •    Adat kora: ${d.age_seconds??'—'} s`;
    for(const [key] of fields){const v=d.vitals[key];$('value-'+key).textContent=v?.value??'—';$('unit-'+key).textContent=v?.unit||'';$('card-'+key).classList.toggle('old',!v?.fresh);$('card-'+key).title=v?`Fogadás: ${time(v.received_at)} · ${v.age_seconds} s · ${v.fresh?'friss':'régi adat'}`:'Nincs mérés';}
    $('observations').textContent=JSON.stringify(d.observations||[],null,2);
    $('csv').href='/api/history.csv'+query;
    if(tab==='raw'){
      const rows=await get('/api/raw');$('raw-list').replaceChildren();
      for(const r of rows.reverse()){const pre=document.createElement('pre');pre.textContent=`${time(r.received_at)} · ${r.device_ip}\n${r.message.replace(/\r\n|\r/g,'\n')}`;$('raw-list').append(pre);}
    }
    if(tab==='history'){
      const rows=await get('/api/history'+query);$('history-rows').replaceChildren();
      for(const r of rows.reverse()){const tr=document.createElement('tr');const values=[time(r.received_at),r.device_id,...fields.slice(0,5).map(([k])=>{const v=r.vitals[k];return v?`${v.value??'—'} ${v.unit}`:'—';})];for(const value of values){const td=document.createElement('td');td.textContent=value;tr.append(td);}$('history-rows').append(tr);}
    }
    if(tab==='settings')$('config').textContent=JSON.stringify(await get('/api/settings'),null,2);
    $('fetch-state').textContent='Web API elérhető · '+new Date().toLocaleTimeString('hu-HU');
  }catch(e){$('status').textContent='Web API nem elérhető';$('status').className='badge stale';$('fetch-state').textContent='Újrapróbálkozás…';document.querySelectorAll('.card').forEach(c=>c.classList.add('old'));}
  finally{setTimeout(refresh,1000);}
}
refresh();
