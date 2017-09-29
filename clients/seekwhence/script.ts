declare const d3;
const svg = d3.select("svg"),
    margin = { top: 20, right: 20, bottom: 30, left: 40 },
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom;

const g = svg.append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


const notes = g.append('g')
    .attr('id', 'notes')

const noteData = [1,2,3];

notes.selectAll('.note')
    .data(d3.range(0, 10))
    .enter().append('rect')
    .attrs({
        'class': 'note'
    })

