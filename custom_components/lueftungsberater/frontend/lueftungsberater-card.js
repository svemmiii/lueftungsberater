const LB_NNBSP = "\u202F";

const LB_I18N = {
  de: {
    "recommendation.open_now": "Jetzt lüften",
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
    const warningNotice = !this._config.remote_stale && a.warning_notice_kind === "all_clear"
      ? [lbT(this._hass, "warning.all_clear"), a.warning_notice_text].filter(Boolean).join(": ")
      : "";
    const title = this._config.name || a.room_name || a.friendly_name || "Lüftungsassistent";
    const expanded = this._isExpanded();
    const hardLock = a.safety_lock === true || status === "locked";
    const showToggle = this._config.force_expanded !== true;
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

    if (ti !== null || ta !== null) {
      const parts = [
        ...(ti !== null ? [this._metric(
          lbT(this._hass, "metric.inside", { value: this._valueUnit(ti, tempUnit) }),
          a.source_temperature_inside,
          lbT(this._hass, "metric.indoor_temperature_open")
        )] : []),
        ...(ta !== null ? [this._metric(
          `${lbT(this._hass, "metric.outside", { value: this._valueUnit(ta, tempUnit) })}${this._fallbackSuffix(a.outdoor_temperature_source)}`,
          a.source_temperature_outside,
          lbT(this._hass, "metric.outdoor_temperature_open")
        )] : []),
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

    if (hi !== null || ho !== null) {
      const rh = [
        ...(hi !== null ? [this._metric(
          lbT(this._hass, "metric.inside", { value: this._valueUnit(hi, "%") }),
          a.source_humidity_inside,
          lbT(this._hass, "metric.indoor_humidity_open")
        )] : []),
        ...(ho !== null ? [this._metric(
          `${lbT(this._hass, "metric.outside", { value: this._valueUnit(ho, "%") })}${this._fallbackSuffix(a.outdoor_humidity_source)}`,
          a.source_humidity_outside,
          lbT(this._hass, "metric.outdoor_humidity_open")
        )] : []),
      ];
      let html = `${lbT(this._hass, "metric.humidity")}: ${rh.join(" · ")}`;
      if (ahi !== null || aho !== null) {
        const absoluteParts = [];
        if (ahi !== null) absoluteParts.push(this._metric(
          lbT(this._hass, "metric.inside", { value: this._valueUnit(ahi, "g/m³") }),
          a.source_absolute_humidity_inside,
          lbT(this._hass, "metric.absolute_humidity_open")
        ));
        if (aho !== null) absoluteParts.push(this._metric(
          lbT(this._hass, "metric.outside", { value: this._valueUnit(aho, "g/m³") }),
          a.source_absolute_humidity_outside,
          lbT(this._hass, "metric.absolute_humidity_outdoor_open")
        ));
        html += ` · ${absoluteParts.join(" · ")}`;
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

    const indoorAir = a.indoor_air_quality_values || {};
    const outdoorAir = a.air_quality_values || {};
    const airParts = [];
    const addAirMetric = (key, labelKey, unit, sourceIn, sourceOut = null) => {
      const insideValue = this._fmt(indoorAir[key]);
      const outsideValue = this._fmt(outdoorAir[key]);
      if (insideValue === null && outsideValue === null) return;
      const parts = [];
      if (insideValue !== null) parts.push(this._metric(
        lbT(this._hass, "metric.inside", { value: this._valueUnit(insideValue, unit) }),
        sourceIn,
        lbT(this._hass, "history_open")
      ));
      if (outsideValue !== null) parts.push(this._metric(
        lbT(this._hass, "metric.outside", { value: this._valueUnit(outsideValue, unit) }),
        sourceOut,
        lbT(this._hass, "history_open")
      ));
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
      if (!inside && !outside) return;
      const display = (item) => item.kind === "index"
        ? lbT(this._hass, "metric.index_value", { value: item.value })
        : this._valueUnit(item.value, item.unit);
      const parts = [];
      if (inside) parts.push(this._metric(
        lbT(this._hass, "metric.inside", { value: display(inside) }),
        sourceIn,
        lbT(this._hass, "history_open")
      ));
      if (outside) parts.push(this._metric(
        lbT(this._hass, "metric.outside", { value: display(outside) }),
        sourceOut,
        lbT(this._hass, "history_open")
      ));
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
    const showDuration = Boolean(durationText) && a.duration_key !== "not_needed";
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
        <div class="header ${meta.cls}${remote ? "" : " main-tap"}" ${remote ? "" : 'tabindex="0" role="button"'}>
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
    const locValue = (value, unit = "", source = null) => {
      const n = this._fmt(value);
      return n === null ? lbT(this._hass, "metric.unavailable") : this._metric(this._valueUnit(n, unit), source, lbT(this._hass, "history_open"));
    };
    const air = (side, choices, source) => {
      const found = lbAirValue(a, side, choices);
      if (!found) return lbT(this._hass, "metric.unavailable");
      const text = found.index ? lbT(this._hass, "metric.index_value", {value: this._fmt(found.value)}) : this._valueUnit(this._fmt(found.value), found.unit);
      return this._metric(text, a[source], lbT(this._hass, "history_open"));
    };
    const values = {
      last_airing: this._metric(this._airingDateLabel(a.last_confirmed_airing), a.source_last_airing, lbT(this._hass, "airing.history")),
      target: locValue(this._displayTemperature(a.target_temperature, tempUnit), tempUnit, a.source_target_temperature),
      humidity_delta: locValue(a.absolute_humidity_difference, "g/m³", a.source_absolute_humidity_difference),
      window_state: a.window_data_status === "unavailable" ? lbT(this._hass,"metric.unavailable") : (a.window_open ? lbT(this._hass,"window.open") : lbT(this._hass,"recommendation.keep_closed")),
      temp_in: locValue(this._displayTemperature(a.temperature_inside,tempUnit),tempUnit,a.source_temperature_inside),
      temp_out: locValue(this._displayTemperature(a.temperature_outside,tempUnit),tempUnit,a.source_temperature_outside),
      humidity_in: locValue(a.humidity_inside,"%",a.source_humidity_inside),
      humidity_out: locValue(a.humidity_outside,"%",a.source_humidity_outside),
      absolute_in: locValue(a.absolute_humidity_inside,"g/m³",a.source_absolute_humidity_inside),
      absolute_out: locValue(a.absolute_humidity_outside,"g/m³",a.source_absolute_humidity_outside),
      co2_in: (a.has_co2 === true && this._fmt(a.co2_ppm,0) === null)
        ? this._metric(lbT(this._hass,"co2.unavailable"),a.source_co2,lbT(this._hass,"co2.open"))
        : this._fmt(a.co2_ppm,0) === null ? lbT(this._hass,"metric.unavailable")
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
        .lb-editor-display label { display:grid; gap:5px; font-size:13px; }
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
        .lb-editor-display label { display:grid; gap:5px; font-size:13px; }
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
