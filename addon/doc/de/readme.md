# Benutzerdefinierte Beschriftungen

* Autor: Kefas Lungu

Hinweis: Dieses Add‑on erfordert NVDA 2025.1 oder neuer.

## Überblick

Dies ist ein Add‑on, mit dem Sie benutzerdefinierte **Beschriftungen** für unbeschriftete Steuerelemente hinzufügen und bestehende bearbeiten können. Das ist besonders nützlich in Anwendungen, deren Schaltflächen oder Steuerelemente keine Beschriftung haben oder von NVDA nicht korrekt erkannt werden.

## Funktionen

* Benutzerdefinierte **Beschriftungen** für unbeschriftete Steuerelemente vergeben.
* Vorhandene **Beschriftungen** bearbeiten.
* **Beschriftungen** entfernen, wenn sie nicht mehr benötigt werden.
* Alle **Beschriftungen** über ein Einstellungsfenster verwalten.
* **Beschriftungen** werden pro Anwendung gespeichert, um Ordnung zu schaffen und Export/Import zu ermöglichen.
* Option, automatisch die Beschreibung eines Steuerelements zu sprechen, wenn keine Beschriftung vorhanden ist.

## Unterstützte Steuerelementtypen

Die folgenden Steuerelemente können beschriftet werden:

* Schaltflächen  
* Menüschaltflächen  
* Umschaltflächen  
* Kontrollkästchen  
* Optionsfelder  
* Kombinationsfelder  
* Schieberegler  
* Registerkarten  
* Menüeinträge  
* Editierbare Texte  

## Tastengesten

* NVDA+Strg+L: Eine benutzerdefinierte **Beschriftung** für das aktuelle Steuerelement setzen oder bearbeiten  
* NVDA+Strg+Entf: Die benutzerdefinierte **Beschriftung** des aktuellen Steuerelements entfernen  
* NVDA+Strg+J: Prüfen, ob das aktuelle Steuerelement eine benutzerdefinierte **Beschriftung** hat  
* NVDA+Strg+; (Semikolon): Einstellungen öffnen  

## Verwendung

### Eine benutzerdefinierte Beschriftung setzen

1. Setzen  Sie den Fokus auf das Steuerelement, das Sie beschriften möchten.  
2. Drücken Sie NVDA+Strg+L.  
3. Ein Dialog erscheint und zeigt Informationen über das Steuerelement.  
4. Geben Sie die gewünschte **Beschriftung** in das Textfeld ein.  
5. Drücken Sie OK, um die Beschriftung zu speichern.  

### Eine bestehende Beschriftung bearbeiten

1. Setzen Sie den Fokus auf ein Steuerelement, das bereits eine benutzerdefinierte **Beschriftung** hat.  
2. Drücken Sie NVDA+Strg+L.  
3. Bearbeiten Sie die **Beschriftung** im Textfeld.  
4. Drücken Sie OK, um die Änderungen zu speichern.  

### Eine Beschriftung entfernen

Sie können eine **Beschriftung** auf zwei Arten entfernen:

1. Setzen Sie den Fokus auf das Steuerelement und drücken Sie NVDA+Strg+Entf.  
2. Oder öffnen Sie den Beschriftungsdialog (NVDA+Strg+L) und drücken Sie die Schaltfläche „Entfernen“.  

### Alle Beschriftungen verwalten

1. Drücken Sie NVDA+Strg+;, um das Einstellungsfenster  zu öffnen.  
2. Durchsuchen Sie die **Beschriftungen**, sortiert nach Anwendung.  
3. Verwenden Sie die Schaltflächen Bearbeiten, Entfernen, App entfernen oder Alle entfernen.  

## Einstellungsfenster

Das Einstellungsfenster erreichen Sie über:

* Die Tastenkombination NVDA+Strg+;  
* NVDA‑Menü > Optionen > Einstellungen > Benutzerdefinierte Beschriftungen 

Das Fenster zeigt alle benutzerdefinierten **Beschriftungen** in einer Baumansicht nach Anwendung sortiert. Sie können:

* Bearbeiten — die ausgewählte **Beschriftung** ändern  
* Entfernen — die ausgewählte **Beschriftung** löschen  
* App entfernen — alle **Beschriftungen** der ausgewählten Anwendung löschen  
* Alle entfernen — sämtliche benutzerdefinierten **Beschriftungen** löschen  

Zusätzlich gibt es eine Einstellung, die es erlaubt, die Beschreibung eines Steuerelements als **Beschriftung** zu verwenden, wenn das Steuerelement keine eigene Beschriftung hat. Beachten Sie jedoch: Wenn eine benutzerdefinierte **Beschriftung** gesetzt wurde, überschreibt diese sowohl die Beschreibung als auch die ursprüngliche Beschriftung des Steuerelements.

## Speicherung

**Beschriftungen** werden als JSON‑Dateien im NVDA‑Konfigurationsverzeichnis im Ordner `customLabels` gespeichert. Jede Anwendung hat ihre eigene JSON‑Datei, was das Sichern oder Teilen von **Beschriftungen** für bestimmte Anwendungen erleichtert.

## Bekannte Einschränkungen

* **Webbasierte Anwendungen:** Bei Anwendungen, die auf Webtechnologien basieren (z. B. neues Outlook, Microsoft Teams, Slack, TeamViewer, WhatsApp, Discord und andere Electron/WebView2‑Apps), funktionieren benutzerdefinierte **Beschriftungen** nur im Fokusmodus. Drücken Sie NVDA+Leertaste, um in den Fokusmodus zu wechseln, bevor Sie **Beschriftungen** verwenden. Grund ist, dass NVDA im Lesemodus einen virtuellen Puffer nutzt, der nicht dieselben Live‑Objekte verwendet, auf die Custom Labels angewiesen ist.  
* **Steuerelemente mit identischen Eigenschaften:** Wenn eine Anwendung mehrere Steuerelemente desselben Typs mit gleichem Namen (oder ohne Namen) hat, kann es vorkommen, dass Custom Labels sie nicht unterscheiden kann. Eine gesetzte **Beschriftung** wird dann auf alle passenden Steuerelemente angewendet. Das ist selten, da die meisten Anwendungen eindeutige Identifikatoren vergeben.

## Mitwirkende

* Leonardo Marenda (@LeonardoMarenda): Italienische Übersetzung hinzugefügt.  
* Kostenkov‑2021 (@Kostenkov‑2021): Russische README und Lokalisierung hinzugefügt.  
* Umut KORKMAZ (umutkork@gmail.com): Türkische Übersetzung hinzugefügt.  
* George‑br: … (Eintrag im Original abgeschnitten)
* Rainer Brell - BFW Würzburg (Deutsche übersetzung)