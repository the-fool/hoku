let MODE = 0;

let bpm = 100;

// setup aliases
const Rnd = Math.random,
      Floor = Math.floor;

// get dimensions of window and resize the canvas to fit
const width = window.innerWidth;
const height = window.innerHeight;

const reticle = $('#Reticle')[0];
const centerPiece = $('#Centerpiece_Frame')[0];

if (!Detector.webgl) Detector.addGetWebGLMessage();

let VISUALS_VISIBLE;

let SCALE_FACTOR;
let CAMERA_BOUND;

let NUM_POINTS_SUBSET;
let NUM_SUBSETS;
let NUM_POINTS;

let NUM_LEVELS;
let LEVEL_DEPTH;

let DEF_BRIGHTNESS;
let DEF_SATURATION;
let ORBIT_REGEN_COOLDOWN;
let SPRITE_SIZE;

// Orbit parameters constraints
let A_MIN;
let A_MAX;
let B_MIN;
let B_MAX;
let C_MIN;
let C_MAX;
let D_MIN;
let D_MAX;
let E_MIN;
let E_MAX;

let speed = 8;
let rotationSpeed = 0.005;

function defaultify() {
  VISUALS_VISIBLE = true;

  SCALE_FACTOR = 1500;
  CAMERA_BOUND = 20000;

  NUM_POINTS_SUBSET = 30000;
  NUM_SUBSETS = 7;
  NUM_POINTS = NUM_POINTS_SUBSET * NUM_SUBSETS;

  NUM_LEVELS = 4;
  LEVEL_DEPTH = 1600;

  DEF_BRIGHTNESS = 1;
  DEF_SATURATION = 0.8;
  ORBIT_REGEN_COOLDOWN = 3000;
  SPRITE_SIZE = 5;

  // Orbit parameters constraints
  A_MIN = -30;
  A_MAX = 30;
  B_MIN = .2;
  B_MAX = 1.8;
  C_MIN = 5;
  C_MAX = 17;
  D_MIN = 0;
  D_MAX = 10;
  E_MIN = 0;
  E_MAX = 12;
}
defaultify();

// Orbit parameters
let a, b, c, d, e;

// Orbit data
let orbit = {
  subsets: [],
  xMin: 0,
  xMax: 0,
  yMin: 0,
  yMax: 0,
  scaleX: 0,
  scaleY: 0
};

var container;
var camera, scene, renderer, composer, hueValues = [];

var mouseX = 0,
    mouseY = 0;

var windowHalfX = window.innerWidth / 2;
var windowHalfY = window.innerHeight / 2;
let i, j;


function init() {
  // Initialize data points
  for (i = 0; i < NUM_SUBSETS; i++) {
    var subsetPoints = [];
    for (j = 0; j < NUM_POINTS_SUBSET; j++) {
      subsetPoints[j] = {
        x: 0,
        y: 0,
        vertex: new THREE.Vertex(new THREE.Vector3(0, 0, 0))
      };
    }
    orbit.subsets.push(subsetPoints);
  }

  const sprite1 = THREE.ImageUtils.loadTexture("/lib/poppy.jpg");

  container = document.getElementById('portal');

  camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 3 * SCALE_FACTOR);
  camera.position.z = SCALE_FACTOR / 2;

  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x000000, 0.0010);

  redoHues();
  generateOrbit();

  // Create particle systems
  for (var k = 0; k < NUM_LEVELS; k++) {
    for (var s = 0; s < NUM_SUBSETS; s++) {

      var geometry = new THREE.Geometry();
      for (var i = 0; i < NUM_POINTS_SUBSET; i++) {
        geometry.vertices.push(orbit.subsets[s][i].vertex);
      }
      var materials = new THREE.ParticleBasicMaterial({
        size: (SPRITE_SIZE),
        map: sprite1,
        blending: THREE.AdditiveBlending,
        depthTest: false,
        transparent: true
      });
      materials.color.setHSV(hueValues[s], DEF_SATURATION, DEF_BRIGHTNESS);


      var particles = new THREE.ParticleSystem(geometry, materials);
      particles.myMaterial = materials;
      particles.myLevel = k;
      particles.mySubset = s;
      particles.position.x = 0;
      particles.position.y = 0;
      particles.position.z = -LEVEL_DEPTH * k - (s * LEVEL_DEPTH / NUM_SUBSETS) + SCALE_FACTOR / 2;
      particles.needsUpdate = 0;
      scene.add(particles);
    }
  }

  // Setup renderer and effects
  renderer = new THREE.WebGLRenderer({
    clearColor: 0x000000,
    clearAlpha: 1,
    antialias: false
  });
  renderer.setSize(window.innerWidth, window.innerHeight);

  container.appendChild(renderer.domElement);

  // Setup listeners
  document.addEventListener('mousemove', onDocumentMouseMove, false);
  document.addEventListener('touchstart', onDocumentTouchStart, false);
  document.addEventListener('touchmove', onDocumentTouchMove, false);
  document.addEventListener('keydown', onKeyDown, false);
  window.addEventListener('resize', onWindowResize, false);

  // Schedule orbit regeneration
  setInterval(updateOrbit, 3000);
}

