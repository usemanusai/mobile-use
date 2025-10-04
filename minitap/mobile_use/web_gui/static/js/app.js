const chat = document.getElementById('chat');
const statusTextEl = document.getElementById('statusText');
const queueEl = document.getElementById('queueLen');
const taskInput = document.getElementById('taskInput');
const outputDesc = document.getElementById('outputDesc');
const sendBtn = document.getElementById('sendBtn');
const enhanceBtn = document.getElementById('enhanceBtn');
const toggleAdvanced = document.getElementById('toggleAdvanced');
const advanced = document.getElementById('advanced');
const clearChat = document.getElementById('clearChat');
const shutdownBtn = document.getElementById('shutdownBtn');

let sending = false;
let history = [];

function ts() { return new Date().toLocaleTimeString(); }

function escapeHtml(str){
  return (str || '').replace(/[&<>"']/g, (c)=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
}

function addMsg(role, text) {
  const el = document.createElement('div');
  el.className = 'msg ' + (role === 'user' ? 'user' : 'agent');
  el.innerHTML = `<div class="bubble"><div>${escapeHtml(text)}</div><div class="timestamp">${ts()}</div></div>`;
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
  history.push({type: role, text});
  persist();
}

function addSystem(text){
  const el = document.createElement('div');
  el.className = 'system';
  el.textContent = text;
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
}

function persist(){
  try{ localStorage.setItem('mobile_use_history', JSON.stringify(history)); }catch(e){}
}

function restore(){
  try{
    const raw = localStorage.getItem('mobile_use_history');
    if(!raw) return;
    history = JSON.parse(raw);
    for(const m of history){ addMsg(m.type, m.text); }
  }catch(e){ history = []; }
}

function setQueue(n){ try{ queueEl.textContent = 'Queue: ' + (typeof n==='number'? n : 0); }catch(e){} }

function setStatus(text){ statusTextEl.textContent = text; }

function disableInputs(dis){
  sendBtn.disabled = dis; enhanceBtn.disabled = dis; taskInput.disabled = dis; outputDesc.disabled = dis;
}

// SSE stream for live updates
function connectSSE(){
  const es = new EventSource('/api/stream');
  es.onmessage = (ev)=>{
    try{
      const data = JSON.parse(ev.data);
      if(data.type === 'status') setStatus(data.status || '');
      if(data.type === 'user_task') addMsg('user', data.text || '');
      if(data.type === 'queued') { addSystem('Task queued'); if(typeof data.size==='number') setQueue(data.size); }
      if(data.type === 'dequeued') addSystem('Running task');
      if(data.type === 'queue' && typeof data.size==='number') setQueue(data.size);
      if(data.type === 'update' && data.node) setStatus('Active: ' + data.node);
      if(data.type === 'final') addMsg('agent', typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2));
      if(data.type === 'error') addMsg('agent', 'Error: ' + (data.message || ''));
    }catch(e){}
  };
  es.onerror = ()=>{ /* keep trying */ };
}

// Actions
sendBtn.addEventListener('click', async ()=>{
  if(sending) return; sending = true; disableInputs(true);
  const task = taskInput.value.trim();
  const output_description = outputDesc.value.trim() || undefined;
  if(!task){ sending = false; disableInputs(false); return; }
  try{
    addMsg('user', task);
    const res = await fetch('/api/task', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({task, output_description})});
    const json = await res.json();
    if(json.ok && json.result !== undefined){ /* final also comes via SSE; ensure display */ }
    else if(!json.ok){ addMsg('agent', 'Error: ' + (json.error || 'unknown')); }
  }catch(e){ addMsg('agent', 'Error: ' + e); }
  finally{ sending = false; disableInputs(false); }
});

enhanceBtn.addEventListener('click', async ()=>{
  const text = taskInput.value.trim(); if(!text) return;
  enhanceBtn.disabled = true;
  try{
    const res = await fetch('/api/enhance', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text})});
    const json = await res.json();
    if(json.ok && json.enhanced){ taskInput.value = json.enhanced; }
  }catch(e){}
  finally{ enhanceBtn.disabled = false; }
});
shutdownBtn.addEventListener('click', async ()=>{
  try{
    shutdownBtn.disabled = true;
    addSystem('Shutting down...');
    await fetch('/api/shutdown', {method:'POST'});
    setStatus('Stopped');
    disableInputs(true);
  }catch(e){ addSystem('Shutdown request failed'); }
});


clearChat.addEventListener('click', ()=>{
  history = []; persist(); chat.innerHTML = ''; setStatus('Ready');
});

toggleAdvanced.addEventListener('click', ()=>{
  if(advanced.classList.contains('hidden')){ advanced.classList.remove('hidden'); toggleAdvanced.textContent='Hide advanced options'; }
  else { advanced.classList.add('hidden'); toggleAdvanced.textContent='Show advanced options'; }
});

// Init
restore();
connectSSE();
fetch('/api/status').then(r=>r.json()).then(j=>setStatus(j.status||''));

