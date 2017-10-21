let controlsEl,
    kindEl,
    pitchEl,
    deployEl,
    bugViewerEl,
    controllerEl;

let timer;

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

// Model
var t = d3.transition()
    .duration(100)
    .ease(d3.easeLinear);

const Bug = {
  pitch: 0,
  kind: 0,
  pk: ''
};

const State = {
  mode: 'creating',
  bug: Bug
};




function drawKind() {
  kindEl.select('#kind-control').remove();
  let el;
  if (Bug.kind === 0)
    el = kindEl.append('rect').attr('width', '30').attr('height', '30');
  if (Bug.kind === 1)
    el = kindEl.append('circle').attr('r', '15');

  el.attr('id', 'kind-control');
}

function drawPitch() {
  pitchEl.select('#pitch-control').remove();
  pitchEl.append('text').attr('id', 'pitch-control').text(pitch);
}


function handlers() {
  $('#deploy-button').on('click', doDeploy);

  $('#bug-options').children().on('click touchstart', function(e) {
    e.preventDefault();
    const id = $(this).attr('id').split('-')[1];
    console.log(id);
    selectBugKind(id);
  });

  $('#pitches').children().on('click touchstart', function(e) {
    e.preventDefault();
    const id = $(this).attr('id').split('-')[1];
    selectPitch(+id);
  });
}

function selectPitch(id) {
  Bug.pitch = id;
  drawPitchSelector();
}

function drawPitchSelector() {
  $('#pitches').children().removeClass('selected');
  $('#pitch-' + Bug.pitch).addClass('selected');
}

function selectBugKind(id) {
  Bug.kind = +id;
  drawBugSelector();
  drawBug();
}

function drawBugSelector() {
  $('#bug-options').children().removeClass('selected');
  $('#bug-' + Bug.kind).addClass('selected');

  d3.select('#bug-0 svg').classed('bug-svg', true).html(OCTO_BUG);
  d3.select('#bug-1 svg').classed('bug-svg', true).html(SPIRAL_BUG);
  d3.select('#bug-2 svg').classed('bug-svg', true).html(LONG_BUG);
}

function drawBug() {
  bugViewerEl.select('g.bug-svg').remove();
  const el = bugViewerEl
        .append('g')
        .attr('id', 'bug-viz')
        .classed('bug-svg', true);
  switch (Bug.kind) {
  case 0:
    el.html(OCTO_BUG);
    break;
  case 1:
    el.html(SPIRAL_BUG);
    break;
  case 2:
    el.html(LONG_BUG);
    break;
  }
  new Vivus('bug-viz', {
    duration: 50,
    type: 'sync'
  });
}

function doDeploy() {
  ws.send(JSON.stringify({
    kind: 'create',
    payload: {
      pitch: +Bug.pitch,
      kind: +Bug.kind
    }
  }));
  gotoGameState();
}

function gotoGameState() {
  State.mode = 1;

  // blank out creation screen
  d3.select('#creation').style('display', 'none');

  const controller = d3.select('#controller');
  controller.style('display', 'block');

  const length = 45 * 1000;
  timer = d3.timer(function(elapsed) {
    if (elapsed > length) {
      die();
    }
    else {
      const newDegree = elapsed / (length) * 360;
      d3.select('#radial-path').attr('d', arcTo(newDegree));
    }
  }, 0);
}

function die() {
  timer.stop();
  ws.send(JSON.stringify({kind: 'die'}));
  State.mode = 0;
  gotoCreationScreen();
  Bug.kind = 0;
  Bug.pitch = 0;
}

function gotoCreationScreen() {
  d3.select('#controller').style('display', 'none');
  d3.select('#creation').style('display', 'block');
}



function arcTo(x) {
  return describeArc(50, 50, 40, x, 360);
}

function drawController() {
  const bigButton = controllerEl
        .append('circle')
        .attrs({
          id: 'ding-button',
          cx: 50,
          cy: 50,
          r: 30,
          fill: 'rgb(255,251,227)'
        });
  const dieButton = controllerEl
        .append('circle')
        .attrs({
          id: 'die-button',
          cx: 50,
          cy: 130,
          r: 15,
          fill: 'rgb(181,16,19)'
        });
  const radialTimer = controllerEl
        .append('path')
        .attrs({
          id: 'radial-path',
          d: describeArc(50, 50, 40, 0, 360),
          fill: 'none',
          stroke: 'rgb(128,203,196)',
          'stroke-width': '3px'
        });
  bigButton.on('click', ding);
  dieButton.on('click', die);
}

