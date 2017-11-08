import logging


def mono_sequencer_factory(
        midi_worker_q,
        notes,
        on_trigger_msgs, ):

    step = 0
    off_note = 0

    logging.info('Mono sequencer starting with notes {}'.format(notes))

    async def metronome_cb(ts):
        """
        Passed to metronome
        """

        nonlocal step
        nonlocal off_note

        if len(notes) == 0:
            return

        step = ts % len(notes)

        note = notes[step]

        logging.info('Mono seq trigger step {}, note {}'.format(step, note))
        # when note is == 0, hold
        # when note is < 0, rest

        # we either have a note, or a rest -- do note off!
        if note is not 0:
            for msg in on_trigger_msgs:
                task = {
                    'instrument_name': msg[0],
                    'method': msg[2],
                    'payload': [off_note]
                }
                await midi_worker_q.put(task)

        # we have a note -- play it!
        if note > 0:
            off_note = note
            for msg in on_trigger_msgs:
                task = {
                    'instrument_name': msg[0],
                    'method': msg[1],
                    'payload': [note]
                }
                await midi_worker_q.put(task)

    return metronome_cb
