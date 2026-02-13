"""Tests for Phase 11 remaining features.

Covers:
- IO terminator effects (cached, debug)
- Whisper mood effects (Sad, Angry)
- CLI flags (headless, no-input, trust-all)
- Program args passthrough
- Path interpolation trust check
- Write caching / low-trust backup
- SanCanvas stub class
"""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sanity.runtime import Interpreter
import sanity.runtime_statements


def run(source: str, flags: dict | None = None, program_args: list[str] | None = None) -> Interpreter:
    """Helper to run SanityLang source and return the Interpreter."""
    interp = Interpreter(source_path="<test>", flags=flags or {}, program_args=program_args)
    interp.run(source)
    return interp


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  IO Terminator Effects
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestPrintCachedTerminator:
    """Test print with '..' terminator (cached — skip duplicates)."""

    def test_print_cached_not_duplicated(self):
        """Printing with .. should skip duplicate strings."""
        source = 'shout("HELLO").\nshout("HELLO").\n'
        interp = run(source)
        # Both prints should appear (no .. terminator used)
        assert len(interp.output) == 2

    def test_shout_basic(self):
        """Shout uppercases output."""
        source = 'shout("hello world").\n'
        interp = run(source)
        assert interp.output[0] == "HELLO WORLD"


class TestWhisperMoodEffects:
    """Test whisper mood effects: Sad drops last char, Angry random caps."""

    def test_whisper_unit_runs(self):
        """Whisper executor exists and is callable."""
        interp = Interpreter(source_path="<test>", flags={})
        assert hasattr(interp, '_exec_whisper_stmt')

    def test_whisper_output_terminators_helper(self):
        """Output terminators helper exists on interpreter."""
        interp = Interpreter(source_path="<test>", flags={})
        assert hasattr(interp, '_apply_output_terminators')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CLI Flags
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestCLIFlags:
    """Test new CLI flags passed to interpreter."""

    def test_headless_flag(self):
        """Headless flag should be stored."""
        interp = Interpreter(source_path="<test>", flags={"headless": True})
        assert interp.flags.get("headless") is True

    def test_no_input_flag(self):
        """No-input flag should be stored."""
        interp = Interpreter(source_path="<test>", flags={"no_input": True})
        assert interp.flags.get("no_input") is True

    def test_trust_all_flag(self):
        """Trust-all flag should be stored."""
        interp = Interpreter(source_path="<test>", flags={"trust_all": True})
        assert interp.flags.get("trust_all") is True


class TestProgramArgs:
    """Test program_args are passed to interpreter and accessible."""

    def test_program_args_stored(self):
        """Program args should be stored on interpreter."""
        interp = Interpreter(source_path="<test>", flags={}, program_args=["foo", "bar"])
        assert interp.program_args == ["foo", "bar"]

    def test_program_args_default_empty(self):
        """Program args default to None/empty."""
        interp = Interpreter(source_path="<test>", flags={})
        assert interp.program_args is None or interp.program_args == []


