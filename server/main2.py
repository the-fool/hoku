import asyncio
from .observable import observable_factory
from .web_servers import ws_server_factory

from .web_clients.clocker import clocker_factory
from .web_clients.particles import particles_factory

from .modules import metronome


def main():
    metronome_obs_sub, metronome_obs_emit = observable_factory()

    clocker_obs, clocker_metronome_cb, clocker_ws_consumer = clocker_factory()
    particles_ws_consumer = particles_factory()

    metr_coro = metronome([clocker_metronome_cb])

    ws_consumers = [
        {'path': 'clocker', 'coro': clocker_ws_consumer},
        {'path': 'particles', 'coro': particles_ws_consumer}
    ]

    ws_producers = {'clocker': clocker_obs}

    ws_server_coro = ws_server_factory(
        consumers=ws_consumers, producers=ws_producers)

    coros = [ws_server_coro, metr_coro]

    loop = asyncio.get_event_loop()

    loop.run_until_complete(asyncio.gather(*coros))

    loop.close()