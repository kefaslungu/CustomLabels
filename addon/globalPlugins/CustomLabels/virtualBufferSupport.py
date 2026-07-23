# virtualBufferSupport
# A part of Custom Labels addon for NVDA
# Injects custom labels into virtual buffer (browse mode) content.
# copyright: 2026 Kefas Lungu
# This file is licensed under the GNU General Public License v2.
# See the file COPYING.txt for details.

# How this works:
# When a VirtualBuffer TreeInterceptor enters browse mode, we patch _getFieldsInRange
# on its TextInfo class.
#
# _getFieldsInRange(start, end) is called by NVDA for every text range read — whether
# the user arrows by character, word, line, or lands on an element via Tab/QuickNav.
# It returns a list of FieldCommand and str items corresponding to the requested slice.
#
# For labeled controls we:
# 1. Look up the label for each controlStart using the cached fingerprint.
# 2. Find the control's first buffer offset via _getOffsetsFromFieldIdentifier().
# 3. At the first character stop of the control (currentOffset == controlTextStart):
#    emit the full label string.
# 4. At subsequent character stops within the same control: emit "" (silence), so the
#    user does not re-hear the label on every arrow press through the original text.
#
# This matches how aria-label works in browsers: the first (and only meaningful)
# character stop speaks the label; the remaining internal offsets are silent.
#
# A per-interceptor cache keyed on (docHandle, ID) -> label|None avoids
# re-fingerprinting the same object on every arrow key press.

import api
import textInfos
import treeInterceptorHandler
from logHandler import log

from .fingerPrintReader import getObjectFingerprint
from .labeler import getLabel


# id(treeInterceptor) -> {(docHandle, ID): label or None}
_interceptorCaches: dict = {}

# id(treeInterceptor) -> (TextInfoClass, original__getFieldsInRange)
_patches: dict = {}

# id(treeInterceptor) -> treeInterceptor
_activeInterceptors: dict = {}


def _lookupLabel(treeInterceptor, tiId, docHandle, ID):
	"""Look up the custom label for a buffer node, using the per-interceptor cache.

	Returns the label string if one exists, or None.
	Populates the cache on first access for each (docHandle, ID) pair.
	"""
	cache = _interceptorCaches.get(tiId)
	if cache is None:
		return None

	cacheKey = (docHandle, ID)
	if cacheKey in cache:
		return cache[cacheKey]

	# Cache miss — reconstruct NVDAObject and fingerprint it
	try:
		obj = treeInterceptor.getNVDAObjectFromIdentifier(docHandle, ID)
	except Exception:
		cache[cacheKey] = None
		return None

	if obj is None:
		cache[cacheKey] = None
		return None

	try:
		fp = getObjectFingerprint(obj)
		label = getLabel(fp) if fp else None
	except Exception:
		log.debugWarning("CustomLabels: error fingerprinting browse mode object", exc_info=True)
		label = None

	cache[cacheKey] = label
	if label:
		log.debug(f"CustomLabels [browse]: cached label '{label}' for node ({docHandle}, {ID})")
	return label


def _makeGetFieldsInRange(originalMethod, treeInterceptor):
	"""Return a patched _getFieldsInRange that replaces buffer text for labeled controls.

	Only active during browse mode (passThrough=False). In focus mode, Tab navigation
	is handled by chooseNVDAObjectOverlayClasses — we must not touch the buffer text
	there or controls will be silenced.

	For each labeled control we replace the text at its first buffer offset with the
	full label, and empty the text at any remaining offsets within the control.
	This makes character-by-character and word-by-word navigation work correctly:
	the first character stop inside a labeled control speaks the full label, and
	subsequent stops within the same control are silent (like embedded objects).
	"""
	tiId = id(treeInterceptor)

	def _patchedGetFieldsInRange(self, start, end):
		commandList = originalMethod(self, start, end)

		# Skip in focus/passThrough mode — chooseNVDAObjectOverlayClasses handles it.
		if treeInterceptor.passThrough:
			return commandList

		# labelStack entries: (label_or_None, controlStart_offset)
		# controlStart_offset is the first buffer offset of the control's text content.
		# We use it to decide whether to emit the full label or silence.
		labelStack = []
		result = []
		# Track the running buffer offset so we know where each text string sits.
		currentOffset = start

		for item in commandList:
			if isinstance(item, textInfos.FieldCommand):
				field = item.field
				if item.command == "controlStart" and field:
					docHandleStr = field.get("controlIdentifier_docHandle")
					IDStr = field.get("controlIdentifier_ID")
					label = None
					controlTextStart = None
					if docHandleStr is not None and IDStr is not None:
						try:
							docHandle = int(docHandleStr)
							ID = int(IDStr)
							label = _lookupLabel(treeInterceptor, tiId, docHandle, ID)
							if label:
								# Get the full offset range for this control in the buffer.
								# This tells us where its text content begins.
								try:
									controlTextStart, _ = self._getOffsetsFromFieldIdentifier(
										docHandle, ID
									)
								except (LookupError, ValueError):
									controlTextStart = None
						except (ValueError, TypeError):
							pass
					labelStack.append((label, controlTextStart))
					result.append(item)

				elif item.command == "controlEnd":
					if labelStack:
						labelStack.pop()
					result.append(item)
				else:
					result.append(item)

			elif isinstance(item, str):
				replaced = False
				if labelStack:
					label, controlTextStart = labelStack[-1]
					if label and controlTextStart is not None:
						if currentOffset == controlTextStart:
							# First character stop of this control: speak the full label.
							result.append(label)
							# Consume the same number of buffer offsets as the original text.
							currentOffset += len(item)
							# Neutralise so inner nested text is not also replaced.
							labelStack[-1] = (None, controlTextStart)
							replaced = True
						else:
							# Subsequent character stops within the same control: silence.
							result.append("")
							currentOffset += len(item)
							replaced = True
				if not replaced:
					result.append(item)
					currentOffset += len(item)
			else:
				result.append(item)

		return result

	return _patchedGetFieldsInRange