function ding() {
  ws.send(JSON.stringify({
    kind: 'ding'
  }));
  d3.select('#ding-button').attr('fill', 'rgb(128, 203, 196)');

  setTimeout(function () {
    d3.select('#ding-button').attr('fill', 'rgb(255, 251, 227)');
  }, 200);
}

function main() {
  setup();
}

function setup() {
  controlsEl = d3.select('#controls-svg').append('g');
  controllerEl = d3.select('#controller-svg').append('g');
  pitchEl = controlsEl
    .append('g')
    .attr('id', 'pitch')
    .attr('transform', 'translate(80 15)');

  deployEl = controlsEl
    .append('g')
    .attr('id', 'deploy')
    .attr('transform', 'translate(220, 15)');

  const bv = d3.select('#bug-viewer');
  const bvBox = bv.node().getBoundingClientRect();
  bugViewerEl = bv.select('svg')
    .attr('height', bvBox.width - 30)
    .attr('width', bvBox.width - 30);

  bv.style('height', bvBox.width);

  drawBug();
  drawPitchSelector();
  drawBugSelector();
  drawController();
  verticalize();
  handlers();
}

function verticalize() {
  $('.pitch-box').each(function() {
    const x = $(this);
    const text = x.text();
    x.text('');
    text.split('').forEach(letter => x.append('<div>'+letter+'</div>'));
  })
}
$(function() {
  main();
});

const OCTO_BUG = `
<g id="octo-bug">
<polygon class="st0" points="50,1.6 62.1,20.7 84.2,15.8 79.3,37.9 98.4,50 79.3,62.1 84.2,84.2 62.1,79.3 50,98.4 37.9,79.3
      15.8,84.2 20.7,62.1 1.6,50 20.7,37.9 15.8,15.8 37.9,20.7    "/>
    <polygon class="st1" points="50,15.7 62.1,20.7 74.3,25.7 79.3,37.9 84.3,50 79.3,62.1 74.3,74.3 62.1,79.3 50,84.3 37.9,79.3
      25.7,74.3 20.7,62.1 15.7,50 20.7,37.9 25.7,25.7 37.9,20.7     "/>
    <circle class="st2" cx="37.9" cy="20.7" r="1.6"/>
    <circle class="st2" cx="15.8" cy="15.8" r="1.6"/>
    <circle class="st2" cx="20.7" cy="37.9" r="1.6"/>
    <circle class="st2" cx="1.6" cy="50" r="1.6"/>
    <circle class="st2" cx="20.7" cy="62.1" r="1.6"/>
    <circle class="st2" cx="15.8" cy="84.2" r="1.6"/>
    <circle class="st2" cx="37.9" cy="79.3" r="1.6"/>
    <circle class="st2" cx="50" cy="98.4" r="1.6"/>
    <circle class="st2" cx="62.1" cy="79.3" r="1.6"/>
    <circle class="st2" cx="84.2" cy="84.2" r="1.6"/>
    <circle class="st2" cx="79.3" cy="62.1" r="1.6"/>
    <circle class="st2" cx="98.4" cy="50" r="1.6"/>
    <circle class="st2" cx="79.3" cy="37.9" r="1.6"/>
    <circle class="st2" cx="84.2" cy="15.8" r="1.6"/>
    <circle class="st2" cx="62.1" cy="20.7" r="1.6"/>
    <circle class="st2" cx="50" cy="1.6" r="1.6"/>
    <polygon class="st0" points="50,35.5 55.1,37.7 60.2,39.8 62.3,44.9 64.5,50 62.3,55.1 60.2,60.2 55.1,62.3 50,64.5 44.9,62.3
      39.8,60.2 37.7,55.1 35.5,50 37.7,44.9 39.8,39.8 44.9,37.7     "/>
    <circle class="st2" cx="57.6" cy="50" r="1.6"/>
    <circle class="st2" cx="50" cy="57.6" r="1.6"/>
    <circle class="st2" cx="42.4" cy="50" r="1.6"/>
    <circle class="st2" cx="50" cy="42.4" r="1.6"/>
</g>
`

