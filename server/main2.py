import asyncio

# from .instruments.four_by_four import instruments

from .web_servers import ws_server_factory


from .web_clients import ColorMonoSequencer as CMS

from .web_socket_clients import Clocker, MetronomeChanger

from .modules import Metronome,\
    MonoSequencer,\
    ColorSequencer

import logging

starting_bpm = 120


def main():
    logging.basicConfig(
        level=logging.DEBUG, format='%(relativeCreated)6d %(message)s')

    # instruments = {}

    # make COLOR_MONO_SEQUENCER
    cms = CMS(rhythm=[-1] * 16)

    # make MONO_SEQUENCER
    notes_1 = [-1] * 16  # the notes in the sequence, a bar of rests

    mono_seq_1 = MonoSequencer(notes_1, instruments=[])
    mono_seq_2 = MonoSequencer(cms.notes, instruments=[])

    # make CLOCKER
    clocker = Clocker()

    # make particles
    # particles_ws_consumer = particles_factory(midi_q)

    # Set up metronome
    metronome_cbs = [
        clocker.metronome_cb,
        mono_seq_1.on_beat, mono_seq_2.on_beat, cms.metro_cb
    ]
    metronome = Metronome(metronome_cbs, starting_bpm)

    metro_changer = MetronomeChanger(
        init_bpm=starting_bpm, on_change_cb=metronome.set_bpm)
    # hash of {path: (consumer, producer)}
    ws_behaviors = {
        'clocker': (None, clocker.obs),
        # 'particles': (particles_ws_consumer, None),
        'metronome_changer': (metro_changer.ws_consumer, metro_changer.obs),
        'colormonosequencer': (cms.ws_consumer, cms.obs)
    }

    ws_server_coro = ws_server_factory(behaviors=ws_behaviors)

    coros = [ws_server_coro, metronome.run()]

    loop = asyncio.get_event_loop()

    loop.run_until_complete(asyncio.gather(*coros))

    loop.close()
