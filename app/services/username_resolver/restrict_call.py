# from https://gist.github.com/jorektheglitch/5ea4972d9cb87c2ec682604e53d1ff94 by @entressi
import asyncio


class RestrictCall:

    def __init__(self, delay):
        self.delay = delay
        self.queue = asyncio.Queue()
        self.bg_worker = asyncio.ensure_future(self.queue_processor())

    async def queue_processor(self):
        while True:
            can_go = await self.queue.get()
            can_go.set()
            await asyncio.sleep(self.delay)

    def __call__(self, func):
        async def wrapped(*args, **kwargs):
            can_go = asyncio.Event()
            await self.queue.put(can_go)
            await can_go.wait()
            return await func(*args, **kwargs)

        return wrapped
