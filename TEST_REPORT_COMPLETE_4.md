# Testbericht – v0.11.1 TEST COMPLETE(4)

Prüfdatum: 05.10.2026. Integrationsversion: 0.11.1. Bestehende Config-Entry-Migration bleibt Minor-Version 14.

## Gegenstand

Dieser Stand behebt ausschließlich den GitHub-Actions-Fehler im Lifecycle-Hardening-Test von TEST COMPLETE(3). Die Integrations-/Entscheidungslogik bleibt unverändert.

## Ursache und Korrektur

- `LueftungsberaterRoomCoordinator.__init__()` legt `_effectiveness_session_unsub` regulär immer an.
- `test_room_coordinator_shutdown_drains_notification_tasks_before_clearing_state` umgeht den Konstruktor absichtlich mit `object.__new__()` und initialisierte bislang nur die älteren Unsubscribe-Felder.
- Nach Einführung der gemeinsamen Temperatur-/Partikel-Wirksamkeits-Subscription fehlte daher ausschließlich im künstlichen Testobjekt `_effectiveness_session_unsub`.
- Der Test setzt dieses Feld nun wie die übrigen Unsubscribe-Felder auf `None`.
- `async_shutdown()` selbst wurde bewusst nicht mit `getattr()` aufgeweicht, weil das Feld bei real erzeugten Coordinator-Instanzen Bestandteil der regulären Initialisierung ist.
- Der gemeldete „lingering task“-Teardown-Fehler ist eine Folge des vorherigen `AttributeError`: Der Shutdown erreichte `_drain_notification_tasks()` nicht. Mit vollständiger Test-Fixture läuft der getestete Pfad wieder bis zur Task-Bereinigung.

## Vorliegender CI-Nachweis für COMPLETE(3)

Der bereitgestellte GitHub-Actions-Lauf erreichte 739 bestandene Tests und genau einen fehlgeschlagenen Test plus einen daraus resultierenden Teardown-Fehler. Beide Meldungen stammen aus demselben unvollständigen Testaufbau (`_effectiveness_session_unsub` fehlt). Es gab keinen zweiten unabhängigen Funktionsfehler.

## In dieser Arbeitsumgebung tatsächlich ausgeführt

- `python -m compileall -q custom_components tests`: erfolgreich.
- JSON-Parsing aller Integrations-JSON-Dateien: erfolgreich.
- `node tests/frontend_cache_test.mjs`: erfolgreich.
- Paketvergleich gegen COMPLETE(3): Produktionscode unverändert; geändert wurden nur `tests/test_lifecycle_hardening.py`, `CHANGELOG.md` und dieser Testbericht.

## Einschränkung

Die vollständige Home-Assistant-Pytest-Suite kann in dieser Laufzeit weiterhin nicht selbst ausgeführt werden, weil das Python-Paket `homeassistant` hier nicht installiert ist. COMPLETE(4) enthält deshalb keine Behauptung eines hier lokal vollständig bestandenen HA-Testlaufs.