function animate() {
  requestAnimationFrame(animate);
  render();
}

function render() {

  if (camera.position.x >= -CAMERA_BOUND && camera.position.x <= CAMERA_BOUND) {
    camera.position.x += (mouseX - camera.position.x) * 0.05;
    if (camera.position.x < -CAMERA_BOUND) camera.position.x = -CAMERA_BOUND;
    if (camera.position.x > CAMERA_BOUND) camera.position.x = CAMERA_BOUND;
  }
  if (camera.position.y >= -CAMERA_BOUND && camera.position.y <= CAMERA_BOUND) {
    camera.position.y += (-mouseY - camera.position.y) * 0.05;
    if (camera.position.y < -CAMERA_BOUND) camera.position.y = -CAMERA_BOUND;
    if (camera.position.y > CAMERA_BOUND) camera.position.y = CAMERA_BOUND;
  }

  camera.lookAt(scene.position);

  for (i = 0; i < scene.objects.length; i++) {
    scene.objects[i].position.z += speed;
    scene.objects[i].rotation.z += rotationSpeed;
    if (scene.objects[i].position.z > camera.position.z) {
      scene.objects[i].position.z = -1 * (NUM_LEVELS - 1) * LEVEL_DEPTH;
      if (scene.objects[i].needsUpdate == 1) {
        scene.objects[i].geometry.__dirtyVertices = true;
        scene.objects[i].myMaterial.color.setHSV(hueValues[scene.objects[i].mySubset], DEF_SATURATION, DEF_BRIGHTNESS);
        scene.objects[i].needsUpdate = 0;
      }
    }
  }

  renderer.render(scene, camera);
}

///////////////////////////////////////////////
// Hopalong Orbit Generator
///////////////////////////////////////////////
function updateOrbit() {
  generateOrbit();
  for (var s = 0; s < NUM_SUBSETS; s++) {
    hueValues[s] = Math.random();
  }
  for (i = 0; i < scene.objects.length; i++) {
    scene.objects[i].needsUpdate = 1;
  }

}

function generateOrbit() {
  var x, y, z, x1;
  var idx = 0;

  prepareOrbit();

  // Using local vars should be faster
  var al = a;
  var bl = b;
  var cl = c;
  var dl = d;
  var el = e;
  var subsets = orbit.subsets;
  var num_points_subset_l = NUM_POINTS_SUBSET;
  var num_points_l = NUM_POINTS;
  var scale_factor_l = SCALE_FACTOR;

  var xMin = 0,
      xMax = 0,
      yMin = 0,
      yMax = 0;
  var choice;
  choice = Math.random();

  for (var s = 0; s < NUM_SUBSETS; s++) {

    // Use a different starting point for each orbit subset
    x = s * .005 * (0.5 - Math.random());
    y = s * .005 * (0.5 - Math.random());

    var curSubset = subsets[s];

    for (var i = 0; i < num_points_subset_l; i++) {

      // Iteration formula (generalization of the Barry Martin's original one)


      if (choice < 0.5) {
        z = (dl + (Math.sqrt(Math.abs(bl * x - cl))));
      } else if (choice < 0.75) {
        z = (dl + Math.sqrt(Math.sqrt(Math.abs(bl * x - cl))));

      } else {
        z = (dl + Math.log(2 + Math.sqrt(Math.abs(bl * x - cl))));
      }

      if (x > 0) {
        x1 = y - z;
      } else if (x == 0) {
        x1 = y;
      } else {
        x1 = y + z;
      }
      y = al - x;
      x = x1 + el;

      curSubset[i].x = x;
      curSubset[i].y = y;

      if (x < xMin) {
        xMin = x;
      } else if (x > xMax) {
        xMax = x;
      }
      if (y < yMin) {
        yMin = y;
      } else if (y > yMax) {
        yMax = y;
      }

      idx++;
    }
  }

  var scaleX = 2 * scale_factor_l / (xMax - xMin);
  var scaleY = 2 * scale_factor_l / (yMax - yMin);

  orbit.xMin = xMin;
  orbit.xMax = xMax;
  orbit.yMin = yMin;
  orbit.yMax = yMax;
  orbit.scaleX = scaleX;
  orbit.scaleY = scaleY;

  // Normalize and update vertex data
  for (var s = 0; s < NUM_SUBSETS; s++) {
    var curSubset = subsets[s];
    for (var i = 0; i < num_points_subset_l; i++) {
      curSubset[i].vertex.position.x = scaleX * (curSubset[i].x - xMin) - scale_factor_l;
      curSubset[i].vertex.position.y = scaleY * (curSubset[i].y - yMin) - scale_factor_l;
    }
  }
}

