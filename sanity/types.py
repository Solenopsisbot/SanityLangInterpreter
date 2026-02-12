"""Type system for (In)SanityLang."""
from __future__ import annotations
from enum import Enum, auto
from typing import Any, Optional
import random
import math


class SanType(Enum):
    NUMBER = "Number"
    WORD = "Word"
    YEP = "Yep"
    NOPE = "Nope"
    DUNNO = "Dunno"
    VOID = "Void"
    LIST = "List"
    BLOB = "Blob"
    FUNCTION = "Function"
    PERSONALITY = "Personality"
    INSTANCE = "Instance"


class SanValue:
    """Wraps a Python value with its SanityLang type."""

    __slots__ = ("value", "type", "_observed_dunno")

    def __init__(self, value: Any, san_type: SanType):
        self.value = value
        self.type = san_type
        self._observed_dunno: Optional[bool] = None  # Locked dunno truthiness

    def __repr__(self):
        return f"SanValue({self.type.value}: {self.value!r})"

    def __str__(self):
        if self.type == SanType.VOID:
            return "Void"
        if self.type == SanType.YEP:
            return "yep"
        if self.type == SanType.NOPE:
            return "nope"
        if self.type == SanType.DUNNO:
            return "dunno"
        if self.type == SanType.LIST:
            inner = ", ".join(str(v) for v in self.value)
            return f"[{inner}]"
        if self.type == SanType.BLOB:
            pairs = ", ".join(f"{k}: {v}" for k, v in self.value.items())
            return f"{{{pairs}}}"
        return str(self.value)

    def copy(self) -> SanValue:
        if self.type == SanType.LIST:
            return SanValue([v.copy() for v in self.value], self.type)
        if self.type == SanType.BLOB:
            return SanValue({k: v.copy() for k, v in self.value.items()}, self.type)
        return SanValue(self.value, self.type)


# ============================================================
# Constructors
# ============================================================

def san_number(value: float | int) -> SanValue:
    return SanValue(float(value) if isinstance(value, float) else value, SanType.NUMBER)

def san_word(value: str) -> SanValue:
    return SanValue(value, SanType.WORD)

def san_yep() -> SanValue:
    return SanValue(True, SanType.YEP)

def san_nope() -> SanValue:
    return SanValue(False, SanType.NOPE)

def san_dunno() -> SanValue:
    return SanValue(None, SanType.DUNNO)

def san_void() -> SanValue:
    return SanValue(None, SanType.VOID)

def san_list(elements: list[SanValue]) -> SanValue:
    return SanValue(elements, SanType.LIST)

def san_blob(pairs: dict[str, SanValue]) -> SanValue:
    return SanValue(pairs, SanType.BLOB)


# ============================================================
# Type Coercion (§5)
# ============================================================

def coerce(left: SanValue, right: SanValue, operator: str) -> tuple[SanValue, SanValue, bool, bool]:
    """
    Coerce two values for an operation. Returns (left, right, left_was_coerced, right_was_coerced).
    Follows §5 coercion rules in order.
    """
    left_coerced = False
    right_coerced = False

    # Rule 1: Void propagates
    if left.type == SanType.VOID or right.type == SanType.VOID:
        return left, right, False, False  # Will produce Void result

    # Rule 2: Dunno propagates
    if left.type == SanType.DUNNO or right.type == SanType.DUNNO:
        return left, right, False, False  # Will produce Dunno result

    # Rule 3 & 4: Yep/Nope coercion
    if left.type in (SanType.YEP, SanType.NOPE):
        if right.type == SanType.NUMBER:
            left = san_number(1 if left.type == SanType.YEP else 0)
            left_coerced = True
        elif right.type == SanType.WORD:
            left = san_word("yep" if left.type == SanType.YEP else "nope")
            left_coerced = True

    if right.type in (SanType.YEP, SanType.NOPE):
        if left.type == SanType.NUMBER:
            right = san_number(1 if right.type == SanType.YEP else 0)
            right_coerced = True
        elif left.type == SanType.WORD:
            right = san_word("yep" if right.type == SanType.YEP else "nope")
            right_coerced = True

    # Rule 5: Number/Word — depends on operator
    if left.type == SanType.NUMBER and right.type == SanType.WORD:
        if operator == "&":
            left = san_word(str(left.value))
            left_coerced = True
        else:
            try:
                right = san_number(float(right.value))
                right_coerced = True
            except (ValueError, TypeError):
                right = san_number(0)
                right_coerced = True

    elif left.type == SanType.WORD and right.type == SanType.NUMBER:
        if operator == "&":
            right = san_word(str(right.value))
            right_coerced = True
        else:
            try:
                left = san_number(float(left.value))
                left_coerced = True
            except (ValueError, TypeError):
                left = san_number(0)
                left_coerced = True

    # Rule 6: List coercion
    if left.type == SanType.LIST and right.type == SanType.NUMBER:
        left = san_number(len(left.value))
        left_coerced = True
    elif left.type == SanType.LIST and right.type == SanType.WORD:
        left = san_word(str(left))
        left_coerced = True
    elif right.type == SanType.LIST and left.type == SanType.NUMBER:
        right = san_number(len(right.value))
        right_coerced = True
    elif right.type == SanType.LIST and left.type == SanType.WORD:
        right = san_word(str(right))
        right_coerced = True

    return left, right, left_coerced, right_coerced


# ============================================================
# Truthiness (§5)
# ============================================================

def is_truthy(value: SanValue, scope_id: int = 0) -> bool:
    """
    Evaluate truthiness per §5 rules.
    Returns (truthy, is_void_check) — caller should deduct SP if void.
    """
    if value.type == SanType.VOID:
        return False
    if value.type == SanType.NOPE:
        return False
    if value.type == SanType.YEP:
        return True
    if value.type == SanType.NUMBER:
        return value.value != 0
    if value.type == SanType.WORD:
        return value.value != ""
    if value.type == SanType.DUNNO:
        # Consistent within a scope, varies across scopes
        if value._observed_dunno is not None:
            return value._observed_dunno
        # Use scope_id as seed for consistency
        result = (hash(scope_id) % 2) == 0
        value._observed_dunno = result
        return result
    if value.type == SanType.LIST:
        return len(value.value) > 0
    if value.type == SanType.BLOB:
        return len(value.value) > 0
    return True


def is_void(value: SanValue) -> bool:
    return value.type == SanType.VOID


def type_name(value: SanValue) -> str:
    return value.type.value


# ============================================================
# Comparison helpers
# ============================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def vibes_equal(left: SanValue, right: SanValue) -> bool:
    """~= comparison: same type and 'close enough' (§7)."""
    if left.type != right.type:
        return False
    if left.type == SanType.NUMBER:
        if left.value == 0 and right.value == 0:
            return True
        if left.value == 0 or right.value == 0:
            return abs(left.value - right.value) <= 0.2
        return abs(left.value - right.value) / max(abs(left.value), abs(right.value)) <= 0.2
    if left.type == SanType.WORD:
        return levenshtein_distance(left.value, right.value) <= 3
    return left.value == right.value


def loose_equal(left: SanValue, right: SanValue) -> bool:
    """== comparison: same value after coercion."""
    if left.type == right.type:
        return left.value == right.value
    # Coerce and compare
    l, r, _, _ = coerce(left, right, "==")
    return l.value == r.value


def strict_equal(left: SanValue, right: SanValue) -> bool:
    """=== comparison: same value AND same type."""
    return left.type == right.type and left.value == right.value
