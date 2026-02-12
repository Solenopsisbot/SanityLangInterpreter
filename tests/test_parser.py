"""Tests for the SanityLang parser."""
import pytest
from sanity.lexer import Lexer
from sanity.parser import Parser
from sanity.ast_nodes import *


def parse(source: str) -> Program:
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


class TestDeclarations:
    def test_sure_declaration(self):
        prog = parse('sure x = 5.')
        assert len(prog.body) == 1
        stmt = prog.body[0]
        assert isinstance(stmt, VarDeclaration)
        assert stmt.keyword == "sure"
        assert stmt.name == "x"

    def test_maybe_declaration(self):
        prog = parse('maybe name = "hello".')
        stmt = prog.body[0]
        assert isinstance(stmt, VarDeclaration)
        assert stmt.keyword == "maybe"

    def test_whatever_declaration(self):
        prog = parse('whatever z = 42.')
        stmt = prog.body[0]
        assert isinstance(stmt, VarDeclaration)
        assert stmt.keyword == "whatever"

    def test_ghost_declaration(self):
        prog = parse('ghost phantom = 0.')
        stmt = prog.body[0]
        assert stmt.keyword == "ghost"

    def test_declaration_with_emphasis(self):
        prog = parse('sure x = 5..')
        stmt = prog.body[0]
        assert '..' in stmt.terminators


class TestFunctions:
    def test_does_function(self):
        prog = parse('does greet(name) { give name. }')
        stmt = prog.body[0]
        assert isinstance(stmt, FunctionDecl)
        assert stmt.keyword == "does"
        assert stmt.name == "greet"
        assert stmt.params == ["name"]

    def test_function_no_params(self):
        prog = parse('does noop() { give 0. }')
        stmt = prog.body[0]
        assert isinstance(stmt, FunctionDecl)
        assert stmt.params == []

    def test_function_multiple_params(self):
        prog = parse('does add(a, b, c) { give a + b + c. }')
        stmt = prog.body[0]
        assert stmt.params == ["a", "b", "c"]

    def test_did_function(self):
        prog = parse('did compute(x) { give x. }')
        assert prog.body[0].keyword == "did"

    def test_might_function(self):
        prog = parse('might risky(x) { give x. }')
        assert prog.body[0].keyword == "might"


class TestControlFlow:
    def test_if_basic(self):
        prog = parse('if x == 5 { print(x). }')
        stmt = prog.body[0]
        assert isinstance(stmt, IfStatement)
        assert stmt.actually_block is None
        assert len(stmt.but_clauses) == 0

    def test_if_with_parens(self):
        prog = parse('if (x == 5) { print(x). }')
        stmt = prog.body[0]
        assert isinstance(stmt, IfStatement)

    def test_if_actually(self):
        prog = parse('if x == 5 { print("yes"). } actually { print("no"). }')
        stmt = prog.body[0]
        assert isinstance(stmt, IfStatement)
        assert stmt.actually_block is not None

    def test_if_but(self):
        prog = parse('if x == 5 { print("five"). } but x == 6 { print("six"). }')
        stmt = prog.body[0]
        assert isinstance(stmt, IfStatement)
        assert len(stmt.but_clauses) == 1

    def test_unless(self):
        prog = parse('unless done { print("working"). }')
        stmt = prog.body[0]
        assert isinstance(stmt, UnlessStatement)

    def test_suppose(self):
        prog = parse('suppose maybe_true { print("trying"). }')
        stmt = prog.body[0]
        assert isinstance(stmt, SupposeStatement)


class TestLoops:
    def test_pls_basic(self):
        prog = parse('pls 5 as idx { print(idx). }')
        stmt = prog.body[0]
        assert isinstance(stmt, PlsLoop)
        assert stmt.counter_name == "idx"

    def test_pls_with_i(self):
        """Using 'i' as a counter variable should work."""
        prog = parse('pls 3 as i { print(i). }')
        stmt = prog.body[0]
        assert isinstance(stmt, PlsLoop)
        assert stmt.counter_name == "i"

    def test_again(self):
        prog = parse('again { print("repeat"). }')
        stmt = prog.body[0]
        assert isinstance(stmt, AgainLoop)

    def test_forever(self):
        prog = parse('forever { print("ever"). }')
        stmt = prog.body[0]
        assert isinstance(stmt, ForeverLoop)

    def test_ugh(self):
        prog = parse('ugh running { print("ugh"). }')
        stmt = prog.body[0]
        assert isinstance(stmt, UghLoop)


class TestExpressions:
    def test_number_literal(self):
        prog = parse('print(42).')
        stmt = prog.body[0]
        assert isinstance(stmt, PrintStatement)

    def test_string_literal(self):
        prog = parse('print("hello").')
        stmt = prog.body[0]
        assert isinstance(stmt, PrintStatement)

    def test_binary_add(self):
        prog = parse('sure x = 1 + 2.')
        stmt = prog.body[0]
        assert isinstance(stmt, VarDeclaration)
        assert isinstance(stmt.value, BinaryOp)
        assert stmt.value.operator == "+"

    def test_binary_multiply(self):
        prog = parse('sure x = 3 * 4.')
        assert isinstance(prog.body[0].value, BinaryOp)

    def test_function_call(self):
        prog = parse('print(add(1, 2)).')
        stmt = prog.body[0]
        assert isinstance(stmt, PrintStatement)


class TestErrorHandling:
    def test_try_cope(self):
        prog = parse('try { print("risky"). } cope { print("failed"). }')
        stmt = prog.body[0]
        assert isinstance(stmt, TryCope)

    def test_oops(self):
        prog = parse('oops "something broke".')
        stmt = prog.body[0]
        assert isinstance(stmt, OopsStatement)

    def test_yolo(self):
        prog = parse('yolo { print("yolo"). }')
        stmt = prog.body[0]
        assert isinstance(stmt, YoloBlock)


class TestGambling:
    def test_bet_basic(self):
        prog = parse('bet (50) reward 10 risk 5 { print("gambling"). }')
        stmt = prog.body[0]
        assert isinstance(stmt, BetBlock)


class TestPrint:
    def test_print_string(self):
        prog = parse('print("hello").')
        assert isinstance(prog.body[0], PrintStatement)

    def test_print_expr(self):
        prog = parse('print(1 + 2).')
        assert isinstance(prog.body[0], PrintStatement)


class TestMultipleStatements:
    def test_two_declarations(self):
        prog = parse('sure x = 1.\nsure y = 2.')
        assert len(prog.body) == 2

    def test_mixed(self):
        prog = parse('sure x = 5.\nprint(x).\nif x == 5 { print("yes"). }')
        assert len(prog.body) == 3
