$(function() {
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
            .attrs({width, height});
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


        console.log(d.data())
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

});
