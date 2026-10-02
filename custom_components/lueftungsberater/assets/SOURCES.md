# Herkunft der geographischen Datendateien

`meteoalarm_regions.json.gz`: EUMETNET / MeteoAlarm EMMA-Regionsgeometrien. Öffentliche Kopie des ursprünglichen MeteoAlarm-Geocodes-Datensatzes: https://saratoga-weather.org/meteoalarm-map/geocodes.json (Stand 2025-10-06). Die Originalkoordinaten wurden unverändert übernommen. EUMETNET / MeteoAlarm nennt CC BY 4.0 für seine offenen Daten; Herkunft und Datumsstand bleiben im JSON enthalten. Die Kopie ist keine aktuelle amtliche API und kann hinter Gebietsänderungen zurückliegen.

758 Datenzuordnungen für Geocode-Aliase aus https://github.com/ktrue/Meteoalarm-warning/blob/master/meteoalarm-geocode-aliases.php (Stand 2023-10-19). Nur die Zuordnungsdaten wurden übernommen, kein PHP-Code. Ursprüngliche Quelle: EUMETNET / MeteoAlarm.

`countries.json.gz`: Natural Earth 1:10m Admin 0 Countries, aus https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_10m_admin_0_countries.geojson, abgerufen 2026-10-02. Public Domain: https://www.naturalearthdata.com/about/terms-of-use/. Geometrien unverändert; reduzierte Eigenschaften für ISO-Code und Bounding Box. Diese Karte dient der Länderwahl, nicht der amtlichen Grenzbestimmung.
