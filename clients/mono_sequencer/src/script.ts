const HOST = window.location.hostname;
const PATH = 'mono_sequencer';
const ws = new WebSocket(`ws://${HOST}:7700/${PATH}`);

declare const d3;
declare const $;


class Column {
    public active = false;

    constructor(public note: number) { }

    get notesList() {
        return [false, false, false].map((x, i) => i !== this.note ? false : true);
    }
}
const columns: Column[] = [0, 1, 2, 0].map(x => new Column(x))


const main = d3.select('main');
const columnG = main.append('div').attrs({
    'id': 'column-group',
    'class': 'flex'
});

function updateColumns() {
    console.log('udpating!')
    const columnBindings = columnG.selectAll('svg.svg-col')
        .data(columns);

    const notesBindings = columnBindings
        .enter()
        .append('div')
        .attr('class', 'column')
        .append('svg')
        .attrs({'class': 'svg-col', 'width': '50px', height: '100%'})
        .merge(columnBindings)
        .selectAll('.note')
        .data(d => d.notesList);

    columnBindings.exit().remove()
    notesBindings.exit().remove()

    notesBindings
        .enter()
        .append('g')
        .attr('class', 'note')
        .append('rect')
        .merge(notesBindings)
        .attrs({ 'color': d => d });
}

$(function() {
    updateColumns();
});