const SPIRAL_BUG = `
  <g id="spiral-bug">
    <path class="st0" d="M76.1,76.6c2.8-3.2,5.1-6.9,6.6-11c5.5-14.5,0.9-30.9-11.4-40.5c-12.4-9.6-29.9-8.7-41.3,2.1
      c-3.1,2.9-5.6,6.6-7.2,10.6C18,50.3,22.3,64.5,33.3,72c3.6,2.4,7.7,3.9,12,4.2c2.1,0.2,4.3,0.1,6.4-0.2c2.1-0.3,4.2-0.9,6.2-1.8
      c4-1.7,7.4-4.4,10.1-7.8c2.7-3.4,4.3-7.5,4.7-11.8c0.7-6.5-1.4-13-5.7-17.9c-0.3-0.4-0.7-0.8-1.1-1.2s-0.8-0.7-1.2-1.1
      c-0.8-0.7-1.7-1.3-2.6-1.9c-7.6-4.7-17.2-4-24.1,1.5c-1.7,1.4-3.1,3-4.3,4.8c-3.6,5.6-4,12.6-1.1,18.5c1.9,3.9,5.1,7,9.1,8.8
      c4,1.7,8.5,1.8,12.6,0.3c4.1-1.5,7.4-4.6,9.3-8.5c2.7-6.1,1.2-13.3-3.8-17.7c-1.6-1.4-3.6-2.4-5.8-2.7c-2.1-0.3-4.3-0.1-6.4,0.6
      c-2.1,0.7-3.9,1.9-5.4,3.5c-0.7,0.8-1.3,1.7-1.8,2.7c-0.5,1-0.8,2-1,3.1c-0.2,1.1-0.3,2.1-0.1,3.2c0.1,1.1,0.5,2.1,1,3.1
      c1.1,1.9,2.6,3.5,4.3,4.8c0.8,0.7,1.8,1.1,2.9,1.4c1.1,0.2,2.2,0.1,3.2-0.2c1-0.3,2-0.8,2.9-1.5c0.4-0.3,0.8-0.7,1.2-1.1
      c0.4-0.4,0.7-0.8,1-1.2c1.1-1.9,1.5-4.1,1.2-6.2c-0.2-1.1-0.5-2.1-1.1-3c-0.6-0.9-1.4-1.7-2.4-2.1c-1-0.4-2.1-0.6-3.2-0.4
      c-1.1,0.1-2.1,0.6-2.9,1.3c0.8-0.8,1.8-1.2,2.9-1.3c1.1-0.2,2.2,0,3.2,0.4c1,0.4,1.9,1.2,2.4,2.1c0.6,0.9,0.9,2,1.1,3
      c0.4,2.2,0,4.4-1.1,6.3c-0.3,0.4-0.7,0.9-1.1,1.2c-0.4,0.4-0.8,0.7-1.2,1.1c-0.9,0.7-1.8,1.2-2.9,1.5c-1,0.3-2.2,0.4-3.2,0.2
      c-1.1-0.2-2.1-0.7-2.9-1.4c-1.8-1.3-3.3-2.9-4.4-4.8c-0.5-1-0.9-2-1-3.1c-0.1-1.1-0.1-2.2,0.1-3.3c0.2-1.1,0.6-2.1,1.1-3.1
      c0.4-1,1-1.9,1.8-2.7c1.5-1.6,3.4-2.8,5.4-3.5c2.1-0.7,4.3-0.9,6.5-0.6c2.2,0.3,4.2,1.3,5.9,2.7c5.1,4.5,6.6,11.8,3.9,18
      c-1.9,4-5.2,7.1-9.4,8.7c-4.1,1.6-8.7,1.5-12.8-0.2c-4.1-1.8-7.3-4.9-9.3-8.9c-1-2-1.6-4.1-1.9-6.3c-0.5-4.4,0.5-8.8,2.9-12.6
      c1.2-1.8,2.7-3.5,4.4-4.9c7-5.7,16.9-6.3,24.6-1.6c0.9,0.6,1.8,1.2,2.7,1.9c0.4,0.3,0.8,0.7,1.2,1.1c0.4,0.4,0.8,0.8,1.1,1.2
      c7.6,8.5,8,21.3,1.1,30.3c-2.7,3.5-6.3,6.2-10.3,8c-2,0.9-4.1,1.5-6.3,1.8c-2.2,0.3-4.4,0.4-6.6,0.2c-4.4-0.4-8.6-1.9-12.3-4.3
      c-7.4-5-12.1-13.1-12.7-22c-0.3-4.4,0.3-8.8,1.9-12.9c1.6-4.1,4.1-7.8,7.3-10.8c11.6-11.1,29.6-12,42.3-2.2
      C84.4,34.3,89.2,51.1,83.6,66c-1.6,4.1-3.8,7.9-6.8,11.2L76.1,76.6z"/>
    <circle class="st0" cx="52" cy="50" r="0.2"/>
    <circle class="st0" cx="51.2" cy="47.9" r="0.2"/>
    <circle class="st0" cx="49" cy="48.2" r="0.2"/>
    <circle class="st0" cx="48" cy="50.2" r="0.2"/>
    <circle class="st0" cx="48.7" cy="52.1" r="0.2"/>
    <circle class="st0" cx="50" cy="50" r="0.2"/>
    <circle class="st0" cx="51.1" cy="51.6" r="0.2"/>
    <polygon class="st0" points="50,50 83.3,12.4 50,50    "/>
    <polygon class="st0" points="49.9,50 70,3.9 50.1,50     "/>
    <polygon class="st0" points="49.9,50 54.8,0 50.1,50     "/>
    <polygon class="st0" points="49.9,50 39.1,1 50.1,50     "/>
    <polygon class="st0" points="49.9,50 24.5,6.7 50.1,50     "/>
    <polygon class="st0" points="50,50 12.4,16.7 50,50    "/>
    <polygon class="st0" points="50,50.1 3.9,30 50,49.9     "/>
    <polygon class="st0" points="50,50.1 0,45.2 50,49.9     "/>
    <polygon class="st0" points="50,50.1 1,60.9 50,49.9     "/>
    <polygon class="st0" points="50,50.1 6.7,75.5 50,49.9     "/>
    <polygon class="st0" points="50,50 16.7,87.6 50,50    "/>
    <polygon class="st0" points="50.1,50 30,96.1 49.9,50    "/>
    <polygon class="st0" points="50.1,50 45.2,100 49.9,50     "/>
    <polygon class="st0" points="50.1,50 60.9,99 49.9,50    "/>
    <polygon class="st0" points="50.1,50 75.5,93.3 49.9,50    "/>
    <polygon class="st0" points="50,50 87.6,83.3 50,50    "/>
    <polygon class="st0" points="50,49.9 96.1,70 50,50.1    "/>
    <polygon class="st0" points="50,49.9 100,54.8 50,50.1     "/>
    <polygon class="st0" points="50,49.9 99,39.1 50,50.1    "/>
    <polygon class="st0" points="50,49.9 93.3,24.5 50,50.1    "/>
  </g>
`

