from homeassistant.const import UnitOfTemperature

from custom_components.lueftungsberater.runtime import _to_celsius


def test_fahrenheit_is_normalized_to_celsius():
    assert round(_to_celsius(77, UnitOfTemperature.FAHRENHEIT), 2) == 25.0


def test_celsius_stays_celsius():
    assert _to_celsius(23.5, UnitOfTemperature.CELSIUS) == 23.5


def test_warning_source_none_is_not_configured():
    from types import SimpleNamespace
    from custom_components.lueftungsberater.runtime import warning_source_configured

    assert warning_source_configured(SimpleNamespace(data={"warning_source": "none"})) is False
    assert warning_source_configured(SimpleNamespace(data={"warning_source": "abc123"})) is True
