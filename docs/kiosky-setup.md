# Kiosky einrichten: Updates, Medien, externe API und Home Assistant

Stand: 14. Oktober 2026. Die beschriebenen Funktionen sind in **Kiosky 3.3.1** enthalten; transparente Element-Hintergründe und native CMS-Medien gibt es ab **3.3.0**. Die eigenständige Home-Assistant-Integration hat die Version **1.0.0**.

## 1. Installation und bestehende Installationen aktualisieren

WordPress und TYPO3 enthalten ihre eigene Kiosky-Laufzeit. Für diese Varianten wird kein zusätzlicher Kiosky-Standalone-Server benötigt.

Vor einem Update die Datenbank und Dateien sichern; bei WordPress insbesondere `wp-content/uploads`, bei TYPO3 die FAL-Dateispeicher. Das ist bei der Übernahme bisheriger Kiosky-Medien besonders wichtig.

### WordPress: Update-Zugang einrichten

1. Mit einem Administrator unter **Einstellungen → Kiosky Updates** den GitHub-Zugangstoken hinterlegen und speichern.
2. Im **Kiosky-Backend → Updates → Nach Updates suchen** die aktuelle Version abrufen.
3. Die angebotene Version installieren. Alternativ unter **WordPress → Dashboard → Aktualisierungen → Erneut prüfen** suchen und Kiosky aktualisieren.
4. Nach dem Update im Kiosky-Updatebereich die installierte Version kontrollieren.

Für eine Installation ohne funktionierenden Updater das WordPress-Release-ZIP `kioski-wordpress-3.3.1.zip` unter **Plugins → Installieren → Plugin hochladen** hochladen und das vorhandene Plugin ersetzen. Das Plugin dafür nicht vorher löschen oder deinstallieren.

### Welchen GitHub-Token brauche ich?

Für den Updatezugang einen **Fine-grained personal access token** verwenden.
Die folgenden Schritte gelten für das Eigentümerkonto `soerenelvers`:

1. GitHub öffnen: **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. Einen aussagekräftigen Namen und ein Ablaufdatum wählen.
3. Als **Resource owner** den Eigentümer des Distributionsrepositories auswählen: `soerenelvers`.
4. **Repository access → Only select repositories → kiosky-distribution** wählen.
5. Unter **Repository permissions → Contents: Read-only** setzen. Die obligatorische Metadata-Leseberechtigung bleibt bestehen; Schreibrechte sind nicht erforderlich.
6. Token erzeugen, einmalig kopieren und im WordPress-Updatezugang speichern.

Für andere GitHub-Konten: Das Distributionsrepository ist derzeit öffentlich. Ein eigener Fine-grained-Token mit **Public repositories (read-only)** kann öffentliche Inhalte lesen; dafür das eigene Konto als Resource owner verwenden. Private Repository-Berechtigungen und Schreibrechte sind dafür nicht nötig.

Ist eine Distribution privat, kann ein fremdes persönliches Eigentümerkonto nicht einfach als Resource owner gewählt werden. Fine-grained-Tokens gelten für das eigene Konto oder passende Organisationen; reine Repository-Kollaboratoren unterliegen Einschränkungen. Der Repository-Eigentümer muss dann einen geeigneten Distributionszugang bereitstellen. Ein Token erweitert die eigenen Kontorechte nicht. Bei Organisationen kann eine Freigabe erforderlich sein.

GitHub-Anleitung und aktuelle Einschränkungen: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

Klassische Tokens sind für diese Einrichtung nicht die bevorzugte Wahl. Nach Ablauf oder Widerruf einen neuen eingeschränkten Token hinterlegen. Tokens nicht in Supportnachrichten, Screenshots oder Repositories veröffentlichen.

### Wann erscheint ein WordPress-Update?

WordPress plant Plugin-Updateprüfungen standardmäßig zweimal täglich, ungefähr alle zwölf Stunden. Im Administrationsbereich können zusätzliche Prüfungen stattfinden. WP-Cron wird normalerweise durch Seitenaufrufe gestartet; auf wenig besuchten Websites kann sich eine geplante Prüfung verzögern.

Kiosky speichert eine erfolgreiche Manifest-Abfrage zusätzlich **sechs Stunden** zwischen. Das ist eine Cache-Laufzeit, kein eigener Sechs-Stunden-Zeitplan. **Kiosky → Updates → Nach Updates suchen** verwirft diesen Cache und fragt sofort neu ab. Auch **Dashboard → Aktualisierungen → Erneut prüfen** verwirft den Kiosky-Cache über die WordPress-Update-Hooks.

