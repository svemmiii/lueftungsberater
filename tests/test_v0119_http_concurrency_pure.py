"""Shared HTTP lifetimes, bounded parallelism, priority and cancellation races."""
import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
import importlib.util
from pathlib import Path
import sys
import time

import pytest

spec = importlib.util.spec_from_file_location(
    "lb_http_concurrency", Path(__file__).resolve().parents[1] / "custom_components/lueftungsberater/polling.py")
polling = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = polling
spec.loader.exec_module(polling)
RequestPacer = polling.RequestPacer


class StatusError(Exception):
    def __init__(self, status, retry_after="0"):
        self.status = status
        self.headers = {"Retry-After": retry_after}


class Client:
    def __init__(self):
        self.calls = []
        self.gates = {}
        self.started = defaultdict(asyncio.Event)
        self.cancelled = defaultdict(asyncio.Event)
        self.failures = defaultdict(list)
        self.live = self.peak = self.normal_live = self.normal_peak = 0

    def request(self, method, url, **kwargs):
        client = self
        attempt = 1 + sum(call[2] == url for call in self.calls)
        headers = dict(kwargs.get("headers") or {})
        self.calls.append((time.monotonic(), method, url, headers))

        class Response:
            active = False

            def finish(self):
                if self.active:
                    self.active = False
                    client.live -= 1
                    client.normal_live -= int(not url.startswith("warning"))

            async def __aenter__(self):
                self.active = True
                client.live += 1
                client.normal_live += int(not url.startswith("warning"))
                client.peak = max(client.peak, client.live)
                client.normal_peak = max(client.normal_peak, client.normal_live)
                client.started[url].set()
                try:
                    if url in client.gates:
                        await client.gates[url].wait()
                    if client.failures[url]:
                        raise client.failures[url].pop(0)
                    return self
                except asyncio.CancelledError:
                    client.cancelled[url].set()
                    self.finish()
                    raise
                except BaseException:
                    self.finish()
                    raise

            async def __aexit__(self, *args):
                self.finish()

            def raise_for_status(self):
                pass

            async def json(self, **kwargs):
                return {"url": url, "headers": headers, "attempt": attempt}

            async def text(self):
                return url

            async def read(self):
                return url.encode()

        return Response()


@asynccontextmanager
async def setup(monkeypatch, gap=0):
    monkeypatch.setattr(RequestPacer, "gap", property(lambda self: gap))
    client = Client()
    pacer = RequestPacer(client)
    try:
        yield pacer, client
    finally:
        await pacer.close()
        assert client.live == 0


async def started(client, url):
    await asyncio.wait_for(client.started[url].wait(), 1)


def job(pacer, name="weather", *, bootstrap=False, urgent=False, deadline=None):
    return pacer.job(name, 900, deadline or pacer.clock() + 1000, bootstrap=bootstrap, urgent=urgent)


@pytest.mark.parametrize("cancel_index", [0, 1, 2])
@pytest.mark.parametrize("bootstrap", [False, True])
async def test_one_cancelled_participant_does_not_cancel_the_other_shared_callers(monkeypatch, cancel_index, bootstrap):
    async with setup(monkeypatch) as (pacer, client):
        client.gates["shared"] = asyncio.Event()
        session = job(pacer, bootstrap=bootstrap)
        tasks = [asyncio.create_task(session.fetch("json", "shared")) for _ in range(3)]
        await started(client, "shared")
        tasks[cancel_index].cancel()
        with pytest.raises(asyncio.CancelledError):
            await tasks[cancel_index]
        assert not client.cancelled["shared"].is_set()
        client.gates["shared"].set()
        results = await asyncio.wait_for(asyncio.gather(*(t for i, t in enumerate(tasks) if i != cancel_index)), 1)
        assert all(result["url"] == "shared" for result in results)
        assert len(client.calls) == pacer.requests == session.count == 1


async def test_all_departed_participants_cancel_the_orphan_transport(monkeypatch):
    async with setup(monkeypatch) as (pacer, client):
        client.gates["shared"] = asyncio.Event()
        session = job(pacer)
        tasks = [asyncio.create_task(session.fetch("json", "shared")) for _ in range(2)]
        await started(client, "shared")
        for task in tasks:
            task.cancel()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert all(isinstance(result, asyncio.CancelledError) for result in results)
        await asyncio.wait_for(client.cancelled["shared"].wait(), 1)
        assert not pacer.active and len(client.calls) == 1


async def test_a_new_caller_after_last_cancellation_does_not_join_a_dying_task(monkeypatch):
    async with setup(monkeypatch) as (pacer, client):
        client.gates["shared"] = asyncio.Event()
        session = job(pacer)
        old = asyncio.create_task(session.fetch("json", "shared"))
        await started(client, "shared")
        old.cancel()
        with pytest.raises(asyncio.CancelledError):
            await old
        new = asyncio.create_task(session.fetch("json", "shared"))
        await asyncio.sleep(0)
        client.gates["shared"].set()
        result = await asyncio.wait_for(new, 1)
        assert result["url"] == "shared" and len(client.calls) == 2


