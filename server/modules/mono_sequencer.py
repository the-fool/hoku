import logging


async def mono_sequencer(midi_worker_q, on_trigger_msgs_q, clock_q, notes_q):
    step = 0
    off_note = 0
    notes = []
    on_trigger_msgs = []

    logging.debug('Mono sequencer starting')

    while True:
        # do some housekeeping first, while waiting for the next beat

        # first, do we need to add or remove note messages?
        # this list of message schema are for instrument & method events
        if not on_trigger_msgs_q.empty():
            x = await on_trigger_msgs_q.get()

            if x['action'] == 'add':
                on_trigger_msgs.append(x['payload'])

            elif x['action'] == 'remove':
                instrument_name_to_remove = x['payload']
                on_trigger_msgs = [
                    x for x in on_trigger_msgs
                    if x[0] != instrument_name_to_remove
                ]

        # are the notes any different
        if not notes_q.empty():
            notes = await notes_q.get()

        # wait for the queue to send its monotonic timestamp
        ts = await clock_q.get()

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
