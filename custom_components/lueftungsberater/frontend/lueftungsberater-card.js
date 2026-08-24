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
    "recommendation.optional": "Lüften ist optional",
    "recommendation.unknown": "Aktuell keine zuverlässige Empfehlung möglich",
    "reason.incomplete_data": "Mindestens ein benötigter Temperatur- oder Feuchtewert ist gerade nicht verfügbar. Sobald die Sensordaten wieder vollständig sind, wird die Empfehlung automatisch aktualisiert.",
    "duration.incomplete_data": "Eine Lüftungsdauer lässt sich mit den aktuellen Sensordaten noch nicht zuverlässig bestimmen.",
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
    "window.open_since": "Fenster / Tür gerade offen · seit {duration}",
    "window.open": "Fenster / Tür gerade offen",
    "window.minute": "Minute",
    "window.minutes": "Minuten",
    "window.hour": "Stunde",
    "window.hours": "Stunden",
    "window.and": "und",
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
    "metric.absolute_humidity_outdoor_open": "Absolute Außenfeuchte öffnen",
    "metric.absolute_humidity_difference_open": "Verlauf der Feuchtedifferenz öffnen",
    "co2.history": "CO₂-Verlauf öffnen",
    "co2.status_history": "Verlauf der CO₂-Bewertung öffnen",
    "co2.grace": "Sensor kurz nicht verfügbar, letzter gültiger Wert",
    "co2.unavailable": "CO₂-Sensor nicht verfügbar · Bewertung vorübergehend ohne CO₂",
    "co2.open": "CO₂-Sensor öffnen",
    "warning.open": "Warn-/Quelldaten öffnen",
    "why": "Warum diese Empfehlung?",
    "duration": "⏱️ Empfohlene Lüftungsdauer:",
    "hint": "Messwerte antippen für Verlauf · farbigen Statusbereich antippen für Details",
    "picker.room.name": "Lüftungsberater – Raum",
    "picker.room.description": "Detaillierte Lüftungsempfehlung für einen einzelnen Raum.",
    "overview.invalid_entities": "entities muss eine Liste von Entity-IDs sein.",
    "overview.open": "offen",
    "overview.not_reachable": "Nicht erreichbar",
    "overview.empty_title": "Keine Lüftungsberater-Räume gefunden.",
    "overview.empty_description": "Räume werden automatisch erkannt oder können per entities: angegeben werden.",
    "overview.no_remote_rooms": "Keine Räume verfügbar",
    "overview.room": "Raum",
    "overview.rooms": "Räume",
    "overview.back": "Zurück",
    "overview.close": "Schließen",
    "picker.overview.name": "Lüftungsberater – Übersicht",
    "picker.overview.description": "Kompakte Übersicht über lokale und entfernte Lüftungsberater.",
    "editor.room": "Raum",
    "editor.select_room": "Raum auswählen …",
    "editor.card_name": "Kartenname (optional)",
    "editor.card_name_placeholder": "z. B. Wohnzimmer",
    "editor.room_hint": "Empfehlung, Farbe, Begründung und Messwerte werden automatisch übernommen.",
    "editor.title": "Titel (optional)",
    "editor.rooms": "Lokale Räume",
    "editor.installations": "Installationen und Räume",
    "editor.local": "Lokal",
    "editor.remote": "Tailscale-Remote",
    "editor.unavailable": "nicht erreichbar",
    "editor.move_up": "Nach oben",
    "editor.move_down": "Nach unten",
    "editor.rooms_hint": "Installationen und Räume können einzeln ein- oder ausgeblendet und mit den Pfeilen sortiert werden. Neue Räume werden standardmäßig automatisch aufgenommen."
  },
  en: {
    "recommendation.open_now": "Open the windows now",
    "recommendation.keep_open": "Keep the windows open a little longer",
    "recommendation.can_close": "You can close the windows now",
    "recommendation.short_observation": "Open the windows briefly and keep an eye on it",
    "recommendation.better_close": "Better close the windows",
    "recommendation.caution_keep_closed": "Better keep the windows closed for now",
    "recommendation.keep_closed": "Keep the windows closed",
    "recommendation.close_now": "Close the windows now",
    "recommendation.wait": "Better wait a little longer",
    "recommendation.optional": "Airing is optional",
    "recommendation.unknown": "No reliable recommendation is available right now",
    "reason.incomplete_data": "At least one required temperature or humidity value is unavailable right now. The recommendation will update automatically as soon as the sensor data is complete again.",
    "duration.incomplete_data": "A reliable window-opening time cannot be determined from the current sensor data yet.",
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
    "window.open_since": "Window / door is open · for {duration}",
    "window.open": "Window / door is open",
    "window.minute": "minute",
    "window.minutes": "minutes",
    "window.hour": "hour",
    "window.hours": "hours",
    "window.and": "and",
    "airing.open": "Open ventilation details",
    "airing.last": "Last confirmed window airing: {hours} h ago",
    "airing.history": "Open ventilation history",
    "airing.none": "No confirmed window airing has been recorded yet",
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
    "metric.absolute_humidity_outdoor_open": "Open outdoor absolute humidity",
    "metric.absolute_humidity_difference_open": "Open absolute humidity difference history",
    "co2.history": "Open CO₂ history",
    "co2.status_history": "Open CO₂ assessment history",
    "co2.grace": "Sensor briefly unavailable, using the last valid value",
    "co2.unavailable": "CO₂ sensor unavailable · assessment temporarily continues without CO₂",
    "co2.open": "Open CO₂ sensor",
    "warning.open": "Open warning / source data",
    "why": "Why this recommendation?",
    "duration": "⏱️ Recommended window-opening time:",
    "hint": "Tap a value for its history · tap the colored status area for details",
    "picker.room.name": "Ventilation Advisor – Room",
    "picker.room.description": "Detailed ventilation recommendation for a single room.",
    "overview.invalid_entities": "entities must be a list of entity IDs.",
    "overview.open": "open",
    "overview.not_reachable": "Not reachable",
    "overview.empty_title": "No Ventilation Advisor rooms found.",
    "overview.empty_description": "Rooms are discovered automatically or can be specified with entities:.",
    "overview.no_remote_rooms": "No rooms available",
    "overview.room": "room",
    "overview.rooms": "rooms",
    "overview.back": "Back",
    "overview.close": "Close",
    "picker.overview.name": "Ventilation Advisor – Overview",
    "picker.overview.description": "Compact overview of local and remote Ventilation Advisors.",
    "editor.room": "Room",
    "editor.select_room": "Select a room …",
    "editor.card_name": "Card name (optional)",
    "editor.card_name_placeholder": "e.g. Living room",
    "editor.room_hint": "Recommendation, color, explanation, and measurements are filled in automatically.",
    "editor.title": "Title (optional)",
    "editor.rooms": "Local rooms",
    "editor.installations": "Installations and rooms",
    "editor.local": "Local",
    "editor.remote": "Tailscale remote",
    "editor.unavailable": "not reachable",
    "editor.move_up": "Move up",
    "editor.move_down": "Move down",
    "editor.rooms_hint": "Installations and rooms can be shown or hidden individually and reordered with the arrow buttons. New rooms are included automatically by default."
  },
  tr: {
    "recommendation.open_now": "Şimdi pencereleri aç",
    "recommendation.keep_open": "Pencereleri biraz daha açık tut",
    "recommendation.can_close": "Artık pencereleri kapatabilirsin",
    "recommendation.short_observation": "Kısa süre havalandır ve durumu takip et",
    "recommendation.better_close": "Pencereleri kapatmak daha iyi",
    "recommendation.caution_keep_closed": "Şimdilik pencereleri kapalı tutmak daha iyi",
    "recommendation.keep_closed": "Pencereleri kapalı tut",
    "recommendation.close_now": "Pencereleri şimdi kapat",
    "recommendation.wait": "Biraz daha beklemek daha iyi",
    "recommendation.optional": "Havalandırma isteğe bağlı",
    "recommendation.unknown": "Şu anda güvenilir bir öneri verilemiyor",
    "reason.incomplete_data": "Gerekli sıcaklık veya nem değerlerinden en az biri şu anda kullanılamıyor. Sensör verileri tekrar tamamlandığında öneri otomatik olarak güncellenecek.",
    "duration.incomplete_data": "Mevcut sensör verileriyle güvenilir bir havalandırma süresi henüz belirlenemiyor.",
    "co2.very_good": "çok iyi",
    "co2.good": "iyi",
    "co2.elevated": "yüksek",
    "co2.high": "çok yüksek",
    "co2.critical": "kritik",
    "co2.unknown": "bilinmiyor",
    "weather_service": "hava durumu hizmeti",
    "history_open": "Geçmişi aç",
    "setup.title": "Oda seç",
    "setup.description": "Görsel düzenleyiciden bir Havalandırma Danışmanı odası seç.",
    "entity_missing": "{entity} entity'si bulunamadı.",
    "window.open_since": "Pencere / kapı açık · {duration}dır",
    "window.open": "Pencere / kapı açık",
    "window.minute": "dakika",
    "window.minutes": "dakika",
    "window.hour": "saat",
    "window.hours": "saat",
    "window.and": "ve",
    "airing.open": "Havalandırma ayrıntılarını aç",
    "airing.last": "Son doğrulanmış havalandırma: {hours} saat önce",
    "airing.history": "Havalandırma geçmişini aç",
    "airing.none": "Henüz doğrulanmış bir havalandırma kaydedilmedi",
    "metric.inside": "{value} içeride",
    "metric.outside": "{value} dışarıda",
    "metric.target": "hedef {value}",
    "metric.temperature": "Sıcaklık",
    "metric.humidity": "Nem",
    "metric.indoor_temperature_open": "İç sıcaklığı aç",
    "metric.outdoor_temperature_open": "Dış sıcaklığı aç",
    "metric.thermostat_open": "Termostatı aç",
    "metric.indoor_humidity_open": "İç nemi aç",
    "metric.outdoor_humidity_open": "Dış nemi aç",
    "metric.absolute_humidity_open": "İç mutlak nemi aç",
    "metric.absolute_humidity_outdoor_open": "Dış mutlak nemi aç",
    "metric.absolute_humidity_difference_open": "Mutlak nem farkı geçmişini aç",
    "co2.history": "CO₂ geçmişini aç",
    "co2.status_history": "CO₂ değerlendirme geçmişini aç",
    "co2.grace": "Sensör kısa süreliğine kullanılamıyor; son geçerli değer kullanılıyor",
    "co2.unavailable": "CO₂ sensörü kullanılamıyor · değerlendirme geçici olarak CO₂ olmadan devam ediyor",
    "co2.open": "CO₂ sensörünü aç",
    "warning.open": "Uyarı / kaynak verisini aç",
    "why": "Bu önerinin nedeni ne?",
    "duration": "⏱️ Önerilen pencere açık kalma süresi:",
    "hint": "Geçmiş için bir değere dokun · ayrıntılar için renkli durum alanına dokun",
    "picker.room.name": "Havalandırma Danışmanı – Oda",
    "picker.room.description": "Tek bir oda için ayrıntılı havalandırma önerisi.",
    "overview.invalid_entities": "entities bir entity ID listesi olmalıdır.",
    "overview.open": "açık",
    "overview.not_reachable": "Ulaşılamıyor",
    "overview.empty_title": "Havalandırma Danışmanı odası bulunamadı.",
    "overview.empty_description": "Odalar otomatik bulunur veya entities: ile belirtilebilir.",
    "overview.no_remote_rooms": "Kullanılabilir oda yok",
    "overview.room": "oda",
    "overview.rooms": "oda",
    "overview.back": "Geri",
    "overview.close": "Kapat",
    "picker.overview.name": "Havalandırma Danışmanı – Genel Bakış",
    "picker.overview.description": "Yerel ve uzak Havalandırma Danışmanlarının kompakt görünümü.",
    "editor.room": "Oda",
    "editor.select_room": "Oda seç …",
    "editor.card_name": "Kart adı (isteğe bağlı)",
    "editor.card_name_placeholder": "örn. Salon",
    "editor.room_hint": "Öneri, renk, açıklama ve ölçüm değerleri otomatik olarak alınır.",
    "editor.title": "Başlık (isteğe bağlı)",
    "editor.rooms": "Yerel odalar",
    "editor.installations": "Kurulumlar ve odalar",
    "editor.local": "Yerel",
    "editor.remote": "Tailscale uzak",
    "editor.unavailable": "ulaşılamıyor",
    "editor.move_up": "Yukarı taşı",
    "editor.move_down": "Aşağı taşı",
    "editor.rooms_hint": "Kurulumlar ve odalar ayrı ayrı gösterilip gizlenebilir ve ok düğmeleriyle sıralanabilir. Yeni odalar varsayılan olarak otomatik eklenir."
  }
};

