# fingerPrintReader
# A part of Custom Labels addon for NVDA
# The addon Allows users to assign custom labels to unlabeled controls and edit and manage them.
# copyright: 2026 Kefas Lungu
# This file is licensed under the GNU General Public License v2.
# See the file COPYING.txt for details.
# This module provides functions to generate a stable fingerprint for an NVDAObject based on its properties.

from NVDAObjects.UIA import UIA


def getObjectFingerprint(obj):
	"""
	Return a stable fingerprint for an NVDAObject.
	SAFE version - no sibling iteration.
	"""
	try:
		fp = {}

		# App name
		try:
			fp["app"] = obj.appModule.appName
		except Exception:
			fp["app"] = "unknown"

		# Role
		try:
			fp["role"] = int(obj.role)
		except Exception:
			fp["role"] = 0

		# Backend-specific ID
		if isinstance(obj, UIA):
			fp["backend"] = "UIA"
			try:
				fp["automationId"] = obj.UIAElement.currentAutomationId or ""
			except Exception:
				fp["automationId"] = ""
			try:
				fp["className"] = obj.windowClassName or ""
			except Exception:
				fp["className"] = ""
		else:
			fp["backend"] = "IA2"
			try:
				fp["windowClassName"] = obj.windowClassName or ""
			except Exception:
				fp["windowClassName"] = ""
			try:
				fp["windowControlID"] = obj.windowControlID or 0
			except Exception:
				fp["windowControlID"] = 0

		# Convert to hashable tuple
		return tuple(sorted(fp.items()))

	except Exception:
		return None


def fingerprintToDict(fp):
	"""Convert a fingerprint tuple back to a dict."""
	if fp:
		return dict(fp)
	return {}
