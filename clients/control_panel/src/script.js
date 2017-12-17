const BPM_CONTAINER = $('#bpm-widget');
const SYNTH_CONTAINER = $('#synth-widget');
const BEAT_CONTAINER = $('#beat-widget');

function wsConnect(name) {
  const wsUrl = path => `ws://${window.location.hostname}:7700/${path}`;
  const ws = new WebSocket(wsUrl(name));
  return ws;
}


const clockWs = wsConnect('clocker');
const bpmWs = wsConnect('metronome_changer');
const drumWs = wsConnect('drummer');
const drumFxWs = wsConnect('fx_reaper');
const outerFxWs = wsConnect('fx_mini_1');
const innerFxWs = wsConnect('fx_mini_2');

makeBpmWidget2(BPM_CONTAINER, bpmWs, clockWs);
makeSynthWidget(SYNTH_CONTAINER, [outerFxWs, innerFxWs]);
makeBeatWidget(BEAT_CONTAINER, drumWs, drumFxWs);
