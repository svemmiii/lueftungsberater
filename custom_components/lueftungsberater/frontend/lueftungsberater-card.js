const LB_NNBSP = "\u202F";

const LB_I18N = {
  de: {
    "recommendation.open_now": "Jetzt lüften",
    "recommendation.keep_open": "Weiter lüften",
    "recommendation.can_close": "Lüften kann beendet werden",
    "recommendation.short_observation": "Nur kurz lüften und im Blick behalten",
    "recommendation.better_close": "Besser schließen",
    "recommendation.caution_keep_closed": "Vorsicht – lieber geschlossen lassen",
    "recommendation.keep_closed": "Geschlossen lassen",
    "recommendation.close_now": "Jetzt schließen",
    "recommendation.wait": "Besser noch etwas warten",
    "co2.very_good": "sehr gut",
    "co2.good": "gut",
    "co2.elevated": "erhöht",
    "co2.high": "hoch",
    "co2.critical": "kritisch",
    "co2.unknown": "unbekannt",
    "weather_service": "Wetterdienst",
    "history_open": "Verlauf öffnen",
    "setup.title": "Raum auswählen",
    "setup.description": "Wähle im visuellen Editor einen Lüftungsberater-Raum aus.",
    "entity_missing": "Entity {entity} nicht gefunden.",
    "window.open_since": "Fenster / Tür gerade offen · seit {minutes} Min.",
    "window.open": "Fenster / Tür gerade offen",
    "airing.open": "Lüftung öffnen",
    "airing.last": "Letzte bestätigte Lüftung: vor {hours} h",
    "airing.history": "Lüftungsverlauf öffnen",
    "airing.none": "Noch keine bestätigte Lüftung erfasst",
    "metric.inside": "{value} innen",
    "metric.outside": "{value} außen",
    "metric.target": "{value} Soll",
    "metric.temperature": "Temperatur",
    "metric.humidity": "Luftfeuchte",
    "metric.indoor_temperature_open": "Innentemperatur öffnen",
    "metric.outdoor_temperature_open": "Außentemperatur öffnen",
    "metric.thermostat_open": "Thermostat öffnen",
    "metric.indoor_humidity_open": "Innenfeuchte öffnen",
    "metric.outdoor_humidity_open": "Außenfeuchte öffnen",
    "metric.absolute_humidity_open": "Absolute Innenfeuchte öffnen",
    "co2.history": "CO₂-Verlauf öffnen",
    "co2.grace": "Sensor kurz nicht verfügbar, letzter gültiger Wert",
    "co2.unavailable": "CO₂-Sensor nicht verfügbar · Bewertung vorübergehend ohne CO₂",
    "co2.open": "CO₂-Sensor öffnen",
    "warning.open": "Warn-/Quelldaten öffnen",
    "why": "Warum diese Empfehlung?",
    "duration": "⏱️ Empfohlene Lüftungsdauer:",
    "hint": "Messwerte antippen für Verlauf · Karte antippen für Details",
    "picker.room.name": "Lüftungsberater – Raum",
    "picker.room.description": "Detaillierte Lüftungsempfehlung für einen einzelnen Raum.",
    "overview.invalid_entities": "entities muss eine Liste von Entity-IDs sein.",
    "overview.no_rooms": "Keine Räume",
    "overview.room": "Raum",
    "overview.rooms": "Räume",
    "overview.critical": "kritisch",
    "overview.attention": "beachten",
    "overview.all_good": "alles im grünen Bereich",
    "overview.open": "offen",
    "overview.no_reason": "Keine Begründung verfügbar",
    "overview.empty_title": "Keine Lüftungsberater-Räume gefunden.",
    "overview.empty_description": "Räume werden automatisch erkannt oder können per entities: angegeben werden.",
    "picker.overview.name": "Lüftungsberater – Übersicht",
    "picker.overview.description": "Kompakte Übersicht über alle oder ausgewählte Lüftungsberater-Räume.",
    "editor.room": "Raum",
    "editor.select_room": "Raum auswählen …",
    "editor.card_name": "Kartenname (optional)",
    "editor.card_name_placeholder": "z. B. Wohnzimmer",
    "editor.room_hint": "Empfehlung, Farbe, Begründung und Messwerte werden automatisch übernommen.",
    "editor.title": "Titel",
    "editor.rooms": "Räume",
    "editor.rooms_hint": "Sind alle angehakt, werden automatisch auch neue Räume aufgenommen."
  },
  en: {
    "recommendation.open_now": "Ventilate now",
    "recommendation.keep_open": "Keep ventilating",
    "recommendation.can_close": "You can stop ventilating now",
    "recommendation.short_observation": "Ventilate briefly and keep an eye on it",
    "recommendation.better_close": "Better close the windows",
    "recommendation.caution_keep_closed": "Better keep the windows closed for now",
    "recommendation.keep_closed": "Keep the windows closed",
    "recommendation.close_now": "Close the windows now",
    "recommendation.wait": "Better wait a little longer",
    "co2.very_good": "very good",
    "co2.good": "good",
    "co2.elevated": "elevated",
    "co2.high": "high",
    "co2.critical": "critical",
    "co2.unknown": "unknown",
    "weather_service": "weather service",
    "history_open": "Open history",
    "setup.title": "Select a room",
    "setup.description": "Choose a Ventilation Advisor room in the visual editor.",
    "entity_missing": "Entity {entity} was not found.",
    "window.open_since": "Window / door is open · for {minutes} min",
    "window.open": "Window / door is open",
    "airing.open": "Open ventilation details",
    "airing.last": "Last confirmed ventilation: {hours} h ago",
    "airing.history": "Open ventilation history",
    "airing.none": "No confirmed ventilation has been recorded yet",
    "metric.inside": "{value} indoors",
    "metric.outside": "{value} outside",
    "metric.target": "{value} target",
    "metric.temperature": "Temperature",
    "metric.humidity": "Humidity",
    "metric.indoor_temperature_open": "Open indoor temperature",
    "metric.outdoor_temperature_open": "Open outdoor temperature",
    "metric.thermostat_open": "Open thermostat",
    "metric.indoor_humidity_open": "Open indoor humidity",
    "metric.outdoor_humidity_open": "Open outdoor humidity",
    "metric.absolute_humidity_open": "Open indoor absolute humidity",
    "co2.history": "Open CO₂ history",
    "co2.grace": "Sensor briefly unavailable, using the last valid value",
    "co2.unavailable": "CO₂ sensor unavailable · assessment temporarily continues without CO₂",
    "co2.open": "Open CO₂ sensor",
    "warning.open": "Open warning / source data",
    "why": "Why this recommendation?",
    "duration": "⏱️ Recommended ventilation time:",
    "hint": "Tap a value for its history · tap the card for details",
    "picker.room.name": "Ventilation Advisor – Room",
    "picker.room.description": "Detailed ventilation recommendation for a single room.",
    "overview.invalid_entities": "entities must be a list of entity IDs.",
    "overview.no_rooms": "No rooms",
    "overview.room": "room",
    "overview.rooms": "rooms",
    "overview.critical": "critical",
    "overview.attention": "need attention",
    "overview.all_good": "all looking good",
    "overview.open": "open",
    "overview.no_reason": "No explanation available",
    "overview.empty_title": "No Ventilation Advisor rooms found.",
    "overview.empty_description": "Rooms are discovered automatically or can be specified with entities:.",
    "picker.overview.name": "Ventilation Advisor – Overview",
    "picker.overview.description": "Compact overview of all or selected Ventilation Advisor rooms.",
    "editor.room": "Room",
    "editor.select_room": "Select a room …",
    "editor.card_name": "Card name (optional)",
    "editor.card_name_placeholder": "e.g. Living room",
    "editor.room_hint": "Recommendation, color, explanation, and measurements are filled in automatically.",
    "editor.title": "Title",
    "editor.rooms": "Rooms",
    "editor.rooms_hint": "When all are selected, newly added rooms are included automatically as well."
  }
};

