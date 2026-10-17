"""Use real HA entities to check the card and history receive one decision."""

import logging

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lueftungsberater.const import CONF_NIGHT_END_TIME, DOMAIN
from custom_components.lueftungsberater.engine import evaluate_room
from custom_components.lueftungsberater.providers import WeatherAssessment, WarningAssessment
from custom_components.lueftungsberater.runtime import RoomSnapshot
from custom_components.lueftungsberater.sensor import HistoryRoomSensor, RoomAdvisorSensor
from test_room_air_closing_colors import reported_room


@pytest.mark.parametrize("display", ["room_air", "ventilation"])
@pytest.mark.parametrize("changes,room_color,room_action", [
    ({}, "green", "better_close"),
    ({"window_open": False}, "yellow", "room_watch"),
    ({"humidity_disarmed": False}, "yellow", "room_keep_brief"),
    ({"air_quality": "very_poor"}, "green", "close_now"),
    ({"nina_status": "danger", "nina_reason_key": "air_smoke_danger"}, "locked", "close_now"),
    ({"weather_danger": True, "weather_hard_lock": True}, "locked", "close_now"),
])
async def test_room_card_and_history_receive_final_colour_and_action(
    hass, enable_custom_integrations, display, changes, room_color, room_action,
):
    data = reported_room(**changes)
    result = evaluate_room(data)
    entry = MockConfigEntry(
        domain=DOMAIN, title="Meine Wohnung", data={"display_mode": display},
        subentries_data=[{
            "subentry_type": "room", "title": "Wohnung", "unique_id": None,
            "data": {CONF_NIGHT_END_TIME: "06:30:00"},
        }],
    )
    entry.add_to_hass(hass)
    room = next(iter(entry.subentries.values()))
    coordinator = DataUpdateCoordinator(
        hass, logging.getLogger(__name__), name="closing-transport", config_entry=entry,
    )
    coordinator.async_set_updated_data(RoomSnapshot(
        result=result, weather=WeatherAssessment(), warnings=WarningAssessment(),
        values={
            "last_confirmed_airing": None, "co2_ppm": data.co2,
            "temperature_inside": data.indoor_temp, "temperature_outside": data.outdoor_temp,
            "target_temperature": data.target_temp, "humidity_inside": data.indoor_humidity,
            "humidity_outside": data.outdoor_humidity, "has_co2": True,
            "has_window_contacts": True, "window_open": data.window_open,
            "open_minutes": data.open_minutes, "hours_since_last_airing": data.hours_since_airing,
        },
    ))
    advisor = RoomAdvisorSensor(entry, room, coordinator)
    advisor.hass = hass
    history = HistoryRoomSensor(entry, room, coordinator, "decision")
    attrs = advisor.extra_state_attributes

    expected_action = room_action if display == "room_air" else result.recommendation_key
    expected_status = (
        "locked" if result.safety_lock
        else room_color if display == "room_air" else result.color
    )
    assert attrs["status"] == expected_status
    assert attrs["recommendation_key"] == expected_action
    assert history.native_value == expected_action
    assert history.extra_state_attributes["room_status"] == attrs["room_status"]
    assert history.extra_state_attributes["ventilation_status"] == attrs["ventilation_status"]
    assert history.extra_state_attributes["safety_lock"] == attrs["safety_lock"]
    # Automations keep the original native action regardless of the card view.
    assert advisor.native_value == result.recommendation_key
    assert attrs["temperature_inside"] == data.indoor_temp
    assert attrs["humidity_inside"] == data.indoor_humidity
    assert attrs["night_ventilation_args"]["requested_night_end"] == "06:30:00"
    if display == "room_air":
        if room_action == "room_keep_brief":
            assert attrs["duration_key"] != "not_needed"
        else:
            assert attrs["duration_key"] == "not_needed"
