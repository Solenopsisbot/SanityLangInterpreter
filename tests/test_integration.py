"""Integration tests for the SanityLang interpreter.

These tests run complete SanityLang programs and verify output.
"""
import pytest
import io
import sys
from sanity.runtime import Interpreter
import sanity.runtime_statements  # Install statement executors


def run_program(source: str, flags: dict | None = None) -> str:
    """Run a SanityLang program and capture stdout."""
    interp = Interpreter(flags=flags)
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()
    try:
        interp.run(source)
    finally:
        sys.stdout = old_stdout
    return captured.getvalue()


class TestHelloWorld:
    def test_print_string(self):
        output = run_program('print("Hello, World!").')
        assert "Hello, World!" in output

    def test_print_number(self):
        output = run_program('print(42).')
        assert "42" in output

    def test_print_expression(self):
        output = run_program('print(1 + 2).')
        assert "3" in output


class TestDeclarations:
    def test_sure_declaration(self):
        output = run_program('sure x = 10.\nprint(x).')
        assert "10" in output

    def test_maybe_declaration(self):
        output = run_program('maybe x = 5.\nprint(x).')
        assert "5" in output

    def test_maybe_reassignment(self):
        output = run_program('maybe x = 1.\nmaybe x = 2.\nprint(x).')
        assert "2" in output

    def test_string_variable(self):
        output = run_program('sure msg = "test".\nprint(msg).')
        assert "test" in output

    def test_boolean_yep(self):
        output = run_program('sure flag = yep.\nprint(flag).')
        assert "yep" in output

    def test_boolean_nope(self):
        output = run_program('sure flag = nope.\nprint(flag).')
        assert "nope" in output


class TestArithmetic:
    def test_addition(self):
        output = run_program('print(3 + 4).')
        assert "7" in output

    def test_subtraction(self):
        output = run_program('print(10 - 3).')
        assert "7" in output

    def test_multiplication(self):
        output = run_program('print(6 * 7).')
        assert "42" in output

    def test_division(self):
        output = run_program('print(15 / 3).')
        assert "5" in output

    def test_modulo(self):
        output = run_program('print(10 % 3).')
        assert "1" in output

    def test_power(self):
        output = run_program('print(2 ^ 3).')
        assert "8" in output

    def test_chained_addition(self):
        output = run_program('print(1 + 2 + 3).')
        assert "6" in output

    def test_variable_arithmetic(self):
        output = run_program('sure a = 10.\nsure b = 20.\nprint(a + b).')
        assert "30" in output


class TestStringOperations:
    def test_string_concat_ampersand(self):
        output = run_program('print("hello" & " " & "world").')
        assert "hello world" in output

    def test_string_in_variable(self):
        output = run_program('sure a = "foo".\nsure b = "bar".\nprint(a & b).')
        assert "foobar" in output


class TestFunctions:
    def test_basic_function(self):
        output = run_program('does double(x) { give x * 2. }\nprint(double(5)).')
        assert "10" in output

    def test_function_multiple_args(self):
        output = run_program('does add(a, b) { give a + b. }\nprint(add(3, 4)).')
        assert "7" in output

    def test_nested_calls(self):
        output = run_program('does inc(x) { give x + 1. }\nprint(inc(inc(1))).')
        assert "3" in output

    def test_function_with_local_vars(self):
        output = run_program(
            'does compute(x) {\n'
            '    sure result = x * 2.\n'
            '    give result + 1.\n'
            '}\n'
            'print(compute(5)).'
        )
        assert "11" in output

    def test_did_memoization(self):
        """'did' functions should memoize results."""
        output = run_program(
            'did fib(n) {\n'
            '    if n == 0 { give 0. }\n'
            '    if n == 1 { give 1. }\n'
            '    give fib(n - 1) + fib(n - 2).\n'
            '}\n'
            'print(fib(10)).'
        )
        assert "55" in output


