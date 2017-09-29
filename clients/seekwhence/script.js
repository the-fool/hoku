var svg = d3.select("svg"), margin = { top: 20, right: 20, bottom: 30, left: 40 }, width = +svg.attr("width") - margin.left - margin.right, height = +svg.attr("height") - margin.top - margin.bottom;
var g = svg.append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
var notes = g.append('g')
    .attr('id', 'notes');
var noteData = [1, 2, 3];
notes.selectAll('.note')
    .data(d3.range(0, 10))
    .enter().append('rect')
    .attrs({
    'class': '.note'
});
