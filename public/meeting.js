const state = {callLocalStream:null, remoteStream:null, sessionId:null, source:null, capturing:false, mediaStream:null, audioContext:null, chunkOffset:0};
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
  panel.className='meeting-card nudge active';
  panel.innerHTML=`<small>TEACHING SUGGESTION · ${escapeHtml(data.strategy.replaceAll('_',' '))}</small><strong>${escapeHtml(data.suggested_reframing)}</strong><p>${escapeHtml(data.trigger_reason)}</p><div class="nudge-actions"><button data-value="applied">Confirm applied</button><button data-value="dismissed">Not applied</button></div>`;
  panel.querySelectorAll('button').forEach(button=>button.onclick=async()=>{
    await fetch(`/api/sessions/${state.sessionId}/nudges/${data.nudge_id}/decision`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({decision:button.dataset.value})});
    panel.querySelectorAll('button').forEach(item=>item.disabled=true);
  });
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
  state.source.addEventListener('model_error',event=>toast(`${JSON.parse(event.data).operation} unavailable`));
}

function buildAnalysisStream() {
  const context=new AudioContext(), destination=context.createMediaStreamDestination();
  context.createMediaStreamSource(state.callLocalStream).connect(destination);
  if(state.remoteStream?.getAudioTracks().length) context.createMediaStreamSource(state.remoteStream).connect(destination);
  state.audioContext=context;
  return new MediaStream(destination.stream.getAudioTracks());
}

function recordMeetingWindow() {
  if(!state.capturing) return;
  const options=MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?{mimeType:'audio/webm;codecs=opus'}:{};
  const recorder=new MediaRecorder(state.mediaStream,options), chunks=[];
  recorder.ondataavailable=event=>{if(event.data.size)chunks.push(event.data);};
  recorder.onstop=async()=>{
    const offset=state.chunkOffset; state.chunkOffset+=6;
    try {
      const blob=new Blob(chunks,{type:recorder.mimeType}), teacher=encodeURIComponent(document.querySelector('#teacherSpeaker').value||'speaker_0');
      const response=await fetch(`/api/sessions/${state.sessionId}/audio-chunks?offset_seconds=${offset}&teacher_speaker=${teacher}&filename=call.webm`,{method:'POST',headers:{'content-type':blob.type},body:blob});
      if(!response.ok) throw new Error((await response.json()).detail||'Transcription failed');
      document.querySelector('#analysisStatus').textContent='Streaming call audio';
    } catch(error) { toast(error.message); }
    if(state.capturing) recordMeetingWindow();
  };
  recorder.start(); setTimeout(()=>{if(recorder.state==='recording')recorder.stop();},6000);
}

async function startMeetingAnalysis() {
  if(!state.callLocalStream||!state.remoteStream) throw new Error('Connect both participants first');
  const response=await fetch('/api/sessions',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({fixture_id:document.querySelector('#meetingConcept').value,mode:'live'})});
  if(!response.ok) throw new Error('Could not start analysis');
  const session=await response.json(); connectAnalysis(session.session_id);
  state.mediaStream=buildAnalysisStream(); state.capturing=true; state.chunkOffset=0;
  document.querySelector('#analysisStart').disabled=true;document.querySelector('#analysisStop').disabled=false;document.querySelector('#meetingSendPoll').disabled=false;document.querySelector('#analysisStatus').textContent='Recording first audio window…';recordMeetingWindow();
}

async function stopMeetingAnalysis() {
  state.capturing=false;state.mediaStream?.getTracks().forEach(track=>track.stop());await state.audioContext?.close();
  if(state.sessionId) await fetch(`/api/sessions/${state.sessionId}/stop`,{method:'POST'});
  document.querySelector('#analysisStart').disabled=false;document.querySelector('#analysisStop').disabled=true;document.querySelector('#meetingSendPoll').disabled=true;document.querySelector('#analysisStatus').textContent='Analysis stopped';
}

async function sendMeetingPoll() {
  const total=Number(document.querySelector('#meetingPollTotal').value),correct=Number(document.querySelector('#meetingPollCorrect').value),question=document.querySelector('#meetingPollQuestion').value.trim();
  if(!question||correct<0||total<1||correct>total) throw new Error('Enter a valid poll result');
  const responses={};for(let index=0;index<total;index++)responses[`Live learner ${index+1}`]=index<correct;
  const response=await fetch(`/api/sessions/${state.sessionId}/polls`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({question,responses})});
  if(!response.ok) throw new Error('Could not submit poll');toast('Poll submitted');
}

document.querySelector('#analysisStart').onclick=()=>startMeetingAnalysis().catch(error=>toast(error.message));
document.querySelector('#analysisStop').onclick=()=>stopMeetingAnalysis().catch(error=>toast(error.message));
document.querySelector('#meetingSendPoll').onclick=()=>sendMeetingPoll().catch(error=>toast(error.message));
initializeMeeting().catch(error=>toast(error.message));
