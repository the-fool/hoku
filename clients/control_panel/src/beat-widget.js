function makeBeatWidget(node,  drumWs) {

  const data = {
    family: 0,
    elements: [true, true, true, true]
  };

  node.find('.elements .button').click(function(e) {
    const el = $(this);
    const i = el.index();
    data.elements[i] = !data.elements[i];
    onChange();
    applyChanges();
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

  function applyChanges() {
    node.find('.elements .button').each(function(i) {
      const el = $(this);
      el.toggleClass('active', data.elements[i]);
    });

    $(node.find('input[type=radio]')[data.family]).trigger('click');
  }

  function onChange() {
    // send data down ws
  }

  drumWs.onmessage = function(d) {
    const msg = JSON.parse(d.data);
    const family = data.family;
    const elements = data.elements;
    data.elements = elements;
    data.family = family;

    applyChanges();
  };

  applyChanges();
}
