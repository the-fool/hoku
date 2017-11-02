def metronome_changer_factory(bpm_queue, bpm):
    async def ws_producer():
        pass

    async def ws_consumer(kind, payload, uuid):
        nonlocal bpm_queue

        if kind == 'change':
            await bpm_queue.put(payload)