function lbLanguage(hass) {
  const raw = (
    hass?.language ||
    document.documentElement?.lang ||
    navigator.language ||
    "en"
  ).toLowerCase();
  return raw.startsWith("de") ? "de" : "en";
}

function lbLocale(hass) {
  return lbLanguage(hass) === "de" ? "de-DE" : "en-US";
}

function lbT(hass, key, values = {}) {
  const lang = lbLanguage(hass);
  let text = LB_I18N[lang]?.[key] ?? LB_I18N.en[key] ?? key;
  for (const [name, value] of Object.entries(values)) {
    text = text.replaceAll(`{${name}}`, String(value));
  }
  return text;
}

function lbLocalizedEntityText(hass, attributes, field, fallback = "") {
  const lang = lbLanguage(hass);
  return attributes?.localized_texts?.[lang]?.[field] || fallback;
}

class LueftungsberaterCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    this._config = {
      tap_action: { action: "more-info" },
      ...config,
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement("lueftungsberater-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  _localizeState(state) {
    return lbT(this._hass, `recommendation.${state}`);
  }

  _co2Label(status) {
    return lbT(this._hass, `co2.${status}`);
  }

  _durationText(duration) {
    return duration || null;
  }

  _statusMeta(status) {
    if (status === "green") {
      return { cls: "green", icon: "mdi:window-open-variant" };
    }
    if (status === "red") {
      return { cls: "red", icon: "mdi:window-closed-variant" };
    }
    return { cls: "yellow", icon: "mdi:window-open" };
  }

  _fmt(value, digits = 1) {
    if (value === null || value === undefined || value === "") {
      return null;
    }
    const n = Number(value);
    return Number.isFinite(n)
      ? new Intl.NumberFormat(lbLocale(this._hass), {
          minimumFractionDigits: digits,
          maximumFractionDigits: digits,
        }).format(n)
      : null;
  }

  _temperatureUnit() {
    return this._hass?.config?.unit_system?.temperature || "°C";
  }

  _displayTemperature(value, unit = this._temperatureUnit()) {
    if (value === null || value === undefined || value === "") return null;
    const n = Number(value);
    if (!Number.isFinite(n)) return null;
    return unit === "°F" ? (n * 9) / 5 + 32 : n;
  }

  _fallbackSuffix(sourceKind) {
    if (sourceKind !== "weather_fallback") return "";
    return ` · ${lbT(this._hass, "weather_service")}`;
  }

  _entityExists(entityId) {
    return Boolean(entityId && this._hass?.states?.[entityId]);
  }

  _valueUnit(value, unit) {
    return `${value}${LB_NNBSP}${unit}`;
  }

  _metric(text, entityId, title = null) {
    title = title || lbT(this._hass, "history_open");
    const escaped = this._escape(text);
    if (!this._entityExists(entityId)) {
      return `<span>${escaped}</span>`;
    }
    return `
      <button
        type="button"
        class="metric-link"
        data-entity="${this._escape(entityId)}"
        title="${this._escape(title)}"
      >${escaped}</button>`;
  }

