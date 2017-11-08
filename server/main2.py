import asyncio

from .instruments.four_by_four import instruments
from .web_servers import ws_server_factory

from .web_clients.clocker import clocker_factory
from .web_clients.particles import particles_factory

from .web_clients import metronome_changer_factory,\
    mono_sequencer_factory as mono_seq_web_client_factory,\
    ColorMonoSequencer as CMS

from .modules import metronome, midi_worker_factory, mono_sequencer_factory
import logging

starting_bpm = 120


def main():
    logging.basicConfig(
        level=logging.DEBUG, format='%(relativeCreated)6d %(message)s')

    midi_q, midi_worker_coro = midi_worker_factory(instruments)

    # make COLOR_MONO_SEQUENCER
    cms = CMS(rhythm=[4,4,4,4, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3])

    # make MONO_SEQUENCER
    notes_1 = [-1] * 16  # the notes in the sequence, a bar of rests
    on_trigger_msgs_mono_1 = []  # the messages to be sent for each note
    mono_seq_1_metr_cb = mono_sequencer_factory(
        midi_worker_q=midi_q,
        notes=notes_1,
        on_trigger_msgs=on_trigger_msgs_mono_1)

    on_trigger_msgs_mono_2 = [('minilogue_1', 'note_on', 'note_off')]
    mono_seq_2_metr_cb = mono_sequencer_factory(
        midi_worker_q=midi_q,
        notes=cms.real_notes,
        on_trigger_msgs=on_trigger_msgs_mono_2)

    mono_seq_obs, mono_seq_ws_consumer = mono_seq_web_client_factory(notes_1)

    # make CLOCKER
    clocker_obs, clocker_metr_cb, clocker_ws_consumer = clocker_factory()

    # make particles
    particles_ws_consumer = particles_factory(midi_q)

    # Set up metronome
    bpm_queue = asyncio.Queue()
    metronome_cbs = [
        clocker_metr_cb, mono_seq_1_metr_cb, mono_seq_2_metr_cb, cms.metro_cb
    ]
    metr_coro = metronome(metronome_cbs, bpm_queue, starting_bpm)
    metro_changer_obs, metro_ws_consumer = metronome_changer_factory(
        bpm_queue, starting_bpm)

    # hash of {path: (consumer, producer)}
    ws_behaviors = {
        'clocker': (clocker_ws_consumer, clocker_obs),
        'particles': (particles_ws_consumer, None),
        'metronome_changer': (metro_ws_consumer, metro_changer_obs),
        'monosequencer': (mono_seq_ws_consumer, mono_seq_obs),
        'colormonosequencer': (cms.ws_consumer, cms.obs)
    }

    ws_server_coro = ws_server_factory(behaviors=ws_behaviors)

    coros = [ws_server_coro, metr_coro, midi_worker_coro]

    loop = asyncio.get_event_loop()

    loop.run_until_complete(asyncio.gather(*coros))

    loop.close()
