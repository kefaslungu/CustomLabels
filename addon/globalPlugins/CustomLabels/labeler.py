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
from logHandler import log
from NVDAObjects import NVDAObject


# Storage location
def getLabelsFolder():
	"""Returns the path to the labels folder."""
	return os.path.join(globalVars.appArgs.configPath, "customLabels")


def _ensureLabelsFolder():
	"""Create the labels folder if it does not exist. Returns the folder path."""
	folder = getLabelsFolder()
	if not os.path.exists(folder):
		try:
			os.makedirs(folder)
		except Exception:
			log.error("CustomLabels: failed to create labels folder", exc_info=True)
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
	"""Get the JSON file path for an app, ensuring the labels folder exists."""
	safeName = sanitizeAppName(appName)
	return os.path.join(_ensureLabelsFolder(), f"{safeName}.json")


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
			log.debug(f"CustomLabels: loaded {len(self._cache[appName])} labels for '{appName}'")
		except Exception:
			log.error(f"CustomLabels: failed to load labels for '{appName}'", exc_info=True)
			self._cache[appName] = {}

	def _saveApp(self, appName):
		"""Save labels for a specific app to disk."""
		filePath = getAppFilePath(appName)
		labels = self._cache.get(appName, {})

		if not labels:
			# Delete file if no labels remain
			if os.path.exists(filePath):
				try:
					os.remove(filePath)
					log.debug(f"CustomLabels: removed empty labels file for '{appName}'")
				except Exception:
					log.error(f"CustomLabels: failed to remove labels file for '{appName}'", exc_info=True)
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
			log.debug(f"CustomLabels: saved {len(labels)} labels for '{appName}'")
		except Exception:
			log.error(f"CustomLabels: failed to save labels for '{appName}'", exc_info=True)

	def _keyToString(self, key):
		"""Convert fingerprint tuple to JSON string."""
		return json.dumps(list(key), ensure_ascii=False)

	def _keyFromString(self, s):
		"""Convert JSON string back to fingerprint tuple."""
		items = [tuple(item) for item in json.loads(s)]
		# Migration: add fields missing from older fingerprint versions
		keys = {item[0] for item in items}
		if "name" not in keys:
			items.append(("name", ""))
		if "description" not in keys:
			items.append(("description", ""))
		if "parentName" not in keys:
			items.append(("parentName", ""))
		# Remove obsolete fields from older fingerprint versions
		_OBSOLETE_FIELDS = {"parentDesc", "ia2Class", "ia2Tag"}
		items = [item for item in items if item[0] not in _OBSOLETE_FIELDS]
		# Remove windowControlID for Ia2Web fingerprints (Chrome_RenderWidgetHostHWND):
		# this value is a renderer-window handle that changes every app restart, so
		# saved labels with it would never match the live fingerprint after a restart.
		fpDict = dict(items)
		if fpDict.get("windowClassName") == "Chrome_RenderWidgetHostHWND" and "windowControlID" in fpDict:
			items = [item for item in items if item[0] != "windowControlID"]
		return tuple(sorted(items))

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
		_invalidateBrowseModeCache()

	def remove(self, fingerprint):
		"""Remove a label for a fingerprint."""
		appName = self._getAppFromFingerprint(fingerprint)
		self._loadApp(appName)

		if appName in self._cache and fingerprint in self._cache[appName]:
			del self._cache[appName][fingerprint]
			self._saveApp(appName)
			_overlayCache.clear()
			_invalidateBrowseModeCache()
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
				if not filename.endswith(".json"):
					continue
				# Use the filename stem as a cheap pre-check before opening the file.
				# The real appName inside the JSON may differ, but this avoids I/O for
				# apps whose sanitized name is already loaded.
				stemName = filename[:-5]
				if stemName in self._loadedApps:
					continue
				filePath = os.path.join(folder, filename)
				try:
					with open(filePath, "r", encoding="utf-8") as f:
						data = json.load(f)
					appName = data.get("appName", stemName)
					if appName not in self._loadedApps:
						self._loadedApps.add(appName)
						self._cache[appName] = {
							self._keyFromString(k): v
							for k, v in data.get("labels", {}).items()
						}
						log.debug(f"CustomLabels: loaded {len(self._cache[appName])} labels for '{appName}' (bulk load)")
				except Exception:
					log.error(f"CustomLabels: failed to load labels file '{filename}'", exc_info=True)
		except Exception:
			log.error("CustomLabels: failed to list labels folder", exc_info=True)


# Global label store instance
labelStore = LabelStore()


# Overlay class cache

_overlayCache = {}


def makeLabelOverlay(labelText):
	"""Create or retrieve a cached overlay class."""
	if labelText in _overlayCache:
		return _overlayCache[labelText]

	class LabelOverlay(NVDAObject):
		# Use a property so instance-level assignment cannot shadow the label.
		@property
		def name(self):
			return labelText

		@name.setter
		def name(self, value):
			pass

	_overlayCache[labelText] = LabelOverlay
	return LabelOverlay


def _invalidateBrowseModeCache():
	"""Notify virtualBufferSupport to clear its label caches.

	Imported lazily to avoid a circular import (virtualBufferSupport imports labeler).
	"""
	try:
		from . import virtualBufferSupport
		virtualBufferSupport.invalidateCacheForLabel(None)
	except Exception:
		pass


# Convenience functions

def getLabel(fingerprint):
	return labelStore.get(fingerprint)


def setLabel(fingerprint, label):
	labelStore.set(fingerprint, label)


def removeLabel(fingerprint):
	return labelStore.remove(fingerprint)


def hasLabel(fingerprint):
	return labelStore.has(fingerprint)
