"""Tests for the SanityLang Sanity Points system."""
import pytest
from sanity.sanity_points import SanityTracker


class TestBasicSP:
    def test_initial_sp(self):
        sp = SanityTracker()
        assert sp.sp == 100

    def test_initial_chaos(self):
        sp = SanityTracker(initial=0)
        assert sp.sp == 0
        assert sp.insanity_mode is True

    def test_insanity_mode_threshold(self):
        sp = SanityTracker(initial=1)
        assert sp.insanity_mode is False
        sp.sp = 0
        assert sp.insanity_mode is True

    def test_auto_terminator_high_sp(self):
        sp = SanityTracker(initial=90)
        assert sp.get_auto_terminator() == "."

    def test_auto_terminator_medium_sp(self):
        sp = SanityTracker(initial=60)
        assert sp.get_auto_terminator() == "?"

    def test_auto_terminator_low_sp(self):
        sp = SanityTracker(initial=30)
        assert sp.get_auto_terminator() == "~"

    def test_auto_terminator_critical_sp(self):
        sp = SanityTracker(initial=10)
        assert sp.get_auto_terminator() == "!"


class TestSPActions:
    def test_single_char_name(self):
        sp = SanityTracker()
        sp.single_char_name()
        assert sp.sp == 95

    def test_long_name(self):
        sp = SanityTracker()
        sp.long_name()
        assert sp.sp == 98

    def test_override_sure(self):
        sp = SanityTracker()
        sp.override_sure()
        assert sp.sp == 90

    def test_whatever_declaration(self):
        sp = SanityTracker()
        sp.whatever_declaration()
        assert sp.sp == 97  # -3 at compile time

    def test_whatever_runtime(self):
        sp = SanityTracker()
        sp.is_runtime = True
        sp.whatever_declaration()
        assert sp.sp == 94  # -6 at runtime

    def test_first_function_call(self):
        sp = SanityTracker()
        sp.first_function_call()
        assert sp.sp == 101

    def test_repetition_penalty(self):
        sp = SanityTracker()
        sp.repetition_penalty()
        assert sp.sp == 99

    def test_pinky_break(self):
        sp = SanityTracker()
        sp.pinky_break()
        assert sp.sp == 85

    def test_bet_win(self):
        sp = SanityTracker()
        sp.bet_win(20)
        assert sp.sp == 120

    def test_bet_lose(self):
        sp = SanityTracker()
        sp.bet_lose(15)
        assert sp.sp == 85

    def test_i_am_okay(self):
        sp = SanityTracker()
        sp.i_am_okay()
        assert sp.sp == 50

    def test_jackpot(self):
        sp = SanityTracker()
        sp.jackpot_win()
        assert sp.sp == 150

    def test_curse_declaration(self):
        sp = SanityTracker()
        sp.curse_declaration()
        assert sp.sp == 80

    def test_curse_runtime(self):
        sp = SanityTracker()
        sp.is_runtime = True
        sp.curse_declaration()
        assert sp.sp == 60


class TestSPModifiers:
    def test_strict_doubles_penalties(self):
        sp = SanityTracker(strict=True)
        sp.single_char_name()  # -5 * 2 = -10
        assert sp.sp == 90

    def test_pray_mercy_halves_penalties(self):
        sp = SanityTracker(pray_mercy=True)
        sp.single_char_name()  # -5 // 2 = -3 (Python floor div)
        assert sp.sp == 97

    def test_lenient_floor(self):
        sp = SanityTracker(initial=15, lenient=True)
        sp.override_sure()  # -10 would make 5, but lenient floors at 10
        assert sp.sp == 10
        assert sp.insanity_mode is False

    def test_strict_and_pray_interact(self):
        sp = SanityTracker(strict=True, pray_mercy=True)
        sp.single_char_name()  # (-5 * 2) // 2 = -5
        assert sp.sp == 95


class TestSPSpecialActions:
    def test_enter_scope(self):
        sp = SanityTracker()
        sp.enter_scope()
        assert sp.sp == 101

    def test_wasted_scope(self):
        sp = SanityTracker()
        sp.wasted_scope()
        assert sp.sp == 96

    def test_dream_fulfilled(self):
        sp = SanityTracker()
        sp.dream_fulfilled()
        assert sp.sp == 105

    def test_bond_formed(self):
        sp = SanityTracker()
        sp.bond_formed()
        assert sp.sp == 102

    def test_bond_broken(self):
        sp = SanityTracker()
        sp.bond_broken()
        assert sp.sp == 93

    def test_no_fun_at_parties(self):
        sp = SanityTracker()
        sp.no_fun_at_parties()
        assert sp.sp == 105

    def test_pray_for_chaos(self):
        sp = SanityTracker()
        sp.pray_for_chaos()
        assert sp.sp == 0
        assert sp.insanity_mode is True

    def test_pray_for_nothing(self):
        sp = SanityTracker()
        sp.pray_for_nothing()
        assert sp.sp == 101

    def test_reset(self):
        sp = SanityTracker(initial=50)
        sp.reset(100)
        assert sp.sp == 100


class TestSPListener:
    def test_threshold_listener(self):
        events = []
        sp = SanityTracker(initial=95)
        sp.add_listener(lambda old, new: events.append((old, new)))
        sp.sp = 85  # Crosses 90
        assert len(events) == 1
        assert events[0] == (95, 85)

    def test_no_listener_same_threshold(self):
        events = []
        sp = SanityTracker(initial=95)
        sp.add_listener(lambda old, new: events.append((old, new)))
        sp.sp = 93  # Same threshold (90s)
        assert len(events) == 0
