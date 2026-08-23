from custom_components.lueftungsberater.const import (
    NOTIFY_TRIGGER_AIR_CAUTION,
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_WEATHER_CAUTION,
    NOTIFY_TRIGGER_WEATHER_DANGER,
)
from custom_components.lueftungsberater.notifications import _message, _trigger_for_mode


def test_notification_modes_are_explicit_not_generic_red_states():
    assert _trigger_for_mode("nina_aussenluftgefahr") == NOTIFY_TRIGGER_AIR_DANGER
    assert _trigger_for_mode("nina_vorsicht") == NOTIFY_TRIGGER_AIR_CAUTION
    assert _trigger_for_mode("wettergefahr") == NOTIFY_TRIGGER_WEATHER_DANGER
    assert _trigger_for_mode("wetter_vorsicht") == NOTIFY_TRIGGER_WEATHER_CAUTION
    # Red recommendations caused by temperature are deliberately not hazards.
    assert _trigger_for_mode("aussen_zu_warm") is None
    assert _trigger_for_mode("aussen_zu_kalt") is None


def test_notification_text_is_natural_in_supported_languages():
    de_title, de_message = _message("de", "Küche", NOTIFY_TRIGGER_AIR_DANGER)
    en_title, en_message = _message("en", "Kitchen", NOTIFY_TRIGGER_AIR_DANGER)
    tr_title, tr_message = _message("tr", "Mutfak", NOTIFY_TRIGGER_AIR_DANGER)

    assert "Küche" in de_title and "Bitte schließe" in de_message
    assert "Kitchen" in en_title and "Please close" in en_message
    assert "Mutfak" in tr_title and "Lütfen kapat" in tr_message
