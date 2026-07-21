const callState = {socket:null, peer:null, localStream:null, remoteStream:null, role:null, room:null, participant:null, pendingIce:[]};

function callStatus(message, connected=false) {
  const element = document.querySelector('#callStatus');
  element.textContent = message;
  element.classList.toggle('connected', connected);
}

function callCode() {
  return Math.random().toString(36).slice(2,8).toUpperCase();
}

async function ensureCallMedia() {
  if (callState.localStream) return callState.localStream;
  callState.localStream = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
  state.callLocalStream = callState.localStream;
  document.querySelector('#localVideo').srcObject = callState.localStream;
  return callState.localStream;
}

function signal(payload) {
  if (callState.socket?.readyState === WebSocket.OPEN) callState.socket.send(JSON.stringify(payload));
}

async function flushIce() {
  if (!callState.peer?.remoteDescription) return;
  for (const candidate of callState.pendingIce.splice(0)) await callState.peer.addIceCandidate(candidate);
}

async function makePeer() {
  callState.peer?.close();
  const peer = new RTCPeerConnection({iceServers:[{urls:'stun:stun.l.google.com:19302'}]});
  callState.peer = peer;
  (await ensureCallMedia()).getTracks().forEach(track => peer.addTrack(track, callState.localStream));
  peer.onicecandidate = event => { if (event.candidate) signal({type:'ice', candidate:event.candidate}); };
  peer.ontrack = event => {
    callState.remoteStream = event.streams[0];
    state.remoteStream = callState.remoteStream;
    document.querySelector('#remoteVideo').srcObject = callState.remoteStream;
    if (callState.role === 'teacher') document.querySelector('#analysisStart').disabled = false;
    callStatus(`Connected · ${callState.role} · room ${callState.room} · 2/2 participants`, true);
  };
  peer.onconnectionstatechange = () => {
    if (['failed','disconnected','closed'].includes(peer.connectionState)) callStatus(`Peer ${peer.connectionState} · room ${callState.room}`);
  };
  return peer;
}

async function handleSignal(message) {
  if (message.type === 'joined') {
    callStatus(`${callState.role === 'teacher' ? 'Room created' : 'Joined'} · ${callState.room} · waiting for ${message.peers.length ? 'connection' : 'second participant'}`, true);
    if (callState.role === 'student') signal({type:'ready'});
    return;
  }
  if (message.type === 'ready' && callState.role === 'teacher') {
    const peer = await makePeer();
    await peer.setLocalDescription(await peer.createOffer());
    signal({type:'offer', sdp:peer.localDescription});
  } else if (message.type === 'offer' && callState.role === 'student') {
    const peer = await makePeer();
    await peer.setRemoteDescription(message.sdp);
    await flushIce();
    await peer.setLocalDescription(await peer.createAnswer());
    signal({type:'answer', sdp:peer.localDescription});
  } else if (message.type === 'answer' && callState.role === 'teacher') {
    await callState.peer.setRemoteDescription(message.sdp);
    await flushIce();
  } else if (message.type === 'ice') {
    if (callState.peer?.remoteDescription) await callState.peer.addIceCandidate(message.candidate);
    else callState.pendingIce.push(message.candidate);
  } else if (message.type === 'peer_left') {
    document.querySelector('#remoteVideo').srcObject = null;
    callState.remoteStream = null; state.remoteStream = null;
    callStatus(`Other participant left · room ${callState.room}`);
  } else if (message.type === 'error') {
    throw new Error(message.message);
  }
}

async function joinDemoCall(role) {
  if (!navigator.mediaDevices || !window.RTCPeerConnection) throw new Error('This browser does not support WebRTC calls');
  if (callState.socket) leaveDemoCall();
  const input = document.querySelector('#callRoom');
  const room = (role === 'teacher' ? (input.value.trim() || callCode()) : input.value.trim()).toUpperCase().replace(/[^A-Z0-9-]/g,'');
  if (!room) throw new Error('Enter the teacher room code');
  input.value = room;
  callState.role = role; callState.room = room;
  document.body.dataset.role = role;
  document.querySelector('#teacherInsights').hidden = role !== 'teacher';
  document.querySelector('.meeting-shell').style.gridTemplateColumns = role === 'teacher' ? '' : '1fr';
  callState.participant = `${role}-${Math.random().toString(36).slice(2,7)}`;
  await ensureCallMedia();
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const socket = new WebSocket(`${protocol}://${location.host}/ws/calls/${encodeURIComponent(room)}/${encodeURIComponent(callState.participant)}`);
  callState.socket = socket;
  socket.onmessage = event => handleSignal(JSON.parse(event.data)).catch(error => { callStatus(error.message); toast(error.message); });
  socket.onclose = event => { if (callState.socket === socket) callStatus(event.reason || 'Call signaling closed'); };
  socket.onerror = () => callStatus('Could not connect to call signaling');
  document.querySelector('#createCall').disabled = true;
  document.querySelector('#joinCall').disabled = true;
  document.querySelector('#leaveCall').disabled = false;
}

function leaveDemoCall() {
  if (state.capturing && typeof stopMeetingAnalysis === 'function') stopMeetingAnalysis().catch(error => toast(error.message));
  callState.socket?.close(); callState.peer?.close();
  callState.localStream?.getTracks().forEach(track => track.stop());
  Object.assign(callState, {socket:null, peer:null, localStream:null, remoteStream:null, role:null, room:null, participant:null, pendingIce:[]});
  state.callLocalStream = null; state.remoteStream = null;
  document.querySelector('#localVideo').srcObject = null;
  document.querySelector('#remoteVideo').srcObject = null;
  document.querySelector('#createCall').disabled = false;
  document.querySelector('#joinCall').disabled = false;
  document.querySelector('#leaveCall').disabled = true;
  document.querySelector('#teacherInsights').hidden = true;
  document.querySelector('.meeting-shell').style.gridTemplateColumns = '';
  document.body.removeAttribute('data-role');
  callStatus('No call joined · maximum 2 participants');
}

document.querySelector('#createCall').onclick = () => joinDemoCall('teacher').catch(error => { callStatus(error.message); toast(error.message); });
document.querySelector('#joinCall').onclick = () => joinDemoCall('student').catch(error => { callStatus(error.message); toast(error.message); });
document.querySelector('#leaveCall').onclick = leaveDemoCall;
