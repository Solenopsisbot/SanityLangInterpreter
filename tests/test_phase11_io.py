"""Tests for Phase 11 IO, filesystem, args, and stdlib features."""
import os
import sys
import tempfile
import pytest

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sanity.runtime import Interpreter


def run(source: str, program_args: list[str] | None = None) -> Interpreter:
    """Run source and return the interpreter."""
    interp = Interpreter(program_args=program_args)
    interp.run(source)
    return interp


# ===================================================================
# Console IO tests
# ===================================================================


class TestShout:
    def test_shout_uppercase(self):
        interp = run('shout("hello world").')
        assert interp.output[0] == "HELLO WORLD"

    def test_shout_sp_cost(self):
        interp = run('shout("x").')
        assert interp.sp.sp < 100  # SP should decrease

    def test_shout_number(self):
        interp = run("shout(42).")
        assert interp.output[0] == "42"


# ===================================================================
# Args and flags built-in variables
# ===================================================================


class TestArgs:
    def test_args_available(self):
        """args variable should exist in global scope."""
        interp = run('print(args).')
        assert len(interp.output) > 0

    def test_args_with_values(self):
        """args should contain program arguments."""
        interp = run(
            'print(args).',
            program_args=["hello", "world"],
        )
        output = interp.output[0]
        assert "hello" in output
        assert "world" in output

    def test_args_tainted_trait(self):
        """args variable should have Tainted trait."""
        from sanity.variables import Trait
        interp = run('print(args).', program_args=["test"])
        args_var = interp.global_env.get("args")
        assert args_var is not None
        assert Trait.TAINTED in args_var.traits

    def test_args_trust_30(self):
        """args variable should have Trust 30."""
        interp = run('print(args).', program_args=["test"])
        args_var = interp.global_env.get("args")
        assert args_var is not None
        assert args_var.trust == 30

    def test_flags_available(self):
        """flags variable should exist in global scope."""
        interp = run('print(flags).')
        assert len(interp.output) > 0

    def test_flags_parsed_from_args(self):
        """flags should parse --key=value patterns."""
        interp = run(
            'print(flags).',
            program_args=["--color=red", "--verbose"],
        )
        flags_var = interp.global_env.get("flags")
        assert flags_var is not None
        assert flags_var.value.value.get("color") is not None
        assert flags_var.value.value.get("verbose") is not None


# ===================================================================
# Filesystem IO tests
# ===================================================================


class TestFilesystem:
    def test_open_write_read_close(self):
        """Full lifecycle: open, write, read, close."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        try:
            source = (
                f'open "{path}" as data.\n'
                f'write "hello san" to data.\n'
                f'close data.\n'
            )
            interp = run(source)
            # Verify file was written
            with open(path) as f:
                content = f.read()
            assert content == "hello san"
        finally:
            os.unlink(path)

    def test_unclosed_handle_penalty(self):
        """Unclosed file handles should incur SP penalty at program end."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        try:
            source = f'open "{path}" as leaked.\n'
            interp = run(source)
            # SP should be less due to open cost AND unclosed penalty
            assert interp.sp.sp < 100
        finally:
            os.unlink(path)

    def test_append_to_file(self):
        """Append should add content to existing file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        try:
            source = (
                f'open "{path}" as data.\n'
                f'write "line1" to data.\n'
                f'append "line2" to data.\n'
                f'close data.\n'
            )
            interp = run(source)
            with open(path) as f:
                content = f.read()
            assert "line1" in content
            assert "line2" in content
        finally:
            os.unlink(path)


# ===================================================================
# Forget calls tests
# ===================================================================


class TestForgetCalls:
    def test_forget_calls_resets_counter(self):
        """forget calls on fn should reset call counter."""
        source = (
            'does greet() { return "hi". }\n'
            'greet().\n'
            'greet().\n'
            'forget calls on greet.\n'
        )
        interp = run(source)
        assert interp.call_counts.get("greet", 0) == 0

    def test_forget_calls_sp_cost(self):
        """forget calls should cost SP."""
        source = (
            'does greet() { return "hi". }\n'
            'forget calls on greet.\n'
        )
        interp = run(source)
        assert interp.sp.sp < 100


# ===================================================================
# Stdlib module tests
# ===================================================================


class TestStdlibIO:
    def test_io_buffer_and_flush(self):
        """IO.buffer stores, IO.flush prints."""
        source = (
            'IO.buffer("buffered1").\n'
            'IO.buffer("buffered2").\n'
            'IO.flush().\n'
        )
        interp = run(source)
        assert "buffered1" in interp.output
        assert "buffered2" in interp.output

    def test_io_silence(self):
        """IO.silence clears buffer without printing."""
        source = (
            'IO.buffer("secret").\n'
            'IO.silence().\n'
        )
        interp = run(source)
        assert "secret" not in interp.output


class TestStdlibFiles:
    def test_files_cwd(self):
        """Files.cwd() returns current working directory."""
        source = 'print(Files.cwd()).'
        interp = run(source)
        assert len(interp.output[0]) > 0

    def test_files_temp(self):
        """Files.temp() returns a temporary file path."""
        source = 'print(Files.temp()).'
        interp = run(source)
        assert ".san.tmp" in interp.output[0]
        # Clean up
        try:
            os.unlink(interp.output[0])
        except OSError:
            pass

    def test_files_exists(self):
        """Files.exists() returns Yep for existing files."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            source = f'print(Files.exists("{path}")).'
            interp = run(source)
            assert "yep" in interp.output[0].lower()
        finally:
            os.unlink(path)

    def test_files_not_exists(self):
        """Files.exists() returns Nope for non-existing files."""
        source = 'print(Files.exists("/nonexistent/fake/path")).'
        interp = run(source)
        assert "nope" in interp.output[0].lower()


