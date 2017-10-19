$(function() {
    main();
});

var ws;
var bugs = [];
var svg;
var svgNS = "http://www.w3.org/2000/svg";
var g;

function main() {
    ws = new WebSocket('ws://127.0.0.1:7700/petri');
    ws.onmessage = onmessage;

    svg = document.querySelector('svg g');
    g = document.querySelector('#main-group');

    setInterval(function() {
        requestAnimationFrame(paint);
    }, 1000 / 60);
}

function onmessage(msg) {
    var state = JSON.parse(msg.data);
    bugs = state.agents;
}

function paintSVG() {
    bugs.forEach(upsertBug);
}
var i = 0;
var w = 0;

function paint() {
    i = (i + 1) % 360;
    w = w + 0.1;
    if (w > 10) w = 0;
    var ctx = document.getElementById('canvas').getContext('2d');

    ctx.globalCompositeOperation = 'destination-over';
    ctx.clearRect(0, 0, 1200, 700); // clear canvas
    ctx.strokeStyle = 'rgba(255, 153, 255, 0.4)';
    ctx.save();

    bugs.forEach(function(bug) {
        ctx.lineWidth = bug.vel * 3;
        ctx.fillStyle = 'hsl(' + (bug.vel * 70) % 360 + ',100%,50%)';
        ctx.beginPath();
        ctx.arc(bug.x, bug.y, 20, 0, Math.PI * 2, false); // Earth orbit
        ctx.stroke();
        ctx.fill();
        ctx.closePath();
    });
}

function upsertBug(bug) {
    var transform = 'translate(' + bug.x + ' ' + bug.y + ')';
    var dinging = bug.dinging;
    var pk = bug.pk;
    var bugEl = document.getElementById('pk' + pk + '');
    if (bugEl === null) {
        bugEl = document.createElementNS(svgNS, 'g');
        const circle = document.createElementNS(svgNS, 'circle');
        circle.setAttributeNS(null, 'r', 20);
        bugEl.setAttributeNS(null, 'id', 'pk' + pk);
        bugEl.setAttributeNS(null, 'class', 'bug');
        bugEl.appendChild(circle);
        svg.appendChild(bugEl);
    } else {
        bugEl.setAttributeNS(null, 'transform', transform);
    }
}