Das Prüfintervall ist derzeit weder in Kiosky noch in WordPress über eine normale Einstellung veränderbar. Technische Anpassungen sind über WP-Cron beziehungsweise einen serverseitigen Cronjob möglich. **Automatische Installation** ist davon getrennt: Sie lässt sich optional pro Plugin in der WordPress-Pluginverwaltung aktivieren.

Quelle zum WordPress-Zeitplan: https://developer.wordpress.org/reference/functions/wp_schedule_update_checks/

### TYPO3

- **Classic Mode:** Das angebotene `kioski_3.3.1.zip` im Extension Manager hochladen. Kiosky prüft Updates, überschreibt im Classic Mode aber keine laufenden PHP-Dateien per Backend-Updateaktion.
- **Composer:** Das Distributionsrepository konfigurieren, Lesetoken in Composer `auth.json` beziehungsweise `COMPOSER_AUTH` hinterlegen und `casesound/kiosky` aktualisieren. Die TYPO3-Extension-Konfiguration `updateAccessToken` kann den Token für den Backend-Updateweg bereitstellen. Das Backend bietet die Installation erst an, wenn der genaue Stable-Tag auflösbar ist.
- Nach einem Composer-Update `vendor/bin/typo3 extension:setup` und `vendor/bin/typo3 cache:flush` ausführen, sofern der gewählte Updateweg dies nicht bereits übernimmt.
- Das Öffnen des Kiosky-Backends erneuert fehlende oder mehr als 24 Stunden alte Updateprüfungen. Eine zusätzliche regelmäßige Prüfung kann über den Scheduler und `kiosky:update:check` eingerichtet werden.

### Standalone

Im Kiosky-Backend **Updates** öffnen. Für den geschützten Distributionszugang `KIOSKY_UPDATE_MANIFEST_URL` und `KIOSKY_UPDATE_ACCESS_TOKEN` in der Serverkonfiguration setzen. Standardmäßig wird täglich geprüft; automatische Installation und automatischer Neustart müssen ausdrücklich aktiviert werden. Die `.env` und die Datenbank gehören in die Sicherung, auch wenn der Updater sie nicht ersetzt.

## 2. Lauftext mit transparentem Hintergrund

1. Den Slide im Editor öffnen und das **Lauftext-Element** auswählen.
2. Unter **Element-Hintergrund** die Option **Transparent** statt **Farbe** wählen.
3. Den laufenden Text und die Schriftfarbe einstellen, speichern und die Player-Vorschau prüfen.

Der Hintergrund des Elements ist dann transparent; darunterliegende Bilder, Videos und andere Slide-Elemente bleiben sichtbar. Die Transparenz betrifft das Element innerhalb des Slides. Sie macht weder den gesamten Slide noch das Browserfenster transparent. Die Einstellung gilt in Standalone, WordPress und TYPO3.

## 3. Medienverwaltung im CMS

### WordPress

Kiosky verwendet die **WordPress-Mediathek**. Vorhandene Anhänge stehen in der Medienauswahl bereit; neue Uploads werden als WordPress-Anhänge gespeichert und sind dort ebenfalls sichtbar. Es gibt keinen zusätzlichen Kiosky-Medienkatalog. Medienordner werden über eine hierarchische Attachment-Taxonomie zugeordnet.

### TYPO3

Kiosky verwendet **Dateiliste/FAL** und die dortigen Ordner. Es muss ein öffentlicher, beschreibbarer Dateispeicher mit passenden Benutzerrechten und Dateifreigaben verfügbar sein. Kiosky-Metadaten werden an den CMS-Dateien geführt. Der Kiosky-Papierkorbstatus ist zunächst ein Metadatum; endgültiges Löschen entfernt die Datei.

### Bisherige Kiosky-Medien übernehmen

Beim ersten Medienzugriff eines Benutzers mit Bearbeitungsberechtigung werden bisherige Kiosky-Medien in die native CMS-Verwaltung übernommen. Verweise in Slides, Vorlagen und Einstellungen werden angepasst. Bei einem Fehler bleiben Quelldaten für einen erneuten Versuch erhalten. Nicht manuell Quelldateien entfernen, bevor Übernahme und Wiedergabe geprüft wurden.

Die Standalone-Variante behält ihre eigene Medienbibliothek.

## 4. Externe API für Gebäudeautomation und Integrationen