class TestStdlibArgs:
    def test_args_env(self):
        """Args.env() returns environment variable value."""
        os.environ["SANITY_TEST_VAR"] = "hakka_was_here"
        try:
            source = 'print(Args.env("SANITY_TEST_VAR")).'
            interp = run(source)
            assert "hakka_was_here" in interp.output[0]
        finally:
            del os.environ["SANITY_TEST_VAR"]

    def test_args_count_no_args(self):
        """Args.count() returns 0 with no args."""
        source = 'print(Args.count()).'
        interp = run(source)
        assert "0" in interp.output[0]

    def test_args_count_with_args(self):
        """Args.count() returns correct count."""
        source = 'print(Args.count()).'
        interp = run(source, program_args=["a", "b", "c"])
        assert "3" in interp.output[0]


class TestStdlibCanvas:
    def test_canvas_fps_returns_zero(self):
        """Canvas.fps() returns 0 in headless mode."""
        source = 'print(Canvas.fps()).'
        interp = run(source)
        assert "0" in interp.output[0]


# ===================================================================
# SP cost method tests
# ===================================================================


class TestSPCostMethods:
    def test_sp_io_shout(self):
        """io_shout should decrease SP by 2."""
        from sanity.sanity_points import SanityTracker
        sp = SanityTracker(initial=100)
        sp.io_shout()
        assert sp.sp == 98

    def test_sp_io_whisper(self):
        """io_whisper should decrease SP by 1."""
        from sanity.sanity_points import SanityTracker
        sp = SanityTracker(initial=100)
        sp.io_whisper()
        assert sp.sp == 99

    def test_sp_file_open(self):
        """file_open should decrease SP by 3."""
        from sanity.sanity_points import SanityTracker
        sp = SanityTracker(initial=100)
        sp.file_open()
        assert sp.sp == 97

    def test_sp_file_close(self):
        """file_close should decrease SP by 1."""
        from sanity.sanity_points import SanityTracker
        sp = SanityTracker(initial=100)
        sp.file_close()
        assert sp.sp == 99

    def test_sp_file_unclosed_penalty(self):
        """file_unclosed_penalty should decrease SP by 5."""
        from sanity.sanity_points import SanityTracker
        sp = SanityTracker(initial=100)
        sp.file_unclosed_penalty()
        assert sp.sp == 95

    def test_sp_forget_calls(self):
        """forget_calls_cost should decrease SP by 5."""
        from sanity.sanity_points import SanityTracker
        sp = SanityTracker(initial=100)
        sp.forget_calls_cost()
        assert sp.sp == 95

    def test_sp_canvas_create(self):
        """canvas_create should decrease SP by 3."""
        from sanity.sanity_points import SanityTracker
        sp = SanityTracker(initial=100)
        sp.canvas_create()
        assert sp.sp == 97


# ===================================================================
# FileHandle tests
# ===================================================================


class TestFileHandle:
    def test_extension_mood_json(self):
        """JSON files should have Paranoid trait."""
        from sanity.filehandle import SanFileHandle
        from sanity.variables import Trait
        fh = SanFileHandle("/tmp/test.json", "data")
        assert Trait.PARANOID in fh.traits

    def test_extension_mood_csv(self):
        """CSV files should start with Sad mood."""
        from sanity.filehandle import SanFileHandle
        from sanity.variables import Mood
        fh = SanFileHandle("/tmp/test.csv", "data")
        assert fh.mood == Mood.SAD

    def test_extension_trust_env(self):
        """Env files should have Trust 40."""
        from sanity.filehandle import SanFileHandle
        fh = SanFileHandle("/tmp/config.env", "secrets")
        assert fh.trust == 40

    def test_extension_default_trust(self):
        """Default trust should be 70."""
        from sanity.filehandle import SanFileHandle
        fh = SanFileHandle("/tmp/test.txt", "data")
        assert fh.trust == 70

    def test_sp_cost_for_size(self):
        """SP cost should scale with file size."""
        from sanity.filehandle import SanFileHandle
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"x" * 1000)
            path = f.name
        try:
            fh = SanFileHandle(path, "data")
            cost = fh.sp_cost_for_size()
            assert cost >= 3  # At least base cost
        finally:
            os.unlink(path)
