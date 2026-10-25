"""Measured HTTP pacing shared by the automatic providers of one advisor.

The queue spaces real requests, not synthetic timer ticks. Deadlines and warning
requests take precedence over spacing. No provider's cache lifetime is extended.
This module deliberately has no Home Assistant dependency (including its clock).
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import time
from typing import Any

import aiohttp


@dataclass(order=True)
class _Request:
    deadline: float
    sequence: int
    operation: Any = field(compare=False)
    future: asyncio.Future = field(compare=False)
    urgent: bool = field(compare=False, default=False)
    bootstrap: bool = field(compare=False, default=False)
    started: bool = field(compare=False, default=False)


@dataclass
class _Flight:
    """Interests in one shared transport, independent of its first caller."""

    deadline: float
    urgent: bool
    bootstrap: bool
    waiters: int = 1
    pending: _Request | None = None


class RequestPacer:
    """Earliest-deadline queue with a bounded three-request startup."""

    def __init__(self, session: Any, *, clock=time.monotonic) -> None:
        self.session = session
        self.clock = clock
        self.weights: dict[str, tuple[float, float]] = {}
        self.queue: list[_Request] = []
        self.wake = asyncio.Event()
        self.worker: asyncio.Task | None = None
        self.active: dict[tuple, asyncio.Task] = {}
        self._flights: dict[asyncio.Task, _Flight] = {}
        self._transports: set[asyncio.Task] = set()
        self._normal_transports = 0
        self.sequence = 0
        self.last_request: float | None = None
        self.requests = 0
        self.retries = 0
        self.deadline_overrides = 0
        self.urgent_bypasses = 0
        self.closed = False

    @property
    def gap(self) -> float:
        rate = sum(count / interval for count, interval in self.weights.values())
        # Reserve 20% of the budget for recovery and changing station coverage.
        return min(120.0, max(0.25, 0.8 / rate)) if rate else 1.0

    def job(self, name: str, period: float, deadline: float, *, bootstrap=False,
            urgent=False) -> ScheduledSession:
        return ScheduledSession(self, name, period, deadline, bootstrap, urgent)

    def learned(self, name: str, count: int, period: float) -> None:
        previous = self.weights.get(name)
        # A newly necessary fallback is budgeted immediately; reduction is gradual.
        measured = max(float(count), previous[0] * 0.75 + count * 0.25) if previous else float(count)
        self.weights[name] = (max(1.0, measured), period)

    async def _run(self) -> None:
        try:
            # Batch already-ready submissions before choosing their order, also
            # under an eager task factory. This does not wait for network work.
            await asyncio.sleep(0)
            while self.queue and not self.closed:
                # Preserve freshness deadlines; warnings win ties before FIFO.
                self.queue.sort(key=lambda item: (item.deadline, not item.urgent, item.sequence))
                self.queue[:] = [item for item in self.queue if not item.future.done()]
                # At most three transports, at most two ordinary transports:
                # slow stations cannot occupy the capacity reserved for warnings.
                request = next((item for item in self.queue
                                if len(self._transports) < 3
                                and (item.urgent or self._normal_transports < 2)), None)
                if request is None:
                    if not self.queue:
                        break
                    self.wake.clear()
                    await self.wake.wait()
                    continue
                now = self.clock()
                paced_due = now if request.bootstrap or self.last_request is None else self.last_request + self.gap
                # A normally paced station must not make an eligible warning
                # wait merely because the station has an earlier deadline.
                if not request.urgent and paced_due > now:
                    latest_normal = request.deadline - 20.0 * sum(
                        1 for item in self.queue if item.deadline <= request.deadline)
                    if latest_normal > now:
                        warning = next((item for item in self.queue if item.urgent), None)
                        if warning is not None:
                            request = warning
                            paced_due = now if request.bootstrap or self.last_request is None else self.last_request + self.gap
                due = now if request.urgent else paced_due
                remaining = sum(1 for item in self.queue if item.deadline <= request.deadline)
                # A 20-second HTTP timeout must fit before a source's refresh deadline.
                latest = request.deadline - 20.0 * remaining
                override = not request.bootstrap and latest < due
                if override:
                    due = max(now, latest)
                if due > now:
                    self.wake.clear()
                    try:
                        await asyncio.wait_for(self.wake.wait(), due - now)
                    except TimeoutError:
                        pass
                    continue
                self.queue.remove(request)
                if request.urgent and paced_due > now:
                    self.urgent_bypasses += 1
                if override:
                    self.deadline_overrides += 1
                self.last_request = self.clock()
                self._start_transport(request)
        finally:
            self.worker = None

    def _start_transport(self, request: _Request) -> None:
        request.started = True
        normal = not request.urgent
        if normal:
            self._normal_transports += 1

        async def run():
            if request.future.cancelled():
                raise asyncio.CancelledError
            self.requests += 1
            return await request.operation()

        task = asyncio.create_task(run())
        self._transports.add(task)

        def finished(done):
            self._transports.discard(done)
            if normal:
                self._normal_transports -= 1
            if done.cancelled():
                request.future.cancel()
            else:
                error = done.exception()  # Retrieve even when the last waiter left.
                if not request.future.done():
                    if error is not None:
                        request.future.set_exception(error)
                    else:
                        request.future.set_result(done.result())
            self.wake.set()

        task.add_done_callback(finished)
        request.future.add_done_callback(lambda future: task.cancel() if future.cancelled() and not task.done() else None)

    async def submit(self, operation, *, deadline: float, bootstrap: bool, urgent: bool,
                     flight: _Flight | None = None):
        if self.closed:
            raise asyncio.CancelledError
        future = asyncio.get_running_loop().create_future()
        self.sequence += 1
        request = _Request(deadline, self.sequence, operation, future, urgent, bootstrap)
        if flight is not None:
            flight.pending = request
        self.queue.append(request)
        self.wake.set()
        if self.worker is None or self.worker.done():
            self.worker = asyncio.create_task(self._run())
        try:
            return await future
        finally:
            if not future.done():
                future.cancel()
            if flight is not None and flight.pending is request:
                flight.pending = None
            self.wake.set()

    async def close(self) -> None:
        self.closed = True
        for request in self.queue:
            request.future.cancel()
        self.queue.clear()
        tasks = set(self.active.values()) | set(self._flights) | self._transports
        if self.worker is not None:
            tasks.add(self.worker)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self.active.clear()
        self._flights.clear()

    def diagnostics(self) -> dict[str, Any]:
        return {"requests": self.requests, "retries": self.retries,
                "spacing_seconds": round(self.gap, 2), "queued": len(self.queue),
                "deadline_overrides": self.deadline_overrides,
                "urgent_bypasses": self.urgent_bypasses,
                "expected_requests_per_hour": round(sum(n * 3600 / p for n, p in self.weights.values()), 2)}


class ScheduledSession:
    """A provider job's view of the shared HTTP queue."""

    def __init__(self, pacer, name, period, deadline, bootstrap, urgent):
        self.pacer, self.name, self.period = pacer, name, period
        self.deadline, self.bootstrap, self.urgent = deadline, bootstrap, urgent
        self.count = 0

    def finish(self) -> None:
        self.pacer.learned(self.name, self.count, self.period)

    async def fetch(self, mode: str, url: str, *, method="GET", **kwargs):
        if self.pacer.closed:
            raise asyncio.CancelledError
        key = (method, url, mode, repr(sorted((str(k), repr(v)) for k, v in kwargs.items())))
        existing = self.pacer.active.get(key)
        if existing is not None and not existing.done():
            flight = self.pacer._flights[existing]
            flight.waiters += 1
            flight.deadline = min(flight.deadline, self.deadline)
            flight.urgent |= self.urgent
            flight.bootstrap |= self.bootstrap
            if flight.pending is not None and not flight.pending.started:
                flight.pending.deadline = flight.deadline
                flight.pending.urgent = flight.urgent
                flight.pending.bootstrap = flight.bootstrap
                self.pacer.wake.set()
            return await self._wait(existing, flight, key)
        flight = _Flight(self.deadline, self.urgent, self.bootstrap)

        async def operation():
            self.count += 1
            previous = self.pacer.weights.get(self.name)
            if previous is not None and self.count > previous[0]:
                # Learn newly necessary reserves during this very cycle.
                self.pacer.weights[self.name] = (float(self.count), self.period)
                self.pacer.wake.set()
            async with self.pacer.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                if mode == "json":
                    return await response.json(content_type=None)
                if mode == "text":
                    return await response.text()
                return await response.read()

        async def execute():
            try:
                # Retry transport errors once. Station-content errors are handled
                # by the station selector, which tries alternatives first.
                for attempt in range(2):
                    try:
                        return await self.pacer.submit(operation, deadline=flight.deadline,
                            bootstrap=flight.bootstrap, urgent=flight.urgent, flight=flight)
                    except (OSError, TimeoutError, aiohttp.ClientConnectionError) as exc:
                        if attempt or self.pacer.closed:
                            raise exc
                    except Exception as exc:
                        status = getattr(exc, "status", 0)
                        if attempt or status not in {408, 429, 500, 502, 503, 504}:
                            raise
                        headers = getattr(exc, "headers", {}) or {}
                        raw = str(headers.get("Retry-After", "1"))
                        # Do not turn a long server cooldown into an early retry.
                        if not raw.isdigit() or int(raw) > 30:
                            raise
                        await asyncio.sleep(max(1, int(raw)))
                    self.pacer.retries += 1
            finally:
                if self.pacer.active.get(key) is asyncio.current_task():
                    self.pacer.active.pop(key, None)

        task = asyncio.create_task(execute())
        self.pacer.active[key] = task
        self.pacer._flights[task] = flight

        def finished(done):
            if not done.cancelled():
                done.exception()
            if not flight.waiters:
                self.pacer._flights.pop(done, None)
            if self.pacer.active.get(key) is done:
                self.pacer.active.pop(key, None)

        task.add_done_callback(finished)
        return await self._wait(task, flight, key)

    async def _wait(self, task, flight: _Flight, key):
        try:
            # The initiating caller has the same cancellation rights as every
            # follower. Only the last departing participant cancels the transport.
            return await asyncio.shield(task)
        finally:
            flight.waiters -= 1
            if not flight.waiters:
                if self.pacer.active.get(key) is task:
                    self.pacer.active.pop(key, None)
                if task.done():
                    self.pacer._flights.pop(task, None)
                else:
                    task.cancel()
