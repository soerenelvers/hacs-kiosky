# Kiosky für Home Assistant

Home-Assistant-Integration für die **Kiosky External Control API**, installierbar über HACS als benutzerdefiniertes Repository.

## Voraussetzungen

- Home Assistant **2026.3.0 oder neuer**, HACS und Kiosky **3.3.1 oder neuer**.
- Die Kiosky-API muss von Home Assistant aus erreichbar sein.
- Einen eigenen Schlüssel unter **Kiosky → Schnittstellen → Externe API → API-Zugänge** erzeugen. Der Schlüssel wird nur einmal angezeigt. **Keinen GitHub-Update-Token verwenden.**

## Installation über HACS

Repository-Adresse: **https://github.com/soerenelvers/hacs-kiosky**

1. In Home Assistant **HACS → ⋮ → Benutzerdefinierte Repositories** öffnen.
2. Die Repository-Adresse eingeben, Typ **Integration** wählen und hinzufügen.
3. Nach **Kiosky** suchen und herunterladen.
4. **Home Assistant neu starten**.
5. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen → Kiosky** Name, externe API-Basisadresse und Kiosky-API-Schlüssel eingeben.

Die Einrichtung prüft die Verbindung und den Schlüssel. Standalone, WordPress und TYPO3 werden unterstützt:

| Installation | Beispiel für die API-Basisadresse |
| --- | --- |
| Standalone | `https://kiosky.example/api/v1` |
| WordPress | `https://website.example/wp-json/kiosky/v1/control` |
| TYPO3 | `https://website.example/kiosky-api/v1` |
| WordPress ohne sprechende Permalinks | `https://website.example/?rest_route=/kiosky/v1/control` |

Die **in Kiosky angezeigte externe API-Adresse** vollständig übernehmen, einschließlich eines Installations-Unterverzeichnisses. Nicht die Player- oder Backend-Adresse eingeben. HTTPS mit gültigem Zertifikat verwenden; HTTP wird für lokale Netze unterstützt. Weiterleitungen werden aus Sicherheitsgründen nicht verfolgt: die endgültige API-Adresse eintragen.

## Entitäten und Bedienung

- **Displays und Displaygruppen:** Auswahl eines extern zugewiesenen Kanals. `[Kiosky schedule]` entfernt die direkten externen Zuweisungen dieses Ziels, ohne Warnungen zu beenden. Ein Display kann danach weiterhin den externen Kanal seiner Gruppe übernehmen. Die Auswahl zeigt die direkte externe Zuweisung, nicht den vollständigen effektiven Player-Zustand. Bei einer direkten Slide-Zuweisung ist die Kanalwahl unbekannt.
- **Presets:** Eine Schaltfläche pro Preset führt dessen gespeicherte Ziele und Einstellungen aus. Presets ohne gespeicherte Ziele über die Aktion `execute_preset` mit expliziten Zielen ausführen.
- **Warnung aktiv:** Binärsensor mit Typ, Titel und Zielen der aktiven Emergency-Warnung. Andere veröffentlichte Webhook-Warnungen werden damit nicht erfasst.
- **Diagnosesensoren:** Anzahl sowie Namen/IDs von Displays, Gruppen, Kanälen, Slides und Presets. Damit stehen die benötigten IDs für Automationen bereit; Player-Schlüssel werden nicht als Attribute veröffentlicht.

Neue Displays, Gruppen und Presets werden beim nächsten Abruf automatisch hinzugefügt. Gelöschte Ressourcen werden nicht verfügbar und können über die Home-Assistant-Entitätsverwaltung entfernt werden.

Standardmäßig wird alle **30 Sekunden** abgefragt. Unter **Einstellungen → Geräte & Dienste → Kiosky → Konfigurieren** lässt sich das Intervall zwischen 10 und 3600 Sekunden einstellen. Nach Steuerbefehlen wird der Zustand direkt neu abgefragt. Mehrere Kiosky-Installationen sind möglich.

## Automationsaktionen

Unter **Entwicklerwerkzeuge → Aktionen** und in Automationen stehen bereit:

| Aktion | Funktion |
| --- | --- |
| `kiosky.assign_content` | Kanal oder Slide an Display, Gruppe, Matrix, Standort oder global zuweisen; optional mit Priorität und Zeitfenster |
| `kiosky.clear_assignments` | Externe Zuweisungen der angegebenen Ziele entfernen; Warnungen bleiben bestehen |
| `kiosky.execute_preset` | Preset ausführen; optional Ziele, Kanal, Warnung oder Zeitfenster überschreiben |
| `kiosky.activate_emergency` | Warnung aktivieren; ersetzt die bisherige aktive Emergency-Warnung |
| `kiosky.end_emergency` | Aktive Emergency-Warnung systemweit beenden |
| `kiosky.refresh` | Sofort neu abfragen |

Bei genau einer geladenen Installation ist `config_entry_id` optional. Bei mehreren Installationen im Aktionsdialog die gewünschte Kiosky-Installation auswählen.

### Kanal zuweisen

```yaml
action: kiosky.assign_content
data:
  target_type: display
  target_id: DISPLAY_ID
  content_type: channel
  content_id: CHANNEL_ID
  priority: 200
  expires_at: "2026-12-01T23:00:00+01:00"
```

### Warnung anzeigen

```yaml
action: kiosky.activate_emergency
data:
  warning_type: information
  title: "Veranstaltung beendet"
  instructions: "Bitte nutzen Sie den Hauptausgang."
  targets:
    - type: group
      id: GROUP_ID
```

### Externe Zuweisung zurücksetzen

```yaml
action: kiosky.clear_assignments
data:
  targets:
    - type: display
      id: DISPLAY_ID
```

Für ein globales Ziel immer `type: global` und `id: global` verwenden. IDs aus den Kiosky-Ressourcensensoren übernehmen.

## Schlüsselwechsel und Fehlerbehebung

Bei widerrufenem oder ungültigem Schlüssel fordert Home Assistant eine erneute Authentifizierung an. Ein neuer Schlüssel kann auch über **Neu konfigurieren** eingetragen werden. Eine andere Serveradresse als neue Installation hinzufügen.

- **Keine Verbindung:** API-Adresse, Erreichbarkeit aus Home Assistant, TLS-Zertifikat und Kiosky-Version prüfen. Bei WordPress muss der Webserver den Authorization-Header weiterreichen.
- **Schlüssel abgewiesen:** Einen Kiosky-API-Zugang verwenden, keine WordPress-Anmeldedaten und keinen GitHub-Token.
- **Preset schlägt fehl:** Ziele im Kiosky-Preset speichern oder über die Aktion mitgeben.
- **Update:** Über HACS herunterladen und Home Assistant neu starten.

HTTP-Aufrufe sind asynchron und zeitlich begrenzt. Schreibbefehle werden bei Verbindungsfehlern nicht automatisch wiederholt. Geheimnisse und API-Antwortkörper werden nicht in Fehlermeldungen übernommen.

## Entwicklung

Python 3.14 und eine virtuelle Umgebung verwenden:

```sh
pip install -r requirements-test.txt
ruff check .
ruff format --check .
pytest -q
```

CI prüft Home-Assistant-Einrichtung, Entitäten, Aktionen und HTTP-Verhalten sowie die HACS-Struktur. Die Integration besitzt eine eigene Versionsnummer, unabhängig von der Kiosky-Serverversion.

## Lizenz

Copyright © 2026 Sören Elvers. Diese eigenständige Home-Assistant-Integration wird unter der MIT-Lizenz veröffentlicht. Die Lizenz des Kiosky-Servers wird dadurch nicht geändert.
