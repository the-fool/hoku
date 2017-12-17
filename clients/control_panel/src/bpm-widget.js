function makeBpmWidget2(node, bpmWs, clockWs) {
  const sliderG = d3.select(node.find('#bpm-slider svg').get()[0]);
  const flowerG = d3.select(node.find('#flower-clock svg').get()[0]);

  function sendBpmWsMsg(val) {
    bpmWs.send(JSON.stringify({
      kind: 'change',
      payload: val
    }));
  }
  const throttledBpmSend = throttle(sendBpmWsMsg, 200);
  makeSlider(sliderG, 5, 30, 300, throttledBpmSend);

  clockWs.onmessage = function(d) {
    const data = JSON.parse(d.data);
    const tick = data.tick % 16 + 1;
    flowerG.select(`#Petal-${tick} path`).classed('active', true);
    flowerG.select(`#Petal-${tick === 1 ? 16 : tick - 1} path`).classed('active', false);
  };

}

function makeBpmWidget(node, bpmWs, clockWs) {
  // input: jquery elm
  const rawHeight = 300;
  const rawWidth = 300;
  const svg = d3.select(node.get()[0])
        .append('svg').attrs({
          width: rawWidth,
          height: rawHeight
        }),
        margin = {
          right: 0,
          left: 0,
          top: 25,
          bot: 25
        },
        width = +svg.attr("width") - margin.left - margin.right,
        height = +svg.attr("height");
  const sliderHeight = height - margin.top - margin.bot;
  const sliderWidth = 40;
  const bpmIndicatorMargin = margin.left + sliderWidth + 30;
  const bpmIndicatorWidth = width - margin.right - bpmIndicatorMargin;
  let bpm = 120;

  const wsUrl = path => `ws://${window.location.hostname}:7700/${path}`;

  /// Encapsulated Recipes

  function initBpmWidget() {
    const indicatorLightGutter = 6;
    //const indicatorLightWidth = bpmIndicatorWidth / 4 - indicatorLightGutter;
    //const indicatorLightHeight = height / 4 - indicatorLightGutter;
    const square = 40;
    const indicatorLightHeight = square;
    const indicatorLightWidth = square;

    const bpmWidget = svg.append('g')
          .attrs({
            id: 'bpm-widget-g',
            transform: `translate(${margin.left},${margin.top})`
          });

    clockWs.onmessage = function(d) {
      const data = JSON.parse(d.data);
      const tick = data.tick % 16;
      bpmWidget.select(`#indicator-${tick}`).classed('active', true);
      bpmWidget.select(`#indicator-${tick === 0 ? 15 : tick - 1}`).classed('active', false);
    };


    function makeBpmIndicator() {
      const bpmIndicator = bpmWidget.append('g')
            .attrs({
              id: 'bpmIndicator',
              transform: `translate(${bpmIndicatorMargin}, ${0})`
            });
      for (let row = 0; row < 4; row++) {
        for (let col = 0; col < 4; col++) {
          bpmIndicator.append('rect')
            .attrs({
              x: col * (indicatorLightWidth + indicatorLightGutter),
              y: row * (indicatorLightHeight + indicatorLightGutter),
              width: indicatorLightWidth,
              height: indicatorLightHeight,
              id: `indicator-${row * 4 + col}`,
              'class': 'indicator-light',
              'stroke-width': 2,
              'stroke': 'white'
            });
        }
      }
    }

    function makeBpmSlider() {
      const g = bpmWidget.append('g')
            .attrs({
              id: 'bpmControl'
            });

      function sendWsMsg(val) {
        bpmWs.send(JSON.stringify({
          kind: 'change',
          payload: val
        }));
      }

      const throttledSend = throttle(sendWsMsg, 200);
      makeSlider(g, 5, sliderWidth, sliderHeight, throttledSend);
    }

    makeBpmSlider();
    makeBpmIndicator();
  }

  initBpmWidget();
};