function prepareOrbit() {
  shuffleParams();
  orbit.xMin = 0;
  orbit.xMax = 0;
  orbit.yMin = 0;
  orbit.yMax = 0;
}

function shuffleParams() {
  a = A_MIN + Math.random() * (A_MAX - A_MIN);
  b = B_MIN + Math.random() * (B_MAX - B_MIN);
  c = C_MIN + Math.random() * (C_MAX - C_MIN);
  d = D_MIN + Math.random() * (D_MAX - D_MIN);
  e = E_MIN + Math.random() * (E_MAX - E_MIN);
}

///////////////////////////////////////////////
// Event listeners
///////////////////////////////////////////////
function onDocumentMouseMove(event) {
  mouseX = event.clientX - windowHalfX;
  mouseY = event.clientY - windowHalfY;
}

function onDocumentTouchStart(event) {
  if (event.touches.length == 1) {
    event.preventDefault();
    mouseX = event.touches[0].pageX - windowHalfX;
    mouseY = event.touches[0].pageY - windowHalfY;
  }
}

function onDocumentTouchMove(event) {
  if (event.touches.length == 1) {
    event.preventDefault();
    mouseX = event.touches[0].pageX - windowHalfX;
    mouseY = event.touches[0].pageY - windowHalfY;
  }
}

