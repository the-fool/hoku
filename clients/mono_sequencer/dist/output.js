var HOST = window.location.hostname;
var PATH = 'mono_sequencer';
var ws = new WebSocket("ws://" + HOST + ":7700/" + PATH);
var Column = (function () {
    function Column(note) {
        this.note = note;
        this.active = false;
    }
    Object.defineProperty(Column.prototype, "notesList", {
        get: function () {
            var _this = this;
            return [false, false, false].map(function (x, i) { return i !== _this.note ? false : true; });
        },
        enumerable: true,
        configurable: true
    });
    return Column;
}());
var columns = [0, 1, 2, 0].map(function (x) { return new Column(x); });
var main = d3.select('main');
var columnG = main.append('div').attrs({
    'id': 'column-group',
    'class': 'flex'
});
function updateColumns() {
    console.log('udpating!');
    var columnBindings = columnG.selectAll('svg.svg-col')
        .data(columns);
    var notesBindings = columnBindings
        .enter()
        .append('div')
        .attr('class', 'column')
        .append('svg')
        .attrs({ 'class': 'svg-col', 'width': '50px', height: '100%' })
        .merge(columnBindings)
        .selectAll('.note')
        .data(function (d) { return d.notesList; });
    columnBindings.exit().remove();
    notesBindings.exit().remove();
    notesBindings
        .enter()
        .append('g')
        .attr('class', 'note')
        .append('rect')
        .merge(notesBindings)
        .attrs({ 'color': function (d) { return d; } });
}
$(function () {
    updateColumns();
});
