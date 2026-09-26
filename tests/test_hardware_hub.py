from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from custom_components.lueftungsberater.const import DATA_HARDWARE_HUBS, DOMAIN
from custom_components.lueftungsberater.hardware_hub import (
    StationRuntime,
    expire_stale_stations,
    station_is_fresh,
)

UTC = timezone.utc


def test_station_freshness_expires_after_three_missed_minutes():
    now = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
    state = StationRuntime(
        hardware_id="AA:BB",
        master_id="master",
        online=True,
        last_seen=now - timedelta(seconds=179),
    )
    assert station_is_fresh(state, now=now) is True

    state.last_seen = now - timedelta(seconds=181)
    assert station_is_fresh(state, now=now) is False


def test_expire_stale_station_marks_it_offline_and_notifies(monkeypatch):
    now = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
    state = StationRuntime(
        hardware_id="AA:BB",
        master_id="master",
        online=True,
        last_seen=now - timedelta(minutes=4),
    )
    hass = SimpleNamespace(
        data={
            DOMAIN: {
                DATA_HARDWARE_HUBS: {
                    "entry": {"states": {"station": state}}
                }
            }
        }
    )
    entry = SimpleNamespace(entry_id="entry")
    sent = []

    monkeypatch.setattr(
        "custom_components.lueftungsberater.hardware_hub.async_dispatcher_send",
        lambda *args: sent.append(args),
    )

    expired = expire_stale_stations(hass, entry, now=now)

    assert expired == ("station",)
    assert state.online is False
    assert sent


def test_legacy_station_defaults_to_master_connection():
    from custom_components.lueftungsberater.hardware_hub import station_connection_type
    from custom_components.lueftungsberater.const import HARDWARE_CONNECTION_MASTER

    station = SimpleNamespace(data={})
    assert station_connection_type(station) == HARDWARE_CONNECTION_MASTER


def test_direct_station_reads_cached_ha_entities_without_master_runtime():
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_CONNECTION_TYPE,
        CONF_HARDWARE_DIRECT_CO2,
        CONF_HARDWARE_DIRECT_HUMIDITY,
        CONF_HARDWARE_DIRECT_TEMP,
        HARDWARE_CONNECTION_DIRECT,
    )
    from custom_components.lueftungsberater.hardware_hub import direct_station_value

    class States:
        values = {
            "sensor.direct_co2": SimpleNamespace(state="1234"),
            "sensor.direct_temp": SimpleNamespace(state="22.5"),
            "sensor.direct_humidity": SimpleNamespace(state="54.2"),
        }

        def get(self, entity_id):
            return self.values.get(entity_id)

    hass = SimpleNamespace(states=States())
    station = SimpleNamespace(
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_DIRECT_CO2: "sensor.direct_co2",
            CONF_HARDWARE_DIRECT_TEMP: "sensor.direct_temp",
            CONF_HARDWARE_DIRECT_HUMIDITY: "sensor.direct_humidity",
        }
    )

    assert direct_station_value(hass, station, "co2") == 1234.0
    assert direct_station_value(hass, station, "temperature") == 22.5
    assert direct_station_value(hass, station, "humidity") == 54.2


def test_direct_station_rejects_unavailable_cached_value():
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_CONNECTION_TYPE,
        CONF_HARDWARE_DIRECT_CO2,
        CONF_HARDWARE_DIRECT_HUMIDITY,
        CONF_HARDWARE_DIRECT_TEMP,
        HARDWARE_CONNECTION_DIRECT,
    )
    from custom_components.lueftungsberater.hardware_hub import direct_station_value

    class States:
        def get(self, entity_id):
            return SimpleNamespace(state="unavailable")

    hass = SimpleNamespace(states=States())
    station = SimpleNamespace(
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_DIRECT_CO2: "sensor.direct_co2",
            CONF_HARDWARE_DIRECT_TEMP: "sensor.direct_temp",
            CONF_HARDWARE_DIRECT_HUMIDITY: "sensor.direct_humidity",
        }
    )
    assert direct_station_value(hass, station, "co2") is None


def test_direct_station_rejects_stale_numeric_state():
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_CONNECTION_TYPE,
        CONF_HARDWARE_DIRECT_CO2,
        CONF_HARDWARE_DIRECT_HUMIDITY,
        CONF_HARDWARE_DIRECT_TEMP,
        HARDWARE_CONNECTION_DIRECT,
    )
    from custom_components.lueftungsberater.hardware_hub import direct_station_value

    stale = datetime.now(UTC) - timedelta(minutes=4)

    class States:
        def get(self, entity_id):
            return SimpleNamespace(state="1234", last_reported=stale)

    hass = SimpleNamespace(states=States())
    station = SimpleNamespace(
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_DIRECT_CO2: "sensor.direct_co2",
            CONF_HARDWARE_DIRECT_TEMP: "sensor.direct_temp",
            CONF_HARDWARE_DIRECT_HUMIDITY: "sensor.direct_humidity",
        }
    )
    assert direct_station_value(hass, station, "co2") is None


def test_master_report_rejects_implausible_sensor_values(monkeypatch):
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_ID,
        CONF_HARDWARE_MASTER_ID,
    )
    from custom_components.lueftungsberater.hardware_hub import report_station

    monkeypatch.setattr(
        "custom_components.lueftungsberater.hardware_hub.async_dispatcher_send",
        lambda *_args: None,
    )
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry")
    station = SimpleNamespace(
        subentry_id="station",
        data={CONF_HARDWARE_ID: "AA:BB", CONF_HARDWARE_MASTER_ID: "master"},
    )

    state = report_station(
        hass,
        entry,
        station,
        {"co2": -1, "temperature": 999, "humidity": 140},
    )

    assert state.co2 is None
    assert state.temperature is None
    assert state.humidity is None
