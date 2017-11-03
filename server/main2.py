import asyncio
from .web_servers import ws_server_factory

from .web_clients.clocker import clocker_factory
from .web_clients.particles import particles_factory
from .web_clients import metronome_changer_factory,\
    mono_sequencer_factory as mono_seq_web_client_factory
from .modules import metronome, midi_worker_factory, mono_sequencer_factory
import logging

starting_bpm = 120


def main():

    logging.basicConfig(
        level=logging.DEBUG, format='%(relativeCreated)6d %(message)s')

    midi_q, midi_worker_coro = midi_worker_factory({})

    # make mono-sequencer
    notes_1 = [-1] * 16  # the notes in the sequence, a bar of rests
    on_trigger_msgs_mono_1 = []  # the messages to be sent for each note
    mono_seq_1_metr_cb = mono_sequencer_factory(
        midi_worker_q=midi_q,
        notes=notes_1,
        on_trigger_msgs=on_trigger_msgs_mono_1)

    mono_seq_obs, mono_seq_ws_consumer = mono_seq_web_client_factory(
        notes_1)

    # make clocker
    clocker_obs, clocker_metr_cb, clocker_ws_consumer = clocker_factory()

    # make particles
    particles_ws_consumer = particles_factory(midi_q)

    # Set up metronome
    bpm_queue = asyncio.Queue()
    metronome_cbs = [clocker_metr_cb, mono_seq_1_metr_cb]
    metr_coro = metronome(metronome_cbs, bpm_queue, starting_bpm)
    metro_changer_obs, metro_ws_consumer = metronome_changer_factory(
        bpm_queue, starting_bpm)

    ws_consumers = [{
        'path': 'clocker',
        'coro': clocker_ws_consumer
    }, {
        'path': 'particles',
        'coro': particles_ws_consumer
    }, {
        'path': 'metronome_changer',
        'coro': metro_ws_consumer
    }, {
        'path': 'monosequencer',
        'coro': mono_seq_ws_consumer
    }]

    ws_producers = {
        'clocker': clocker_obs,
        'monosequencer': mono_seq_obs,
        'metronome_changer': metro_changer_obs
    }

    ws_server_coro = ws_server_factory(
        consumers=ws_consumers, producers=ws_producers)

    coros = [ws_server_coro, metr_coro]

    loop = asyncio.get_event_loop()

    loop.run_until_complete(asyncio.gather(*coros))

    loop.close()