  _dispatchMoreInfo(entityId) {
    if (!this._entityExists(entityId)) return;

    const event = new Event("hass-action", {
      bubbles: true,
      composed: true,
    });
    event.detail = {
      config: {
        entity: entityId,
        tap_action: { action: "more-info" },
      },
      action: "tap",
    };
    this.dispatchEvent(event);
  }

  _handleMainTap() {
    const event = new Event("hass-action", {
      bubbles: true,
      composed: true,
    });
    event.detail = {
      config: {
        entity: this._config.entity,
        tap_action: this._config.tap_action || { action: "more-info" },
      },
      action: "tap",
    };
    this.dispatchEvent(event);
  }

  _reasonSource(a) {
    if (String(a.mode || "").startsWith("nina")) {
      return a.source_nina_status || null;
    }
    return (
      a.source_weather_reason ||
      a.source_weather_danger ||
      a.source_nina_status ||
      null
    );
  }

  _render() {
    if (!this.shadowRoot) return;

    if (!this._hass || !this._config) {
      this.shadowRoot.innerHTML = "";
      return;
    }

    if (!this._config.entity) {
      this.shadowRoot.innerHTML = `
        <style>
          ha-card { padding: 18px; }
          .setup { display: grid; gap: 6px; }
          .setup strong { font-size: 16px; }
          .setup span {
            color: var(--secondary-text-color);
            line-height: 1.4;
          }
        </style>
        <ha-card>
          <div class="setup">
            <strong>${lbT(this._hass, "setup.title")}</strong>
            <span>${lbT(this._hass, "setup.description")}</span>
          </div>
        </ha-card>`;
      return;
    }

    const st = this._hass.states[this._config.entity];
    if (!st) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="error">
            ${this._escape(lbT(this._hass, "entity_missing", { entity: this._config.entity }))}
          </div>
        </ha-card>`;
      return;
    }

    const a = st.attributes || {};
    const status = a.status || "yellow";
    const meta = this._statusMeta(status);
    const recommendation = lbLocalizedEntityText(
      this._hass, a, "recommendation", a.recommendation || this._localizeState(st.state)
    );
    const reason = lbLocalizedEntityText(this._hass, a, "reason", a.reason || "");
    const durationText = lbLocalizedEntityText(
      this._hass, a, "duration", a.duration || ""
    );
    const title =
      this._config.name ||
      st.attributes.friendly_name ||
      "Lüftungsberater";

    const tempUnit = a.temperature_display_unit || this._temperatureUnit();
    const ti = this._fmt(this._displayTemperature(a.temperature_inside, tempUnit));
    const ta = this._fmt(this._displayTemperature(a.temperature_outside, tempUnit));
    const target = this._fmt(this._displayTemperature(a.target_temperature, tempUnit));
    const hi = this._fmt(a.humidity_inside);
    const ho = this._fmt(a.humidity_outside);
    const ahi = this._fmt(a.absolute_humidity_inside);
    const aho = this._fmt(a.absolute_humidity_outside);
    const diff = this._fmt(a.absolute_humidity_difference);
    const co2ppm = this._fmt(a.co2_ppm, 0);
    const hours = this._fmt(a.hours_since_last_airing);
    const openMinutes = this._fmt(a.open_minutes, 0);

    const hasWindows = a.has_window_contacts === true;
    const windowOpen = a.window_open === true;
    const hasCo2 = a.has_co2 === true && co2ppm !== null;

    const windowSources = Array.isArray(a.source_window_entities)
      ? a.source_window_entities
      : [];
    const airingSource =
      a.source_airing ||
      a.source_last_airing ||
      windowSources.find((entityId) => this._entityExists(entityId)) ||
      null;

    const rows = [];

    if (hasWindows) {
      if (windowOpen) {
        const label =
          openMinutes !== null
            ? lbT(this._hass, "window.open_since", { minutes: openMinutes })
            : lbT(this._hass, "window.open");
        rows.push({
          icon: "mdi:window-open-variant",
          cls: "window-open",
          html: this._metric(label, airingSource, lbT(this._hass, "airing.open")),
        });
      } else if (hours !== null) {
        rows.push({
          icon: "mdi:history",
          html: this._metric(
            lbT(this._hass, "airing.last", { hours }),
            a.source_last_airing || airingSource,
            lbT(this._hass, "airing.history")
          ),
        });
      } else {
        rows.push({
          icon: "mdi:history",
          html: this._metric(
            lbT(this._hass, "airing.none"),
            airingSource,
            lbT(this._hass, "airing.open")
          ),
        });
      }
    }

    if (ti !== null && ta !== null) {
      const parts = [
        this._metric(
          lbT(this._hass, "metric.inside", { value: this._valueUnit(ti, tempUnit) }),
          a.source_temperature_inside,
          lbT(this._hass, "metric.indoor_temperature_open")
        ),
        this._metric(
          `${lbT(this._hass, "metric.outside", { value: this._valueUnit(ta, tempUnit) })}${this._fallbackSuffix(a.outdoor_temperature_source)}`,
          a.source_temperature_outside,
          lbT(this._hass, "metric.outdoor_temperature_open")
        ),
      ];

      if (target !== null) {
        parts.push(
          this._metric(
            lbT(this._hass, "metric.target", { value: this._valueUnit(target, tempUnit) }),
            a.source_target_temperature,
            lbT(this._hass, "metric.thermostat_open")
          )
        );
      }

      rows.push({
        icon: "mdi:thermometer",
        html: `${lbT(this._hass, "metric.temperature")}: ${parts.join(" · ")}`,
      });
    }

    if (hi !== null && ho !== null) {
      const rh = [
        this._metric(
          lbT(this._hass, "metric.inside", { value: this._valueUnit(hi, "%") }),
          a.source_humidity_inside,
          lbT(this._hass, "metric.indoor_humidity_open")
        ),
        this._metric(
          `${lbT(this._hass, "metric.outside", { value: this._valueUnit(ho, "%") })}${this._fallbackSuffix(a.outdoor_humidity_source)}`,
          a.source_humidity_outside,
          lbT(this._hass, "metric.outdoor_humidity_open")
        ),
      ];

      let html = `${lbT(this._hass, "metric.humidity")}: ${rh.join(" · ")}`;

      if (ahi !== null && aho !== null) {
        html += ` · ${this._metric(
          lbT(this._hass, "metric.inside", { value: this._valueUnit(ahi, "g/m³") }),
          a.source_absolute_humidity_inside,
          lbT(this._hass, "metric.absolute_humidity_open")
        )} · ${lbT(this._hass, "metric.outside", { value: this._valueUnit(aho, "g/m³") })}`;
      }

      if (diff !== null) {
        html += ` · Δ ${this._valueUnit(diff, "g/m³")}`;
      }

      rows.push({
        icon: "mdi:water-percent",
        html,
      });
    }

    const co2DataStatus = a.co2_data_status || "current";

    if (a.has_co2 === true) {
      if (co2ppm !== null) {
        let co2Text = `CO₂: ${this._metric(
          this._valueUnit(co2ppm, "ppm"),
          a.source_co2,
          lbT(this._hass, "co2.history")
        )} · ${this._escape(this._co2Label(a.co2_status))}`;

        if (co2DataStatus === "grace") {
          co2Text += ` · ${lbT(this._hass, "co2.grace")}`;
        }

        rows.push({
          icon: "mdi:molecule-co2",
          cls: co2DataStatus === "grace" ? "data-warning" : "",
          html: co2Text,
        });
      } else {
        rows.push({
          icon: "mdi:molecule-co2-off",
          cls: "data-warning",
          html: this._metric(
            lbT(this._hass, "co2.unavailable"),
            a.source_co2,
            lbT(this._hass, "co2.open")
          ),
        });
      }
    }

    const showDuration = Boolean(durationText) && a.duration_key !== "not_needed";

    const reasonHtml = reason
      ? this._metric(
          reason,
          this._reasonSource(a),
          lbT(this._hass, "warning.open")
        )
      : "";

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --lb-green: var(--success-color, #43a047);
          --lb-yellow: var(--warning-color, #f9a825);
          --lb-red: var(--error-color, #db4437);
          display: block;
        }

        ha-card {
          overflow: hidden;
          padding: 0;
          cursor: pointer;
          user-select: none;
          -webkit-tap-highlight-color: transparent;
        }

        ha-card:focus-visible {
          outline: 2px solid var(--primary-color);
          outline-offset: 2px;
        }

        .header {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 16px;
          color: var(--primary-text-color);
          border-left: 6px solid var(--lb-accent);
          background:
            color-mix(
              in srgb,
              var(--lb-accent) 14%,
              var(--ha-card-background, var(--card-background-color))
            );
        }

        .header.green { --lb-accent: var(--lb-green); }
        .header.yellow { --lb-accent: var(--lb-yellow); }
        .header.red { --lb-accent: var(--lb-red); }

        .icon-wrap {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          display: grid;
          place-items: center;
          flex: 0 0 auto;
          background: color-mix(in srgb, var(--lb-accent) 20%, transparent);
          color: var(--lb-accent);
        }

        .main-icon {
          --mdc-icon-size: 31px;
          color: var(--lb-accent);
        }

        .head-text {
          min-width: 0;
          flex: 1;
        }

        .title {
          font-size: 14px;
          color: var(--secondary-text-color);
          margin-bottom: 3px;
        }

        .recommendation {
          font-size: 20px;
          font-weight: 600;
          line-height: 1.15;
          overflow-wrap: anywhere;
        }

        .body {
          padding: 14px 16px 16px;
        }

        .why {
          font-size: 15px;
          font-weight: 700;
          color: var(--primary-text-color);
          margin-bottom: 6px;
        }

        .reason {
          line-height: 1.45;
          overflow-wrap: anywhere;
        }

        .duration {
          display: grid;
          gap: 2px;
          margin-top: 12px;
          line-height: 1.4;
        }

        .duration-label {
          font-weight: 700;
        }

        .facts {
          display: grid;
          gap: 8px;
          padding-top: 13px;
          margin-top: 13px;
          border-top: 1px solid var(--divider-color);
          color: var(--secondary-text-color);
          font-size: 12.5px;
        }

        .fact {
          display: grid;
          grid-template-columns: 22px minmax(0, 1fr);
          gap: 7px;
          align-items: start;
          line-height: 1.35;
        }

        .fact ha-icon {
          --mdc-icon-size: 18px;
          color: var(--secondary-text-color);
        }

        .fact.window-open {
          color: var(--primary-text-color);
          font-weight: 600;
        }

        .fact.window-open ha-icon {
          color: var(--primary-color);
        }

        .fact.data-warning {
          color: var(--warning-color);
          font-weight: 600;
        }

        .fact.data-warning ha-icon {
          color: var(--warning-color);
        }

        .metric-link {
          appearance: none;
          background: none;
          border: 0;
          padding: 0;
          margin: 0;
          color: inherit;
          font: inherit;
          line-height: inherit;
          cursor: pointer;
          text-decoration-line: underline;
          text-decoration-style: dotted;
          text-decoration-thickness: 1px;
          text-underline-offset: 2px;
          text-decoration-color: color-mix(
            in srgb,
            currentColor 45%,
            transparent
          );
          text-align: inherit;
        }

        .metric-link:hover,
        .metric-link:focus-visible {
          color: var(--primary-color);
          text-decoration-style: solid;
          outline: none;
        }

        .hint {
          margin-top: 12px;
          color: var(--secondary-text-color);
          font-size: 11px;
          opacity: 0.8;
        }

        .error {
          padding: 16px;
          color: var(--error-color);
        }
      </style>

      <ha-card
        tabindex="0"
        role="button"
        aria-label="${this._escape(title)}"
      >
        <div class="header ${meta.cls}">
          <div class="icon-wrap">
            <ha-icon class="main-icon" icon="${meta.icon}"></ha-icon>
          </div>
          <div class="head-text">
            <div class="title">${this._escape(title)}</div>
            <div class="recommendation">
              ${this._escape(recommendation)}
            </div>
          </div>
        </div>

        <div class="body">
          ${
            reason
              ? `
                <div class="why">${lbT(this._hass, "why")}</div>
                <div class="reason">${reasonHtml}</div>
              `
              : ""
          }

          ${
            showDuration
              ? `
                <div class="duration">
                  <span class="duration-label">${lbT(this._hass, "duration")}</span>
                  <span>${this._escape(durationText)}</span>
                </div>`
              : ""
          }

          ${
            rows.length
              ? `
                <div class="facts">
                  ${rows
                    .map(
                      (row) => `
                        <div class="fact ${row.cls || ""}">
                          <ha-icon icon="${row.icon}"></ha-icon>
                          <span>${row.html}</span>
                        </div>`
                    )
                    .join("")}
                </div>
              `
              : ""
          }

          <div class="hint">
            ${lbT(this._hass, "hint")}
          </div>
        </div>
      </ha-card>`;

    const card = this.shadowRoot.querySelector("ha-card");

    if (card) {
      card.addEventListener("click", () => this._handleMainTap());
      card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          this._handleMainTap();
        }
      });
    }

    this.shadowRoot.querySelectorAll("[data-entity]").forEach((element) => {
      element.addEventListener("click", (event) => {
        event.stopPropagation();
        this._dispatchMoreInfo(element.dataset.entity);
      });
    });
  }

  _escape(value) {
    const div = document.createElement("div");
    div.textContent = String(value ?? "");
    return div.innerHTML;
  }
}

