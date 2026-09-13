"""Regression tests for VOC/NO2 auto-detection of raw values vs vendor indices."""

from custom_components.lueftungsberater.air_sensors import (
    classify_absolute,
    pollutant_reading,
)


class FakeState:
    def __init__(self, state, attributes=None):
        self.state = state
        self.attributes = attributes or {}


class FakeStates:
    def __init__(self, values):
        self._values = values

    def get(self, entity_id):
        return self._values.get(entity_id)


class FakeHass:
    def __init__(self, values):
        self.states = FakeStates(values)


def _read(state, pollutant):
    hass = FakeHass({"sensor.air": state})
    return pollutant_reading(hass, "sensor.air", pollutant=pollutant)


def test_unitless_voc_is_vendor_index():
    reading = _read(FakeState("6.2"), "voc")
    assert reading.value == 6.2
    assert reading.pollutant_key == "voc_index"
    assert reading.measurement_type == "index"
    assert reading.unit is None


def test_voc_mass_raw_value_is_normalized_to_ugm3():
    reading = _read(
        FakeState(
            "0.95",
            {
                "unit_of_measurement": "mg/m³",
                "device_class": "volatile_organic_compounds",
            },
        ),
        "voc",
    )
    assert reading.value == 950.0
    assert reading.pollutant_key == "voc"
    assert reading.measurement_type == "mass"
    assert reading.unit == "µg/m³"
    assert classify_absolute("voc", reading.value) == "good"


def test_voc_parts_raw_value_is_kept_separate_from_mass_and_index():
    reading = _read(
        FakeState(
            "0.25",
            {
                "unit_of_measurement": "ppm",
                "device_class": "volatile_organic_compounds_parts",
            },
        ),
        "voc",
    )
    assert reading.value == 250.0
    assert reading.pollutant_key == "voc_parts"
    assert reading.measurement_type == "parts"
    assert reading.unit == "ppb"


def test_no2_mass_raw_value_uses_absolute_path():
    reading = _read(
        FakeState(
            "42",
            {"unit_of_measurement": "µg/m³", "device_class": "nitrogen_dioxide"},
        ),
        "no2",
    )
    assert reading.value == 42.0
    assert reading.pollutant_key == "no2"
    assert reading.measurement_type == "mass"
    assert classify_absolute("no2", reading.value) == "moderate"


def test_no2_ppm_is_normalized_to_ppb_without_mass_conversion():
    reading = _read(
        FakeState(
            "0.04",
            {"unit_of_measurement": "ppm", "device_class": "nitrogen_dioxide"},
        ),
        "no2",
    )
    assert reading.value == 40.0
    assert reading.pollutant_key == "no2_parts"
    assert reading.measurement_type == "parts"
    assert reading.unit == "ppb"
    assert classify_absolute("no2_parts", reading.value) == "poor"


def test_physical_device_class_without_unit_is_rejected_not_guessed_as_index():
    reading = _read(
        FakeState("42", {"device_class": "nitrogen_dioxide"}),
        "no2",
    )
    assert reading.value is None
    assert reading.pollutant_key is None


def test_unknown_foreign_unit_is_rejected_not_guessed_as_index():
    reading = _read(FakeState("55", {"unit_of_measurement": "%"}), "voc")
    assert reading.value is None
    assert reading.pollutant_key is None


def test_o3_ppm_is_normalized_to_ppb_and_classified_without_mass_guess():
    reading = _read(
        FakeState(
            "0.10",
            {"unit_of_measurement": "ppm", "device_class": "ozone"},
        ),
        "o3",
    )
    assert reading.value == 100.0
    assert reading.pollutant_key == "o3_parts"
    assert reading.measurement_type == "parts"
    assert reading.unit == "ppb"
    assert classify_absolute("o3_parts", reading.value) == "poor"


def test_unitless_o3_is_rejected_not_guessed_as_vendor_index():
    reading = _read(FakeState("100", {"device_class": "ozone"}), "o3")
    assert reading.value is None
    assert reading.pollutant_key is None
