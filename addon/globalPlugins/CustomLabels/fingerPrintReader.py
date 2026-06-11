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
	def needs_disambiguation(cls, fields: dict) -> bool:
		"""Return True if the primary fields are too weak to uniquely identify the control."""
		return False

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


def _addDisambiguation(obj, fp):
	"""Add positional disambiguation fields when primary identifiers are weak.

	Uses parent automationId/class and sibling index. These are positional so
	they can shift if the app dynamically adds/removes controls, but they are
	the best available option when no stable ID exists.

	NOTE: Do NOT call obj.parent.children (sibling iteration) here —
	it freezes NVDA. Use indexInParent instead.
	"""
	try:
		parent = obj.parent
		if parent is None:
			fp["parentAutoId"] = ""
			fp["parentClass"] = ""
			fp["siblingIndex"] = -1
			return

		# Parent automationId (UIA only, safe to try on any object)
		try:
			fp["parentAutoId"] = parent.UIAElement.currentAutomationId or ""
		except Exception:
			fp["parentAutoId"] = ""

		fp["parentClass"] = ""
		try:
			fp["parentClass"] = parent.windowClassName or ""
		except Exception:
			pass

		# Sibling index — use indexInParent, never iterate children
		try:
			fp["siblingIndex"] = obj.indexInParent if obj.indexInParent is not None else -1
		except Exception:
			fp["siblingIndex"] = -1

	except Exception:
		log.debugWarning("CustomLabels: failed to add disambiguation fields", exc_info=True)
		fp["parentAutoId"] = ""
		fp["parentClass"] = ""
		fp["siblingIndex"] = -1


class UIAHandler(FingerprintHandler):
	backend_name = "UIA"

	# FrameworkId values that indicate web/Chromium content
	_WEB_FRAMEWORKS = {"Chrome"}

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

		# Detect the underlying UI framework — kept internal, not stored in the
		# fingerprint, to avoid breaking existing saved labels.
		frameworkId = ""
		try:
			frameworkId = obj.UIAElement.currentFrameworkId or ""
		except Exception:
			log.debugWarning("CustomLabels [UIA]: failed to get frameworkId", exc_info=True)

		# For web/Chromium content only, include ARIA fields as a stable
		# middle tier — they map from HTML attributes (aria-label, aria-describedby,
		# etc.) and survive app restarts unlike positional fields.
		# Only add them when non-empty so existing labels without these fields
		# continue to match (backward compatible).
		if frameworkId in cls._WEB_FRAMEWORKS:
			try:
				ariaProps = obj.UIAElement.currentAriaProperties or ""
			except Exception:
				log.debugWarning("CustomLabels [UIA]: failed to get ariaProperties", exc_info=True)
				ariaProps = ""
			try:
				ariaRole = obj.UIAElement.currentAriaRole or ""
			except Exception:
				log.debugWarning("CustomLabels [UIA]: failed to get ariaRole", exc_info=True)
				ariaRole = ""
			if ariaProps:
				fields["ariaProperties"] = ariaProps
			if ariaRole:
				fields["ariaRole"] = ariaRole

		# Store frameworkId on the fields dict under a private key so
		# needs_disambiguation can read it without it entering the fingerprint.
		fields["_frameworkId"] = frameworkId
		return fields

	@classmethod
	def needs_disambiguation(cls, fields: dict) -> bool:
		# automationId empty means we have no stable unique ID.
		# For web frameworks, ARIA fields may serve as a stable middle tier,
		# so only fall back to positional disambiguation if those are also empty.
		if fields.get("automationId"):
			return False
		if fields.get("_frameworkId") in cls._WEB_FRAMEWORKS:
			if fields.get("ariaProperties") or fields.get("ariaRole"):
				return False
		return True


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
		fields = {
			"windowClassName": cls._safeGet(obj, "windowClassName", "", "windowClassName"),
		}

		# For Ia2Web objects (Chromium/WebView2/Electron), windowControlID is a
		# renderer-window handle that changes every restart and is shared across
		# all elements — it provides no identification value and must be excluded.
		# For all other IA2 objects, include it as it is a stable control identifier.
		if not _isIa2Web(obj):
			fields["windowControlID"] = cls._safeGet(obj, "windowControlID", 0, "windowControlID")

		return fields

	@classmethod
	def needs_disambiguation(cls, fields: dict) -> bool:
		# windowControlID of 0 means no useful ID for non-web IA2 objects.
		if fields.get("windowControlID") == 0:
			return True
		# Ia2Web objects never have windowControlID in their fields (excluded above).
		# For them, windowClassName + role + name + description + parentName
		# (added by getObjectFingerprint) are the only safe stable fields.
		# Positional disambiguation is unsafe here (IA2Attributes unavailable during
		# chooseNVDAObjectOverlayClasses, and windowControlID changes every restart).
		if fields.get("windowClassName") == "Chrome_RenderWidgetHostHWND":
			return False
		return False


registerHandler(UIAHandler, priority=10)
registerHandler(JABHandler, priority=20)
registerHandler(IA2Handler, priority=100)  # fallback, always last


_IA2WEB_WINDOW_CLASSES = {"Chrome_RenderWidgetHostHWND"}


def _isIa2Web(obj):
	"""Return True if obj is a Chromium/WebView2 web content object.

	Detects by windowClassName rather than isinstance() — the class name is
	stable and available at all object construction stages, including during
	chooseNVDAObjectOverlayClasses before overlay classes are applied.
	"""
	try:
		return obj.windowClassName in _IA2WEB_WINDOW_CLASSES
	except Exception:
		return False


def getObjectFingerprint(obj):
	"""
	Return a stable fingerprint for an NVDAObject.
	Uses backend-specific properties plus the original name for differentiation.
	When primary identifiers are weak (e.g. empty automationId, or web content
	where controlID is shared), positional disambiguation fields are added.
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

		# Original name - helps differentiate controls with different names.
		# Prefer _get_name() to bypass any custom label overlay, but fall back to
		# obj.name if _get_name() returns empty — during chooseNVDAObjectOverlayClasses
		# the IAccessible COM call may not be ready yet for partially constructed objects,
		# while NVDA's cached obj.name (populated from the focus event) is reliable.
		try:
			name = ""
			if hasattr(obj, '_get_name'):
				try:
					name = obj._get_name() or ""
				except Exception:
					pass
			if not name:
				name = obj.name or ""
			fp["name"] = name
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
		backendFields = handler.get_fields(obj)
		# Strip private keys (prefixed with _) before updating fp —
		# they are for internal handler logic only and must not enter the fingerprint.
		fp.update({k: v for k, v in backendFields.items() if not k.startswith("_")})

		# Add positional disambiguation when primary IDs are too weak.
		# Each handler's needs_disambiguation() decides based on what fields it collected.
		if handler.needs_disambiguation(backendFields):
			log.debug(f"CustomLabels: weak fingerprint for '{fp.get('app')}', adding disambiguation")
			_addDisambiguation(obj, fp)

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
