# Custom Labels

* Authors: Kefas Lungu

Note: this add-on requires NVDA 2025.1 or later.
## Overview

Custom Labels is an NVDA add-on that allows you to add custom labels for unlabelled controls and edit existing ones. This is particularly useful for applications with buttons or controls that don't have labels or NVDA cannot properly identify.

## Features

* Assign custom labels to unlabelled controls.
* Edit existing custom labels.
* Remove custom labels when no longer needed.
* Manage all labels through a settings panel.
* Labels are stored per-application for better organisation, and for exporting and importing for sharing later.
* Option to automatically speak control descriptions when no label is available.

## Supported Control Types

The following control types can be labelled:

* Buttons
* Menu buttons
* Toggle buttons
* Checkboxes
* Radio buttons
* Combo boxes
* Sliders
* Tabs
* Menu items
* Editable text

## Gestures

* NVDA+Control+L: Set or edit a custom label for the current control
* NVDA+Control+Delete: Remove the custom label from the current control
* NVDA+Control+J: Check if the current control has a custom label
* NVDA+Control+; (semicolon): Open custom labels settings

## Usage

### Setting a Custom Label

1. Focus on a control you want to label
2. Press NVDA+Control+L
3. A dialog will appear showing information about the control
4. Enter the desired label in the text field
5. Press OK to save the label

### Editing an Existing Label

1. Focus on a control that has a custom label
2. Press NVDA+Control+L
3. Modify the label in the text field
4. Press OK to save the changes

### Removing a Label

You can remove a label in two ways:

1. Focus on the control and press NVDA+Control+Delete
2. Or open the label dialog (NVDA+Control+L) and press the Remove button

### Managing All Labels

1. Press NVDA+Control+; to open the Custom Labels settings panel
2. Browse labels organised by application
3. Use the Edit, Remove, Remove App, or Remove All buttons as needed

## Settings Panel

The Custom Labels settings panel can be accessed through:

* The keyboard shortcut NVDA+Control+;
* NVDA menu > Preferences > Settings > Custom Labels

The panel displays all custom labels organised in a tree view by application. You can:

* Edit: Modify the selected label
* Remove: Delete the selected label
* Remove App: Delete all labels for the selected application
* Remove All: Delete all custom labels

In addition to that, there is a setting that allows you to use the description of a control as the label of that control if the control has no label. But note: if a custom label has been set, that custom label will overwrite the description, even the original label on the control.

## Storage

Labels are stored in JSON files in NVDA's configuration directory under a `customLabels` folder. Each application has its own JSON file, making it easy to backup or share labels for specific applications.

## Known Limitations

* Web-based applications: For applications built with web technologies (such as the new Outlook, Microsoft Teams, Slack, TeamViewer, WhatsApp, Discord, and other Electron/WebView2 apps), custom labels only work in focus mode. Press NVDA+Space to switch to focus mode before using custom labels in these applications. This is due to how NVDA handles browse mode using a virtual buffer, which does not use the same live objects that custom labels rely on.
* Controls with identical properties: If an application has multiple controls of the same type with the same name (or no name), sometimes custom labels cannot distinguish between them. Labelling one will label all matching controls. This is rare in practice, as most applications assign unique identifiers to their controls.

## Contributors

* [Leonardo Marenda (@LeonardoMarenda)](https://github.com/LeonardoMarenda): Added Italian translation. ([#1](https://github.com/kefaslungu/CustomLabels/pull/1))
* [Kostenkov-2021 (@Kostenkov-2021)](https://github.com/Kostenkov-2021): Added Russian README and localisation. ([#3](https://github.com/kefaslungu/CustomLabels/pull/3))
* Umut KORKMAZ (umutkork@gmail.com): Added Turkish translation.
* [George-br (@George-br)](https://github.com/George-br): Added Ukrainian translation. ([#6](https://github.com/kefaslungu/CustomLabels/pull/6))
* Brell Rainer (Rainer.Brell@bfw-wuerzburg.de): Added German translations.

## Changelog

### Version 2026.1
* A release compartable with NVDA 2026.1.
### Version 2026.02

* Added support for NVDA 2026.1
* Added Ukrainian, Russian, german and Turkish translations.
* Improved control identification using original control name.
* Fixed labels not working in web-based applications (Electron, WebView2).
* Fixed all buttons getting the same label in some applications.
* Added support for labelling editable text.
* Added option to speak description for unlabelled controls, greatly improving accessibility in Java-based applications (Settings > Custom Labels).
* Added known limitations documentation.

### Version 2026.0

* Initial release
