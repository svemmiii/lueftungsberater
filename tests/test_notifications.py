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
    _assistant_warning_fingerprint,
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


def test_assistant_warning_fingerprint_is_room_independent():
    from types import SimpleNamespace

    warnings = SimpleNamespace(
        provider_domain="nina",
        nina_status="danger",
        nina_reason_key="official_close_instruction",
        nina_original_reason="Fenster und Türen schließen",
        weather_reason_key=None,
        weather_original_reason=None,
        official_close_instruction=True,
        warning_ids={"warning-123"},
    )
    weather = SimpleNamespace(
        air_quality_index="unknown",
        air_quality_pollutant=None,
        air_quality_value=None,
    )
    room_a = SimpleNamespace(
        warnings=warnings,
        weather=weather,
        result=SimpleNamespace(mode="nina_aussenluftgefahr", reason_key="room_a_reason"),
    )
    room_b = SimpleNamespace(
        warnings=warnings,
        weather=weather,
        result=SimpleNamespace(mode="nina_aussenluftgefahr", reason_key="room_b_reason"),
    )

    assert _assistant_warning_fingerprint(room_a, NOTIFY_TRIGGER_AIR_DANGER) == (
        _assistant_warning_fingerprint(room_b, NOTIFY_TRIGGER_AIR_DANGER)
    )


def test_warning_fingerprint_ignores_mutable_text_and_raw_air_value():
    from types import SimpleNamespace

    def snapshot(text: str, value: float):
        return SimpleNamespace(
            warnings=SimpleNamespace(
                provider_domain="nina",
                warning_ids={"warning-123"},
                nina_status="danger",
                nina_reason_key="official_close_instruction",
                nina_original_reason=text,
                weather_reason_key=None,
                weather_original_reason=None,
                official_close_instruction=True,
            ),
            weather=SimpleNamespace(
                air_quality_index="very_poor",
                air_quality_pollutant="pm25",
                air_quality_value=value,
            ),
            result=SimpleNamespace(mode="nina_aussenluftgefahr"),
        )

    assert _assistant_warning_fingerprint(
        snapshot("Fenster schließen", 160.0), NOTIFY_TRIGGER_AIR_DANGER
    ) == _assistant_warning_fingerprint(
        snapshot("Fenster und Türen geschlossen halten", 161.0),
        NOTIFY_TRIGGER_AIR_DANGER,
    )


def test_warning_fingerprint_changes_for_new_warning_id():
    from types import SimpleNamespace

    def snapshot(warning_id: str):
        return SimpleNamespace(
            warnings=SimpleNamespace(
                provider_domain="nina",
                warning_ids={warning_id},
                nina_status="danger",
                nina_reason_key="official_close_instruction",
                nina_original_reason="same text",
                weather_reason_key=None,
                weather_original_reason=None,
                official_close_instruction=True,
            ),
            weather=SimpleNamespace(
                air_quality_index="unknown",
                air_quality_pollutant=None,
                air_quality_value=None,
            ),
            result=SimpleNamespace(mode="nina_aussenluftgefahr"),
        )

    assert _assistant_warning_fingerprint(
        snapshot("warning-1"), NOTIFY_TRIGGER_AIR_DANGER
    ) != _assistant_warning_fingerprint(
        snapshot("warning-2"), NOTIFY_TRIGGER_AIR_DANGER
    )


def test_nina_fingerprint_ignores_unrelated_air_quality_class_changes():
    from types import SimpleNamespace

    def snapshot(aq_index: str, pollutant: str | None):
        return SimpleNamespace(
            warnings=SimpleNamespace(
                provider_domain="nina",
                warning_ids={"warning-123"},
                nina_status="danger",
                nina_reason_key="official_close_instruction",
                weather_reason_key=None,
                official_close_instruction=True,
            ),
            weather=SimpleNamespace(
                air_quality_index=aq_index,
                air_quality_pollutant=pollutant,
            ),
            result=SimpleNamespace(mode="nina_aussenluftgefahr"),
        )

    assert _assistant_warning_fingerprint(
        snapshot("good", "pm25"), NOTIFY_TRIGGER_AIR_DANGER
    ) == _assistant_warning_fingerprint(
        snapshot("moderate", "ozone"), NOTIFY_TRIGGER_AIR_DANGER
    )


def test_air_quality_fingerprint_ignores_unrelated_nina_changes():
    from types import SimpleNamespace

    def snapshot(warning_id: str, nina_status: str):
        return SimpleNamespace(
            warnings=SimpleNamespace(
                provider_domain="nina",
                warning_ids={warning_id},
                nina_status=nina_status,
                nina_reason_key="official_close_instruction",
                weather_reason_key=None,
                official_close_instruction=True,
            ),
            weather=SimpleNamespace(
                air_quality_index="very_poor",
                air_quality_pollutant="pm25",
            ),
            result=SimpleNamespace(mode="luftqualitaet_sehr_schlecht"),
        )

    assert _assistant_warning_fingerprint(
        snapshot("warning-1", "danger"), NOTIFY_TRIGGER_AIR_DANGER
    ) == _assistant_warning_fingerprint(
        snapshot("warning-2", "none"), NOTIFY_TRIGGER_AIR_DANGER
    )


def test_air_quality_fingerprint_changes_when_semantic_air_class_changes():
    from types import SimpleNamespace

    def snapshot(index: str, pollutant: str):
        return SimpleNamespace(
            warnings=SimpleNamespace(
                provider_domain=None,
                warning_ids=set(),
                nina_status="none",
                nina_reason_key=None,
                weather_reason_key=None,
                official_close_instruction=False,
            ),
            weather=SimpleNamespace(
                air_quality_index=index,
                air_quality_pollutant=pollutant,
            ),
            result=SimpleNamespace(mode="luftqualitaet_sehr_schlecht"),
        )

    assert _assistant_warning_fingerprint(
        snapshot("very_poor", "pm25"), NOTIFY_TRIGGER_AIR_DANGER
    ) != _assistant_warning_fingerprint(
        snapshot("poor", "pm25"), NOTIFY_TRIGGER_AIR_DANGER
    )


def test_weather_fingerprint_ignores_air_quality_and_nina_fields():
    from types import SimpleNamespace

    def snapshot(aq_index: str, nina_status: str):
        return SimpleNamespace(
            warnings=SimpleNamespace(
                provider_domain="dwd_weather_warnings",
                warning_ids={"dwd-123"},
                nina_status=nina_status,
                nina_reason_key="unrelated",
                weather_reason_key="weather_wind_danger",
                official_close_instruction=False,
            ),
            weather=SimpleNamespace(
                air_quality_index=aq_index,
                air_quality_pollutant="pm25",
            ),
            result=SimpleNamespace(mode="wettergefahr"),
        )

    assert _assistant_warning_fingerprint(
        snapshot("good", "none"), NOTIFY_TRIGGER_WEATHER_DANGER
    ) == _assistant_warning_fingerprint(
        snapshot("very_poor", "danger"), NOTIFY_TRIGGER_WEATHER_DANGER
    )
