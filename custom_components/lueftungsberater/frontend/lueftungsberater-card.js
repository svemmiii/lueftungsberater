const LB_NNBSP = "\u202F";

const LB_I18N = {
  de: {
    "recommendation.open_now": "Jetzt lüften",
    "recommendation.room_good": "Aktuell kein Lüftungsgrund",
    "recommendation.room_watch": "Werte im Blick behalten",
    "recommendation.room_need": "Lüften ist sinnvoll",
    "recommendation.room_urgent": "Jetzt lüften",
    "recommendation.room_keep_brief": "Noch kurz weiterlüften",
    "recommendation.keep_open": "Weiter lüften",
    "recommendation.can_close": "Lüften kann beendet werden",
    "recommendation.short_observation": "Nur kurz lüften und die Situation im Blick behalten",
    "recommendation.better_close": "Besser wieder schließen",
    "recommendation.caution_keep_closed": "Vorsicht – lieber geschlossen lassen",
    "recommendation.keep_closed": "Geschlossen lassen",
    "recommendation.close_now": "Jetzt schließen",
    "recommendation.wait": "Besser noch etwas warten",
    "recommendation.optional": "Lüften ist aktuell optional",
    "recommendation.unknown": "Aktuell keine zuverlässige Empfehlung möglich",
    "recommendation.window_state_unknown": "Fensterzustand derzeit nicht verfügbar – bitte prüfen",
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
    "setup.description": "Wähle im visuellen Editor einen Lüftungsassistent-Raum aus.",
    "entity_missing": "Raum {entity} nicht gefunden. Prüfe die Raumauswahl im Karteneditor.",
    "window.open_since": "Fenster/Tür gerade offen · seit {duration}",
    "window.open": "Fenster/Tür gerade offen",
    "window.minute": "Minute",
    "window.minutes": "Minuten",
    "window.hour": "Stunde",
    "window.hours": "Stunden",
    "window.and": "und",
    "airing.open": "Lüftungsdetails öffnen",
    "airing.last": "Letzte bestätigte Lüftung: vor {hours} h",
    "airing.history": "Lüftungsverlauf öffnen",
    "airing.none": "Noch keine bestätigte Lüftung erfasst",
    "metric.inside": "{value} innen",
    "metric.outside": "{value} außen",
    "metric.target": "{value} Soll",
    "metric.temperature": "Temperatur",
    "metric.humidity": "Luftfeuchte",
    "metric.air_quality": "Luftqualität",
    "metric.pm25": "PM2,5",
    "metric.pm10": "PM10",
    "metric.voc": "VOC",
    "metric.no2": "NO₂ / NOx",
    "metric.o3": "Ozon",
    "metric.index_value": "Index {value}",
    "metric.formaldehyde": "Formaldehyd",
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
    "forecast.stale": "Wetterprognose veraltet · Nacht-/Kurzzeitprognose wird nicht verwendet",
    "forecast.unavailable": "Wetterprognose nicht verfügbar",
    "warning.open": "Warn-/Quelldaten öffnen",
    "why": "Warum diese Empfehlung?",
    "details.show": "Details anzeigen",
    "details.hide": "Details ausblenden",
    "night.title": "Nachtlüften",
    "duration": "⏱️ Empfohlene Lüftungsdauer:",
    "hint": "Messwerte antippen für Verlauf · farbigen Statusbereich antippen für Details",
    "picker.room.name": "Lüftungsassistent – Raum",
    "picker.room.description": "Detaillierte Lüftungsempfehlung für einen einzelnen Raum.",
    "overview.invalid_entities": "entities muss eine Liste von Entity-IDs sein.",
    "overview.open": "offen",
    "overview.remote_used": "wird remote abgefragt",
    "overview.remote_rooms": "{count} Raum/Räume werden von einer anderen Instanz abgefragt",
    "warning.info": "Amtlicher Hinweis",
    "warning.all_clear": "Entwarnung eingegangen",
    "remote.active": "Wird remote abgefragt",
    "remote.active_by": "Wird remote abgefragt von {clients}",
    "overview.not_reachable": "Nicht erreichbar",
    "overview.empty_title": "Keine Lüftungsassistent-Räume gefunden.",
    "overview.empty_description": "Räume werden automatisch erkannt oder können per entities: angegeben werden.",
    "overview.no_remote_rooms": "Keine Räume verfügbar",
    "overview.room": "Raum",
    "overview.rooms": "Räume",
    "overview.back": "Zurück",
    "overview.close": "Schließen",
    "picker.overview.name": "Lüftungsassistent – Übersicht",
    "picker.overview.description": "Kompakte Übersicht über lokale und entfernte Lüftungsassistenten.",
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
    "editor.layout": "Anordnung",
    "editor.classic": "Klassisch",
    "editor.split": "Innen | Außen",
    "editor.general": "Allgemein",
    "editor.inside": "Innen",
    "editor.outside": "Außen",
    "editor.fields": "Messwerte auf der Karte",
    "editor.reason": "„Warum diese Empfehlung?“ anzeigen",
    "editor.density": "Darstellung",
    "editor.compact": "Kompakt",
    "editor.normal": "Normal",
    "editor.detailed": "Ausführlich",
    "editor.reset": "Kartenanzeige zurücksetzen",
    "editor.reset_confirm": "Nur die Anzeige dieser Karte zurücksetzen? Sensoren und Einstellungen der Integration bleiben erhalten.",
    "editor.drag": "Ziehen zum Sortieren",
    "editor.labels": "Name (optional)",
    "editor.icon": "Symbol (optional)",
    "editor.empty_fields": "Für diesen Bereich sind keine Messwerte eingerichtet.",
    "metric.unavailable": "Nicht verfügbar",
    "metric.not_assessable": "Nicht bewertbar",
    "remote.offline": "Verbindung unterbrochen",
    "remote.stale_notice": "Letzte bekannte Messwerte. Keine aktuelle Lüftungsempfehlung verfügbar.",
    "airing.today": "Heute, {time}",
    "airing.yesterday": "Gestern, {time}",
    "airing.day_before": "Vorgestern, {time}",
    "metric.last_airing": "Zuletzt gelüftet",
    "metric.target_temperature": "Solltemperatur",
    "metric.humidity_delta": "Feuchtedifferenz",
    "metric.window_state": "Fenster",
    "metric.relative_humidity": "Relative Feuchte",
    "metric.absolute_humidity": "Absolute Feuchte",
    "metric.co2": "CO₂",
    "metric.surface_temp": "Oberflächentemperatur",
    "metric.surface_humidity": "Oberflächenfeuchte",
    "metric.mold_risk": "Schimmelrisiko",
    "metric.wind": "Wind",
    "metric.gust": "Böen",
    "metric.rain": "Regen",
    "metric.yes": "Erhöht",
    "metric.no": "Unauffällig",
    "entity_missing": "Raum {entity} nicht gefunden. Prüfe die Raumauswahl im Karteneditor.",
    "night.times": "{start}–{end}",
    "night.sleep": "Nicht über Nacht offen lassen. Falls nötig, vor dem Schlafengehen kurz lüften.",
    "editor.rooms_hint": "Installationen und Räume können einzeln ein- oder ausgeblendet und mit den Pfeilen sortiert werden. Neue lokale Räume werden automatisch erkannt; neue Remote-Räume werden erst nach Auswahl in der Remote-Verbindung übernommen."
  },
  en: {
    "recommendation.open_now": "Open the windows now",
    "recommendation.room_good": "No current reason to ventilate",
    "recommendation.room_watch": "Keep an eye on the values",
    "recommendation.room_need": "Ventilation is worthwhile",
    "recommendation.room_urgent": "Ventilate now",
    "recommendation.room_keep_brief": "Keep ventilating briefly",
    "recommendation.keep_open": "Keep the windows open a little longer",
    "recommendation.can_close": "You can close the windows now",
    "recommendation.short_observation": "Open the windows briefly and keep an eye on it",
    "recommendation.better_close": "Better close the windows",
    "recommendation.caution_keep_closed": "Better keep the windows closed for now",
    "recommendation.keep_closed": "Keep the windows closed",
    "recommendation.close_now": "Close the windows now",
    "recommendation.wait": "Better wait a little longer",
    "recommendation.optional": "Ventilation is optional",
    "recommendation.unknown": "No reliable recommendation is available right now",
    "recommendation.window_state_unknown": "Window status is currently unavailable — please check",
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
    "setup.description": "Choose a Fresh Air Assistant room in the visual editor.",
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
    "metric.air_quality": "Air quality",
    "metric.pm25": "PM2.5",
    "metric.pm10": "PM10",
    "metric.voc": "VOC",
    "metric.no2": "NO₂ / NOx",
    "metric.o3": "Ozone",
    "metric.index_value": "Index {value}",
    "metric.formaldehyde": "Formaldehyde",
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
    "forecast.stale": "Weather forecast is stale · night/short-term forecast is not being used",
    "forecast.unavailable": "Weather forecast unavailable",
    "warning.open": "Open warning / source data",
    "why": "Why this recommendation?",
    "details.show": "Show details",
    "details.hide": "Hide details",
    "night.title": "Night ventilation",
    "duration": "⏱️ Recommended window-opening time:",
    "hint": "Tap a value for its history · tap the colored status area for details",
    "picker.room.name": "Fresh Air Assistant – Room",
    "picker.room.description": "Detailed ventilation recommendation for a single room.",
    "overview.invalid_entities": "entities must be a list of entity IDs.",
    "overview.open": "open",
    "overview.remote_used": "queried remotely",
    "overview.remote_rooms": "{count} room(s) are being queried by another instance",
    "warning.info": "Official notice",
    "warning.all_clear": "All-clear received",
    "remote.active": "Queried remotely",
    "remote.active_by": "Queried remotely by {clients}",
    "overview.not_reachable": "Not reachable",
    "overview.empty_title": "No Fresh Air Assistant rooms found.",
    "overview.empty_description": "Rooms are discovered automatically or can be specified with entities:.",
    "overview.no_remote_rooms": "No rooms available",
    "overview.room": "room",
    "overview.rooms": "rooms",
    "overview.back": "Back",
    "overview.close": "Close",
    "picker.overview.name": "Fresh Air Assistant – Overview",
    "picker.overview.description": "Compact overview of local and remote Fresh Air Assistant installations.",
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
    "editor.layout": "Layout",
    "editor.classic": "Classic",
    "editor.split": "Indoor | Outdoor",
    "editor.general": "General",
    "editor.inside": "Indoor",
    "editor.outside": "Outdoor",
    "editor.fields": "Measurements on the card",
    "editor.reason": "Show “Why this recommendation?”",
    "editor.density": "Display",
    "editor.compact": "Compact",
    "editor.normal": "Normal",
    "editor.detailed": "Detailed",
    "editor.reset": "Reset card display",
    "editor.reset_confirm": "Reset only this card’s display? Sensors and integration settings will stay unchanged.",
    "editor.drag": "Drag to reorder",
    "editor.labels": "Label (optional)",
    "editor.icon": "Icon (optional)",
    "editor.empty_fields": "No measurements set up for this section.",
    "metric.unavailable": "Unavailable",
    "metric.not_assessable": "Cannot be assessed",
    "remote.offline": "Connection lost",
    "remote.stale_notice": "Last known readings. No current ventilation advice is available.",
    "airing.today": "Today, {time}",
    "airing.yesterday": "Yesterday, {time}",
    "airing.day_before": "The day before yesterday, {time}",
    "metric.last_airing": "Last aired",
    "metric.target_temperature": "Target temperature",
    "metric.humidity_delta": "Humidity difference",
    "metric.window_state": "Window",
    "metric.relative_humidity": "Relative humidity",
    "metric.absolute_humidity": "Absolute humidity",
    "metric.co2": "CO₂",
    "metric.surface_temp": "Surface temperature",
    "metric.surface_humidity": "Surface humidity",
    "metric.mold_risk": "Mold risk",
    "metric.wind": "Wind",
    "metric.gust": "Wind gusts",
    "metric.rain": "Rain",
    "metric.yes": "Elevated",
    "metric.no": "Normal",
    "entity_missing": "Room {entity} not found. Check the room selection in the card editor.",
    "night.times": "{start}–{end}",
    "night.sleep": "Do not leave the window open overnight. Air the room briefly before bed if needed.",
    "editor.rooms_hint": "Installations and rooms can be shown or hidden individually and reordered with the arrow buttons. New local rooms are discovered automatically; new remote rooms appear only after they are selected in the remote connection."
  },
  tr: {
    "recommendation.open_now": "Şimdi pencereleri aç",
    "recommendation.room_good": "Şu anda havalandırma nedeni yok",
    "recommendation.room_watch": "Değerleri takip et",
    "recommendation.room_need": "Havalandırmak faydalı",
    "recommendation.room_urgent": "Şimdi havalandır",
    "recommendation.room_keep_brief": "Kısa süre daha havalandır",
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
    "recommendation.window_state_unknown": "Pencere durumu şu anda kullanılamıyor — lütfen kontrol et",
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
    "setup.description": "Görsel düzenleyiciden bir Fresh Air Assistant odası seç.",
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
    "metric.air_quality": "Hava kalitesi",
    "metric.pm25": "PM2.5",
    "metric.pm10": "PM10",
    "metric.voc": "VOC",
    "metric.no2": "NO₂ / NOx",
    "metric.o3": "Ozon",
    "metric.index_value": "İndeks {value}",
    "metric.formaldehyde": "Formaldehit",
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
    "forecast.stale": "Hava tahmini eski · gece/kısa vadeli tahmin kullanılmıyor",
    "forecast.unavailable": "Hava tahmini kullanılamıyor",
    "warning.open": "Uyarı / kaynak verisini aç",
    "why": "Bu önerinin nedeni ne?",
    "details.show": "Ayrıntıları göster",
    "details.hide": "Ayrıntıları gizle",
    "night.title": "Gece havalandırması",
    "duration": "⏱️ Önerilen pencere açık kalma süresi:",
    "hint": "Geçmiş için bir değere dokun · ayrıntılar için renkli durum alanına dokun",
    "picker.room.name": "Fresh Air Assistant – Oda",
    "picker.room.description": "Tek bir oda için ayrıntılı havalandırma önerisi.",
    "overview.invalid_entities": "entities bir entity ID listesi olmalıdır.",
    "overview.open": "açık",
    "overview.remote_used": "uzaktan sorgulanıyor",
    "overview.remote_rooms": "{count} oda başka bir örnek tarafından uzaktan sorgulanıyor",
    "warning.info": "Resmî bilgilendirme",
    "warning.all_clear": "Tehlikenin geçtiğine dair bildirim geldi",
    "remote.active": "Uzaktan sorgulanıyor",
    "remote.active_by": "{clients} tarafından uzaktan sorgulanıyor",
    "overview.not_reachable": "Ulaşılamıyor",
    "overview.empty_title": "Fresh Air Assistant odası bulunamadı.",
    "overview.empty_description": "Odalar otomatik bulunur veya entities: ile belirtilebilir.",
    "overview.no_remote_rooms": "Kullanılabilir oda yok",
    "overview.room": "oda",
    "overview.rooms": "oda",
    "overview.back": "Geri",
    "overview.close": "Kapat",
    "picker.overview.name": "Fresh Air Assistant – Genel Bakış",
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
    "editor.layout": "Düzen",
    "editor.classic": "Klasik",
    "editor.split": "İç | Dış",
    "editor.general": "Genel",
    "editor.inside": "İçerisi",
    "editor.outside": "Dışarısı",
    "editor.fields": "Kartta gösterilen ölçümler",
    "editor.reason": "“Bu öneri neden verildi?” göster",
    "editor.density": "Görünüm",
    "editor.compact": "Kompakt",
    "editor.normal": "Normal",
    "editor.detailed": "Ayrıntılı",
    "editor.reset": "Kart görünümünü sıfırla",
    "editor.reset_confirm": "Yalnızca bu kartın görünümünü sıfırlamak istiyor musun? Sensörler ve entegrasyon ayarları değişmez.",
    "editor.drag": "Sıralamak için sürükle",
    "editor.labels": "Başlık (isteğe bağlı)",
    "editor.icon": "Simge (isteğe bağlı)",
    "editor.empty_fields": "Bu bölümde tanımlı ölçüm yok.",
    "metric.unavailable": "Kullanılamıyor",
    "metric.not_assessable": "Değerlendirilemiyor",
    "remote.offline": "Bağlantı kesildi",
    "remote.stale_notice": "Son ölçümler gösteriliyor. Güncel havalandırma önerisi yok.",
    "airing.today": "Bugün, {time}",
    "airing.yesterday": "Dün, {time}",
    "airing.day_before": "Evvelsi gün, {time}",
    "metric.last_airing": "Son havalandırma",
    "metric.target_temperature": "Hedef sıcaklık",
    "metric.humidity_delta": "Nem farkı",
    "metric.window_state": "Pencere",
    "metric.relative_humidity": "Bağıl nem",
    "metric.absolute_humidity": "Mutlak nem",
    "metric.co2": "CO₂",
    "metric.surface_temp": "Yüzey sıcaklığı",
    "metric.surface_humidity": "Yüzey nemi",
    "metric.mold_risk": "Küf riski",
    "metric.wind": "Rüzgâr",
    "metric.gust": "Rüzgâr hamlesi",
    "metric.rain": "Yağmur",
    "metric.yes": "Yüksek",
    "metric.no": "Normal",
    "entity_missing": "{entity} odası bulunamadı. Kart düzenleyicisinden oda seçimini kontrol et.",
    "night.times": "{start}–{end}",
    "night.sleep": "Pencereyi gece boyunca açık bırakma. Gerekirse yatmadan önce kısa süre havalandır.",
    "editor.rooms_hint": "Kurulumlar ve odalar ayrı ayrı gösterilip gizlenebilir ve ok düğmeleriyle sıralanabilir. Yeni yerel odalar otomatik bulunur; yeni uzak odalar yalnızca uzak bağlantıda seçildikten sonra görünür."
  }
};


// View configuration is local to a Lovelace card. It never enters the advisor engine.
const LB_FIELD_INFO = [
  ["last_airing", "general", "mdi:history", false],
  ["target", "general", "mdi:thermostat", false],
  ["humidity_delta", "general", "mdi:water-minus", false],
  ["window_state", "general", "mdi:window-open", false],
  ["temp_in", "inside", "mdi:thermometer", false],
  ["humidity_in", "inside", "mdi:water-percent", false],
  ["absolute_in", "inside", "mdi:water", false],
  ["co2_in", "inside", "mdi:molecule-co2", false],
  ["pm25_in", "inside", "mdi:air-filter", false],
  ["pm10_in", "inside", "mdi:air-filter", false],
  ["voc_in", "inside", "mdi:air-filter", false],
  ["no2_in", "inside", "mdi:air-filter", false],
  ["formaldehyde_in", "inside", "mdi:air-filter", false],
  ["surface_temp", "inside", "mdi:thermometer", true],
  ["surface_humidity", "inside", "mdi:water-percent", true],
  ["mold_risk", "inside", "mdi:alert-circle-outline", true],
  ["temp_out", "outside", "mdi:thermometer", false],
  ["humidity_out", "outside", "mdi:water-percent", false],
  ["absolute_out", "outside", "mdi:water", false],
  ["co2_out", "outside", "mdi:molecule-co2", true],
  ["pm25_out", "outside", "mdi:air-filter", false],
  ["pm10_out", "outside", "mdi:air-filter", false],
  ["voc_out", "outside", "mdi:air-filter", false],
  ["no2_out", "outside", "mdi:air-filter", false],
  ["o3_out", "outside", "mdi:air-filter", false],
  ["wind", "outside", "mdi:weather-windy", true],
  ["gust", "outside", "mdi:weather-windy", true],
  ["rain", "outside", "mdi:weather-rainy", true],
];
function lbHasValue(value) {
  return value !== null && value !== undefined && value !== "" && value !== "unknown" && value !== "unavailable";
}
function lbAirValue(a, side, choices) {
  const obj = side === "inside" ? a.indoor_air_quality_values : a.air_quality_values;
  for (const [key, unit, index] of choices) {
    if (lbHasValue(obj?.[key])) return { value: obj[key], unit, index };
  }
  return null;
}
function lbConfiguredFields(a = {}) {
  // A configured source is still present when its current measurement is offline.
  const present = (attribute, source, extra = false) => lbHasValue(a[attribute]) || Boolean(a[source]) || extra;
  const air = (side, choices, source) => !!a[source] || !!lbAirValue(a, side, choices);
  const enabled = {
    last_airing: a.has_window_contacts === true || !!a.source_last_airing || lbHasValue(a.last_confirmed_airing),
    target: present("target_temperature", "source_target_temperature"),
    humidity_delta: present("absolute_humidity_difference", "source_absolute_humidity_difference"),
    window_state: a.has_window_contacts === true,
    temp_in: present("temperature_inside", "source_temperature_inside"),
    humidity_in: present("humidity_inside", "source_humidity_inside"),
    absolute_in: present("absolute_humidity_inside", "source_absolute_humidity_inside"),
    co2_in: a.has_co2 === true || present("co2_ppm", "source_co2"),
    temp_out: present("temperature_outside", "source_temperature_outside", !!a.weather_provider),
    humidity_out: present("humidity_outside", "source_humidity_outside", !!a.weather_provider),
    absolute_out: present("absolute_humidity_outside", "source_absolute_humidity_outside"),
    co2_out: present("outdoor_co2_ppm", "source_outdoor_co2"),
    surface_temp: present("surface_temperature", "source_surface_temperature"),
    surface_humidity: lbHasValue(a.surface_relative_humidity) || !!a.source_surface_temperature,
    mold_risk: !!a.source_surface_temperature || a.mold_risk === true || a.mold_persistent === true,
    wind: present("wind_speed_kmh", "source_wind_outside"),
    gust: present("wind_gust_kmh", "source_gust_outside"),
    rain: present("rain_minutes_until", "source_rain_outside"),
  };
  const flex = {
    voc: [["voc","µg/m³",false],["voc_parts","ppb",false],["voc_index","",true]],
    no2: [["no2","µg/m³",false],["no2_parts","ppb",false],["no2_index","",true]],
    o3: [["o3","µg/m³",false],["o3_parts","ppb",false]],
    pm25: [["pm2_5","µg/m³",false]],
    pm10: [["pm10","µg/m³",false]],
    formaldehyde: [["formaldehyde","mg/m³",false]],
  };
  for (const [key, choices] of Object.entries(flex)) {
    enabled[`${key}_in`] = air("inside", choices, `source_${key}_inside`);
    enabled[`${key}_out`] = air("outside", choices, `source_${key}_outside`);
  }
  return LB_FIELD_INFO.filter(([key]) => enabled[key]);
}
function lbFieldsInOrder(fields, group, settings) {
  const candidates = fields.filter((f) => f[1] === group);
  const order = settings?.order?.[group] || [];
  return [...candidates].sort((a, b) => {
    const ai = order.indexOf(a[0]), bi = order.indexOf(b[0]);
    return (ai < 0 ? 999 : ai) - (bi < 0 ? 999 : bi);
  });
}
function lbFieldVisible(field, settings) {
  return !settings?.hidden?.includes(field[0]) && (!field[3] || settings?.extra?.includes(field[0]));
}
function lbDisplaySettings(config) {
  return config?.display_settings && typeof config.display_settings === "object" ? config.display_settings : {};
}


function lbFieldLabel(hass, id) {
  const names = {
    last_airing: "metric.last_airing", target: "metric.target_temperature", humidity_delta: "metric.humidity_delta", window_state: "metric.window_state",
    temp_in: "metric.temperature", temp_out: "metric.temperature",
    humidity_in: "metric.relative_humidity", humidity_out: "metric.relative_humidity",
    absolute_in: "metric.absolute_humidity", absolute_out: "metric.absolute_humidity",
    co2_in: "metric.co2", co2_out: "metric.co2", pm25_in: "metric.pm25", pm25_out: "metric.pm25",
    pm10_in: "metric.pm10", pm10_out: "metric.pm10", voc_in: "metric.voc", voc_out: "metric.voc",
    no2_in: "metric.no2", no2_out: "metric.no2", o3_out: "metric.o3", formaldehyde_in: "metric.formaldehyde",
    surface_temp: "metric.surface_temp", surface_humidity: "metric.surface_humidity", mold_risk: "metric.mold_risk",
    wind: "metric.wind", gust: "metric.gust", rain: "metric.rain",
  };
  return lbT(hass, names[id] || id);
}


