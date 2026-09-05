import asyncio
import sys
import time
from io import BytesIO

PROBE_INTERVAL = 0.010


async def _probe(stop: asyncio.Event, lags: list[float]) -> None:
    while not stop.is_set():
        started = time.perf_counter()
        await asyncio.sleep(PROBE_INTERVAL)
        lags.append(time.perf_counter() - started - PROBE_INTERVAL)


async def _measure(work, concurrency: int, in_thread: bool) -> tuple[float, float, float]:
    stop = asyncio.Event()
    lags: list[float] = []
    # a bench script, not the app: nothing here outlives this function
    probe = asyncio.create_task(_probe(stop, lags))  # noqa: TID251
    await asyncio.sleep(0.05)
    lags.clear()

    async def one() -> None:
        if in_thread:
            await asyncio.to_thread(work)
        else:
            work()

    began = time.perf_counter()
    await asyncio.gather(*(one() for _ in range(concurrency)))
    wall = time.perf_counter() - began
    stop.set()
    await probe

    lags.sort()
    p99 = lags[int(len(lags) * 0.99)] if lags else float("nan")
    return wall, p99, (max(lags) if lags else float("nan"))


def _matplotlib_render():
    import matplotlib as mpl

    mpl.use("Agg")
    from matplotlib import pyplot as plt

    def render() -> None:
        fig, ax = plt.subplots()
        for series in range(12):
            ax.plot(range(400), [((i * (series + 3)) % 97) for i in range(400)])
        ax.legend([f"team {i}" for i in range(12)])
        ax.grid()
        out = BytesIO()
        plt.savefig(out, format="png")
        plt.close(fig)

    return render


def _bcrypt_verify():
    from passlib.context import CryptContext

    context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = context.hash("correct horse battery staple")
    return lambda: context.verify("correct horse battery staple", hashed)


WORKLOADS = {"matplotlib": _matplotlib_render, "bcrypt": _bcrypt_verify}


async def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "matplotlib"
    work = WORKLOADS[name]()
    work()  # warm up imports, font caches, the first-call costs

    print(f"== {name}, {'pinned' if len(sys.argv) > 2 else 'as scheduled'} ==")  # noqa: T201
    print(f"{'':>28} | {'wall':>9} | {'lag p99':>9} | {'lag max':>9}")  # noqa: T201
    wall, p99, worst = await _measure(work, 1, in_thread=False)
    print(f"{'inline on the loop':>28} | {wall * 1000:8.0f}ms | {'—':>9} | {worst * 1000:8.2f}ms")  # noqa: T201
    for concurrency in (1, 2, 4, 8, 16):
        wall, p99, worst = await _measure(work, concurrency, in_thread=True)
        label = f"to_thread, {concurrency} at once"
        print(  # noqa: T201
            f"{label:>28} | {wall * 1000:8.0f}ms | {p99 * 1000:8.2f}ms | {worst * 1000:8.2f}ms"
        )


if __name__ == "__main__":
    asyncio.run(main())
