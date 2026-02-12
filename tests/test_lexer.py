"""Tests for the SanityLang lexer."""
import pytest
from sanity.lexer import Lexer
from sanity.tokens import TokenType


def lex(source: str) -> list:
    return Lexer(source).tokenize()


def token_types(source: str) -> list[TokenType]:
    return [t.type for t in lex(source) if t.type != TokenType.EOF]


class TestLiterals:
    def test_integer(self):
        toks = lex("42")
        assert toks[0].type == TokenType.NUMBER
        assert toks[0].value == 42

    def test_float(self):
        toks = lex("3.14")
        assert toks[0].type == TokenType.NUMBER
        assert toks[0].value == 3.14

    def test_negative_number(self):
        toks = lex("-7")
        # Should produce a negative number or MINUS + NUMBER
        types = token_types("-7")
        assert TokenType.NUMBER in types or TokenType.MINUS in types

    def test_string_double_quotes(self):
        toks = lex('"hello"')
        assert toks[0].type == TokenType.STRING
        assert toks[0].value == "hello"

    def test_string_single_quotes(self):
        toks = lex("'world'")
        assert toks[0].type == TokenType.STRING
        assert toks[0].value == "world"

    def test_empty_string(self):
        toks = lex('""')
        assert toks[0].type == TokenType.STRING
        assert toks[0].value == ""


class TestKeywords:
    def test_declaration_keywords(self):
        for kw, expected in [
            ("sure", TokenType.SURE), ("maybe", TokenType.MAYBE),
            ("whatever", TokenType.WHATEVER), ("swear", TokenType.SWEAR),
            ("ghost", TokenType.GHOST), ("dream", TokenType.DREAM),
        ]:
            toks = lex(kw)
            assert toks[0].type == expected, f"Expected {expected} for '{kw}'"

    def test_function_keywords(self):
        for kw, expected in [
            ("does", TokenType.DOES), ("did", TokenType.DID),
            ("will", TokenType.WILL), ("might", TokenType.MIGHT),
            ("should", TokenType.SHOULD), ("must", TokenType.MUST),
        ]:
            toks = lex(kw)
            assert toks[0].type == expected

    def test_control_flow_keywords(self):
        for kw, expected in [
            ("if", TokenType.IF), ("but", TokenType.BUT),
            ("actually", TokenType.ACTUALLY), ("unless", TokenType.UNLESS),
        ]:
            toks = lex(kw)
            assert toks[0].type == expected

    def test_loop_keywords(self):
        for kw, expected in [
            ("again", TokenType.AGAIN), ("pls", TokenType.PLS),
            ("ugh", TokenType.UGH), ("forever", TokenType.FOREVER),
            ("hopefully", TokenType.HOPEFULLY), ("enough", TokenType.ENOUGH),
        ]:
            toks = lex(kw)
            assert toks[0].type == expected

    def test_boolean_keywords(self):
        assert lex("yep")[0].type == TokenType.YEP
        assert lex("nope")[0].type == TokenType.NOPE
        assert lex("dunno")[0].type == TokenType.DUNNO

    def test_give_is_return(self):
        assert lex("give")[0].type == TokenType.RETURN

    def test_i_is_identifier(self):
        """The letter 'i' should be an IDENTIFIER, not the I keyword."""
        toks = lex("i")
        assert toks[0].type == TokenType.IDENTIFIER
        assert toks[0].value == "i"


class TestTerminators:
    def test_period(self):
        toks = lex("x.")
        types = token_types("x.")
        assert TokenType.PERIOD in types

    def test_emphasis(self):
        toks = lex("x..")
        types = token_types("x..")
        assert TokenType.EMPHASIS in types

    def test_forceful(self):
        toks = lex("x!")
        types = token_types("x!")
        assert TokenType.FORCEFUL in types

    def test_questioning(self):
        toks = lex("x?")
        types = token_types("x?")
        assert TokenType.QUESTIONING in types


class TestOperators:
    def test_arithmetic(self):
        types = token_types("a + b")
        assert TokenType.PLUS in types

    def test_comparison_loose_equal(self):
        types = token_types("a == b")
        assert TokenType.LOOSE_EQUAL in types

    def test_comparison_strict_equal(self):
        types = token_types("a === b")
        assert TokenType.STRICT_EQUAL in types

    def test_not_equal(self):
        types = token_types("a != b")
        assert TokenType.NOT_EQUAL in types

    def test_ampersand_concat(self):
        types = token_types("a & b")
        assert TokenType.AMPERSAND in types


class TestWhitespace:
    def test_spaces_tracked(self):
        toks = lex("a + b")
        plus_tok = [t for t in toks if t.type == TokenType.PLUS][0]
        assert plus_tok.spaces_before > 0

    def test_tight_binding(self):
        toks = lex("a+b")
        plus_tok = [t for t in toks if t.type == TokenType.PLUS][0]
        assert plus_tok.spaces_before == 0
        assert plus_tok.spaces_after == 0


class TestComments:
    def test_single_line_comment(self):
        toks = lex("x // this is a comment\ny")
        types = token_types("x // this is a comment\ny")
        assert TokenType.IDENTIFIER in types
        # Comment should be stripped, x and y should be present
        ids = [t for t in lex("x // this is a comment\ny") if t.type == TokenType.IDENTIFIER]
        assert len(ids) == 2

    def test_inline_comment(self):
        toks = lex("sure x = 5. // declaration")
        ids = [t for t in toks if t.type == TokenType.IDENTIFIER]
        assert ids[0].value == "x"


class TestComplexTokenization:
    def test_full_declaration(self):
        toks = lex('sure greeting = "hello".')
        types = [t.type for t in toks if t.type not in (TokenType.EOF, TokenType.NEWLINE)]
        assert types == [TokenType.SURE, TokenType.IDENTIFIER, TokenType.EQUALS, TokenType.STRING, TokenType.PERIOD]

    def test_function_header(self):
        toks = lex("does add(a, b) {")
        types = [t.type for t in toks if t.type not in (TokenType.EOF, TokenType.NEWLINE)]
        assert types == [TokenType.DOES, TokenType.IDENTIFIER, TokenType.LPAREN,
                         TokenType.IDENTIFIER, TokenType.COMMA, TokenType.IDENTIFIER,
                         TokenType.RPAREN, TokenType.LBRACE]

    def test_emotional_operator(self):
        types = token_types("x loves y")
        assert TokenType.LOVES in types

    def test_if_condition(self):
        types = token_types("if x == 5 {")
        assert types[0] == TokenType.IF