// Shared editor controls: individual cards and the overview's popup rooms.
function lbViewEditorHtml(hass, config, available, esc) {
  const settings = lbDisplaySettings(config);
  const layout = settings.layout === "split" ? "split" : "classic";
  const density = ["compact","normal","detailed"].includes(settings.density) ? settings.density : "normal";
  const sideOrder = settings.sides?.join(",") === "outside,inside" ? ["outside","inside"] : ["inside","outside"];
  const orderedGroups = ["general", ...sideOrder];
  const options = (group) => lbFieldsInOrder(available, group, settings);
  const item = (field) => {
    const [id, , icon, extra] = field;
    const shown = lbFieldVisible(field, settings);
    const safe = esc(id);
    return `<div class="lb-editor-item" draggable="true" data-lb-drag-metric="${safe}">
      <span class="lb-grip" title="${esc(lbT(hass,"editor.drag"))}" aria-hidden="true">⠿</span>
      <label class="lb-item-visible"><input type="checkbox" data-lb-visible="${safe}" ${shown ? "checked" : ""} />${esc(lbFieldLabel(hass,id))}</label>
      <div class="lb-item-options">
        <input type="text" data-lb-label="${safe}" placeholder="${esc(lbT(hass,"editor.labels"))}" aria-label="${esc(lbT(hass,"editor.labels"))}" value="${esc(settings.labels?.[id] || "")}" />
        <input type="text" data-lb-icon="${safe}" placeholder="mdi:${esc(icon.slice(4))}" aria-label="${esc(lbT(hass,"editor.icon"))}" value="${esc(settings.icons?.[id] || "")}" />
      </div>
    </div>`;
  };
  return `<section class="lb-editor-display">
    <h3>${lbT(hass,"editor.fields")}</h3>
    <label>${lbT(hass,"editor.layout")}<select data-lb-layout>
      <option value="classic" ${layout==="classic"?"selected":""}>${lbT(hass,"editor.classic")}</option>
      <option value="split" ${layout==="split"?"selected":""}>${lbT(hass,"editor.split")}</option>
    </select></label>
    <label>${lbT(hass,"editor.density")}<select data-lb-density>
      ${["compact","normal","detailed"].map(v=>`<option value="${v}" ${density===v?"selected":""}>${lbT(hass,"editor."+v)}</option>`).join("")}
    </select></label>
    <label class="lb-show-reason"><input type="checkbox" data-lb-reason ${settings.show_reason===false?"":"checked"} />${lbT(hass,"editor.reason")}</label>
    ${orderedGroups.map(group=>`<div class="lb-editor-group" data-lb-group="${group}" ${group!=="general"?'draggable="true"':""}>
      <h4>${group==="general"?"":'<span class="lb-grip" aria-hidden="true">⠿</span>'}${lbT(hass,"editor."+group)}</h4>
      <div class="lb-editor-fields" data-lb-fields="${group}">${options(group).map(item).join("") || `<span class="lb-editor-empty">${lbT(hass,"editor.empty_fields")}</span>`}</div>
    </div>`).join("")}
    <button type="button" class="lb-reset" data-lb-reset>${lbT(hass,"editor.reset")}</button>
  </section>`;
}
function lbBindViewEditor(root, hass, config, available, update) {
  if (!root) return;
  const get = () => JSON.parse(JSON.stringify(lbDisplaySettings(config)));
  const change = (modify) => { const next = get(); modify(next); update(next); };
  root.querySelector("[data-lb-layout]")?.addEventListener("change",e=>change(o=>{o.layout=e.target.value;}));
  root.querySelector("[data-lb-density]")?.addEventListener("change",e=>change(o=>{o.density=e.target.value;}));
  root.querySelector("[data-lb-reason]")?.addEventListener("change",e=>change(o=>{o.show_reason=e.target.checked;}));
  root.querySelectorAll("[data-lb-visible]").forEach(el=>el.addEventListener("change",()=>{
    const id=el.dataset.lbVisible;
    change(o=>{
      const f=LB_FIELD_INFO.find(x=>x[0]===id);
      o.hidden=Array.isArray(o.hidden)?o.hidden.filter(x=>x!==id):[];
      o.extra=Array.isArray(o.extra)?o.extra.filter(x=>x!==id):[];
      if(el.checked && f?.[3]) o.extra.push(id);
      if(!el.checked && !f?.[3]) o.hidden.push(id);
    });
  }));
  root.querySelectorAll("[data-lb-label]").forEach(el=>el.addEventListener("change",()=>change(o=>{
    o.labels={...(o.labels||{})}; const value=el.value.trim().slice(0,50);
    if(value) o.labels[el.dataset.lbLabel]=value; else delete o.labels[el.dataset.lbLabel];
  })));
  root.querySelectorAll("[data-lb-icon]").forEach(el=>el.addEventListener("change",()=>change(o=>{
    o.icons={...(o.icons||{})};const value=el.value.trim();
    if(/^mdi:[a-z0-9-]+$/.test(value)) o.icons[el.dataset.lbIcon]=value;
    else delete o.icons[el.dataset.lbIcon];
  })));
  let drag=null;
  root.querySelectorAll("[data-lb-drag-metric]").forEach(el=>{
    el.addEventListener("dragstart", e=>{drag={type:"field",id:el.dataset.lbDragMetric};e.dataTransfer.effectAllowed="move";});
    el.addEventListener("dragover", e=>{if(drag?.type==="field")e.preventDefault();});
    el.addEventListener("drop",e=>{
      if(!drag || drag.type!=="field")return;
      const target=el.dataset.lbDragMetric;
      const source=drag.id;
      const gf=LB_FIELD_INFO.find(f=>f[0]===source), gt=LB_FIELD_INFO.find(f=>f[0]===target);
      if(!gf||!gt||gf[1]!==gt[1]||source===target)return;
      e.preventDefault();
      change(o=>{
        o.order={...(o.order||{})};
        const order=lbFieldsInOrder(available,gf[1],o).map(f=>f[0]).filter(id=>id!==source);
        order.splice(order.indexOf(target),0,source);
        o.order[gf[1]]=order;
      });
      drag=null;
    });
  });
  root.querySelectorAll('[data-lb-group="inside"],[data-lb-group="outside"]').forEach(el=>{
    el.addEventListener("dragstart",e=>{
      if(e.target.closest?.("[data-lb-drag-metric]"))return;
      drag={type:"group",id:el.dataset.lbGroup};e.dataTransfer.effectAllowed="move";
    });
    el.addEventListener("dragover",e=>{if(drag?.type==="group")e.preventDefault();});
    el.addEventListener("drop",e=>{
      if(drag?.type!=="group"||drag.id===el.dataset.lbGroup)return;
      e.preventDefault();change(o=>{o.sides=[el.dataset.lbGroup,drag.id];});drag=null;
    });
  });
  root.querySelector("[data-lb-reset]")?.addEventListener("click",()=>{
    if(window.confirm(lbT(hass,"editor.reset_confirm"))) update(null);
  });
}

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

const LB_TEXT_CACHE_MAX_ENTRIES = 256;
const LB_TEXT_CACHE = new Map();
const LB_TEXT_PENDING = new Map();
const LB_TEXT_RETRY = new Map();
const LB_TEXT_RETRY_MAX_ATTEMPTS = 6;

function lbTextCacheGet(key) {
  const value = LB_TEXT_CACHE.get(key);
  if (value === undefined) return null;
  // Refresh insertion order so the bounded Map behaves as a small LRU cache.
  LB_TEXT_CACHE.delete(key);
  LB_TEXT_CACHE.set(key, value);
  return value;
}

function lbTextCacheSet(key, value) {
  if (LB_TEXT_CACHE.has(key)) LB_TEXT_CACHE.delete(key);
  LB_TEXT_CACHE.set(key, value);
  while (LB_TEXT_CACHE.size > LB_TEXT_CACHE_MAX_ENTRIES) {
    const oldestKey = LB_TEXT_CACHE.keys().next().value;
    if (oldestKey === undefined) break;
    LB_TEXT_CACHE.delete(oldestKey);
  }
}

function lbScheduleTextRetry(key, callbacks) {
  let retry = LB_TEXT_RETRY.get(key);
  if (!retry) {
    retry = { attempts: 0, callbacks: new Set(), timer: null };
    LB_TEXT_RETRY.set(key, retry);
  }
  for (const callback of callbacks || []) {
    if (typeof callback === "function") retry.callbacks.add(callback);
  }
  if (retry.timer) return;
  if (retry.attempts >= LB_TEXT_RETRY_MAX_ATTEMPTS) {
    // Keep the backend fallback text after a bounded retry sequence. Any later
    // normal card render may start a fresh request, but a disconnected/static
    // card cannot keep itself alive forever through retry timers.
    LB_TEXT_RETRY.delete(key);
    return;
  }

  retry.attempts += 1;
  const delay = Math.min(30000, 1000 * (2 ** Math.min(retry.attempts - 1, 5)));
  retry.timer = setTimeout(() => {
    retry.timer = null;
    const waiting = [...retry.callbacks];
    retry.callbacks.clear();
    for (const callback of waiting) {
      try { callback(); } catch (_err) { /* one card must not block peers */ }
    }
  }, delay);
}

function lbTextCacheKey(hass, attributes) {
  return JSON.stringify([
    lbLanguage(hass),
    attributes?.temperature_display_unit || "°C",
    attributes?.recommendation_key || "unknown",
    attributes?.reason_key || "incomplete_data",
    attributes?.reason_args || {},
    attributes?.duration_key || "incomplete_data",
    attributes?.night_ventilation_key || null,
    attributes?.night_ventilation_args || {},
  ]);
}

function lbLocalizedEntityTexts(hass, attributes, onReady) {
  if (!hass || !attributes) return null;
  const key = lbTextCacheKey(hass, attributes);
  const cached = lbTextCacheGet(key);
  if (cached) return cached;

  const retry = LB_TEXT_RETRY.get(key);
  if (retry?.timer) {
    if (typeof onReady === "function") retry.callbacks.add(onReady);
    return null;
  }

  const existing = LB_TEXT_PENDING.get(key);
  if (existing) {
    if (typeof onReady === "function") existing.callbacks.add(onReady);
    return null;
  }

  if (typeof hass.callWS !== "function") return null;

  const callbacks = new Set();
  if (typeof onReady === "function") callbacks.add(onReady);
  const pending = { promise: null, callbacks };
  const request = hass.callWS({
    type: "lueftungsberater/localize",
    language: lbLanguage(hass),
    temperature_unit: attributes.temperature_display_unit || "°C",
    recommendation_key: attributes.recommendation_key || "unknown",
    reason_key: attributes.reason_key || "incomplete_data",
    reason_args: attributes.reason_args || {},
    duration_key: attributes.duration_key || "incomplete_data",
    night_ventilation_key: attributes.night_ventilation_key || null,
    night_ventilation_args: attributes.night_ventilation_args || {},
  })
    .then((bundle) => {
      if (bundle && typeof bundle === "object") lbTextCacheSet(key, bundle);
      const retryState = LB_TEXT_RETRY.get(key);
      if (retryState?.timer) clearTimeout(retryState.timer);
      LB_TEXT_RETRY.delete(key);
      const finished = LB_TEXT_PENDING.get(key);
      LB_TEXT_PENDING.delete(key);
      for (const callback of finished?.callbacks || []) {
        try { callback(); } catch (_err) { /* one card must not block peers */ }
      }
    })
    .catch(() => {
      const failed = LB_TEXT_PENDING.get(key);
      LB_TEXT_PENDING.delete(key);
      lbScheduleTextRetry(key, failed?.callbacks || []);
    });
  pending.promise = request;
  LB_TEXT_PENDING.set(key, pending);
  return null;
}


class LueftungsberaterCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._renderSignature = null;
    this._expandedStorageKey = null;
    this._expandedState = null;
  }

  setConfig(config) {
    // Distinguish an explicit user action from the old default More-Info tap.
    // The latter shows the automation/action state (open_now), which can differ
    // from the green room-air recommendation shown in the card itself.
    this._explicitTapAction = Object.prototype.hasOwnProperty.call(config || {}, "tap_action");
    this._config = {
      tap_action: { action: "more-info" },
      ...config,
    };
    this._expandedStorageKey = null;
    this._expandedState = null;
    this._renderSignature = null;
    this._render();
  }

  _signature(hass) {
    if (!hass || !this._config) return "none";
    if (this._isRemoteSnapshot()) {
      const snap = this._config.remote_snapshot || {};
      return `${lbLanguage(hass)}|remote|${JSON.stringify([snap.state, snap.attributes || {}])}`;
    }
    const stateObj = this._config.entity ? hass.states?.[this._config.entity] : null;
    return `${lbLanguage(hass)}|${hass.config?.unit_system?.temperature || ""}|${this._config.entity || ""}|${stateObj?.state || ""}|${stateObj?.last_updated || ""}`;
  }

  set hass(hass) {
    const signature = this._signature(hass);
    this._hass = hass;
    if (signature !== this._renderSignature) {
      this._renderSignature = signature;
      this._render();
    }
  }

  getCardSize() {
    if (this._isExpanded()) return 4;
    const stateObj = this._stateObject();
    const attrs = stateObj?.attributes || {};
    const hardLock = attrs.safety_lock === true || attrs.status === "locked";
    const showNight = Boolean(attrs.night_ventilation)
      && attrs.night_ventilation_status
      && attrs.night_ventilation_status !== "unavailable";
    return hardLock || showNight ? 2 : 1;
  }

  _persistenceKey() {
    if (this._config?.force_expanded) return null;
    const identity = this._config?.entity || this._config?.storage_key || null;
    return identity ? `lueftungsberater-card:expanded:${identity}` : null;
  }

  _isExpanded() {
    if (this._config?.force_expanded) return true;
    const key = this._persistenceKey();
    if (key !== this._expandedStorageKey) {
      this._expandedStorageKey = key;
      this._expandedState = false;
      if (key) {
        try {
          this._expandedState = window.localStorage.getItem(key) === "1";
        } catch (_err) {
          this._expandedState = false;
        }
      }
    }
    return this._expandedState === true;
  }

  _setExpanded(expanded) {
    if (this._config?.force_expanded) return;
    const key = this._persistenceKey();
    this._expandedStorageKey = key;
    this._expandedState = Boolean(expanded);
    if (key) {
      try {
        window.localStorage.setItem(key, this._expandedState ? "1" : "0");
      } catch (_err) {
        // Browser storage can be disabled; the current session still works.
      }
    }
    this._renderSignature = null;
    this._render();
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

  _statusMeta(status, displayMode = "ventilation") {
    if (status === "locked") {
      return { cls: "locked", icon: "mdi:lock" };
    }
    if (displayMode === "room_air") {
      if (status === "green") return { cls: "green", icon: "mdi:check-circle-outline" };
      if (status === "red") return { cls: "red", icon: "mdi:alert-circle-outline" };
      if (status === "orange") return { cls: "orange", icon: "mdi:alert-outline" };
      return { cls: "yellow", icon: "mdi:information-outline" };
    }
    if (status === "green") {
      return { cls: "green", icon: "mdi:window-open-variant" };
    }
    if (status === "orange") {
      return { cls: "orange", icon: "mdi:window-closed-variant" };
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
    const attributes = this._stateObject()?.attributes || {};
    // The room-air card and the advisor's HA state have distinct purposes:
    // room_good describes indoor comfort, open_now is the stable automation
    // action. Default taps should explain what the green card ACTUALLY says,
    // not open a More-Info dialog headed by the different action state.
    // Honor every explicitly configured tap_action as before.
    if (attributes.display_mode === "room_air" && !this._explicitTapAction) {
      if (!this._config.force_expanded) this._setExpanded(!this._isExpanded());
      return;
    }
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
    const meta = this._statusMeta(this._config.remote_stale ? "yellow" : status, a.display_mode || "ventilation");
    const incompleteData = ["unknown", "unavailable", "none", ""].includes(String(st.state ?? "").toLowerCase());
    const localizedTexts = lbLocalizedEntityTexts(this._hass, a, () => {
      this._renderSignature = null;
      this._render();
    });
    const recommendation = this._config.remote_stale ? lbT(this._hass,"remote.offline") : (localizedTexts?.recommendation
      || a.recommendation
      || (incompleteData ? lbT(this._hass, "recommendation.unknown") : this._localizeState(st.state)));
    // Old remote readings remain visible, but old advice must never appear current.
    const reason = this._config.remote_stale ? "" : (localizedTexts?.reason
      || a.reason
      || (incompleteData ? lbT(this._hass, "reason.incomplete_data") : ""));
    const durationText = this._config.remote_stale ? "" : (localizedTexts?.duration
      || a.duration
      || (incompleteData ? lbT(this._hass, "duration.incomplete_data") : ""));
    const nightText = this._config.remote_stale ? "" : (localizedTexts?.night || a.night_ventilation || "");
    const noticeType = a.warning_notice_kind;
    const warningNotice = !this._config.remote_stale && (noticeType === "all_clear" || noticeType === "info")
      ? [lbT(this._hass, noticeType === "all_clear" ? "warning.all_clear" : "warning.info"), a.warning_notice_text].filter(Boolean).join(": ")
      : "";
    const title = this._config.name || a.room_name || a.friendly_name || "Lüftungsassistent";
    const expanded = this._isExpanded();
    const hardLock = a.safety_lock === true || status === "locked";
    const showToggle = this._config.force_expanded !== true;
    // Already-expanded overview dialogs have nothing further to expand.
    // Avoid presenting their green header as a clickable control when the
    // default HA More-Info state would disagree with the visible room advice.
    const mainTapEnabled = !remote && !(this._config.force_expanded === true
      && a.display_mode === "room_air" && !this._explicitTapAction);
    const remoteAccess = !remote && a.remote_access_active === true;
    const remoteClients = Array.isArray(a.remote_access_clients) ? a.remote_access_clients.filter(Boolean) : [];
    const remoteAccessTitle = remoteClients.length
      ? lbT(this._hass, "remote.active_by", { clients: remoteClients.join(", ") })
      : lbT(this._hass, "remote.active");

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

    // Keep the unchanged/default card's familiar grouped rows, but evaluate
    // missing measurements by the same configured-source rules as the editor.
    // Never label an unconfigured sensor as unavailable.
    const configuredFields = new Set(lbConfiguredFields(a).map(([key]) => key));
    const missingMetric = (label, source, historyLabel) =>
      `<span class="lb-missing">${this._metric(
        lbT(this._hass, label, { value: lbT(this._hass, "metric.unavailable") }),
        source, historyLabel
      )}</span>`;
    const missingAirMetric = (label, source) => missingMetric(label, source, lbT(this._hass, "history_open"));

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
            this._airingDateLabel(a.last_confirmed_airing) || lbT(this._hass, "airing.last", { hours }),
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

    if (ti !== null || ta !== null || target !== null || configuredFields.has("temp_in") || configuredFields.has("temp_out") || configuredFields.has("target")) {
      const parts = [
        ...(ti !== null ? [this._metric(
          lbT(this._hass, "metric.inside", { value: this._valueUnit(ti, tempUnit) }),
          a.source_temperature_inside,
          lbT(this._hass, "metric.indoor_temperature_open")
        )] : configuredFields.has("temp_in") ? [missingMetric(
          "metric.inside", a.source_temperature_inside, lbT(this._hass, "metric.indoor_temperature_open")
        )] : []),
        ...(ta !== null ? [this._metric(
          `${lbT(this._hass, "metric.outside", { value: this._valueUnit(ta, tempUnit) })}${this._fallbackSuffix(a.outdoor_temperature_source)}`,
          a.source_temperature_outside,
          lbT(this._hass, "metric.outdoor_temperature_open")
        )] : configuredFields.has("temp_out") ? [missingMetric(
          "metric.outside", a.source_temperature_outside, lbT(this._hass, "metric.outdoor_temperature_open")
        )] : []),
      ];
      if (target !== null) {
        parts.push(this._metric(
          lbT(this._hass, "metric.target", { value: this._valueUnit(target, tempUnit) }),
          a.source_target_temperature,
          lbT(this._hass, "metric.thermostat_open")
        ));
      }
      if (target === null && configuredFields.has("target")) {
        parts.push(missingMetric(
          "metric.target", a.source_target_temperature, lbT(this._hass, "metric.thermostat_open")
        ));
      }
      rows.push({ icon: "mdi:thermometer", html: `${lbT(this._hass, "metric.temperature")}: ${parts.join(" · ")}` });
    }

    if (hi !== null || ho !== null || configuredFields.has("humidity_in") || configuredFields.has("humidity_out")
        || configuredFields.has("absolute_in") || configuredFields.has("absolute_out") || configuredFields.has("humidity_delta")) {
      const rh = [
        ...(hi !== null ? [this._metric(
          lbT(this._hass, "metric.inside", { value: this._valueUnit(hi, "%") }),
          a.source_humidity_inside,
          lbT(this._hass, "metric.indoor_humidity_open")
        )] : configuredFields.has("humidity_in") ? [missingMetric(
          "metric.inside", a.source_humidity_inside, lbT(this._hass, "metric.indoor_humidity_open")
        )] : []),
        ...(ho !== null ? [this._metric(
          `${lbT(this._hass, "metric.outside", { value: this._valueUnit(ho, "%") })}${this._fallbackSuffix(a.outdoor_humidity_source)}`,
          a.source_humidity_outside,
          lbT(this._hass, "metric.outdoor_humidity_open")
        )] : configuredFields.has("humidity_out") ? [missingMetric(
          "metric.outside", a.source_humidity_outside, lbT(this._hass, "metric.outdoor_humidity_open")
        )] : []),
      ];
      let html = `${lbT(this._hass, "metric.humidity")}: ${rh.join(" · ")}`;
      if (ahi !== null || aho !== null || configuredFields.has("absolute_in") || configuredFields.has("absolute_out")) {
        const absoluteParts = [];
        if (ahi !== null) absoluteParts.push(this._metric(
          lbT(this._hass, "metric.inside", { value: this._valueUnit(ahi, "g/m³") }),
          a.source_absolute_humidity_inside,
          lbT(this._hass, "metric.absolute_humidity_open")
        ));
        else if (configuredFields.has("absolute_in")) absoluteParts.push(missingMetric(
          "metric.inside", a.source_absolute_humidity_inside, lbT(this._hass, "metric.absolute_humidity_open")
        ));
        if (aho !== null) absoluteParts.push(this._metric(
          lbT(this._hass, "metric.outside", { value: this._valueUnit(aho, "g/m³") }),
          a.source_absolute_humidity_outside,
          lbT(this._hass, "metric.absolute_humidity_outdoor_open")
        ));
        else if (configuredFields.has("absolute_out")) absoluteParts.push(missingMetric(
          "metric.outside", a.source_absolute_humidity_outside, lbT(this._hass, "metric.absolute_humidity_outdoor_open")
        ));
        html += `${rh.length ? " · " : ""}${absoluteParts.join(" · ")}`;
      }
      if (diff !== null) html += `${rh.length || ahi !== null || aho !== null || configuredFields.has("absolute_in") || configuredFields.has("absolute_out") ? " · " : ""}${this._metric(
        `Δ ${this._valueUnit(diff, "g/m³")}`,
        a.source_absolute_humidity_difference,
        lbT(this._hass, "metric.absolute_humidity_difference_open")
      )}`;
      else if (configuredFields.has("humidity_delta")) html += `${rh.length || ahi !== null || aho !== null || configuredFields.has("absolute_in") || configuredFields.has("absolute_out") ? " · " : ""}<span class="lb-missing">${this._metric(
        `Δ ${lbT(this._hass,"metric.unavailable")}`,
        a.source_absolute_humidity_difference, lbT(this._hass,"metric.absolute_humidity_difference_open")
      )}</span>`;
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
          html: `<span class="lb-missing">${this._metric(lbT(this._hass, "co2.unavailable"), a.source_co2, lbT(this._hass, "co2.open"))}</span>`,
        });
      }
    }

    const indoorAir = a.indoor_air_quality_values || {};
    const outdoorAir = a.air_quality_values || {};
    const airParts = [];
    const addAirMetric = (key, labelKey, unit, sourceIn, sourceOut = null) => {
      const insideValue = this._fmt(indoorAir[key]);
      const outsideValue = this._fmt(outdoorAir[key]);
      if (insideValue === null && outsideValue === null && !sourceIn && !sourceOut) return;
      const parts = [];
      if (insideValue !== null) parts.push(this._metric(
        lbT(this._hass, "metric.inside", { value: this._valueUnit(insideValue, unit) }),
        sourceIn,
        lbT(this._hass, "history_open")
      ));
      else if (sourceIn) parts.push(missingAirMetric("metric.inside", sourceIn));
      if (outsideValue !== null) parts.push(this._metric(
        lbT(this._hass, "metric.outside", { value: this._valueUnit(outsideValue, unit) }),
        sourceOut,
        lbT(this._hass, "history_open")
      ));
      else if (sourceOut) parts.push(missingAirMetric("metric.outside", sourceOut));
      airParts.push(`${lbT(this._hass, labelKey)}: ${parts.join(" · ")}`);
    };
    addAirMetric("pm2_5", "metric.pm25", "µg/m³", a.source_pm25_inside, a.source_pm25_outside);
    addAirMetric("pm10", "metric.pm10", "µg/m³", a.source_pm10_inside, a.source_pm10_outside);
    const addFlexibleAirMetric = (choices, labelKey, sourceIn, sourceOut = null) => {
      const firstValue = (values) => {
        for (const [key, unit, kind] of choices) {
          const value = this._fmt(values[key]);
          if (value !== null) return { value, unit, kind };
        }
        return null;
      };
      const inside = firstValue(indoorAir);
      const outside = firstValue(outdoorAir);
      if (!inside && !outside && !sourceIn && !sourceOut) return;
      const display = (item) => item.kind === "index"
        ? lbT(this._hass, "metric.index_value", { value: item.value })
        : this._valueUnit(item.value, item.unit);
      const parts = [];
      if (inside) parts.push(this._metric(
        lbT(this._hass, "metric.inside", { value: display(inside) }),
        sourceIn,
        lbT(this._hass, "history_open")
      ));
      else if (sourceIn) parts.push(missingAirMetric("metric.inside", sourceIn));
      if (outside) parts.push(this._metric(
        lbT(this._hass, "metric.outside", { value: display(outside) }),
        sourceOut,
        lbT(this._hass, "history_open")
      ));
      else if (sourceOut) parts.push(missingAirMetric("metric.outside", sourceOut));
      airParts.push(`${lbT(this._hass, labelKey)}: ${parts.join(" · ")}`);
    };
    addFlexibleAirMetric(
      [["voc", "µg/m³", "mass"], ["voc_parts", "ppb", "parts"], ["voc_index", "", "index"]],
      "metric.voc",
      a.source_voc_inside,
      a.source_voc_outside
    );
    addFlexibleAirMetric(
      [["no2", "µg/m³", "mass"], ["no2_parts", "ppb", "parts"], ["no2_index", "", "index"]],
      "metric.no2",
      a.source_no2_inside,
      a.source_no2_outside
    );
    addFlexibleAirMetric(
      [["o3", "µg/m³", "mass"], ["o3_parts", "ppb", "parts"]],
      "metric.o3",
      null,
      a.source_o3_outside
    );
    addAirMetric("formaldehyde", "metric.formaldehyde", "mg/m³", a.source_formaldehyde_inside);
    if (airParts.length) rows.push({ icon: "mdi:air-filter", html: `${lbT(this._hass, "metric.air_quality")}: ${airParts.join(" · ")}` });

    const forecastStatus = a.forecast_data_status || null;
    if (forecastStatus === "stale" || forecastStatus === "unavailable") {
      rows.push({
        icon: forecastStatus === "stale" ? "mdi:weather-clock" : "mdi:weather-cloudy-alert",
        cls: "data-warning",
        html: lbT(this._hass, forecastStatus === "stale" ? "forecast.stale" : "forecast.unavailable"),
      });
    }

    const showNight = Boolean(nightText) && a.night_ventilation_status && a.night_ventilation_status !== "unavailable";
    const nightHtml = showNight ? this._escape(nightText) : "";
    // Old/remote snapshots can still expose the ventilation-action duration.
    // In room-air mode only *visible* open/continue-ventilating instructions
    // warrant an unconditional "recommended duration" label. Watching,
    // closing and no-action recommendations must not inherit that duration.
    const roomAirVentilationAction = [
      "open_now", "room_need", "room_urgent", "keep_open", "room_keep_brief",
    ].includes(a.recommendation_key);
    const showDuration = Boolean(durationText) && a.duration_key !== "not_needed"
      && (a.display_mode !== "room_air" || roomAirVentilationAction);
    const reasonHtml = reason ? this._escape(reason) : "";
    const settings = lbDisplaySettings(this._config);
    const showReason = Boolean(reason) && (expanded || hardLock) && (settings.show_reason !== false || hardLock);
    const showWarningNotice = expanded && Boolean(warningNotice);
    const showDetails = expanded;
    const showBody = showReason || showWarningNotice || showNight || showDetails;
    // A visibility-only change to the explanation must not replace the old
    // grouped temperature/humidity rows while "Klassisch" is selected.
    const customizedMeasurements = settings.layout === "split" ||
      (Array.isArray(settings.extra) && settings.extra.length > 0) ||
      (Array.isArray(settings.hidden) && settings.hidden.length > 0) ||
      (settings.order && Object.keys(settings.order).length > 0) ||
      (settings.labels && Object.keys(settings.labels).length > 0) ||
      (settings.icons && Object.keys(settings.icons).length > 0) ||
      (settings.density && settings.density !== "normal") ||
      (Array.isArray(settings.sides) && settings.sides.join(",") !== "inside,outside");
    const customFacts = this._config.display_settings && showDetails && customizedMeasurements
      ? (settings.layout === "split"
          ? this._customFacts(a,tempUnit,settings)
          : this._classicFacts(a,tempUnit,settings)) : null;
    // Hiding the CO2 *measurement* must never hide a sensor outage/grace warning.
    // When the measurement is visible, its own field already contains the warning.
    const hiddenCo2Warning = customFacts !== null && settings.hidden?.includes("co2_in") && a.has_co2 === true
      && (co2ppm === null || a.co2_data_status === "grace")
      ? `<div class="fact data-warning"><ha-icon icon="mdi:molecule-co2-off"></ha-icon><span>${this._metric(
          lbT(this._hass, co2ppm === null ? "co2.unavailable" : "co2.grace"),
          a.source_co2,
          lbT(this._hass, "co2.open")
        )}</span></div>` : "";
    const toggleLabel = lbT(this._hass, expanded ? "details.hide" : "details.show");

    this.shadowRoot.innerHTML = `
      <style>
        :host { --lb-green: var(--success-color, #43a047); --lb-yellow: #f9c74f; --lb-orange: #f57c00; --lb-red: var(--error-color, #db4437); --lb-lock: #111; display: block; }
        ha-card { overflow: hidden; padding: 0; user-select: none; -webkit-tap-highlight-color: transparent; }
        .header { display: flex; align-items: center; gap: 14px; padding: 16px; color: var(--primary-text-color); border-left: 6px solid var(--lb-accent); background: color-mix(in srgb, var(--lb-accent) 14%, var(--ha-card-background, var(--card-background-color))); }
        .header.main-tap { cursor: pointer; }
        .header.main-tap:focus-visible { outline: 2px solid var(--primary-color); outline-offset: -2px; }
        .header.green { --lb-accent: var(--lb-green); } .header.yellow { --lb-accent: var(--lb-yellow); } .header.orange { --lb-accent: var(--lb-orange); } .header.red { --lb-accent: var(--lb-red); } .header.locked { --lb-accent: var(--lb-lock); background: #fff; color: #111; }
        .header.locked .title { color: #424242; }
        .header.locked .icon-wrap { background: #f2f2f2; }
        .icon-wrap { width: 48px; height: 48px; border-radius: 50%; display: grid; place-items: center; flex: 0 0 auto; background: color-mix(in srgb, var(--lb-accent) 20%, transparent); color: var(--lb-accent); }
        .main-icon { --mdc-icon-size: 31px; color: var(--lb-accent); }
        .head-text { min-width: 0; flex: 1; }
        .remote-access-icon { width: 30px; height: 30px; border-radius: 50%; display: grid; place-items: center; flex: 0 0 auto; color: var(--info-color, #039be5); background: color-mix(in srgb, var(--info-color, #039be5) 12%, transparent); }
        .remote-access-icon ha-icon { --mdc-icon-size: 19px; }
        .info-toggle { appearance: none; border: 0; width: 34px; height: 34px; border-radius: 50%; display: grid; place-items: center; flex: 0 0 auto; cursor: pointer; color: inherit; background: color-mix(in srgb, currentColor 8%, transparent); padding: 0; }
        .info-toggle:hover, .info-toggle:focus-visible { background: color-mix(in srgb, currentColor 15%, transparent); outline: 2px solid color-mix(in srgb, currentColor 45%, transparent); outline-offset: 1px; }
        .info-toggle ha-icon { --mdc-icon-size: 22px; }
        .title { font-size: 14px; color: var(--secondary-text-color); margin-bottom: 3px; }
        .recommendation { font-size: 20px; font-weight: 600; line-height: 1.15; overflow-wrap: anywhere; }
        .body { padding: 14px 16px 16px; }
        .why { font-size: 15px; font-weight: 700; color: var(--primary-text-color); margin-bottom: 6px; }
        .reason { line-height: 1.45; overflow-wrap: anywhere; }
        .night-advice { display: grid; grid-template-columns: 26px minmax(0,1fr); gap: 9px; align-items: start; margin-top: 13px; padding: 11px 12px; border-radius: 10px; background: color-mix(in srgb, var(--primary-color) 8%, transparent); line-height: 1.4; }
        .night-advice ha-icon { --mdc-icon-size: 21px; color: var(--primary-color); margin-top: 1px; }
        .night-copy { display: grid; gap: 2px; min-width: 0; }
        .night-title { font-size: 13px; font-weight: 700; color: var(--primary-text-color); }
        .night-text { overflow-wrap: anywhere; }
        .duration { display: grid; gap: 2px; margin-top: 12px; line-height: 1.4; }
        .duration-label { font-weight: 700; }
        .facts { display: grid; gap: 8px; padding-top: 13px; margin-top: 13px; border-top: 1px solid var(--divider-color); color: var(--secondary-text-color); font-size: 12.5px; }
        .fact { display: grid; grid-template-columns: 22px minmax(0, 1fr); gap: 7px; align-items: start; line-height: 1.35; }
        .fact ha-icon { --mdc-icon-size: 18px; color: var(--secondary-text-color); }
        .fact.window-open { color: var(--primary-text-color); font-weight: 600; }
        .fact.window-open ha-icon { color: var(--primary-color); }
        .fact.data-warning { color: var(--warning-color); font-weight: 600; }
        .fact.data-warning ha-icon { color: var(--warning-color); }
        .lb-classic { display: grid; gap: 8px; }
        .lb-classic.lb-compact { gap: 4px; font-size: 12px; }
        .lb-classic.lb-compact .fact { line-height: 1.2; }
        .lb-classic.lb-detailed { gap: 12px; font-size: 14px; }
        .lb-classic.lb-detailed .fact { line-height: 1.55; }
        .lb-custom { display: grid; gap: 10px; font-size: 13px; }
        .lb-general { display: grid; gap: 7px; padding-bottom: 10px; border-bottom: 1px solid var(--divider-color); }
        .lb-sides { display: grid; gap: 10px; }
        .lb-split .lb-sides { grid-template-columns: minmax(0,1fr) minmax(0,1fr); }
        .lb-split .lb-side + .lb-side { border-left: 1px solid var(--divider-color); padding-left: 12px; }
        .lb-side h4 { font-size: 13px; margin: 0 0 9px; color: var(--primary-text-color); }
        .lb-field { display:flex; align-items:start; gap: 7px; margin-bottom: 9px; min-width: 0; }
        .lb-field ha-icon { --mdc-icon-size: 16px; color: var(--secondary-text-color); margin-top: 1px; flex-shrink: 0; }
        .lb-field-copy { display:grid; gap: 2px; min-width: 0; overflow-wrap:anywhere; }
        .lb-field-label { font-size: 11px; color: var(--secondary-text-color); }
        .lb-field-value { color: var(--primary-text-color); font-weight: 600; }
        .lb-missing, .lb-missing .metric-link { color: var(--warning-color, #f9c74f); font-weight: 650; text-decoration: underline; text-decoration-style: dotted; text-underline-offset: 2px; }
        .lb-compact .lb-field { margin-bottom: 3px; }
        .lb-compact .lb-field-copy { display: block; }
        .lb-compact .lb-field-label { display: inline; }
        .lb-compact .lb-field-label::after { content: ": "; }
        .lb-detailed .lb-field { margin-bottom: 13px; }
        @media (max-width: 310px) { .lb-split .lb-sides { grid-template-columns: 1fr; } .lb-split .lb-side + .lb-side { border-left: 0; border-top: 1px solid var(--divider-color); padding-left: 0; padding-top: 10px; } }
        .metric-link { appearance: none; background: none; border: 0; padding: 0; margin: 0; color: inherit; font: inherit; line-height: inherit; cursor: pointer; text-decoration-line: underline; text-decoration-style: dotted; text-decoration-thickness: 1px; text-underline-offset: 2px; text-decoration-color: color-mix(in srgb, currentColor 45%, transparent); text-align: inherit; }
        .metric-link:hover, .metric-link:focus-visible { color: var(--primary-color); text-decoration-style: solid; outline: none; }
        .warning-notice { margin: 10px 0; padding: 9px 10px; border-radius: 8px; background: color-mix(in srgb, var(--info-color, #039be5) 10%, transparent); border-left: 3px solid var(--info-color, #039be5); line-height: 1.35; font-size: 12px; }
        .hint { margin-top: 12px; color: var(--secondary-text-color); font-size: 11px; opacity: 0.8; }
        .error { padding: 16px; color: var(--error-color); }
      </style>
      <ha-card aria-label="${this._escape(title)}">
        <div class="header ${meta.cls}${mainTapEnabled ? " main-tap" : ""}" ${mainTapEnabled ? 'tabindex="0" role="button"' : ""}>
          <div class="icon-wrap"><ha-icon class="main-icon" icon="${meta.icon}"></ha-icon></div>
          <div class="head-text"><div class="title">${this._escape(title)}</div><div class="recommendation">${this._escape(recommendation)}</div></div>
          ${remoteAccess ? `<span class="remote-access-icon" title="${this._escape(remoteAccessTitle)}" aria-label="${this._escape(remoteAccessTitle)}"><ha-icon icon="mdi:lan-connect"></ha-icon></span>` : ""}
          ${showToggle ? `<button type="button" class="info-toggle" aria-label="${this._escape(toggleLabel)}" title="${this._escape(toggleLabel)}" aria-expanded="${expanded ? "true" : "false"}"><ha-icon icon="mdi:information-outline"></ha-icon></button>` : ""}
        </div>
        ${showBody ? `<div class="body">
          ${this._config.remote_stale ? `<div class="warning-notice">${lbT(this._hass, "remote.stale_notice")}</div>` : ""}
          ${showReason ? `<div class="why">${lbT(this._hass, "why")}</div><div class="reason">${reasonHtml}</div>` : ""}
          ${showWarningNotice ? `<div class="warning-notice">${this._escape(warningNotice)}</div>` : ""}
          ${showNight ? `<div class="night-advice"><ha-icon icon="mdi:weather-night"></ha-icon><div class="night-copy"><span class="night-title">${lbT(this._hass, "night.title")}</span><span class="night-text">${nightHtml}</span></div></div>` : ""}
          ${showDetails && showDuration ? `<div class="duration"><span class="duration-label">${lbT(this._hass, "duration")}</span><span>${this._escape(durationText)}</span></div>` : ""}
          ${showDetails && customFacts !== null ? `<div class="facts">${customFacts}${hiddenCo2Warning}${rows.filter((row) => row.cls === "data-warning" && (row.icon === "mdi:weather-clock" || row.icon === "mdi:weather-cloudy-alert")).map((row) => `<div class="fact data-warning"><ha-icon icon="${row.icon}"></ha-icon><span>${row.html}</span></div>`).join("")}</div>` : (showDetails && rows.length ? `<div class="facts">${rows.map((row) => `<div class="fact ${row.cls || ""}"><ha-icon icon="${row.icon}"></ha-icon><span>${row.html}</span></div>`).join("")}</div>` : "")}
          ${showDetails && !remote ? `<div class="hint">${lbT(this._hass, "hint")}</div>` : ""}
        </div>` : ""}
      </ha-card>`;

    const infoToggle = this.shadowRoot.querySelector(".info-toggle");
    infoToggle?.addEventListener("click", (event) => {
      event.stopPropagation();
      this._setExpanded(!expanded);
    });
    infoToggle?.addEventListener("keydown", (event) => event.stopPropagation());

    if (!remote) {
      const mainTap = this.shadowRoot.querySelector(".header.main-tap");
      mainTap?.addEventListener("click", (event) => {
        if (event.target?.closest?.(".info-toggle")) return;
        this._handleMainTap();
      });
      mainTap?.addEventListener("keydown", (event) => {
        if (event.target !== mainTap) return;
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


  _airingDateLabel(iso) {
    if (!iso) return lbT(this._hass, "airing.none");
    const date = new Date(iso);
    if (!Number.isFinite(date.getTime())) return lbT(this._hass, "airing.none");
    const loc = lbLocale(this._hass);
    const dayParts = (d) => new Intl.DateTimeFormat("en-CA", { timeZone: this._hass?.config?.time_zone || undefined, year: "numeric", month: "2-digit", day: "2-digit" }).format(d);
    // Use calendar dates in HA's configured time zone, not elapsed 24-hour blocks.
    const today = new Date();
    const dateKey = dayParts(date);
    const todayKey = dayParts(today);
    // Calendar dates (not UTC intervals) survive 23/25-hour DST days.
    const [year, month, localDay] = todayKey.split(/\D+/).map(Number);
    const calendarBack = (days) => {
      const d = new Date(Date.UTC(year, month - 1, localDay - days, 12));
      return new Intl.DateTimeFormat("en-CA", {timeZone: "UTC", year: "numeric", month: "2-digit", day: "2-digit"}).format(d);
    };
    const clock = new Intl.DateTimeFormat(loc, { hour: "2-digit", minute: "2-digit", timeZone: this._hass?.config?.time_zone || undefined }).format(date);
    if (dateKey === todayKey) return lbT(this._hass, "airing.today", { time: clock });
    if (dateKey === calendarBack(1)) return lbT(this._hass, "airing.yesterday", { time: clock });
    if (dateKey === calendarBack(2)) return lbT(this._hass, "airing.day_before", { time: clock });
    const day = new Intl.DateTimeFormat(loc, { year: "numeric", month: "2-digit", day: "2-digit", timeZone: this._hass?.config?.time_zone || undefined }).format(date);
    return `${day}, ${clock}`;
  }

  _metricItems(a, tempUnit) {
    const unavailable = () => `<span class="lb-missing">${lbT(this._hass,"metric.unavailable")}</span>`;

    const locValue = (value, unit = "", source = null) => {
      const n = this._fmt(value);
      return n === null ? unavailable() : this._metric(this._valueUnit(n, unit), source, lbT(this._hass, "history_open"));
    };
    const air = (side, choices, source) => {
      const found = lbAirValue(a, side, choices);
      if (!found) return unavailable();
      const text = found.index ? lbT(this._hass, "metric.index_value", {value: this._fmt(found.value)}) : this._valueUnit(this._fmt(found.value), found.unit);
      return this._metric(text, a[source], lbT(this._hass, "history_open"));
    };
    const values = {
      // Historical close time is not the current airing. Do not display
      // "yesterday" while the contact is still open, even after 48 hours.
      last_airing: a.has_window_contacts && a.window_open
        ? this._metric(
            this._openDuration(a.open_minutes)
              ? lbT(this._hass, "window.open_since", {duration: this._openDuration(a.open_minutes)})
              : lbT(this._hass, "window.open"),
            a.source_airing || a.source_last_airing,
            lbT(this._hass, "airing.open")
          )
        : this._metric(this._airingDateLabel(a.last_confirmed_airing), a.source_last_airing, lbT(this._hass, "airing.history")),
      target: locValue(this._displayTemperature(a.target_temperature, tempUnit), tempUnit, a.source_target_temperature),
      humidity_delta: locValue(a.absolute_humidity_difference, "g/m³", a.source_absolute_humidity_difference),
      window_state: a.window_data_status === "unavailable" ? unavailable() : (a.window_open ? lbT(this._hass,"window.open") : lbT(this._hass,"recommendation.keep_closed")),
      temp_in: locValue(this._displayTemperature(a.temperature_inside,tempUnit),tempUnit,a.source_temperature_inside),
      temp_out: locValue(this._displayTemperature(a.temperature_outside,tempUnit),tempUnit,a.source_temperature_outside),
      humidity_in: locValue(a.humidity_inside,"%",a.source_humidity_inside),
      humidity_out: locValue(a.humidity_outside,"%",a.source_humidity_outside),
      absolute_in: locValue(a.absolute_humidity_inside,"g/m³",a.source_absolute_humidity_inside),
      absolute_out: locValue(a.absolute_humidity_outside,"g/m³",a.source_absolute_humidity_outside),
      co2_in: (a.has_co2 === true && this._fmt(a.co2_ppm,0) === null)
        ? `<span class="lb-missing">${this._metric(lbT(this._hass,"co2.unavailable"),a.source_co2,lbT(this._hass,"co2.open"))}</span>`
        : this._fmt(a.co2_ppm,0) === null ? unavailable()
        : this._metric(this._valueUnit(this._fmt(a.co2_ppm,0),"ppm")
          + (a.co2_data_status === "grace" ? ` · ${lbT(this._hass,"co2.grace")}` : ""),
          a.source_co2,lbT(this._hass,"co2.history")),
      co2_out: locValue(a.outdoor_co2_ppm,"ppm",a.source_outdoor_co2),
      surface_temp: locValue(this._displayTemperature(a.surface_temperature,tempUnit),tempUnit,a.source_surface_temperature),
      surface_humidity: locValue(a.surface_relative_humidity,"%",a.source_surface_temperature),
      mold_risk: !lbHasValue(a.surface_temperature) || !lbHasValue(a.surface_relative_humidity)
        ? lbT(this._hass, "metric.not_assessable")
        : lbT(this._hass, a.mold_risk || a.mold_persistent ? "metric.yes" : "metric.no"),
      wind: locValue(a.wind_speed_kmh,"km/h",a.source_wind_outside),
      gust: locValue(a.wind_gust_kmh,"km/h",a.source_gust_outside),
      rain: locValue(a.rain_minutes_until,"min",a.source_rain_outside),
    };
    const airKeys = {
      pm25: [["pm2_5","µg/m³",false]], pm10: [["pm10","µg/m³",false]],
      voc: [["voc","µg/m³",false],["voc_parts","ppb",false],["voc_index","",true]],
      no2: [["no2","µg/m³",false],["no2_parts","ppb",false],["no2_index","",true]],
      o3: [["o3","µg/m³",false],["o3_parts","ppb",false]],
      formaldehyde: [["formaldehyde","mg/m³",false]],
    };
    for (const [key, choices] of Object.entries(airKeys)) {
      for (const [suffix, side] of [["in","inside"],["out","outside"]]) {
        values[`${key}_${suffix}`] = air(side, choices, `source_${key}_${side}`);
      }
    }
    return values;
  }

  _classicFacts(a, tempUnit, settings) {
    // Preserve the familiar grouped, single-column fact rows while allowing
    // visibility, icons, names and per-section ordering to be customized.
    // Only the explicit split layout may create separate inside/outside panels.
    const available = lbConfiguredFields(a);
    const values = this._metricItems(a,tempUnit);
    const ordered = ["general", "inside", "outside"].flatMap(group =>
      lbFieldsInOrder(available, group, settings).filter(field => lbFieldVisible(field, settings)));
    const groups = [
      ["temperature", ["temp_in", "temp_out", "target"], "metric.temperature", "mdi:thermometer"],
      ["humidity", ["humidity_in", "humidity_out", "absolute_in", "absolute_out", "humidity_delta"], "metric.humidity", "mdi:water-percent"],
      ["co2", ["co2_in", "co2_out"], "metric.co2", "mdi:molecule-co2"],
      ["air", ["pm25_in", "pm25_out", "pm10_in", "pm10_out", "voc_in", "voc_out", "no2_in", "no2_out", "o3_out", "formaldehyde_in"], "metric.air_quality", "mdi:air-filter"],
    ];
    const emitted = new Set();
    const renderRow = (fields, heading = "", defaultIcon = null) => {
      if (!fields.length) return "";
      const icon = settings.icons?.[fields[0][0]] || defaultIcon || fields[0][2];
      const safeIcon = /^mdi:[a-z0-9-]+$/.test(icon) ? icon : fields[0][2];
      const pieces = fields.map(field => {
        const id = field[0];
        emitted.add(id);
        const name = settings.labels?.[id] || (field[1] === "general"
          ? lbFieldLabel(this._hass,id)
          : `${lbT(this._hass, "editor."+field[1])} ${lbFieldLabel(this._hass,id)}`);
        return `${this._escape(name)}: ${values[id] ?? lbT(this._hass,"metric.unavailable")}`;
      });
      return `<div class="fact"><ha-icon icon="${safeIcon}"></ha-icon><span>${heading ? this._escape(heading)+": " : ""}${pieces.join(" · ")}</span></div>`;
    };
    const output = [];
    // Preserve the old groups when no order has been customized. Once a user
    // reorders a section, never let a fixed metric family silently override
    // that section's explicit order (including the general facts).
    const customOrder = group => Array.isArray(settings.order?.[group]) && settings.order[group].length > 0;
    const customGeneral = customOrder("general");
    const generalFields = ordered.filter(field => field[1] === "general");
    for (const field of generalFields.filter(field => customGeneral || !["target","humidity_delta"].includes(field[0]))) {
      output.push(renderRow([field]));
    }
    const sides = settings.sides?.join(",") === "outside,inside" ? ["outside", "inside"] : ["inside", "outside"];
    const sidesReordered = sides[0] !== "inside";
    if (!sidesReordered && !sides.some(customOrder)) {
      // No side order has changed: preserve the familiar grouped classic rows,
      // including when only the general facts are reordered.
      for (const [,ids,title,icon] of groups) {
        const fields = ordered.filter(field => ids.includes(field[0]) && !emitted.has(field[0]));
        if (fields.length) output.push(renderRow(fields, lbT(this._hass,title), icon));
      }
    } else {
      // The user's side order ALWAYS wins. Inside each side, follow its own
      // saved field order independently. Merge adjacent fields of one metric
      // family only within that side, never across a side boundary.
      const sideFields = sides.flatMap(side => lbFieldsInOrder(available, side, settings)
        .filter(field => lbFieldVisible(field, settings)));
      const groupFor = field => groups.find(([,ids]) => ids.includes(field[0]));
      let run = [], currentGroup = null;
      const flush = () => {
        if (!run.length) return;
        const group = currentGroup;
        // When General itself has not been reordered, keep target and delta
        // with the first matching metric row, as in the original classic card.
        if (group && !customGeneral) {
          const extraId = group[0] === "temperature" ? "target" : group[0] === "humidity" ? "humidity_delta" : null;
          const extra = extraId && generalFields.find(field => field[0] === extraId && !emitted.has(extraId));
          if (extra) run.push(extra);
        }
        output.push(renderRow(run, group ? lbT(this._hass,group[2]) : "", group?.[3]));
        run = [];
      };
      for (const field of sideFields) {
        const group = groupFor(field);
        // Standalone measurements must never get joined into an unrelated row.
        if (run.length && (field[1] !== run[0][1] || !group || !currentGroup || group[0] !== currentGroup[0])) flush();
        run.push(field);
        currentGroup = group || null;
      }
      flush();
    }
    for (const field of ordered) {
      if (!emitted.has(field[0])) output.push(renderRow([field]));
    }
    const density = ["compact","normal","detailed"].includes(settings.density) ? settings.density : "normal";
    return `<div class="lb-classic lb-${density}">${output.join("")}</div>`;
  }

  _customFacts(a, tempUnit, settings) {
    const available = lbConfiguredFields(a);
    const values = this._metricItems(a,tempUnit);
    const sideOrder = settings.sides?.join(",") === "outside,inside" ? ["outside","inside"] : ["inside","outside"];
    const density = ["compact","normal","detailed"].includes(settings.density) ? settings.density : "normal";
    const renderField = (field) => {
      const [key, , defaultIcon] = field;
      const label = String(settings.labels?.[key] || lbFieldLabel(this._hass, key));
      const icon = String(settings.icons?.[key] || defaultIcon);
      // Only trusted MDI names are allowed to become element attributes.
      const safeIcon = /^mdi:[a-z0-9-]+$/.test(icon) ? icon : defaultIcon;
      const visibleLabel = this._escape(label);
      return `<div class="lb-field"><ha-icon icon="${safeIcon}"></ha-icon><span class="lb-field-copy"><span class="lb-field-label">${visibleLabel}</span><span class="lb-field-value">${values[key] ?? lbT(this._hass, "metric.unavailable")}</span></span></div>`;
    };
    const fields = (group) => lbFieldsInOrder(available, group, settings).filter((f) => lbFieldVisible(f, settings));
    const generic = fields("general");
    const general = generic.length ? `<div class="lb-general">${generic.map(renderField).join("")}</div>` : "";
    const panels = sideOrder.map((side) => {
      const items = fields(side);
      return items.length ? `<section class="lb-side"><h4>${lbT(this._hass, "editor."+side)}</h4>${items.map(renderField).join("")}</section>` : "";
    }).filter(Boolean);
    const split = settings.layout === "split" && panels.length > 1;
    return `<div class="lb-custom ${split ? "lb-split" : ""} lb-${density}">${general}${panels.length ? `<div class="lb-sides">${panels.join("")}</div>` : ""}</div>`;
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
    this._localRenderSignature = null;
    this._localAdvisorIds = null;
    this._advisorDiscoveryTimer = null;
    this._advisorDiscoveryDue = 0;
    this._localizedRenderScheduled = false;
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
    if (this._advisorDiscoveryTimer) clearTimeout(this._advisorDiscoveryTimer);
    this._advisorDiscoveryTimer = null;
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

  _discoverLocalAdvisors(hass) {
    const states = hass?.states || {};
    this._localAdvisorIds = Object.values(states)
      .filter((stateObj) => this._isAdvisorEntity(stateObj))
      .map((stateObj) => stateObj.entity_id)
      .sort();
    this._advisorDiscoveryDue = Date.now() + 2000;
  }

  _scheduleAdvisorDiscovery() {
    if (this._advisorDiscoveryTimer || !this._hass || !this._localAdvisorIds) return;
    const delay = Math.max(0, this._advisorDiscoveryDue - Date.now());
    this._advisorDiscoveryTimer = setTimeout(() => {
      this._advisorDiscoveryTimer = null;
      if (!this._hass) return;
      const signature = this._localSignatureFor(this._hass, true);
      if (signature === this._localRenderSignature) return;
      this._localRenderSignature = signature;
      this._renderOverview();
      if (this._dialogMode === "instance") {
        const group = this._findGroup(this._dialogGroupId);
        if (group) this._renderInstanceDialog(group);
      }
    }, delay);
  }

  _localSignatureFor(hass, forceDiscovery = false) {
    if (!hass) return "none";
    const states = hass.states || {};
    const now = Date.now();
    let needsDiscovery = forceDiscovery || !Array.isArray(this._localAdvisorIds) || now >= this._advisorDiscoveryDue;

    if (!needsDiscovery) {
      // Known advisors are cheap to validate on every update. A removed or
      // downgraded advisor triggers an immediate full discovery; discovering a
      // brand-new advisor is bounded to at most two seconds by the timer below.
      needsDiscovery = this._localAdvisorIds.some((entityId) => !this._isAdvisorEntity(states[entityId]));
    }

    if (needsDiscovery) this._discoverLocalAdvisors(hass);
    else this._scheduleAdvisorDiscovery();

    const advisors = (this._localAdvisorIds || []).map((entityId) => {
      const stateObj = states[entityId];
      return `${entityId}:${stateObj?.state || ""}:${stateObj?.last_updated || ""}`;
    });
    return `${lbLanguage(hass)}|${advisors.join("|")}`;
  }

  set hass(hass) {
    if (this._dialog && this._dialogLocation && window.location.pathname !== this._dialogLocation) {
      this._destroyDialog();
    }
    const first = !this._hass;
    const previousLanguage = this._hass ? lbLanguage(this._hass) : null;
    const signature = this._localSignatureFor(hass);
    this._hass = hass;
    this._ensureShell();
    if (signature !== this._localRenderSignature) {
      this._localRenderSignature = signature;
      this._renderOverview();
      if (this._dialogMode === "instance") {
        const group = this._findGroup(this._dialogGroupId);
        if (group && !group.remote) this._renderInstanceDialog(group);
      }
    }

    if (this._popupCard && !this._openRoomRef?.remote) {
      this._popupCard.hass = hass;
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
    this._remoteTimer = setInterval(() => this._fetchRemote(), 30000);
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
    return String(friendly).replace(/^Lüftungsassistent\s*/i, "").replace(/\s*Lüftungsassistent$/i, "").trim() || friendly;
  }

  _statusMeta(status, displayMode = "ventilation") {
    if (status === "locked") return { rank: 5, cls: "locked", icon: "mdi:lock" };
    if (displayMode === "room_air") {
      if (status === "red") return { rank: 4, cls: "red", icon: "mdi:alert-circle-outline" };
      if (status === "orange") return { rank: 3, cls: "orange", icon: "mdi:alert-outline" };
      if (status === "yellow") return { rank: 2, cls: "yellow", icon: "mdi:information-outline" };
      return { rank: 1, cls: "green", icon: "mdi:check-circle-outline" };
    }
    if (status === "red") return { rank: 4, cls: "red", icon: "mdi:window-closed-variant" };
    if (status === "orange") return { rank: 3, cls: "orange", icon: "mdi:window-closed-variant" };
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

  _localizedTextsReady() {
    // One shared localization response can wake many rooms in this same
    // overview. Coalesce all callbacks from the current turn into one render so
    // a ten-room dashboard does not rebuild itself ten times back-to-back.
    if (this._localizedRenderScheduled) return;
    this._localizedRenderScheduled = true;
    Promise.resolve().then(() => {
      this._localizedRenderScheduled = false;
      this._localRenderSignature = null;
      this._renderOverview();
      if (this._dialogMode === "instance") {
        const group = this._findGroup(this._dialogGroupId);
        if (group) this._renderInstanceDialog(group);
      }
      if (this._openRoomRef?.remote) this._refreshRemoteDialog();
    });
  }

  _roomFromLocal(stateObj, index) {
    const a = stateObj.attributes || {};
    const meta = this._statusMeta(a.status || "yellow", a.display_mode || "ventilation");
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
      recommendation: (lbLocalizedEntityTexts(this._hass, a, () => {
        this._localizedTextsReady();
      })?.recommendation) || a.recommendation || lbT(this._hass, `recommendation.${state}`),
      windowOpen: a.window_open === true,
      remoteAccess: a.remote_access_active === true,
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
      const instanceName = String(a.instance_name || "Lüftungsassistent");
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
      group.remoteAccessCount = group.rooms.filter((room) => room.remoteAccess).length;
    }
    return [...groups.values()];
  }

  _remoteRoomKey(group, room, index) {
    // Current peers export a stable subentry id; use it before the editable
    // room name so hide/order preferences survive renames. Name remains the
    // legacy fallback for old v0.6.10 peers without an id.
    const stable = room?.id ?? room?.name ?? room?.attributes?.room_name ?? index;
    return `${group.id}:room:${String(stable)}`;
  }

  _remoteRoom(group, room, index) {
    const attrs = room?.attributes && typeof room.attributes === "object" ? room.attributes : {};
    const state = String(room?.state || "unknown");
    const status = String(attrs.status || "yellow");
    const meta = this._statusMeta(status, attrs.display_mode || "ventilation");
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
      recommendation: (lbLocalizedEntityTexts(this._hass, attrs, () => {
        this._localizedTextsReady();
      })?.recommendation) || attrs.recommendation || lbT(this._hass, `recommendation.${state}`),
      windowOpen: attrs.window_open === true,
      remoteAccess: false,
      remote: true,
      index,
    };
  }

  _normalizedRemoteGroups() {
    return (this._remoteGroups || []).map((rawGroup) => {
      const group = {
        id: String(rawGroup.id),
        name: String(rawGroup.name || "Lüftungsassistent"),
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
    if (group.rooms.some((room) => room.status === "locked")) return "locked";
    if (group.rooms.some((room) => room.status === "red")) return "red";
    if (group.rooms.some((room) => room.status === "orange")) return "orange";
    if (group.rooms.some((room) => room.status === "yellow")) return "yellow";
    return "green";
  }

  _roomRow(room, groupId) {
    const badges = [];
    if (room.windowOpen) {
      badges.push(`<span class="badge"><ha-icon icon="mdi:window-open-variant"></ha-icon>${lbT(this._hass, "overview.open")}</span>`);
    }
    if (room.remoteAccess) {
      badges.push(`<span class="badge remote"><ha-icon icon="mdi:lan-connect"></ha-icon>${lbT(this._hass, "overview.remote_used")}</span>`);
    }
    const badge = badges.join("");
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
    let secondary = !group.available
      ? lbT(this._hass, "overview.not_reachable")
      : `${count} ${lbT(this._hass, count === 1 ? "overview.room" : "overview.rooms")}`;
    if (!group.remote && group.remoteAccessCount > 0) {
      secondary += ` · ${lbT(this._hass, "overview.remote_rooms", { count: group.remoteAccessCount })}`;
    }
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
        :host { --lb-green: var(--success-color, #43a047); --lb-yellow: #f9c74f; --lb-orange: #f57c00; --lb-red: var(--error-color, #db4437); --lb-lock: #111; display: block; }
        ha-card { overflow: hidden; padding: 0; }
        .overview-title { padding: 12px 16px 9px; color: var(--primary-text-color); font-size: 17px; font-weight: 700; border-bottom: 1px solid var(--divider-color); }
        .room-row, .group-row { --row-accent: var(--lb-green); appearance: none; width: 100%; min-width: 0; border: 0; border-top: 1px solid var(--divider-color); border-left: 4px solid var(--row-accent); background: transparent; color: var(--primary-text-color); font: inherit; text-align: left; cursor: pointer; -webkit-tap-highlight-color: transparent; }
        .room-row:first-child, .group-row:first-child { border-top: 0; }
        .room-row.yellow, .group-row.yellow { --row-accent: var(--lb-yellow); }
        .room-row.orange, .group-row.orange { --row-accent: var(--lb-orange); }
        .room-row.red, .group-row.red { --row-accent: var(--lb-red); }
        .room-row.locked, .group-row.locked { --row-accent: var(--lb-lock); background: #fff; color: #111; box-shadow: inset 0 0 0 1px #111; }
        .room-row.locked .room-line, .room-row.locked .room-line strong, .group-row.locked .group-copy, .group-row.locked .group-copy strong, .group-row.locked .group-copy small { color: #111; }
        .group-row.unavailable { --row-accent: var(--secondary-text-color); opacity: .75; cursor: default; }
        .room-row { display: grid; grid-template-columns: 27px minmax(0, 1fr) auto 22px; gap: 8px; align-items: center; min-height: 48px; padding: 9px 10px 9px 12px; }
        .group-row { display: grid; grid-template-columns: 34px minmax(0, 1fr) 22px; gap: 9px; align-items: center; min-height: 56px; padding: 10px 12px; }
        .room-row:not(:disabled):hover, .room-row:focus-visible, .group-row:not(:disabled):hover, .group-row:focus-visible { background: color-mix(in srgb, var(--row-accent) 7%, transparent); outline: none; }
        .status-icon { --mdc-icon-size: 22px; color: var(--row-accent); }
        .group-icon { --mdc-icon-size: 25px; color: var(--row-accent); }
        .room-line { min-width: 0; line-height: 1.3; overflow-wrap: anywhere; }
        .room-line strong { font-weight: 700; }
        .separator { color: var(--secondary-text-color); }
        .badge { display: inline-flex; align-items: center; gap: 3px; padding: 2px 6px; margin-left: 4px; border-radius: 999px; background: color-mix(in srgb, var(--primary-color) 12%, transparent); color: var(--primary-text-color); font-size: 10px; font-weight: 600; white-space: nowrap; }
        .badge.remote { background: color-mix(in srgb, var(--info-color, #039be5) 12%, transparent); }
        .badge ha-icon { --mdc-icon-size: 13px; color: var(--primary-color); }
        .chevron { --mdc-icon-size: 21px; color: var(--secondary-text-color); }
        .group-copy { display: grid; min-width: 0; gap: 2px; }
        .group-copy strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14px; }
        .group-copy small { color: var(--secondary-text-color); font-size: 11px; }
        .remote-note { display:flex; gap:7px; align-items:center; padding:8px 12px; font-size:11px; color:var(--secondary-text-color); border-bottom:1px solid var(--divider-color); }
        .remote-note ha-icon { --mdc-icon-size:17px; color:var(--info-color, #039be5); }
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
      const group = groups[0];
      const remoteNote = (!group.remote && group.remoteAccessCount > 0)
        ? `<div class="remote-note"><ha-icon icon="mdi:lan-connect"></ha-icon><span>${this._escape(lbT(this._hass, "overview.remote_rooms", { count: group.remoteAccessCount }))}</span></div>`
        : "";
      content = remoteNote + group.rooms.map((room) => this._roomRow(room, group.id)).join("");
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
    const display = this._config.display_settings ? {display_settings: this._config.display_settings} : {};
    if (room.remote) {
      card.setConfig({ ...display, remote_snapshot: { state: room.state, attributes: room.attributes }, name: room.name, force_expanded: true, storage_key: room.key });
    } else {
      card.setConfig({ ...display, entity: room.entityId, name: room.name, force_expanded: true });
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
      this._popupCard.setConfig({ ...this._popupCard._config, remote_stale: true });
      this._popupCard.hass = this._hass;
      return;
    }
    this._popupCard.setConfig({ ...this._popupCard._config, remote_stale: false, remote_snapshot: { state: room.state, attributes: room.attributes }, name: room.name, force_expanded: true, storage_key: room.key });
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
    const entities = this._advisorEntities(hass).map((stateObj) => `${stateObj.entity_id}:${this._name(stateObj)}:${lbConfiguredFields(stateObj.attributes).map(f=>f[0]).join(",")}`);
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
    if (!current && entities.length === 1 && !this._config.remote_snapshot) {
      this._changed({entity: entities[0].entity_id});
      return;
    }
    this.shadowRoot.innerHTML = `
      <style>
        .editor { display: grid; gap: 14px; padding: 8px 0 16px; }
        label { display: grid; gap: 6px; color: var(--primary-text-color); font-size: 14px; font-weight: 600; }
        select, input { box-sizing: border-box; width: 100%; min-height: 44px; padding: 8px 10px; border: 1px solid var(--divider-color); border-radius: 8px; background: var(--ha-color-form-background, var(--card-background-color)); color: var(--primary-text-color); font: inherit; }
        .lb-editor-display { display:grid; gap:11px; border-top:1px solid var(--divider-color); padding-top:12px; }
        .lb-editor-display h3 { margin:0; font-size:15px; }
        .lb-editor-display label { display:grid; gap:5px; font-size:14px; line-height:1.4; }
        .lb-editor-display input[type="checkbox"] { appearance:auto; box-sizing:border-box; width:18px !important; min-width:18px; max-width:18px; height:18px !important; min-height:18px !important; padding:0; margin:0; flex:0 0 18px; accent-color:var(--primary-color); }
        .lb-show-reason,.lb-item-visible { gap:10px !important; }
        .lb-item-options input { font-size:14px; }
        @media(max-width:600px){.lb-editor-display {gap:9px}.lb-editor-display label {font-size:14px}.lb-editor-item {grid-template-columns:19px minmax(0,1fr);gap:8px}.lb-item-options{flex-wrap:wrap}.lb-item-options input { flex:1 1 120px; }}
        .lb-show-reason { display:flex !important; align-items:center; }
        .lb-editor-group { border-top:1px solid var(--divider-color); padding-top:6px; }
        .lb-editor-group h4 { margin:5px 0; display:flex; gap:6px; font-size:13px; }
        .lb-editor-fields { display:grid; gap:4px; }
        .lb-editor-item { display:grid; grid-template-columns:22px minmax(0,1fr); gap:6px; align-items:center; padding:6px 2px; border-bottom:1px solid color-mix(in srgb,var(--divider-color) 65%,transparent); }
        .lb-grip { cursor:grab; color:var(--secondary-text-color); }
        .lb-item-visible { display:flex !important; align-items:center; gap:6px !important; }
        .lb-item-options { grid-column:2; display:flex; gap:5px; }
        .lb-item-options input { min-width:0; flex:1; font-size:12px; min-height:34px; }
        .lb-editor-empty { color:var(--secondary-text-color); font-size:12px; }
        .lb-reset { background:transparent; border:1px solid var(--divider-color); padding:10px; border-radius:8px; color:var(--error-color); cursor:pointer; }
        .hint { color: var(--secondary-text-color); font-size: 12px; line-height: 1.4; }
      </style>
      <div class="editor">
        <label>${lbT(this._hass, "editor.room")}<select id="entity"><option value="">${lbT(this._hass, "editor.select_room")}</option>${entities.map((stateObj) => `<option value="${this._escape(stateObj.entity_id)}" ${stateObj.entity_id === current ? "selected" : ""}>${this._escape(this._name(stateObj))}</option>`).join("")}</select></label>
        <label>${lbT(this._hass, "editor.card_name")}<input id="name" type="text" value="${this._escape(this._config.name || "")}" placeholder="${this._escape(lbT(this._hass, "editor.card_name_placeholder"))}" /></label>
        <div class="hint">${lbT(this._hass, "editor.room_hint")}</div>
        ${lbViewEditorHtml(this._hass, this._config, lbConfiguredFields(this._hass?.states?.[current]?.attributes || {}), v=>this._escape(v))}
      </div>`;
    this.shadowRoot.querySelector("#entity")?.addEventListener("change", (event) => this._changed({ entity: event.target.value || undefined }));
    this.shadowRoot.querySelector("#name")?.addEventListener("change", (event) => this._changed({ name: event.target.value.trim() || undefined }));
    lbBindViewEditor(this.shadowRoot, this._hass, this._config, lbConfiguredFields(this._hass?.states?.[current]?.attributes || {}), next=>{
      this._changed({display_settings: next || undefined});this._render();
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
    this._remoteTimer = setInterval(() => this._fetchRemote(), 30000);
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
          name: String(a.instance_name || "Lüftungsassistent"),
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
    // Current peers export a stable subentry id; use it before the editable
    // room name so hide/order preferences survive renames. Name remains the
    // legacy fallback for old v0.6.10 peers without an id.
    const stable = room?.id ?? room?.name ?? room?.attributes?.room_name ?? index;
    return `${group.id}:room:${String(stable)}`;
  }

  _remoteEditorGroups() {
    return (this._remoteGroups || []).map((rawGroup) => {
      const group = {
        id: String(rawGroup.id),
        name: String(rawGroup.name || "Lüftungsassistent"),
        remote: true,
        available: rawGroup.available !== false,
        rooms: [],
      };
      const rooms = Array.isArray(rawGroup.rooms) ? rawGroup.rooms : [];
      group.rooms = rooms.map((room, index) => ({
        key: this._remoteRoomKey(group, room, index),
        name: String(room?.name || room?.attributes?.room_name || room?.attributes?.friendly_name || `${lbT(this._hass, "overview.room")} ${index + 1}`),
        remote: true,
        // Feed the editor the peer's actual room capabilities.
        attributes: room?.attributes || {},
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
        .lb-editor-display { display:grid; gap:11px; border-top:1px solid var(--divider-color); padding-top:12px; }
        .lb-editor-display h3 { margin:0; font-size:15px; }
        .lb-editor-display label { display:grid; gap:5px; font-size:14px; line-height:1.4; }
        .lb-editor-display input[type="checkbox"] { appearance:auto; box-sizing:border-box; width:18px !important; min-width:18px; max-width:18px; height:18px !important; min-height:18px !important; padding:0; margin:0; flex:0 0 18px; accent-color:var(--primary-color); }
        .lb-show-reason,.lb-item-visible { gap:10px !important; }
        .lb-item-options input { font-size:14px; }
        @media(max-width:600px){.lb-editor-display {gap:9px}.lb-editor-display label {font-size:14px}.lb-editor-item {grid-template-columns:19px minmax(0,1fr);gap:8px}.lb-item-options{flex-wrap:wrap}.lb-item-options input { flex:1 1 120px; }}
        .lb-show-reason { display:flex !important; align-items:center; }
        .lb-editor-group { border-top:1px solid var(--divider-color); padding-top:6px; }
        .lb-editor-group h4 { margin:5px 0; display:flex; gap:6px; font-size:13px; }
        .lb-editor-fields { display:grid; gap:4px; }
        .lb-editor-item { display:grid; grid-template-columns:22px minmax(0,1fr); gap:6px; align-items:center; padding:6px 2px; border-bottom:1px solid color-mix(in srgb,var(--divider-color) 65%,transparent); }
        .lb-grip { cursor:grab; color:var(--secondary-text-color); }
        .lb-item-visible { display:flex !important; align-items:center; gap:6px !important; }
        .lb-item-options { grid-column:2; display:flex; gap:5px; }
        .lb-item-options input { min-width:0; flex:1; font-size:12px; min-height:34px; }
        .lb-editor-empty { color:var(--secondary-text-color); font-size:12px; }
        .lb-reset { background:transparent; border:1px solid var(--divider-color); padding:10px; border-radius:8px; color:var(--error-color); cursor:pointer; }
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
            return `<div class="group" data-group-id="${this._escape(group.id)}">
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
                return `<label class="room" data-room-key="${this._escape(room.key)}" data-room-group="${this._escape(group.id)}">
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
        ${lbViewEditorHtml(this._hass, this._config, [...new Map(groups.flatMap(g=>g.rooms).flatMap(r=>lbConfiguredFields(r.attributes || this._hass?.states?.[r.entityId]?.attributes || {})).map(f=>[f[0],f])).values()], v=>this._escape(v))}
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
    const editorFields = [...new Map(groups.flatMap(g=>g.rooms).flatMap(r=>lbConfiguredFields(r.attributes || this._hass?.states?.[r.entityId]?.attributes || {})).map(f=>[f[0],f])).values()];
    lbBindViewEditor(this.shadowRoot,this._hass,this._config,editorFields,next=>{
      const config={...this._config};
      if(next) config.display_settings=next; else delete config.display_settings;
      this._emit(config);
    });
    let orderDrag=null;
    const sortable = (selector,key,callback) => {
      this.shadowRoot.querySelectorAll(selector).forEach(el=>{
        el.draggable=true;
        el.addEventListener("dragstart",e=>{
          // Room drags bubble through the group: do not overwrite them.
          if(key === "groupId" && e.target.closest?.(".room[data-room-key]")) return;
          if(e.target.closest?.("[data-lb-drag-metric]")) return;
          orderDrag={key,id:el.dataset[key],group:el.dataset.roomGroup};e.dataTransfer.effectAllowed="move";
        });
        el.addEventListener("dragover",e=>{if(orderDrag?.key===key)e.preventDefault();});
        el.addEventListener("drop",e=>{
          if(orderDrag?.key!==key||orderDrag.id===el.dataset[key])return;
          if(key==="roomMove"&&orderDrag.group!==el.dataset.roomGroup)return;
          e.preventDefault();callback(orderDrag.id,el.dataset[key],el.dataset.roomGroup);orderDrag=null;
        });
      });
    };
    sortable(".group[data-group-id]", "groupId",(source,target)=>{
      const ids=groups.map(g=>g.id);ids.splice(ids.indexOf(source),1);ids.splice(ids.indexOf(target),0,source);
      this._emit({...this._config,group_order:ids});
    });
    sortable(".room[data-room-key]","roomKey",(source,target,groupId)=>{
      const group=groups.find(g=>g.id===groupId);if(!group)return;
      const ids=group.rooms.map(r=>r.key);ids.splice(ids.indexOf(source),1);ids.splice(ids.indexOf(target),0,source);
      this._emit({...this._config,room_order:{...(this._config.room_order||{}),[groupId]:ids}});
    });
  }
}

if (!customElements.get("lueftungsberater-overview-card-editor")) {
  customElements.define("lueftungsberater-overview-card-editor", LueftungsberaterOverviewCardEditor);
}

// History-only UI labels. Actual thresholds remain exclusively Python-owned.
const LB_HISTORY_LABELS = {
  co2_in:['CO₂ innen','CO₂ indoor','CO₂ iç'],co2_out:['CO₂ außen','CO₂ outdoor','CO₂ dış'],
  temp_in:['Temperatur innen','Indoor temperature','İç sıcaklık'],temp_out:['Temperatur außen','Outdoor temperature','Dış sıcaklık'],
  target_temp:['Solltemperatur','Target temperature','Hedef sıcaklık'],surface_temp:['Oberflächentemperatur','Surface temperature','Yüzey sıcaklığı'],
  surface_humidity:['Oberflächenfeuchte','Surface humidity','Yüzey nemi'],absolute_delta:['Feuchtedifferenz','Humidity difference','Nem farkı'],
  humidity_in:['Luftfeuchte innen','Indoor humidity','İç nem'],humidity_out:['Luftfeuchte außen','Outdoor humidity','Dış nem'],
  absolute_in:['Absolute Feuchte innen','Indoor absolute humidity','İç mutlak nem'],absolute_out:['Absolute Feuchte außen','Outdoor absolute humidity','Dış mutlak nem'],
  pm25_in:['PM2,5 innen','PM2.5 indoor','PM2,5 iç'],pm25_out:['PM2,5 außen','PM2.5 outdoor','PM2,5 dış'],
  pm10_in:['PM10 innen','PM10 indoor','PM10 iç'],pm10_out:['PM10 außen','PM10 outdoor','PM10 dış'],
  no2_in:['NO₂ innen','NO₂ indoor','NO₂ iç'],no2_out:['NO₂ außen','NO₂ outdoor','NO₂ dış'],
  o3_out:['Ozon außen','Outdoor ozone','Dış ozon'],voc_in:['TVOC innen','Indoor TVOC','İç TVOC'],
  voc_out:['TVOC außen','Outdoor TVOC','Dış TVOC'],hcho_in:['Formaldehyd innen','Indoor formaldehyde','İç formaldehit'],
  wind_out:['Wind außen','Outdoor wind','Dış rüzgâr'],gust_out:['Böen außen','Outdoor gusts','Dış rüzgâr hamleleri'],
};
function lbHistoryLabel(hass,key) {
  const ix=lbLanguage(hass)==='en'?1:lbLanguage(hass)==='tr'?2:0;
  return LB_HISTORY_LABELS[key]?.[ix]||key;
}

const LB_HISTORY_PALETTE = ['#b6ac25', '#2f9cbc', '#7ab01c', '#2a61cb', '#46af2c', '#2f20cb', '#23a942', '#7e31c4', '#1ebe88', '#bc28c3', '#2997a3', '#a8d421', '#2569b6', '#5cbc2f', '#1c20b0', '#2acb3b', '#612caf', '#20cb7d', '#9323a9', '#31c4c1', '#abbe1e', '#2883c3', '#60a329', '#213dd4'];
function lbHistoryColorFamily(key){
  if(key==='target_temp')return 'temp';
  // Paired indoor/outdoor measurements share a default paint, never a limit.
  return key.replace(/_(in|out)$/,'');
}
const LB_HISTORY_COLOR_FAMILIES=[...new Set(Object.keys(LB_HISTORY_LABELS).map(lbHistoryColorFamily))];
const LB_HISTORY_NAMED_COLORS={co2:'#309cdb',temp:'#e4b14b',humidity:'#8ab94e',pm25:'#a178e4',pm10:'#a8c74d',voc:'#23b9a8'};
function lbHistoryDefaultColor(key){
  const index=LB_HISTORY_COLOR_FAMILIES.indexOf(lbHistoryColorFamily(key));
  return LB_HISTORY_NAMED_COLORS[lbHistoryColorFamily(key)] || LB_HISTORY_PALETTE[(index>=0?index:0)%LB_HISTORY_PALETTE.length];
}
function lbHistoryFocusFamily(key){
  const family=lbHistoryColorFamily(key);
  if(family==='temp'||family==='surface_temp')return 'temp';
  if(family==='humidity'||family==='surface_humidity')return 'humidity';
  return family;
}
function lbHistoryFocusLabel(hass,family){
  const lang=lbLanguage(hass);
  const names={co2:['CO₂','CO₂','CO₂'],temp:['Temp.','Temp.','Sıcaklık'],humidity:['Feuchte','Humidity','Nem'],pm25:['PM2,5','PM2.5','PM2,5'],pm10:['PM10','PM10','PM10'],voc:['VOC','VOC','VOC'],no2:['NO₂','NO₂','NO₂'],o3:['Ozon','Ozone','Ozon'],absolute:['Abs. Feuchte','Abs. humidity','Mutlak nem'],wind:['Wind','Wind','Rüzgâr']};
  return (names[family]||[family,family,family])[lang==='en'?1:lang==='tr'?2:0];
}

// Scales are keyed by physical measurement family, not by curve order.
// Indoor/outdoor values and temperature setpoints with matching units use the
// same raw-value -> Y mapping. This is a display rule, never an outdoor limit.
const LB_HISTORY_AXIS_GROUP = {
  temp_in:'temp',temp_out:'temp',target_temp:'temp',
  humidity_in:'humidity',humidity_out:'humidity',
  co2_in:'co2',co2_out:'co2',
  pm25_in:'pm25',pm25_out:'pm25',pm10_in:'pm10',pm10_out:'pm10',
  absolute_in:'absolute',absolute_out:'absolute',
  wind_out:'wind',gust_out:'wind',
};
function lbHistoryAxisGroup(key,unit){
  // Avoid combining physically incompatible Recorder scales after unit changes.
  return (LB_HISTORY_AXIS_GROUP[key]||key)+':'+(unit||'');
}

const LB_HISTORY_ALERT_RED = '#df1717';  // clearly saturated red, not theme-dependent pink

// Third card: interactive Recorder history. Its sources and good-band limits
// are supplied by the integration; no UI-owned pollution threshold table.
class LueftungsberaterHistoryCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._metrics = [];
    this._series = new Map();
    this._history = [];
    this._plotCache = new Map();
    this._cursor = null;
    this._cursorIdleTimer = null;
    this._loading = false;
    this._lastQuery = '';
    this._enableRequested = new Map();
    this._helperMissingSince = new Map();
    this._chartRegion = null;
    this._historyCache = new Map();
    this._historyCacheScope = null;
    this._stripCache = null;
    this._configRevision = 0;
    this._refreshAgain = false;
    this._chartWidth = 600;
    this._focusFamily = null;
    this._historyFetchFailed = new Set();
    this._recorderExcluded = [];
    this._advisorEvents = null;
    this._emptyHistoryRetryTimer = null;
    this._emptyHistoryRetryCount = 0;
    this._stateRefreshTimer = null;
    this._lastRefreshStart = 0;
    this._axisValueCache = new Map();
    this._labelsCache = null;
    this._labelsLanguage = null;
  }
  _scheduleStateRefresh() {
    // HA passes a new hass object for every state update, sometimes many
    // times per second. Do not rebuild the entire SVG on each notification.
    // The periodic poll still refreshes the rolling window every minute.
    if(!this.isConnected || this._stateRefreshTimer!==null)return;
    const elapsed=Date.now()-this._lastRefreshStart;
    const wait=Math.max(0,30000-Math.max(0,elapsed));
    this._stateRefreshTimer=setTimeout(()=>{
      this._stateRefreshTimer=null;
      if(this.isConnected)this._refresh();
    },wait);
  }
  setConfig(config) {
    if(this._config?.entity !== config?.entity)this._roomName=null;
    this._configRevision++;
    clearTimeout(this._cursorIdleTimer);
    this._cursorIdleTimer=null;
    this._cursor=null;
    clearTimeout(this._emptyHistoryRetryTimer);
    this._emptyHistoryRetryTimer = null;
    clearTimeout(this._stateRefreshTimer);
    this._stateRefreshTimer = null;
    this._emptyHistoryRetryCount = 0;
    this._axisValueCache.clear();
    // Older cards may contain a manually chosen perspective. From 0.11.5
    // the configured room perspective is authoritative for both cards.
    const {perspective: _legacyPerspective, ...settings} = config || {};
    this._config = {hours:24, metrics:null, colors:{}, ...settings};
    this._lastQuery = '';
    this._plotCache.clear();
    if (this._historyCacheScope !== `${this._config.entity || ''}`) {
      this._historyCache.clear();
      this._historyCacheScope = null;
    }
    this._stripCache = null;
    this._render();
    this._refresh();
  }
  set hass(hass) {
    const previous = this._hass;
    this._hass = hass;
    const current = this._config?.entity ? hass.states?.[this._config.entity] : null;
    const key = `${this._config?.entity||''}:${current?.last_updated||''}:${current?.attributes?.target_temperature||''}`;
    if (!previous) {
      this._stateKey = key;
      this._refresh();
    } else if(this._stateKey!==key){
      this._stateKey=key;
      this._scheduleStateRefresh();
    }
  }
  connectedCallback() {
    if (typeof ResizeObserver !== 'undefined') {
      this._resizeObserver = new ResizeObserver(entries=>{
        const size=entries[0]?.contentRect?.width;
        if(Number.isFinite(size) && size>0 && Math.abs(size-this._chartWidth)>3){
          this._chartWidth=size;
          this._plotCache.clear();
          this._stripCache=null;
          this._render();
        }
      });
      this._resizeObserver.observe(this);
    }
    this._timer = setInterval(() => {
      // The state-triggered refresh may already have run just before this
      // poll. Do not perform a duplicate Recorder fetch and SVG rebuild.
      if(Date.now()-this._lastRefreshStart>=30000)this._refresh();
    },60000);
    if(!this._loading)this._refresh();
  }
  disconnectedCallback() {
    clearInterval(this._timer);
    clearTimeout(this._stateRefreshTimer);
    this._stateRefreshTimer=null;
    clearTimeout(this._cursorIdleTimer);
    this._cursorIdleTimer=null;
    clearTimeout(this._emptyHistoryRetryTimer);
    this._emptyHistoryRetryTimer = null;
    this._resizeObserver?.disconnect();
  }
  getCardSize() {return 6;}
  static getConfigElement() {return document.createElement('lueftungsberater-history-card-editor');}
  static getStubConfig() {return {type:'custom:lueftungsberater-history-card'};}
  _selectCursor(timestamp) {
    if(!Number.isFinite(timestamp))return;
    this._cursor=timestamp;
    clearTimeout(this._cursorIdleTimer);
    // Only USER activity resets this timer. Neither fresh Recorder rows nor
    // automatic status updates may keep a historical inspection pinned.
    this._cursorIdleTimer=setTimeout(()=>{
      this._cursorIdleTimer=null;
      this._cursor=null;
      // Refresh gives us the latest time range and the newest Recorder rows;
      // _refresh() is safe even if another request is still in flight.
      if(this.isConnected)this._refresh();
      else this._render();
    },5*60*1000);
  }
  _source() {return this._hass?.states?.[this._config?.entity];}
  _language() {return lbLanguage(this._hass);}
  _fmt(n, digits=1) {return Number(n).toLocaleString(lbLocale(this._hass), {maximumFractionDigits:digits});}
  _esc(s) {return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  _color(metric, index) {
    const fromUser = this._config?.colors?.[metric];
    if (/^#[\da-f]{6}$/i.test(fromUser || '')) return fromUser;
    return lbHistoryDefaultColor(metric);
  }
  _historyNumber(raw) {
    if (typeof raw !== 'string' && typeof raw !== 'number') return null;
    if (String(raw).trim() === '') return null;
    const number = Number(raw);
    return Number.isFinite(number) ? number : null;
  }
  _historyUnit(unit) {
    // Normalize spelling only. A concentration in ppb is not interchangeable
    // with mass/volume without chemical and environmental context.
    const compact=String(unit??'').trim().toLowerCase()
      .replace(/[µμ]/g,'u').replace(/³/g,'3').replace(/\^3/g,'3').replace(/\s+/g,'');
    const aliases={'°c':'c','℃':'c','celsius':'c','°f':'f','℉':'f','fahrenheit':'f',
      'kelvin':'k','%':'percent','percent':'percent','kmh':'km/h',
      'km/h':'km/h','m/s':'m/s','mph':'mph','kn':'kn','kt':'kn','kts':'kn',
      'ug/m3':'ug/m3','mg/m3':'mg/m3','g/m3':'g/m3',
      'vocindex':'index','voc_index':'index'};
    return aliases[compact]||compact;
  }
  _convertHistoryUnit(value, recordedUnit, displayUnit, metricKey='') {
    if(!Number.isFinite(value))return null;
    const from=this._historyUnit(recordedUnit),to=this._historyUnit(displayUnit);
    // The normal REST Recorder response includes per-state attributes. If a
    // numeric row has no unit, its historical measurement scale is unknown.
    // A unitless Recorder row can be an authentic vendor VOC/NO₂ index.
    // Only accept it when the backend positively identifies THIS metric as
    // index-based; never guess a physical unit for arbitrary numeric states.
    if(!from && to==='index' && /^(voc|no2)_(in|out)$/.test(String(metricKey||'')))
      return value;
    if(!from||!to||['unknown','unavailable','none','n/a','?'].includes(from)||['unknown','unavailable','none','n/a','?'].includes(to))
      return null;  // Unknown scales are not comparable, even to each other.
    if(from===to)return value;
    const isTemp=x=>x==='c'||x==='f'||x==='k';
    if(isTemp(from)&&isTemp(to)){
      const c=from==='c'?value:from==='f'?(value-32)*5/9:value-273.15;
      return to==='c'?c:to==='f'?c*9/5+32:c+273.15;
    }
    // Factors are expressed relative to milligrams per cubic metre.
    const mass={'ug/m3':.001,'mg/m3':1,'g/m3':1000};
    if(Object.hasOwn(mass,from)&&Object.hasOwn(mass,to))return value*mass[from]/mass[to];
    // Factors are expressed relative to metres per second.
    const speed={'m/s':1,'km/h':1/3.6,'mph':0.44704,'kn':1852/3600};
    if(Object.hasOwn(speed,from)&&Object.hasOwn(speed,to))return value*speed[from]/speed[to];
    const parts={'ppb':1,'ppm':1000};
    if(Object.hasOwn(parts,from)&&Object.hasOwn(parts,to))return value*parts[from]/parts[to];
    // Incompatible/unknown scales are data gaps, never guessed values.
    return null;
  }
  _parseHistorySamples(rows, start, end, metric=null, keepOutageAtStart=false) {
    const parsed=(rows||[]).map(row => {
      const number=this._historyNumber(row.state);
      const converted=number!==null && metric
        ?this._convertHistoryUnit(number,row.attributes?.unit_of_measurement,metric.unit,metric.key)
        :number;
      return {t:Date.parse(row.last_updated||row.last_changed),v:converted,
        // Keep the Recorder's original value alongside its plotting value.
        raw:number!==null?String(row.state).trim():null,
        rawUnit:number!==null?String(row.attributes?.unit_of_measurement??''):null,
        invalidUnit:number!==null && metric!==null && converted===null};
    }).filter(point=>Number.isFinite(point.t)&&point.t<=end)
      .sort((a,b)=>a.t-b.t);
    const visible=parsed.filter(point=>point.t>=start);
    // Preserve the *recorded* last-good/outage pair separately from normal
    // measurements. It can precede the visible range by many hours. Never
    // publish it as a current sample or use it for cursor/limit evaluation.
    let priorGood=null,priorOutage=null;
    for(const point of parsed){
      if(point.t>=start)break;
      if(Number.isFinite(point.v)){priorGood=point;priorOutage=null;}
      else if(priorGood && !priorOutage){
        priorOutage={from:priorGood.t,start:point.t,value:priorGood.v};
      }
    }
    if(priorOutage)visible.outageContext=priorOutage;
    else if(priorGood && visible.length && !Number.isFinite(visible[0].v)){
      // First outage starts *inside* this window; preceding genuine data is
      // needed only by the orange overlay, never by the value list.
      visible.outageContext={from:priorGood.t,start:visible[0].t,value:priorGood.v};
    }
    // Recorder reports the most recent state preceding the time window.
    // It is a known state at the boundary, not a new sensor observation.
    // Crucially, a last state of unknown/unavailable or an incompatible unit
    // cannot be replaced by an earlier good reading across a real outage.
    const preceding=parsed.filter(point=>point.t<start).at(-1);
    // Once a room helper has recorded an unavailable state, that state is
    // authoritative even when it predates the visible window. Ordinary raw
    // sources retain their historical behavior (no synthetic outage rows).
    if(preceding && (Number.isFinite(preceding.v) || keepOutageAtStart)
        && !visible.some(point=>point.t===start))
      visible.unshift({...preceding,t:start,carriedFrom:preceding.t});
    return visible;
  }
  _historyAxisLabel(timestamp, otherTimestamp, hours) {
    const date=new Date(timestamp),other=new Date(otherTimestamp);
    const locale=lbLocale(this._hass);
    const sameDay=date.toLocaleDateString(locale)===other.toLocaleDateString(locale);
    const options=Number(hours)<=6&&sameDay
      ?{hour:'2-digit',minute:'2-digit'}
      :{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit',
        ...(date.getFullYear()!==other.getFullYear()?{year:'numeric'}:{})};
    return date.toLocaleString(locale,options);
  }
  _selected() {
    const all = new Set(this._metrics.map(x=>x.key));
    const selected = (Array.isArray(this._config?.metrics) ? this._config.metrics : []).filter(x=>all.has(x));
    if (Array.isArray(this._config?.metrics)) return selected;
    const preferred = this._metrics.find(m=>m.key==='co2_in') || this._metrics[0];
    if (!preferred) return [];
    return this._metrics.filter(m=>m.key.split('_')[0]===preferred.key.split('_')[0]).map(m=>m.key);
  }
  async _refresh() {
    if (this._loading) {this._refreshAgain=true;return;}
    if (!this._hass || !this._config?.entity || !this._hass.callWS) return;
    clearTimeout(this._stateRefreshTimer);
    this._stateRefreshTimer=null;
    this._lastRefreshStart=Date.now();
    const revision=this._configRevision;
    // Keep a valid time window even if the FIRST websocket call fails.
    const hours=Math.max(1,Math.min(720,Number(this._config.hours)||24));
    const end=new Date(),start=new Date(end.getTime()-hours*3600000);
    const scope=`${this._config.entity}:${this._config.hours}`;
    if(this._visibleScope!==scope){
      this._visibleScope=scope;
      this._series=new Map();this._history=[];this._decisionEvents=[];this._advisorEvents=null;
      this._plotCache.clear();this._stripCache=null;
      this._cursor=null;
    }
    // Compare against the PREVIOUS right edge. A live cursor must follow
    // the moving window; a deliberately selected historical point stays pinned.
    const wasAtLiveEdge = this._cursor===null || !Number.isFinite(this._end)
      || Math.abs(this._cursor-this._end)<=1000;
    this._start=start.getTime();this._end=end.getTime();
    if(wasAtLiveEdge || !Number.isFinite(this._cursor) || this._cursor<this._start || this._cursor>this._end)
      this._cursor=this._end;
    const checkRevision=()=>{if(revision!==this._configRevision){const error=new Error('stale history request');error.stale=true;throw error;}};
    this._loading = true;
    this._notice = null;
    try {
      // Each refresh uses live limits exported by the Python evaluator, so
      // changing the integration's target or criteria updates the chart.
      // Independent metadata requests can run together. Range changes are
      // revision-guarded so a slow answer from the old window cannot render.
      const lang=this._language();
      // Localized recommendation names rarely change. Avoid querying their
      // large lookup on every sensor tick, but invalidate on language change.
      const labelsCached=this._labelsLanguage===lang && this._labelsCache;
      const [metrics,labels,roomInfo] = await Promise.all([
        this._hass.callWS({type:'lueftungsberater/history_metrics',entity:this._config.entity}),
        labelsCached?Promise.resolve(this._labelsCache):this._hass.callWS({type:'lueftungsberater/history_recommendations',language:lang}),
        this._hass.callWS({type:'lueftungsberater/history_room_info',entity:this._config.entity}),
      ]);
      checkRevision();
      this._metrics=Array.isArray(metrics)?metrics:[];
      this._recommendationLabels=labels;
      this._labelsLanguage=lang;
      this._labelsCache=labels;
      this._roomId = roomInfo.room;
      this._recorderExcluded = Array.isArray(roomInfo.recorder_excluded) ? roomInfo.recorder_excluded : [];
      this._roomName = roomInfo.room_name || this._source()?.attributes?.room_name || this._roomName;
      const enabled = new Set(roomInfo.enabled||[]);
      const disabledHelpers = new Set(roomInfo.disabled||[]);
      const failedHelpers = new Set(roomInfo.failed||[]);
      this._historyStoreReadonly = roomInfo.history_store_readonly === true;
      this._failedHistoryMetrics = [...failedHelpers];
      if (this._historyStoreReadonly) {
        this._notice = this._language()==='de'
          ? 'Historien-Einstellungen sind beschädigt oder nicht lesbar (schreibgeschützt). Bitte Speicherdatei prüfen.'
          : this._language()==='tr'
            ? 'Geçmiş ayarları bozuk veya okunamıyor; veri dosyası yazmaya karşı korumalı.'
            : 'History preferences are damaged or unreadable (read-only). Repair the stored file.';
      } else if (failedHelpers.size) {
        const lang = this._language();
        const labels = [...failedHelpers].join(', ');
        const unavailable = roomInfo.failure_reason === 'registry_unavailable';
        this._notice = (unavailable
          ? (lang==='de'?'Historien-Registrierung konnte nicht überprüft werden':lang==='tr'?'Geçmiş sensör kaydı doğrulanamadı':'History entity registration could not be verified')
          : (lang==='de'?'Historien-Sensoranlage nach mehreren Versuchen fehlgeschlagen':lang==='tr'?'Geçmiş sensörleri birkaç denemeden sonra oluşturulamadı':'History helper registration failed after repeated attempts')) + ` (${labels}).`;
      }
      const knownHelpers = new Map(Object.entries(roomInfo.helpers||{}));
      const selected = this._selected();
      const advisor = this._source();
      const room = advisor?.attributes?.room_name;
      const lookupMirrors = () => {
        const list = Object.values(this._hass.states||{}).filter(s=>s.attributes?.history_room && s.attributes?.history_metric);
        const found = new Map();
        for (const s of list) {
          if (s.attributes.history_room && s.attributes.history_room === this._roomId) {
            if(s.attributes.history_metric==='surface_humidity' && s.attributes.history_revision!==2)continue;
            found.set(s.attributes.history_metric,s.entity_id);
          }
        }
        return found;
      };
      const toRead = new Map();
      for (const key of selected) {
        const metric = this._metrics.find(x=>x.key===key);
        if (!metric) continue;
        if (/^(sensor|number|input_number)\.[\w]+$/.test(metric.source||'')) {
          toRead.set(key,metric.source);
        }
      }
      // Keep a historical recommendation even before this card was installed.
      toRead.set('__advisor',this._config.entity);
      // Decision recording must not depend on a successful raw REST request.
      if(!enabled.has('decision') && !disabledHelpers.has('decision') &&
          !this._historyStoreReadonly && this._hass.user?.is_admin===true){
        const request=`${this._config.entity}:${this._roomId}:decision`;
        if(Date.now()-(this._enableRequested.get(request)||0)>90000){
          this._enableRequested.set(request,Date.now());
          try {
            await this._hass.callWS({type:'lueftungsberater/history_enable',
              entity:this._config.entity,metrics:['decision']});
            checkRevision();
            enabled.add('decision');
            // A helper starts at the present, not retroactively. Re-query
            // once HA has registered its new Recorder source.
            if(this.isConnected)setTimeout(()=>{if(this.isConnected&&revision===this._configRevision)this._refresh();},2200);
          } catch(error){
            this._enableRequested.delete(request);
            this._notice=this._language()==='de'
              ? 'Entscheidungsaufzeichnung konnte nicht gestartet werden.'
              : 'Decision history could not be enabled.';
          }
        }
      }
      // Fetch already-known helper timelines in the SAME Recorder request as
      // raw sources, instead of a second round trip for every range switch.
      const initialHelpers=lookupMirrors();
      for(const [key,id] of knownHelpers)initialHelpers.set(key,id);
      const wanted=[...toRead.values(),...selected.map(key=>initialHelpers.get(key)),initialHelpers.get('decision')].filter(Boolean);
      const recoverIds=new Set(selected.flatMap(key=>[toRead.get(key),initialHelpers.get(key)]).filter(Boolean));
      // Both Recorder sources of a metric use the same strict unit validator
      // as the displayed curve. A numeric state with an incompatible unit
      // must NOT become a valid last-known-value anchor.
      const historyMetricsById=new Map();
      for(const key of selected){
        const metric=this._metrics.find(item=>item.key===key);
        if(!metric)continue;
        for(const id of [toRead.get(key),initialHelpers.get(key)])
          if(id)historyMetricsById.set(id,metric);
      }
      let historical = await this._getHistory([...new Set(wanted)],start,end,recoverIds,historyMetricsById);
      const initialFetchFailures=new Set(this._historyFetchFailed);
      checkRevision();
      const byId = new Map(historical.map(a=>[a[0]?.entity_id,a]));
      // A numeric Recorder state alone is not a usable history point. The
      // original unit must be convertible into the selected metric's scale.
      const sourceIds=new Map(toRead);
      const missing = selected.filter(key=> {
        const metric=this._metrics.find(m=>m.key===key);
        const rows=toRead.has(key)?byId.get(toRead.get(key))||[]:[];
        // Raw values that the integration deliberately purges each night
        // cannot substitute for a durable, explicitly selected recording.
        const rawDays = Number(metric?.raw_retention_days);
        const rangeExceedsRawRetention = Number.isFinite(rawDays) && rawDays > 0
          && Number(this._config.hours || 24) > rawDays * 24;
        if(toRead.has(key) && this._historyFetchFailed.has(toRead.get(key)))return false;
        return !metric || metric.helper_required === true || rangeExceedsRawRetention || !this._parseHistorySamples(
          rows,start.getTime(),end.getTime(),metric).some(point=>point.v!==null);
      });
      const existingHelpers = lookupMirrors();
      for (const [key,id] of knownHelpers) existingHelpers.set(key,id);
      // Persisted opt-in is not proof that HA ever registered the helper.
      // The backend reconciles its registry after a grace period, while the
      // browser only retries missing helpers at most once per 90 seconds.
      const scopedRequest = key => `${this._config.entity}:${this._roomId}:${key}`;
      const now=Date.now();
      // A registry entry can survive a late HA registration failure. Allow
      // time for the platform to finish, then ask the backend to reconcile a
      // persisted helper that still has no live state. Existing Recorder
      // history remains readable during this wait.
      const needsRepair = key => {
        if (disabledHelpers.has(key) || failedHelpers.has(key)) {
          this._helperMissingSince.delete(scopedRequest(key));
          return false;
        }
        if (!existingHelpers.has(key)) return true;
        const id=existingHelpers.get(key);
        if (this._hass.states?.[id] || !enabled.has(key)) {
          this._helperMissingSince.delete(scopedRequest(key));
          return false;
        }
        const first=this._helperMissingSince.get(scopedRequest(key))??now;
        this._helperMissingSince.set(scopedRequest(key),first);
        return now-first>=90000;
      };
      const requests = [...new Set(['decision', ...missing].filter(key=>
        needsRepair(key) &&
        // A persisted opt-in is repaired by an admin; ordinary dashboard
        // readers retain access to Recorder without privileged write calls.
        (!enabled.has(key) || this._hass.user?.is_admin===true) &&
        this._hass.user?.is_admin!==false
      ))];
      const retryRequests=(this._historyStoreReadonly ? [] : requests).filter(key=>
        now-(this._enableRequested.get(scopedRequest(key))||0)>=90000
      );
      if (retryRequests.length) {
        retryRequests.forEach(k=>this._enableRequested.set(scopedRequest(k),now));
        try {
          const result = await this._hass.callWS({type:'lueftungsberater/history_enable',entity:this._config.entity,metrics:retryRequests});
          checkRevision();
          this._roomId = result.room;
          // Refresh after HA has had a chance to register the entities.
          if(this.isConnected)setTimeout(()=>{if(this.isConnected&&revision===this._configRevision)this._refresh();},2200);
        } catch (error) {
          if(error.stale)throw error;
          retryRequests.forEach(k=>this._enableRequested.delete(scopedRequest(k)));
          this._notice = this._language()==='de'?'Aufzeichnung konnte nicht aktiviert werden (Administratorrechte/Recorder prüfen).':'Recording could not be enabled (check administrator rights and Recorder).';
        }
      }
      const mirrorMap = lookupMirrors();
      for (const [key,id] of knownHelpers) mirrorMap.set(key,id);
      // An existing helper is the durable room-specific timeline, even if an
      // original source happens to have one older, valid Recorder sample.
      for (const key of selected) if (mirrorMap.get(key)) toRead.set(key,mirrorMap.get(key));
      if (mirrorMap.get('decision')) toRead.set('__decision',mirrorMap.get('decision'));
      const changedIds = [...new Set(toRead.values())].filter(id=>!byId.has(id));
      if (changedIds.length) {
        historical = historical.concat(await this._getHistory(changedIds,start,end,recoverIds,historyMetricsById));
        for(const id of initialFetchFailures)this._historyFetchFailed.add(id);
        checkRevision();
        for (const series of historical) if(series[0]?.entity_id) byId.set(series[0].entity_id, series);
      }
      // A helper may be unavailable during a reload and consequently have no
      // current unit. Recover the last *recorded* scale rather than assuming
      // that a VOC index/NO₂ parts reading was a mass concentration.
      for (const key of selected) {
        const metric = this._metrics.find(m=>m.key===key);
        if (!metric || metric.unit || !/^(voc|no2|o3)_/.test(key)) continue;
        const rows = byId.get(toRead.get(key)) || [];
        const last = [...rows].reverse().find(row =>
          this._historyNumber(row.state)!==null &&
          ['index','ppb','ppm','ug/m3','mg/m3'].includes(this._historyUnit(row.attributes?.unit_of_measurement)));
        if (last) {
          metric.unit = String(last.attributes.unit_of_measurement);
          // An offline unit recovery is not evidence of current limit bands.
          metric.low = null;
          metric.high = null;
        }
      }
      this._series = new Map(selected.map(key=>{
        const metric=this._metrics.find(m=>m.key===key);
        const helperId=mirrorMap.get(key);
        const helper=this._parseHistorySamples(
          helperId?byId.get(helperId):null,start.getTime(),end.getTime(),metric,true);
        const sourceId=sourceIds.get(key);
        const source=this._parseHistorySamples(
          sourceId?byId.get(sourceId):null,start.getTime(),end.getTime(),metric);
        if (!helper.length) return [key,source];
        // A recorded 'unavailable'/invalid unit is still a real helper
        // state, not an empty series. Never replace it with an old raw
        // measurement and then carry that measurement through the outage.
        // The helper is authoritative from its first recorded event onwards.
        const first=helper[0].t;
        const last=helper[helper.length-1].t;
        const prefix=source.filter(point=>point.t<first);
        // Raw recording can resume after a *valid* helper state, with a
        // visible source boundary. It must not override a known outage.
        const suffix=Number.isFinite(helper[helper.length-1].v)
          ? source.filter(point=>point.t>last) : [];
        const helperPeriod=helper.map((point,i)=>(i===0 && prefix.length)
          ? {...point,sourceBoundary:true} : point);
        if(suffix.length) suffix[0]={...suffix[0],sourceBoundary:true};
        const merged=[...prefix,...helperPeriod,...suffix].sort((a,b)=>a.t-b.t);
        // Array metadata is deliberately *not* a sample. An old good value
        // may only anchor the orange stale overlay, never a cursor reading.
        if(helper.outageContext || source.outageContext)
          merged.outageContext=helper.outageContext||source.outageContext;
        return [key,merged];
      }));
      if(this._historyFetchFailed.size){
        const failureCount=this._historyFetchFailed.size;
        this._notice=(this._language()==='de'
          ? `${failureCount} Verlaufsquelle(n) derzeit nicht abrufbar; verfügbare Kurven bleiben sichtbar.`
          : `${failureCount} history source(s) unavailable; other curves remain visible.`);
      }
      this._historyInvalidUnits=selected.some(key=>(this._series.get(key)||[]).some(point=>point.invalidUnit));
      // Display range starts at the oldest genuine measurement while a fresh
      // recording grows. Never let a new sensor reset the shared time origin.
      // Recorder's synthetic preceding state at the query boundary is not a
      // measurement, so it must not make an hour-old history look 30 days old.
      this._updateGrowingWindow(start.getTime(),end.getTime(),selected);
      this._plotCache.clear();
      const parseStatus = (row, kind) => ({t:Date.parse(row.last_updated||row.last_changed),key:row.state, attrs:kind==='decision'?row.attributes||{}:{},kind});
      this._history = [...(byId.get(this._config.entity)||[]).map(x=>parseStatus(x,'advisor')),
          ...(byId.get(toRead.get('__decision'))||[]).map(x=>parseStatus(x,'decision'))]
        .filter(x=>Number.isFinite(x.t)).sort((a,b)=>a.t-b.t);
      this._decisionEvents=this._history.filter(x=>x.kind==='decision');
      this._advisorEvents=this._history.filter(x=>x.kind==='advisor');
      this._stripCache=null;
      // A just-enabled helper can register later than the first 2.2-second
      // requery. Give empty helper timelines a handful of prompt followups,
      // without spinning forever when Recorder is unavailable or filtered.
      const awaitingFirstSamples=[...new Set([...selected,'decision'])].some(key=>{
        const id=mirrorMap.get(key);
        return id && !disabledHelpers.has(key) &&
          !this._recorderExcluded.includes(id) && !this._historyFetchFailed.has(id) &&
          !(byId.get(id)||[]).length;
      });
      if(this.isConnected && awaitingFirstSamples && this._emptyHistoryRetryCount<4
          && !this._emptyHistoryRetryTimer){
        this._emptyHistoryRetryCount++;
        this._emptyHistoryRetryTimer=setTimeout(()=>{
          this._emptyHistoryRetryTimer=null;
          if(this.isConnected && revision===this._configRevision)this._refresh();
        },3500);
      } else if(!awaitingFirstSamples){
        clearTimeout(this._emptyHistoryRetryTimer);
        this._emptyHistoryRetryTimer=null;
      }
      // Follow the moving right edge only when the cursor was actually there.
      // A manually selected historical timestamp must survive refreshes.
      const followedEnd=this._cursor===null || !Number.isFinite(this._end) || Math.abs(this._cursor-this._end)<=1000;
      // _updateGrowingWindow() has already chosen the display left edge.
      this._end=end.getTime();
      if (followedEnd || this._cursor>this._end || this._cursor<this._start) this._cursor=this._end;
    } catch (error) {
      if(!error.stale){
        console.warn('[Lüftungsassistent] History refresh failed',error);
        this._notice = this._language()==='de'
          ? 'Historie konnte nicht vollständig geladen werden. Bitte HA-Protokoll und Berechtigungen prüfen.'
          : 'History loading failed. Check the HA log and permissions.';
      }
    } finally {
      this._loading=false;
      if(revision===this._configRevision)this._render();
      if(this._refreshAgain || revision!==this._configRevision){
        this._refreshAgain=false;
        Promise.resolve().then(()=>this._refresh());
      }
    }
  }
  async _getHistory(ids,start,end,recoverIds=new Set(),metricById=new Map()) {
    if (!ids.length) return [];
    const startMs=start.getTime(), endMs=end.getTime();
    // Pure renderer callers may omit the optional source map. The runtime
    // supplies an explicit metric for every source/helper; tests with one
    // selected metric may safely infer that metric too.
    const metricFor=id=>metricById.get(id)
      ||this._metrics?.find(m=>m.source===id || m.helper_entity_id===id)
      ||(recoverIds.size===1 && this._metrics?.length===1 ? this._metrics[0] : null);
    const usable=(row,id)=>{
      const number=this._historyNumber(row?.state);
      if(number===null)return false;
      const metric=metricFor(id);
      return !metric || this._convertHistoryUnit(number,row?.attributes?.unit_of_measurement,metric.unit,metric.key)!==null;
    };
    // A different room/range must not reuse the previous history. Moving
    // 30-day windows keep their unchanged raw rows and fetch only new data.
    const scope=`${this._config.entity||''}`;
    if(this._historyCacheScope!==scope){
      this._historyCache.clear();this._historyCacheScope=scope;
    }
    const cached=[],missing=[];
    for(const id of new Set(ids)){
      const entry=this._historyCache.get(id);
      if(!entry || entry.from>startMs)missing.push(id);
      else cached.push(id);
    }
    const fetch=async(queryIds, from)=>{
      if(!queryIds.length)return;
      const url=`history/period/${encodeURIComponent(new Date(from).toISOString())}?filter_entity_id=${encodeURIComponent(queryIds.join(','))}&end_time=${encodeURIComponent(end.toISOString())}&significant_changes_only=0`;
      const response=await this._hass.callApi('GET',url);
      const groups=new Map((Array.isArray(response)?response:[]).filter(group=>group?.length).map(group=>[group[0].entity_id,group]));
      for(const id of queryIds){
        const previous=this._historyCache.get(id);
        const merge=previous && from>previous.from ? previous.rows : [];
        const combined=new Map();
        for(const row of [...merge,...(groups.get(id)||[])]){
          // The overlap is intentional: updates to recent HA states replace
          // older cached copies rather than duplicating cursor samples.
          combined.set(`${row.last_updated||row.last_changed}:${row.state}`,row);
        }
        const ordered=[...combined.values()].sort((a,b)=>Date.parse(a.last_updated||a.last_changed)-Date.parse(b.last_updated||b.last_changed));
        // Keep enough Recorder rows to revisit other time ranges, but cap
        // the cache to the supported 30-day horizon plus one left-edge state.
        const base=previous && from>previous.from ? previous.from : startMs;
        const floor=Math.max(base,endMs-720*3600000);
        let leading=null;
        const retained=[];
        for(const row of ordered){
          const t=Date.parse(row.last_updated||row.last_changed);
          if(t<floor)leading=row;
          else if(t<=endMs)retained.push(row);
        }
        if(leading)retained.unshift(leading);
        // When a later disconnect passes the cache boundary, retain its
        // newest real good/outage pair before discarding historical rows.
        // Otherwise an older, already recovered outage could anchor a newer
        // failure at the wrong stale value after weeks of running.
        let lastGood=null,firstBad=null;
        for(const row of ordered){
          const timestamp=Date.parse(row.last_updated||row.last_changed);
          if(timestamp>=floor)break;
          if(usable(row,id)){lastGood=row;firstBad=null;}
          else if(lastGood && !firstBad)firstBad=row;
        }
        const rolloverSeed=leading && !usable(leading,id) && lastGood && firstBad
          ?{good:lastGood,outage:firstBad}:null;
        this._historyCache.set(id,{from:floor,to:endMs,rows:retained,
          outageSeed:rolloverSeed||previous?.outageSeed||null,
          outageProbeBefore:previous?.outageProbeBefore??null});
      }
    };
    this._historyFetchFailed=new Set();
    const safeFetch=async(ids,from)=>{
      if(!ids.length)return;
      try {await fetch(ids,from);} catch(error) {
        console.warn('[Lüftungsassistent] History REST request failed',error);
        // A broken source must not prevent other configured curves loading.
        // On a partial failure, independent retries run concurrently rather
        // than seven successive full REST round trips.
        await Promise.all(ids.map(async id=>{
          try {await fetch([id],from);} catch(sourceError){
            this._historyFetchFailed.add(id);
            console.warn('[Lüftungsassistent] History source unavailable',id,sourceError);
          }
        }));
      }
    };
    await safeFetch(missing,startMs);
    // Freshly activated helpers are often empty on their first Recorder read.
    // Recheck an empty result promptly, without polling nonempty histories.
    const due=cached.filter(id=>{
      const entry=this._historyCache.get(id);
      return endMs-entry.to >= (entry.rows.length ? 55000 : 1500);
    });
    if(due.length){
      const from=Math.max(startMs,Math.min(...due.map(id=>this._historyCache.get(id).to))-5*60000);
      await safeFetch(due,from);
    }
    // A standard HA history response carries at most one state before the
    // requested boundary. When that state is already unavailable it does
    // NOT reveal the last numerical measurement (or the true outage start).
    // Only for selected numerical sources, recover a bounded older context
    // in progressively wider steps. Cache both positive and negative probes.
    // Do not scan unrelated decision/advisor state entities.
    const intervals=[6,48,7*24,31*24].map(hours=>hours*3600000);
    const rowTime=row=>Date.parse(row.last_updated||row.last_changed);
    const findSeed=(rows,id)=>{
      let good=null,outage=null;
      for(const row of rows){
        if(usable(row,id)){good=row;outage=null;}
        else if(good && !outage)outage=row;
      }
      return good&&outage&&!usable(rows.at(-1),id)?{good,outage}:null;
    };
    await Promise.all([...new Set(ids)].filter(id=>recoverIds.has(id)).map(async id=>{
      const entry=this._historyCache.get(id);
      if(!entry||this._historyFetchFailed.has(id))return;
      const before=entry.rows.filter(row=>rowTime(row)<=startMs);
      const first=before.at(-1)||entry.rows.find(row=>rowTime(row)>=startMs);
      if(!first)return;
      // Re-evaluate on EACH requested left edge. A recovered real value
      // followed by another outage supersedes an earlier persisted seed,
      // even before the 30-day Recorder cache is trimmed.
      const prior=entry.outageSeed && usable(entry.outageSeed.good,id)
        && !usable(entry.outageSeed.outage,id) ? entry.outageSeed : null;
      const combinedBefore=prior?[prior.good,prior.outage,...before]
        .filter(row=>rowTime(row)<=startMs).sort((a,b)=>rowTime(a)-rowTime(b)) : before;
      const existing=findSeed(combinedBefore,id);
      if(existing){
        entry.outageSeed=existing;
        return;
      }
      // A good value at the boundary is not an outage. A recovery also
      // invalidates an old seed when a later failure has no usable context.
      if(usable(first,id)){
        if(prior && before.some(row=>rowTime(row)>rowTime(prior.outage) && usable(row,id)))
          entry.outageSeed=null;
        return;
      }
      entry.outageSeed=null;
      // A failed lookup must not cause four more REST requests every minute.
      // On a later, wider period selection the cache can still be searched.
      let queried=entry.outageProbeBefore??startMs;
      for(const interval of intervals){
        const from=startMs-interval;
        if(from>=queried)continue;
        try{
          const url=`history/period/${encodeURIComponent(new Date(from).toISOString())}?filter_entity_id=${encodeURIComponent(id)}&end_time=${encodeURIComponent(new Date(startMs).toISOString())}&significant_changes_only=0`;
          const result=await this._hass.callApi('GET',url);
          const historic=(Array.isArray(result)?result:[]).flat().filter(row=>row?.state!==undefined && Number.isFinite(rowTime(row)) && rowTime(row)<=startMs);
          const combined=[...historic,...before].sort((a,b)=>rowTime(a)-rowTime(b));
          const seed=findSeed(combined,id);
          entry.outageProbeBefore=from;
          if(seed){entry.outageSeed=seed;break;}
        }catch(error){
          console.warn('[Lüftungsassistent] Older outage context unavailable',id,error);
          break; // Never claim to have searched a failed time range.
        }
        queried=from;
      }
    }));
    return [...new Set(ids)].map(id=>{
      const entry=this._historyCache.get(id);
      const rows=entry?.rows||[];
      let lo=0,hi=rows.length;
      while(lo<hi){const mid=(lo+hi)>>1;const time=Date.parse(rows[mid].last_updated||rows[mid].last_changed);
        if(time<startMs)lo=mid+1;else hi=mid;}
      const slice=rows.slice(Math.max(0,lo-1)).filter(row=>Date.parse(row.last_updated||row.last_changed)<=endMs);
      // Outage seed rows predate the visible window, and are not new
      // measurements. The parser strips them from the normal series while
      // retaining their provenance for the orange stale overlay.
      const seed=entry?.outageSeed;
      // Seeds describe the outage *active at this left edge*, never a
      // replacement measurement or a future outage from another period.
      const atBoundary=rows.filter(row=>rowTime(row)<=startMs).at(-1);
      const relevantSeed=seed && rowTime(seed.outage)<=startMs
        && (!atBoundary || !usable(atBoundary,id)) ?seed:null;
      const actual=relevantSeed?[relevantSeed.good,relevantSeed.outage,...slice]:slice;
      const unique=new Map(actual.map(row=>[`${row.last_updated||row.last_changed}:${row.state}`,row]));
      return [...unique.values()].sort((a,b)=>rowTime(a)-rowTime(b))
        .map(row=>row.entity_id?row:{...row,entity_id:id});
    });
  }
  _historicalDecision(at) {
    if(!Number.isFinite(at))return null;
    // A room decision has its own, authoritative Recorder timeline. Later
    // technical advisor updates never replace its perspective or color.
    const decisions=this._decisionEvents || this._history.filter(x=>x.kind==='decision');
    const recorded=this._atOrBefore(decisions,at);
    const fallback=this._atOrBefore(this._advisorEvents || this._history.filter(x=>x.kind==='advisor'),at);
    const decision=recorded || fallback;
    if(!decision || ['unknown','unavailable'].includes(decision.key))return null;
    const attrs=decision.attrs||{};
    const perspective=this._source()?.attributes?.display_mode||'room_air';
    const color=decision.kind==='decision'
      ? (attrs.safety_lock?'locked':perspective==='room_air'?attrs.room_status:attrs.ventilation_status)
      : null;
    const key=decision.kind==='decision'
      ? (attrs.safety_lock ? attrs.ventilation_recommendation_key||decision.key
        : (perspective==='room_air'?attrs.room_recommendation_key:attrs.ventilation_recommendation_key)||decision.key)
      : decision.key;
    return {key,color:color||null};
  }
  _statusPaint(status) {
    return ({green:'var(--success-color,#43a047)',yellow:'#f9c74f',orange:'#f57c00',red:'var(--error-color,#db4437)',locked:'#ffffff'})[status]||'var(--secondary-text-color,#999)';
  }
  _atOrBefore(data, at) {
    let lo=0,hi=data.length;
    while(lo<hi){const mid=(lo+hi)>>1;if(data[mid].t<=at)lo=mid+1;else hi=mid;}
    return lo?data[lo-1]:null;
  }
  _updateGrowingWindow(requestedStart, end, selected=this._selected()) {
    // There is only ONE clock for all selected curves. A later-added CO2
    // trace joins at its real time instead of restarting at the left edge.
    let first=Infinity;
    let hasPreWindowState=false;
    for(const key of selected){
      // Every series is chronological. Only its first genuine reading is
      // needed, so thousands of Recorder samples do not slow every update.
      const series=this._series.get(key)||[];
      const context=series.outageContext;
      if(context && context.start<=requestedStart && Number.isFinite(context.value))
        hasPreWindowState=true;
      for(const point of series){
        if(!Number.isFinite(point.t)||point.t>end)break;
        if(!Number.isFinite(point.v)){
          if(point.carriedFrom!==undefined)hasPreWindowState=true;
          continue;
        }
        if(point.carriedFrom!==undefined){
          hasPreWindowState=true;
          continue;
        }
        if(point.t>=requestedStart && point.t<first)first=point.t;
        break;
      }
    }
    // With zero samples the time axis begins *now*, not with a fictitious
    // 30-day recording. An actual pre-window HA state is an exception: its
    // still-active value belongs at the normal left window boundary.
    this._start=hasPreWindowState?requestedStart
      :Number.isFinite(first)?Math.max(requestedStart,Math.min(first,end)):end;
    this._end=end;
    return this._start;
  }
  _outageRuns(data, start, end) {
    // Unknown/unavailable/invalid-unit states are interruptions. Draw the
    // previous observed value as a *visually stale* orange hold, without
    // publishing that old number as a valid cursor reading during the outage.
    const runs=[];
    const context=data?.outageContext;
    let lastGood=context&&Number.isFinite(context.value)
      ?{t:context.from,v:context.value}:null;
    let outage=lastGood&&Number.isFinite(context.start)
      ?{start:context.start,from:context.from,value:context.value}:null;
    for(const point of data||[]){
      if(!Number.isFinite(point.t)||point.t>end)continue;
      if(Number.isFinite(point.v)){
        if(outage){
          if(point.t>outage.start)runs.push({...outage,end:point.t,recovered:true});
          outage=null;
        }
        lastGood=point;
      }else if(lastGood && !outage && point.t>=lastGood.t){
        // A recorded failure (rather than just an old timestamp) begins the
        // orange zone at the first failure event. Subsequent failures do not
        // move that beginning or extend a genuine measured segment.
        outage={start:point.t,from:lastGood.t,value:lastGood.v};
      }
    }
    if(outage && end>outage.start)runs.push({...outage,end,recovered:false});
    return runs.filter(run=>run.end>start&&run.start<end);
  }
  _outagePaths(data, metric, axis, x, py, normalColor, start, end) {
    let runs=this._outageRuns(data,start,end);
    if(!runs.length)return '';
    // Frequent disconnect/reconnect flapping can create many more outages
    // than available screen pixels. Keep the longest representative hold in
    // each horizontal pixel; otherwise a 30-day graph can produce megabytes
    // of near-identical, subpixel SVG paths and freeze the browser.
    const pixels=Math.max(1,Math.round(Math.abs(x(end)-x(start))));
    if(runs.length>Math.max(100,pixels)){
      const buckets=new Map(),origin=x(start);
      for(const run of runs){
        const mid=Math.max(start,Math.min(end,(run.start+run.end)/2));
        const bucket=Math.max(0,Math.min(pixels-1,Math.floor(x(mid)-origin)));
        const previous=buckets.get(bucket);
        if(!previous || run.end-run.start>previous.end-previous.start)
          buckets.set(bucket,run);
      }
      runs=[...buckets.values()].sort((a,b)=>a.start-b.start);
      this._outageCondensed=true;
    }
    const outside=metric.key.endsWith('_out') || metric.key==='wind_out'||metric.key==='gust_out';
    const dash=outside?' stroke-dasharray="6 4"':' stroke-dasharray="5 4"';
    return runs.map(run=>{
      const sx=x(Math.max(run.start,start)),ex=x(Math.min(run.end,end));
      if(ex<=sx)return '';
      const y=py(axis.y(run.value));
      // The last recorded state is held through to the first failure, but
      // never misrepresented as a newly measured point or an active alert.
      const bridge=run.from>=start && run.start>run.from
        ? `<path data-outage-lead="${this._esc(metric.key)}" d="M${x(run.from).toFixed(1)} ${y.toFixed(1)} L${sx.toFixed(1)} ${y.toFixed(1)}" stroke="${normalColor}" stroke-opacity=".45" stroke-width="1.8" fill="none" stroke-dasharray="3 5"/>`:'';
      const path=`M${sx.toFixed(1)} ${y.toFixed(1)} L${ex.toFixed(1)} ${y.toFixed(1)}`;
      const label=this._language()==='de'?'Sensor nicht verfügbar – letzter bekannter Wert':this._language()==='tr'?'Sensör kullanılamıyor – son bilinen değer':'Sensor unavailable – last known value';
      return `${bridge}<g data-history-outage="${this._esc(metric.key)}"><title>${this._esc(label)}</title>
        <path d="${path}" fill="none" stroke="#ff9500" stroke-opacity=".27" stroke-width="12" stroke-linecap="round"/>
        <path d="${path}" fill="none" stroke="#ff9d13" stroke-width="2.6"${dash} stroke-linecap="round"/></g>`;
    }).join('');
  }
  _plotSamples(data, start, end, budget=1200, isStep=false) {
    // Mark gaps on the *original* series. Rendering buckets can skip hours
    // even when the original observations were continuous.
    let segment=0,last=null,interrupted=false;
    const valid=[];
    for(const point of data){
      if(!Number.isFinite(point.t))continue;
      if(!Number.isFinite(point.v)) {
        // Recorder state 'unknown', 'unavailable' or an empty/non-numeric
        // reading is a real disconnection, even for a five-minute interval.
        // For a state-valued setpoint, the previous value lasted until this
        // precise outage, and must not terminate early or extend past it.
        if(isStep && !interrupted && last!==null && point.t>last)
          valid.push({...valid[valid.length-1],t:point.t,carriedToOutage:true});
        if(last!==null)interrupted=true;
        continue;
      }
      if(last!==null && (interrupted || point.sourceBoundary))segment++;
      valid.push({...point,segment});
      last=point.t;
      interrupted=false;
    }
    // The last valid Recorder state is still in force at the chart's right
    // edge if no subsequent unavailable/unknown event intervened. This is
    // a graphical state-duration anchor, not a fabricated measurement.
    if(valid.length && !interrupted && last<end){
      valid.push({...valid[valid.length-1],t:end,carriedToEnd:true});
    }
    if(isStep){
      // A state change is semantically significant even without an extremum.
      // Preserve every transition and each segment end; discarding a middle
      // change would turn a genuine step into a misleading long plateau.
      const transitions=[];
      for(let i=0;i<valid.length;i++){
        const point=valid[i];
        const previous=transitions[transitions.length-1];
        if(previous && previous.segment===point.segment && previous.v===point.v
            && !previous.sourceBoundary && !point.sourceBoundary){
          // Consecutive equal reports only extend the duration of a state.
          // Keep their latest timestamp as the terminal duration anchor.
          if(i+1<valid.length && valid[i+1].segment===point.segment
              && valid[i+1].v===point.v)continue;
        }
        transitions.push(point);
      }
      return transitions;
    }
    if(valid.length<=budget)return valid;
    const n=Math.max(1,Math.floor(budget/4));
    const span=Math.max(1,end-start);
    const buckets=new Map();
    for(const point of valid){
      const index=Math.min(n-1,Math.max(0,Math.floor((point.t-start)/span*n)));
      // Keep the first/last and extrema of each actual continuous segment
      // inside a bucket, not just of the whole bucket.
      const key=`${index}:${point.segment}`;
      let bucket=buckets.get(key);
      if(!bucket){bucket={first:point,last:point,min:point,max:point};buckets.set(key,bucket);}
      else{
        bucket.last=point;
        if(point.v<bucket.min.v)bucket.min=point;
        if(point.v>bucket.max.v)bucket.max=point;
      }
    }
    const result=[];
    for(const bucket of buckets.values()){
      const uniq=new Map();
      for(const point of [bucket.first,bucket.min,bucket.max,bucket.last])uniq.set(point.t,point);
      result.push(...[...uniq.values()].sort((a,b)=>a.t-b.t));
    }
    result.sort((a,b)=>a.t-b.t);
    if(result.length<=budget)return result;
    // Exceptionally fragmented recordings need a second, strict limit.
    // Uniform sampling alone loses isolated peaks (including hazardous ones).
    // Protect the global extrema, then local extrema in time windows, before
    // evenly filling the remaining slots. The original segment identifiers
    // are carried through untouched: omitted segments cannot join lines.
    const cap=Math.max(1,Math.floor(budget));
    const selected=new Set();
    let minIndex=0,maxIndex=0;
    for(let i=1;i<result.length;i++){
      if(result[i].v<result[minIndex].v)minIndex=i;
      if(result[i].v>result[maxIndex].v)maxIndex=i;
    }
    selected.add(maxIndex);
    if(selected.size<cap)selected.add(minIndex);
    if(selected.size<cap)selected.add(0);
    if(selected.size<cap)selected.add(result.length-1);
    // Reserve at least one third of the budget for temporal coverage. Every
    // time window may retain both its lowest and its highest reading.
    const windows=Math.max(1,Math.floor((cap-selected.size)/3));
    const extremes=new Array(windows);
    const duration=Math.max(1,end-start);
    for(let i=0;i<result.length;i++){
      const point=result[i];
      const index=Math.min(windows-1,Math.max(0,Math.floor((point.t-start)/duration*windows)));
      const win=extremes[index];
      if(!win){extremes[index]={min:i,max:i};continue;}
      if(point.v<result[win.min].v)win.min=i;
      if(point.v>result[win.max].v)win.max=i;
    }
    for(const win of extremes){
      if(!win)continue;
      if(selected.size<cap)selected.add(win.max);
      if(selected.size<cap)selected.add(win.min);
    }
    if(selected.size<cap){
      const remaining=[];
      for(let i=0;i<result.length;i++)if(!selected.has(i))remaining.push(i);
      const count=Math.min(cap-selected.size,remaining.length);
      for(let i=0;i<count;i++)selected.add(remaining[Math.floor((i+.5)*remaining.length/count)]);
    }
    const reduced=[...selected].sort((a,b)=>a-b).map(index=>result[index]);
    reduced.condensedSegments=segment+1;
    return reduced;
  }
  _curvePaths(group, metric, axis, x, py, normalColor) {
    const thresholds=[metric.low,metric.high].filter(Number.isFinite).sort((a,b)=>a-b);
    const alertAt=value=>(Number.isFinite(metric.low)&&value<metric.low) ||
      (Number.isFinite(metric.high)&&value>metric.high);
    if(group.length===1){
      const point=group[0];
      return `<circle data-curve="${metric.key}" cx="${x(point.t).toFixed(1)}" cy="${py(axis.y(point.v)).toFixed(1)}" r="3.5" fill="${alertAt(point.v)?LB_HISTORY_ALERT_RED:normalColor}" data-history-point/>`;
    }
    // A setpoint holds until the next report, then jumps; measurements use
    // linear interpolation. Threshold crossings split at their exact value.
    const points=[{t:group[0].t,v:group[0].v}];
    for(let i=1;i<group.length;i++){
      const prev=group[i-1],next=group[i];
      if(metric.key==='target_temp')points.push({t:next.t,v:prev.v});
      points.push({t:next.t,v:next.v});
    }
    const segments=[];
    for(let i=1;i<points.length;i++){
      const a=points[i-1],b=points[i];
      const crossing=thresholds.filter(limit=> (a.v<limit&&b.v>limit)||(a.v>limit&&b.v<limit))
        .map(limit=>({t:a.t+(b.t-a.t)*(limit-a.v)/(b.v-a.v),v:limit}))
        .sort((left,right)=>a.v<b.v?left.v-right.v:right.v-left.v);
      const parts=[a,...crossing,b];
      for(let j=1;j<parts.length;j++){
        const from=parts[j-1],to=parts[j];
        if(from.t===to.t&&from.v===to.v)continue;
        segments.push({from,to,color:alertAt((from.v+to.v)/2)?LB_HISTORY_ALERT_RED:normalColor});
      }
    }
    // Collect adjacent runs of the same color to keep DOM sizes bounded.
    let markup='',path='',paint=null;
    const outside=metric.key.endsWith('_out')||metric.key==='wind_out'||metric.key==='gust_out';
    const dash=metric.key==='target_temp'?' stroke-dasharray="2 4"':outside?' stroke-dasharray="6 4"':'';
    const flush=()=>{if(path)markup+=`<path d="${path}" fill="none" stroke="${paint}" data-curve="${metric.key}" stroke-width="${metric.key==='target_temp'?1.8:outside?2.1:2.7}"${dash} stroke-linecap="round" stroke-linejoin="round"/>`;};
    for(const segment of segments){
      const {from,to,color}=segment;
      const xy=point=>`${x(point.t).toFixed(1)},${py(axis.y(point.v)).toFixed(1)}`;
      if(paint!==color){flush();paint=color;path=`M${xy(from)}`;}
      path+=` L${xy(to)}`;
    }
    flush();
    return markup;
  }
  _axis(metric, values, lowerZoneVisible=false) {
    // Fixed horizontal 'good' boundaries. Each metric has its own piecewise
    // *raw-value* axis, automatically expanded to contain every sample.
    const low=Number.isFinite(metric.low)?metric.low:null, high=Number.isFinite(metric.high)?metric.high:null;
    const observed=values.filter(x=>Number.isFinite(x));
    // Never spread Recorder arrays into function arguments: large 30-day
    // histories can exceed the JS engine's maximum argument count.
    let minObs=Infinity, maxObs=-Infinity;
    for(const sample of observed){
      if(sample<minObs)minObs=sample;
      if(sample>maxObs)maxObs=sample;
    }
    if(!observed.length){minObs=0;maxObs=Math.max(1,high??1);}
    const min=low!==null?Math.min(minObs,low-(high-low)*0.2):Math.min(0,minObs);
    const max=high!==null?Math.max(maxObs, high + Math.max(1,high-(low??0))*0.2):Math.max(1,maxObs);
    const range=(a,b,x,y,v)=> x+(v-a)/Math.max(0.0001,b-a)*(y-x);
    return {
      y:(v)=> {
        if (high===null && low===null) return 0.95-0.9*(v-min)/Math.max(0.0001,max-min);
        if (high===null) return v<low?range(min,low,.95,.72,v):range(low,max,.72,.04,v);
        if (low===null) return v>high?range(high,max,0.40,0.04,v):range(min,high,lowerZoneVisible?0.70:0.95,0.40,v);
        if (v<low) return range(min,low,0.95,0.72,v);
        if (v>high) return range(high,max,0.38,0.04,v);
        return range(low,high,0.72,0.38,v);
      },
      ticks: low!==null && high===null?[{v:min,p:.95},{v:low,p:.72},{v:max,p:.04}]:low!==null?[{v:min,p:.95},{v:low,p:.72},{v:high,p:.38},{v:max,p:.04}]:high!==null?[{v:min,p:lowerZoneVisible?.70:.95},{v:high,p:.40},{v:max,p:.04}]:[{v:min,p:.95},{v:max,p:.04}],
    };
  }
  _axisTickLabels(ticks) {
    // Distinct physical tick values must not be rounded to the same displayed
    // label (e.g. 24 °C and 24.4 °C). Keep integers if they are sufficient.
    const unique=[];
    for(const tick of ticks){
      if(!Number.isFinite(tick.v)||!Number.isFinite(tick.p))continue;
      if(unique.some(previous=>previous.v===tick.v))continue;
      unique.push(tick);
    }
    let digits=0;
    while(digits<6 && new Set(unique.map(tick=>this._fmt(tick.v,digits))).size<unique.length)digits++;
    return unique.map(tick=>({...tick,label:this._fmt(tick.v,digits)}));
  }
  _statusStrips(plotLeft,plotRight) {
    const perspective=this._source()?.attributes?.display_mode||'room_air';
    const cached=this._stripCache;
    if(cached&&cached.history===this._history&&cached.start===this._start&&cached.end===this._end&&cached.perspective===perspective&&cached.left===plotLeft&&cached.right===plotRight)return cached.svg;
    const begin=this._start||0,end=this._end||begin+1;
    const width=Math.max(1,Math.ceil(plotRight-plotLeft));
    const palette={green:1,yellow:2,orange:3,red:4,locked:5};
    const colors=new Array(width).fill(null);
    // Work in chronological order, once per data refresh. Multiple status
    // transitions within one pixel retain the strongest *recorded* color.
    const events=this._history;
    let current=this._historicalDecision(begin)?.color||null;
    let previous=begin;
    const mark=(a,b,color)=>{
      if(!color||b<=a)return;
      const from=Math.max(0,Math.min(width-1,Math.floor((Math.max(a,begin)-begin)/(end-begin)*width)));
      const to=Math.max(from+1,Math.min(width,Math.ceil((Math.min(b,end)-begin)/(end-begin)*width)));
      for(let px=from;px<to;px++){
        if((palette[color]||0)>(palette[colors[px]]||0))colors[px]=color;
      }
    };
    for(const event of events){
      if(event.t<=begin)continue;
      if(event.t>end)break;
      mark(previous,event.t,current);
      current=this._historicalDecision(event.t)?.color||null;
      previous=event.t;
    }
    mark(previous,end,current);
    let svg='',from=0;
    while(from<width){
      const color=colors[from];let to=from+1;
      while(to<width&&colors[to]===color)to++;
      if(color)svg+=`<rect x="${plotLeft+from}" y="28" width="${to-from}" height="12" fill="${this._statusPaint(color)}"/>`;
      from=to;
    }
    this._stripCache={history:this._history,start:this._start,end:this._end,perspective,left:plotLeft,right:plotRight,svg};
    return svg;
  }
  _cursorDetail(entries, at, t) {
    const decision=this._historicalDecision(at);
    const safeTime=Number.isFinite(at)?at:(Number.isFinite(this._end)?this._end:Date.now());
    const time=new Date(safeTime).toLocaleString(lbLocale(this._hass),{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
    const isLive=!this._cursorIdleTimer && Number.isFinite(this._end) && Math.abs(safeTime-this._end)<=1000;
    const livePrefix=this._language()==='de'?'Jetzt':this._language()==='tr'?'Şimdi':'Now';
    const displayedTime=isLive?`${livePrefix} · ${time}`:time;
    const backendLabel=decision?this._recommendationLabels?.[decision.key]:null;
    // Fresh installations may temporarily lack the history translation WS
    // response. Never expose implementation keys such as recommendation.room_good.
    const label=decision?(typeof backendLabel==='string' && backendLabel.trim()
      && !backendLabel.startsWith('recommendation.') ? backendLabel
      : lbT(this._hass,`recommendation.${decision.key}`)):t('unknown');
    const lines=entries.map((m,i)=>{
      const records=this._series.get(m.key)||[];
      const nearest=this._atOrBefore(records,at);
      // Recorder records state changes, not necessarily every repeated report.
      // A known value remains the state until a real outage/update is recorded.
      let value='—';
      if(nearest&&Number.isFinite(nearest.v)){
        // Display the original recorded state first. A converted equivalent is
        // also useful when the unit changed during the selected time period.
        const hasRaw=nearest.raw!==null&&nearest.raw!==undefined&&nearest.rawUnit;
        value=hasRaw?`${nearest.raw} ${nearest.rawUnit}`:`${this._fmt(nearest.v)} ${m.unit}`;
        if(hasRaw&&this._historyUnit(nearest.rawUnit)!==this._historyUnit(m.unit)){
          value+=` (≈ ${this._fmt(nearest.v)} ${m.unit})`;
        }
      }
      return `<span class="reading"><span class="line ${m.key.endsWith('_out')?'outside':''}" style="--metric-color:${this._color(m.key,i)}"></span><span>${this._esc(lbHistoryLabel(this._hass,m.key))}</span><strong>${this._esc(value)}</strong></span>`;
    }).join('');
    return `<div class="status"><strong>${this._esc(displayedTime)}</strong><span class="dot" style="background:${this._statusPaint(decision?.color)}"></span><span class="status-label">${this._esc(label)}</span></div>
      ${decision&&!decision.color?`<div class="hint">${t('noColor')}</div>`:''}<div class="values">${lines}</div>`;
  }
  async _retryHistoryRecording() {
    if (this._historyRetryBusy || this._historyStoreReadonly ||
        this._hass?.user?.is_admin !== true || !this._failedHistoryMetrics?.length) return;
    this._historyRetryBusy=true;
    try {
      await this._hass.callWS({type:'lueftungsberater/history_enable',
        entity:this._config.entity,metrics:[...this._failedHistoryMetrics],retry:true});
      this._failedHistoryMetrics=[];
      // Manual intervention is explicit; clear local cooldowns only here.
      this._enableRequested.clear();
      await this._refresh();
    } catch (error) {
      this._notice = this._language()==='de'
        ? 'Neuer Reparaturversuch fehlgeschlagen. Home-Assistant-Protokoll prüfen.'
        : this._language()==='tr'
          ? 'Yeni onarım denemesi başarısız. Home Assistant günlüğünü kontrol edin.'
          : 'Manual retry failed. Check the Home Assistant logs.';
      this._render();
    } finally {
      this._historyRetryBusy=false;
    }
  }
  _render() {
    if (!this.shadowRoot||!this._config) return;
    // Live Recorder refreshes must not close the opened time selector or a
    // finger-driven cursor drag. Apply the newest graph after interaction.
    if(this._pointerDragging || this.shadowRoot.activeElement?.matches?.('[data-range]')){
      this._deferredRender=true;
      return;
    }
    this._deferredRender=false;
    const t=s=>this._language()==='tr'?({title:'Geçmiş',roomStatus:'Oda değerlendirmesi',select:'Ölçümler',period:'Dönem',empty:'Yapılandırılmış ölçüm yok',loading:'Geçmiş yükleniyor …',nohistory:'Henüz geçmiş yok',raw:'Ham değerler',decision:'Karar',unknown:'Kayıtlı karar yok',noColor:'Eski kararın rengi kaydedilmemiş',begin:'Kayıt etkinleştirildikten sonra başlar.',units:'Sınırlar asistanın geçerli değerlendirmesinden alınır',selectHelp:'Eğrileri ve renkleri kart düzenleyicisinden seçin.',retention:'30 gün için Home Assistant Recorder saklama ayarı gereklidir.',axisZones:'Kırmızı işaretler yalnızca ilgili ölçüm ölçeğine aittir.',condensedGaps:'Çok sayıda kesinti: çizim için noktalar azaltıldı; boşluklar birleştirilmez.',unsupportedUnits:'Geçmişteki birimi bilinmeyen veya dönüştürülemeyen ölçümler gösterilmedi.'})[s]||s:this._language()==='de'?({title:'Historie',roomStatus:'Raumbewertung',select:'Messwerte',period:'Zeitraum',empty:'Keine Messwerte eingerichtet',loading:'Lade Verlauf …',nohistory:'Noch kein Verlauf für diese Auswahl',raw:'Messwerte',decision:'Entscheidung',unknown:'Keine aufgezeichnete Entscheidung',noColor:'Farbe für ältere Entscheidung nicht aufgezeichnet',begin:'Die Aufzeichnung beginnt ab Aktivierung.',units:'Grenzen aus der aktuellen Assistentenbewertung',selectHelp:'Farbe und Messgrößen im Karteneditor einstellen.',retention:'30 Tage sind nur verfügbar, wenn Home Assistant Recorder sie aufbewahrt.',axisZones:'Rote Markierungen gelten nur für die jeweils zugehörige Messwertskala.',condensedGaps:'Sehr viele Unterbrechungen: Darstellung verdichtet; Messlücken bleiben getrennt.',unsupportedUnits:'Messwerte mit unbekannter oder nicht umrechenbarer historischer Einheit ausgelassen.'})[s]||s:({title:'History',roomStatus:'Room assessment',select:'Measurements',period:'Period',empty:'No configured measurements',loading:'Loading history …',nohistory:'No history yet for this selection',raw:'Recorded values',decision:'Decision',unknown:'No recorded decision',noColor:'Historical color was not recorded',begin:'Recording starts after activation.',units:'Limits from current assistant evaluation',selectHelp:'Choose curves and colors in the card editor.',retention:'30 days require matching Home Assistant Recorder retention settings.',axisZones:'Red markers apply only to their corresponding measurement axes.',condensedGaps:'Many interruptions: plotted points reduced; gaps remain disconnected.',unsupportedUnits:'Readings with unknown or incompatible historical units were omitted.'})[s]||s;
    const selected=this._selected(); const entries=selected.map(key=>this._metrics.find(m=>m.key===key)).filter(Boolean);
    const n=entries.length;
    const focusFamilies=[...new Set(entries.map(m=>lbHistoryFocusFamily(m.key)))];
    if(this._focusFamily&&!focusFamilies.includes(this._focusFamily))this._focusFamily=null;
    const focusLabel=this._language()==='de'?'Kurven hervorheben':this._language()==='tr'?'Eğrileri vurgula':'Highlight curves';
    const focusButtons=`<div class="focus-row" role="group" aria-label="${this._esc(focusLabel)}"><span class="focus-label">${this._esc(focusLabel)}</span><div class="focus-buttons"><button type="button" data-history-focus="" aria-pressed="${!this._focusFamily}">${this._language()==='de'?'Alle':this._language()==='tr'?'Tümü':'All'}</button>${focusFamilies.map(family=>`<button type="button" data-history-focus="${this._esc(family)}" aria-pressed="${this._focusFamily===family}">${this._esc(lbHistoryFocusLabel(this._hass,family))}</button>`).join('')}</div></div>`;
    // The chart stays inside the actual card column (no forced 860px width).
    const measured=typeof this.getBoundingClientRect==='function' ? this.getBoundingClientRect().width : 0;
    const width=Math.max(290,Math.floor((measured>100?measured:this._chartWidth||600)-24));
    // One directly labelled Y-axis per PHYSICAL scale, inside the SVG.
    // Reserve enough pixels for a legible trace even on a 360px phone card.
    const scaleGroups=[...new Set(entries.map(m=>lbHistoryAxisGroup(m.key,m.unit)))];
    // SIMOCODE-style axis separation: one-sided (and unlimited) groups left,
    // dual-limit groups right. Axes stay tied to PHYSICAL units, not curves.
    const instrumentMetrics=entries.filter(m=>!m.key.endsWith('_out') &&
      (Number.isFinite(m.low)||Number.isFinite(m.high)));
    const instrumentGroups=[...new Set(instrumentMetrics.map(m=>lbHistoryAxisGroup(m.key,m.unit)))];
    const twoSided=group=>instrumentMetrics.some(m=>lbHistoryAxisGroup(m.key,m.unit)===group &&
      Number.isFinite(m.low)&&Number.isFinite(m.high));
    const leftGroups=scaleGroups.filter(group=>!twoSided(group));
    const rightGroups=scaleGroups.filter(twoSided);
    const axisWidth=Math.max(24,Math.min(54,Math.floor((width-112)/Math.max(1,scaleGroups.length))));
    const plotLeft=Math.min(width-90,10+leftGroups.length*axisWidth);
    // Own recorded room-status lane ABOVE the plot and its Y-axis labels.
    // This is not a ppm/°C/% measurement; both lanes share exactly the same X.
    const height=398,plotRight=Math.max(plotLeft+60,width-10-rightGroups.length*axisWidth),top=86,bottom=height-48;
    const slot=group=>{
      const side=rightGroups.includes(group)?'right':'left';
      const index=side==='right'?rightGroups.indexOf(group):leftGroups.indexOf(group);
      return {side,origin:side==='right'?plotRight+5+index*axisWidth:10+index*axisWidth};
    };
    const initial=Number.isFinite(this._start)?this._start:Date.now()-86400000;
    const finish=Number.isFinite(this._end)&&this._end>initial?this._end:initial+1;
    const x=t=>plotLeft+(Math.max(initial,Math.min(finish,t))-initial)/(finish-initial)*(plotRight-plotLeft);
    const py=p=>top+p*(bottom-top);
    const at=this._cursor??this._end??Date.now();
    const isDual=entries.some(m=>Number.isFinite(m.low));
    const groupAxes=new Map();
    for(const group of scaleGroups){
      const members=entries.filter(m=>lbHistoryAxisGroup(m.key,m.unit)===group);
      const bounded=members.find(m=>Number.isFinite(m.low)||Number.isFinite(m.high))||members[0];
      const bounds={...bounded,low:Number.isFinite(bounded.low)?bounded.low:null,
        high:Number.isFinite(bounded.high)?bounded.high:null};
      const refs=members.map(member=>this._series.get(member.key));
      const previous=this._axisValueCache.get(group);
      let values;
      if(previous && previous.refs.length===refs.length &&
          refs.every((ref,index)=>ref===previous.refs[index])){
        values=previous.values;
      } else {
        values=[];
        for(const ref of refs){
          for(const point of ref||[]){
            if(Number.isFinite(point.v))values.push(point.v);
          }
          // Stale overlay must remain on a meaningful Y scale even when
          // every visible numeric measurement is unavailable.
          if(Number.isFinite(ref?.outageContext?.value))values.push(ref.outageContext.value);
        }
        this._axisValueCache.set(group,{refs,values});
      }
      // If a setpoint lacks history its axis comes from the other real
      // temperature measurements. Never create a fake 0-1 setpoint axis.
      groupAxes.set(group,this._axis(bounds,values,entries.some(m=>Number.isFinite(m.low))));
    }
    const metricAxes=entries.map((m,i)=>{
      const data=this._series.get(m.key)||[];
      const span=plotRight-plotLeft;
      const isStep=m.key==='target_temp';
      const group=lbHistoryAxisGroup(m.key,m.unit);
      const axis=groupAxes.get(group);
      const cached=this._plotCache.get(m.key);
      if(cached && cached.data===data && cached.span===span && cached.isStep===isStep
          && cached.start===this._start && cached.end===this._end){return {m,i,group,axis,visible:cached.visible};}
      const visible=this._plotSamples(data,this._start,this._end,Math.max(250,2*span),isStep);
      this._plotCache.set(m.key,{data,span,isStep,start:this._start,end:this._end,axis,visible});
      return {m,i,group,axis,visible};
    });
    const guides=[0,0.38,0.40,0.72,0.95].map(p=>`<line x1="${plotLeft}" y1="${py(p)}" x2="${plotRight}" y2="${py(p)}" stroke="var(--divider-color,#555)" stroke-opacity=".6" stroke-dasharray="3 5"/>`).join('');
    const hasSamples=metricAxes.some(({m,visible})=>visible.length>0 ||
      this._outageRuns(this._series.get(m.key)||[],this._start,this._end).length>0);
    const condensed=metricAxes.some(({visible})=>Number.isFinite(visible.condensedSegments));
    // Full-width red bands are meaningful for ONE metric only. With several
    // independent scales they could falsely label a limitless wind curve red.
    const fullBands=n===1;
    // A high-only axis maps its good/high limit to .40, while a dual-limit
    // axis maps that boundary to .38. The red band must meet the SAME limit
    // as the curve/axis, not end ~5 SVG pixels early on CO2-like metrics.
    const upperRedBoundary=isDual?.38:.40;
    const topZone=fullBands&&entries.some(m=>Number.isFinite(m.high))?`<rect x="${plotLeft}" y="${py(0.04)}" width="${plotRight-plotLeft}" height="${py(upperRedBoundary)-py(.04)}" fill="${LB_HISTORY_ALERT_RED}" fill-opacity="0.12"/>`:'';
    const bottomZone=fullBands&&isDual?`<rect x="${plotLeft}" y="${py(.72)}" width="${plotRight-plotLeft}" height="${py(.95)-py(.72)}" fill="${LB_HISTORY_ALERT_RED}" fill-opacity="0.10"/><text x="${plotLeft+4}" y="${py(.91)}" font-size="10" fill="${LB_HISTORY_ALERT_RED}" opacity=".9">${this._language()==='de'?'Zu niedrig (nur zweiseitige Werte)':'Too low (two-sided values only)'}</text>`:'';
    this._outageCondensed=false;
    const lines=metricAxes.map(({m,i,axis,visible})=>{
      // Never connect two real outages, and show isolated Recorder values as
      // circles: a path with a single 'M' command is otherwise invisible.
      const groups=[];let current=[],last=null;
      for(const point of visible){
        if(last!==null&&point.segment!==last){if(current.length)groups.push(current);current=[];}
        current.push(point);last=point.segment;
      }
      if(current.length)groups.push(current);
      const color=this._color(m.key,i);
      const dimmed=this._focusFamily && lbHistoryFocusFamily(m.key)!==this._focusFamily;
      const outages=this._outagePaths(this._series.get(m.key)||[],m,axis,x,py,color,this._start,this._end);
      return `<g data-history-curve="${this._esc(m.key)}" opacity="${dimmed?'.12':'1'}">${groups.map(group=>this._curvePaths(group,m,axis,x,py,color)).join('')}${outages}</g>`;
    }).join('');
    const axes=metricAxes.filter(({m})=>instrumentMetrics.some(item=>item.key===m.key)).map(({m,i})=>{
      const color=this._color(m.key,i);
      // Each red band belongs to exactly one named measurement. Outline it
      // in that curve's *own* color and repeat the same key, limit and color
      // below in the numeric scale legend. This remains unambiguous when
      // several physical units and independently mapped Y axes overlap.
      const group=lbHistoryAxisGroup(m.key,m.unit);
      const {side,origin}=slot(group);
      const ownIndex=entries.filter(previous=>lbHistoryAxisGroup(previous.key,previous.unit)===group).findIndex(item=>item.key===m.key);
      const position=origin+(side==='right'?1:1)+Math.min(ownIndex*5,Math.max(0,axisWidth-12));
      const band=(from,to,kind,limit)=>{
        const direction=kind==='upper'?'>':'<';
        const description=`${lbHistoryLabel(this._hass,m.key)}: ${direction} ${this._fmt(limit)} ${m.unit||''}`.trim();
        return `<g data-axis-zone="${this._esc(m.key)}" data-axis-zone-kind="${kind}" aria-label="${this._esc(description)}"><title>${this._esc(description)}</title><rect x="${position}" y="${py(from)}" width="4" height="${py(to)-py(from)}" fill="${LB_HISTORY_ALERT_RED}" fill-opacity="0.98" stroke="${this._esc(color)}" stroke-width="1.5"/></g>`;
      };
      return (Number.isFinite(m.high)?band(.04,Number.isFinite(m.low)?.38:.40,'upper',m.high):'')+
        (Number.isFinite(m.low)?band(.72,.95,'lower',m.low):'');
    }).join('');
    // All physical scales need numeric ticks, including outdoor-only and
    // target-only selections. Threshold lanes remain indoor/limited only.
    const axisTicks=scaleGroups.map(group=>{
      const axis=groupAxes.get(group),member=entries.find(m=>lbHistoryAxisGroup(m.key,m.unit)===group);
      const {side,origin}=slot(group);
      const edge=side==='right'?origin+7:origin+axisWidth-3;
      const anchor=side==='right'?'start':'end';
      const unit=member?.unit||'';
      const title=`${group.split(':')[0]} ${unit}`.trim();
      const ticks=this._axisTickLabels(axis?.ticks||[]);
      return `<g data-inline-axis="${this._esc(group)}" data-axis-side="${side}" aria-label="${this._esc(title)}">
        <title>${this._esc(title)}</title>
        <text x="${edge}" y="${top-12}" text-anchor="${anchor}" font-size="11" fill="currentColor" font-weight="600">${this._esc(unit||group.split(':')[0])}</text>
        ${ticks.map(({p,label})=>`<text x="${edge}" y="${py(p)+4}" text-anchor="${anchor}" font-size="12" fill="currentColor">${this._esc(label)}</text>`).join('')}
      </g>`;
    }).join('');
    const instrumentLanes=instrumentGroups.map(group=>{
      const member=instrumentMetrics.find(m=>lbHistoryAxisGroup(m.key,m.unit)===group);
      const {side,origin}=slot(group);
      const axis=groupAxes.get(group);
      const position=origin+(side==='right'?1:1);
      const upper=Number.isFinite(member.high),lower=Number.isFinite(member.low);
      const greenTop=upper?py(upper&&lower?.38:.40):py(.04);
      const greenBottom=lower?py(.72):py(.95);
      return `<rect data-instrument-lane="${this._esc(group)}" x="${position}" y="${greenTop}" width="5" height="${Math.max(1,greenBottom-greenTop)}" rx="2" fill="#29a662" fill-opacity=".82"/>`;
    }).join('');
    const instrumentMarkers=instrumentMetrics.map((m,i)=>{
      const group=lbHistoryAxisGroup(m.key,m.unit);
      const {side,origin}=slot(group),axis=groupAxes.get(group);
      const ownIndex=instrumentMetrics.filter(other=>lbHistoryAxisGroup(other.key,other.unit)===group).findIndex(item=>item.key===m.key);
      const position=origin+3.5+Math.min(ownIndex*5,Math.max(0,axisWidth-12));
      const point=this._atOrBefore(this._series.get(m.key)||[],at);
      const visible=point&&Number.isFinite(point.v);
      const vertical=visible?py(axis.y(point.v)):top;
      return `<circle data-axis-marker="${this._esc(m.key)}" cx="${position}" cy="${vertical}" r="4.5" fill="#fff" stroke="${this._esc(this._color(m.key,i))}" stroke-width="2" ${visible?'':'visibility="hidden"'}/>`;
    }).join('');
    const cursorX=x(Number.isFinite(at)?at:finish); const decision=this._historicalDecision(at);
    const strips=this._statusStrips(plotLeft,plotRight);
    const statusLane=`<g data-room-status-row><text x="${plotLeft}" y="18" font-size="12" font-weight="600" fill="currentColor">${this._esc(t('roomStatus'))}</text>
      <line x1="${plotLeft}" y1="50" x2="${plotRight}" y2="50" stroke="var(--divider-color,#666)" stroke-opacity=".7"/></g>`;
    const emptyPlot=n&&!hasSamples?`<text x="${(plotLeft+plotRight)/2}" y="${py(.56)}" text-anchor="middle" font-size="13" fill="currentColor" opacity=".8">${this._esc(t(this._loading?'loading':'nohistory'))}</text>`:'';
    const detailMarkup=this._cursorDetail(entries,at,t);
    this.shadowRoot.innerHTML=`<style>
      ha-card{display:block;padding:16px;color:var(--primary-text-color);}
      h3{margin:0 0 8px;font-size:18px} .hint{color:var(--secondary-text-color);font-size:12px;line-height:1.5}
      .controls{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
      select{background:var(--card-background-color);color:inherit;border:1px solid var(--divider-color);padding:7px;border-radius:8px;font-size:14px}
      .chart-scroll{overflow:hidden;max-width:100%} svg{width:100%;max-width:100%;height:auto;touch-action:pan-y;user-select:none;cursor:crosshair;display:block}
      .line{height:3px;width:16px;display:inline-block;border-radius:3px;flex-shrink:0;background:var(--metric-color)} .line.outside{height:0;border-top:3px dashed var(--metric-color);background:transparent}
      .detail{background:var(--secondary-background-color,var(--ha-card-background));border-radius:9px;padding:10px;margin-top:8px}
      .focus-row{margin:8px 0 6px;display:grid;gap:6px}.focus-label{font-size:12px;color:var(--secondary-text-color)}.focus-buttons{display:flex;gap:5px;flex-wrap:wrap}.focus-buttons button{font:inherit;font-size:12px;color:var(--primary-text-color);background:transparent;border:1px solid var(--divider-color,#666);border-radius:999px;padding:6px 12px;min-height:32px;cursor:pointer}.focus-buttons button[aria-pressed=true]{background:var(--secondary-background-color,#404348);border-color:var(--primary-color,#888);font-weight:600}
      .status{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:13px}.dot{width:9px;height:9px;border-radius:9px;display:inline-block}
      .values{display:flex;gap:6px 16px;flex-wrap:wrap;margin-top:7px}.reading{display:flex;align-items:center;gap:6px;font-size:14px}
      .reading strong{font-variant-numeric:tabular-nums} .status-label{font-weight:600}
      .key{font-size:12px;color:var(--secondary-text-color)}
      @media(max-width:520px){ha-card{padding:12px} h3{font-size:16px}.reading{width:100%;justify-content:space-between}.reading strong{margin-left:auto} }
    </style><ha-card><div class="controls"><h3>${t('title')} · ${this._esc(this._source()?.attributes?.room_name||this._roomName||this._config?.entity||'')}</h3><span class="key" data-range-loading role="status" aria-live="polite"></span><label class="key">${t('period')} · ${this._language()==='de'?'temporär':this._language()==='tr'?'geçici':'temporary'} <select data-range>${[6,24,24*7,24*30].map(h=>`<option value="${h}" ${Number(this._config.hours)===h?'selected':''}>${h<24?h+'h':h===24?'24h':h===168?'7d':'30d'}</option>`).join('')}</select></label></div>
    ${n?`${focusButtons}<div class="chart-scroll"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${t('title')}" data-chart>
      ${statusLane}${strips}${topZone}${bottomZone}${guides}${instrumentLanes}${axes}${lines}${axisTicks}${instrumentMarkers}${emptyPlot}<line x1="${cursorX}" x2="${cursorX}" y1="24" y2="${bottom}" stroke="var(--primary-text-color)" stroke-dasharray="3 3" stroke-width="1.4" data-cursor-line/>
      <rect x="${plotLeft}" y="0" width="${plotRight-plotLeft}" height="${height}" fill="transparent" data-hit/>
      <text x="${plotLeft}" y="${height-11}" font-size="11" fill="currentColor" opacity=".7">${this._esc(this._historyAxisLabel(this._start??Date.now(),this._end??Date.now(),this._config.hours))}</text>
      <text x="${plotRight}" y="${height-11}" font-size="11" fill="currentColor" text-anchor="end" opacity=".7">${this._esc(this._historyAxisLabel(this._end??Date.now(),this._start??Date.now(),this._config.hours))}</text>
      </svg></div>${condensed?`<p class="hint" data-condensed-gaps>${t('condensedGaps')}</p>`:''}${this._outageCondensed?`<p class="hint" data-condensed-outages>${this._esc(this._language()==='de'?'Viele kurze Sensorausfälle wurden entsprechend der Bildschirmauflösung zusammengefasst.':this._language()==='tr'?'Kısa sensör kesintileri ekran çözünürlüğüne göre özetlendi.':'Numerous short sensor outages were condensed to the screen resolution.')}</p>`:''}${this._historyInvalidUnits?`<p class="hint" data-unsupported-units>${t('unsupportedUnits')}</p>`:''}`:`<p class="hint">${t('empty')}</p>`}
      <div class="detail" data-cursor-detail>${detailMarkup}</div>
      <p class="hint">${this._esc(this._notice||t('units'))}${Number(this._config.hours)===720?' · '+t('retention'):''}</p>
      ${this._recorderExcluded?.length ? `<p class="hint" data-recorder-excluded>${this._esc(this._language()==='de'
        ? 'Recorder-Filter schließt folgende Historien-Hilfssensoren aus: '
        : this._language()==='tr'?'Recorder filtresi şu geçmiş sensörlerini hariç tutuyor: '
        : 'Recorder filters exclude these history helpers: ')}${this._esc(this._recorderExcluded.join(', '))}. ${this._esc(this._language()==='de'
        ? 'Bitte Recorder include/exclude in configuration.yaml prüfen. Ohne Freigabe entstehen keine neuen Verlaufspunkte.'
        : this._language()==='tr'?'Recorder include/exclude yapılandırmasını kontrol edin.':'Check Recorder include/exclude configuration; no new history is recorded until allowed.')}</p>`:''}
      ${this._failedHistoryMetrics?.length && !this._historyStoreReadonly && this._hass?.user?.is_admin===true
        ? `<button type="button" data-history-retry ${this._historyRetryBusy?'disabled':''}>${this._language()==='de'?'Aufzeichnung erneut versuchen':this._language()==='tr'?'Kaydı yeniden dene':'Retry history recording'}</button>` : ''}
      </ha-card>`;
    this.shadowRoot.querySelector('[data-history-retry]')?.addEventListener('click',()=>this._retryHistoryRecording());
    this.shadowRoot.querySelectorAll('[data-history-focus]').forEach(button=>button.addEventListener('click',()=>{
      this._focusFamily=button.getAttribute('data-history-focus')||null;
      // Only opacity and pressed state change. Keep the SVG, marker position,
      // expanded tools and current cursor DOM mounted; avoid a full re-render.
      for(const control of this.shadowRoot.querySelectorAll('[data-history-focus]')){
        control.setAttribute('aria-pressed',String((control.getAttribute('data-history-focus')||null)===this._focusFamily));
      }
      for(const curve of this.shadowRoot.querySelectorAll('[data-history-curve]')){
        const key=curve.getAttribute('data-history-curve');
        curve.setAttribute('opacity',String(this._focusFamily && lbHistoryFocusFamily(key)!==this._focusFamily ? .12 : 1));
      }
    }));
    const hit=this.shadowRoot.querySelector('[data-hit]');
    const updateAt=(clientX,rect)=>{
      if(!Number.isFinite(this._start)||!Number.isFinite(this._end) ||
          !Number.isFinite(clientX)||!Number.isFinite(rect?.width))return;
      const frac=Math.max(0,Math.min(1,(clientX-rect.left)/Math.max(1,rect.width)));
      this._selectCursor(this._start+frac*(this._end-this._start));
      // Move cursor and refresh only the small readout, not thousands of SVG
      // paths or the cached status strip on every pointer movement.
      const cursor=this.shadowRoot.querySelector('[data-cursor-line]');
      if(cursor){
        const x=plotLeft+frac*(plotRight-plotLeft);
        cursor.setAttribute('x1',x);cursor.setAttribute('x2',x);
      }
      for(const marker of this.shadowRoot.querySelectorAll('[data-axis-marker]')){
        const key=marker.getAttribute('data-axis-marker');
        const metric=instrumentMetrics.find(item=>item.key===key);
        if(!metric)continue;
        const point=this._atOrBefore(this._series.get(key)||[],this._cursor);
        const axis=groupAxes.get(lbHistoryAxisGroup(key,metric.unit));
        if(!point||!Number.isFinite(point.v)||!axis){marker.setAttribute('visibility','hidden');continue;}
        marker.setAttribute('cy',py(axis.y(point.v)));
        marker.removeAttribute('visibility');
      }
      const detail=this.shadowRoot.querySelector('[data-cursor-detail]');
      if(detail)detail.innerHTML=this._cursorDetail(entries,this._cursor,t);
    };
    hit?.addEventListener('pointerdown',e=>{
      if(!Number.isFinite(this._start)||!Number.isFinite(this._end))return;
      this._pointerDragging=true;
      try{hit.setPointerCapture?.(e.pointerId);}catch(_error){/* detached DOM */}
      updateAt(e.clientX,hit.getBoundingClientRect());
    });
    hit?.addEventListener('pointermove',e=>{
      if(!Number.isFinite(this._start)||!Number.isFinite(this._end))return;
      if(this._pointerDragging || (e.pointerType==='mouse'&&e.buttons===0))
        updateAt(e.clientX,hit.getBoundingClientRect());
    });
    const release=e=>{
      this._pointerDragging=false;
      // The idle period starts after the finger/mouse has been released, too.
      if(Number.isFinite(this._cursor))this._selectCursor(this._cursor);
      try{if(hit.hasPointerCapture?.(e.pointerId))hit.releasePointerCapture(e.pointerId);}catch(_error){}
      if(this._deferredRender)this._render();
    };
    hit?.addEventListener('pointerup',release);
    hit?.addEventListener('pointercancel',release);
    this.shadowRoot.querySelector('[data-range]')?.addEventListener('change',e=>{
      this._config={...this._config,hours:Number(e.target.value)};
      this._configRevision++; // discard obsolete pending requests for the old range
      const loadingLabel=this.shadowRoot.querySelector('[data-range-loading]');
      if(loadingLabel)loadingLabel.textContent=this._language()==='de'?'Lade Zeitraum …':
        this._language()==='tr'?'Dönem yükleniyor …':'Loading period …';
      this._emptyHistoryRetryCount=0;
      clearTimeout(this._cursorIdleTimer);this._cursorIdleTimer=null;
      this._cursor=null;
      this._notice=null;
      // Preserve the native select while a request is pending; avoid replacing
      // its DOM with stale SVG/data from the previous range mid-interaction.
      this._refresh();
    });
    this.shadowRoot.querySelector('[data-range]')?.addEventListener('blur',()=>{
      if(this._deferredRender){this._deferredRender=false;this._render();}
    });
  }
}
if(!customElements.get('lueftungsberater-history-card')){
  customElements.define('lueftungsberater-history-card',LueftungsberaterHistoryCard);
}
window.customCards=window.customCards||[];
if(!window.customCards.some(c=>c.type==='lueftungsberater-history-card')){
  window.customCards.push({type:'lueftungsberater-history-card',name:'Lüftungsassistent – Historie',description:'Messverläufe, dynamische Grenzbereiche und aufgezeichnete Entscheidungen.',preview:true});
}

class LueftungsberaterHistoryCardEditor extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});this._availableMetrics=[];this._availableRoom=null;this._availableSignature=null;this._loadingRoom=null;this._loadingSignature=null;this._metricsRequestId=0;this._rooms=null;this._roomsRequested=false;this._roomsRequestFailed=false;this._roomsLastRequest=0;this._roomsTimer=null;this._editorInstance=null;}
  setConfig(c){
    const previous=this._config?.entity;
    const oldSignature=JSON.stringify(this._config||{});
    const {perspective:_legacyPerspective,...next}=c||{};
    this._config=next;
    if(previous!==next.entity)this._editorInstance=null;
    if(oldSignature!==JSON.stringify(next))this._render();
  }
  set hass(h){
    this._hass=h;this._loadRooms();
    // Only configured-source/availability changes need a new editor render.
    // Repeated sensor measurement updates do not destroy an open color picker.
    const signature=this._metricsSignature(this._config?.entity||'');
    const changed=signature!==this._editorStateSignature;
    this._editorStateSignature=signature;
    if(changed || !this.shadowRoot?.querySelector?.('[data-entity]'))this._render();
  }
  connectedCallback(){
    if(!this._focusListener){
      this._focusListener=()=>{
        if(this._pendingEditorRender){
          this._pendingEditorRender=false;
          setTimeout(()=>this._render(),0);
        }
      };
      this.shadowRoot.addEventListener?.('focusout',this._focusListener);
    }
    // Config subentries do not necessarily emit a state change (e.g. a new
    // room whose advisor is still unavailable). Refresh while editor is open.
    if(!this._roomsTimer)this._roomsTimer=setInterval(()=>this._loadRooms(),20000);
    this._loadRooms();
  }
  disconnectedCallback(){
    if(this._roomsTimer)clearInterval(this._roomsTimer);
    this._roomsTimer=null;
    if(this._focusListener){
      this.shadowRoot.removeEventListener?.('focusout',this._focusListener);
      this._focusListener=null;
    }
  }
  _loadRooms(){
    // Retry after transient WS failures; throttle normal HA state updates.
    // Never make a new backend request on every editor render/keystroke.
    if(this._roomsRequested||!this._hass?.callWS)return;
    const now=Date.now();
    const minInterval=this._roomsRequestFailed?5000:20000;
    if(this._roomsLastRequest && now-this._roomsLastRequest<minInterval)return;
    this._roomsRequested=true;
    this._roomsLastRequest=now;
    this._hass.callWS({type:'lueftungsberater/history_rooms'})
      .then(rooms=>{
        if(!Array.isArray(rooms))throw new Error('Invalid history room list');
        this._roomsRequestFailed=false;
        const changed=JSON.stringify(this._rooms)!==JSON.stringify(rooms);
        this._rooms=rooms;
        if(changed)this._render();
      })
      .catch(()=>{
        this._roomsRequestFailed=true;
        // Keep the previous list during reload. Only use live-state fallback
        // when no authoritative list has ever been fetched.
        if(!Array.isArray(this._rooms))this._render();
      })
      .finally(()=>{this._roomsRequested=false;});
  }
  _metricsSignature(entity){
    // Backend availability depends on configured sources, the presence of
    // advisor measurements, and air-quality value names; not every reading.
    // Avoid a WS request on every sensor state update or editor keystroke.
    const attrs=this._hass?.states?.[entity]?.attributes||{};
    const sources=Object.keys(attrs).filter(key=>key.startsWith('source_')).sort().map(key=>[key,attrs[key]]);
    const values=['co2_ppm','outdoor_co2_ppm','temperature_inside','temperature_outside',
      'humidity_inside','humidity_outside','target_temperature','surface_temperature',
      'surface_relative_humidity','absolute_humidity_difference','absolute_humidity_inside',
      'absolute_humidity_outside','wind_speed_kmh','wind_gust_kmh'];
    const availability=values.map(key=>attrs[key]!=null);
    const air=(key)=>Object.keys(attrs[key]||{}).sort();
    return JSON.stringify([entity,attrs.has_co2===true,sources,availability,
      air('indoor_air_quality_values'),air('air_quality_values')]);
  }
  _loadAvailableMetrics(entity,signature){
    if(!entity || !this._hass?.callWS ||
      (this._loadingRoom===entity && this._loadingSignature===signature) ||
      (this._availableRoom===entity && this._availableSignature===signature))return;
    this._loadingRoom=entity;
    this._loadingSignature=signature;
    const requestId=++this._metricsRequestId;
    this._hass.callWS({type:'lueftungsberater/history_metrics',entity})
      .then(metrics=>{
        if(requestId!==this._metricsRequestId)return;
        this._availableMetrics=Array.isArray(metrics)?metrics:[];
        this._availableRoom=entity;
        this._availableSignature=signature;
        if((this._config?.entity||'')===entity && this._metricsSignature(entity)===signature)this._render();
      })
      .catch(()=>{ /* Keep the conservative fallback until HA responds. */ })
      .finally(()=>{
        if(requestId===this._metricsRequestId){this._loadingRoom=null;this._loadingSignature=null;}
      });
  }
  _changed(patch){const next={...this._config,...patch};this._config=next;const e=new Event('config-changed',{bubbles:true,composed:true});e.detail={config:next};this.dispatchEvent(e);}
  _render(force=false){if(!this._config||!this._hass)return;
    const focusedControl=this.shadowRoot?.activeElement;
    if(!force && focusedControl &&
        (focusedControl.matches?.('input[type=color]') || focusedControl.matches?.('select'))){
      this._pendingEditorRender=true;
      return;
    }
    this._pendingEditorRender=false;
    const liveAdvisors=Object.values(this._hass.states||{}).filter(s=>s.entity_id?.startsWith('sensor.')&&s.attributes?.instance_id&&s.attributes?.room_name&&s.attributes?.recommendation_key);
    const advisors=Array.isArray(this._rooms)
      ?this._rooms.map(room=>({
        entity_id:room.entity||'',instance_id:room.instance_id||'',
        instance_name:room.instance_name||'',room_id:room.room_id||'',
        room_name:room.room_name||'',available:room.available!==false,
      }))
      :liveAdvisors.map(s=>({entity_id:s.entity_id,instance_id:s.attributes.instance_id,
        instance_name:s.attributes.instance_name||s.attributes.instance_id,
        room_name:s.attributes.room_name,available:!['unknown','unavailable'].includes(s.state)}));
    // Never let an unavailable room disappear merely because its live advisor
    // attributes could not be produced. The backend list is authoritative.
    const instances=[...new Map(advisors.map(a=>[a.instance_id,a.instance_name])).entries()];
    const configured=this._config.entity||'';
    const configuredInstance=advisors.find(a=>a.entity_id===configured)?.instance_id;
    const instance=this._editorInstance||configuredInstance||instances[0]?.[0]||'';
    const instanceRooms=advisors.filter(a=>a.instance_id===instance);
    const selected=configured&&instanceRooms.some(a=>a.entity_id===configured)
      ?configured:(instanceRooms.find(a=>a.entity_id)?.entity_id||'');
    if(!this._config.entity&&selected && (Array.isArray(this._rooms)||this._roomsRequestFailed||!this._hass?.callWS)){
      this._changed({entity:selected});this._render();return;
    }
    const attrs=this._hass.states?.[selected]?.attributes||{};
    const known=[['co2_in','CO₂ innen'],['co2_out','CO₂ außen'],['temp_in','Temperatur innen'],['temp_out','Temperatur außen'],['humidity_in','Luftfeuchte innen'],['humidity_out','Luftfeuchte außen'],['pm25_in','PM2,5 innen'],['pm25_out','PM2,5 außen'],['pm10_in','PM10 innen'],['pm10_out','PM10 außen'],['no2_in','NO₂ innen'],['no2_out','NO₂ außen'],['o3_out','Ozon außen'],['voc_in','TVOC innen'],['voc_out','TVOC außen'],['hcho_in','Formaldehyd innen'],['target_temp','Solltemperatur'],['surface_temp','Oberflächentemperatur'],['surface_humidity','Oberflächenfeuchte'],['absolute_delta','Feuchtedifferenz'],['absolute_in','Absolute Feuchte innen'],['absolute_out','Absolute Feuchte außen'],['wind_out','Wind außen'],['gust_out','Böen außen']];
    const signature=this._metricsSignature(selected);
    this._loadAvailableMetrics(selected,signature);
    const fallbackActive=known.filter(([key])=>{
      const map={co2_in:['source_co2','co2_ppm'],co2_out:['source_outdoor_co2','outdoor_co2_ppm'],temp_in:['source_temperature_inside','temperature_inside'],temp_out:['source_temperature_outside','temperature_outside'],humidity_in:['source_humidity_inside','humidity_inside'],humidity_out:['source_humidity_outside','humidity_outside']};
      if(map[key])return attrs[map[key][0]] || attrs[map[key][1]]!=null;
      const side=key.endsWith('_in')?'inside':'outside';const substance=key.split('_')[0];
      if(['pm25','pm10','no2','o3','voc','hcho'].includes(substance)){
        const prop={pm25:'pm2_5',pm10:'pm10',no2:'no2',o3:'o3',voc:'voc',hcho:'formaldehyde'}[substance];
        return attrs[`source_${substance==='hcho'?'formaldehyde':substance}_${side}`] || (attrs[side==='inside'?'indoor_air_quality_values':'air_quality_values']||{})[prop]!=null;
      }
      const extra={target_temp:'source_target_temperature',surface_temp:'source_surface_temperature',surface_humidity:null,absolute_delta:'source_absolute_humidity_difference',absolute_in:'source_absolute_humidity_inside',absolute_out:'source_absolute_humidity_outside',wind_out:'source_wind_outside',gust_out:'source_gust_outside'};
      return (extra[key] && attrs[extra[key]]) || (key==='surface_humidity' && (
        attrs.surface_relative_humidity!=null || (
          attrs.source_surface_temperature && attrs.source_humidity_inside && attrs.source_temperature_inside
        )
      ));
    });
    const active=this._availableRoom===selected && this._availableSignature===signature
      ? known.filter(([key])=>this._availableMetrics.some(metric=>metric.key===key))
      : fallbackActive;
    const esc=s=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const lang=lbLanguage(this._hass);
    const chosen=Array.isArray(this._config.metrics)?this._config.metrics:[];
    const defaultCurveColor=key=>lbHistoryDefaultColor(key);
    const strings={
      de:['Raum','Ansicht','Innenraum','Lüftung','Kurven und Farben','Nur eingerichtete Werte. Grenzwerte kommen live aus der Integration. Fehlende Aufzeichnungen werden bei erstmaliger Nutzung aktiviert.','Instanz','(aktuell nicht verfügbar)','Noch keine registrierte Raumentität'],
      en:['Room','View','Indoor air','Ventilation','Curves and colors','Only configured measurements. Live thresholds come from the integration. Missing histories start when first used.','Instance','(currently unavailable)','No registered room entity yet'],
      tr:['Oda','Görünüm','İç hava','Havalandırma','Eğriler ve renkler','Yalnızca yapılandırılmış ölçümler. Sınırlar entegrasyondan alınır. Eksik geçmiş kayıtları ilk kullanımda başlatılır.','Kurulum','(şu anda kullanılamıyor)','Henüz kayıtlı oda varlığı yok'],
    }[lang]||[];
    this.shadowRoot.innerHTML=`<style>.editor{display:grid;gap:11px;padding:8px 2px} label{display:flex;align-items:center;gap:9px;font-size:14px;min-height:40px}select{width:100%;background:var(--card-background-color);color:var(--primary-text-color);padding:10px;border:1px solid var(--divider-color);border-radius:8px}input[type=checkbox]{width:18px;height:18px;flex-shrink:0}input[type=color]{width:38px;height:32px;border:0;padding:0;background:none} .metric{display:flex;align-items:center;justify-content:space-between;gap:8px;border-bottom:1px solid var(--divider-color)}.info{font-size:12px;color:var(--secondary-text-color)}</style><div class="editor"><label>${strings[6]}<select data-instance>${instances.map(([id,name])=>`<option value="${esc(id)}" ${id===instance?'selected':''}>${esc(name)}</option>`).join('')}</select></label><label>${strings[0]}<select data-entity>${instanceRooms.map(room=>`<option value="${esc(room.entity_id)}" ${!room.entity_id?'disabled':''} ${room.entity_id&&room.entity_id===selected?'selected':''}>${esc(room.room_name)}${room.available?'':` ${strings[7]}`}${room.entity_id?'':` · ${strings[8]}`}</option>`).join('')}</select></label><label>${lang==='de'?'Standard-Zeitraum':lang==='tr'?'Varsayılan dönem':'Default period'}<select data-default-range>${[6,24,168,720].map(h=>`<option value="${h}" ${Number(this._config.hours||24)===h?'selected':''}>${h===6?'6h':h===24?'24h':h===168?'7d':'30d'}</option>`).join('')}</select></label><strong>${strings[4]}</strong>${active.map(([key,label],index)=>`<div class="metric"><label><input type="checkbox" data-metric="${key}" ${(this._config.metrics||[]).includes(key)?'checked':''}/>${esc(lbHistoryLabel(this._hass,key))}</label><input type="color" aria-label="${esc(lbHistoryLabel(this._hass,key))}" data-color="${key}" value="${/^#[a-f0-9]{6}$/i.test(this._config.colors?.[key]||'')?this._config.colors[key]:defaultCurveColor(key,index)}"/></div>`).join('')}<p class="info">${strings[5]}</p></div>`;
    this.shadowRoot.querySelector('[data-instance]')?.addEventListener('change',e=>{
      this._editorInstance=e.target.value;
      const first=advisors.find(a=>a.instance_id===this._editorInstance&&a.entity_id);
      if(first)this._changed({entity:first.entity_id,metrics:[]});
      this._render(true);
    });
    this.shadowRoot.querySelector('[data-entity]')?.addEventListener('change',e=>{
      if(e.target.value)this._changed({entity:e.target.value,metrics:[]});
    });
    this.shadowRoot.querySelector('[data-default-range]')?.addEventListener('change',e=>this._changed({hours:Number(e.target.value)}));
    this.shadowRoot.querySelectorAll('[data-metric]').forEach(input=>input.addEventListener('change',()=>{
      const chosen=[...this.shadowRoot.querySelectorAll('[data-metric]:checked')].map(n=>n.dataset.metric);
      this._changed({metrics:chosen});
      // New selections can change the available color family. Refresh the swatches
      // immediately so the editor and actual graph never show mismatched defaults.
      this._render(true);
    }));
    this.shadowRoot.querySelectorAll('[data-color]').forEach(input=>input.addEventListener('change',()=>this._changed({colors:{...(this._config.colors||{}),[input.dataset.color]:input.value}})));
  }
}
if(!customElements.get('lueftungsberater-history-card-editor'))customElements.define('lueftungsberater-history-card-editor',LueftungsberaterHistoryCardEditor);
