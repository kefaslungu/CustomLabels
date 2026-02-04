# Custom Labels

* Authors: Kefas Lungu

Note: this add-on requires NVDA 2025.1 or later.
## Overview

Custom Labels is an NVDA add-on that allows you to add custom labels for unlabeled controls and edit existing ones. This is particularly useful for applications with buttons or controls that doesn't have labels or NVDA cannot properly identify.

## Features

* Assign custom labels to unlabeled controls
* Edit existing custom labels
* Remove custom labels when no longer needed
* Manage all labels through a settings panel
* Labels are stored per-application for better organization, and for exporting and importing for sharing later

## Supported Control Types

The following control types can be labeled:

* Buttons
* Menu buttons
* Toggle buttons
* Checkboxes
* Radio buttons
* Combo boxes
* Sliders
* Tabs
* Menu items

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
2. Browse labels organized by application
3. Use the Edit, Remove, Remove App, or Remove All buttons as needed

## Settings Panel

The Custom Labels settings panel can be accessed through:

* The keyboard shortcut NVDA+Control+;
* NVDA menu > Preferences > Settings > Custom Labels

The panel displays all custom labels organized in a tree view by application. You can:

* **Edit**: Modify the selected label
* **Remove**: Delete the selected label
* **Remove App**: Delete all labels for the selected application
* **Remove All**: Delete all custom labels

## Storage

Labels are stored in JSON files in NVDA's configuration directory under a `customLabels` folder. Each application has its own JSON file, making it easy to backup or share labels for specific applications.

## Changelog

### Version 2026.0

* Initial release

