import logging


class MonoSequencer:
    def __init__(self, notes, instruments=[], time_multiplier=1):
        """
        Notes are a mutable, public list of notes
        cbs are a list of objects that implement the BaseInstrument interface,
          -- namely, they have a note_on, note_off methods
        """
        self.notes = notes
        self.off_note = 0
        self.instruments = instruments

        # if a time_multiplier is 1, then we hit on every beat
        # else, if the multiplier increases the amount of time each step takes
        # eg, with multiplier at 4, each step will be 4 times as long
        self.time_multiplier = time_multiplier

    async def on_beat(self, ts):
        if len(self.notes) == 0:
            return

        if len(self.instruments) == 0:
            return

        if ts % self.time_multiplier != 0:
            return

        step = (ts // self.time_multiplier) % len(self.notes)

        note = self.notes[step]

        logging.info('Mono seq trigger step {}, note {}'.format(step, note))
        # when note is == 0, hold
        # when note is < 0, rest

        # we either have a note, or a rest -- do note off!
        if note is not 0:
            for instrument in self.instruments:
                instrument.note_off(self.off_note)

        # we have a note -- play it!
        if note > 0:
            self.off_note = note
            for instrument in self.instruments:
                instrument.note_on(note)
