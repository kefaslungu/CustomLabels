# A part of Custom Labels addon for NVDA
# The addon allows users to assign custom labels to unlabeled controls and edit and manage them.
# copyright: 2026 Kefas Lungu
# This file is licensed under the GNU General Public License v2.
# See the file COPYING.txt for details.

import wx
import api
import config
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
from .dialogs import SetLabelDialog, makeSettingsPanel
from .fingerPrintReader import getObjectFingerprint, fingerprintToDict
from . import virtualBufferSupport

import addonHandler

# Initialize translations
addonHandler.initTranslation()

# Config spec for addon settings
config.conf.spec["customLabels"] = {
	"autoDescribe": "boolean(default=False)",
}

# Only these roles can be labeled
# Subjected to change based on user feedback
LABELABLE_ROLES = {
	controlTypes.Role.BUTTON,
	controlTypes.Role.MENUBUTTON,
	controlTypes.Role.EDITABLETEXT,
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
	except AttributeError:
		return str(role)


def isLabelable(obj):
	"""Return True if the object's role supports custom labeling."""
	return obj.role in LABELABLE_ROLES


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# Translators: The gestures category for this add-on in input gestures dialog.
	scriptCategory = _("Custom Labels")

	def __init__(self):
		super().__init__()
		# Create the settings panel class with the label store bound
		self._settingsPanel = makeSettingsPanel(labelStore)
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(self._settingsPanel)
		virtualBufferSupport.initialize()

	def terminate(self):
		virtualBufferSupport.terminate()
		# Unregister the settings panel
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(self._settingsPanel)
		except ValueError:
			pass
		super().terminate()

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		"""Inject overlay if custom label exists, or auto-describe if enabled."""
		try:
			if not isLabelable(obj):
				return

			fp = getObjectFingerprint(obj)
			if fp:
				label = getLabel(fp)
				if label:
					clsList.insert(0, makeLabelOverlay(label))
					return

			# Auto-describe: if enabled and name is empty, use description
			if config.conf["customLabels"]["autoDescribe"]:
				try:
					name = obj._get_name() if hasattr(obj, '_get_name') else obj.name
				except Exception:
					log.debugWarning("CustomLabels: failed to get name for auto-describe check", exc_info=True)
					name = obj.name
				if not name:
					try:
						desc = obj.description
					except Exception:
						log.debugWarning("CustomLabels: failed to get description for auto-describe", exc_info=True)
						desc = None
					if desc:
						clsList.insert(0, makeLabelOverlay(desc))

		except Exception:
			log.error("CustomLabels: unexpected error in chooseNVDAObjectOverlayClasses", exc_info=True)

	@script(
		# Translators: Description for the set custom label script
		description=_("Set or edit a custom label for the current control"),
		gesture="kb:NVDA+control+l",
	)
	def script_setCustomLabel(self, gesture):
		"""Set or edit a custom label for the focused control."""
		obj = api.getFocusObject()

		if not isLabelable(obj):
			# Translators: Error message when control cannot be labeled
			ui.message(_("Cannot label this type of control"))
			return

		try:
			fp = getObjectFingerprint(obj)
			if not fp:
				# Translators: Error message when control cannot be identified
				ui.message(_("Cannot identify this control"))
				return
		except Exception:
			log.error("CustomLabels: unexpected error getting fingerprint in script_setCustomLabel", exc_info=True)
			# Translators: Error message when label cannot be set due to an unexpected error
			ui.message(_("An unexpected error occurred"))
			return

		currentLabel = getLabel(fp)
		fpDict = fingerprintToDict(fp)

		# Get original name, bypassing any custom label overlay
		# _get_name() is the underlying NVDA method that returns the actual name
		try:
			originalName = obj._get_name() if hasattr(obj, '_get_name') else obj.name
		except Exception:
			log.debugWarning("CustomLabels: failed to get original name for dialog", exc_info=True)
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
		except Exception:
			log.error("CustomLabels: unexpected error in script_removeCustomLabel", exc_info=True)
			# Translators: Error message when label cannot be removed due to an unexpected error
			ui.message(_("An unexpected error occurred"))

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
		except Exception:
			log.error("CustomLabels: unexpected error in script_checkLabel", exc_info=True)
			# Translators: Error message when label cannot be checked due to an unexpected error
			ui.message(_("An unexpected error occurred"))

	@script(
		# Translators: Description for the manage labels script
		description=_("Open custom labels settings"),
		gesture="kb:NVDA+control+;",
	)
	def script_manageLabels(self, gesture):
		"""Open the Custom Labels settings panel."""
		wx.CallAfter(self._openSettingsPanel)

	def event_gainFocus(self, obj, nextHandler):
		"""Ensure the browse mode patch is applied whenever a virtual buffer gains focus."""
		ti = getattr(obj, "treeInterceptor", None)
		if ti is not None:
			virtualBufferSupport.ensurePatched(ti)
		nextHandler()

	def _openSettingsPanel(self):
		"""Open NVDA settings to the Custom Labels panel."""
		gui.mainFrame.popupSettingsDialog(
			gui.settingsDialogs.NVDASettingsDialog,
			self._settingsPanel
		)
