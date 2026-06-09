# fingerPrintReader
# A part of Custom Labels addon for NVDA
# The addon Allows users to assign custom labels to unlabeled controls and edit and manage them.
# copyright: 2026 Kefas Lungu
# This file is licensed under the GNU General Public License v2.
# See the file COPYING.txt for details.
# This module provides functions to generate a stable fingerprint for an NVDAObject based on its properties.

from logHandler import log
from NVDAObjects.UIA import UIA
from NVDAObjects.JAB import JAB


class FingerprintHandler:
	"""Base class for UI-framework-specific fingerprint handlers.
	Each handler knows how to identify objects from a specific UI framework
	and contributes the framework-specific fields to the fingerprint.
	"""
	backend_name = ""

	@classmethod
	def can_handle(cls, obj) -> bool:
		raise NotImplementedError

	@classmethod
	def get_fields(cls, obj) -> dict:
		"""Return the framework-specific fields to include in the fingerprint."""
		raise NotImplementedError

	@classmethod
	def _safeGet(cls, obj, attr, default, label):
		"""Safely get an attribute, logging on failure."""
		try:
			return getattr(obj, attr) or default
		except Exception:
			log.debugWarning(f"CustomLabels [{cls.backend_name}]: failed to get {label}", exc_info=True)
			return default


_handlers: list[tuple[int, type[FingerprintHandler]]] = []


def registerHandler(handler_class: type[FingerprintHandler], priority: int = 50):
	"""Register a fingerprint handler. Lower priority number = tried first."""
	_handlers.append((priority, handler_class))
	_handlers.sort(key=lambda x: x[0])


def _getHandler(obj):
	for _, handler in _handlers:
		if handler.can_handle(obj):
			return handler
	return None


class UIAHandler(FingerprintHandler):
	backend_name = "UIA"

	@classmethod
	def can_handle(cls, obj):
		return isinstance(obj, UIA)

	@classmethod
	def get_fields(cls, obj):
		fields = {}
		try:
			fields["automationId"] = obj.UIAElement.currentAutomationId or ""
		except Exception:
			log.debugWarning("CustomLabels [UIA]: failed to get automationId", exc_info=True)
			fields["automationId"] = ""
		fields["className"] = cls._safeGet(obj, "windowClassName", "", "windowClassName")
		return fields


class JABHandler(FingerprintHandler):
	backend_name = "JAB"

	@classmethod
	def can_handle(cls, obj):
		return isinstance(obj, JAB)

	@classmethod
	def get_fields(cls, obj):
		return {
			"windowClassName": cls._safeGet(obj, "windowClassName", "", "windowClassName"),
			"windowControlID": cls._safeGet(obj, "windowControlID", 0, "windowControlID"),
		}


class IA2Handler(FingerprintHandler):
	"""Fallback handler for IAccessible2 and any other framework."""
	backend_name = "IA2"

	@classmethod
	def can_handle(cls, obj):
		return True  # fallback — always last due to priority=100

	@classmethod
	def get_fields(cls, obj):
		return {
			"windowClassName": cls._safeGet(obj, "windowClassName", "", "windowClassName"),
			"windowControlID": cls._safeGet(obj, "windowControlID", 0, "windowControlID"),
		}


registerHandler(UIAHandler, priority=10)
registerHandler(JABHandler, priority=20)
registerHandler(IA2Handler, priority=100)  # fallback, always last


def getObjectFingerprint(obj):
	"""
	Return a stable fingerprint for an NVDAObject.
	Uses backend-specific properties plus the original name for differentiation.
	"""
	try:
		fp = {}

		# App name
		try:
			fp["app"] = obj.appModule.appName
		except Exception:
			log.debugWarning("CustomLabels: failed to get appName", exc_info=True)
			fp["app"] = "unknown"

		# Role
		try:
			fp["role"] = int(obj.role)
		except Exception:
			log.debugWarning("CustomLabels: failed to get role", exc_info=True)
			fp["role"] = 0

		# Original name - helps differentiate controls with different names
		# (e.g., labeled buttons vs unlabeled ones in the same app)
		# Use _get_name() to bypass any custom label overlay and get the real name
		try:
			if hasattr(obj, '_get_name'):
				fp["name"] = obj._get_name() or ""
			else:
				fp["name"] = obj.name or ""
		except Exception:
			log.debugWarning("CustomLabels: failed to get name", exc_info=True)
			fp["name"] = ""

		# Description - helps differentiate controls with the same name
		# (e.g., multiple "Filter Options" buttons in Java apps like Ghidra)
		try:
			fp["description"] = obj.description or ""
		except Exception:
			log.debugWarning("CustomLabels: failed to get description", exc_info=True)
			fp["description"] = ""

		# Parent name - helps differentiate controls in different
		# toolbars/panels that otherwise have identical properties
		try:
			parent = obj.parent
			fp["parentName"] = parent.name or "" if parent else ""
		except Exception:
			log.debugWarning("CustomLabels: failed to get parentName", exc_info=True)
			fp["parentName"] = ""

		# Framework-specific fields
		handler = _getHandler(obj)
		if handler is None:
			log.debugWarning("CustomLabels: no fingerprint handler matched for object")
			return None

		fp["backend"] = handler.backend_name
		fp.update(handler.get_fields(obj))

		# Convert to hashable tuple
		return tuple(sorted(fp.items()))

	except Exception:
		log.debugWarning("CustomLabels: unexpected error building fingerprint", exc_info=True)
		return None


def fingerprintToDict(fp):
	"""Convert a fingerprint tuple back to a dict."""
	if fp:
		return dict(fp)
	return {}
