"""v0.11.9: station reserves, source ages, paced HTTP and official warning time."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import aiohttp
import pytest

from custom_components.lueftungsberater import auto_providers as ap
from custom_components.lueftungsberater.auto_polling import AutomaticPolling
from custom_components.lueftungsberater.const import CONF_SHOW_GENERAL_WARNINGS
from custom_components.lueftungsberater.location import EffectiveLocation
from custom_components.lueftungsberater.polling import RequestPacer
from custom_components.lueftungsberater.providers import _automatic_warning_assessment
from custom_components.lueftungsberater.warning_policy import assess_official_warning

NOW = datetime(2026, 10, 23, 12, 30, tzinfo=timezone.utc)  # 14:30 Berlin
LOCATION = EffectiveLocation(50.7567, 6.993, 60, "DE", "home", NOW)


def warning(**changes):
    return ap.AutoWarningRecord(**{
        "warning_id": "dwd.gusts", "provider_domain": "nina_auto_dwd", "category": "weather",
        "headline": "Amtliche WARNUNG vor SCHWEREN STURMBÖEN", "severity": "Moderate",
        "effective": NOW - timedelta(hours=12), "onset": NOW + timedelta(minutes=30),
        "expires": NOW + timedelta(hours=5), "parameters": {"gusts": "90-100 [km/h]"},
        "evidence_at": NOW, **changes})


@pytest.mark.parametrize("minutes,locked,phase", [(-1, False, "announced"),
    (0, True, "prelock"), (29, True, "prelock"), (30, True, "active"), (299, True, "active")])
def test_exact_thirty_minute_lead(minutes, locked, phase):
    notice = assess_official_warning(warning(), NOW + timedelta(minutes=minutes))
    assert notice["hard_lock"] is locked
    assert notice["phase"] == phase
    assert notice["lock_from"] == NOW.isoformat()
    assert notice["onset"] != notice["effective"]


@pytest.mark.parametrize("gusts,locked", [("30 km/h", False), ("50-60 km/h", False),
    ("65-85 km/h", False), ("89 km/h", False), ("90 km/h", True),
    ("25 m/s", True), ("58 mph", True), ("48 kn", False), ("49 knots", True),
    ("<90 km/h", False), ("100", False), ("nan km/h", False), ("-90 km/h", False)])
def test_only_explicit_official_gust_speed_with_known_unit(gusts, locked):
    notice = assess_official_warning(warning(parameters={"gusts": gusts}), NOW)
    assert notice["hard_lock"] is locked


def test_exposed_gust_maximum_and_severity_are_not_global_window_thresholds():
    notice = assess_official_warning(warning(severity="Extreme", parameters={
        "gusts": "60-75 [km/h]", "exposed gusts": "120 km/h"}), NOW)
    assert notice["gust_max_kmh"] == 75
    assert notice["level"] == "strong"
    assert not notice["hard_lock"]
    assert not assess_official_warning(warning(parameters={}), NOW)["hard_lock"]


@pytest.mark.parametrize("provider,description", [
    ("nws_auto", "Wind gusts up to 60 mph."),
    ("meteoalarm_auto", "Rafales de 100 km/h."),
    ("meteoalarm_auto", "Rachas de 100 km/h."),
    ("meteoalarm_auto", "Raffiche fino a 100 km/h."),
    ("nina_auto_dwd", "Böen mit 100 km/h."),
])
def test_provider_independent_official_speed_policy(provider, description):
    notice = assess_official_warning(warning(provider_domain=provider,
        parameters={}, description=description), NOW)
    assert notice["hard_lock"]


def test_unrelated_numbers_altitudes_and_invalid_time_do_not_lock():
    assert not assess_official_warning(warning(parameters={}, description="90 Liter Regen, Wind 30 km/h."), NOW)["hard_lock"]
    assert assess_official_warning(warning(area_altitude=3000), NOW, elevation=60) is None
    assert not assess_official_warning(warning(area_altitude=3000), NOW)["hard_lock"]
    assert not assess_official_warning(warning(onset=NOW + timedelta(days=1), expires=NOW + timedelta(hours=1)), NOW)["hard_lock"]
    assert assess_official_warning(warning(expires=NOW), NOW) is None
    assert assess_official_warning(warning(msg_type="Cancel"), NOW) is None


def test_explicit_close_instruction_is_not_delayed_until_wind_lead_time():
    notice = assess_official_warning(warning(onset=NOW + timedelta(hours=3),
        parameters={}, instruction="Fenster schließen."), NOW, explicit_close=True)
    assert notice["hard_lock"]


def test_dst_transition_uses_absolute_instants_and_the_same_thirty_minutes():
    for onset in (datetime.fromisoformat("2026-10-25T02:15:00+02:00"),
                  datetime.fromisoformat("2026-10-25T02:15:00+01:00")):
        start = onset.astimezone(timezone.utc) - timedelta(minutes=30)
        record = warning(effective=start - timedelta(hours=1), onset=onset,
                         expires=onset + timedelta(hours=1))
        assert not assess_official_warning(record, start - timedelta(seconds=1))["hard_lock"]
        assert assess_official_warning(record, start)["hard_lock"]


def test_required_notice_visible_without_general_info_and_unrelated_warning_not_hazard(hass, freezer):
    freezer.move_to(NOW)
    config = SimpleNamespace(entry_id="119", data={CONF_SHOW_GENERAL_WARNINGS: False})
    data = ap.AutoWarningData("nina_auto", NOW, True, "DE", warnings=[warning(),
        warning(warning_id="water", category="civil", headline="Trinkwasser abkochen",
                description="", parameters={}, severity="Extreme")])
    with patch("custom_components.lueftungsberater.providers.auto_warning_data", return_value=data):
        assessment = _automatic_warning_assessment(hass, config)
    assert assessment.weather_hard_lock
    assert not assessment.official_close_instruction
    assert [n["id"] for n in assessment.warning_notices] == ["dwd.gusts"]
    assert assessment.warning_ids == {"dwd.gusts"}
    assert assessment.next_transition_at == NOW + timedelta(minutes=30)


@pytest.mark.parametrize("description,locked,speed", [
    ("Böen von 110 km/h, jedoch kein Starkregen.", True, 110),
    ("Böen von 120 km/h, aber kein Hagel.", True, 120),
    ("Böen 110 km/h, in exponierten Lagen 140 km/h.", True, 110),
    ("Böen 75 km/h, in exponierten Lagen 140 km/h.", False, 75),
    ("Böen 110 km/h, nur auf Gipfeln.", False, None),
    ("Windböen von 110 km/h, Schäden sind nicht auszuschließen.", True, 110),
    ("Sturmböen bis 110 km/h ohne nennenswerte Niederschläge.", True, 110),
    ("Wind gusts 110 km/h and lightning is not expected.", True, 110),
    ("Böen über 90 km/h sind ausgeschlossen.", False, None),
    ("Böen 110 km/h sind nicht auszuschließen.", True, 110),
    ("Bei Böen bis 110 km/h sind keine Fenster offen zu lassen.", True, 110),
    ("Böen 85 km/h, in freien Lagen 120 km/h.", False, 85),
])
def test_mixed_official_wind_notice_reaches_ha_safety_assessment(hass, freezer, description, locked, speed):
    freezer.move_to(NOW)
    config = SimpleNamespace(entry_id="wind-scope", data={CONF_SHOW_GENERAL_WARNINGS: False})
    feed = ap.AutoWarningData("nina_auto", NOW, True, "DE", warnings=[
        warning(description=description, parameters={})])
    with patch("custom_components.lueftungsberater.providers.auto_warning_data", return_value=feed):
        result = _automatic_warning_assessment(hass, config)
    assert result.weather_hard_lock is locked
    assert not result.official_close_instruction
    assert len(result.warning_notices) == 1
    assert result.warning_notices[0]["gust_max_kmh"] == speed
    assert result.warning_notices[0]["hard_lock"] is locked


def dwd_bytes(**changes):
    values = {key: "20" for key in ap._DWD_FIELDS}
    values.update(relative_humidity="60", present_weather="1")
    values.update(changes)
    keys = list(values)
    return ("date;time;" + ";".join(keys) + "\nunit;unit;" + ";".join("-" for _ in keys)
        + "\ndesc;desc;" + ";".join("-" for _ in keys)
        + "\n20261023;1200;" + ";".join(values.values()) + "\n").encode()


async def test_dwd_lazy_nearest_station_and_invalid_field_reserve(freezer):
    freezer.move_to(NOW)
    candidates = [(ap.DwdStation(str(i), str(i), 50.7, 7.1), float(i)) for i in range(8)]
    with (patch.object(ap, "_dwd_station_candidates", AsyncMock(return_value=candidates)),
          patch.object(ap, "_get_bytes", AsyncMock(side_effect=[
              dwd_bytes(relative_humidity="999"), dwd_bytes(relative_humidity="72")])) as get):
        _, observations = await ap._fetch_dwd_observations(object(), LOCATION, ap.AutoProviderState())
    assert get.await_count == 2
    assert observations[0][0].station_id == "0"
    assert "relative_humidity" not in observations[0][2]
    assert observations[1][2]["relative_humidity"] == "72"


async def test_dwd_complete_response_stops_after_one_and_failed_station_retries(freezer):
    freezer.move_to(NOW)
    candidates = [(ap.DwdStation(str(i), str(i), 50.7, 7.1), float(i)) for i in range(8)]
    with (patch.object(ap, "_dwd_station_candidates", AsyncMock(return_value=candidates)),
          patch.object(ap, "_get_bytes", AsyncMock(return_value=dwd_bytes())) as get):
        await ap._fetch_dwd_observations(object(), LOCATION, ap.AutoProviderState())
    assert get.await_count == 1
    with (patch.object(ap, "_dwd_station_candidates", AsyncMock(return_value=candidates[:2])),
          patch.object(ap, "_get_bytes", AsyncMock(side_effect=[
              TimeoutError(), b"broken", dwd_bytes()])) as get):
        _, observations = await ap._fetch_dwd_observations(object(), LOCATION, ap.AutoProviderState())
    assert get.await_count == 3
    assert observations[0][0].station_id == "0"


def uba_payload(stamp="2026-10-23 14:00:00", kinds=range(1, 6), value=10):
    return {"data": {"station": {stamp: [stamp, 1, 0, *[[k, value, 1] for k in kinds]]}}}


async def test_uba_lazy_per_pollutant_and_no_stale_success(freezer):
    freezer.move_to(NOW)
    candidates = [(ap.UbaStation(str(i), str(i), str(i), 50.7, 7.1), i) for i in range(12)]
    components = dict(enumerate(["pm2_5", "pm10", "no2", "o3", "so2"], start=1))
    with (patch.object(ap, "_uba_station_candidates", AsyncMock(return_value=candidates)),
          patch.object(ap, "_uba_component_index", AsyncMock(return_value=components)),
          patch.object(ap, "_get_json", AsyncMock(side_effect=[
              uba_payload(kinds=[1, 2], value=11), uba_payload(kinds=[2, 3, 4, 5], value=22)])) as get):
        values, sources = await ap._fetch_uba_air_quality(object(), LOCATION, ap.AutoProviderState())
    assert get.await_count == 2
    assert values["pm10"] == 11
    assert sources["o3"].startswith("uba_station:1:")
    assert values.observed_at["pm10"] == NOW.replace(minute=0)
    stale = ap._parse_uba_airquality_fresh(uba_payload("2026-10-23 09:00:00"), components, ZoneInfo("Europe/Berlin"))
    assert not stale


def test_another_source_does_not_freshen_old_measurements(hass, freezer):
    freezer.move_to(NOW)
    config = SimpleNamespace(entry_id="age", data={})
    state = ap._state(hass, config)
    state.weather = ap.AutoWeatherData("test", NOW, temperature=20, humidity=50,
        measurement_sources={"temperature": {"fetched_at": (NOW - timedelta(hours=2)).isoformat()},
                             "humidity": {"fetched_at": NOW.isoformat()}},
        air_quality_values={"o3": 50}, air_quality_updated_at={"o3": NOW - timedelta(hours=4)})
    exposed = ap.auto_weather_data(hass, config)
    assert exposed.temperature is None
    assert exposed.humidity == 50
    assert not exposed.air_quality_values


async def test_pacer_spaces_and_coalesces_actual_requests(monkeypatch):
    class Response:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        def raise_for_status(self):
            pass
        async def json(self, **kwargs):
            await asyncio.sleep(0)
            return {"ok": True}
    calls = []
    def request(method, url, **kwargs):
        calls.append((asyncio.get_running_loop().time(), url))
        return Response()
    pacer = RequestPacer(SimpleNamespace(request=request))
    monkeypatch.setattr(RequestPacer, "gap", property(lambda self: 0.01))
    session = pacer.job("weather", 900, pacer.clock() + 1000)
    await asyncio.gather(*(session.fetch("json", f"https://example.invalid/{i // 2}") for i in range(10)))
    session.finish()
    assert len(calls) == 5
    assert session.count == 5
    assert all(b[0] - a[0] >= .008 for a, b in zip(calls, calls[1:]))
    assert pacer.weights["weather"][0] == 5
    await pacer.close()


async def test_pacer_deadline_priority_and_startup_parallelism(monkeypatch):
    pacer = RequestPacer(None)
    monkeypatch.setattr(RequestPacer, "gap", property(lambda self: .01))
    called = []
    async def operation(name):
        called.append(name)
    deadline = pacer.clock() + 1000
    await asyncio.gather(
        pacer.submit(lambda: operation("weather"), deadline=deadline, bootstrap=False, urgent=False),
        pacer.submit(lambda: operation("warning"), deadline=deadline - 500, bootstrap=False, urgent=True))
    assert called == ["warning", "weather"]
    inflight, peak = 0, 0
    async def bootstrap_request():
        nonlocal inflight, peak
        inflight += 1
        peak = max(peak, inflight)
        await asyncio.sleep(.005)
        inflight -= 1
    await asyncio.gather(*(pacer.submit(bootstrap_request, deadline=deadline,
        bootstrap=True, urgent=False) for _ in range(12)))
    assert peak == 2  # The third transport slot is reserved for urgent warnings.
    await pacer.close()


async def test_transport_recovery_is_bounded_and_shutdown_cancels_queue():
    class BadSession:
        def request(self, *args, **kwargs):
            raise aiohttp.ClientConnectionError("simulated")
    pacer = RequestPacer(BadSession())
    session = pacer.job("forecast", 900, pacer.clock() + 1000, bootstrap=True)
    with pytest.raises(aiohttp.ClientConnectionError):
        await session.fetch("json", "https://example.invalid/weather")
    assert session.count == 2
    assert pacer.retries == 1
    await pacer.close()
    with pytest.raises(asyncio.CancelledError):
        await session.fetch("json", "https://example.invalid/closed")


async def test_location_generation_ignores_late_old_response(hass, freezer):
    freezer.move_to(NOW)
    config = SimpleNamespace(entry_id="move", title="Test", data={})
    runtime = AutomaticPolling(hass, config, AsyncMock())
    runtime.location = LOCATION
    gate = asyncio.Event()
    async def delayed(*args):
        await gate.wait()
        return ap.AutoWarningData("nina_auto", NOW, True, "DE", warnings=[warning()])
    with patch.object(ap, "_fetch_auto_warning", delayed):
        task = asyncio.create_task(runtime._job("warnings", bootstrap=True))
        await asyncio.sleep(0)
        runtime.generation += 1
        runtime.location = replace(LOCATION, latitude=53)
        gate.set()
        assert not await task
    assert ap._state(hass, config).warning is None
    await runtime.close()


async def test_warning_boundary_updates_locally_without_another_http_request(hass, freezer):
    from homeassistant.config_entries import ConfigEntryState
    from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
    from custom_components.lueftungsberater.const import DOMAIN
    from custom_components.lueftungsberater.outside import LueftungsberaterOutsideCoordinator

    before = NOW - timedelta(minutes=1)
    freezer.move_to(before)
    config = MockConfigEntry(domain=DOMAIN, title="Test", data={
        "weather_source_mode": "manual", "warning_source_mode": "auto"})
    config.add_to_hass(hass)
    config._async_set_state(hass, ConfigEntryState.SETUP_IN_PROGRESS, None)
    ap._state(hass, config).warning = ap.AutoWarningData("nina_auto", before, True, "DE",
        safety_source_key="auto_warning:50.7567:6.9930", warnings=[warning(evidence_at=before)])
    coordinator = LueftungsberaterOutsideCoordinator(hass, config)
    with (patch.object(AutomaticPolling, "start", AsyncMock()) as start,
          patch.object(coordinator, "_candidate_location", return_value=LOCATION),
          patch.object(ap, "_get_json", AsyncMock()) as http,
          patch("custom_components.lueftungsberater.outside.async_apply_persistent_safety_state", AsyncMock())):
        try:
            await coordinator.async_start()
            assert not coordinator.data.warnings.weather_hard_lock
            assert coordinator._warning_transition_at == NOW
            freezer.move_to(NOW)
            async_fire_time_changed(hass, NOW)
            await hass.async_block_till_done()
            assert coordinator.data.warnings.weather_hard_lock
            assert coordinator.data.warnings.warning_notices[0]["phase"] == "prelock"
            freezer.move_to(NOW + timedelta(minutes=30))
            async_fire_time_changed(hass, ap.dt_util.utcnow())
            await hass.async_block_till_done()
            assert coordinator.data.warnings.weather_hard_lock
            assert coordinator.data.warnings.warning_notices[0]["phase"] == "active"
            start.assert_awaited_once()
            http.assert_not_awaited()
        finally:
            await coordinator.async_shutdown()
    assert coordinator._warning_transition_unsub is None


async def test_forecast_deadline_tracks_actual_success_after_initial_phase(hass, freezer, monkeypatch):
    freezer.move_to(NOW)
    config = SimpleNamespace(entry_id="deadline", title="Test", data={})
    runtime = AutomaticPolling(hass, config, AsyncMock())
    clock = [0.0]
    runtime.pacer.clock = lambda: clock[0]
    calls = []
    original_sleep = asyncio.sleep

    async def virtual_sleep(seconds):
        clock[0] += seconds
        freezer.tick(timedelta(seconds=seconds))
        await original_sleep(0)

    async def job(name, *, deadline):
        calls.append((clock[0], deadline))
        ap._state(hass, config).forecast_updated_at = ap.dt_util.utcnow()
        if len(calls) == 3:
            runtime.stopping = True
        return True

    monkeypatch.setattr(asyncio, "sleep", virtual_sleep)
    monkeypatch.setattr(runtime, "_job", job)
    await runtime._loop("forecast")
    assert len(calls) == 3
    assert all(850 <= b[0] - a[0] <= 900 for a, b in zip(calls, calls[1:]))
    assert all(deadline - started >= 19.9 for started, deadline in calls)
    await runtime.close()


async def test_mixed_hard_warning_kinds_expire_independently_after_restart(hass, freezer):
    import copy
    from custom_components.lueftungsberater import safety_state
    from custom_components.lueftungsberater.providers import WarningAssessment

    freezer.move_to(NOW)
    config = SimpleNamespace(entry_id="mixed", title="Test", data={"warning_source_mode": "auto"})
    base = "auto_warning:50.7567:6.9930"
    smoke = warning(warning_id="mow.smoke", provider_domain="nina_auto_mowas", category="civil",
        headline="Rauch", parameters={}, instruction="Fenster und Türen geschlossen halten.",
        onset=NOW, expires=NOW + timedelta(minutes=10))
    feed = ap.AutoWarningData("nina_auto", NOW, True, "DE", safety_source_key=base,
        warnings=[warning(), smoke], source_availability={"nina_auto_dwd": True, "nina_auto_mowas": True})
    ap._state(hass, config).warning = feed
    active = _automatic_warning_assessment(hass, config)
    disk = {}

    async def save(hass, entry, state):
        disk.clear()
        disk.update(copy.deepcopy(state))

    with (patch.object(safety_state, "_async_state", AsyncMock(return_value={})),
          patch.object(safety_state, "_async_save_state", save),
          patch.object(safety_state, "_weather_provider_availability", return_value=("clear", "weather"))):
        await safety_state.async_apply_persistent_safety_state(hass, config, SimpleNamespace(), active)
    parts = {item["id"]: item for item in disk["channels"]["warning"]["warning_records"]}
    assert parts["dwd.gusts"]["kind"] == "warning_weather_danger"
    assert not parts["dwd.gusts"]["official_close_instruction"]
    assert parts["mow.smoke"]["kind"] == "nina_danger"
    assert parts["mow.smoke"]["valid_until"] == smoke.expires.isoformat()
    # Both are still unresolved immediately after a restart.
    for minutes in (1, 31):
        freezer.move_to(NOW + timedelta(minutes=minutes))
        outage = WarningAssessment(provider_domain="nina_auto", safety_source_key=base,
            provider_availability={base: False, f"{base}:nina_auto_dwd": False, f"{base}:nina_auto_mowas": False})
        with (patch.object(safety_state, "_async_state", AsyncMock(return_value=copy.deepcopy(disk))),
              patch.object(safety_state, "_async_save_state", save),
              patch.object(safety_state, "_weather_provider_availability", return_value=("clear", "weather"))):
            await safety_state.async_apply_persistent_safety_state(hass, config, SimpleNamespace(), outage)
        assert outage.weather_hard_lock
        assert outage.official_close_instruction is (minutes < 10)
        wind = next(n for n in outage.warning_notices if n["id"] == "dwd.gusts")
        assert wind["using_cached_data"]
        assert wind["phase"] == ("prelock" if minutes < 30 else "active")
        if minutes > 30:
            assert outage.weather_reason_key == "official_wind_lock"
            assert outage.nina_status != "danger"


@pytest.mark.parametrize("invalid", [float("inf"), float("nan"), True, 1.5])
def test_invalid_pollutant_identifiers_do_not_become_other_pollutants(invalid):
    assert ap._uba_measurement_tuple([invalid, 10, 1]) is None


def test_invalid_condition_does_not_discard_other_station_fields(freezer):
    freezer.move_to(NOW)
    measurement = ap._valid_dwd_measurement(dwd_bytes(present_weather="inf"))
    assert "present_weather" not in measurement
    assert measurement["relative_humidity"] == "60"
    assert not assess_official_warning(warning(headline="Sturmböen oberhalb 1500 m"), NOW)["hard_lock"]
