"""Time-based room tests using real HA events, timers and session memory.

Only the external weather feed is controlled. Window tracking, coordinator,
humidity/CO2 memory, engine and sensor/history projections are production code.
"""

from datetime import timedelta
import json
import logging
from types import SimpleNamespace

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.lueftungsberater.airing import async_get_or_create_tracker
from custom_components.lueftungsberater.const import (
    CONF_CO2, CONF_DISPLAY_MODE, CONF_INDOOR_HUMIDITY, CONF_INDOOR_TEMP,
    CONF_TARGET_TEMP, CONF_WARNING_SOURCE, CONF_WINDOWS,
    DATA_OUTSIDE_COORDINATORS, DOMAIN,
)
from custom_components.lueftungsberater.coordinator import LueftungsberaterRoomCoordinator
from custom_components.lueftungsberater.providers import WeatherAssessment, WarningAssessment
from custom_components.lueftungsberater.sensor import HistoryRoomSensor, RoomAdvisorSensor


class Lifetime:
    def __init__(self, hass, freezer, coordinator, outside, tracker, advisor, history):
        self.hass, self.freezer = hass, freezer
        self.coordinator, self.outside, self.tracker = coordinator, outside, tracker
        self.advisor, self.history = advisor, history
        self.start = dt_util.utcnow()
        self.minute = 0
        self.trace = []

    @property
    def result(self):
        return self.coordinator.data.result

    def capture(self):
        snapshot = self.coordinator.data
        result = snapshot.result
        attrs = self.advisor.extra_state_attributes
        action, color = attrs["recommendation_key"], attrs["status"]
        closing = {"better_close", "close_now", "can_close"}
        if result is not None:
            assert self.history.native_value == action
            assert self.history.extra_state_attributes["room_status"] == attrs["room_status"]
            if result.safety_lock:
                assert color == "locked"
            else:
                if action in closing:
                    assert color == "green", (self.minute, action, color)
                if color == "yellow":
                    assert action not in closing
                if color == "green":
                    assert action not in {"open_now", "keep_open", "room_need", "room_urgent", "room_keep_brief"}
            if action in closing | {"room_good", "room_watch", "window_state_unknown"}:
                assert attrs["duration_key"] == "not_needed"
        state = self.coordinator._humidity_session
        record = {
            "minute": self.minute, "temperature": attrs["temperature_inside"],
            "humidity": attrs["humidity_inside"], "absolute_humidity": attrs["absolute_humidity_inside"],
            "temperature_outside": attrs["temperature_outside"], "humidity_outside": attrs["humidity_outside"],
            "co2": attrs["co2_ppm"], "window_open": attrs["window_open"],
            "window_data_status": attrs["window_data_status"],
            "status": color, "action": action, "mode": attrs["mode"],
            "reason": attrs["reason_key"], "safety_lock": attrs["safety_lock"],
            "humidity_active": state.session_active, "humidity_disarmed": state.disarmed,
            "humidity_exhausted": state.exhausted,
            "co2_active": self.coordinator._co2_hysteresis.session_active,
        }
        self.trace.append(record)
        return record

    async def at(self, minute, *, rh=None, temperature=None, co2=None, window=None,
                 outdoor_temperature=None, warning=None, **weather):
        assert minute >= self.minute
        if outdoor_temperature is not None:
            weather["temperature"] = outdoor_temperature
        ticks = range(self.minute + 1, minute + 1) if minute > self.minute else [minute]
        for tick in ticks:
            self.freezer.move_to(self.start + timedelta(minutes=tick))
            self.minute = tick
            if tick == minute:
                for entity, value, unit in (
                    ("sensor.lifetime_humidity", rh, "%"),
                    ("sensor.lifetime_temperature", temperature, "°C"),
                    ("sensor.lifetime_co2", co2, "ppm"),
                ):
                    if value is not None:
                        self.hass.states.async_set(entity, value, {"unit_of_measurement": unit})
                if window is not None:
                    self.hass.states.async_set("binary_sensor.lifetime_window", window)
                if weather or warning is not None:
                    assessment = self.outside.data.weather
                    for key, value in weather.items():
                        setattr(assessment, key, value)
                    self.outside.async_set_updated_data(SimpleNamespace(
                        weather=assessment,
                        warnings=WarningAssessment(**warning) if warning is not None else self.outside.data.warnings,
                    ))
            await self.hass.async_block_till_done()
            async_fire_time_changed(self.hass, dt_util.utcnow())
            await self.hass.async_block_till_done()
            self.capture()
        return self.trace[-1]