if (!customElements.get("lueftungsberater-card")) {
  customElements.define("lueftungsberater-card", LueftungsberaterCard);
}

window.customCards = window.customCards || [];

if (!window.customCards.some((card) => card.type === "lueftungsberater-card")) {
  window.customCards.push({
    type: "lueftungsberater-card",
    name: lbT(null, "picker.room.name"),
    description: lbT(null, "picker.room.description"),
    preview: false,
    getEntitySuggestion: (hass, entityId) => {
      const stateObj = hass.states[entityId];

      if (
        !stateObj ||
        stateObj.attributes.status === undefined ||
        stateObj.attributes.reason === undefined
      ) {
        return null;
      }

      return {
        config: {
          type: "custom:lueftungsberater-card",
          entity: entityId,
        },
      };
    },
  });
}

class LueftungsberaterOverviewCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    this._config = {
      title: "Lüftungsberater",
      ...config,
    };

    if (
      this._config.entities !== undefined &&
      !Array.isArray(this._config.entities)
    ) {
      throw new Error(lbT(this._hass, "overview.invalid_entities"));
    }

    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return Math.max(2, (this._rooms()?.length || 1) + 1);
  }

  static getConfigElement() {
    return document.createElement("lueftungsberater-overview-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  _escape(value) {
    const div = document.createElement("div");
    div.textContent = String(value ?? "");
    return div.innerHTML;
  }

  _localizeRecommendation(state, fallback) {
    return fallback || lbT(this._hass, `recommendation.${state}`);
  }

  _statusMeta(status) {
    if (status === "red") {
      return {
        rank: 3,
        cls: "red",
        icon: "mdi:window-closed-variant",
      };
    }

    if (status === "yellow") {
      return {
        rank: 2,
        cls: "yellow",
        icon: "mdi:window-open",
      };
    }

    return {
      rank: 1,
      cls: "green",
      icon: "mdi:window-open-variant",
    };
  }

  _isAdvisorEntity(stateObj) {
    if (!stateObj || !stateObj.attributes) return false;

    const a = stateObj.attributes;

    return (
      stateObj.entity_id?.startsWith("sensor.") &&
      typeof a.status === "string" &&
      typeof a.mode === "string" &&
      typeof a.reason === "string" &&
      typeof a.recommendation === "string" &&
      (
        a.room_name !== undefined ||
        a.absolute_humidity_inside !== undefined
      )
    );
  }

  _roomName(stateObj) {
    const explicit = stateObj.attributes.room_name;

    if (explicit) return explicit;

    const friendly = stateObj.attributes.friendly_name || stateObj.entity_id;

    return String(friendly)
      .replace(/^Lüftungsberater\s*/i, "")
      .replace(/\s*Lüftungsberater$/i, "")
      .trim() || friendly;
  }

  _rooms() {
    if (!this._hass) return [];

    let entityIds = [];

    if (Array.isArray(this._config?.entities) && this._config.entities.length) {
      entityIds = this._config.entities;
    } else {
      entityIds = Object.keys(this._hass.states).filter((entityId) =>
        this._isAdvisorEntity(this._hass.states[entityId])
      );
    }

    const rooms = entityIds
      .map((entityId, index) => {
        const stateObj = this._hass.states[entityId];

        if (!this._isAdvisorEntity(stateObj)) return null;

        const a = stateObj.attributes;
        const meta = this._statusMeta(a.status);

        return {
          entityId,
          index,
          name: this._roomName(stateObj),
          recommendation: lbLocalizedEntityText(
            this._hass,
            a,
            "recommendation",
            this._localizeRecommendation(stateObj.state, a.recommendation)
          ),
          reason: lbLocalizedEntityText(this._hass, a, "reason", a.reason || ""),
          status: a.status,
          rank: meta.rank,
          cls: meta.cls,
          icon: meta.icon,
          windowOpen: a.window_open === true,
          co2ppm: a.co2_ppm,
          co2Status: a.co2_status,
        };
      })
      .filter(Boolean);

    // Manuell angegebene Räume behalten exakt ihre Reihenfolge.
    // Autodiscovery sortiert nur alphabetisch für reproduzierbare Darstellung.
    if (!Array.isArray(this._config?.entities) || !this._config.entities.length) {
      rooms.sort((a, b) =>
        a.name.localeCompare(b.name, this._hass.language || "de")
      );
    }

    return rooms;
  }

  _dispatchMoreInfo(entityId) {
    const event = new Event("hass-action", {
      bubbles: true,
      composed: true,
    });

    event.detail = {
      config: {
        entity: entityId,
        tap_action: { action: "more-info" },
      },
      action: "tap",
    };

    this.dispatchEvent(event);
  }

  _summary(rooms) {
    if (!rooms.length) return lbT(this._hass, "overview.no_rooms");

    const red = rooms.filter((room) => room.status === "red").length;
    const yellow = rooms.filter((room) => room.status === "yellow").length;
    const green = rooms.filter((room) => room.status === "green").length;

    const parts = [
      `${rooms.length} ${lbT(this._hass, rooms.length === 1 ? "overview.room" : "overview.rooms")}`
    ];

    if (red) parts.push(`${red} ${lbT(this._hass, "overview.critical")}`);
    if (yellow) parts.push(`${yellow} ${lbT(this._hass, "overview.attention")}`);
    if (green && !red && !yellow) parts.push(lbT(this._hass, "overview.all_good"));

    return parts.join(" · ");
  }

  _overallClass(rooms) {
    if (rooms.some((room) => room.status === "red")) return "red";
    if (rooms.some((room) => room.status === "yellow")) return "yellow";
    return "green";
  }

  _render() {
    if (!this.shadowRoot) return;

    if (!this._hass || !this._config) {
      this.shadowRoot.innerHTML = "";
      return;
    }

    const rooms = this._rooms();
    const overall = this._overallClass(rooms);
    const title = this._config.title || "Lüftungsberater";

    const roomHtml = rooms.length
      ? rooms
          .map((room) => {
            const secondary = room.reason
              ? room.reason
              : lbT(this._hass, "overview.no_reason");

            const windowBadge = room.windowOpen
              ? `
                <span class="badge">
                  <ha-icon icon="mdi:window-open-variant"></ha-icon>
                  ${lbT(this._hass, "overview.open")}
                </span>
              `
              : "";

            return `
              <button
                type="button"
                class="room ${room.cls}"
                data-entity="${this._escape(room.entityId)}"
              >
                <div class="room-icon">
                  <ha-icon icon="${room.icon}"></ha-icon>
                </div>

                <div class="room-copy">
                  <div class="room-topline">
                    <span class="room-name">${this._escape(room.name)}</span>
                    ${windowBadge}
                  </div>

                  <div class="room-recommendation">
                    ${this._escape(room.recommendation)}
                  </div>

                  <div class="room-reason">
                    ${this._escape(secondary)}
                  </div>
                </div>

                <ha-icon
                  class="chevron"
                  icon="mdi:chevron-right"
                ></ha-icon>
              </button>
            `;
          })
          .join("")
      : `
        <div class="empty">
          <ha-icon icon="mdi:home-search-outline"></ha-icon>
          <div>
            <strong>${lbT(this._hass, "overview.empty_title")}</strong>
            <span>${lbT(this._hass, "overview.empty_description")}</span>
          </div>
        </div>
      `;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --lb-green: var(--success-color, #43a047);
          --lb-yellow: var(--warning-color, #f9a825);
          --lb-red: var(--error-color, #db4437);
          display: block;
        }

        ha-card {
          overflow: hidden;
          padding: 0;
        }

        .header {
          --lb-accent: var(--lb-green);
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 15px 16px;
          border-left: 6px solid var(--lb-accent);
          background:
            color-mix(
              in srgb,
              var(--lb-accent) 10%,
              var(--ha-card-background, var(--card-background-color))
            );
        }

        .header.yellow {
          --lb-accent: var(--lb-yellow);
        }

        .header.red {
          --lb-accent: var(--lb-red);
        }

        .header ha-icon {
          --mdc-icon-size: 27px;
          color: var(--lb-accent);
        }

        .header-text {
          min-width: 0;
        }

        .title {
          color: var(--primary-text-color);
          font-size: 18px;
          font-weight: 700;
          line-height: 1.2;
        }

        .summary {
          margin-top: 2px;
          color: var(--secondary-text-color);
          font-size: 12px;
        }

        .rooms {
          display: grid;
        }

        .room {
          --room-accent: var(--lb-green);
          appearance: none;
          display: grid;
          grid-template-columns: 42px minmax(0, 1fr) 24px;
          gap: 11px;
          align-items: center;
          width: 100%;
          min-width: 0;
          padding: 13px 14px 13px 16px;
          border: 0;
          border-top: 1px solid var(--divider-color);
          border-left: 4px solid var(--room-accent);
          background: transparent;
          color: var(--primary-text-color);
          font: inherit;
          text-align: left;
          cursor: pointer;
          -webkit-tap-highlight-color: transparent;
        }

        .room:first-child {
          border-top: 0;
        }

        .room.yellow {
          --room-accent: var(--lb-yellow);
        }

        .room.red {
          --room-accent: var(--lb-red);
        }

        .room:hover,
        .room:focus-visible {
          background:
            color-mix(
              in srgb,
              var(--room-accent) 7%,
              transparent
            );
          outline: none;
        }

        .room-icon {
          width: 38px;
          height: 38px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          background:
            color-mix(
              in srgb,
              var(--room-accent) 15%,
              transparent
            );
          color: var(--room-accent);
        }

        .room-icon ha-icon {
          --mdc-icon-size: 23px;
        }

        .room-copy {
          min-width: 0;
        }

        .room-topline {
          display: flex;
          align-items: center;
          gap: 7px;
          min-width: 0;
        }

        .room-name {
          min-width: 0;
          overflow: hidden;
          color: var(--primary-text-color);
          font-size: 14px;
          font-weight: 700;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .room-recommendation {
          margin-top: 2px;
          color: var(--primary-text-color);
          font-size: 14px;
          font-weight: 600;
          line-height: 1.25;
        }

        .room-reason {
          display: -webkit-box;
          margin-top: 3px;
          overflow: hidden;
          color: var(--secondary-text-color);
          font-size: 11.5px;
          line-height: 1.3;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 2;
        }

        .badge {
          display: inline-flex;
          align-items: center;
          gap: 3px;
          flex: 0 0 auto;
          padding: 2px 6px;
          border-radius: 999px;
          background:
            color-mix(
              in srgb,
              var(--primary-color) 12%,
              transparent
            );
          color: var(--primary-text-color);
          font-size: 10px;
          font-weight: 600;
        }

        .badge ha-icon {
          --mdc-icon-size: 13px;
          color: var(--primary-color);
        }

        .chevron {
          --mdc-icon-size: 22px;
          color: var(--secondary-text-color);
        }

        .empty {
          display: grid;
          grid-template-columns: 32px minmax(0, 1fr);
          gap: 10px;
          align-items: start;
          padding: 18px 16px;
          color: var(--secondary-text-color);
        }

        .empty > ha-icon {
          --mdc-icon-size: 25px;
        }

        .empty strong {
          display: block;
          color: var(--primary-text-color);
          margin-bottom: 4px;
        }

        .empty span {
          display: block;
          line-height: 1.4;
          font-size: 12px;
        }

        code {
          font-family: var(--code-font-family, monospace);
        }
      </style>

      <ha-card>
        <div class="header ${overall}">
          <ha-icon icon="mdi:window-open-variant"></ha-icon>
          <div class="header-text">
            <div class="title">${this._escape(title)}</div>
            <div class="summary">
              ${this._escape(this._summary(rooms))}
            </div>
          </div>
        </div>

        <div class="rooms">
          ${roomHtml}
        </div>
      </ha-card>
    `;

    this.shadowRoot.querySelectorAll("[data-entity]").forEach((element) => {
      element.addEventListener("click", () => {
        this._dispatchMoreInfo(element.dataset.entity);
      });
    });
  }
}

if (!customElements.get("lueftungsberater-overview-card")) {
  customElements.define(
    "lueftungsberater-overview-card",
    LueftungsberaterOverviewCard
  );
}

window.customCards = window.customCards || [];

if (
  !window.customCards.some(
    (card) => card.type === "lueftungsberater-overview-card"
  )
) {
  window.customCards.push({
    type: "lueftungsberater-overview-card",
    name: lbT(null, "picker.overview.name"),
    description: lbT(null, "picker.overview.description"),
    preview: false,
  });
}

class LueftungsberaterCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _advisorEntities() {
    if (!this._hass) return [];
    return Object.values(this._hass.states)
      .filter((stateObj) => {
        const a = stateObj.attributes || {};
        return (
          stateObj.entity_id.startsWith("sensor.") &&
          typeof a.status === "string" &&
          typeof a.mode === "string" &&
          typeof a.recommendation === "string" &&
          typeof a.reason === "string" &&
          (a.room_name !== undefined || a.absolute_humidity_inside !== undefined)
        );
      })
      .sort((a, b) =>
        this._name(a).localeCompare(this._name(b), this._hass.language || "de")
      );
  }

  _name(stateObj) {
    return (
      stateObj.attributes.room_name ||
      stateObj.attributes.friendly_name ||
      stateObj.entity_id
    );
  }

  _escape(value) {
    const div = document.createElement("div");
    div.textContent = String(value ?? "");
    return div.innerHTML;
  }

  _changed(patch) {
    const next = { ...this._config, ...patch };
    for (const key of Object.keys(next)) {
      if (next[key] === undefined || next[key] === "") delete next[key];
    }
    this._config = next;

    const event = new Event("config-changed", {
      bubbles: true,
      composed: true,
    });
    event.detail = { config: next };
    this.dispatchEvent(event);
  }

  _render() {
    if (!this.shadowRoot || !this._config) return;

    const entities = this._advisorEntities();
    const current = this._config.entity || "";

    this.shadowRoot.innerHTML = `
      <style>
        .editor { display: grid; gap: 14px; padding: 8px 0 16px; }
        label {
          display: grid;
          gap: 6px;
          color: var(--primary-text-color);
          font-size: 14px;
          font-weight: 600;
        }
        select, input {
          box-sizing: border-box;
          width: 100%;
          min-height: 44px;
          padding: 8px 10px;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          background: var(--ha-color-form-background, var(--card-background-color));
          color: var(--primary-text-color);
          font: inherit;
        }
        .hint {
          color: var(--secondary-text-color);
          font-size: 12px;
          line-height: 1.4;
        }
      </style>

      <div class="editor">
        <label>
          ${lbT(this._hass, "editor.room")}
          <select id="entity">
            <option value="">${lbT(this._hass, "editor.select_room")}</option>
            ${entities.map((stateObj) => `
              <option
                value="${this._escape(stateObj.entity_id)}"
                ${stateObj.entity_id === current ? "selected" : ""}
              >${this._escape(this._name(stateObj))}</option>
            `).join("")}
          </select>
        </label>

        <label>
          ${lbT(this._hass, "editor.card_name")}
          <input
            id="name"
            type="text"
            value="${this._escape(this._config.name || "")}"
            placeholder="${this._escape(lbT(this._hass, "editor.card_name_placeholder"))}"
          />
        </label>

        <div class="hint">
          ${lbT(this._hass, "editor.room_hint")}
        </div>
      </div>
    `;

    this.shadowRoot.querySelector("#entity")?.addEventListener("change", (event) => {
      this._changed({ entity: event.target.value || undefined });
    });

    this.shadowRoot.querySelector("#name")?.addEventListener("change", (event) => {
      this._changed({ name: event.target.value.trim() || undefined });
    });
  }
}

if (!customElements.get("lueftungsberater-card-editor")) {
  customElements.define("lueftungsberater-card-editor", LueftungsberaterCardEditor);
}


class LueftungsberaterOverviewCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _advisorEntities() {
    if (!this._hass) return [];
    return Object.values(this._hass.states)
      .filter((stateObj) => {
        const a = stateObj.attributes || {};
        return (
          stateObj.entity_id.startsWith("sensor.") &&
          typeof a.status === "string" &&
          typeof a.mode === "string" &&
          typeof a.recommendation === "string" &&
          typeof a.reason === "string" &&
          (a.room_name !== undefined || a.absolute_humidity_inside !== undefined)
        );
      })
      .sort((a, b) => {
        const an = a.attributes.room_name || a.attributes.friendly_name || a.entity_id;
        const bn = b.attributes.room_name || b.attributes.friendly_name || b.entity_id;
        return an.localeCompare(bn, this._hass.language || "de");
      });
  }

  _escape(value) {
    const div = document.createElement("div");
    div.textContent = String(value ?? "");
    return div.innerHTML;
  }

  _emit(next) {
    this._config = next;
    const event = new Event("config-changed", {
      bubbles: true,
      composed: true,
    });
    event.detail = { config: next };
    this.dispatchEvent(event);
  }

  _render() {
    if (!this.shadowRoot || !this._config) return;

    const entities = this._advisorEntities();
    const explicit = Array.isArray(this._config.entities)
      ? this._config.entities
      : null;

    this.shadowRoot.innerHTML = `
      <style>
        .editor { display: grid; gap: 14px; padding: 8px 0 16px; }
        .title {
          display: grid;
          gap: 6px;
          color: var(--primary-text-color);
          font-size: 14px;
          font-weight: 600;
        }
        input[type="text"] {
          box-sizing: border-box;
          width: 100%;
          min-height: 44px;
          padding: 8px 10px;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          background: var(--ha-color-form-background, var(--card-background-color));
          color: var(--primary-text-color);
          font: inherit;
        }
        .rooms { display: grid; gap: 6px; }
        .room {
          display: flex;
          align-items: center;
          gap: 9px;
          min-height: 34px;
          color: var(--primary-text-color);
          font-size: 13px;
        }
        .hint {
          color: var(--secondary-text-color);
          font-size: 12px;
          line-height: 1.4;
        }
      </style>

      <div class="editor">
        <label class="title">
          ${lbT(this._hass, "editor.title")}
          <input
            id="title"
            type="text"
            value="${this._escape(this._config.title || "Lüftungsberater")}"
          />
        </label>

        <div>
          <strong>${lbT(this._hass, "editor.rooms")}</strong>
          <div class="hint">${lbT(this._hass, "editor.rooms_hint")}</div>
        </div>

        <div class="rooms">
          ${entities.map((stateObj) => {
            const checked = explicit === null || explicit.includes(stateObj.entity_id);
            const name =
              stateObj.attributes.room_name ||
              stateObj.attributes.friendly_name ||
              stateObj.entity_id;
            return `
              <label class="room">
                <input
                  type="checkbox"
                  data-entity="${this._escape(stateObj.entity_id)}"
                  ${checked ? "checked" : ""}
                />
                <span>${this._escape(name)}</span>
              </label>
            `;
          }).join("")}
        </div>
      </div>
    `;

    this.shadowRoot.querySelector("#title")?.addEventListener("change", (event) => {
      const next = { ...this._config };
      const value = event.target.value.trim();
      if (value && value !== "Lüftungsberater") next.title = value;
      else delete next.title;
      this._emit(next);
    });

    this.shadowRoot.querySelectorAll("[data-entity]").forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        const selected = Array.from(
          this.shadowRoot.querySelectorAll("[data-entity]:checked")
        ).map((item) => item.dataset.entity);

        const next = { ...this._config };
        if (selected.length === entities.length) delete next.entities;
        else next.entities = selected;
        this._emit(next);
      });
    });
  }
}

if (!customElements.get("lueftungsberater-overview-card-editor")) {
  customElements.define(
    "lueftungsberater-overview-card-editor",
    LueftungsberaterOverviewCardEditor
  );
}

