# labeler
# A part of Custom Labels addon for NVDA
# The addon Allows users to assign custom labels to unlabeled controls and edit and manage them.
# copyright: 2026 Kefas Lungu
# This file is licensed under the GNU General Public License v2.
# See the file COPYING.txt for details.
# Label storage with per-app JSON files
# This module manages the storage of custom labels using per-app JSON files.

import os
import re
import json
import globalVars
from NVDAObjects import NVDAObject


# Storage location
def getLabelsFolder():
	"""Returns the path to the labels folder."""
	folder = os.path.join(globalVars.appArgs.configPath, "customLabels")
	if not os.path.exists(folder):
		os.makedirs(folder)
	return folder


def sanitizeAppName(appName):
	"""
	Sanitize app name for use as filename.
	- Lowercase
	- Replace spaces and unsafe chars with underscore
	- Remove consecutive underscores
	"""
	if not appName:
		return "unknown"
	# Lowercase
	name = appName.lower()
	# Replace unsafe characters with underscore
	name = re.sub(r'[\\/:*?"<>|\s]+', '_', name)
	# Remove leading/trailing underscores
	name = name.strip('_')
	# Remove consecutive underscores
	name = re.sub(r'_+', '_', name)
	return name or "unknown"


def getAppFilePath(appName):
	"""Get the JSON file path for an app."""
	safeName = sanitizeAppName(appName)
	return os.path.join(getLabelsFolder(), f"{safeName}.json")


# Per-app label storage
class LabelStore:
	"""
	Manages custom labels with per-app JSON files.
	Labels are cached in memory and saved per-app.
	"""

	def __init__(self):
		# Cache: {appName: {fingerprint: label}}
		self._cache = {}
		self._loadedApps = set()

	def _loadApp(self, appName):
		"""Load labels for a specific app from disk."""
		if appName in self._loadedApps:
			return
		self._loadedApps.add(appName)

		filePath = getAppFilePath(appName)
		if not os.path.exists(filePath):
			self._cache[appName] = {}
			return

		try:
			with open(filePath, "r", encoding="utf-8") as f:
				data = json.load(f)
			# Convert string keys back to tuples
			self._cache[appName] = {
				self._keyFromString(k): v
				for k, v in data.get("labels", {}).items()
			}
		except Exception:
			self._cache[appName] = {}

	def _saveApp(self, appName):
		"""Save labels for a specific app to disk."""
		filePath = getAppFilePath(appName)
		labels = self._cache.get(appName, {})

		if not labels:
			# Delete file if no labels
			if os.path.exists(filePath):
				try:
					os.remove(filePath)
				except Exception:
					pass
			return

		try:
			data = {
				"appName": appName,
				"labels": {
					self._keyToString(k): v
					for k, v in labels.items()
				}
			}
			with open(filePath, "w", encoding="utf-8") as f:
				json.dump(data, f, indent=2, ensure_ascii=False)
		except Exception:
			pass

	def _keyToString(self, key):
		"""Convert fingerprint tuple to JSON string."""
		return json.dumps(list(key), ensure_ascii=False)

	def _keyFromString(self, s):
		"""Convert JSON string back to fingerprint tuple."""
		return tuple(tuple(item) for item in json.loads(s))

	def _getAppFromFingerprint(self, fingerprint):
		"""Extract app name from fingerprint."""
		fpDict = dict(fingerprint)
		return fpDict.get("app", "unknown")

	def get(self, fingerprint):
		"""Get a label for a fingerprint."""
		appName = self._getAppFromFingerprint(fingerprint)
		self._loadApp(appName)
		return self._cache.get(appName, {}).get(fingerprint)

	def set(self, fingerprint, label):
		"""Set a label for a fingerprint."""
		appName = self._getAppFromFingerprint(fingerprint)
		self._loadApp(appName)

		if appName not in self._cache:
			self._cache[appName] = {}
		self._cache[appName][fingerprint] = label
		self._saveApp(appName)
		_overlayCache.clear()

	def remove(self, fingerprint):
		"""Remove a label for a fingerprint."""
		appName = self._getAppFromFingerprint(fingerprint)
		self._loadApp(appName)

		if appName in self._cache and fingerprint in self._cache[appName]:
			del self._cache[appName][fingerprint]
			self._saveApp(appName)
			_overlayCache.clear()
			return True
		return False

	def has(self, fingerprint):
		"""Check if a label exists."""
		appName = self._getAppFromFingerprint(fingerprint)
		self._loadApp(appName)
		return fingerprint in self._cache.get(appName, {})

	def getAll(self):
		"""Get all labels from all apps."""
		self._loadAllApps()
		result = {}
		for appName, labels in self._cache.items():
			result.update(labels)
		return result

	def getAllByApp(self):
		"""Get all labels grouped by app. Returns {appName: {fingerprint: label}}."""
		self._loadAllApps()
		return dict(self._cache)

	def getApps(self):
		"""Get list of apps that have labels."""
		self._loadAllApps()
		return [app for app, labels in self._cache.items() if labels]

	def getLabelsForApp(self, appName):
		"""Get all labels for a specific app."""
		self._loadApp(appName)
		return dict(self._cache.get(appName, {}))

	def removeApp(self, appName):
		"""Remove all labels for an app."""
		self._loadApp(appName)
		if appName in self._cache:
			self._cache[appName] = {}
			self._saveApp(appName)
			_overlayCache.clear()
			return True
		return False

	def clear(self):
		"""Remove all labels for all apps."""
		self._loadAllApps()
		for appName in list(self._cache.keys()):
			self._cache[appName] = {}
			self._saveApp(appName)
		_overlayCache.clear()

	def _loadAllApps(self):
		"""Load all app label files from disk."""
		folder = getLabelsFolder()
		try:
			for filename in os.listdir(folder):
				if filename.endswith(".json"):
					# Read the file to get actual app name
					filePath = os.path.join(folder, filename)
					try:
						with open(filePath, "r", encoding="utf-8") as f:
							data = json.load(f)
						appName = data.get("appName", filename[:-5])
						if appName not in self._loadedApps:
							self._loadedApps.add(appName)
							self._cache[appName] = {
								self._keyFromString(k): v
								for k, v in data.get("labels", {}).items()
							}
					except Exception:
						pass
		except Exception:
			pass


# Global label store instance
labelStore = LabelStore()


# Overlay class cache

_overlayCache = {}


def makeLabelOverlay(labelText):
	"""Create or retrieve a cached overlay class."""
	if labelText in _overlayCache:
		return _overlayCache[labelText]

	class LabelOverlay(NVDAObject):
		name = labelText

	_overlayCache[labelText] = LabelOverlay
	return LabelOverlay


# Convenience functions

def getLabel(fingerprint):
	return labelStore.get(fingerprint)


def setLabel(fingerprint, label):
	labelStore.set(fingerprint, label)


def removeLabel(fingerprint):
	return labelStore.remove(fingerprint)


def hasLabel(fingerprint):
	return labelStore.has(fingerprint)