@pytest.fixture
async def lifetime(hass, enable_custom_integrations, freezer, record_property, request):
    freezer.move_to("2026-10-17T08:00:00+00:00")
    for entity, value, unit in (
        ("sensor.lifetime_temperature", 22, "°C"),
        ("sensor.lifetime_humidity", getattr(request, "param", 70), "%"),
        ("sensor.lifetime_co2", 800, "ppm"),
    ):
        hass.states.async_set(entity, value, {"unit_of_measurement": unit})
    hass.states.async_set("binary_sensor.lifetime_window", "off")
    entry = MockConfigEntry(
        domain=DOMAIN, title="Lifetime",
        data={CONF_DISPLAY_MODE: "room_air", CONF_WARNING_SOURCE: "controlled-warning-provider"},
        subentries_data=[{
            "subentry_type": "room", "title": "Wohnzimmer", "unique_id": None,
            "data": {CONF_INDOOR_TEMP: "sensor.lifetime_temperature",
                     CONF_INDOOR_HUMIDITY: "sensor.lifetime_humidity",
                     CONF_CO2: "sensor.lifetime_co2", CONF_TARGET_TEMP: 22,
                     CONF_WINDOWS: ["binary_sensor.lifetime_window"]},
        }],
    )
    entry.add_to_hass(hass)
    entry._async_set_state(hass, ConfigEntryState.SETUP_IN_PROGRESS, None)
    room = next(iter(entry.subentries.values()))
    outside = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="controlled-outside", config_entry=entry)
    outside.async_set_updated_data(SimpleNamespace(
        weather=WeatherAssessment(temperature=20, humidity=45), warnings=WarningAssessment(),
    ))
    hass.data.setdefault(DOMAIN, {}).setdefault(DATA_OUTSIDE_COORDINATORS, {})[entry.entry_id] = outside
    tracker = await async_get_or_create_tracker(hass, entry, room)
    coordinator = LueftungsberaterRoomCoordinator(hass, entry, room)
    scenario = None
    try:
        await coordinator.async_start()
        advisor = RoomAdvisorSensor(entry, room, coordinator)
        advisor.hass = hass
        history = HistoryRoomSensor(entry, room, coordinator, "decision")
        scenario = Lifetime(hass, freezer, coordinator, outside, tracker, advisor, history)
        scenario.capture()
        yield scenario
    finally:
        if scenario is not None:
            record_property("timeline", json.dumps(scenario.trace))
        await coordinator.async_shutdown()
        await tracker.async_stop()
        await outside.async_shutdown()


async def test_humidity_falls_to_target_then_stays_calm(lifetime):
    s = lifetime
    need = await s.at(1, rh=70)
    assert need["status"] in {"orange", "red"}
    await s.at(2, window="on")
    assert s.coordinator._humidity_session.session_active
    for minute, humidity in [(5, 68), (10, 65), (15, 62), (20, 59), (25, 56)]:
        await s.at(minute, rh=humidity)
    assert not s.coordinator._humidity_session.session_active
    assert s.coordinator._humidity_session.disarmed
    assert s.result.room_status_color == "green"
    await s.at(26, window="off")
    for minute, humidity in [(30, 59), (35, 60.2), (40, 59.8), (45, 60.1)]:
        record = await s.at(minute, rh=humidity)
        assert record["action"] not in {"room_need", "room_urgent", "open_now"}


