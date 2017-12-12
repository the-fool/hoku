function makeBeatWidget(node,  drumWs, fxWs) {
  let virgin = true;

  const data = {
    family: 0,
    elements: [true, true, true, true]
  };

  node.find('.elements .button').click(function(e) {
    const el = $(this);
    const i = el.index();
    data.elements[i] = !data.elements[i];
    onChangeElements();
    applyChanges();
  });

  node.find('input[type=radio]').change(function() {
    console.log('change');
    data.family = +this.value;

    onChangeFamily();
  });

  const g = d3.select(node.find('.reverb svg g').get()[0]);

  function sendVerbChange(x) {
    fxWs.send(JSON.stringify({kind: 'drum_reverb', payload: x}));
  }
  const throttledSendVerbChange = throttle(sendVerbChange, 200);
  function onVerbChange(x) {
    if (drumWs.readyState !== 1) return;
    throttledSendVerbChange(x);
  }

  makeSlider(g, 5, 30, 300, onVerbChange);

  function applyChanges() {
    node.find('.elements .button').each(function(i) {
      const el = $(this);
      el.toggleClass('active', data.elements[i]);
    });

    $(node.find('input[type=radio]')[data.family]).trigger('click');
  }
  function onChangeFamily() {
    if (drumWs.readyState !== 1) return;
    drumWs.send(JSON.stringify({kind: 'change_family', payload: data.family}));
  }

  function onChangeElements() {
    if (drumWs.readyState !== 1) return;
    drumWs.send(JSON.stringify({kind: 'change_elements', payload: data.elements}));
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
