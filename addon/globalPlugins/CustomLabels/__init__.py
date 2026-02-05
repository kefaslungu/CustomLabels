# A part of Custom Labels addon for NVDA
# The addon allows users to assign custom labels to unlabeled controls and edit and manage them.
# copyright: 2026 Kefas Lungu
# This file is licensed under the GNU General Public License v2.
# See the file COPYING.txt for details.

import wx
import api
import controlTypes
import globalPluginHandler
import gui
import ui
from logHandler import log
from scriptHandler import script

from .labeler import (
	makeLabelOverlay,
	labelStore,
	getLabel,
	setLabel,
	removeLabel,
)
from .dialogs import SetLabelDialog, CustomLabelsSettingsPanel, setLabelStore
from .fingerPrintReader import getObjectFingerprint, fingerprintToDict

import addonHandler

# Initialize translations
addonHandler.initTranslation()

# Only these roles can be labeled
# Subjected to change based on user feedback
LABELABLE_ROLES = {
	controlTypes.Role.BUTTON,
	controlTypes.Role.MENUBUTTON,
	controlTypes.Role.TOGGLEBUTTON,
	controlTypes.Role.CHECKBOX,
	controlTypes.Role.RADIOBUTTON,
	controlTypes.Role.COMBOBOX,
	controlTypes.Role.SLIDER,
	controlTypes.Role.TAB,
	controlTypes.Role.MENUITEM,
}


def getRoleName(role):
	"""Get a human-readable role name."""
	try:
		return role.displayString
	except Exception:
		return str(role)


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# Translators: The gestures category for this add-on in input gestures dialog.
	scriptCategory = _("Custom Labels")
	def __init__(self):
		super().__init__()
		# Set the label store for the settings panel
		setLabelStore(labelStore)
		# Register the settings panel
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(CustomLabelsSettingsPanel)

	def terminate(self):
		# Unregister the settings panel
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(CustomLabelsSettingsPanel)
		except ValueError:
			pass
		super().terminate()

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		"""Inject overlay if custom label exists."""
		try:
			if obj.role not in LABELABLE_ROLES:
				return

			fp = getObjectFingerprint(obj)
			if not fp:
				return

			label = getLabel(fp)
			if not label:
				return

			clsList.insert(0, makeLabelOverlay(label))

		except Exception as e:
			log.error(f"customlabels error: {e}")

	@script(
		# Translators: Description for the set custom label script
		description=_("Set or edit a custom label for the current control"),
		gesture="kb:NVDA+control+l",
	)
	def script_setCustomLabel(self, gesture):
		"""Set or edit a custom label for the focused control."""
		obj = api.getFocusObject()

		if obj.role not in LABELABLE_ROLES:
			# Translators: Error message when control cannot be labeled
			ui.message(_("Cannot label this type of control"))
			return

		try:
			fp = getObjectFingerprint(obj)
			if not fp:
				# Translators: Error message when control cannot be identified
				ui.message(_("Cannot identify this control"))
				return
		except Exception as e:
			# Translators: Error message with details. {error} is the error message.
			ui.message(_("Error: {error}").format(error=e))
			return

		currentLabel = getLabel(fp)
		fpDict = fingerprintToDict(fp)

		# Get original name, bypassing any custom label overlay
		# _get_name() is the underlying NVDA method that returns the actual name
		try:
			originalName = obj._get_name() if hasattr(obj, '_get_name') else obj.name
		except Exception:
			originalName = obj.name

		controlInfo = {
			'name': originalName or "",
			'role': getRoleName(obj.role),
			'app': fpDict.get('app', _('Unknown')),
		}

		def showDialog():
			dlg = SetLabelDialog(gui.mainFrame, controlInfo, currentLabel)
			gui.mainFrame.prePopup()
			try:
				result = dlg.ShowModal()
				if result == wx.ID_OK:
					if dlg.result == "":
						if removeLabel(fp):
							# Translators: Confirmation when label is removed
							wx.CallAfter(ui.message, _("Label removed"))
						else:
							# Translators: Message when there's no label to remove
							wx.CallAfter(ui.message, _("No label to remove"))
					elif dlg.result:
						setLabel(fp, dlg.result)
						# Translators: Confirmation when label is set. {label} is the new label text.
						wx.CallAfter(ui.message, _("Label set to: {label}").format(label=dlg.result))
			finally:
				gui.mainFrame.postPopup()
				dlg.Destroy()

		wx.CallAfter(showDialog)

	@script(
		# Translators: Description for the remove custom label script
		description=_("Remove the custom label from the current control"),
		gesture="kb:NVDA+control+delete",
	)
	def script_removeCustomLabel(self, gesture):
		"""Remove the custom label from the focused control."""
		obj = api.getFocusObject()

		try:
			fp = getObjectFingerprint(obj)
			if fp and removeLabel(fp):
				# Translators: Confirmation when label is removed
				ui.message(_("Label removed"))
			else:
				# Translators: Message when there's no label to remove
				ui.message(_("No label to remove"))
		except Exception as e:
			# Translators: Error message with details. {error} is the error message.
			ui.message(_("Error: {error}").format(error=e))

	@script(
		# Translators: Description for the check label script
		description=_("Check if current control has a custom label"),
		gesture="kb:NVDA+control+j",
	)
	def script_checkLabel(self, gesture):
		"""Check if the current control has a custom label."""
		obj = api.getFocusObject()

		try:
			fp = getObjectFingerprint(obj)
			label = getLabel(fp) if fp else None

			if label:
				# Translators: Message showing the custom label. {label} is the label text.
				ui.message(_("Custom label: {label}").format(label=label))
			else:
				# Translators: Message when no custom label exists. {name} is the original name.
				ui.message(_("No custom label. Original: {name}").format(name=obj.name or _("unlabeled")))
		except Exception as e:
			# Translators: Error message with details. {error} is the error message.
			ui.message(_("Error: {error}").format(error=e))

	@script(
		# Translators: Description for the manage labels script
		description=_("Open custom labels settings"),
		gesture="kb:NVDA+control+;",
	)
	def script_manageLabels(self, gesture):
		"""Open the Custom Labels settings panel."""
		wx.CallAfter(self._openSettingsPanel)

	def _openSettingsPanel(self):
		"""Open NVDA settings to the Custom Labels panel."""
		gui.mainFrame.popupSettingsDialog(
			gui.settingsDialogs.NVDASettingsDialog,
			CustomLabelsSettingsPanel
		)