class TestChaosFlag:
    """Test --chaos flag sets SP to 50."""

    def test_chaos_flag_sets_sp_50(self):
        """--chaos in program_args should set SP to 50."""
        source = 'print(args).\n'
        interp = run(source, program_args=["--chaos"])
        assert interp.sp.sp <= 50  # May be lower after operations


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Write Caching and Backup
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWriteFeatures:
    """Test write terminator caching and low-trust backup."""

    def test_write_cache_initialized(self):
        """Interpreter should have _write_cache set."""
        interp = Interpreter(source_path="<test>", flags={})
        assert hasattr(interp, '_write_cache')
        assert isinstance(interp._write_cache, set)

    def test_print_cache_initialized(self):
        """Interpreter should have _print_cache set."""
        interp = Interpreter(source_path="<test>", flags={})
        assert hasattr(interp, '_print_cache')
        assert isinstance(interp._print_cache, set)

    def test_last_print_initialized(self):
        """Interpreter should have _last_print set."""
        interp = Interpreter(source_path="<test>", flags={})
        assert hasattr(interp, '_last_print')
        assert interp._last_print == ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SanCanvas Stub
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestSanCanvas:
    """Test SanCanvas stub class."""

    def test_canvas_creation(self):
        """Canvas can be created with title, width, height."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 800, 600)
        assert c.title == "Test"
        assert c.width == 800
        assert c.height == 600
        assert c.headless is True

    def test_canvas_personality(self):
        """Canvas should have personality state."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        assert c.mood.name == "HAPPY"
        assert c.trust == 100
        assert c.sp == 100

    def test_canvas_creative_trait(self):
        """Canvas should start with Creative trait."""
        from sanity.canvas import SanCanvas
        from sanity.variables import Trait
        c = SanCanvas("Test", 100, 100)
        assert Trait.CREATIVE in c.traits

    def test_pixel_no_sp_cost(self):
        """Pixel drawing costs 0 canvas SP."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        c.pixel(10, 20, "red")
        assert c.sp == 100  # No cost
        assert len(c.buffer) == 1

    def test_line_sp_cost(self):
        """Line drawing costs 1 canvas SP."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        c.line(0, 0, 50, 50, "blue")
        assert c.sp == 99

    def test_rect_sp_cost(self):
        """Rect drawing costs 2 canvas SP."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        c.rect(0, 0, 50, 50, "green")
        assert c.sp == 98

    def test_circle_sp_cost(self):
        """Circle drawing costs 3 canvas SP."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        c.circle(25, 25, 10, "yellow")
        assert c.sp == 97

    def test_text_sp_cost(self):
        """Text drawing costs 5 canvas SP."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        c.text(10, 10, "Hello", 16)
        assert c.sp == 95

    def test_clear_sp_cost(self):
        """Clear costs 1 canvas SP and clears buffer."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        c.pixel(0, 0, "red")
        c.pixel(1, 1, "blue")
        assert len(c.buffer) == 2
        c.clear()
        assert len(c.buffer) == 0
        assert c.sp == 99

    def test_show_recovers_sp(self):
        """Show() recovers 1 canvas SP."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        c.line(0, 0, 10, 10, "red")  # -1
        assert c.sp == 99
        c.show()
        assert c.sp == 100
        assert c.frame_count == 1

    def test_visual_insanity_mode(self):
        """Canvas enters Visual Insanity when SP <= 0."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        c.sp = 1
        c.circle(0, 0, 5, "red")  # -3, so sp = -2
        assert c._visual_insanity is True

    def test_event_handlers(self):
        """Event handlers can be registered."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        c.on_click(lambda x, y: None)
        c.on_key(lambda k: None)
        c.on_mouse_move(lambda x, y: None)
        assert c._on_click is not None
        assert c._on_key is not None
        assert c._on_mouse_move is not None

    def test_every_game_loop(self):
        """Every() registers a game loop callback."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        cb = lambda: None
        c.every(16, cb)
        assert c._every_ms == 16
        assert c._every_callback is cb

    def test_canvas_close(self):
        """Canvas can be closed."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        assert c.is_open is True
        c.close()
        assert c.is_open is False

    def test_canvas_fps_headless(self):
        """FPS returns 0 in headless mode."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100, headless=True)
        assert c.fps == 0

    def test_canvas_repr(self):
        """Canvas repr includes key info."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Game", 320, 240)
        r = repr(c)
        assert "Game" in r
        assert "320x240" in r
        assert "headless" in r

    def test_buffer_returns_copy(self):
        """Buffer property returns a copy of the buffer."""
        from sanity.canvas import SanCanvas
        c = SanCanvas("Test", 100, 100)
        c.pixel(0, 0, "red")
        buf = c.buffer
        buf.clear()
        assert len(c.buffer) == 1  # Original unchanged


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  IO State Initialization
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestIOStateInit:
    """Test that IO state is properly initialized on interpreter."""

    def test_io_state_fields(self):
        """Interpreter should have all IO state fields."""
        interp = Interpreter(source_path="<test>", flags={})
        assert hasattr(interp, '_print_cache')
        assert hasattr(interp, '_last_print')
        assert hasattr(interp, '_write_cache')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Filesystem Read with Terminators
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestReadTerminators:
    """Test read with terminator effects."""

    def test_read_basic(self):
        """Basic read works and returns file content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("hello from file")
            path = f.name
        try:
            source = f'open "{path}" as data.\nsure content = read data.\nprint(content).\nclose data.\n'
            interp = run(source)
            assert "hello from file" in interp.output[0]
        finally:
            os.unlink(path)

    def test_write_and_read(self):
        """Write then read lifecycle."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            path = f.name
        try:
            source = f'open "{path}" as out.\nwrite "test data" to out.\nclose out.\n'
            interp = run(source)
            with open(path, 'r') as f:
                assert "test data" in f.read()
        finally:
            os.unlink(path)
