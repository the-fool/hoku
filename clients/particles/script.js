var width = Math.max(960, innerWidth),
    height = Math.max(500, innerHeight);

var x1 = width / 2,
    y1 = height / 2,
    x0 = x1,
    y0 = y1,
    i = 0,
    r = 200,
    τ = 2 * Math.PI,
    xMsg = x1,
    yMsg = y1;

var body = document.getElementById('body');
var ws = new WebSocket('ws://' + window.location.hostname + ':4444?name=particles');

ws.onmessage = function(e) {
    body.style.transition = '';
    body.style.background = '#222';
    setTimeout(() => {
        body.style.transition = 'all .1s';
        body.style.background = '#111';
    }, 100);
};

var throttledMsg = throttle(doMessage, 50);

function doMessage(x, y) {
    if (ws.readyState < 1) return;
    x = Math.round(x / width * 100);
    y = Math.round(y / height * 100);
    if ((x !== xMsg) || (y !== yMsg)) {
        xMsg = x;
        yMsg = y;
        ws.send(JSON.stringify({
            x: x,
            y: y
        }));
    }
}
var canvas = d3.select("body").append("canvas")
    .attr("width", width)
    .attr("height", height)
    .on("ontouchstart" in document ? "touchmove" : "mousemove", move);

var context = canvas.node().getContext("2d");
context.globalCompositeOperation = "lighter";
context.lineWidth = 2;

d3.timer(function() {
    context.clearRect(0, 0, width, height);

    var z = d3.hsl(++i % 360, 1, .5).rgb(),
        c = "rgba(" + z.r + "," + z.g + "," + z.b + ",",
        x = x0 += (x1 - x0) * .03,
        y = y0 += (y1 - y0) * .03;

    d3.select({}).transition()
        .duration(500)
        .ease(Math.sqrt)
        .tween("circle", function() {
            return function(t) {
                context.strokeStyle = c + (1 - t) + ")";
                context.beginPath();
                context.arc(x, y, r * t, 0, τ);
                context.stroke();

                throttledMsg(x0, y0);
            };
        });
});


function move() {
    var mouse = d3.mouse(this);
    x1 = mouse[0];
    y1 = mouse[1];
    d3.event.preventDefault();
}
