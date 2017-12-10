function makeSynthWidget(node) {
  const labels = ['Vol', 'Dist', 'Rev', 'Filt'];
  const makeDatum = (name) => ({
    name,
    values: [0.1, 0.5, 0.25, 0.75].map((value, i) => ({
      value,
      label: labels[i]
    }))
  });


  ['outer', 'inner'].forEach(name => {

    const datum = makeDatum(name);
    const attractorContainer = node.find(`#${name} .attractor`).first();
    const controlsContainer = node.find(`#${name} .controls`).first();


    const a = new AttractorWidget(attractorContainer, controlsContainer);

    a.initialize();

    window[name] = a;
  });
}

function makeSynthWidget1(node) {
  // input: jq elm

  const labels = ['Vol', 'Dist', 'Rev', 'Filt'];
  const datum = (name) => ({
    name,
    values: [0.1, 0.5, 0.25, 0.75].map((value, i) => ({
      value,
      label: labels[i]
    }))
  });
  const data = [datum('outer'), datum('inner')];

  const width = 600,
        height = 400;
  const split = 50;
  const sliderGroupWidth = width / 2 - 50;
  const sliderGutter = 20;
  const sliderWidth = sliderGroupWidth / 4 - sliderGutter;

  const gutter = width / 4 / 2;

  const scaleY = d3.scaleLinear()
        .domain([0, 1])
        .rangeRound([height, 0]);

  const scaleX = d3.scaleLinear()
        .domain([0, data[0].values.length])
        .rangeRound([0, width]);



  const svg = d3.select(node.get()[0]).append('svg')
        .attrs({
          width: width * 2,
          height
        });

  const g = svg.append('g').attr('id', 'synths');
  const instrumentGroups = g.selectAll('.instrument')
        .data(data)
        .enter()
        .append('g')
        .attr('id', d => `inst-${d.name}`)
        .attr('transform', (d, i) => `translate(${i * (width + split)}, 0)`);


  data.forEach((d, index) => {
    const a = appendAttractor(index);
    const inst = d3.select(`#inst-${d.name}`);
    d.values.forEach((_, i) => {
      const x = i * (sliderWidth + sliderGutter);
      makeSlider(inst, x, sliderWidth, height, x => console.log('wat'));
    });
  });


  function appendAttractor(index) {
    const cont = $('<div></div>').attr('id', `container-${index}`).attr('class', 'attractor-container');
    node.append(cont);
    const a = new AttractorWidget(cont);
    a.initialize();
    return a;
  }



}







function makeInstrumentWidget() {
  const labels = ['Vol', 'Dist', 'Rev', 'Filt'];
  const datum = (name) => ({
    name,
    values: [0.1, 0.5, 0.25, 0.75].map((value, i) => ({
      value,
      label: labels[i]
    }))
  });
  const data = [datum('Outer'), datum('iner')];
  const width = 300,
        height = 200;
  const gutter = width / 4 / 2 / 1.5;
  const scaleY = d3.scaleLinear()
        .domain([0, 1])
        .rangeRound([height, 0]);
  const scaleX = d3.scaleLinear()
        .domain([0, data[0].values.length])
        .rangeRound([0, width]);


  function init() {
    data.map(d => d.values).forEach(makeInstrument);

    function makeInstrument(data, index) {
      const svg = d3.select('#instruments-widget').append('svg')
            .attrs({
              width,
              height
            });
      const g = svg.append('g').attr('class', 'instrument');
      g
        .append('rect')
        .attrs({
          x: 0,
          y: 0,
          width,
          height
        });
      const brushY = d3.brushY()
            .extent(function(d, i) {
              return [
                [scaleX(i) + gutter / 2, 0],
                [scaleX(i) + scaleX(1) - gutter / 2, height]
              ];
            })
            .handleSize([12])
            .on("brush", brushmoveY)
            .on("end", brushendY);
      const brushes = g
            .selectAll('.brush')
            .data(data)
            .enter()
            .append('g')
            .attr('class', 'brush')
            .append('g')
            .call(brushY)
            .call(brushY.move, function(d) {
              return [d.value, 0].map(scaleY);
            });

      $('.brush .handle--n').each(function() {
        const h = $(this);
        const child = h.parent().children()[0];
        const goodX = child.x.baseVal.value;
        const goodW = child.width.baseVal.value;
        h[0].x.baseVal.value = goodX;

        h[0].width.baseVal.value = goodW;
      });



      function brushendY() {
        if (!d3.event.sourceEvent) return;
        if (d3.event.sourceEvent.type === "brush") return;
        if (!d3.event.selection) { // just in case of click with no move
          brushes
            .call(brushY.move, function(d) {
              return [d.value, 0].map(scaleY);
            });
        };
      }

      function brushmoveY() {
        if (!d3.event.sourceEvent) return;
        if (d3.event.sourceEvent.type === "brush") return;
        if (!d3.event.selection) return;

        const d0 = d3.event.selection.map(scaleY.invert);
        const d = d3.select(this).select('.selection');

        d.datum().value = d0[0]; // Change the value of the original data
        update();
      }

      function update() {
        brushes
          .call(brushY.move, function(d) {
            console.log(d);
            return [d.value, 0].map(scaleY);
          });
      }
    }
  }

  init();
};