@pytest.mark.parametrize("bootstrap", [False, True])
async def test_two_slow_stations_leave_real_capacity_for_an_urgent_warning(monkeypatch, bootstrap):
    async with setup(monkeypatch) as (pacer, client):
        for url in ["station1", "station2"]:
            client.gates[url] = asyncio.Event()
        session = job(pacer, bootstrap=bootstrap)
        stations = [asyncio.create_task(session.fetch("json", url)) for url in client.gates]
        for url in client.gates:
            await started(client, url)
        third = asyncio.create_task(session.fetch("json", "station3"))
        warning = asyncio.create_task(job(pacer, "warning", bootstrap=bootstrap, urgent=True,
                                         deadline=pacer.clock() + .1).fetch("json", "warning"))
        result = await asyncio.wait_for(warning, 1)
        assert result["url"] == "warning"
        assert not any(task.done() for task in stations)
        assert not client.started["station3"].is_set()
        assert client.peak == 3 and client.normal_peak == 2
        for gate in client.gates.values():
            gate.set()
        await asyncio.wait_for(asyncio.gather(*stations, third), 1)


async def test_a_later_urgent_interest_promotes_an_already_queued_shared_request(monkeypatch):
    async with setup(monkeypatch) as (pacer, client):
        client.gates.update({url: asyncio.Event() for url in ["station1", "station2"]})
        ordinary = job(pacer)
        stations = [asyncio.create_task(ordinary.fetch("json", url)) for url in client.gates]
        for url in client.gates:
            await started(client, url)
        original = asyncio.create_task(ordinary.fetch("json", "warning_shared"))
        await asyncio.sleep(0)
        urgent = asyncio.create_task(job(pacer, "warning", urgent=True).fetch("json", "warning_shared"))
        result = await asyncio.wait_for(urgent, 1)
        assert await original == result
        assert sum(call[2] == "warning_shared" for call in client.calls) == 1
        assert not any(task.done() for task in stations)
        for gate in client.gates.values():
            gate.set()
        await asyncio.gather(*stations)


@pytest.mark.parametrize("failure", [TimeoutError("timeout"), OSError("connection"), StatusError(503), StatusError(429)])
async def test_shared_retry_survives_the_original_callers_cancellation(monkeypatch, failure):
    original_sleep = asyncio.sleep
    delays = []

    async def fast_sleep(delay):
        if delay:
            delays.append(delay)
        await original_sleep(0)

    monkeypatch.setattr(polling.asyncio, "sleep", fast_sleep)
    async with setup(monkeypatch) as (pacer, client):
        client.gates["shared"] = asyncio.Event()
        client.failures["shared"] = [failure]
        session = job(pacer)
        first = asyncio.create_task(session.fetch("json", "shared"))
        await started(client, "shared")
        second = asyncio.create_task(session.fetch("json", "shared"))
        await original_sleep(0)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        client.gates["shared"].set()
        result = await asyncio.wait_for(second, 1)
        assert result["attempt"] == 2
        assert len(client.calls) == pacer.requests == 2 and pacer.retries == 1
        if isinstance(failure, StatusError):
            assert delays == [1]


