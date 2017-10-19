let controlsEl, kindEl, pitchEl, deployEl;

const hn = window.location.hostname;
let ws = new WebSocket(`ws://${hn}:7700`);
ws.onmessage = function(msg) {
  const data = msg.data;
  if (data.kind === 'ping') {
    ws.send(JSON.stringify({
      kind: 'pong'
    }));
  }
};

let pitch = 0;
let kind = 0;
let state = 0;


function drawKind() {
  kindEl.select('#kind-control').remove();
  let el;
  if (kind === 0)
    el = kindEl.append('rect').attr('width', '30').attr('height', '30');
  if (kind === 1)
    el = kindEl.append('circle').attr('r', '15');

  el.attr('id', 'kind-control');
}

function drawPitch() {
  pitchEl.select('#pitch-control').remove();
  pitchEl.append('text').attr('id', 'pitch-control').text(pitch);
}


function drawDeploy() {
  deployEl.append('circle').attrs({
    r: 40,
    cy: 30
  });
}

function handlers() {
  pitchEl.on('click', changePitch);
  kindEl.on('click', changeKind);
  deployEl.on('click', doDeploy);
}

function changePitch() {
  pitch = (pitch + 1) % 7;
  drawPitch();
}

function changeKind() {
  kind = (kind + 1) % 2;
  drawKind();
}

function doDeploy() {
  ws.send(JSON.stringify({
    kind: 'create',
    payload: {
      pitch,
      kind
    }
  }));
  gotoGameState();
}

function gotoGameState() {
  state = 1;
  controlsEl.remove();
  const bigButton = d3.select('#controls-svg')
        .append('g')
        .append('circle')
        .attrs({
          cx: 40,
          cy: 40,
          r: 30,
          fill: 'white'
        });
  bigButton.on('click', ding);
  //bigButton.on('touchstart', ding);
}

function ding() {
  ws.send(JSON.stringify({
    kind: 'ding'
  }));
}

function main() {
  setup();
}

function setup() {
  controlsEl = d3.select('#controls-svg').append('g');

  kindEl = controlsEl
    .append('g')
    .attr('id', 'kind')
    .attr('transform', 'translate(15 15)');
  pitchEl = controlsEl
    .append('g')
    .attr('id', 'pitch')
    .attr('transform', 'translate(80 15)');

  deployEl = controlsEl
    .append('g')
    .attr('id', 'deploy')
    .attr('transform', 'translate(220, 15)');

  drawKind();
  drawPitch();
  drawDeploy();
  handlers();
}

$(function() {
  main();
});