const LONG_BUG = `
<g id="long-bug">
    <path class="st0" d="M38,80.1L38,80.1c-1.9-0.1-2.4-1.6-2.8-2.8l-0.1-0.2c-0.3-0.9-0.7-1.7-1.2-2.5c-1.5-2.2-5.1-3.8-5.2-3.8
      l-0.4-0.2l0.2-0.4c0,0,1.9-3.7,1.9-6.4c0.1-1.4-0.6-2.8-1.8-3.6L28.5,60l0.1-0.3c0-0.1,3-6.9,3-11.6s-3.1-11.8-3.1-11.8l-0.2-0.4
      l0.5-0.1c1-0.2,1.6-1.1,1.7-2.1c0-1.9-1.9-6.8-1.9-6.9l-0.1-0.4l0.4-0.1c0,0,3-1.2,3.8-3.4c0.4-0.9,0.3-2.1,0.3-3.1
      c0-0.5,0-0.9,0-1.3s0.1-1.5,1-1.7c0.2,0,0.3,0,0.5,0c0.5,0,1.3,0.2,2.4,0.3c3,0.5,8.1,1.3,13.1,1.3s10.1-0.8,13.1-1.3
      c1.1-0.2,2-0.3,2.4-0.3c0.2,0,0.3,0,0.5,0c1,0.2,1,1.3,1,1.7c0,0.4,0,0.9,0,1.3c0,1-0.1,2.2,0.3,3.1c0.9,2.2,3.8,3.4,3.8,3.4
      l0.4,0.1l-0.1,0.4c0,0.1-1.9,5-1.9,6.9c0,1.6,1.6,2.1,1.7,2.1l0.5,0.1l-0.2,0.4c0,0.1-3.1,7.1-3.1,11.8s3,11.6,3,11.6l0.1,0.3
      l-0.3,0.2c-1.2,0.8-1.8,2.2-1.8,3.6c0,2.7,1.9,6.4,1.9,6.4l0.2,0.4l-0.4,0.2c0,0-3.6,1.7-5.2,3.8c-0.5,0.8-0.9,1.6-1.2,2.5
      l-0.1,0.2c-0.4,1.2-0.9,2.7-2.8,2.8c-0.2,0-0.4,0-0.6-0.1c-3.8-0.7-7.6-1.1-11.4-1.2c-3.8,0.1-7.6,0.5-11.4,1.2
      C38.4,80,38.2,80,38,80.1z M50,78c3.9,0.1,7.8,0.5,11.6,1.2l0.5,0.1c1.2-0.1,1.6-0.9,2-2.2l0.1-0.2c0.3-1,0.7-1.9,1.3-2.7
      c1.4-1.9,4.1-3.4,5.1-3.9c-0.5-1-1.8-4-1.8-6.4c-0.1-1.6,0.6-3.1,1.9-4.1c-0.6-1.4-3-7.2-3-11.7c0-4.3,2.3-10.2,2.9-11.8
      c-1.1-0.4-1.8-1.5-1.8-2.7c0-1.7,1.4-5.6,1.9-6.8c-0.9-0.4-3.1-1.7-3.9-3.7c-0.4-1.1-0.4-2.4-0.4-3.5c0-0.5,0-0.9,0-1.3
      c-0.1-0.9-0.3-1-0.4-1c0,0,0,0-0.2,0c-0.5,0-1.3,0.2-2.4,0.3c-3,0.5-8.1,1.3-13.2,1.3s-10.2-0.8-13.2-1.3
      c-1.1-0.2-1.9-0.3-2.4-0.3c-0.1,0-0.2,0-0.2,0c-0.1,0-0.4,0.1-0.4,1c0,0.4,0,0.8,0,1.2c0,1.1,0.1,2.4-0.4,3.5
      c-0.8,2.1-3,3.3-3.9,3.7c0.5,1.2,1.9,5.1,1.9,6.8c0,1.2-0.7,2.3-1.8,2.7c0.7,1.6,2.9,7.4,2.9,11.8c0,4.4-2.4,10.2-3,11.7
      c1.2,1,1.9,2.5,1.9,4.1c0,2.4-1.3,5.4-1.8,6.4c1,0.5,3.7,2,5.1,3.9c0.6,0.8,1,1.8,1.3,2.7l0.1,0.2c0.5,1.4,0.8,2.2,2.1,2.2
      l0.4-0.1C42.2,78.4,46.1,78,50,78z"/>
    <path class="st0" d="M50.8,71.8h-1.6c-6.7,0-12.2-5.5-12.2-12.2V36.5c0-6.7,5.5-12.2,12.2-12.2h1.6c6.7,0,12.2,5.5,12.2,12.2v23.1
      C63,66.3,57.5,71.7,50.8,71.8z M49.2,25.8c-5.9,0-10.6,4.7-10.6,10.6v23.1c0,5.9,4.7,10.6,10.6,10.6h1.6c5.9,0,10.6-4.7,10.6-10.6
      V36.5c0-5.9-4.7-10.6-10.6-10.6L49.2,25.8z"/>
    <polygon class="st0" points="24.3,0 41.5,28.8 40.8,29.2     "/>
    <polygon class="st0" points="9.8,8.8 38.1,34.4 37.5,34.9    "/>
    <polygon class="st0" points="0.2,19 38,40.9 37.6,41.6     "/>
    <polygon class="st0" points="1.6,73.7 37.6,55 38,55.7     "/>
    <polygon class="st0" points="7,90.2 37.5,62.1 38.1,62.6     "/>
    <polygon class="st0" points="28.6,100 42.4,69.2 43.1,69.5     "/>
    <polygon class="st0" points="75.7,0 59.2,29.2 58.5,28.8     "/>
    <polygon class="st0" points="90.2,8.8 62.5,34.9 61.9,34.4     "/>
    <polygon class="st0" points="99.8,19 62.4,41.6 62,40.9    "/>
    <polygon class="st0" points="98.4,73.7 62,55.7 62.4,55    "/>
    <polygon class="st0" points="93,90.2 61.9,62.6 62.5,62.1    "/>
    <polygon class="st0" points="71.4,100 56.9,69.5 57.6,69.2     "/>
  </g>
`

function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
  var angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;

  return {
    x: centerX + (radius * Math.cos(angleInRadians)),
    y: centerY + (radius * Math.sin(angleInRadians))
  };
}

function describeArc(x, y, radius, startAngle, endAngle) {

  var start = polarToCartesian(x, y, radius, endAngle);
  var end = polarToCartesian(x, y, radius, startAngle);

  var largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";

  var d = [
    "M", start.x, start.y,
    "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y
  ].join(" ");

  return d;
}
