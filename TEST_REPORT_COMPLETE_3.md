# Testbericht – v0.11.1 TEST COMPLETE(3)

Prüfdatum: 05.10.2026. Integrationsversion: 0.11.1. Bestehende Config-Entry-Migration bleibt Minor-Version 14.

## Gegenstand

Dieser Stand behebt ausschließlich die in TEST COMPLETE(2) verbliebene Querwirkung der PM-Wirksamkeitsruhe auf andere Innenluft-Schadstoffe. Wetter-/Providerlogik, Zonen-Unterstützung, Temperatur-Wirksamkeit sowie PM-Timer und PM-Reaktivierung aus COMPLETE(2) bleiben unverändert.

## Korrektur

- `particulate_session_exhausted` unterdrückt `moderate`/`poor` nur noch, wenn `indoor_air_quality_pollutant` aktuell `pm2_5` oder `pm10` ist.
- Wechselt der aktuell schlechteste Innenluft-Schadstoff während einer PM-Ruhephase zu `voc`, `no2`, `no2_parts` oder `formaldehyde`, bleibt der entsprechende Innenluftgrund sofort aktiv.
- `very_poor` bleibt unabhängig von der PM-Ruhephase weiterhin dringend.
- Regressionstest erweitert: PM2.5 und PM10 bleiben bei `moderate`/`poor` korrekt unterdrückbar; VOC, NO₂, NO₂-parts und Formaldehyd werden bei `moderate` und `poor` trotz gesetztem PM-Exhaustion-Flag nicht unterdrückt.

## In dieser Arbeitsumgebung tatsächlich ausgeführt

- `python -m compileall -q custom_components tests`: erfolgreich.
- JSON-Parsing aller Integrations-JSON-Dateien: erfolgreich.
- `node tests/frontend_cache_test.mjs`: erfolgreich.
- Isolierter Engine-Regressionstest ohne Import des Home-Assistant-Pakets: PM2.5/PM10 werden bei laufender PM-Ruhephase für `moderate`/`poor` unterdrückt; `very_poor` bleibt aktiv: erfolgreich.
- Isolierter Engine-Regressionstest: VOC, NO₂, NO₂-parts und Formaldehyd bleiben jeweils bei `moderate` und `poor` trotz `particulate_session_exhausted=True` aktiv: erfolgreich.
- Zusätzlicher Grenzfall ohne Pollutant-Key: ein veraltetes PM-Exhaustion-Flag unterdrückt keinen allgemeinen `poor`-Innenluftgrund: erfolgreich.

## Einschränkung

Die vollständige Pytest-Suite wurde in dieser Laufzeit nicht ausgeführt, weil das Python-Paket `homeassistant` hier nicht installiert ist. Ein normaler Pytest-Import der Integration bricht deshalb bereits bei der Test-Sammlung in `custom_components/lueftungsberater/__init__.py` ab. Dieser Bericht behauptet daher ausdrücklich **nicht**, dass die komplette HA-Testmatrix bestanden wurde. Die betroffene HA-unabhängige Engine-Logik wurde stattdessen direkt mit den oben genannten Regressionen ausgeführt.