async def test_humidity_stagnates_and_timer_finishes_attempt(lifetime):
    s = lifetime
    await s.at(1, rh=70)
    await s.at(2, window="on")
    assert s.coordinator._humidity_session.session_active
    await s.at(16)
    assert s.coordinator._humidity_session.session_active
    record = await s.at(18)
    assert record["humidity_exhausted"]
    assert record["action"] == "can_close"
    assert record["status"] == "green"
    await s.at(19, window="off")
    record = await s.at(90)
    assert record["humidity_disarmed"]
    assert record["action"] == "room_watch"


async def test_slow_measurable_drying_does_not_exhaust_the_session(lifetime):
    s = lifetime
    await s.at(1, rh=70)
    await s.at(2, window="on")
    for minute, humidity in [(10, 69.2), (17, 68.5), (25, 68), (32, 67)]:
        record = await s.at(minute, rh=humidity)
        assert record["humidity_active"]
        assert not record["humidity_exhausted"]
        assert record["action"] not in {"close_now", "better_close", "can_close"}


async def test_rising_relative_humidity_during_cooling_can_still_be_drying(lifetime):
    s = lifetime
    initial = await s.at(1, rh=68)
    await s.at(2, window="on")
    await s.at(10, rh=70, temperature=21)
    record = await s.at(17, rh=72, temperature=20)

    assert record["humidity"] > initial["humidity"]
    assert record["absolute_humidity"] < initial["absolute_humidity"] - 0.25
    assert record["humidity_active"]
    assert not record["humidity_exhausted"]


async def test_humidity_rises_without_measurable_success(lifetime):
    s = lifetime
    await s.at(1, rh=70)
    await s.at(2, window="on")
    await s.at(8, rh=71)
    record = await s.at(18, rh=72)

    assert record["humidity_exhausted"]
    assert record["status"] == "green"
    assert record["action"] == "can_close"
    await s.at(19, window="off")
    record = await s.at(25)
    assert record["status"] == "yellow"
    assert record["action"] == "room_watch"


@pytest.mark.parametrize("weather", [
    pytest.param({"outdoor_temperature": 22, "humidity": 90}, id="wetter-outside"),
    pytest.param({"outdoor_temperature": 8, "humidity": 85}, id="colder-outside"),
    pytest.param({"air_quality_index": "very_poor"}, id="polluted-outside"),
])
async def test_weather_changes_after_stalled_session_keep_closing_green(lifetime, weather):
    s = lifetime
    await s.at(1, rh=70)
    await s.at(2, window="on")
    await s.at(18)
    assert s.coordinator._humidity_session.exhausted
    record = await s.at(20, **weather)
    assert record["status"] == "green"
    assert record["action"] in {"can_close", "better_close", "close_now"}
    await s.at(21, window="off")
    record = await s.at(40)
    assert record["action"] == "room_watch"


async def test_wetter_outside_interrupts_an_active_airing(lifetime):
    s = lifetime
    await s.at(1, rh=70)
    await s.at(2, window="on")
    record = await s.at(6, outdoor_temperature=22, humidity=80)
    assert record["status"] == "green"
    assert record["action"] == "better_close"
    assert record["reason"] == "humidity_wait"
    await s.at(7, window="off")
    record = await s.at(25)
    assert record["action"] == "room_watch"


@pytest.mark.parametrize("danger", ["nina", "weather"])
async def test_hard_danger_interrupts_a_running_humidity_session(lifetime, danger):
    s = lifetime
    await s.at(1, rh=70)
    await s.at(2, window="on")
    if danger == "nina":
        record = await s.at(6, warning={"nina_status": "danger", "nina_reason_key": "air_smoke_danger"})
    else:
        record = await s.at(6, weather_danger=True, weather_hard_lock=True)
    assert record["status"] == "locked"
    assert record["action"] == "close_now"
    assert not record["humidity_active"]
    record = await s.at(7, window="off")
    assert record["status"] == "locked"
    assert record["action"] == "keep_closed"


