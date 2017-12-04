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

// setup aliases
const Rnd = Math.random,
    Floor = Math.floor;
// get dimensions of window and resize the canvas to fit
const width = window.innerWidth,
    height = window.innerHeight,
    canvas = document.getElementById('c');

canvas.width = width;
canvas.height = height;

let mousex = width / 2,
    mousey = height / 2;

// get 2d graphics context and set global alpha
const G = canvas.getContext('2d');
G.globalAlpha = 0.5;


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

// star rendering anim function
function animFrame() {
    // clear background
    G.fillStyle = '#000';
    G.fillRect(0, 0, width, height);

    // mouse position to head towards
    const cx = (mousex - width / 2) + (width / 2),
        cy = (mousey - height / 2) + (height / 2);

    // update all stars
    const sat = Math.min(Floor(warpSpeed * 500), 100); // warpSpeed range 0.01 -> 0.5

    stars.forEach((star, i) => {
        const xx = star.x / star.z, // star position
            yy = star.y / star.z,
            e = (1.0 / star.z + 1) * 20; // size i.e. z

        if (star.px !== 0) {
            G.strokeStyle = `hsl(${(cycle * i) % 360},${sat}%,${lightness}%)`;
            G.lineWidth = starWidth;
            G.beginPath();
            G.moveTo(xx + cx, yy + cy);
            G.lineTo(star.px + cx, star.py + cy);
            G.stroke();
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

    requestAnimFrame(animFrame);
};
requestAnimFrame(animFrame);
