# dialogs.py
# A part of Custom Labels addon for NVDA
# Allows users to assign custom labels to unlabeled controls and edit and manage them.
# copyright: 2026 Kefas Lungu
# This file is licensed under the GNU General Public License v2.
# See the file COPYING.txt for details.

import wx
import config
import gui
import gui.guiHelper
import gui.settingsDialogs
import controlTypes
import addonHandler
from logHandler import log

# Initialize translations
addonHandler.initTranslation()


def getRoleDisplayString(roleValue):
	"""Convert a role integer back to a display string."""
	try:
		role = controlTypes.Role(roleValue)
		return role.displayString
	except (ValueError, AttributeError):
		log.debugWarning(f"CustomLabels: unknown role value {roleValue!r}")
		return str(roleValue)


class SetLabelDialog(wx.Dialog):
	"""Dialog to set or edit a custom label for a control."""

	def __init__(self, parent, controlInfo, currentLabel=None):
		# Translators: Title of dialog when editing an existing label or setting a new label
		title = _("Edit Custom Label") if currentLabel else _("Set Custom Label")
		super().__init__(parent, title=title)

		self.result = None

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

		# Translators: Label for the control information list
		infoText = _("Control &information:")
		self.infoList = sHelper.addLabeledControl(
			infoText,
			wx.ListCtrl,
			style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER
		)
		# Translators: Column header for property name
		self.infoList.InsertColumn(0, _("Property"), width=120)
		# Translators: Column header for property value
		self.infoList.InsertColumn(1, _("Value"), width=250)

		# Populate control info
		row = 0
		# Original name
		originalName = controlInfo.get('name') or _("(unlabeled)")
		# Translators: Property name for original control name
		self.infoList.InsertItem(row, _("Original name"))
		self.infoList.SetItem(row, 1, originalName)
		row += 1

		# Role
		# Translators: Property name for control role
		self.infoList.InsertItem(row, _("Role"))
		self.infoList.SetItem(row, 1, controlInfo.get('role', _('Unknown')))
		row += 1

		# Application
		# Translators: Property name for application
		self.infoList.InsertItem(row, _("Application"))
		self.infoList.SetItem(row, 1, controlInfo.get('app', _('Unknown')))
		row += 1

		# Identifier (if available)
		identifier = controlInfo.get('identifier')
		if identifier:
			# Translators: Property name for control identifier
			self.infoList.InsertItem(row, _("Identifier"))
			self.infoList.SetItem(row, 1, identifier)
			row += 1

		# Current label (if editing)
		if currentLabel:
			# Translators: Property name for current custom label
			self.infoList.InsertItem(row, _("Current label"))
			self.infoList.SetItem(row, 1, currentLabel)
			row += 1

		# Translators: Label for the custom label input field
		labelText = _("&Custom label:")
		self.labelEdit = sHelper.addLabeledControl(labelText, wx.TextCtrl, size=(300, -1))
		# Pre-populate with current label (if editing) or original name (if setting new)
		self.labelEdit.SetValue(currentLabel or controlInfo.get('name', ''))

		bHelper = sHelper.addItem(gui.guiHelper.ButtonHelper(orientation=wx.HORIZONTAL))

		# Translators: OK button
		okayButton = bHelper.addButton(self, id=wx.ID_OK, label=_("&OK"))
		okayButton.Bind(wx.EVT_BUTTON, self.Okay)
		okayButton.SetDefault()

		# Translators: Cancel button
		cancelButton = bHelper.addButton(self, id=wx.ID_CANCEL, label=_("&Cancel"))

		if currentLabel:
			# Translators: Remove button to delete the label
			removeButton = bHelper.addButton(self, label=_("&Remove"))
			removeButton.Bind(wx.EVT_BUTTON, self.onRemove)

		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		self.labelEdit.SetFocus()
		self.CentreOnScreen()

	def Okay(self, evt):
		self.result = self.labelEdit.GetValue().strip()
		self.EndModal(wx.ID_OK)

	def onRemove(self, evt):
		self.result = ""
		self.EndModal(wx.ID_OK)


# Global reference to labelStore, set by GlobalPlugin
_labelStore = None


def setLabelStore(store):
	"""Set the label store reference for the settings panel."""
	global _labelStore
	_labelStore = store


