let liveChunkOffset = 0;

function renderExplanationRisk(data) {
  const panel = document.querySelector('#explanationRisk');
  const highest = Math.max(data.factual_risk, data.clarity_risk);
  panel.classList.toggle('elevated', highest >= .55);
  panel.innerHTML = `<p class="eyebrow">TEACHER EXPLANATION RISK</p><strong>${Math.round(data.factual_risk * 100)}% factual · ${Math.round(data.clarity_risk * 100)}% clarity</strong><p>${escapeHtml(data.possible_issue)} ${escapeHtml(data.suggested_check)}</p>`;
}

async function decideNudge(nudgeId, decision, button) {
  const response = await fetch(`/api/sessions/${state.sessionId}/nudges/${nudgeId}/decision`, {
    method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify({decision})
  });
  if (!response.ok) throw new Error('Could not save nudge decision');
  button.parentElement.querySelectorAll('button').forEach(item => item.disabled = true);
  button.parentElement.insertAdjacentHTML('beforeend', `<small>Marked ${escapeHtml(decision)}</small>`);
  await loadOutcomes();
}

function addNudgeControls(data) {
  const panel = document.querySelector('#nudgePanel');
  const controls = document.createElement('div');
  controls.className = 'nudge-actions';
  controls.innerHTML = '<button data-decision="applied">Applied</button><button class="dismiss" data-decision="dismissed">Dismissed</button>';
  controls.querySelectorAll('button').forEach(button => button.onclick = () => decideNudge(data.nudge_id, button.dataset.decision, button).catch(error => toast(error.message)));
  panel.append(controls);
}

async function loadOutcomes() {
  if (!state.sessionId) return;
  const response = await fetch(`/api/sessions/${state.sessionId}/outcomes`);
  if (!response.ok) return;
  const records = await response.json();
  document.querySelector('#outcomeTable tbody').innerHTML = records.length ? records.map(record => {
    const percent = value => value == null ? '—' : `${Math.round(value * 100)}%`;
    const delta = record.correctness_delta == null ? 'Awaiting next poll' : `${record.correctness_delta >= 0 ? '+' : ''}${Math.round(record.correctness_delta * 100)} pts`;
    return `<tr><td>${escapeHtml(record.nudge_id)}</td><td>${escapeHtml(record.decision)}</td><td>${percent(record.baseline_correctness)}</td><td>${percent(record.next_poll_correctness)}</td><td>${delta}</td></tr>`;
  }).join('') : '<tr><td colspan="5" class="waiting">No nudges recorded yet.</td></tr>';
}

async function uploadAudio(blob, offset) {
  const teacher = encodeURIComponent(document.querySelector('#teacherSpeaker').value.trim() || 'speaker_0');
  const response = await fetch(`/api/sessions/${state.sessionId}/audio-chunks?offset_seconds=${offset}&teacher_speaker=${teacher}&filename=classroom.webm`, {method:'POST', headers:{'content-type':blob.type || 'audio/webm'}, body:blob});
  if (!response.ok) { const error = await response.json(); throw new Error(error.detail || 'Transcription failed'); }
  const result = await response.json();
  document.querySelector('#captureStatus').textContent = `Streaming · ${result.segments.length} speaker segment(s) received`;
}

function recordNextWindow() {
  if (!state.capturing) return;
  const audio = new MediaStream(state.mediaStream.getAudioTracks());
  const options = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? {mimeType:'audio/webm;codecs=opus'} : {};
  const recorder = new MediaRecorder(audio, options);
  const chunks = [];
  recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
  recorder.onstop = async () => {
    const offset = liveChunkOffset;
    liveChunkOffset += 6;
    try { await uploadAudio(new Blob(chunks, {type:recorder.mimeType}), offset); }
    catch (error) { toast(error.message); document.querySelector('#captureStatus').textContent = error.message; }
    if (state.capturing) recordNextWindow();
  };
  recorder.start();
  setTimeout(() => { if (recorder.state === 'recording') recorder.stop(); }, 6000);
}

async function startLiveLecture() {
  if (!navigator.mediaDevices || !window.MediaRecorder) throw new Error('This browser does not support media capture');
  if (state.source) state.source.close();
  const response = await fetch('/api/sessions', {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify({fixture_id:document.querySelector('#lessonSelect').value, mode:'live'})});
  if (!response.ok) throw new Error('Could not create live session');
  const session = await response.json();
  connectSession(session.session_id);
  state.mediaStream = await navigator.mediaDevices.getUserMedia({audio:true, video:true});
  document.querySelector('#lecturePreview').srcObject = state.mediaStream;
  state.capturing = true; liveChunkOffset = 0;
  document.querySelector('#startLecture').disabled = true;
  document.querySelector('#stopLecture').disabled = false;
  document.querySelector('#captureStatus').textContent = 'Recording first 6-second audio window…';
  recordNextWindow();
}

async function stopLiveLecture() {
  state.capturing = false;
  state.mediaStream?.getTracks().forEach(track => track.stop());
  document.querySelector('#lecturePreview').srcObject = null;
  document.querySelector('#startLecture').disabled = false;
  document.querySelector('#stopLecture').disabled = true;
  document.querySelector('#captureStatus').textContent = 'Live lecture stopped.';
  if (state.sessionId) await fetch(`/api/sessions/${state.sessionId}/stop`, {method:'POST'});
  await loadOutcomes();
}

document.querySelector('#startLecture').onclick = () => startLiveLecture().catch(error => toast(error.message));
document.querySelector('#stopLecture').onclick = () => stopLiveLecture().catch(error => toast(error.message));

const originalConnectSession = connectSession;
connectSession = function(sessionId) {
  originalConnectSession(sessionId);
  state.source.addEventListener('explanation_risk', event => renderExplanationRisk(JSON.parse(event.data)));
  state.source.addEventListener('nudge', event => addNudgeControls(JSON.parse(event.data)));
  state.source.addEventListener('event', event => {
    const data = JSON.parse(event.data);
    if (data.source === 'live_audio') document.querySelector('.turn:last-child .live-badge').textContent = 'LIVE AUDIO';
  });
  state.source.addEventListener('complete', loadOutcomes);
};
