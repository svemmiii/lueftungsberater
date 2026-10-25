"""Urgent warning dispatch has no intentional wait for ordinary HTTP pacing."""
import asyncio

import pytest

from test_v0119_http_concurrency_pure import job, setup, started


@pytest.mark.parametrize("gap", [0.25, 60, 120])
async def test_free_warning_capacity_bypasses_even_a_long_unexpired_gap(monkeypatch, gap):
    async with setup(monkeypatch, gap=gap) as (pacer, client):
        assert (await job(pacer).fetch("json", "station"))["url"] == "station"
        warning = job(pacer, "warning", urgent=True)
        assert (await asyncio.wait_for(warning.fetch("json", "warning"), .2))["url"] == "warning"
        assert pacer.urgent_bypasses == 1 and len(client.calls) == 2
        assert pacer.diagnostics()["urgent_bypasses"] == 1


async def test_an_earlier_noncritical_station_deadline_does_not_hide_a_ready_warning(monkeypatch):
    async with setup(monkeypatch, gap=120) as (pacer, client):
        await job(pacer).fetch("json", "station0")
        normal = asyncio.create_task(job(pacer, deadline=pacer.clock() + 300).fetch("json", "station1"))
        await asyncio.sleep(0)
        urgent = job(pacer, "warning", urgent=True, deadline=pacer.clock() + 1000)
        assert (await asyncio.wait_for(urgent.fetch("json", "warning"), .2))["url"] == "warning"
        assert not client.started["station1"].is_set()
        normal.cancel()
        with pytest.raises(asyncio.CancelledError):
            await normal


async def test_an_urgent_joiner_promotes_a_shared_request_waiting_for_spacing(monkeypatch):
    async with setup(monkeypatch, gap=120) as (pacer, client):
        await job(pacer).fetch("json", "station0")
        original = asyncio.create_task(job(pacer).fetch("json", "warning_shared"))
        await asyncio.sleep(0)
        urgent = job(pacer, "warning", urgent=True)
        response = await asyncio.wait_for(urgent.fetch("json", "warning_shared"), .2)
        assert await original == response
        assert sum(call[2] == "warning_shared" for call in client.calls) == 1


async def test_warning_capacity_release_does_not_introduce_another_pacing_delay(monkeypatch):
    async with setup(monkeypatch, gap=120) as (pacer, client):
        for url in ["station1", "station2", "warning1"]:
            client.gates[url] = asyncio.Event()
        stations = [asyncio.create_task(job(pacer, bootstrap=True).fetch("json", url))
                    for url in ["station1", "station2"]]
        for url in ["station1", "station2"]:
            await started(client, url)
        warning1 = asyncio.create_task(job(pacer, "warning", urgent=True).fetch("json", "warning1"))
        await started(client, "warning1")
        warning2 = asyncio.create_task(job(pacer, "warning", urgent=True).fetch("json", "warning2"))
        for _ in range(5):
            await asyncio.sleep(0)
        assert not client.started["warning2"].is_set() and client.peak == 3
        client.gates["warning1"].set()
        assert (await asyncio.wait_for(warning2, .2))["url"] == "warning2"
        for gate in client.gates.values():
            gate.set()
        await asyncio.gather(*stations, warning1)
        assert client.peak == 3 and client.normal_peak == 2


async def test_ordinary_transports_still_obey_spacing_after_an_urgent_warning(monkeypatch):
    async with setup(monkeypatch, gap=.06) as (pacer, client):
        await job(pacer).fetch("json", "station1")
        await job(pacer, "warning", urgent=True).fetch("json", "warning")
        await job(pacer).fetch("json", "station2")
        assert client.calls[-1][0] - client.calls[-2][0] >= .05


async def test_immediate_station_deadlines_retain_their_protection(monkeypatch):
    async with setup(monkeypatch, gap=120) as (pacer, client):
        await job(pacer).fetch("json", "station0")
        normal = job(pacer, deadline=pacer.clock() + .01)
        urgent = job(pacer, "warning", urgent=True)
        values = await asyncio.wait_for(asyncio.gather(normal.fetch("json", "station1"),
                                                        urgent.fetch("json", "warning")), .2)
        assert {value["url"] for value in values} == {"station1", "warning"}
        assert [call[2] for call in client.calls] == ["station0", "station1", "warning"]
        assert pacer.deadline_overrides >= 1