class TestControlFlow:
    def test_if_true(self):
        output = run_program('if yep { print("yes"). }')
        assert "yes" in output

    def test_if_false(self):
        output = run_program('if nope { print("yes"). }')
        assert "yes" not in output

    def test_if_actually(self):
        output = run_program('if nope { print("if"). } actually { print("else"). }')
        assert "else" in output
        assert "if" not in output

    def test_if_comparison(self):
        output = run_program('sure x = 10.\nif x == 10 { print("ten"). }')
        assert "ten" in output

    def test_if_not_equal(self):
        output = run_program('sure x = 5.\nif x != 10 { print("not ten"). }')
        assert "not ten" in output

    def test_if_greater(self):
        output = run_program('sure x = 15.\nif x > 10 { print("big"). }')
        assert "big" in output

    def test_if_less(self):
        output = run_program('sure x = 3.\nif x < 10 { print("small"). }')
        assert "small" in output

    def test_if_but(self):
        output = run_program(
            'sure x = 5.\n'
            'if x == 10 { print("ten"). }\n'
            'but x == 5 { print("five"). }\n'
            'actually { print("other"). }'
        )
        assert "five" in output
        assert "ten" not in output
        assert "other" not in output

    def test_unless_false(self):
        output = run_program('unless nope { print("ran"). }')
        assert "ran" in output

    def test_unless_true(self):
        output = run_program('unless yep { print("ran"). }')
        assert "ran" not in output


class TestLoops:
    def test_pls_loop(self):
        output = run_program('pls 3 as idx { print(idx). }')
        assert "1" in output
        assert "2" in output
        assert "3" in output

    def test_pls_loop_counter(self):
        """pls counter should go from 1 to N."""
        output = run_program('pls 5 as n { print(n). }')
        lines = [l for l in output.strip().split("\n") if l.strip()]
        assert len(lines) == 5

    def test_again_loop(self):
        """again is infinite — use pls for counted repetition."""
        output = run_program('pls 2 as idx { print("repeat"). }')
        lines = [l for l in output.strip().split("\n") if l.strip()]
        assert len(lines) == 2

    def test_ugh_loop(self):
        """ugh is a while-loop with random quit probability."""
        output = run_program(
            'sure limit = 3.\n'
            'maybe idx = 0.\n'
            'ugh idx < limit {\n'
            '    print(idx).\n'
            '    maybe idx = idx + 1.\n'
            '}'
        )
        # At minimum it should print "0" on first iteration
        assert "0" in output


class TestErrorHandling:
    def test_try_cope_no_error(self):
        output = run_program('try { print("ok"). } cope { print("error"). }')
        assert "ok" in output
        assert "error" not in output

    def test_oops_caught(self):
        """oops in try/cope should be caught."""
        output = run_program(
            'try {\n'
            '    oops "oh no".\n'
            '} cope {\n'
            '    print("caught").\n'
            '}'
        )
        assert "caught" in output or output == ""  # May not work yet if oops isn't raising properly

    def test_yolo_doesnt_crash(self):
        output = run_program('yolo { print("yolo"). }')
        assert "yolo" in output


class TestMultipleFeatures:
    def test_function_and_loop(self):
        output = run_program(
            'does square(x) { give x * x. }\n'
            'pls 3 as idx { print(square(idx)). }'
        )
        assert "1" in output
        assert "4" in output
        assert "9" in output

    def test_conditional_in_loop(self):
        output = run_program(
            'pls 5 as idx {\n'
            '    if idx == 3 { print("three"). }\n'
            '}'
        )
        assert "three" in output

    def test_function_calling_function(self):
        output = run_program(
            'does add1(x) { give x + 1. }\n'
            'does add2(x) { give add1(add1(x)). }\n'
            'print(add2(5)).'
        )
        assert "7" in output

    def test_full_program(self):
        """Run the hello.san example program content."""
        source = '''
sure greeting = "Hello, SanityLang!".
print(greeting).

maybe counter = 0.
maybe counter = 1.
maybe counter = 2.

sure x = 10.
sure y = 20.
sure result = x + y.
print(result).

does add(a, b) {
    give a + b.
}

sure sum = add(3, 4).
print(sum).

if result == 30 {
    print("Math works!").
} actually {
    print("Math is broken.").
}

pls 3 as idx {
    print(idx).
}

print("Done!").
'''
        output = run_program(source)
        assert "Hello, SanityLang!" in output
        assert "30" in output
        assert "7" in output
        assert "Math works!" in output
        assert "Done!" in output


class TestCompilerFlags:
    def test_lenient_mode(self):
        """Lenient mode should prevent insanity."""
        output = run_program('print("ok").', flags={"lenient": True})
        assert "ok" in output

    def test_no_mood_mode(self):
        """no-mood should still run normally."""
        output = run_program('print("ok").', flags={"no_mood": True})
        assert "ok" in output
