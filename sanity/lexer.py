"""Lexer for (In)SanityLang — tokenizes source into a stream of Tokens."""
from __future__ import annotations
from .tokens import Token, TokenType, KEYWORDS


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"[SanityLang L{line}:C{column}] Lexer error: {message}")
        self.line = line
        self.column = column


class Lexer:
    def __init__(self, source: str, aliases: dict[str, str] | None = None):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
        self.aliases: dict[str, str] = aliases or {}
        self.removed_keywords: set[str] = set()

    def error(self, msg: str) -> LexerError:
        return LexerError(msg, self.line, self.column)

    @property
    def current(self) -> str:
        if self.pos >= len(self.source):
            return "\0"
        return self.source[self.pos]

    def peek(self, offset: int = 1) -> str:
        p = self.pos + offset
        if p >= len(self.source):
            return "\0"
        return self.source[p]

    def advance(self) -> str:
        ch = self.current
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def skip_whitespace_no_newline(self) -> int:
        """Skip spaces/tabs (not newlines). Returns count of spaces skipped."""
        count = 0
        while self.pos < len(self.source) and self.current in (" ", "\t"):
            self.advance()
            count += 1
        return count

    def skip_comment(self):
        """Skip // to end of line."""
        while self.pos < len(self.source) and self.current != "\n":
            self.advance()

    def read_string(self, quote: str) -> str:
        """Read a string literal (single or double quoted)."""
        result = []
        self.advance()  # skip opening quote
        while self.pos < len(self.source) and self.current != quote:
            if self.current == "\\":
                self.advance()
                esc = self.advance()
                if esc == "n":
                    result.append("\n")
                elif esc == "t":
                    result.append("\t")
                elif esc == "\\":
                    result.append("\\")
                elif esc == quote:
                    result.append(quote)
                else:
                    result.append("\\" + esc)
            else:
                result.append(self.advance())
        if self.pos >= len(self.source):
            raise self.error(f"Unterminated string literal")
        self.advance()  # skip closing quote
        return "".join(result)

    def read_number(self) -> float | int:
        """Read a numeric literal."""
        start = self.pos
        has_dot = False
        while self.pos < len(self.source) and (self.current.isdigit() or self.current == "."):
            if self.current == ".":
                # Check if it's a decimal point or a terminator
                if self.peek() == ".":
                    # ".." emphasis terminator — stop here
                    break
                if not self.peek().isdigit():
                    # Likely a terminator, stop
                    break
                if has_dot:
                    break  # second dot, stop
                has_dot = True
            self.advance()
        text = self.source[start : self.pos]
        if has_dot:
            return float(text)
        return int(text)

    def read_identifier(self) -> str:
        """Read an identifier/keyword."""
        start = self.pos
        while self.pos < len(self.source) and (
            self.current.isalnum() or self.current in ("_", "é")
        ):
            self.advance()
        return self.source[start : self.pos]

    def count_equals(self) -> int:
        """Count consecutive = signs."""
        count = 0
        p = self.pos
        while p < len(self.source) and self.source[p] == "=":
            count += 1
            p += 1
        return count

    def make_token(self, ttype: TokenType, value=None, spaces_before: int = 0, equal_count: int = 0) -> Token:
        return Token(
            type=ttype,
            value=value,
            line=self.line,
            column=self.column,
            spaces_before=spaces_before,
            equal_count=equal_count,
        )

    def is_terminator_context(self) -> bool:
        """Check if we're in a position where . ~ ! ? could be terminators.
        Terminators come at the end of a statement (before newline, EOF, or }).
        """
        # Look ahead past any whitespace to see if we hit newline, EOF, or }
        p = self.pos + 1
        while p < len(self.source) and self.source[p] in (" ", "\t"):
            p += 1
        if p >= len(self.source):
            return True
        next_ch = self.source[p]
        # Terminators also stack, so the next char could be another terminator
        return next_ch in ("\n", "\0", "}", ".", "~", "!", "?")

    def read_terminators(self) -> list[Token]:
        """Read one or more stacked terminators."""
        terminators = []
        while self.pos < len(self.source) and self.current in (".", "~", "!", "?"):
            line, col = self.line, self.column
            ch = self.current
            if ch == ".":
                if self.peek() == ".":
                    self.advance()
                    self.advance()
                    terminators.append(Token(TokenType.EMPHASIS, "..", line, col))
                else:
                    self.advance()
                    terminators.append(Token(TokenType.PERIOD, ".", line, col))
            elif ch == "~":
                self.advance()
                terminators.append(Token(TokenType.UNCERTAIN, "~", line, col))
            elif ch == "!":
                self.advance()
                terminators.append(Token(TokenType.FORCEFUL, "!", line, col))
            elif ch == "?":
                self.advance()
                terminators.append(Token(TokenType.QUESTIONING, "?", line, col))
            # Check if more terminators follow (stacking)
            # Skip whitespace between terminators
            while self.pos < len(self.source) and self.current in (" ", "\t"):
                self.advance()
        return terminators

    def check_chapter_header(self) -> bool:
        """Check if we're at a --- Chapter: Name --- line."""
        if self.pos + 2 < len(self.source):
            return (
                self.source[self.pos] == "-"
                and self.source[self.pos + 1] == "-"
                and self.source[self.pos + 2] == "-"
            )
        return False

    def read_chapter_header(self) -> tuple[str, str]:
        """Read --- Key: Value --- and return (key, value)."""
        # Skip ---
        for _ in range(3):
            self.advance()
        # Skip whitespace
        while self.current in (" ", "\t"):
            self.advance()
        # Read key
        key_start = self.pos
        while self.current not in (":", "\n", "\0"):
            self.advance()
        key = self.source[key_start : self.pos].strip()
        # Skip colon
        if self.current == ":":
            self.advance()
        # Skip whitespace
        while self.current in (" ", "\t"):
            self.advance()
        # Read value until ---
        val_start = self.pos
        while self.pos < len(self.source):
            if (
                self.current == "-"
                and self.peek() == "-"
                and self.peek(2) == "-"
            ):
                break
            self.advance()
        value = self.source[val_start : self.pos].strip()
        # Skip closing ---
        if self.current == "-":
            for _ in range(3):
                if self.pos < len(self.source):
                    self.advance()
        return key, value

    def tokenize(self) -> list[Token]:
        """Tokenize the entire source into a list of Tokens."""
        self.tokens = []

        while self.pos < len(self.source):
            # Track spaces before this token
            spaces = self.skip_whitespace_no_newline()

            if self.pos >= len(self.source):
                break

            ch = self.current
            line, col = self.line, self.column

            # Newlines
            if ch == "\n":
                self.advance()
                self.tokens.append(Token(TokenType.NEWLINE, "\n", line, col, spaces))
                continue

            # Comments
            if ch == "/" and self.peek() == "/":
                self.skip_comment()
                continue

            # Chapter headers: --- Key: Value ---
            if ch == "-" and self.peek() == "-" and self.peek(2) == "-":
                # Peek further to see if this is a chapter header or just dashes
                p = self.pos + 3
                while p < len(self.source) and self.source[p] in (" ", "\t"):
                    p += 1
                # Check if there's text after ---
                if p < len(self.source) and self.source[p].isalpha():
                    key, value = self.read_chapter_header()
                    key_lower = key.lower()
                    if key_lower == "chapter":
                        self.tokens.append(Token(TokenType.CHAPTER, value, line, col, spaces))
                    elif key_lower == "allies":
                        self.tokens.append(Token(TokenType.ALLIES, value, line, col, spaces))
                    elif key_lower == "rivals":
                        self.tokens.append(Token(TokenType.RIVALS, value, line, col, spaces))
                    else:
                        self.tokens.append(Token(TokenType.CHAPTER, value, line, col, spaces))
                    continue
                else:
                    self.tokens.append(Token(TokenType.TRIPLE_DASH, "---", line, col, spaces))
                    self.advance()
                    self.advance()
                    self.advance()
                    continue

            # String literals
            if ch in ('"', "'"):
                s = self.read_string(ch)
                self.tokens.append(Token(TokenType.STRING, s, line, col, spaces))
                continue

            # Numbers
            if ch.isdigit() or (ch == "-" and self.peek().isdigit() and self._can_be_negative()):
                if ch == "-":
                    self.advance()
                    num = self.read_number()
                    num = -num
                else:
                    num = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, num, line, col, spaces))
                continue

            # Identifiers / keywords
            if ch.isalpha() or ch == "_" or ch == "é":
                ident = self.read_identifier()

                # Apply grammar aliases
                if ident in self.aliases:
                    ident = self.aliases[ident]

                # Check if removed
                if ident in self.removed_keywords:
                    raise self.error(f"Keyword '{ident}' has been removed from grammar")

                # "but not" is a two-word operator
                if ident == "but":
                    # Peek ahead for "not"
                    save_pos, save_line, save_col = self.pos, self.line, self.column
                    ws = self.skip_whitespace_no_newline()
                    if self.pos < len(self.source) and self.current.isalpha():
                        next_word_start = self.pos
                        next_word = self.read_identifier()
                        if next_word == "not":
                            self.tokens.append(Token(TokenType.BUT_NOT, "but not", line, col, spaces))
                            continue
                        else:
                            # Back up
                            self.pos = save_pos
                            self.line = save_line
                            self.column = save_col

                # "i am okay" is a three-word statement
                if ident == "i":
                    save_pos, save_line, save_col = self.pos, self.line, self.column
                    self.skip_whitespace_no_newline()
                    if self.pos < len(self.source):
                        w2 = self.read_identifier()
                        if w2 == "am":
                            self.skip_whitespace_no_newline()
                            if self.pos < len(self.source):
                                w3 = self.read_identifier()
                                if w3 == "okay":
                                    self.tokens.append(Token(TokenType.I, "i am okay", line, col, spaces))
                                    continue
                    self.pos, self.line, self.column = save_pos, save_line, save_col

                # Look up keyword
                if ident in KEYWORDS:
                    self.tokens.append(Token(KEYWORDS[ident], ident, line, col, spaces))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, ident, line, col, spaces))
                continue

            # Operators and punctuation
            if ch == "=":
                eq_count = self.count_equals()
                for _ in range(eq_count):
                    self.advance()
                if eq_count == 1:
                    self.tokens.append(Token(TokenType.EQUALS, "=", line, col, spaces))
                elif eq_count == 2:
                    self.tokens.append(Token(TokenType.LOOSE_EQUAL, "==", line, col, spaces, equal_count=2))
                elif eq_count == 3:
                    self.tokens.append(Token(TokenType.STRICT_EQUAL, "===", line, col, spaces, equal_count=3))
                elif eq_count == 4:
                    self.tokens.append(Token(TokenType.IDENTITY_EQUAL, "====", line, col, spaces, equal_count=4))
                else:
                    self.tokens.append(Token(TokenType.EXTENDED_EQUAL, "=" * eq_count, line, col, spaces, equal_count=eq_count))
                continue

            if ch == "!":
                if self.peek() == "=":
                    self.advance()
                    self.advance()
                    self.tokens.append(Token(TokenType.NOT_EQUAL, "!=", line, col, spaces))
                elif self.is_terminator_context():
                    terms = self.read_terminators()
                    self.tokens.extend(terms)
                else:
                    self.advance()
                    self.tokens.append(Token(TokenType.FORCEFUL, "!", line, col, spaces))
                continue

            if ch == "~":
                if self.peek() == "=":
                    self.advance()
                    self.advance()
                    self.tokens.append(Token(TokenType.VIBES_EQUAL, "~=", line, col, spaces))
                elif self.is_terminator_context():
                    terms = self.read_terminators()
                    self.tokens.extend(terms)
                else:
                    self.advance()
                    self.tokens.append(Token(TokenType.UNCERTAIN, "~", line, col, spaces))
                continue

            if ch == "?":
                if self.is_terminator_context():
                    terms = self.read_terminators()
                    self.tokens.extend(terms)
                else:
                    self.advance()
                    self.tokens.append(Token(TokenType.QUESTIONING, "?", line, col, spaces))
                continue

            if ch == ".":
                if self.peek() == ".":
                    # Could be emphasis terminator
                    terms = self.read_terminators()
                    self.tokens.extend(terms)
                elif self.is_terminator_context():
                    terms = self.read_terminators()
                    self.tokens.extend(terms)
                else:
                    self.advance()
                    self.tokens.append(Token(TokenType.DOT, ".", line, col, spaces))
                continue

            if ch == "+":
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, "+", line, col, spaces))
                continue

            if ch == "-":
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, "-", line, col, spaces))
                continue

            if ch == "*":
                self.advance()
                self.tokens.append(Token(TokenType.STAR, "*", line, col, spaces))
                continue

            if ch == "/":
                self.advance()
                self.tokens.append(Token(TokenType.SLASH, "/", line, col, spaces))
                continue

            if ch == "%":
                self.advance()
                self.tokens.append(Token(TokenType.PERCENT, "%", line, col, spaces))
                continue

            if ch == "^":
                self.advance()
                self.tokens.append(Token(TokenType.CARET, "^", line, col, spaces))
                continue

            if ch == "&":
                self.advance()
                self.tokens.append(Token(TokenType.AMPERSAND, "&", line, col, spaces))
                continue

            if ch == "<":
                self.advance()
                if self.current == "=":
                    self.advance()
                    self.tokens.append(Token(TokenType.LESS_EQUAL, "<=", line, col, spaces))
                else:
                    self.tokens.append(Token(TokenType.LESS, "<", line, col, spaces))
                continue

            if ch == ">":
                self.advance()
                if self.current == "=":
                    self.advance()
                    self.tokens.append(Token(TokenType.GREATER_EQUAL, ">=", line, col, spaces))
                else:
                    self.tokens.append(Token(TokenType.GREATER, ">", line, col, spaces))
                continue

            if ch == "(":
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, "(", line, col, spaces))
                continue

            if ch == ")":
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ")", line, col, spaces))
                continue

            if ch == "{":
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, "{", line, col, spaces))
                continue

            if ch == "}":
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, "}", line, col, spaces))
                continue

            if ch == "[":
                self.advance()
                self.tokens.append(Token(TokenType.LBRACKET, "[", line, col, spaces))
                continue

            if ch == "]":
                self.advance()
                self.tokens.append(Token(TokenType.RBRACKET, "]", line, col, spaces))
                continue

            if ch == ",":
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ",", line, col, spaces))
                continue

            if ch == ":":
                self.advance()
                self.tokens.append(Token(TokenType.COLON, ":", line, col, spaces))
                continue

            raise self.error(f"Unexpected character: {ch!r}")

        # Add EOF
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))

        # Set spaces_after for each token  
        for i in range(len(self.tokens) - 1):
            self.tokens[i].spaces_after = self.tokens[i + 1].spaces_before

        return self.tokens

    def _can_be_negative(self) -> bool:
        """Check if a minus sign can start a negative number literal.
        It can if the previous meaningful token is an operator, opening paren,
        equals sign, comma, or if there is no previous token.
        """
        for t in reversed(self.tokens):
            if t.type == TokenType.NEWLINE:
                continue
            return t.type in (
                TokenType.EQUALS, TokenType.PLUS, TokenType.MINUS,
                TokenType.STAR, TokenType.SLASH, TokenType.PERCENT,
                TokenType.CARET, TokenType.LPAREN, TokenType.LBRACKET,
                TokenType.COMMA, TokenType.COLON,
                TokenType.LOOSE_EQUAL, TokenType.STRICT_EQUAL,
                TokenType.IDENTITY_EQUAL, TokenType.EXTENDED_EQUAL,
                TokenType.VIBES_EQUAL, TokenType.NOT_EQUAL,
                TokenType.LESS, TokenType.GREATER,
                TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL,
                TokenType.RETURN,
            )
        return True  # No previous token
