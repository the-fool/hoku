const svg = d3.select("svg"),
      margin = {
        right: 25,
        left: 25,
        top: 25,
        bot: 25
      },
      width = +svg.attr("width") - margin.left - margin.right,
      height = +svg.attr("height"),
      bpmWidth = width / 2,
      bpmHeight = height / 2;

let bpm = 120;


/// Encapsulated Recipes

function makeBpmWidget() {
  const gutter = 30;
  const indicatorLightWidth = 15;
  const indicatorLightGutter = 15;
  const bpmWidget = svg.append('g')
        .attrs({
          id: 'bpmWidget',
          transform: `translate(${margin.left},${margin.top})`
        });


  function makeBpmIndicator() {
    const bpmIndicator = bpmWidget.append('g')
          .attrs({
            id: 'bpmIndicator',
            transform: `translate(${gutter}, 0)`
          });
    for (let row = 0; row < 4; row++) {
      for (let col = 0; col < 4; col++) {
        bpmIndicator.append('circle')
          .attrs({
            cx: col * (indicatorLightWidth + indicatorLightGutter),
            cy: row * (indicatorLightWidth + indicatorLightGutter),
            r: indicatorLightWidth / 2,
            'class': 'indicator-light'
          });
      }
    }
  }

  function makeBpmSlider() {
    const bpmScale = makeLinearScale(bpmHeight, [30, 180]);

    const bpmControl = bpmWidget.append('g')
          .attrs({
            id: 'bpmControl'
          });

    makeTrack(bpmControl, bpmScale, onDragBpm);
    const bpmHandle = makeHandle(bpmControl);

    function onDragBpm() {
      const newVal = bpmScale(bpmScale.invert(d3.event.y));
      console.log(newVal / bpmScale.range()[1]);
      bpmHandle.attr('cy', newVal);
    }
  }

  makeBpmSlider();
  makeBpmIndicator();
}

function makeDemoSlider() {
  const slider = svg.append("g")
        .attr("class", "slider")
        .attr("transform", "translate(" + margin.left + "," + height / 2 + ")");

  const x = makeLinearScale(width, [20, 200]);
  makeTrack(slider, x, () => hue(x.invert(d3.event.x)), false);


  slider.insert("g", ".track-overlay")
    .attr("class", "ticks")
    .attr("transform", "translate(0," + 18 + ")")
    .selectAll("text")
    .data(x.ticks(10))
    .enter().append("text")
    .attr("x", x)
    .attr("text-anchor", "middle")
    .text(function(d) {
      return d + "°";
    });

  var handle = makeHandle(slider);

  slider.transition() // Gratuitous intro!
    .duration(750)
    .tween("hue", function() {
      var i = d3.interpolate(0, 70);
      return function(t) {
        hue(i(t));
      };
    });

  function hue(h) {
    handle.attr("cx", x(h));
    svg.style("background-color", d3.hsl(h, 0.8, 0.8));
  }
}



/// UTILITY FUNCTIONS

function makeLinearScale(maxRange, domain = [0, 127]) {
  return d3.scaleLinear()
    .domain(domain)
    .range([0, maxRange])
    .clamp(true);
}

function makeTrack(parentGroup, scale, onDrag, isVertical = true) {
  const axis = isVertical ? 'y' : 'x';

  parentGroup.append("line")
    .attr("class", "track")
    .attr(`${axis}1`, scale.range()[0])
    .attr(`${axis}2`, scale.range()[1])
    .select(function() {
      return this.parentNode.appendChild(this.cloneNode(true));
    })
    .attr("class", "track-inset")
    .select(function() {
      return this.parentNode.appendChild(this.cloneNode(true));
    })
    .attr("class", "track-overlay")
    .call(d3.drag()
          .on("start.interrupt", function() {
            parentGroup.interrupt();
          })
          .on("start drag", onDrag));
}

function makeHandle(parentGroup) {
  return parentGroup.insert("circle", ".track-overlay")
    .attr("class", "handle")
    .attr("r", 9);
}


$(function() {
  makeBpmWidget();
})