### Eigenen Maschinenzugang anlegen

1. Kiosky als Administrator öffnen.
2. **Schnittstellen → Externe API → API-Zugänge** öffnen.
3. Einen eigenen Zugang mit erkennbarem Namen anlegen, beispielsweise „Home Assistant Stadthalle“.
4. Den **einmal angezeigten Kiosky-API-Schlüssel** sicher speichern.
5. Die angezeigte **externe API-Basisadresse** kopieren.

| Variante | Beispiel für die API-Basisadresse |
| --- | --- |
| Standalone | `https://kiosky.example/api/v1` |
| WordPress | `https://website.example/wp-json/kiosky/v1/control` |
| WordPress ohne sprechende Permalinks | `https://website.example/?rest_route=/kiosky/v1/control` |
| TYPO3 | `https://website.example/kiosky-api/v1` |

Bei einer Installation in einem Unterverzeichnis dieses mit übernehmen. Die in Kiosky angezeigte vollständige Adresse ist maßgeblich.

Die Integration benötigt **keine CMS-Anmeldung**, kein Cookie und keinen WordPress-Nonce. Ein aktiver Maschinenzugang gibt die External Control API frei. Zugänge können einzeln widerrufen werden. Der Schlüssel erlaubt keine Benutzerverwaltung, Medienverwaltung, Einstellungen oder Updates.

### Verbindung prüfen

Für Standalone beziehungsweise WordPress mit sprechenden Permalinks oder TYPO3 den passenden Basiswert einsetzen:

```sh
export KIOSKY_API_BASE='https://website.example/wp-json/kiosky/v1/control'
# KIOSKY_API_KEY vorher sicher als Umgebungsvariable bereitstellen.
curl --fail-with-body "$KIOSKY_API_BASE/displays" \
  --header "Authorization: Bearer $KIOSKY_API_KEY"
```

Alternativ ist `X-API-Key: <Schlüssel>` möglich. Bei der WordPress-Adresse mit `?rest_route=` den Ressourcenpfad **an den rest_route-Wert** anhängen, etwa `?rest_route=/kiosky/v1/control/displays`. Nicht blind hinter eine URL mit Query-Parametern anhängen. Die HACS-Integration übernimmt das automatisch.

Verfügbar sind unter anderem Ressourcenlisten, Kanal-/Slide-Zuweisungen, Presets, Warnungen und Zurücksetzen externer Zuweisungen. Die konkrete Ziel-ID wird über die API ermittelt, nicht aus Namen geraten. Vollständiger Vertrag: `docs/external-api.md` und `docs/openapi.yaml` in der Kiosky-Auslieferung.

- **401:** Schlüssel fehlt, ist ungültig oder wurde widerrufen.
- **403:** Zugriff ist nicht erlaubt.
- **404:** API-Adresse oder Ressourcenpfad prüfen.
- **422:** Anfrageinhalt prüfen, beispielsweise Ziel-ID, Zeitfenster oder Priorität.
- **Verbindungsfehler:** Erreichbarkeit aus dem Automationsnetz und TLS-Zertifikat prüfen. Bei WordPress muss der Webserver den Authorization-Header weiterreichen.

## 5. Home Assistant über HACS einrichten

**Öffentliches Repository:** https://github.com/soerenelvers/hacs-kiosky

Voraussetzungen: **Home Assistant ab 2026.3.0**, HACS und **Kiosky ab 3.3.1**. Die HACS-Integration ist ein eigener Client; Kiosky wird damit nicht auf Home Assistant installiert.

1. In Home Assistant **HACS → ⋮ → Benutzerdefinierte Repositories** öffnen.
2. `https://github.com/soerenelvers/hacs-kiosky` eintragen und Typ **Integration** wählen.
3. **Kiosky** suchen und herunterladen.
4. **Home Assistant neu starten**.
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Kiosky** öffnen.
6. Name, vollständige externe API-Basisadresse und den **in Kiosky erzeugten API-Schlüssel** eingeben.
7. Die Einrichtung prüft Verbindung und Schlüssel. Anschließend stehen die Entitäten und Aktionen bereit.

### Was lässt sich steuern?

- Externen Kanal für einzelne Displays oder Displaygruppen auswählen.
- Gespeicherte Presets über Schaltflächen ausführen.
- Den aktiven Emergency-Warnungsstatus sehen.
- Ressourcen-IDs über Diagnosesensoren für Automationen ablesen.
- In Automationen Kanäle oder Slides zuweisen, Presets ausführen, Warnungen aktivieren/beenden und Zuweisungen entfernen.

