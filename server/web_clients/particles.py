from ..util import cent_to_midi


def particles_cb(minilogue):
    def do_it(data):
        cut = cent_to_midi(data['x'])
        res = cent_to_midi(data['y'])

        minilogue.amp_decay(cut)
        minilogue.eg_decay(res)
    return do_it
