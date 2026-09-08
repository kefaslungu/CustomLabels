# Changelog for custom labels

## Version 2026.3

* Fixed a bug where a custom label could be silently overwritten by NVDA's internal name assignment.
* The settings panel tree now preserves expanded and selected state after editing or removing a label.
* Fixed labelling individual controls in apps where multiple controls share identical properties. Labelling one button no longer labels all buttons of the same type.
* Added browse mode (virtual buffer) support for Electron and WebView2-based applications: custom labels are now applied when reading content with arrow keys or quick navigation, not only in focus mode. Note: regular browsers (Chrome, Firefox, Edge, etc.) are not yet supported.
* Fixed labels failing to match after an application restart in Electron and WebView2-based apps. The volatile renderer-window identifier is now excluded from the fingerprint so saved labels survive restarts.
* Improved fingerprinting for Electron and WebView2 content using ARIA properties and role, making label assignments more stable across page reloads.

## Version 2026.1

* A release compatible with NVDA 2026.1.

## Version 2026.02

* Added support for NVDA 2026.1.
* Added Ukrainian, Russian, German and Turkish translations.
* Improved control identification using original control name.
* Fixed labels not working in web-based applications (Electron, WebView2).
* Fixed all buttons getting the same label in some applications.
* Added support for labelling editable text.
* Added option to speak description for unlabeled controls, greatly improving accessibility in Java-based applications (Settings > Custom Labels).
* Added known limitations documentation.

## Version 2026.0

* Initial release.
