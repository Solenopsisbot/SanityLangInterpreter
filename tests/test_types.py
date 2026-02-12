"""Tests for the SanityLang type system."""
import pytest
from sanity.types import (
    SanValue, SanType,
    san_number, san_word, san_yep, san_nope, san_dunno, san_void, san_list, san_blob,
    coerce, is_truthy, is_void, type_name,
    vibes_equal, loose_equal, strict_equal, levenshtein_distance,
)


class TestSanValueCreation:
    def test_number(self):
        v = san_number(42)
        assert v.type == SanType.NUMBER
        assert v.value == 42

    def test_float_number(self):
        v = san_number(3.14)
        assert v.type == SanType.NUMBER
        assert v.value == 3.14

    def test_word(self):
        v = san_word("hello")
        assert v.type == SanType.WORD
        assert v.value == "hello"

    def test_yep(self):
        v = san_yep()
        assert v.type == SanType.YEP
        assert v.value is True

    def test_nope(self):
        v = san_nope()
        assert v.type == SanType.NOPE
        assert v.value is False

    def test_dunno(self):
        v = san_dunno()
        assert v.type == SanType.DUNNO
        assert v.value is None

    def test_void(self):
        v = san_void()
        assert v.type == SanType.VOID

    def test_list(self):
        v = san_list([san_number(1), san_number(2)])
        assert v.type == SanType.LIST
        assert len(v.value) == 2

    def test_blob(self):
        v = san_blob({"name": san_word("test")})
        assert v.type == SanType.BLOB
        assert "name" in v.value

    def test_copy_number(self):
        v = san_number(42)
        c = v.copy()
        assert c.value == 42
        assert c is not v

    def test_copy_list_deep(self):
        v = san_list([san_number(1)])
        c = v.copy()
        assert c.value[0].value == 1
        assert c.value[0] is not v.value[0]


class TestTruthiness:
    """§5 truthiness rules."""
    def test_void_is_falsy(self):
        assert is_truthy(san_void()) is False

    def test_nope_is_falsy(self):
        assert is_truthy(san_nope()) is False

    def test_yep_is_truthy(self):
        assert is_truthy(san_yep()) is True

    def test_zero_is_falsy(self):
        assert is_truthy(san_number(0)) is False

    def test_nonzero_is_truthy(self):
        assert is_truthy(san_number(42)) is True

    def test_negative_is_truthy(self):
        assert is_truthy(san_number(-1)) is True

    def test_empty_string_is_falsy(self):
        assert is_truthy(san_word("")) is False

    def test_nonempty_string_is_truthy(self):
        assert is_truthy(san_word("hi")) is True

    def test_empty_list_is_falsy(self):
        assert is_truthy(san_list([])) is False

    def test_nonempty_list_is_truthy(self):
        assert is_truthy(san_list([san_number(1)])) is True

    def test_empty_blob_is_falsy(self):
        assert is_truthy(san_blob({})) is False

    def test_nonempty_blob_is_truthy(self):
        assert is_truthy(san_blob({"a": san_number(1)})) is True

    def test_dunno_is_consistent_within_scope(self):
        v = san_dunno()
        result1 = is_truthy(v, scope_id=42)
        result2 = is_truthy(v, scope_id=42)
        assert result1 == result2


class TestCoercion:
    """§5 coercion rules."""
    def test_void_propagates(self):
        l, r, lc, rc = coerce(san_void(), san_number(5), "+")
        assert l.type == SanType.VOID

    def test_dunno_propagates(self):
        l, r, lc, rc = coerce(san_dunno(), san_number(5), "+")
        assert l.type == SanType.DUNNO

    def test_yep_to_number(self):
        l, r, lc, rc = coerce(san_yep(), san_number(5), "+")
        assert l.type == SanType.NUMBER
        assert l.value == 1
        assert lc is True

    def test_nope_to_number(self):
        l, r, lc, rc = coerce(san_nope(), san_number(5), "+")
        assert l.type == SanType.NUMBER
        assert l.value == 0

    def test_yep_to_word(self):
        l, r, lc, rc = coerce(san_yep(), san_word("x"), "+")
        assert l.type == SanType.WORD
        assert l.value == "yep"

    def test_number_word_arithmetic(self):
        l, r, lc, rc = coerce(san_number(5), san_word("3"), "+")
        assert r.type == SanType.NUMBER
        assert r.value == 3.0

    def test_number_word_concat(self):
        l, r, lc, rc = coerce(san_number(5), san_word("hello"), "&")
        assert l.type == SanType.WORD
        assert l.value == "5"

    def test_list_to_number(self):
        l, r, lc, rc = coerce(san_list([san_number(1), san_number(2)]), san_number(3), "+")
        assert l.type == SanType.NUMBER
        assert l.value == 2  # length


class TestComparisons:
    def test_vibes_equal_numbers_close(self):
        assert vibes_equal(san_number(10), san_number(11)) is True

    def test_vibes_equal_numbers_far(self):
        assert vibes_equal(san_number(10), san_number(50)) is False

    def test_vibes_equal_words_close(self):
        assert vibes_equal(san_word("hello"), san_word("hallo")) is True

    def test_vibes_equal_words_far(self):
        assert vibes_equal(san_word("hello"), san_word("xyzzy")) is False

    def test_vibes_equal_different_types(self):
        assert vibes_equal(san_number(1), san_word("1")) is False

    def test_loose_equal_same_type(self):
        assert loose_equal(san_number(5), san_number(5)) is True

    def test_loose_equal_coerced(self):
        assert loose_equal(san_yep(), san_number(1)) is True

    def test_strict_equal(self):
        assert strict_equal(san_number(5), san_number(5)) is True
        assert strict_equal(san_yep(), san_number(1)) is False

    def test_levenshtein(self):
        assert levenshtein_distance("kitten", "sitting") == 3
        assert levenshtein_distance("", "abc") == 3
        assert levenshtein_distance("same", "same") == 0


class TestStr:
    def test_void_str(self):
        assert str(san_void()) == "Void"

    def test_yep_str(self):
        assert str(san_yep()) == "yep"

    def test_nope_str(self):
        assert str(san_nope()) == "nope"

    def test_number_str(self):
        assert str(san_number(42)) == "42"

    def test_word_str(self):
        assert str(san_word("hello")) == "hello"

    def test_list_str(self):
        s = str(san_list([san_number(1), san_number(2)]))
        assert "1" in s and "2" in s

    def test_type_name(self):
        assert type_name(san_number(0)) == "Number"
        assert type_name(san_word("")) == "Word"
        assert type_name(san_void()) == "Void"
