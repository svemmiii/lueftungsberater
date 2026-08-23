from custom_components.lueftungsberater.const import (
    NOTIFY_TRIGGER_AIR_CAUTION,
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_AIRING_FINISHED,
    NOTIFY_TRIGGER_AIRING_RECOMMENDED,
    NOTIFY_TRIGGER_WEATHER_CAUTION,
    NOTIFY_TRIGGER_WEATHER_DANGER,
    NOTIFY_VIBRATION_OFF,
    NOTIFY_VIBRATION_STRONG,
)
from custom_components.lueftungsberater.notifications import (
    _message,
    _mobile_payload,
    _transition_trigger,
    _trigger_for_mode,
)


def test_notification_modes_are_explicit_not_generic_red_states():
    assert _trigger_for_mode("nina_aussenluftgefahr") == NOTIFY_TRIGGER_AIR_DANGER
    assert _trigger_for_mode("nina_vorsicht") == NOTIFY_TRIGGER_AIR_CAUTION
    assert _trigger_for_mode("wettergefahr") == NOTIFY_TRIGGER_WEATHER_DANGER
    assert _trigger_for_mode("wetter_vorsicht") == NOTIFY_TRIGGER_WEATHER_CAUTION
    # Red recommendations caused by temperature are deliberately not hazards.
    assert _trigger_for_mode("aussen_zu_warm") is None
    assert _trigger_for_mode("aussen_zu_kalt") is None


def test_quiet_status_notifications_are_edge_triggered():
    assert (
        _transition_trigger("normal", "wait", "co2_lueften", "open_now")
        == NOTIFY_TRIGGER_AIRING_RECOMMENDED
    )
    assert _transition_trigger("co2_lueften", "open_now", "kuehlen", "open_now") is None
    assert (
        _transition_trigger(
            "weiter_lueften", "keep_open", "lueftung_fertig", "can_close"
        )
        == NOTIFY_TRIGGER_AIRING_FINISHED
    )
    assert (
        _transition_trigger(
            "lueftung_fertig", "can_close", "lueftung_fertig", "can_close"
        )
        is None
    )


def test_notification_text_is_natural_in_supported_languages():
    de_title, de_message = _message("de", "Küche", NOTIFY_TRIGGER_AIR_DANGER)
    en_title, en_message = _message("en", "Kitchen", NOTIFY_TRIGGER_AIR_DANGER)
    tr_title, tr_message = _message("tr", "Mutfak", NOTIFY_TRIGGER_AIR_DANGER)
    de_info_title, de_info = _message(
        "de", "Küche", NOTIFY_TRIGGER_AIRING_RECOMMENDED
    )

    assert "Küche" in de_title and "Bitte schließe" in de_message
    assert "Kitchen" in en_title and "Please close" in en_message
    assert "Mutfak" in tr_title and "Lütfen kapat" in tr_message
    assert "Küche" in de_info_title and "wieder sinnvoll" in de_info


def test_companion_status_hint_is_silent():
    payload = _mobile_payload(NOTIFY_TRIGGER_AIRING_FINISHED, "kueche")

    assert payload["importance"] == "low"
    assert payload["push"]["interruption-level"] == "passive"
    assert payload["push"]["sound"] == "none"
    assert "vibrationPattern" not in payload


def test_android_vibration_strength_changes_pattern_and_channel():
    quiet = _mobile_payload(
        NOTIFY_TRIGGER_AIR_CAUTION,
        "kueche",
        caution_vibration=NOTIFY_VIBRATION_OFF,
    )
    strong = _mobile_payload(
        NOTIFY_TRIGGER_AIR_DANGER,
        "kueche",
        danger_vibration=NOTIFY_VIBRATION_STRONG,
    )

    assert "vibrationPattern" not in quiet
    assert strong["vibrationPattern"] == "0, 500, 150, 500, 150, 800"
    assert strong["importance"] == "high"
    assert strong["priority"] == "high"
    assert strong["ttl"] == 0
    assert quiet["channel"] != strong["channel"]


def test_critical_bypass_is_opt_in():
    normal = _mobile_payload(
        NOTIFY_TRIGGER_WEATHER_DANGER,
        "wohnzimmer",
        critical_bypass=False,
    )
    critical = _mobile_payload(
        NOTIFY_TRIGGER_WEATHER_DANGER,
        "wohnzimmer",
        critical_bypass=True,
    )

    assert normal["push"]["interruption-level"] == "active"
    assert critical["importance"] == "max"
    assert "Kritisch" in critical["channel"]
    assert critical["push"]["interruption-level"] == "critical"
    assert critical["push"]["sound"]["critical"] == 1
