// requestAnimFrame shim
window.requestAnimFrame = (function() {
  return window.requestAnimationFrame ||
    window.webkitRequestAnimationFrame ||
    window.mozRequestAnimationFrame ||
    window.oRequestAnimationFrame ||
    window.msRequestAnimationFrame ||
    function(callback) {
      window.setTimeout(callback);
    };
})();

let MODE = 0;

// DEMO TESTINctx DUMMY!
let bpm = 100;
const bpmToWarpSpeed = d3.scaleLinear().domain([80, 260]).range([0.01, 0.8]).clamp(true);

// setup aliases
const Rnd = Math.random,
      Floor = Math.floor;

// get dimensions of window and resize the canvas to fit
const width = window.innerWidth;
const height = window.innerHeight;

/*
  const canvas = document.getElementById('c');
  canvas.width = width;
  canvas.height = height;

  // get 2d graphics ctx and set global alpha
  const ctx = canvas.getContext('2d');
  //ctx.globalAlpha = 0.5;
  */
// constants and storage for objects that represent star positions
const startingWarpSpeed = 12,
      numStars = 500,
      stars = [];

let cycle = 0,
    starWidth = 2,
    lightness = 80,
    warpSpeed = (1 / 25 * 2);

// mouse events
function addCanvasEventListener(name, fn) {
  canvas.addEventListener(name, fn, false);
}
/*
  addCanvasEventListener('mousemove', function(e) {
  mousex = e.clientX;
  mousey = e.clientY;
  });

  function wheel(e) {
  const delta = e.detail ? -e.detail / 3 : e.wheelDelta / 120;
  const doff = (delta / 25);
  if (delta > 0 && warpSpeed + doff <= 0.5 || delta < 0 && warpSpeed + doff >= 0.01) {
  warpSpeed += (delta / 25);
  }
  }
  addCanvasEventListener('DOMMouseScroll', wheel);
  addCanvasEventListener('mousewheel', wheel);
*/


// function to reset a star object
function resetstar(a = {}) {
  a.x = (Rnd() * width - (width * 0.5)) * startingWarpSpeed;
  a.y = (Rnd() * height - (height * 0.5)) * startingWarpSpeed;
  a.z = startingWarpSpeed;
  a.px = 0;
  a.py = 0;

  return a;
}

// initial star setup
for (let i = 0; i < numStars; i++) {
  stars.push(resetstar());
}

let rotation = 0;
let alpha = 0.4;
let rotationIncr = 0;

function defaultify() {
  rotation = 0;
  alpha = 0.6;
  rotationIncr = 0;
}

// star rendering anim function
function animFrame() {
  // clear background
  // reset transforms before clearing
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = 'rgba(0,0,0,0.1)';
  ctx.fillRect(0, 0, width, height);


  ctx.save();

  if (rotation) {
    ctx.translate((width / 2), (width / 2));
    ctx.rotate(rotation);
    rotation += rotationIncr;
    // ctx.translate((-width / 2) , (-width / 2));
  }
  // mouse position to head towards
  const cx = width / 2,
        cy = height / 2;

  // update all stars
  const sat = Math.min(Floor(warpSpeed * 500), 100); // warpSpeed range 0.01 -> 0.5

  stars.forEach((star, i) => {
    const xx = star.x / star.z, // star position
          yy = star.y / star.z,
          e = (1.0 / star.z + 1) * 20; // size i.e. z

    if (star.px !== 0) {
      ctx.strokeStyle = `hsl(${(cycle * i) % 360},${sat}%,${lightness}%)`;
      ctx.lineWidth = starWidth;
      ctx.beginPath();
      ctx.moveTo(xx + cx, yy + cy);
      ctx.lineTo(star.px + cx, star.py + cy);
      ctx.stroke();
    }

    // update star position values with new settings
    star.px = xx;
    star.py = yy;
    star.z -= warpSpeed;

    // reset when star is out of the view field
    if (star.z < warpSpeed || star.px > width || star.py > height) {
      // reset star
      resetstar(star);
    }
    // colour cycle sinewave rotation
    cycle += 0.01;
  });

  ctx.restore();
  requestAnimFrame(animFrame);
};

document.addEventListener('keydown', event => {
  const key = event.key;
  const keyCode = parseInt(event.key);
  if (keyCode >= 0) {
    setMode(keyCode);
  } else if (key === 'ArrowUp') {
    if (bpm > 240) return;
    bpm += 10;
    setBpm(bpm);
  } else if (key === 'ArrowDown') {
    if (bpm < 90) return;
    bpm -= 10;
    setBpm(bpm);
  }
});

function setMode(keyCode) {
  defaultify();

  if (keyCode === 1) {
    // rotation
    alpha = 0.1;
    rotation = 0.05;
    rotationIncr = 0.01;
  }
}

function setBpm(bpm) {
  warpSpeed = bpmToWarpSpeed(bpm);
}
