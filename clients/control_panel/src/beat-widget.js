function makeBeatWidget(node) {
  const data = {
    family: 0,
    elements: [true, true, true, true]
  };

  node.find('.elements .button').click(function(e) {
    const el = $(this);
    const i = el.index();
    data.elements[i] = !data.elements[i];
    onChange();
    applyStyles();
  });


  node.find('input[type=radio]').change(function() {
    data.family = +this.value;

    onChange();
  });

  const g = d3.select(node.find('.reverb svg g').get()[0]);

  function onVerbChange(x) {
    console.log(x);
  }
  makeSlider(g, 5, 30, 300, onVerbChange);

  function applyStyles() {
    node.find('.elements .button').each(function(i) {
      const el = $(this);
      el.toggleClass('active', data.elements[i]);
    });
  }

  function onChange() {
    // send data down ws
  }

  applyStyles();
}