function onWindowResize(event) {
  windowHalfX = window.innerWidth / 2;
  windowHalfY = window.innerHeight / 2;
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function onKeyDown(event) {
  if (event.keyCode == 38 && speed < 20) speed += .5;
  else if (event.keyCode == 40 && speed > 0) speed -= .5;
  else if (event.keyCode == 37) rotationSpeed += .001;
  else if (event.keyCode == 39) rotationSpeed -= .001;
  else if (event.keyCode == 72 || event.keyCode == 104) toggleVisuals();
}

function showHideAbout() {
  if (document.getElementById('about').style.display == "block") {
    document.getElementById('about').style.display = "none";
  } else {
    document.getElementById('about').style.display = "block";
  }
}

function toggleVisuals() {
  if (VISUALS_VISIBLE) {
    document.getElementById('plusone').style.display = 'none';
    document.getElementById('tweet').style.display = 'none';
    document.getElementById('fb').style.display = 'none';
    document.getElementById('aboutlink').style.display = 'none';
    document.getElementById('about').style.display = 'none';
    document.getElementById('info').style.display = 'none';
    document.getElementById('chaosnebula').style.display = 'none';
    renderer.domElement.style.cursor = "none";
    VISUALS_VISIBLE = false;
  } else {
    document.getElementById('plusone').style.display = 'block';
    document.getElementById('tweet').style.display = 'block';
    document.getElementById('fb').style.display = 'block';
    document.getElementById('aboutlink').style.display = 'block';
    document.getElementById('info').style.display = 'block';
    document.getElementById('chaosnebula').style.display = 'block';
    renderer.domElement.style.cursor = "";
    VISUALS_VISIBLE = true;
  }
}

init();
animate();

function defaultUniverse() {
  SCALE_FACTOR = 1500;
  A_MIN = -30;
  A_MAX = 30;
  B_MIN = .2;
  B_MAX = 1.8;
  C_MIN = 5;
  C_MAX = 17;
  D_MIN = 0;
  D_MAX = 10;
  E_MIN = 0;
  E_MAX = 12;
}

function fiberyPlantCells() {
  setAll(2, 30, 3, 1, 0);
  SCALE_FACTOR = 1600;
}

function circleWire() {
  setAll(-22, 0.5, 7, 3.33, 7.9);
  SCALE_FACTOR = 2000;
}

function sparseness() {
  setAll(2, 300, 3, 1, 0);
  SCALE_FACTOR = 3000;
}

function spinalColumn() {
  setAll(200, 300, 3, 1, 0);
  SCALE_FACTOR = 400;
}

function boxUniverse() {
  const a = 200,
        b = 0,
        c = 3,
        d = 0,
        e = 0;
  setAll(a, b, c, d, e);
  SCALE_FACTOR = 400;
}

const UNIVERSES = [defaultUniverse, boxUniverse, spinalColumn, sparseness, circleWire, fiberyPlantCells];
const RED = 0xd10000;
const ORANGE = 0xff6622;
const YELLOW = 0xffda21;
const GREEN = 0x33dd00;
const BLUE = 0x1133cc;
const VIOLET = 0x330044;
const WHITE = 0xdddddd;
const COLORS = [RED, YELLOW, GREEN, BLUE, VIOLET, WHITE];

function setAll(a, b, c, d, e) {
  setA(a);
  setB(b);
  setC(c);
  setD(d);
  setE(e);
}

function setA(x) {
  A_MIN = A_MAX = x;
}

function setB(x) {
  B_MIN = B_MAX = x;
}

function setC(x) {
  C_MIN = C_MAX = x;
}

function setD(x) {
  D_MIN = D_MAX = x;
}

function setE(x) {
  E_MIN = E_MAX = x;
}

function ejectConfig() {
  return {
    A_MIN,
    A_MAX,
    B_MIN,
    B_MAX,
    C_MIN,
    C_MAX,
    D_MIN,
    D_MAX,
    E_MIN,
    E_MAX
  };
}

function ejectInstance() {
  return {
    a,
    b,
    c,
    d,
    e
  };
}


function recolor() {
  redoHues();
  for (i = 0; i < scene.objects.length; i++) {
    //scene.objects[i].geometry.__dirtyVertices = true;
    scene.objects[i].myMaterial.color.setHSV(hueValues[scene.objects[i].mySubset], DEF_SATURATION, DEF_BRIGHTNESS);
  }
}

function redoHues() {
  for (var i = 0; i < NUM_SUBSETS; i++) {
    hueValues[i] = Math.random();
  }
}

let BEAT_INTERVAL = 50;

function beat() {
  let nearestIndex = findNearest();
  let i = nearestIndex;
  let old_i = -1;
  let oldColor = new THREE.Color();
  let oldSize = 5;
  let intervalId = setInterval(() => {
    if (old_i >= 0) {
      scene.objects[old_i].myMaterial.color.copy(oldColor);
      scene.objects[old_i].myMaterial.size = SPRITE_SIZE;
    }
    oldColor.copy(scene.objects[i].myMaterial.color);

    scene.objects[i].myMaterial.size = 50;
    scene.objects[i].myMaterial.color.setHSV(hueValues[scene.objects[i].mySubset], 0.2, 1);
    old_i = i;
    i = (i + 1) % scene.objects.length;
    if (i === nearestIndex) {

      scene.objects[old_i].myMaterial.color.copy(oldColor);
      scene.objects[old_i].myMaterial.size = SPRITE_SIZE;
      clearInterval(intervalId);
    }
  }, BEAT_INTERVAL - speed / 5);

}

function findNearest() {
  let nearest;
  let z;
  let bestZ = 0;
  let best = 0;
  for (i = 0; i < scene.objects.length; i++) {
    z = scene.objects[i].position.z;
    if (z > bestZ) {
      bestZ = z;
      best = i;

    }

    if (bestZ > 0 && z < 0) {
      // we have looped around to the back!
      return best;
    }
  }

  return 0;
}


function rotate(n, x) {
  n.style['transform'] = `rotate(${x}deg)`;
}

function wobble() {
  if (Rnd() > 0.8) {
    let x = Rnd() * 360;
    rotate(reticle, x);
  }

  if (Rnd() > 0.7) {
    let x = Rnd() * 360;
    rotate(centerPiece, x);
  }
}



function initWs() {

  const wsUrl = path => `ws://${window.location.hostname}:7700/${path}`;
  const bpmWs = new WebSocket(wsUrl('metronome_changer'));

  const bpmToWarpSpeed = d3.scaleLinear().domain([0, 1]).range([0.3, 30]).clamp(true);

  bpmWs.onmessage = function(d) {
    const data = JSON.parse(d.data);
    speed = bpmToWarpSpeed(data.current_bpm);
    console.log(data);
  };

  const circles = d3.selectAll('#Time_Dots circle');
  const clockWs = new WebSocket(wsUrl('clocker'));
  clockWs.onmessage = function(d) {
    const data = JSON.parse(d.data);
    const tick = data.tick % 16;
    if (data.tick % (16 * 4) === 0) {
      viewWobble();
    }

    // if (tick == 0) beat();

    circles.each(function(d, i) {
      const elm = d3.select(this);
      elm.classed('active', i === tick);
    });
  };


  const patchWs = new WebSocket(wsUrl('patch'));
  patchWs.onmessage = function(d) {
    const data = JSON.parse(d.data);

    const colorIndex = data.patch;
    scene.fog = new THREE.FogExp2(COLORS[colorIndex], 0.00025);
  };


  const scaleWs = new WebSocket(wsUrl('scale'));
  scaleWs.onmessage = function(d) {
    const data = JSON.parse(d.data);

    UNIVERSES[data.scale]();
    console.log(data);
  };
}

function viewWobble() {
  const factor = 500;
  const x = (Math.random() * factor) - (factor / 2);
  const y = (Math.random() * factor) - (factor / 2);
  mouseX = x;
  mouseY = y;
}

$(function() {
  initWs();
  setInterval(wobble, 1000);
});