function lbLanguage(hass) {
  const raw = (
    hass?.language ||
    document.documentElement?.lang ||
    navigator.language ||
    "en"
  ).toLowerCase();
  if (raw.startsWith("de")) return "de";
  if (raw.startsWith("tr")) return "tr";
  return "en";
}

function lbLocale(hass) {
  const lang = lbLanguage(hass);
  if (lang === "de") return "de-DE";
  if (lang === "tr") return "tr-TR";
  return "en-US";
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

  _isRemoteSnapshot() {
    return Boolean(this._config?.remote_snapshot);
  }

  _stateObject() {
    if (this._isRemoteSnapshot()) {
      const snap = this._config.remote_snapshot || {};
      return {
        state: snap.state,
        attributes: snap.attributes || {},
      };
    }
    return this._config?.entity ? this._hass?.states?.[this._config.entity] : null;
  }

  _localizeState(state) {
    return lbT(this._hass, `recommendation.${state}`);
  }

  _co2Label(status) {
    return lbT(this._hass, `co2.${status}`);
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
    if (value === null || value === undefined || value === "") return null;
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
    if (this._isRemoteSnapshot()) return false;
    return Boolean(entityId && this._hass?.states?.[entityId]);
  }

  _valueUnit(value, unit) {
    return `${value}${LB_NNBSP}${unit}`;
  }

  _openDuration(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return null;
    const minutes = Math.max(0, Math.round(number));
    if (minutes <= 60) {
      return `${minutes} ${lbT(this._hass, minutes === 1 ? "window.minute" : "window.minutes")}`;
    }

    const hours = Math.floor(minutes / 60);
    const remainder = minutes % 60;
    const hourPart = `${hours} ${lbT(this._hass, hours === 1 ? "window.hour" : "window.hours")}`;
    if (!remainder) return hourPart;
    return `${hourPart} ${lbT(this._hass, "window.and")} ${remainder} ${lbT(this._hass, remainder === 1 ? "window.minute" : "window.minutes")}`;
  }

  _metric(text, entityId, title = null) {
    title = title || lbT(this._hass, "history_open");
    const escaped = this._escape(text);
    if (!this._entityExists(entityId)) return `<span>${escaped}</span>`;
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
    const event = new Event("hass-action", { bubbles: true, composed: true });
    event.detail = {
      config: { entity: entityId, tap_action: { action: "more-info" } },
      action: "tap",
    };
    this.dispatchEvent(event);
  }

  _handleMainTap() {
    if (this._isRemoteSnapshot() || !this._config?.entity) return;
    const event = new Event("hass-action", { bubbles: true, composed: true });
    event.detail = {
      config: {
        entity: this._config.entity,
        tap_action: this._config.tap_action || { action: "more-info" },
      },
      action: "tap",
    };
    this.dispatchEvent(event);
  }

  _render() {
    if (!this.shadowRoot) return;
    if (!this._hass || !this._config) {
      this.shadowRoot.innerHTML = "";
      return;
    }

    if (!this._config.entity && !this._isRemoteSnapshot()) {
      this.shadowRoot.innerHTML = `
        <style>
          ha-card { padding: 18px; }
          .setup { display: grid; gap: 6px; }
          .setup strong { font-size: 16px; }
          .setup span { color: var(--secondary-text-color); line-height: 1.4; }
        </style>
        <ha-card><div class="setup">
          <strong>${lbT(this._hass, "setup.title")}</strong>
          <span>${lbT(this._hass, "setup.description")}</span>
        </div></ha-card>`;
      return;
    }

    const st = this._stateObject();
    if (!st) {
      const entity = this._config.entity || "remote";
      this.shadowRoot.innerHTML = `<ha-card><div class="error">${this._escape(lbT(this._hass, "entity_missing", { entity }))}</div></ha-card>`;
      return;
    }

    const remote = this._isRemoteSnapshot();
    const a = st.attributes || {};
    const status = a.status || "yellow";
    const meta = this._statusMeta(status);
    const incompleteData = ["unknown", "unavailable", "none", ""].includes(String(st.state ?? "").toLowerCase());
    const recommendation = lbLocalizedEntityText(
      this._hass,
      a,
      "recommendation",
      a.recommendation || (incompleteData ? lbT(this._hass, "recommendation.unknown") : this._localizeState(st.state))
    );
    const reason = lbLocalizedEntityText(
      this._hass,
      a,
      "reason",
      a.reason || (incompleteData ? lbT(this._hass, "reason.incomplete_data") : "")
    );
    const durationText = lbLocalizedEntityText(
      this._hass,
      a,
      "duration",
      a.duration || (incompleteData ? lbT(this._hass, "duration.incomplete_data") : "")
    );
    const title = this._config.name || a.room_name || a.friendly_name || "Lüftungsberater";

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
    const openDuration = this._openDuration(a.open_minutes);

    const hasWindows = a.has_window_contacts === true;
    const windowOpen = a.window_open === true;
    const windowSources = Array.isArray(a.source_window_entities) ? a.source_window_entities : [];
    const airingSource =
      a.source_airing ||
      a.source_last_airing ||
      windowSources.find((entityId) => this._entityExists(entityId)) ||
      null;

    const rows = [];
    if (hasWindows) {
      if (windowOpen) {
        const label = openDuration
          ? lbT(this._hass, "window.open_since", { duration: openDuration })
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
          html: this._metric(lbT(this._hass, "airing.none"), airingSource, lbT(this._hass, "airing.open")),
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
        parts.push(this._metric(
          lbT(this._hass, "metric.target", { value: this._valueUnit(target, tempUnit) }),
          a.source_target_temperature,
          lbT(this._hass, "metric.thermostat_open")
        ));
      }
      rows.push({ icon: "mdi:thermometer", html: `${lbT(this._hass, "metric.temperature")}: ${parts.join(" · ")}` });
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
        )} · ${this._metric(
          lbT(this._hass, "metric.outside", { value: this._valueUnit(aho, "g/m³") }),
          a.source_absolute_humidity_outside,
          lbT(this._hass, "metric.absolute_humidity_outdoor_open")
        )}`;
      }
      if (diff !== null) html += ` · ${this._metric(
        `Δ ${this._valueUnit(diff, "g/m³")}`,
        a.source_absolute_humidity_difference,
        lbT(this._hass, "metric.absolute_humidity_difference_open")
      )}`;
      rows.push({ icon: "mdi:water-percent", html });
    }

    const co2DataStatus = a.co2_data_status || "current";
    if (a.has_co2 === true) {
      if (co2ppm !== null) {
        let co2Text = `CO₂: ${this._metric(this._valueUnit(co2ppm, "ppm"), a.source_co2, lbT(this._hass, "co2.history"))} · ${this._metric(this._co2Label(a.co2_status), a.source_co2_status, lbT(this._hass, "co2.status_history"))}`;
        if (co2DataStatus === "grace") co2Text += ` · ${lbT(this._hass, "co2.grace")}`;
        rows.push({ icon: "mdi:molecule-co2", cls: co2DataStatus === "grace" ? "data-warning" : "", html: co2Text });
      } else {
        rows.push({
          icon: "mdi:molecule-co2-off",
          cls: "data-warning",
          html: this._metric(lbT(this._hass, "co2.unavailable"), a.source_co2, lbT(this._hass, "co2.open")),
        });
      }
    }

    const showDuration = Boolean(durationText) && a.duration_key !== "not_needed";
    const reasonHtml = reason ? this._escape(reason) : "";

    this.shadowRoot.innerHTML = `
      <style>
        :host { --lb-green: var(--success-color, #43a047); --lb-yellow: var(--warning-color, #f9a825); --lb-red: var(--error-color, #db4437); display: block; }
        ha-card { overflow: hidden; padding: 0; user-select: none; -webkit-tap-highlight-color: transparent; }
        .header { display: flex; align-items: center; gap: 14px; padding: 16px; color: var(--primary-text-color); border-left: 6px solid var(--lb-accent); background: color-mix(in srgb, var(--lb-accent) 14%, var(--ha-card-background, var(--card-background-color))); }
        .header.main-tap { cursor: pointer; }
        .header.main-tap:focus-visible { outline: 2px solid var(--primary-color); outline-offset: -2px; }
        .header.green { --lb-accent: var(--lb-green); } .header.yellow { --lb-accent: var(--lb-yellow); } .header.red { --lb-accent: var(--lb-red); }
        .icon-wrap { width: 48px; height: 48px; border-radius: 50%; display: grid; place-items: center; flex: 0 0 auto; background: color-mix(in srgb, var(--lb-accent) 20%, transparent); color: var(--lb-accent); }
        .main-icon { --mdc-icon-size: 31px; color: var(--lb-accent); }
        .head-text { min-width: 0; flex: 1; }
        .title { font-size: 14px; color: var(--secondary-text-color); margin-bottom: 3px; }
        .recommendation { font-size: 20px; font-weight: 600; line-height: 1.15; overflow-wrap: anywhere; }
        .body { padding: 14px 16px 16px; }
        .why { font-size: 15px; font-weight: 700; color: var(--primary-text-color); margin-bottom: 6px; }
        .reason { line-height: 1.45; overflow-wrap: anywhere; }
        .duration { display: grid; gap: 2px; margin-top: 12px; line-height: 1.4; }
        .duration-label { font-weight: 700; }
        .facts { display: grid; gap: 8px; padding-top: 13px; margin-top: 13px; border-top: 1px solid var(--divider-color); color: var(--secondary-text-color); font-size: 12.5px; }
        .fact { display: grid; grid-template-columns: 22px minmax(0, 1fr); gap: 7px; align-items: start; line-height: 1.35; }
        .fact ha-icon { --mdc-icon-size: 18px; color: var(--secondary-text-color); }
        .fact.window-open { color: var(--primary-text-color); font-weight: 600; }
        .fact.window-open ha-icon { color: var(--primary-color); }
        .fact.data-warning { color: var(--warning-color); font-weight: 600; }
        .fact.data-warning ha-icon { color: var(--warning-color); }
        .metric-link { appearance: none; background: none; border: 0; padding: 0; margin: 0; color: inherit; font: inherit; line-height: inherit; cursor: pointer; text-decoration-line: underline; text-decoration-style: dotted; text-decoration-thickness: 1px; text-underline-offset: 2px; text-decoration-color: color-mix(in srgb, currentColor 45%, transparent); text-align: inherit; }
        .metric-link:hover, .metric-link:focus-visible { color: var(--primary-color); text-decoration-style: solid; outline: none; }
        .hint { margin-top: 12px; color: var(--secondary-text-color); font-size: 11px; opacity: 0.8; }
        .error { padding: 16px; color: var(--error-color); }
      </style>
      <ha-card aria-label="${this._escape(title)}">
        <div class="header ${meta.cls}${remote ? "" : " main-tap"}" ${remote ? "" : 'tabindex="0" role="button"'}>
          <div class="icon-wrap"><ha-icon class="main-icon" icon="${meta.icon}"></ha-icon></div>
          <div class="head-text"><div class="title">${this._escape(title)}</div><div class="recommendation">${this._escape(recommendation)}</div></div>
        </div>
        <div class="body">
          ${reason ? `<div class="why">${lbT(this._hass, "why")}</div><div class="reason">${reasonHtml}</div>` : ""}
          ${showDuration ? `<div class="duration"><span class="duration-label">${lbT(this._hass, "duration")}</span><span>${this._escape(durationText)}</span></div>` : ""}
          ${rows.length ? `<div class="facts">${rows.map((row) => `<div class="fact ${row.cls || ""}"><ha-icon icon="${row.icon}"></ha-icon><span>${row.html}</span></div>`).join("")}</div>` : ""}
          ${remote ? "" : `<div class="hint">${lbT(this._hass, "hint")}</div>`}
        </div>
      </ha-card>`;

    if (!remote) {
      const mainTap = this.shadowRoot.querySelector(".header.main-tap");
      mainTap?.addEventListener("click", () => this._handleMainTap());
      mainTap?.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          this._handleMainTap();
        }
      });
      this.shadowRoot.querySelectorAll("[data-entity]").forEach((element) => {
        element.addEventListener("click", (event) => {
          event.stopPropagation();
          this._dispatchMoreInfo(element.dataset.entity);
        });
      });
    }
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
      if (!stateObj || stateObj.attributes.status === undefined || stateObj.attributes.reason === undefined) return null;
      return { config: { type: "custom:lueftungsberater-card", entity: entityId } };
    },
  });
}

class LueftungsberaterOverviewCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._remoteGroups = [];
    this._remoteFetchBusy = false;
    this._remoteTimer = null;
    this._dialog = null;
    this._dialogMode = null;
    this._dialogGroupId = null;
    this._openRoomRef = null;
    this._popupCard = null;
    this._dialogLocation = null;
    this._handleNavigation = () => this._destroyDialog();
  }

  connectedCallback() {
    this._ensureRemoteTimer();
    window.addEventListener("location-changed", this._handleNavigation);
    window.addEventListener("popstate", this._handleNavigation);
  }

  disconnectedCallback() {
    if (this._remoteTimer) clearInterval(this._remoteTimer);
    this._remoteTimer = null;
    window.removeEventListener("location-changed", this._handleNavigation);
    window.removeEventListener("popstate", this._handleNavigation);
    this._destroyDialog();
  }

  setConfig(config) {
    this._config = { ...config };
    if (this._config.entities !== undefined && !Array.isArray(this._config.entities)) {
      throw new Error(lbT(this._hass, "overview.invalid_entities"));
    }
    this._ensureShell();
    this._renderOverview();
  }

  set hass(hass) {
    if (this._dialog && this._dialogLocation && window.location.pathname !== this._dialogLocation) {
      this._destroyDialog();
    }
    const first = !this._hass;
    const previousLanguage = this._hass ? lbLanguage(this._hass) : null;
    this._hass = hass;
    this._ensureShell();
    this._renderOverview();

    if (this._popupCard && !this._openRoomRef?.remote) {
      this._popupCard.hass = hass;
    }
    if (this._dialogMode === "instance") {
      const group = this._findGroup(this._dialogGroupId);
      if (group && !group.remote) this._renderInstanceDialog(group);
    }

    if (first || previousLanguage !== lbLanguage(hass)) this._fetchRemote();
    this._ensureRemoteTimer();
  }

  getCardSize() {
    const groups = this._groups();
    if (groups.length > 1) return Math.max(2, groups.length + 1);
    return Math.max(1, groups[0]?.rooms?.length || 1);
  }

  static getConfigElement() {
    return document.createElement("lueftungsberater-overview-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  _ensureRemoteTimer() {
    if (this._remoteTimer || !this.isConnected) return;
    this._remoteTimer = setInterval(() => this._fetchRemote(), 10000);
    if (this._hass) this._fetchRemote();
  }

  async _fetchRemote() {
    if (!this._hass || this._remoteFetchBusy) return;
    this._remoteFetchBusy = true;
    try {
      const message = { type: "lueftungsberater/remote_overview" };
      let result;
      if (typeof this._hass.callWS === "function") {
        result = await this._hass.callWS(message);
      } else if (this._hass.connection?.sendMessagePromise) {
        result = await this._hass.connection.sendMessagePromise(message);
      } else {
        return;
      }
      this._remoteGroups = Array.isArray(result) ? result : [];
      this._renderOverview();
      this._refreshRemoteDialog();
    } catch (_err) {
      // The backend coordinator owns the 3-minute grace period. A temporary
      // frontend websocket hiccup must not invalidate a cached remote snapshot.
    } finally {
      this._remoteFetchBusy = false;
    }
  }

  _escape(value) {
    const div = document.createElement("div");
    div.textContent = String(value ?? "");
    return div.innerHTML;
  }

  _isAdvisorEntity(stateObj) {
    if (!stateObj?.attributes) return false;
    const a = stateObj.attributes;
    return Boolean(
      stateObj.entity_id?.startsWith("sensor.") &&
      typeof a.status === "string" &&
      typeof a.mode === "string" &&
      typeof a.recommendation === "string" &&
      typeof a.reason === "string" &&
      (a.room_name !== undefined || a.absolute_humidity_inside !== undefined)
    );
  }

  _roomName(stateObj) {
    const a = stateObj.attributes || {};
    if (a.room_name) return String(a.room_name);
    const friendly = a.friendly_name || stateObj.entity_id;
    return String(friendly).replace(/^Lüftungsberater\s*/i, "").replace(/\s*Lüftungsberater$/i, "").trim() || friendly;
  }

  _statusMeta(status) {
    if (status === "red") return { rank: 3, cls: "red", icon: "mdi:window-closed-variant" };
    if (status === "yellow") return { rank: 2, cls: "yellow", icon: "mdi:window-open" };
    return { rank: 1, cls: "green", icon: "mdi:window-open-variant" };
  }

  _hiddenGroups() {
    return new Set(Array.isArray(this._config?.hidden_groups) ? this._config.hidden_groups : []);
  }

  _hiddenRooms(groupId) {
    const value = this._config?.hidden_rooms?.[groupId];
    return new Set(Array.isArray(value) ? value : []);
  }

  _ordered(items, order, getId) {
    const ids = Array.isArray(order) ? order : [];
    const position = new Map(ids.map((id, index) => [String(id), index]));
    return [...items].sort((a, b) => {
      const aId = String(getId(a));
      const bId = String(getId(b));
      const ai = position.has(aId) ? position.get(aId) : Number.MAX_SAFE_INTEGER;
      const bi = position.has(bId) ? position.get(bId) : Number.MAX_SAFE_INTEGER;
      if (ai !== bi) return ai - bi;
      return String(a.name || aId).localeCompare(String(b.name || bId), lbLocale(this._hass));
    });
  }

  _roomFromLocal(stateObj, index) {
    const a = stateObj.attributes || {};
    const meta = this._statusMeta(a.status || "yellow");
    const state = String(stateObj.state || "unknown");
    return {
      key: stateObj.entity_id,
      entityId: stateObj.entity_id,
      state,
      attributes: a,
      name: this._roomName(stateObj),
      status: a.status || "yellow",
      cls: meta.cls,
      icon: meta.icon,
      rank: meta.rank,
      recommendation: lbLocalizedEntityText(
        this._hass,
        a,
        "recommendation",
        a.recommendation || lbT(this._hass, `recommendation.${state}`)
      ),
      windowOpen: a.window_open === true,
      remote: false,
      index,
    };
  }

  _localGroups() {
    if (!this._hass) return [];
    const explicit = Array.isArray(this._config?.entities) ? new Set(this._config.entities) : null;
    const groups = new Map();
    let index = 0;
    for (const stateObj of Object.values(this._hass.states)) {
      if (!this._isAdvisorEntity(stateObj)) continue;
      if (explicit && !explicit.has(stateObj.entity_id)) continue;
      const a = stateObj.attributes || {};
      const instanceId = String(a.instance_id || "legacy-local");
      const instanceName = String(a.instance_name || "Lüftungsberater");
      const groupId = `local:${instanceId}`;
      if (this._hiddenRooms(groupId).has(stateObj.entity_id)) continue;
      if (!groups.has(instanceId)) {
        groups.set(instanceId, {
          id: groupId,
          sourceId: instanceId,
          name: instanceName,
          available: true,
          remote: false,
          rooms: [],
        });
      }
      groups.get(instanceId).rooms.push(this._roomFromLocal(stateObj, index++));
    }
    for (const group of groups.values()) {
      group.rooms = this._ordered(
        group.rooms,
        this._config?.room_order?.[group.id],
        (room) => room.key
      );
    }
    return [...groups.values()];
  }

  _remoteRoomKey(group, room, index) {
    // Prefer the room name so selection/order survives a rolling upgrade from
    // v0.6.10 peers which did not export a dedicated room id yet.
    const stable = room?.name ?? room?.attributes?.room_name ?? room?.id ?? index;
    return `${group.id}:room:${String(stable)}`;
  }

  _remoteRoom(group, room, index) {
    const attrs = room?.attributes && typeof room.attributes === "object" ? room.attributes : {};
    const state = String(room?.state || "unknown");
    const status = String(attrs.status || "yellow");
    const meta = this._statusMeta(status);
    const name = String(room?.name || attrs.room_name || attrs.friendly_name || `${lbT(this._hass, "overview.room")} ${index + 1}`);
    return {
      key: this._remoteRoomKey(group, room, index),
      state,
      attributes: attrs,
      name,
      status,
      cls: meta.cls,
      icon: meta.icon,
      rank: meta.rank,
      recommendation: lbLocalizedEntityText(
        this._hass,
        attrs,
        "recommendation",
        attrs.recommendation || lbT(this._hass, `recommendation.${state}`)
      ),
      windowOpen: attrs.window_open === true,
      remote: true,
      index,
    };
  }

  _normalizedRemoteGroups() {
    return (this._remoteGroups || []).map((rawGroup) => {
      const group = {
        id: String(rawGroup.id),
        name: String(rawGroup.name || "Lüftungsberater"),
        available: rawGroup.available !== false,
        remote: true,
        rooms: [],
      };
      const hidden = this._hiddenRooms(group.id);
      const rawRooms = Array.isArray(rawGroup.rooms) ? rawGroup.rooms : [];
      group.rooms = rawRooms
        .map((room, index) => this._remoteRoom(group, room, index))
        .filter((room) => !hidden.has(room.key));
      group.rooms = this._ordered(
        group.rooms,
        this._config?.room_order?.[group.id],
        (room) => room.key
      );
      return group;
    });
  }

  _groups() {
    const hidden = this._hiddenGroups();
    const groups = [...this._localGroups(), ...this._normalizedRemoteGroups()]
      .filter((group) => !hidden.has(group.id))
      .filter((group) => !group.available || group.rooms.length > 0);
    return this._ordered(groups, this._config?.group_order, (group) => group.id);
  }

  _groupClass(group) {
    if (!group.available) return "unavailable";
    if (group.rooms.some((room) => room.status === "red")) return "red";
    if (group.rooms.some((room) => room.status === "yellow")) return "yellow";
    return "green";
  }

  _roomRow(room, groupId) {
    const badge = room.windowOpen
      ? `<span class="badge"><ha-icon icon="mdi:window-open-variant"></ha-icon>${lbT(this._hass, "overview.open")}</span>`
      : "";
    return `
      <button type="button" class="room-row ${room.cls}" data-room-key="${this._escape(room.key)}" data-group-id="${this._escape(groupId)}">
        <ha-icon class="status-icon" icon="${room.icon}"></ha-icon>
        <span class="room-line"><strong>${this._escape(room.name)}</strong><span class="separator"> · </span><span>${this._escape(room.recommendation)}</span></span>
        ${badge}
        <ha-icon class="chevron" icon="mdi:chevron-right"></ha-icon>
      </button>`;
  }

  _groupRow(group) {
    const cls = this._groupClass(group);
    const count = group.rooms.length;
    const secondary = !group.available
      ? lbT(this._hass, "overview.not_reachable")
      : `${count} ${lbT(this._hass, count === 1 ? "overview.room" : "overview.rooms")}`;
    const disabled = !group.available || !count;
    return `
      <button type="button" class="group-row ${cls}" data-group-open="${this._escape(group.id)}" ${disabled ? "disabled" : ""}>
        <ha-icon class="group-icon" icon="${group.remote ? "mdi:lan-connect" : "mdi:home-outline"}"></ha-icon>
        <span class="group-copy"><strong>${this._escape(group.name)}</strong><small>${this._escape(secondary)}</small></span>
        ${disabled ? "" : '<ha-icon class="chevron" icon="mdi:chevron-right"></ha-icon>'}
      </button>`;
  }

  _ensureShell() {
    if (!this.shadowRoot || this.shadowRoot.querySelector("#overview")) return;
    this.shadowRoot.innerHTML = `
      <style>
        :host { --lb-green: var(--success-color, #43a047); --lb-yellow: var(--warning-color, #f9a825); --lb-red: var(--error-color, #db4437); display: block; }
        ha-card { overflow: hidden; padding: 0; }
        .overview-title { padding: 12px 16px 9px; color: var(--primary-text-color); font-size: 17px; font-weight: 700; border-bottom: 1px solid var(--divider-color); }
        .room-row, .group-row { --row-accent: var(--lb-green); appearance: none; width: 100%; min-width: 0; border: 0; border-top: 1px solid var(--divider-color); border-left: 4px solid var(--row-accent); background: transparent; color: var(--primary-text-color); font: inherit; text-align: left; cursor: pointer; -webkit-tap-highlight-color: transparent; }
        .room-row:first-child, .group-row:first-child { border-top: 0; }
        .room-row.yellow, .group-row.yellow { --row-accent: var(--lb-yellow); }
        .room-row.red, .group-row.red { --row-accent: var(--lb-red); }
        .group-row.unavailable { --row-accent: var(--secondary-text-color); opacity: .75; cursor: default; }
        .room-row { display: grid; grid-template-columns: 27px minmax(0, 1fr) auto 22px; gap: 8px; align-items: center; min-height: 48px; padding: 9px 10px 9px 12px; }
        .group-row { display: grid; grid-template-columns: 34px minmax(0, 1fr) 22px; gap: 9px; align-items: center; min-height: 56px; padding: 10px 12px; }
        .room-row:not(:disabled):hover, .room-row:focus-visible, .group-row:not(:disabled):hover, .group-row:focus-visible { background: color-mix(in srgb, var(--row-accent) 7%, transparent); outline: none; }
        .status-icon { --mdc-icon-size: 22px; color: var(--row-accent); }
        .group-icon { --mdc-icon-size: 25px; color: var(--row-accent); }
        .room-line { min-width: 0; line-height: 1.3; overflow-wrap: anywhere; }
        .room-line strong { font-weight: 700; }
        .separator { color: var(--secondary-text-color); }
        .badge { display: inline-flex; align-items: center; gap: 3px; padding: 2px 6px; border-radius: 999px; background: color-mix(in srgb, var(--primary-color) 12%, transparent); color: var(--primary-text-color); font-size: 10px; font-weight: 600; white-space: nowrap; }
        .badge ha-icon { --mdc-icon-size: 13px; color: var(--primary-color); }
        .chevron { --mdc-icon-size: 21px; color: var(--secondary-text-color); }
        .group-copy { display: grid; min-width: 0; gap: 2px; }
        .group-copy strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14px; }
        .group-copy small { color: var(--secondary-text-color); font-size: 11px; }
        .empty { display: grid; grid-template-columns: 30px minmax(0, 1fr); gap: 9px; padding: 16px; color: var(--secondary-text-color); }
        .empty strong { display: block; color: var(--primary-text-color); margin-bottom: 3px; }
        .empty span { display: block; line-height: 1.4; font-size: 12px; }
        dialog { box-sizing: border-box; width: min(94vw, 620px); max-height: min(88vh, 850px); margin: auto; padding: 0; border: 0; border-radius: var(--ha-card-border-radius, 12px); background: var(--ha-card-background, var(--card-background-color)); color: var(--primary-text-color); box-shadow: var(--ha-card-box-shadow, 0 8px 35px rgba(0,0,0,.35)); overflow: hidden; }
        dialog::backdrop { background: rgba(0,0,0,.48); }
        .dialog-shell { display: grid; grid-template-rows: auto minmax(0, 1fr); max-height: min(88vh, 850px); }
        .dialog-header { display: grid; grid-template-columns: 40px minmax(0,1fr) 40px; align-items: center; min-height: 52px; border-bottom: 1px solid var(--divider-color); }
        .dialog-title { padding: 0 8px; text-align: center; font-size: 16px; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .dialog-action { appearance: none; width: 40px; height: 40px; margin: 6px; border: 0; border-radius: 50%; background: transparent; color: var(--primary-text-color); cursor: pointer; display: grid; place-items: center; }
        .dialog-action:hover, .dialog-action:focus-visible { background: color-mix(in srgb, var(--primary-text-color) 8%, transparent); outline: none; }
        .dialog-action.hidden { visibility: hidden; }
        .dialog-body { min-height: 0; overflow: auto; padding: 0; }
        .detail-wrap { padding: 12px; }
        @media (max-width: 520px) { dialog { width: calc(100vw - 16px); max-height: calc(100vh - 32px); } .dialog-shell { max-height: calc(100vh - 32px); } .room-row { grid-template-columns: 25px minmax(0,1fr) auto 20px; gap: 6px; } }
      </style>
      <ha-card><div id="overview"></div></ha-card>`;
  }

  _renderOverview() {
    if (!this.shadowRoot || !this._hass || !this._config) return;
    this._ensureShell();
    const container = this.shadowRoot.querySelector("#overview");
    if (!container) return;
    const groups = this._groups();
    const title = String(this._config.title || "").trim();

    let content;
    if (!groups.length) {
      content = `<div class="empty"><ha-icon icon="mdi:home-search-outline"></ha-icon><div><strong>${lbT(this._hass, "overview.empty_title")}</strong><span>${lbT(this._hass, "overview.empty_description")}</span></div></div>`;
    } else if (groups.length === 1 && groups[0].available && groups[0].rooms.length) {
      content = groups[0].rooms.map((room) => this._roomRow(room, groups[0].id)).join("");
    } else {
      content = groups.map((group) => this._groupRow(group)).join("");
    }

    container.innerHTML = `${title ? `<div class="overview-title">${this._escape(title)}</div>` : ""}<div class="overview-content">${content}</div>`;
    container.querySelectorAll("[data-room-key]").forEach((element) => {
      element.addEventListener("click", () => this._showRoom(element.dataset.groupId, element.dataset.roomKey, false));
    });
    container.querySelectorAll("[data-group-open]").forEach((element) => {
      element.addEventListener("click", () => this._showInstanceRooms(element.dataset.groupOpen));
    });
  }

  _findGroup(groupId) {
    return this._groups().find((group) => group.id === groupId) || null;
  }

  _ensureDialog() {
    if (this._dialog?.isConnected) return this._dialog;
    const dialog = document.createElement("dialog");
    dialog.id = "lb-dialog";
    dialog.innerHTML = `
      <div class="dialog-shell">
        <div class="dialog-header">
          <button type="button" id="dialog-back" class="dialog-action hidden" aria-label="${lbT(this._hass, "overview.back")}"><ha-icon icon="mdi:arrow-left"></ha-icon></button>
          <div id="dialog-title" class="dialog-title"></div>
          <button type="button" id="dialog-close" class="dialog-action" aria-label="${lbT(this._hass, "overview.close")}"><ha-icon icon="mdi:close"></ha-icon></button>
        </div>
        <div id="dialog-body" class="dialog-body"></div>
      </div>`;
    this.shadowRoot.appendChild(dialog);
    this._dialog = dialog;

    dialog.querySelector("#dialog-close")?.addEventListener("click", () => this._closeDialog());
    dialog.querySelector("#dialog-back")?.addEventListener("click", () => this._showInstanceRooms(this._dialogGroupId));
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) this._closeDialog();
    });
    dialog.addEventListener("close", () => {
      if (this._dialog !== dialog) return;
      this._dialog = null;
      this._resetDialogState();
      dialog.remove();
    });
    return dialog;
  }

  _openDialog() {
    const dialog = this._ensureDialog();
    if (!dialog.open) {
      this._dialogLocation = window.location.pathname;
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    }
  }

  _closeDialog() {
    this._destroyDialog();
  }

  _destroyDialog() {
    const dialog = this._dialog;
    this._dialog = null;
    this._resetDialogState();
    if (!dialog) return;
    try {
      if (dialog.open && typeof dialog.close === "function") dialog.close();
    } catch (_err) {
      // Removing the freshly-created dialog below is sufficient as fallback.
    }
    dialog.removeAttribute("open");
    dialog.remove();
  }

  _resetDialogState() {
    this._destroyPopupCard();
    this._dialogMode = null;
    this._dialogGroupId = null;
    this._openRoomRef = null;
    this._dialogLocation = null;
  }

  _destroyPopupCard() {
    if (this._popupCard?.remove) this._popupCard.remove();
    this._popupCard = null;
  }

  _setDialogHeader(title, canBack) {
    const dialog = this._ensureDialog();
    const titleNode = dialog.querySelector("#dialog-title");
    const back = dialog.querySelector("#dialog-back");
    if (titleNode) titleNode.textContent = title || "";
    if (back) {
      back.classList.toggle("hidden", !canBack);
      back.setAttribute("aria-label", lbT(this._hass, "overview.back"));
    }
    const close = dialog.querySelector("#dialog-close");
    if (close) close.setAttribute("aria-label", lbT(this._hass, "overview.close"));
  }

  _renderInstanceDialog(group) {
    const dialog = this._ensureDialog();
    const body = dialog.querySelector("#dialog-body");
    if (!body) return;
    body.innerHTML = group.rooms.map((room) => this._roomRow(room, group.id)).join("");
    body.querySelectorAll("[data-room-key]").forEach((element) => {
      element.addEventListener("click", () => this._showRoom(element.dataset.groupId, element.dataset.roomKey, true));
    });
  }

  _showInstanceRooms(groupId) {
    const group = this._findGroup(groupId);
    if (!group || !group.available || !group.rooms.length) return;
    this._destroyPopupCard();
    this._dialogMode = "instance";
    this._dialogGroupId = group.id;
    this._openRoomRef = null;
    this._setDialogHeader(group.name, false);
    this._renderInstanceDialog(group);
    this._openDialog();
  }

  _showRoom(groupId, roomKey, canBack) {
    const group = this._findGroup(groupId);
    const room = group?.rooms?.find((candidate) => candidate.key === roomKey);
    if (!group || !room) return;
    this._destroyPopupCard();
    this._dialogMode = "room";
    this._dialogGroupId = group.id;
    this._openRoomRef = { groupId: group.id, roomKey: room.key, remote: room.remote, canBack };
    this._setDialogHeader(room.name, canBack);
    const dialog = this._ensureDialog();
    const body = dialog.querySelector("#dialog-body");
    if (!body) return;
    body.innerHTML = '<div class="detail-wrap" id="detail-wrap"></div>';
    const wrap = body.querySelector("#detail-wrap");
    const card = document.createElement("lueftungsberater-card");
    if (room.remote) {
      card.setConfig({ remote_snapshot: { state: room.state, attributes: room.attributes }, name: room.name });
    } else {
      card.setConfig({ entity: room.entityId, name: room.name });
    }
    card.hass = this._hass;
    wrap.appendChild(card);
    this._popupCard = card;
    this._openDialog();
  }

  _refreshRemoteDialog() {
    if (this._dialogMode === "instance") {
      const group = this._findGroup(this._dialogGroupId);
      if (!group || !group.remote) return;
      if (!group.available || !group.rooms.length) {
        this._closeDialog();
        return;
      }
      this._setDialogHeader(group.name, false);
      this._renderInstanceDialog(group);
      return;
    }

    if (!this._popupCard || !this._openRoomRef?.remote) return;
    const group = this._findGroup(this._openRoomRef.groupId);
    const room = group?.rooms?.find((candidate) => candidate.key === this._openRoomRef.roomKey);
    if (!group?.available || !room) {
      this._closeDialog();
      return;
    }
    this._popupCard.setConfig({ remote_snapshot: { state: room.state, attributes: room.attributes }, name: room.name });
    this._popupCard.hass = this._hass;
  }
}

if (!customElements.get("lueftungsberater-overview-card")) {
  customElements.define("lueftungsberater-overview-card", LueftungsberaterOverviewCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "lueftungsberater-overview-card")) {
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
    this._hassSignature = null;
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    const signature = this._signature(hass);
    this._hass = hass;
    if (signature !== this._hassSignature) {
      this._hassSignature = signature;
      this._render();
    }
  }

  _advisorEntities(hass = this._hass) {
    if (!hass) return [];
    return Object.values(hass.states)
      .filter((stateObj) => {
        const a = stateObj.attributes || {};
        return stateObj.entity_id.startsWith("sensor.") && typeof a.status === "string" && typeof a.mode === "string" && typeof a.recommendation === "string" && typeof a.reason === "string" && (a.room_name !== undefined || a.absolute_humidity_inside !== undefined);
      })
      .sort((a, b) => this._name(a).localeCompare(this._name(b), lbLocale(hass)));
  }

  _signature(hass) {
    if (!hass) return "none";
    const entities = this._advisorEntities(hass).map((stateObj) => `${stateObj.entity_id}:${this._name(stateObj)}`);
    return `${lbLanguage(hass)}|${entities.join("|")}`;
  }

  _name(stateObj) {
    return stateObj.attributes.room_name || stateObj.attributes.friendly_name || stateObj.entity_id;
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
    const event = new Event("config-changed", { bubbles: true, composed: true });
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
        label { display: grid; gap: 6px; color: var(--primary-text-color); font-size: 14px; font-weight: 600; }
        select, input { box-sizing: border-box; width: 100%; min-height: 44px; padding: 8px 10px; border: 1px solid var(--divider-color); border-radius: 8px; background: var(--ha-color-form-background, var(--card-background-color)); color: var(--primary-text-color); font: inherit; }
        .hint { color: var(--secondary-text-color); font-size: 12px; line-height: 1.4; }
      </style>
      <div class="editor">
        <label>${lbT(this._hass, "editor.room")}<select id="entity"><option value="">${lbT(this._hass, "editor.select_room")}</option>${entities.map((stateObj) => `<option value="${this._escape(stateObj.entity_id)}" ${stateObj.entity_id === current ? "selected" : ""}>${this._escape(this._name(stateObj))}</option>`).join("")}</select></label>
        <label>${lbT(this._hass, "editor.card_name")}<input id="name" type="text" value="${this._escape(this._config.name || "")}" placeholder="${this._escape(lbT(this._hass, "editor.card_name_placeholder"))}" /></label>
        <div class="hint">${lbT(this._hass, "editor.room_hint")}</div>
      </div>`;
    this.shadowRoot.querySelector("#entity")?.addEventListener("change", (event) => this._changed({ entity: event.target.value || undefined }));
    this.shadowRoot.querySelector("#name")?.addEventListener("change", (event) => this._changed({ name: event.target.value.trim() || undefined }));
  }
}

if (!customElements.get("lueftungsberater-card-editor")) {
  customElements.define("lueftungsberater-card-editor", LueftungsberaterCardEditor);
}

class LueftungsberaterOverviewCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hassSignature = null;
    this._remoteSignature = "";
    this._remoteGroups = [];
    this._remoteFetchBusy = false;
    this._remoteTimer = null;
    this._pendingRender = false;
  }

  connectedCallback() {
    this._ensureRemoteTimer();
  }

  disconnectedCallback() {
    if (this._remoteTimer) clearInterval(this._remoteTimer);
    this._remoteTimer = null;
  }

  setConfig(config) {
    this._config = { ...config };
    this._requestRender();
  }

  set hass(hass) {
    const first = !this._hass;
    const previousLanguage = this._hass ? lbLanguage(this._hass) : null;
    const signature = this._localSignature(hass);
    this._hass = hass;
    if (signature !== this._hassSignature) {
      this._hassSignature = signature;
      this._requestRender();
    }
    if (first || previousLanguage !== lbLanguage(hass)) this._fetchRemote();
    this._ensureRemoteTimer();
  }

  _ensureRemoteTimer() {
    if (this._remoteTimer || !this.isConnected) return;
    this._remoteTimer = setInterval(() => this._fetchRemote(), 10000);
    if (this._hass) this._fetchRemote();
  }

  async _fetchRemote() {
    if (!this._hass || this._remoteFetchBusy) return;
    this._remoteFetchBusy = true;
    try {
      const message = { type: "lueftungsberater/remote_overview" };
      let result;
      if (typeof this._hass.callWS === "function") {
        result = await this._hass.callWS(message);
      } else if (this._hass.connection?.sendMessagePromise) {
        result = await this._hass.connection.sendMessagePromise(message);
      } else {
        return;
      }
      const incoming = Array.isArray(result) ? result : [];
      const previous = new Map((this._remoteGroups || []).map((group) => [String(group.id), group]));
      this._remoteGroups = incoming.map((group) => {
        const old = previous.get(String(group.id));
        if (group?.available === false && (!Array.isArray(group.rooms) || !group.rooms.length) && Array.isArray(old?.rooms)) {
          return { ...group, rooms: old.rooms };
        }
        return group;
      });
      const signature = this._remoteStructureSignature();
      if (signature !== this._remoteSignature) {
        this._remoteSignature = signature;
        this._requestRender();
      }
    } catch (_err) {
      // Keep the last structural editor snapshot during a short frontend hiccup.
    } finally {
      this._remoteFetchBusy = false;
    }
  }

  _requestRender() {
    if (!this.shadowRoot || !this._config) return;
    const active = this.shadowRoot.activeElement;
    if (active && (active.matches?.('input[type="text"]') || active.matches?.("textarea"))) {
      this._pendingRender = true;
      if (!active.dataset.lbRenderAfterBlur) {
        active.dataset.lbRenderAfterBlur = "1";
        active.addEventListener("blur", () => {
          // Let the input's native `change` event finish first, otherwise a
          // deferred structural refresh could destroy the field before its
          // edited value is emitted to Home Assistant.
          setTimeout(() => {
            if (!this._pendingRender) return;
            this._pendingRender = false;
            this._render();
          }, 0);
        }, { once: true });
      }
      return;
    }
    this._pendingRender = false;
    this._render();
  }

  _escape(value) {
    const div = document.createElement("div");
    div.textContent = String(value ?? "");
    return div.innerHTML;
  }

  _isAdvisorEntity(stateObj) {
    if (!stateObj?.attributes) return false;
    const a = stateObj.attributes;
    return Boolean(
      stateObj.entity_id?.startsWith("sensor.") &&
      typeof a.status === "string" &&
      typeof a.mode === "string" &&
      typeof a.recommendation === "string" &&
      typeof a.reason === "string" &&
      (a.room_name !== undefined || a.absolute_humidity_inside !== undefined)
    );
  }

  _localGroups(hass = this._hass) {
    if (!hass) return [];
    const groups = new Map();
    for (const stateObj of Object.values(hass.states)) {
      if (!this._isAdvisorEntity(stateObj)) continue;
      const a = stateObj.attributes || {};
      const instanceId = String(a.instance_id || "legacy-local");
      const groupId = `local:${instanceId}`;
      if (!groups.has(groupId)) {
        groups.set(groupId, {
          id: groupId,
          name: String(a.instance_name || "Lüftungsberater"),
          remote: false,
          available: true,
          rooms: [],
        });
      }
      groups.get(groupId).rooms.push({
        key: stateObj.entity_id,
        entityId: stateObj.entity_id,
        name: String(a.room_name || a.friendly_name || stateObj.entity_id),
        remote: false,
      });
    }
    return [...groups.values()];
  }

  _remoteRoomKey(group, room, index) {
    // Prefer the room name so selection/order survives a rolling upgrade from
    // v0.6.10 peers which did not export a dedicated room id yet.
    const stable = room?.name ?? room?.attributes?.room_name ?? room?.id ?? index;
    return `${group.id}:room:${String(stable)}`;
  }

  _remoteEditorGroups() {
    return (this._remoteGroups || []).map((rawGroup) => {
      const group = {
        id: String(rawGroup.id),
        name: String(rawGroup.name || "Lüftungsberater"),
        remote: true,
        available: rawGroup.available !== false,
        rooms: [],
      };
      const rooms = Array.isArray(rawGroup.rooms) ? rawGroup.rooms : [];
      group.rooms = rooms.map((room, index) => ({
        key: this._remoteRoomKey(group, room, index),
        name: String(room?.name || room?.attributes?.room_name || room?.attributes?.friendly_name || `${lbT(this._hass, "overview.room")} ${index + 1}`),
        remote: true,
      }));
      return group;
    });
  }

  _ordered(items, order, getId) {
    const ids = Array.isArray(order) ? order : [];
    const position = new Map(ids.map((id, index) => [String(id), index]));
    return [...items].sort((a, b) => {
      const aId = String(getId(a));
      const bId = String(getId(b));
      const ai = position.has(aId) ? position.get(aId) : Number.MAX_SAFE_INTEGER;
      const bi = position.has(bId) ? position.get(bId) : Number.MAX_SAFE_INTEGER;
      if (ai !== bi) return ai - bi;
      return String(a.name || aId).localeCompare(String(b.name || bId), lbLocale(this._hass));
    });
  }

  _allGroups() {
    const groups = [...this._localGroups(), ...this._remoteEditorGroups()];
    for (const group of groups) {
      group.rooms = this._ordered(
        group.rooms,
        this._config?.room_order?.[group.id],
        (room) => room.key
      );
    }
    return this._ordered(groups, this._config?.group_order, (group) => group.id);
  }

  _localSignature(hass) {
    if (!hass) return "none";
    const groups = this._localGroups(hass)
      .flatMap((group) => group.rooms.map((room) => `${group.id}:${group.name}:${room.key}:${room.name}`));
    return `${lbLanguage(hass)}|${groups.join("|")}`;
  }

  _remoteStructureSignature() {
    return this._remoteEditorGroups()
      .flatMap((group) => [
        `${group.id}:${group.name}:${group.available}`,
        ...group.rooms.map((room) => `${room.key}:${room.name}`),
      ])
      .join("|");
  }

  _emit(next, rerender = true) {
    this._config = next;
    const event = new Event("config-changed", { bubbles: true, composed: true });
    event.detail = { config: next };
    this.dispatchEvent(event);
    if (rerender) this._requestRender();
  }

  _setHiddenGroup(groupId, hidden) {
    const set = new Set(Array.isArray(this._config.hidden_groups) ? this._config.hidden_groups : []);
    if (hidden) set.add(groupId); else set.delete(groupId);
    const next = { ...this._config };
    if (set.size) next.hidden_groups = [...set]; else delete next.hidden_groups;
    this._emit(next);
  }

  _setRemoteRoomHidden(groupId, roomKey, hidden) {
    const all = this._config.hidden_rooms && typeof this._config.hidden_rooms === "object"
      ? { ...this._config.hidden_rooms }
      : {};
    const set = new Set(Array.isArray(all[groupId]) ? all[groupId] : []);
    if (hidden) set.add(roomKey); else set.delete(roomKey);
    if (set.size) all[groupId] = [...set]; else delete all[groupId];
    const next = { ...this._config };
    if (Object.keys(all).length) next.hidden_rooms = all; else delete next.hidden_rooms;
    this._emit(next);
  }

  _setLocalRoomSelected(entityId, selected) {
    // Migrate the old `entities:` allow-list to the same exclusion model used
    // by remote rooms. That way newly-created local rooms are visible by
    // default even after the user has hidden a different room before.
    const localGroups = this._localGroups();
    const explicit = Array.isArray(this._config.entities) ? new Set(this._config.entities) : null;
    const hiddenRooms = this._config.hidden_rooms && typeof this._config.hidden_rooms === "object"
      ? { ...this._config.hidden_rooms }
      : {};

    for (const group of localGroups) {
      const currentHidden = new Set(Array.isArray(hiddenRooms[group.id]) ? hiddenRooms[group.id] : []);
      for (const room of group.rooms) {
        const currentlySelected = (!explicit || explicit.has(room.entityId)) && !currentHidden.has(room.entityId);
        const shouldSelect = room.entityId === entityId ? selected : currentlySelected;
        if (shouldSelect) currentHidden.delete(room.entityId);
        else currentHidden.add(room.entityId);
      }
      if (currentHidden.size) hiddenRooms[group.id] = [...currentHidden];
      else delete hiddenRooms[group.id];
    }

    const next = { ...this._config };
    delete next.entities;
    if (Object.keys(hiddenRooms).length) next.hidden_rooms = hiddenRooms;
    else delete next.hidden_rooms;
    this._emit(next);
  }

  _moveGroup(groupId, delta) {
    const ids = this._allGroups().map((group) => group.id);
    const index = ids.indexOf(groupId);
    const target = index + delta;
    if (index < 0 || target < 0 || target >= ids.length) return;
    [ids[index], ids[target]] = [ids[target], ids[index]];
    this._emit({ ...this._config, group_order: ids });
  }

  _moveRoom(groupId, roomKey, delta) {
    const group = this._allGroups().find((item) => item.id === groupId);
    if (!group) return;
    const ids = group.rooms.map((room) => room.key);
    const index = ids.indexOf(roomKey);
    const target = index + delta;
    if (index < 0 || target < 0 || target >= ids.length) return;
    [ids[index], ids[target]] = [ids[target], ids[index]];
    const roomOrder = this._config.room_order && typeof this._config.room_order === "object"
      ? { ...this._config.room_order }
      : {};
    roomOrder[groupId] = ids;
    this._emit({ ...this._config, room_order: roomOrder });
  }

  _render() {
    if (!this.shadowRoot || !this._config) return;
    const groups = this._allGroups();
    const hiddenGroups = new Set(Array.isArray(this._config.hidden_groups) ? this._config.hidden_groups : []);
    const explicitLocal = Array.isArray(this._config.entities) ? new Set(this._config.entities) : null;
    const hiddenRooms = this._config.hidden_rooms && typeof this._config.hidden_rooms === "object" ? this._config.hidden_rooms : {};

    this.shadowRoot.innerHTML = `
      <style>
        .editor { display: grid; gap: 14px; padding: 8px 0 16px; }
        .title { display: grid; gap: 6px; color: var(--primary-text-color); font-size: 14px; font-weight: 600; }
        input[type="text"] { box-sizing: border-box; width: 100%; min-height: 44px; padding: 8px 10px; border: 1px solid var(--divider-color); border-radius: 8px; background: var(--ha-color-form-background, var(--card-background-color)); color: var(--primary-text-color); font: inherit; }
        .groups { display: grid; gap: 10px; }
        .group { border: 1px solid var(--divider-color); border-radius: 10px; overflow: hidden; background: color-mix(in srgb, var(--card-background-color) 96%, var(--primary-text-color) 4%); }
        .group-head { display: grid; grid-template-columns: auto minmax(0,1fr) auto; gap: 9px; align-items: center; min-height: 44px; padding: 7px 8px; }
        .group-copy, .room-copy { display: grid; gap: 1px; min-width: 0; }
        .group-copy strong, .room-copy span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .group-copy small, .room-copy small { color: var(--secondary-text-color); font-size: 11px; }
        .room-list { border-top: 1px solid var(--divider-color); }
        .room { display: grid; grid-template-columns: auto minmax(0,1fr) auto; gap: 9px; align-items: center; min-height: 39px; padding: 5px 8px 5px 28px; border-top: 1px solid color-mix(in srgb, var(--divider-color) 65%, transparent); color: var(--primary-text-color); font-size: 13px; }
        .room:first-child { border-top: 0; }
        .order { display: inline-flex; gap: 2px; }
        .order button { appearance: none; border: 0; border-radius: 6px; width: 31px; height: 31px; display: grid; place-items: center; background: transparent; color: var(--secondary-text-color); cursor: pointer; }
        .order button:not(:disabled):hover, .order button:not(:disabled):focus-visible { background: color-mix(in srgb, var(--primary-text-color) 8%, transparent); color: var(--primary-text-color); outline: none; }
        .order button:disabled { opacity: .25; cursor: default; }
        .order ha-icon { --mdc-icon-size: 19px; }
        .hint { color: var(--secondary-text-color); font-size: 12px; line-height: 1.4; }
      </style>
      <div class="editor">
        <label class="title">${lbT(this._hass, "editor.title")}<input id="title" type="text" value="${this._escape(this._config.title || "")}" /></label>
        <div class="groups">
          <strong>${lbT(this._hass, "editor.installations")}</strong>
          ${groups.map((group, groupIndex) => {
            const groupChecked = !hiddenGroups.has(group.id);
            const groupType = group.remote ? lbT(this._hass, "editor.remote") : lbT(this._hass, "editor.local");
            const reachability = group.remote && !group.available ? ` · ${lbT(this._hass, "editor.unavailable")}` : "";
            return `<div class="group">
              <div class="group-head">
                <input type="checkbox" data-group-toggle="${this._escape(group.id)}" ${groupChecked ? "checked" : ""}/>
                <span class="group-copy"><strong>${this._escape(group.name)}</strong><small>${this._escape(groupType + reachability)}</small></span>
                <span class="order">
                  <button type="button" data-group-move="${this._escape(group.id)}" data-delta="-1" title="${this._escape(lbT(this._hass, "editor.move_up"))}" ${groupIndex === 0 ? "disabled" : ""}><ha-icon icon="mdi:chevron-up"></ha-icon></button>
                  <button type="button" data-group-move="${this._escape(group.id)}" data-delta="1" title="${this._escape(lbT(this._hass, "editor.move_down"))}" ${groupIndex === groups.length - 1 ? "disabled" : ""}><ha-icon icon="mdi:chevron-down"></ha-icon></button>
                </span>
              </div>
              ${group.rooms.length ? `<div class="room-list">${group.rooms.map((room, roomIndex) => {
                const roomHidden = Array.isArray(hiddenRooms[group.id]) && hiddenRooms[group.id].includes(room.key);
                const checked = room.remote
                  ? !roomHidden
                  : (explicitLocal ? explicitLocal.has(room.entityId) : true) && !roomHidden;
                return `<label class="room">
                  <input type="checkbox" ${room.remote ? `data-remote-room="${this._escape(room.key)}" data-room-group="${this._escape(group.id)}"` : `data-local-entity="${this._escape(room.entityId)}"`} ${checked ? "checked" : ""}/>
                  <span class="room-copy"><span>${this._escape(room.name)}</span></span>
                  <span class="order">
                    <button type="button" data-room-move="${this._escape(room.key)}" data-room-group="${this._escape(group.id)}" data-delta="-1" title="${this._escape(lbT(this._hass, "editor.move_up"))}" ${roomIndex === 0 ? "disabled" : ""}><ha-icon icon="mdi:chevron-up"></ha-icon></button>
                    <button type="button" data-room-move="${this._escape(room.key)}" data-room-group="${this._escape(group.id)}" data-delta="1" title="${this._escape(lbT(this._hass, "editor.move_down"))}" ${roomIndex === group.rooms.length - 1 ? "disabled" : ""}><ha-icon icon="mdi:chevron-down"></ha-icon></button>
                  </span>
                </label>`;
              }).join("")}</div>` : ""}
            </div>`;
          }).join("") || `<span class="hint">${lbT(this._hass, "overview.empty_title")}</span>`}
        </div>
        <div class="hint">${lbT(this._hass, "editor.rooms_hint")}</div>
      </div>`;

    this.shadowRoot.querySelector("#title")?.addEventListener("change", (event) => {
      const next = { ...this._config };
      const value = event.target.value.trim();
      if (value) next.title = value; else delete next.title;
      this._emit(next, false);
    });

    this.shadowRoot.querySelectorAll("[data-group-toggle]").forEach((checkbox) => {
      checkbox.addEventListener("change", () => this._setHiddenGroup(checkbox.dataset.groupToggle, !checkbox.checked));
    });
    this.shadowRoot.querySelectorAll("[data-local-entity]").forEach((checkbox) => {
      checkbox.addEventListener("change", () => this._setLocalRoomSelected(checkbox.dataset.localEntity, checkbox.checked));
    });
    this.shadowRoot.querySelectorAll("[data-remote-room]").forEach((checkbox) => {
      checkbox.addEventListener("change", () => this._setRemoteRoomHidden(checkbox.dataset.roomGroup, checkbox.dataset.remoteRoom, !checkbox.checked));
    });
    this.shadowRoot.querySelectorAll("[data-group-move]").forEach((button) => {
      button.addEventListener("click", () => this._moveGroup(button.dataset.groupMove, Number(button.dataset.delta)));
    });
    this.shadowRoot.querySelectorAll("[data-room-move]").forEach((button) => {
      button.addEventListener("click", () => this._moveRoom(button.dataset.roomGroup, button.dataset.roomMove, Number(button.dataset.delta)));
    });
  }
}

if (!customElements.get("lueftungsberater-overview-card-editor")) {
  customElements.define("lueftungsberater-overview-card-editor", LueftungsberaterOverviewCardEditor);
}