async def test_retry_after_wait_ends_when_the_last_participant_leaves(monkeypatch):
    backoff = asyncio.Event()
    began_backoff = asyncio.Event()
    original_sleep = asyncio.sleep

    async def pause(delay):
        if not delay:
            await original_sleep(0)
            return
        began_backoff.set()
        await backoff.wait()

    monkeypatch.setattr(polling.asyncio, "sleep", pause)
    async with setup(monkeypatch) as (pacer, client):
        client.failures["shared"] = [StatusError(429)]
        task = asyncio.create_task(job(pacer).fetch("json", "shared"))
        await asyncio.wait_for(began_backoff.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        backoff.set()
        assert len(client.calls) == 1


@pytest.mark.parametrize("changes", [
    {"headers": {"If-None-Match": '"other"'}}, {"headers": {"Authorization": "other"}},
    {"params": {"station": "other"}}, {"method": "POST"}, {"mode": "text"},
])
async def test_distinct_request_headers_parameters_methods_and_response_modes_do_not_coalesce(monkeypatch, changes):
    async with setup(monkeypatch) as (pacer, client):
        session = job(pacer)
        first = {"mode": "json", "headers": {"If-None-Match": '"first"'}, "params": {"station": "one"}}
        second = {**first, **changes}
        a, b = await asyncio.gather(session.fetch(url="shared", **first), session.fetch(url="shared", **second))
        assert len(client.calls) == 2
        if "headers" in changes:
            assert a["headers"] != b["headers"]


async def test_start_spacing_remains_in_force_for_nonurgent_transports(monkeypatch):
    async with setup(monkeypatch, gap=.02) as (pacer, client):
        session = job(pacer)
        await asyncio.gather(*(session.fetch("json", f"station{i}") for i in range(5)))
        times = [call[0] for call in client.calls]
        assert all(b - a >= .016 for a, b in zip(times, times[1:]))


async def test_close_cancels_running_queued_and_shared_waiters(monkeypatch):
    async with setup(monkeypatch) as (pacer, client):
        client.gates.update({url: asyncio.Event() for url in ["station1", "station2"]})
        session = job(pacer)
        tasks = [asyncio.create_task(session.fetch("json", url))
                 for url in ["station1", "station1", "station2", "station3"]]
        for url in client.gates:
            await started(client, url)
        await pacer.close()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert all(isinstance(result, asyncio.CancelledError) for result in results)
        assert not client.started["station3"].is_set() and not pacer.active
        with pytest.raises(asyncio.CancelledError):
            await session.fetch("json", "after_close")


async def test_completion_and_caller_cancellation_can_race_without_losing_followers(monkeypatch):
    async with setup(monkeypatch) as (pacer, client):
        session = job(pacer)
        for index in range(50):
            url = f"race{index}"
            client.gates[url] = asyncio.Event()
            first = asyncio.create_task(session.fetch("json", url))
            await started(client, url)
            second = asyncio.create_task(session.fetch("json", url))
            await asyncio.sleep(0)
            if index % 2:
                client.gates[url].set()
                first.cancel()
            else:
                first.cancel()
                client.gates[url].set()
            await asyncio.gather(first, return_exceptions=True)
            assert (await asyncio.wait_for(second, 1))["url"] == url
        assert len(client.calls) == 50


async def test_departed_queued_shared_callers_never_start_an_orphan_request(monkeypatch):
    async with setup(monkeypatch) as (pacer, client):
        client.gates.update({url: asyncio.Event() for url in ["station1", "station2"]})
        session = job(pacer)
        stations = [asyncio.create_task(session.fetch("json", url)) for url in client.gates]
        for url in client.gates:
            await started(client, url)
        waiting = [asyncio.create_task(session.fetch("json", "shared")) for _ in range(2)]
        await asyncio.sleep(0)
        for task in waiting:
            task.cancel()
        await asyncio.gather(*waiting, return_exceptions=True)
        for gate in client.gates.values():
            gate.set()
        await asyncio.gather(*stations)
        assert not client.started["shared"].is_set()
        assert (await session.fetch("json", "shared"))["attempt"] == 1


async def test_near_warning_deadline_can_override_spacing_without_waiting_for_a_station(monkeypatch):
    async with setup(monkeypatch, gap=60) as (pacer, client):
        client.gates["station"] = asyncio.Event()
        station = asyncio.create_task(job(pacer).fetch("json", "station"))
        await started(client, "station")
        urgent = job(pacer, "warning", urgent=True, deadline=pacer.clock() + .01)
        assert (await asyncio.wait_for(urgent.fetch("json", "warning"), 1))["url"] == "warning"
        assert not station.done() and pacer.deadline_overrides >= 1
        client.gates["station"].set()
        await station


async def test_many_waiters_still_have_bounded_transport_parallelism(monkeypatch):
    async with setup(monkeypatch) as (pacer, client):
        gate = asyncio.Event()
        urls = [f"station{i}" for i in range(20)] + [f"warning{i}" for i in range(10)]
        client.gates.update(dict.fromkeys(urls, gate))
        tasks = [asyncio.create_task(job(pacer, urgent=url.startswith("warning")).fetch("json", url)) for url in urls]
        await started(client, "station0")
        await started(client, "station1")
        await started(client, "warning0")
        assert client.peak == 3 and client.normal_peak == 2
        gate.set()
        await asyncio.wait_for(asyncio.gather(*tasks), 1)
        assert len(client.calls) == len(urls) and client.peak <= 3 and client.normal_peak <= 2


@pytest.mark.parametrize("bootstrap", [False, True])
async def test_eager_task_factory_preserves_shared_request_lifetimes(monkeypatch, bootstrap):
    async with setup(monkeypatch) as (pacer, client):
        loop = asyncio.get_running_loop()
        previous = loop.get_task_factory()
        loop.set_task_factory(asyncio.eager_task_factory)
        try:
            session = job(pacer, bootstrap=bootstrap)
            a, b = await asyncio.gather(session.fetch("json", "shared"), session.fetch("json", "shared"))
            assert a == b and len(client.calls) == 1
            assert (await session.fetch("json", "next"))["url"] == "next"
        finally:
            loop.set_task_factory(previous)


async def test_ready_warning_priority_is_preserved_with_an_eager_task_factory(monkeypatch):
    async with setup(monkeypatch) as (pacer, client):
        loop = asyncio.get_running_loop()
        previous = loop.get_task_factory()
        loop.set_task_factory(asyncio.eager_task_factory)
        try:
            deadline = pacer.clock() + 1000
            await asyncio.gather(*(job(pacer, urgent=url.startswith("warning"), deadline=deadline).fetch("json", url)
                                   for url in ["station1", "warning1", "station2", "warning2"]))
            assert [call[2] for call in client.calls] == ["warning1", "warning2", "station1", "station2"]
        finally:
            loop.set_task_factory(previous)
