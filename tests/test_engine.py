from custom_components.lueftungsberater.engine import absolute_humidity, evaluate_room
from custom_components.lueftungsberater.models import RoomInput

def base(**kw):
    data = dict(indoor_temp=23, indoor_humidity=50, outdoor_temp=15, outdoor_humidity=70, target_temp=22)
    data.update(kw)
    return RoomInput(**data)

def test_absolute_humidity_cold_humid_air_can_be_drier():
    assert absolute_humidity(15, 90) < absolute_humidity(23, 60)

def test_high_co2_good_conditions_is_green():
    r = evaluate_room(base(co2=1500))
    assert r.color == "green" and r.mode == "co2_lueften"

def test_nina_danger_wins():
    r = evaluate_room(base(co2=1800, nina_status="danger", nina_reason="Brandrauch"))
    assert r.color == "red" and r.mode == "nina_aussenluftgefahr"

def test_nina_caution_is_yellow():
    r = evaluate_room(base(co2=900, nina_status="caution"))
    assert r.color == "yellow" and r.mode == "nina_vorsicht"

def test_weather_danger_wins_and_keeps_specific_reason():
    r = evaluate_room(base(co2=1500, weather_danger=True, weather_reason="DWD warnt vor Starkregen"))
    assert r.color == "red" and "Starkregen" in r.reason

def test_window_open_keeps_airing_for_co2():
    r = evaluate_room(base(co2=1200, window_open=True))
    assert r.mode == "weiter_lueften"

def test_window_open_finished_when_goals_are_done():
    r = evaluate_room(base(indoor_temp=22, indoor_humidity=50, outdoor_temp=21.5, outdoor_humidity=55, co2=850, window_open=True))
    assert r.mode == "lueftung_fertig"

def test_co2_optional():
    r = evaluate_room(base(co2=None, indoor_humidity=65, outdoor_humidity=50))
    assert r.mode == "feuchte_lueften"
