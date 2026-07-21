const state = {callLocalStream:null, remoteStream:null, sessionId:null, source:null, capturing:false, analysisTracks:[], windowPromise:null, chunkOffset:0, generatedPoll:null, studentProfile:null};
const TRANSCRIPTION_WINDOW_SECONDS=10;
const escapeHtml = value => String(value).replace(/[&<>'"]/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));
function toast(text) { const element=document.querySelector('#toast'); element.textContent=text; element.classList.add('show'); setTimeout(()=>element.classList.remove('show'),2400); }

async function initializeMeeting() {
  const [classes, health] = await Promise.all([fetch('/api/classes').then(response=>response.json()), fetch('/api/health').then(response=>response.json())]);
  document.querySelector('#meetingConcept').innerHTML = classes.map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.title)}</option>`).join('');
  document.querySelector('#meetingMode').textContent = health.llm_mode==='gpt-5.6' ? 'GPT-5.6 live' : 'Demo fallback';
}

function appendTranscript(data) {
  const feed=document.querySelector('#meetingTranscript');
  if(feed.querySelector('p')) feed.innerHTML='';
  feed.insertAdjacentHTML('beforeend',`<div class="meeting-turn"><b>${escapeHtml(data.speaker||'Poll')}</b> ${escapeHtml(data.text||data.question||'')}</div>`);
  feed.scrollTop=feed.scrollHeight;
}

function renderMeetingNudge(data) {
  const panel=document.querySelector('#meetingNudge');
  const memory=data.evidence?.longitudinal_memory;
  const memoryNote=memory?`<p class="memory-note"><b>Memory-informed:</b> ${escapeHtml(memory.summary)} ${escapeHtml(memory.rationale)}</p>`:'';
  panel.className='meeting-card nudge active';
  panel.innerHTML=`<small>TEACHING SUGGESTION · ${escapeHtml(data.strategy.replaceAll('_',' '))}</small><strong>${escapeHtml(data.suggested_reframing)}</strong><p>${escapeHtml(data.trigger_reason)}</p>${memoryNote}<div class="nudge-actions"><button data-value="applied">Confirm applied</button><button data-value="dismissed">Not applied</button></div>`;
  panel.querySelectorAll('button').forEach(button=>button.onclick=async()=>{
    await fetch(`/api/sessions/${state.sessionId}/nudges/${data.nudge_id}/decision`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({decision:button.dataset.value})});
    panel.querySelectorAll('button').forEach(item=>item.disabled=true);
  });
}

function presentGeneratedPoll(data) {
  state.generatedPoll=data;
  const card=document.querySelector('#aiPollCard');
  card.className='meeting-card ai-poll active';
  card.innerHTML=`<small>AI-GENERATED ${escapeHtml(data.stage.toUpperCase())} CHECK · ${escapeHtml(data.llm_mode)}</small><strong>${escapeHtml(data.question)}</strong><p>${data.options.map((option,index)=>`${String.fromCharCode(65+index)}. ${escapeHtml(option)}`).join('<br>')}</p><p>Waiting for the student response · ${escapeHtml(data.checks)}</p>`;
  signal({type:'app_event',payload:{kind:'generated_poll',poll_id:data.poll_id,stage:data.stage,question:data.question,options:data.options}});
}

function showStudentPoll(data) {
  const panel=document.querySelector('#studentPoll');panel.hidden=false;
  document.querySelector('#studentPollQuestion').textContent=data.question;
  document.querySelector('#studentPollStatus').textContent=`${data.stage} check · choose one answer`;
  const options=document.querySelector('#studentPollOptions');
  options.innerHTML=data.options.map((option,index)=>`<button data-index="${index}">${escapeHtml(option)}</button>`).join('');
  options.querySelectorAll('button').forEach(button=>button.onclick=()=>{
    options.querySelectorAll('button').forEach(item=>item.disabled=true);
    button.style.borderColor='var(--teal)';document.querySelector('#studentPollStatus').textContent='Answer submitted';
    signal({type:'app_event',payload:{kind:'poll_response',poll_id:data.poll_id,selected_index:Number(button.dataset.index)}});
  });
}

async function gradeStudentPoll(data) {
  const poll=state.generatedPoll;if(!poll||poll.poll_id!==data.poll_id)return;
  const correct=data.selected_index===poll.correct_index;
  const studentId=state.studentProfile?.subject_id||'student';
  const response=await fetch(`/api/sessions/${state.sessionId}/polls`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({question:poll.question,responses:{[studentId]:correct}})});
  if(!response.ok)throw new Error('Could not record student poll response');
  const card=document.querySelector('#aiPollCard');
  card.insertAdjacentHTML('beforeend',`<p><b>${correct?'Correct':'Incorrect'}</b> · ${escapeHtml(poll.explanation)}</p>`);
}

function connectAnalysis(sessionId) {
  state.source?.close(); state.sessionId=sessionId;
  state.source=new EventSource(`/stream/${sessionId}?speed=1`);
  state.source.addEventListener('event',event=>appendTranscript(JSON.parse(event.data)));
  state.source.addEventListener('ccs',event=>{const data=JSON.parse(event.data);document.querySelector('#meetingCCS').textContent=data.score.toFixed(2);document.querySelector('#meetingCCSLabel').textContent=(data.state||'calm').toUpperCase();document.querySelector('#meetingEvidence').textContent=`${Math.round((data.evidence_quality||0)*100)}% evidence quality`;});
  state.source.addEventListener('mastery',event=>{const students=JSON.parse(event.data).students;if(!students.length)return;document.querySelector('#meetingMastery').textContent=`${Math.round(students.reduce((sum,item)=>sum+item.mastery,0)/students.length*100)}%`;});
  state.source.addEventListener('explanation_risk',event=>{const data=JSON.parse(event.data),panel=document.querySelector('#meetingRisk');panel.classList.toggle('elevated',Math.max(data.factual_risk,data.clarity_risk)>=.55);panel.innerHTML=`<small>EXPLANATION RISK</small><strong>${Math.round(data.factual_risk*100)}% factual · ${Math.round(data.clarity_risk*100)}% clarity</strong><p>${escapeHtml(data.possible_issue)} ${escapeHtml(data.suggested_check)}</p>`;});
  state.source.addEventListener('nudge',event=>renderMeetingNudge(JSON.parse(event.data)));
  state.source.addEventListener('implementation_verification',event=>{const data=JSON.parse(event.data),panel=document.querySelector('#meetingNudge');panel.querySelector('.implementation-check')?.remove();panel.insertAdjacentHTML('beforeend',`<p class="implementation-check"><b>Implementation: ${escapeHtml(data.implementation_status.replaceAll('_',' '))}</b> · ${Math.round((data.implementation_confidence||0)*100)}%<br>${escapeHtml(data.implementation_evidence||data.implementation_rationale)}</p>`);});
  state.source.addEventListener('generated_poll',event=>presentGeneratedPoll(JSON.parse(event.data)));
  state.source.addEventListener('model_error',event=>toast(`${JSON.parse(event.data).operation} unavailable`));
}

function buildAnalysisTracks(){
  const teacherTrack=state.callLocalStream?.getAudioTracks()[0],studentTrack=state.remoteStream?.getAudioTracks()[0];
  if(!teacherTrack||!studentTrack)throw new Error('Both audio tracks are required');
  return [
    {role:'teacher',subjectId:callState.profile.subject_id,stream:new MediaStream([teacherTrack])},
    {role:'student',subjectId:state.studentProfile.subject_id,stream:new MediaStream([studentTrack])},
  ];
}

function captureTrackWindow(source) {
  const options=MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?{mimeType:'audio/webm;codecs=opus'}:{};
  return new Promise(resolve=>{const recorder=new MediaRecorder(source.stream,options),chunks=[];recorder.ondataavailable=event=>{if(event.data.size)chunks.push(event.data);};recorder.onstop=()=>resolve({source,blob:new Blob(chunks,{type:recorder.mimeType})});recorder.start();setTimeout(()=>{if(recorder.state==='recording')recorder.stop();},TRANSCRIPTION_WINDOW_SECONDS*1000);});
}

async function recordMeetingWindow() {
  if(!state.capturing)return;
  const offset=state.chunkOffset;state.chunkOffset+=TRANSCRIPTION_WINDOW_SECONDS;
  try{
    const captures=await Promise.all(state.analysisTracks.map(captureTrackWindow));
    await Promise.all(captures.map(async({source,blob})=>{
      const role=encodeURIComponent(source.role),speaker=encodeURIComponent(source.subjectId);
      const response=await fetch(`/api/sessions/${state.sessionId}/audio-chunks?offset_seconds=${offset}&known_role=${role}&known_speaker_id=${speaker}&filename=${role}.webm`,{method:'POST',headers:{'content-type':blob.type},body:blob});
      if(!response.ok)throw new Error((await response.json()).detail||`${source.role} transcription failed`);
    }));
    document.querySelector('#analysisStatus').textContent=`Streaming separate teacher + student audio · ${TRANSCRIPTION_WINDOW_SECONDS} s windows`;
  }catch(error){toast(error.message);}
  if(state.capturing)state.windowPromise=recordMeetingWindow();
}

async function startMeetingAnalysis() {
  if(!state.callLocalStream||!state.remoteStream) throw new Error('Connect both participants first');
  if(!callState.profile||callState.role!=='teacher'||!state.studentProfile)throw new Error('Teacher and student identities must be connected');
  const response=await fetch('/api/sessions',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({fixture_id:document.querySelector('#meetingConcept').value,mode:'live',teacher_id:callState.profile.subject_id,teacher_name:callState.profile.display_name,student_id:state.studentProfile.subject_id,student_name:state.studentProfile.display_name})});
  if(!response.ok) throw new Error('Could not start analysis');
  const session=await response.json(); connectAnalysis(session.session_id);
  state.analysisTracks=buildAnalysisTracks(); state.capturing=true; state.chunkOffset=0;
  document.querySelector('#analysisStart').disabled=true;document.querySelector('#analysisStop').disabled=false;document.querySelector('#analysisStatus').textContent='Recording first audio window…';state.windowPromise=recordMeetingWindow();
}

async function stopMeetingAnalysis() {
  state.capturing=false;await state.windowPromise;state.windowPromise=null;state.analysisTracks=[];
  if(state.sessionId) await fetch(`/api/sessions/${state.sessionId}/stop`,{method:'POST'});
  document.querySelector('#analysisStart').disabled=false;document.querySelector('#analysisStop').disabled=true;document.querySelector('#analysisStatus').textContent='Analysis stopped';
  await loadPerformance();
}

async function loadPerformance(){
  if(!callState.profile||callState.role!=='teacher')return;
  const [teacher,student]=await Promise.all([
    fetch(`/api/performance/teacher/${encodeURIComponent(callState.profile.subject_id)}`).then(r=>r.ok?r.json():null),
    state.studentProfile?fetch(`/api/performance/student/${encodeURIComponent(state.studentProfile.subject_id)}`).then(r=>r.ok?r.json():null):null,
  ]);
  const card=document.querySelector('#performanceCard');
  const concepts=student?.concepts||[], strategies=teacher?.strategies||{};
  const latest=concepts.length?concepts.map(x=>`${escapeHtml(x.concept)} ${Math.round(x.mastery*100)}%`).join(' · '):'No learner evidence yet';
  const teaching=Object.entries(strategies).length?Object.entries(strategies).map(([name,x])=>`${escapeHtml(name.replaceAll('_',' '))}: ${x.implemented}/${x.attempts} implemented${x.mean_observed_delta===null?'':`, ${x.mean_observed_delta>=0?'+':''}${Math.round(x.mean_observed_delta*100)} pts`}`).join('<br>'):'No completed teaching outcomes yet';
  card.innerHTML=`<small>SAVED PERFORMANCE · PSEUDONYMOUS</small><strong>${escapeHtml(student?.display_name||state.studentProfile?.display_name||'Student')}: ${latest}</strong><p>${teaching}</p><p>Observed changes are not causal proof of teaching improvement.</p>`;
}

document.querySelector('#analysisStart').onclick=()=>startMeetingAnalysis().catch(error=>toast(error.message));
document.querySelector('#analysisStop').onclick=()=>stopMeetingAnalysis().catch(error=>toast(error.message));
window.addEventListener('call_app_event',event=>{const data=event.detail;if(data.kind==='participant_profile'&&data.role==='student'){state.studentProfile=data;if(callState.role==='teacher')loadPerformance().catch(()=>{});}if(data.kind==='generated_poll'&&document.body.dataset.role==='student')showStudentPoll(data);if(data.kind==='poll_response'&&document.body.dataset.role==='teacher')gradeStudentPoll(data).catch(error=>toast(error.message));});
initializeMeeting().catch(error=>toast(error.message));
