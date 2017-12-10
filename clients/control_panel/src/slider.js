function makeSlider(g, x, width, height, cb) {
    // g is a d3 elm
  console.log(x, width, height)
    let mostRecentChange = 0;
    height = height <= 0 ? 1 : height;
    makeTrack(g, onDrag);
    const handle = makeHandle(g);

    const scale = d3.scaleLinear()
        .domain([0, 1])
        .range([0, height])
        .clamp(true);

    function makeTrack(parentGroup, onDrag, isVertical = true) {
        const axis = isVertical ? 'y' : 'x';

        parentGroup.append("rect")
            .attrs({
                'class': 'track',
                x,
                y: 0,
                width,
                height
            })
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
        return parentGroup.insert("rect", ".track-overlay")
            .attr("class", "handle")
            .attrs({
                x,
                y: 0,
                width,
                height
            });
    }

    function onDrag() {
        const newVal = scale(scale.invert(d3.event.y));
        handle.attr('height', height - newVal);
        handle.attr('y', newVal);

        if (newVal !== mostRecentChange) {
            mostRecentChange = newVal;
            // do not send a zero
            const percent = (height - newVal) / height;
            cb(Math.max(percent, 0.01));
        }
    }

}