def _getTextInfoClass(treeInterceptor):
	"""Return the TextInfo class used by this TreeInterceptor, or None."""
	TextInfoClass = getattr(type(treeInterceptor), "TextInfo", None)
	if TextInfoClass is not None:
		return TextInfoClass
	try:
		ti = treeInterceptor.makeTextInfo(textInfos.POSITION_FIRST)
		return type(ti)
	except Exception:
		return None


def _patchInterceptor(treeInterceptor):
	"""Patch TextInfo methods on a VirtualBuffer TreeInterceptor."""
	tiId = id(treeInterceptor)
	if tiId in _patches:
		return

	if not hasattr(treeInterceptor, "getNVDAObjectFromIdentifier"):
		return

	TextInfoClass = _getTextInfoClass(treeInterceptor)
	if TextInfoClass is None:
		log.debugWarning("CustomLabels: could not find TextInfo class for TreeInterceptor")
		return

	origGetFields = getattr(TextInfoClass, "_getFieldsInRange", None)
	if origGetFields is None:
		log.debugWarning("CustomLabels: _getFieldsInRange not found on TextInfo class")
		return

	_interceptorCaches[tiId] = {}
	_patches[tiId] = (TextInfoClass, origGetFields)
	_activeInterceptors[tiId] = treeInterceptor

	TextInfoClass._getFieldsInRange = _makeGetFieldsInRange(origGetFields, treeInterceptor)
	log.debug(f"CustomLabels: browse mode patch applied for {type(treeInterceptor).__name__}")


def _unpatchInterceptor(treeInterceptor):
	"""Restore original TextInfo methods."""
	tiId = id(treeInterceptor)
	patch = _patches.pop(tiId, None)
	_interceptorCaches.pop(tiId, None)
	_activeInterceptors.pop(tiId, None)
	if patch is None:
		return
	TextInfoClass, origGetFields = patch
	TextInfoClass._getFieldsInRange = origGetFields
	log.debug(f"CustomLabels: browse mode patch removed for {type(treeInterceptor).__name__}")


def _onBrowseModeStateChange(browseMode: bool):
	"""Called when a TreeInterceptor switches between browse mode and focus mode."""
	try:
		focusObj = api.getFocusObject()
		ti = treeInterceptorHandler.getTreeInterceptor(focusObj)
	except Exception:
		return
	if ti is None:
		return
	if browseMode:
		_patchInterceptor(ti)
	else:
		_unpatchInterceptor(ti)


def initialize():
	"""Register for browse mode state changes."""
	treeInterceptorHandler.post_browseModeStateChange.register(_onBrowseModeStateChange)
	log.debug("CustomLabels: virtualBufferSupport initialized")


def terminate():
	"""Unregister and restore all patches."""
	treeInterceptorHandler.post_browseModeStateChange.unregister(_onBrowseModeStateChange)
	for tiId, (TextInfoClass, origGetFields) in list(_patches.items()):
		TextInfoClass._getFieldsInRange = origGetFields
	_patches.clear()
	_interceptorCaches.clear()
	_activeInterceptors.clear()
	log.debug("CustomLabels: virtualBufferSupport terminated")


def ensurePatched(treeInterceptor):
	"""Patch a TreeInterceptor if it is in browse mode and not already patched.

	Called from GlobalPlugin.event_gainFocus so the patch is applied whenever
	focus enters a virtual buffer document, not only when the mode toggles.
	"""
	tiId = id(treeInterceptor)
	if tiId in _patches:
		return
	if not treeInterceptor.passThrough:
		_patchInterceptor(treeInterceptor)


def invalidateCacheForLabel(_fingerprint):
	"""Clear all browse mode label caches after a label is set or removed."""
	_interceptorCaches.clear()
