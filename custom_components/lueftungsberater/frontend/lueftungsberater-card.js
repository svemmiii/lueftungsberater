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
    const de = {
      open_now: "Jetzt lüften",
      keep_open: "Weiter lüften",
      can_close: "Lüften kann beendet werden",
      short_observation: "Nur kurz unter Beobachtung",
      better_close: "Besser schließen",
      caution_keep_closed: "Vorsicht – lieber geschlossen lassen",
      keep_closed: "Geschlossen lassen",
      close_now: "Jetzt schließen",
      wait: "Noch nicht nötig / besser warten",
    };
    const en = {
      open_now: "Ventilate now",
      keep_open: "Keep ventilating",
      can_close: "Ventilation can be stopped",
      short_observation: "Briefly, under observation",
      better_close: "Better close",
      caution_keep_closed: "Caution – better keep closed",
      keep_closed: "Keep closed",
      close_now: "Close now",
      wait: "Not needed yet / better wait",
    };
    const lang = (this._hass?.language || "de").toLowerCase();
    return (lang.startsWith("de") ? de : en)[state] || state;
  }

  _co2Label(status) {
    const de = {
      very_good: "sehr gut",
      good: "gut",
      elevated: "erhöht",
      high: "hoch",
      critical: "kritisch",
      unknown: "unbekannt",
    };
    const en = {
      very_good: "very good",
      good: "good",
      elevated: "elevated",
      high: "high",
      critical: "critical",
      unknown: "unknown",
    };
    const lang = (this._hass?.language || "de").toLowerCase();
    return (lang.startsWith("de") ? de : en)[status] || status;
  }

  _durationText(duration) {
    if (!duration) return null;

    if (
      duration ===
      "15–30 Minuten bzw. solange draußen günstiger bleibt"
    ) {
      return (
        "15–30 Minuten. Länger lüften, solange die Außenluft " +
        "weiterhin zum Abkühlen geeignet ist."
      );
    }

    return duration;
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
      ? n.toFixed(digits).replace(".", ",")
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
    const lang = (this._hass?.language || "de").toLowerCase();
    return lang.startsWith("de") ? " · Wetterdienst" : " · weather service";
  }

  _entityExists(entityId) {
    return Boolean(entityId && this._hass?.states?.[entityId]);
  }

  _metric(text, entityId, title = "Verlauf öffnen") {
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
            <strong>Raum auswählen</strong>
            <span>Wähle im visuellen Editor einen Lüftungsberater-Raum aus.</span>
          </div>
        </ha-card>`;
      return;
    }

    const st = this._hass.states[this._config.entity];
    if (!st) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="error">
            Entity ${this._escape(this._config.entity)} nicht gefunden.
          </div>
        </ha-card>`;
      return;
    }

    const a = st.attributes || {};
    const status = a.status || "yellow";
    const meta = this._statusMeta(status);
    const recommendation =
      a.recommendation || this._localizeState(st.state);
    const reason = a.reason || "";
    const duration = a.duration;
    const durationText = this._durationText(duration);
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
            ? `Fenster / Tür gerade offen · seit ${openMinutes} Min.`
            : "Fenster / Tür gerade offen";
        rows.push({
          icon: "mdi:window-open-variant",
          cls: "window-open",
          html: this._metric(label, airingSource, "Lüftung öffnen"),
        });
      } else if (hours !== null) {
        rows.push({
          icon: "mdi:history",
          html: this._metric(
            `Letzte bestätigte Lüftung: vor ${hours} h`,
            a.source_last_airing || airingSource,
            "Lüftungsverlauf öffnen"
          ),
        });
      } else {
        rows.push({
          icon: "mdi:history",
          html: this._metric(
            "Noch keine bestätigte Lüftung erfasst",
            airingSource,
            "Lüftung öffnen"
          ),
        });
      }
    }

    if (ti !== null && ta !== null) {
      const parts = [
        this._metric(
          `${ti} ${tempUnit} innen`,
          a.source_temperature_inside,
          "Innentemperatur öffnen"
        ),
        this._metric(
          `${ta} ${tempUnit} außen${this._fallbackSuffix(a.outdoor_temperature_source)}`,
          a.source_temperature_outside,
          "Außentemperatur öffnen"
        ),
      ];

      if (target !== null) {
        parts.push(
          this._metric(
            `${target} ${tempUnit} Soll`,
            a.source_target_temperature,
            "Thermostat öffnen"
          )
        );
      }

      rows.push({
        icon: "mdi:thermometer",
        html: `Temperatur: ${parts.join(" · ")}`,
      });
    }

    if (hi !== null && ho !== null) {
      const rh = [
        this._metric(
          `${hi} % innen`,
          a.source_humidity_inside,
          "Innenfeuchte öffnen"
        ),
        this._metric(
          `${ho} % außen${this._fallbackSuffix(a.outdoor_humidity_source)}`,
          a.source_humidity_outside,
          "Außenfeuchte öffnen"
        ),
      ];

      let html = `Luftfeuchte: ${rh.join(" · ")}`;

      if (ahi !== null && aho !== null) {
        html += ` · ${this._metric(
          `${ahi} g/m³ innen`,
          a.source_absolute_humidity_inside,
          "Absolute Innenfeuchte öffnen"
        )} · ${aho} g/m³ außen`;
      }

      if (diff !== null) {
        html += ` · Δ ${diff} g/m³`;
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
          `${co2ppm} ppm`,
          a.source_co2,
          "CO₂-Verlauf öffnen"
        )} · ${this._escape(this._co2Label(a.co2_status))}`;

        if (co2DataStatus === "grace") {
          co2Text +=
            " · Sensor kurz nicht verfügbar, letzter gültiger Wert";
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
            "CO₂-Sensor nicht verfügbar · Bewertung vorübergehend ohne CO₂",
            a.source_co2,
            "CO₂-Sensor öffnen"
          ),
        });
      }
    }

    const showDuration =
      durationText &&
      durationText !== "Jetzt nicht nötig" &&
      durationText !== "Not needed now";

    const reasonHtml = reason
      ? this._metric(
          reason,
          this._reasonSource(a),
          "Warn-/Quelldaten öffnen"
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
                <div class="why">Warum diese Empfehlung?</div>
                <div class="reason">${reasonHtml}</div>
              `
              : ""
          }

          ${
            showDuration
              ? `
                <div class="duration">
                  <span class="duration-label">⏱️ Empfohlene Lüftungsdauer:</span>
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
            Messwerte antippen für Verlauf · Karte antippen für Details
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
    name: "Lüftungsberater – Raum",
    description:
      "Detaillierte Lüftungsempfehlung für einen einzelnen Raum.",
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
      throw new Error("entities muss eine Liste von Entity-IDs sein.");
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
    if (fallback) return fallback;

    const de = {
      open_now: "Jetzt lüften",
      keep_open: "Weiter lüften",
      can_close: "Lüften kann beendet werden",
      short_observation: "Nur kurz unter Beobachtung",
      better_close: "Besser schließen",
      caution_keep_closed: "Vorsicht – lieber geschlossen lassen",
      keep_closed: "Geschlossen lassen",
      close_now: "Jetzt schließen",
      wait: "Noch nicht nötig / besser warten",
    };

    const en = {
      open_now: "Ventilate now",
      keep_open: "Keep ventilating",
      can_close: "Ventilation can be stopped",
      short_observation: "Briefly, under observation",
      better_close: "Better close",
      caution_keep_closed: "Caution – better keep closed",
      keep_closed: "Keep closed",
      close_now: "Close now",
      wait: "Not needed yet / better wait",
    };

    const lang = (this._hass?.language || "de").toLowerCase();
    return (lang.startsWith("de") ? de : en)[state] || state;
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
          recommendation: this._localizeRecommendation(
            stateObj.state,
            a.recommendation
          ),
          reason: a.reason || "",
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
    if (!rooms.length) return "Keine Räume";

    const red = rooms.filter((room) => room.status === "red").length;
    const yellow = rooms.filter((room) => room.status === "yellow").length;
    const green = rooms.filter((room) => room.status === "green").length;

    const parts = [`${rooms.length} ${rooms.length === 1 ? "Raum" : "Räume"}`];

    if (red) parts.push(`${red} kritisch`);
    if (yellow) parts.push(`${yellow} beachten`);
    if (green && !red && !yellow) parts.push("alles im grünen Bereich");

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
              : "Keine Begründung verfügbar";

            const windowBadge = room.windowOpen
              ? `
                <span class="badge">
                  <ha-icon icon="mdi:window-open-variant"></ha-icon>
                  offen
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
            <strong>Keine Lüftungsberater-Räume gefunden.</strong>
            <span>
              Räume werden automatisch erkannt oder können per
              <code>entities:</code> angegeben werden.
            </span>
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
    name: "Lüftungsberater – Übersicht",
    description:
      "Kompakte Übersicht über alle oder ausgewählte Lüftungsberater-Räume.",
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
          Raum
          <select id="entity">
            <option value="">Raum auswählen …</option>
            ${entities.map((stateObj) => `
              <option
                value="${this._escape(stateObj.entity_id)}"
                ${stateObj.entity_id === current ? "selected" : ""}
              >${this._escape(this._name(stateObj))}</option>
            `).join("")}
          </select>
        </label>

        <label>
          Kartenname (optional)
          <input
            id="name"
            type="text"
            value="${this._escape(this._config.name || "")}"
            placeholder="z. B. Wohnzimmer"
          />
        </label>

        <div class="hint">
          Empfehlung, Farbe, Begründung und Messwerte werden automatisch übernommen.
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
          Titel
          <input
            id="title"
            type="text"
            value="${this._escape(this._config.title || "Lüftungsberater")}"
          />
        </label>

        <div>
          <strong>Räume</strong>
          <div class="hint">Sind alle angehakt, werden automatisch auch neue Räume aufgenommen.</div>
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

