import logging
import asyncio


def mono_sequencer_factory(
        midi_worker_q,
        notes,
        on_trigger_msgs, ):

    clock_q = asyncio.Queue()

    async def metronome_cb(ts):
        """
        Passed to the metronome module as one of its callbacks
        """
        await clock_q.put(ts)

    async def mono_sequencer_coro():
        step = 0
        off_note = 0

        logging.info('Mono sequencer starting with notes {}'.format(notes))

        while True:
            # wait for the queue to send its monotonic timestamp
            ts = await clock_q.get()

            if len(notes) == 0:
                continue

            step = ts % len(notes)

            note = notes[step]

            # when note is == 0, hold
            # when note is < 0, rest

            # we either have a note, or a rest -- do note off!
            if note is not 0:
                for msg in on_trigger_msgs:
                    task = {
                        'instrument_name': msg[0],
                        'method': msg[2],
                        'payload': [off_note, step]
                    }
                    await midi_worker_q.put(task)

            # we have a note -- play it!
            if note > 0:
                off_note = note
                for msg in on_trigger_msgs:
                    task = {
                        'instrument_name': msg[0],
                        'method': msg[1],
                        'payload': [note, step]
                    }
                    await midi_worker_q.put(task)

    return mono_sequencer_coro(), metronome_cb
