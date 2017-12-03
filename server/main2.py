import asyncio

from .instruments.four_by_four import instruments

from .web_servers import ws_server_factory

from .web_clients.clocker import clocker_factory
from .web_clients.particles import particles_factory

from .web_clients import metronome_changer_factory,\
    mono_sequencer_factory as mono_seq_web_client_factory,\
    ColorMonoSequencer as CMS

from .modules import Metronome,\
    midi_worker_factory,\
    MonoSequencer

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

    mono_seq_obs, mono_seq_ws_consumer = mono_seq_web_client_factory(notes_1)

    # make CLOCKER
    clocker_obs, clocker_metr_cb, clocker_ws_consumer = clocker_factory()

    # make particles
    # particles_ws_consumer = particles_factory(midi_q)

    # Set up metronome
    metronome_cbs = [
        clocker_metr_cb, mono_seq_1.on_beat, mono_seq_2.on_beat, cms.metro_cb
    ]
    metronome = Metronome(metronome_cbs, starting_bpm)

    metro_changer_obs, metro_ws_consumer = metronome_changer_factory(
        metronome.set_bpm, starting_bpm)

    # hash of {path: (consumer, producer)}
    ws_behaviors = {
        'clocker': (clocker_ws_consumer, clocker_obs),
        # 'particles': (particles_ws_consumer, None),
        'metronome_changer': (metro_ws_consumer, metro_changer_obs),
        'monosequencer': (mono_seq_ws_consumer, mono_seq_obs),
        'colormonosequencer': (cms.ws_consumer, cms.obs)
    }

    ws_server_coro = ws_server_factory(behaviors=ws_behaviors)

    coros = [ws_server_coro, metronome.run()]

    loop = asyncio.get_event_loop()

    loop.run_until_complete(asyncio.gather(*coros))

    loop.close()
