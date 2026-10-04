const $ = (s) => document.querySelector(s);
const form = $('#match-form');
function esc(s=''){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function render(data){
  $('#match-count').textContent=`${data.matches} ${data.matches===1?'match':'matches'} logged`;
  if(!data.matches)return;
  $('#focus-text').textContent=`Next up: ${data.focus}.`;
  $('#focus-note').textContent='A small, focused drill in your next session can turn this into progress.';
  const latest=data.trend[data.trend.length-1];
  $('#match-opponent').textContent=`${latest.opponent||'Latest match'}${latest.date?' · '+latest.date:''}`;
  const scores=data.scores||{};
  $('#scores').innerHTML=Object.entries(scores).map(([name,n])=>`<div class="score-row"><span>${esc(name)}</span><div class="bar"><i style="width:${Math.min(100,n)}%"></i></div><b>${n}%</b></div>`).join('');
  const note=latest.self_note?` Your note: “${latest.self_note}”`:'';
  $('#chat-response').textContent=`Latest match logged. Your pass accuracy was ${data.latest_metrics.pass_accuracy}% and ${data.latest_metrics.shot_accuracy}% of shots were on target. Your next focus is ${data.focus}.${note}`;
}
async function refresh(){try{const r=await fetch('/api/analysis');render(await r.json())}catch{}}
form.addEventListener('submit',async e=>{e.preventDefault();const status=$('#form-status');status.textContent='Saving…';const raw=Object.fromEntries(new FormData(form));for(const k of ['minutes','goals','assists','shots','shots_on_target','passes_attempted','passes_completed','tackles'])raw[k]=Number(raw[k]);try{const r=await fetch('/api/matches',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(raw)});const data=await r.json();if(!r.ok)throw Error(data.detail||'Could not save match');render(data.analysis);status.textContent='Match saved — your snapshot is up to date.';$('#chat-response').textContent=`Match saved! Your pass accuracy was ${data.analysis.latest_metrics.pass_accuracy}% and your next focus is ${data.analysis.focus}. Ask me for a drill below.`;form.elements.opponent.value='';form.elements.self_note.value='';}catch(err){status.textContent=err.message}});
$('#csv-upload').addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;const body=new FormData();body.append('file',file);$('#form-status').textContent='Importing…';try{const r=await fetch('/api/import',{method:'POST',body});const d=await r.json();if(!r.ok)throw Error(d.detail);render(d.analysis);$('#form-status').textContent=`Imported ${d.imported} match${d.imported===1?'':'es'}.`}catch(err){$('#form-status').textContent=err.message}e.target.value=''});
$('#chat-form').addEventListener('submit',async e=>{e.preventDefault();const input=e.currentTarget.elements.question;const q=input.value.trim();if(!q)return;$('#chat-response').textContent='Thinking through your match data…';$('#source-label').textContent='';try{const r=await fetch('/api/coach',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});const d=await r.json();if(!r.ok)throw Error(d.detail);$('#chat-response').textContent=d.answer;$('#source-label').textContent=`Answered by ${d.source}`;input.value=''}catch(err){$('#chat-response').textContent=err.message}});
document.querySelectorAll('[data-q]').forEach(b=>b.addEventListener('click',()=>{const input=$('#chat-form [name=question]');input.value=b.dataset.q;$('#chat-form').requestSubmit()}));
refresh();