class CustomLabelsSettingsPanel(gui.settingsDialogs.SettingsPanel):
	"""Settings panel for managing custom labels."""
	# Translators: Title of the settings panel
	title = _("Custom Labels")

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)

		# Store mapping from tree items to data
		self._itemData = {}

		# Translators: Label for the tree of custom labels
		labelsText = _("&Available custom labels:")
		self.labelsTree = sHelper.addLabeledControl(
			labelsText,
			wx.TreeCtrl,
			style=wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_SINGLE
		)

		self._populateTree()

		self.labelsTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.onTreeSelChanged)

		bHelper = sHelper.addItem(gui.guiHelper.ButtonHelper(orientation=wx.HORIZONTAL))

		# Translators: Edit button
		self.editButton = bHelper.addButton(self, label=_("&Edit"))
		self.editButton.Bind(wx.EVT_BUTTON, self.onEdit)
		self.editButton.Disable()

		# Translators: Remove button
		self.removeButton = bHelper.addButton(self, label=_("&Remove"))
		self.removeButton.Bind(wx.EVT_BUTTON, self.onRemove)
		self.removeButton.Disable()

		# Translators: Remove app button
		self.removeAppButton = bHelper.addButton(self, label=_("Remove A&pp"))
		self.removeAppButton.Bind(wx.EVT_BUTTON, self.onRemoveApp)
		self.removeAppButton.Disable()

		# Translators: Remove all button
		self.removeAllButton = bHelper.addButton(self, label=_("Remove &All"))
		self.removeAllButton.Bind(wx.EVT_BUTTON, self.onRemoveAll)

		self._updateButtonStates()

		# Translators: Checkbox label for auto-describe feature
		self.autoDescribeCheckbox = sHelper.addItem(
			wx.CheckBox(self, label=_("&Speak description for unlabeled controls as labels if available"))
		)
		self.autoDescribeCheckbox.SetValue(config.conf["customLabels"]["autoDescribe"])

	def _getExpandedApps(self):
		"""Return the set of app names whose tree nodes are currently expanded."""
		expanded = set()
		root = self.labelsTree.GetRootItem()
		if not root.IsOk():
			return expanded
		child, cookie = self.labelsTree.GetFirstChild(root)
		while child.IsOk():
			if self.labelsTree.IsExpanded(child):
				data = self._itemData.get(child)
				if data:
					expanded.add(data[0])
			child, cookie = self.labelsTree.GetNextChild(root, cookie)
		return expanded

	def _getSelectedAppName(self):
		data = self._getSelectedData()
		if data:
			return data[0]
		return None

	def _populateTree(self, restoreAppName=None):
		"""Rebuild the tree, restoring expanded state and optionally re-selecting an app node.

		Args:
			restoreAppName: if given, select this app's node after rebuilding.
		"""
		expandedApps = self._getExpandedApps()

		self.labelsTree.DeleteAllItems()
		self._itemData.clear()

		if not _labelStore:
			return

		# Translators: Root item in the labels tree
		root = self.labelsTree.AddRoot(_("All Labels"))

		# Get labels grouped by app
		labelsByApp = _labelStore.getAllByApp()

		restoreItem = None
		for appName in sorted(labelsByApp.keys()):
			labels = labelsByApp[appName]
			if not labels:
				continue

			# Translators: App node showing app name and label count
			appText = _("{app} ({count} labels)").format(app=appName, count=len(labels))
			appItem = self.labelsTree.AppendItem(root, appText)
			self._itemData[appItem] = (appName, None)

			for fp, label in labels.items():
				fpDict = dict(fp)
				idStr = fpDict.get("automationId") or fpDict.get("windowClassName") or fpDict.get("htmlId") or ""
				labelText = _("{label} - {identifier}").format(label=label, identifier=idStr) if idStr else label
				labelItem = self.labelsTree.AppendItem(appItem, labelText)
				self._itemData[labelItem] = (appName, fp)

			# Restore expanded state for this app node
			if appName in expandedApps:
				self.labelsTree.Expand(appItem)

			if appName == restoreAppName:
				restoreItem = appItem

		self.labelsTree.Expand(root)

		# Restore selection, or fall back to expanding the first child
		if restoreItem and restoreItem.IsOk():
			self.labelsTree.SelectItem(restoreItem)
		else:
			firstChild, cookie = self.labelsTree.GetFirstChild(root)
			if firstChild.IsOk() and firstChild not in self._itemData:
				pass  # root only, nothing to expand
			elif firstChild.IsOk() and not expandedApps:
				# First open: expand the first app node by default
				self.labelsTree.Expand(firstChild)

	def _updateButtonStates(self):
		selection = self.labelsTree.GetSelection()
		hasLabels = bool(self._itemData)

		if not selection.IsOk() or selection == self.labelsTree.GetRootItem():
			self.editButton.Disable()
			self.removeButton.Disable()
			self.removeAppButton.Disable()
		else:
			data = self._itemData.get(selection)
			if data:
				appName, fp = data
				if fp is None:
					self.editButton.Disable()
					self.removeButton.Disable()
					self.removeAppButton.Enable()
				else:
					self.editButton.Enable()
					self.removeButton.Enable()
					self.removeAppButton.Enable()
			else:
				self.editButton.Disable()
				self.removeButton.Disable()
				self.removeAppButton.Disable()

		if hasLabels:
			self.removeAllButton.Enable()
		else:
			self.removeAllButton.Disable()

	def onTreeSelChanged(self, evt):
		self._updateButtonStates()

	def _getSelectedData(self):
		selection = self.labelsTree.GetSelection()
		if not selection.IsOk():
			return None
		return self._itemData.get(selection)

	def onEdit(self, evt):
		if not _labelStore:
			return
		data = self._getSelectedData()
		if not data or data[1] is None:
			return

		appName, fp = data
		currentLabel = _labelStore.get(fp)
		fpDict = dict(fp)

		identifier = fpDict.get("automationId") or fpDict.get("windowClassName") or fpDict.get("htmlId") or ""
		roleValue = fpDict.get("role", 0)
		roleName = getRoleDisplayString(roleValue)

		controlInfo = {
			'name': fpDict.get("name", _("(not available from saved data)")),
			'role': roleName,
			'app': fpDict.get("app", ""),
			'identifier': identifier,
		}

		dlg = SetLabelDialog(self, controlInfo, currentLabel)
		try:
			if dlg.ShowModal() == wx.ID_OK:
				if dlg.result == "":
					_labelStore.remove(fp)
					log.debug(f"CustomLabels: label removed for '{appName}' via settings panel")
				elif dlg.result:
					_labelStore.set(fp, dlg.result)
					log.debug(f"CustomLabels: label updated for '{appName}' via settings panel")
				self._populateTree(restoreAppName=appName)
				self._updateButtonStates()
		except Exception:
			log.error("CustomLabels: unexpected error in settings panel onEdit", exc_info=True)
		finally:
			dlg.Destroy()

	def onRemove(self, evt):
		if not _labelStore:
			return
		data = self._getSelectedData()
		if not data or data[1] is None:
			return

		appName, fp = data
		label = _labelStore.get(fp)

		if gui.messageBox(
			_("Remove label '{label}'?").format(label=label),
			_("Confirm Removal"),
			wx.YES_NO | wx.ICON_QUESTION
		) == wx.YES:
			_labelStore.remove(fp)
			log.debug(f"CustomLabels: label '{label}' removed for '{appName}' via settings panel")
			self._populateTree(restoreAppName=appName)
			self._updateButtonStates()

	def onRemoveApp(self, evt):
		if not _labelStore:
			return
		appName = self._getSelectedAppName()
		if not appName:
			return

		labels = _labelStore.getLabelsForApp(appName)
		count = len(labels)

		if gui.messageBox(
			_("Remove all {count} labels for '{app}'?").format(count=count, app=appName),
			_("Confirm Removal"),
			wx.YES_NO | wx.ICON_WARNING
		) == wx.YES:
			_labelStore.removeApp(appName)
			log.debug(f"CustomLabels: all {count} labels removed for '{appName}' via settings panel")
			self._populateTree()
			self._updateButtonStates()

	def onRemoveAll(self, evt):
		if not _labelStore:
			return
		allLabels = _labelStore.getAll()
		if not allLabels:
			return

		if gui.messageBox(
			_("Remove all {count} custom labels?").format(count=len(allLabels)),
			_("Confirm Removal"),
			wx.YES_NO | wx.ICON_WARNING
		) == wx.YES:
			_labelStore.clear()
			log.debug(f"CustomLabels: all {len(allLabels)} labels cleared via settings panel")
			self._populateTree()
			self._updateButtonStates()

	def onSave(self):
		config.conf["customLabels"]["autoDescribe"] = self.autoDescribeCheckbox.GetValue()
