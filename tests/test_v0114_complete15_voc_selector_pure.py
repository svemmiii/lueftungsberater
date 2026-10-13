"""Do not offer calibration/reference channels as VOC and NO2 measurements."""
from types import SimpleNamespace as NS
from test_v0114_complete2_pure import _extract

def test_picker_rejects_calibration_channels_but_keeps_real_indices():
    def state(name,unit='',klass=None):
        return NS(entity_id='sensor.'+name,attributes={
            'friendly_name':name.replace('_',' '),
            'unit_of_measurement':unit,'device_class':klass},state='98')
    readings=[state('VOC_Index'),state('VOC_Index_Calibration'),state('VOC_baseline','index'),
              state('NO2_Index'),state('NO2_Index_reference'),state('NO2_calibration','ppb'),
              state('NO2_Air','ppb')]
    classes=NS(PM25='pm25',PM10='pm10',VOLATILE_ORGANIC_COMPOUNDS='voc',
               VOLATILE_ORGANIC_COMPOUNDS_PARTS='voc_parts',NITROGEN_DIOXIDE='no2',OZONE='o3')
    scope=_extract('config_flow.py',{'_air_sensor_selector','_is_numeric_sensor_state'},
        {'re':__import__('re'),'math':__import__('math'),'HomeAssistant':object,
         'SensorDeviceClass':classes,'EntitySelector':lambda config:config,
         'EntitySelectorConfig':lambda **kwargs:kwargs})
    hass=NS(states=NS(async_all=lambda d:readings))
    voc=scope['_air_sensor_selector']('voc',hass)['include_entities']
    no2=scope['_air_sensor_selector']('no2',hass)['include_entities']
    assert voc==['sensor.VOC_Index']
    assert no2==['sensor.NO2_Index','sensor.NO2_Air']
