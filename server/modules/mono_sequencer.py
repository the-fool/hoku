import logging


class MonoSequencer:
    def __init__(self, midi_worker_q, notes, on_beat_msgs=[]):
        self.midi_worker_q = midi_worker_q
        self.notes = notes
        self.off_note = 0
        self.on_beat_msgs = on_beat_msgs

    async def on_beat(self, ts):
        if len(self.notes) == 0:
            return

        if len(self.on_beat_msgs) == 0:
            return

        step = ts % len(self.notes)

        note = self.notes[step]

        logging.info('Mono seq trigger step {}, note {}'.format(step, note))
        # when note is == 0, hold
        # when note is < 0, rest

        # we either have a note, or a rest -- do note off!
        if note is not 0:
            for msg in self.on_beat_msgs:
                task = {
                    'instrument_name': msg[0],
                    'method': msg[2],
                    'payload': [self.off_note]
                }
                await self.midi_worker_q.put(task)

        # we have a note -- play it!
        if note > 0:
            self.off_note = note
            for msg in self.on_beat_msgs:
                task = {
                    'instrument_name': msg[0],
                    'method': msg[1],
                    'payload': [note]
                }
                await self.midi_worker_q.put(task)


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
