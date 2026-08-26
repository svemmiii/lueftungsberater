from custom_components.lueftungsberater.const import (
    NOTIFY_TRIGGER_AIR_CAUTION,
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_AIRING_FINISHED,
    NOTIFY_TRIGGER_AIRING_RECOMMENDED,
    NOTIFY_TRIGGER_WEATHER_CAUTION,
    NOTIFY_TRIGGER_WEATHER_DANGER,
    NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED,
    NOTIFY_TRIGGER_ALL_CLEAR,
)
from custom_components.lueftungsberater.notifications import (
    _message,
    _transition_trigger,
    _trigger_for_mode,
)


def test_notification_modes_are_explicit_not_generic_red_states():
    assert _trigger_for_mode("nina_aussenluftgefahr") == NOTIFY_TRIGGER_AIR_DANGER
    assert _trigger_for_mode("nina_vorsicht") == NOTIFY_TRIGGER_AIR_CAUTION
    assert _trigger_for_mode("luftqualitaet_schlecht") == NOTIFY_TRIGGER_AIR_CAUTION
    assert _trigger_for_mode("luftqualitaet_sehr_schlecht") == NOTIFY_TRIGGER_AIR_DANGER
    assert _trigger_for_mode("luftqualitaet_maessig") == NOTIFY_TRIGGER_AIR_CAUTION
    assert _trigger_for_mode("wettergefahr") == NOTIFY_TRIGGER_WEATHER_DANGER
    assert _trigger_for_mode("wetter_vorsicht") == NOTIFY_TRIGGER_WEATHER_CAUTION
    # Red recommendations caused only by comfort/efficiency are deliberately
    # not treated as warning notifications.
    assert _trigger_for_mode("aussen_zu_warm") is None
    assert _trigger_for_mode("aussen_zu_kalt") is None
    assert _trigger_for_mode("aussen_deutlich_feuchter") is None


def test_status_notifications_are_edge_triggered():
    assert (
        _transition_trigger("normal", "optional", "co2_lueften", "open_now")
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


def test_optional_closed_warning_text_explicitly_says_windows_are_closed():
    title, message = _message("de", "Wohnung", NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED)
    assert "Lüftungsassistent" in title
    assert "aktuell geschlossen" in message


def test_all_clear_notification_text_is_available():
    title, message = _message("en", "Office", NOTIFY_TRIGGER_ALL_CLEAR)
    assert "Fresh Air Assistant" in title
    assert "all-clear" in message.lower() or "all clear" in message.lower()
