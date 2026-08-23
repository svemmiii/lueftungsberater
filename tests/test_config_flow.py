from custom_components.lueftungsberater.config_flow import _remote_summary


def test_remote_summary_counts_instances_and_rooms() -> None:
    payload = {
        "instances": [
            {"rooms": [{"id": "1"}, {"id": "2"}]},
            {"rooms": [{"id": "3"}]},
        ]
    }

    assert _remote_summary(payload) == {"instances": "2", "rooms": "3"}


def test_remote_summary_handles_missing_payload() -> None:
    assert _remote_summary(None) == {"instances": "0", "rooms": "0"}