Die Kanalwahl zeigt die **direkte externe Zuweisung**, nicht den vollständigen effektiven Player-Zustand. `[Kiosky schedule]` entfernt die direkte externe Zuweisung dieses Ziels und erhält Warnungen. Eine weiterhin gültige Gruppenzuweisung kann ein einzelnes Display danach noch beeinflussen. Bei direkter Slide-Zuweisung ist der Kanalwahlzustand unbekannt.

Der Warnungssensor erfasst die aktive Emergency-Warnung; andere veröffentlichte Webhook-Warnungen werden damit nicht dargestellt. Preset-Schaltflächen verwenden die im Preset gespeicherten Ziele; fehlende Ziele über die Aktion explizit angeben.

### Abfrageintervall und Schlüsselwechsel

Standard: **30 Sekunden**, unter **Geräte & Dienste → Kiosky → Konfigurieren** auf 10–3600 Sekunden einstellbar. Steuerbefehle lösen eine sofortige Statusabfrage aus. Mehrere Kiosky-Installationen sind möglich; in Aktionen dann `config_entry_id` auswählen.

Bei widerrufenem Schlüssel fordert Home Assistant eine erneute Authentifizierung an. Ein neuer Schlüssel kann auch über **Neu konfigurieren** eingetragen werden. Zum Wechsel der API-Adresse die Installation entfernen und mit der neuen Adresse hinzufügen. HACS-Updates herunterladen und danach Home Assistant neu starten.

### Beispiel: Kanal zuweisen

```yaml
action: kiosky.assign_content
data:
  target_type: display
  target_id: DISPLAY_ID
  content_type: channel
  content_id: CHANNEL_ID
  priority: 200
```

### Beispiel: Informationswarnung anzeigen

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

### Beispiel: Direkte Zuweisung entfernen

```yaml
action: kiosky.clear_assignments
data:
  targets:
    - type: display
      id: DISPLAY_ID
```

Vollständige Aktionsfelder, Mehrfachinstallationen und weitere Beispiele: https://github.com/soerenelvers/hacs-kiosky#automationsaktionen

## 6. Die beiden Schlüssel auseinanderhalten

| Zugang | Wird erstellt bei | Wird eingetragen in | Zweck |
| --- | --- | --- | --- |
| GitHub-Update-Token | GitHub → Developer settings → Personal access tokens | WordPress: Einstellungen → Kiosky Updates; TYPO3/Standalone: Updatekonfiguration | Release-Metadaten und Installationspakete laden |
| Kiosky-API-Schlüssel | Kiosky → Schnittstellen → Externe API → API-Zugänge | Home Assistant oder andere externe Integration | Displays, Inhalte, Presets und Warnungen steuern |

Der öffentliche HACS-Repository-Link erfordert keinen eigenen Kiosky-Distributions-Token. HACS verwendet seine reguläre GitHub-Anbindung. Zum Steuern der Kiosky-Installation benötigt die eingerichtete Integration trotzdem ihren eigenen Kiosky-API-Schlüssel.

## 7. Versionen, Releases und Prüfungen

| Version | Änderungen |
| --- | --- |
| Kiosky 3.3.0 | Transparente Element-Hintergründe, native WordPress-/TYPO3-Medien und Übernahme bisheriger Medien |
| Kiosky 3.3.1 | Externe API-Zugänge ohne CMS-Anmeldung in allen Varianten, sofortiger Widerruf und Schutz bei parallelen Zugriffen |
| HACS-Integration 1.0.0 | Home-Assistant-Einrichtung, Entitäten und Automationsaktionen als eigenständiges öffentliches Repository |

Die Kiosky-Pakete wurden mit automatisierten Tests und echten WordPress-/TYPO3-Installations- und Upgradeprüfungen geprüft. Die HACS-Integration wurde mit Home Assistant 2026.3 und 2026.10, HACS und hassfest validiert; direkte HTTP-Steuerung bis zum Player wurde in Standalone, WordPress sowie TYPO3 13/14 geprüft.

Diese Anleitung ergänzt die bestehenden Releases nachträglich. Veröffentlichte Versions-Tags und Installationspakete bleiben unverändert. Ergänzungen an aktuellen Releasebeschreibungen und am veränderlichen Stable-Feed sind als Dokumentationsnachtrag zu verstehen, nicht als neue Programmversion.