@pytest.mark.parametrize("lifetime", [50], indirect=True)
async def test_two_minute_airing_after_peak_is_unconfirmed_and_need_persists(lifetime):
    s = lifetime
    await s.at(2, rh=56)
    await s.at(5, rh=63)
    await s.at(8, rh=68)
    await s.at(9, window="on")
    early = await s.at(11, window="off")
    assert s.tracker.last_confirmed_airing is None
    record = await s.at(65)
    # Two open minutes with unchanged high humidity are not a completed airing.
    # A renewed request here is not evidence of a defect in the colour fix.
    assert early["action"] == "room_need"
    assert record["action"] == "room_need"
    assert s.tracker.last_confirmed_airing is None


async def test_two_minute_airing_without_peak_is_not_confirmed(lifetime):
    s = lifetime
    await s.at(16, rh=70)
    await s.at(17, window="on")
    await s.at(19, window="off")
    assert s.tracker.last_confirmed_airing is None
    await s.at(80)
    assert s.tracker.last_confirmed_airing is None


@pytest.mark.parametrize("duration", [2, 4, 5, 6])
async def test_confirmed_airing_starts_at_five_minutes(lifetime, duration):
    s = lifetime
    await s.at(1, window="on")
    await s.at(1 + duration)
    assert s.tracker.current_airing_qualified is (duration >= 5)
    await s.at(1 + duration, window="off")
    assert (s.tracker.last_confirmed_airing is not None) is (duration >= 5)


async def test_sustained_new_humidity_rise_rearms_after_rest(lifetime):
    s = lifetime
    await s.at(1, rh=68)
    await s.at(2, window="on")
    await s.at(18)
    await s.at(19, window="off")
    await s.at(79, rh=71.2)
    record = await s.at(93)
    assert record["humidity_disarmed"]
    record = await s.at(95)
    assert not record["humidity_disarmed"]
    assert record["action"] in {"room_need", "room_urgent"}


async def test_sensor_outage_and_recovery_during_humidity_airing(lifetime):
    s = lifetime
    await s.at(1, rh=70)
    await s.at(2, window="on")
    record = await s.at(5, rh="unavailable")
    assert record["humidity"] is None
    assert s.result is None
    record = await s.at(8, rh=68)
    assert s.result is not None
    assert record["humidity_active"]
    await s.at(12, rh=65)
    await s.at(20, rh=56)
    assert s.result.room_status_color == "green"


async def test_contact_outage_does_not_invent_a_confirmed_close(lifetime):
    s = lifetime
    await s.at(1, rh=70)
    await s.at(2, window="on")
    record = await s.at(8, window="unavailable")
    # The short contact grace preserves an already open session; a sustained
    # outage must subsequently become unknown without inventing a close.
    assert record["window_open"] is True
    assert s.tracker.last_confirmed_airing is None
    record = await s.at(14)
    assert record["action"] == "window_state_unknown"
    assert s.tracker.last_confirmed_airing is None
    record = await s.at(15, window="on")
    assert record["window_open"] is True
    assert s.tracker.last_confirmed_airing is None
    await s.at(20, rh=56)
    await s.at(21, window="off")
    assert s.tracker.last_confirmed_airing is not None


async def test_finished_humidity_does_not_hide_still_required_co2_airing(lifetime):
    s = lifetime
    await s.at(1, rh=70, co2=1800)
    await s.at(2, window="on")
    record = await s.at(18, co2=1700)
    assert record["humidity_exhausted"]
    assert record["co2_active"]
    assert record["action"] in {"keep_open", "room_keep_brief"}
    for minute, ppm in [(22, 1500), (26, 1100), (30, 800), (33, 600), (36, 590)]:
        record = await s.at(minute, co2=ppm)
    assert record["action"] in {"can_close", "better_close"}
    assert record["status"] == "green"


@pytest.mark.parametrize("lifetime", [50], indirect=True)
async def test_opening_without_need_does_not_create_a_humidity_session(lifetime):
    s = lifetime
    record = await s.at(1, window="on")
    assert record["status"] == "green"
    assert not record["humidity_active"]
    await s.at(5, rh=55)
    await s.at(10, rh=60)
    record = await s.at(15, rh=70)
    assert record["humidity_active"]
    assert record["action"] in {"keep_open", "room_keep_brief"}
