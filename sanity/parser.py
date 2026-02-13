"""Recursive descent parser for (In)SanityLang."""
from __future__ import annotations
from .tokens import Token, TokenType
from .ast_nodes import *
from typing import Optional


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(f"[SanityLang L{token.line}:C{token.column}] Parse error: {message}")
        self.token = token


class Parser:
    def __init__(self, tokens: list[Token], sanity_points: int = 100):
        self.tokens = tokens
        self.pos = 0
        self.sp = sanity_points  # For auto-terminator selection

    # ================================================
    # Utilities
    # ================================================

    @property
    def current(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        p = self.pos + offset
        if p >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[p]

    def advance(self) -> Token:
        tok = self.current
        self.pos += 1
        return tok

    def expect(self, ttype: TokenType, msg: str = "") -> Token:
        if self.current.type != ttype:
            raise ParseError(
                msg or f"Expected {ttype.name}, got {self.current.type.name} ({self.current.value!r})",
                self.current,
            )
        return self.advance()

    def match(self, *types: TokenType) -> Optional[Token]:
        if self.current.type in types:
            return self.advance()
        return None

    def skip_newlines(self):
        while self.current.type == TokenType.NEWLINE:
            self.advance()

    def at_end(self) -> bool:
        return self.current.type == TokenType.EOF

    def error(self, msg: str) -> ParseError:
        return ParseError(msg, self.current)

    # ================================================
    # Terminators
    # ================================================

    TERMINATOR_TYPES = {
        TokenType.PERIOD, TokenType.EMPHASIS, TokenType.UNCERTAIN,
        TokenType.FORCEFUL, TokenType.QUESTIONING,
    }

    TERMINATOR_MAP = {
        TokenType.PERIOD: ".",
        TokenType.EMPHASIS: "..",
        TokenType.UNCERTAIN: "~",
        TokenType.FORCEFUL: "!",
        TokenType.QUESTIONING: "?",
    }

    def parse_terminators(self) -> list[str]:
        """Parse one or more statement terminators. If none found, auto-pick based on SP."""
        terminators = []
        while self.current.type in self.TERMINATOR_TYPES:
            terminators.append(self.TERMINATOR_MAP[self.current.type])
            self.advance()
        if not terminators:
            # Auto-pick based on SP (§1)
            if self.sp > 80:
                terminators = ["."]
            elif self.sp >= 50:
                terminators = ["?"]
            elif self.sp >= 20:
                terminators = ["~"]
            else:
                terminators = ["!"]
        return terminators

    def maybe_parse_terminators(self) -> list[str]:
        """Parse terminators if present, otherwise return empty list."""
        terminators = []
        while self.current.type in self.TERMINATOR_TYPES:
            terminators.append(self.TERMINATOR_MAP[self.current.type])
            self.advance()
        return terminators

    # ================================================
    # Top-level
    # ================================================

    def parse(self) -> Program:
        """Parse the entire program."""
        self.skip_newlines()
        program = Program(line=1, column=1)

        # Check for chapter definitions and narrative structure
        while not self.at_end():
            self.skip_newlines()
            if self.at_end():
                break

            # Chapter definitions
            if self.current.type == TokenType.CHAPTER:
                program.chapters.append(self.parse_chapter())
            # Narrative structure
            elif self.current.type == TokenType.PROLOGUE:
                program.prologue = self.parse_narrative_block("prologue")
            elif self.current.type == TokenType.ARC:
                program.arcs.append(self.parse_arc())
            elif self.current.type == TokenType.CLIMAX:
                program.climax = self.parse_climax()
            elif self.current.type == TokenType.EPILOGUE:
                program.epilogue = self.parse_narrative_block("epilogue")
            else:
                stmt = self.parse_statement()
                if stmt:
                    program.body.append(stmt)

        return program

    # ================================================
    # Statements
    # ================================================

    def parse_statement(self) -> Optional[Statement]:
        """Parse a single statement."""
        self.skip_newlines()
        if self.at_end():
            return None

        tok = self.current

        # Declaration keywords
        if tok.type in (
            TokenType.SURE, TokenType.MAYBE, TokenType.WHATEVER,
            TokenType.SWEAR, TokenType.PINKY, TokenType.GHOST,
            TokenType.DREAM, TokenType.WHISPER, TokenType.CURSE,
            TokenType.SCREAM,
        ):
            return self.parse_declaration()

        # Secret declarations
        if tok.type == TokenType.SECRET:
            return self.parse_secret()

        # Function declarations
        if tok.type in (
            TokenType.DOES, TokenType.DID, TokenType.WILL,
            TokenType.MIGHT, TokenType.SHOULD, TokenType.MUST,
        ):
            return self.parse_function_decl()

        # Control flow
        if tok.type == TokenType.IF:
            return self.parse_if()
        if tok.type == TokenType.UNLESS:
            return self.parse_unless()
        if tok.type == TokenType.SUPPOSE:
            return self.parse_suppose()
        if tok.type == TokenType.PRETEND:
            return self.parse_pretend()
        if tok.type == TokenType.CHECK:
            return self.parse_check()

        # Loops
        if tok.type == TokenType.AGAIN:
            return self.parse_again()
        if tok.type == TokenType.PLS:
            return self.parse_pls()
        if tok.type == TokenType.UGH:
            return self.parse_ugh()
        if tok.type == TokenType.FOREVER:
            return self.parse_forever()
        if tok.type == TokenType.HOPEFULLY:
            return self.parse_hopefully()
        if tok.type == TokenType.RELUCTANTLY:
            return self.parse_reluctantly()
        if tok.type == TokenType.NEVER:
            return self.parse_never()
        if tok.type == TokenType.ENOUGH:
            return self.parse_enough()

        # Return
        if tok.type == TokenType.RETURN:
            return self.parse_return()

        # Error handling
        if tok.type == TokenType.TRY:
            return self.parse_try()
        if tok.type == TokenType.BLAME:
            return self.parse_blame()
        if tok.type == TokenType.OOPS:
            return self.parse_oops()
        if tok.type == TokenType.YOLO:
            return self.parse_yolo()

        # Print
        if tok.type == TokenType.PRINT:
            return self.parse_print()

        # Gambling
        if tok.type == TokenType.BET:
            return self.parse_bet()
        if tok.type == TokenType.JACKPOT:
            return self.parse_jackpot()

        # Narrative
        if tok.type == TokenType.SKIP:
            return self.parse_skip()

        # Time
        if tok.type == TokenType.FORESHADOW:
            return self.parse_foreshadow()
        if tok.type == TokenType.FULFILL:
            return self.parse_fulfill()
        if tok.type == TokenType.REWIND:
            return self.parse_rewind()

        # Chapters
        if tok.type == TokenType.RECALL:
            return self.parse_recall()

        # Personalities
        if tok.type == TokenType.PERSONALITY:
            return self.parse_personality()

        # Concurrency
        if tok.type == TokenType.VIBE:
            return self.parse_vibe()
        if tok.type == TokenType.FEEL:
            return self.parse_feel()

        # Events
        if tok.type == TokenType.WHEN:
            return self.parse_when()

        # Debugging
        if tok.type == TokenType.WTF:
            return self.parse_wtf()
        if tok.type == TokenType.HUH:
            return self.parse_huh()
        if tok.type == TokenType.CRY:
            return self.parse_cry()
        if tok.type == TokenType.THERAPY:
            return self.parse_therapy()
        if tok.type == TokenType.ORACLE:
            return self.parse_oracle()

        # Self-modification
        if tok.type == TokenType.GRAMMAR:
            return self.parse_grammar()
        if tok.type == TokenType.PRAY:
            return self.parse_pray()
        if tok.type == TokenType.NO:
            return self.parse_no()
        if tok.type == TokenType.EXORCISE:
            return self.parse_exorcise()

        # "i am okay" — lexer produces a single TokenType.I token
        if tok.type == TokenType.I:
            return self.parse_i_am_okay()

        # Delete
        if tok.type == TokenType.DELETE:
            return self.parse_delete()

        # Console IO — shout
        if tok.type == TokenType.SHOUT:
            return self.parse_shout()

        # Whisper as statement: whisper(expr)
        # Note: WHISPER is also a declaration keyword. We check if followed by '('
        # to distinguish whisper(expr). from whisper x = val.
        # The declaration case is already handled above.

        # Filesystem IO
        if tok.type == TokenType.OPEN:
            return self.parse_open()
        if tok.type == TokenType.WRITE_KW:
            return self.parse_write()
        if tok.type == TokenType.APPEND_KW:
            return self.parse_append()
        if tok.type == TokenType.CLOSE:
            return self.parse_close()

        # Call management
        if tok.type == TokenType.FORGET:
            return self.parse_forget_calls()

        # Identifier — could be assignment, emotional op, or expression
        if tok.type == TokenType.IDENTIFIER:
            return self.parse_identifier_statement()

        # Expression statement
        return self.parse_expression_statement()

    def parse_block(self) -> Block:
        """Parse a { ... } block."""
        line, col = self.current.line, self.current.column
        self.expect(TokenType.LBRACE, "Expected '{'")
        self.skip_newlines()
        stmts = []
        while self.current.type != TokenType.RBRACE and not self.at_end():
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            self.skip_newlines()
        self.expect(TokenType.RBRACE, "Expected '}'")
        return Block(line=line, column=col, statements=stmts)

    # ================================================
    # Declarations
    # ================================================

    def parse_declaration(self) -> VarDeclaration:
        """Parse: <keyword> <name> = <value> <terminator>"""
        tok = self.advance()  # keyword
        keyword = tok.value
        line, col = tok.line, tok.column

        name_tok = self.expect(TokenType.IDENTIFIER, "Expected variable name")
        name = name_tok.value

        value = None
        source = None
        curse_type = None

        # Curse has special syntax: curse name: Type = value
        if keyword == "curse":
            if self.match(TokenType.COLON):
                curse_type = self.expect(TokenType.IDENTIFIER, "Expected type for curse").value

        if self.match(TokenType.EQUALS):
            value = self.parse_expression()

        # Pinky can point to a source: pinky x = y
        if keyword == "pinky" and value and isinstance(value, VariableAccess):
            source = value.name

        terminators = self.parse_terminators()
        return VarDeclaration(
            line=line, column=col, terminators=terminators,
            keyword=keyword, name=name, value=value,
            source=source, curse_type=curse_type,
        )

    def parse_secret(self) -> Statement:
        """Parse: secret does funcName() { ... }"""
        self.advance()  # secret
        if self.current.type in (
            TokenType.DOES, TokenType.DID, TokenType.WILL,
            TokenType.MIGHT, TokenType.SHOULD, TokenType.MUST,
        ):
            decl = self.parse_function_decl()
            decl.is_secret = True
            return decl
        # Secret variable
        decl = self.parse_declaration()
        return decl

    # ================================================
    # Functions
    # ================================================

    def parse_function_decl(self) -> FunctionDecl:
        """Parse: does/did/will/might/should/must name(params) [when cond] { body }"""
        tok = self.advance()  # keyword
        keyword = tok.value
        line, col = tok.line, tok.column

        name_tok = self.expect(TokenType.IDENTIFIER, "Expected function name")
        name = name_tok.value

        # Parameters
        self.expect(TokenType.LPAREN, "Expected '(' after function name")
        params = []
        while self.current.type != TokenType.RPAREN:
            params.append(self.expect(TokenType.IDENTIFIER, "Expected parameter name").value)
            if not self.match(TokenType.COMMA):
                break
        self.expect(TokenType.RPAREN, "Expected ')'")

        # For 'might': optional when condition
        condition = None
        if keyword == "might" and self.current.type == TokenType.WHEN:
            self.advance()
            condition = self.parse_expression()

        # Body
        self.skip_newlines()
        body = self.parse_block()

        return FunctionDecl(
            line=line, column=col, terminators=[],
            keyword=keyword, name=name, params=params,
            body=body, condition=condition,
        )

    def parse_return(self) -> ReturnStatement:
        tok = self.advance()  # return
        value = None
        if self.current.type not in self.TERMINATOR_TYPES and self.current.type != TokenType.RBRACE:
            value = self.parse_expression()
        terminators = self.parse_terminators()
        return ReturnStatement(line=tok.line, column=tok.column, terminators=terminators, value=value)

    # ================================================
    # Control Flow
    # ================================================

    def _parse_condition(self):
        """Parse a condition expression, optionally wrapped in parens."""
        has_parens = self.current.type == TokenType.LPAREN
        if has_parens:
            self.advance()
        cond = self.parse_expression()
        if has_parens:
            self.expect(TokenType.RPAREN)
        return cond

    def parse_if(self) -> IfStatement:
        tok = self.advance()  # if
        condition = self._parse_condition()
        self.skip_newlines()
        body = self.parse_block()

        but_clauses = []
        actually_block = None

        self.skip_newlines()
        while self.current.type == TokenType.BUT:
            self.advance()
            bcond = self._parse_condition()
            self.skip_newlines()
            bbody = self.parse_block()
            but_clauses.append(ButClause(line=self.current.line, column=self.current.column, condition=bcond, body=bbody))
            self.skip_newlines()

        if self.current.type == TokenType.ACTUALLY:
            self.advance()
            self.skip_newlines()
            actually_block = self.parse_block()

        return IfStatement(
            line=tok.line, column=tok.column, terminators=[],
            condition=condition, body=body,
            but_clauses=but_clauses, actually_block=actually_block,
        )

    def parse_unless(self) -> UnlessStatement:
        tok = self.advance()
        condition = self._parse_condition()
        self.skip_newlines()
        body = self.parse_block()
        return UnlessStatement(line=tok.line, column=tok.column, terminators=[], condition=condition, body=body)

    def parse_suppose(self) -> SupposeStatement:
        tok = self.advance()
        condition = self._parse_condition()
        self.skip_newlines()
        body = self.parse_block()
        return SupposeStatement(line=tok.line, column=tok.column, terminators=[], condition=condition, body=body)

    def parse_pretend(self) -> PretendStatement:
        tok = self.advance()
        condition = self._parse_condition()
        self.skip_newlines()
        body = self.parse_block()
        return PretendStatement(line=tok.line, column=tok.column, terminators=[], condition=condition, body=body)

    # ================================================
    # Pattern Matching
    # ================================================

    def parse_check(self) -> CheckStatement:
        tok = self.advance()  # check
        value = self.parse_expression()
        self.skip_newlines()
        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        cases = []
        otherwise = None

        while self.current.type != TokenType.RBRACE and not self.at_end():
            self.skip_newlines()
            if self.current.type == TokenType.OTHERWISE:
                self.advance()
                self.skip_newlines()
                otherwise = self.parse_block()
            elif self.current.type == TokenType.IS:
                cases.append(self.parse_check_case())
            else:
                break
            self.skip_newlines()

        self.expect(TokenType.RBRACE)
        return CheckStatement(line=tok.line, column=tok.column, terminators=[], value=value, cases=cases, otherwise=otherwise)

    def parse_check_case(self) -> CheckCase:
        self.advance()  # is
        line, col = self.current.line, self.current.column

        type_names = []
        type_name = self.expect(TokenType.IDENTIFIER, "Expected type name in check case").value
        type_names.append(type_name)

        # Handle "is Yep or Nope"
        while self.current.type == TokenType.OR:
            self.advance()
            type_names.append(self.expect(TokenType.IDENTIFIER, "Expected type name").value)

        condition = None
        blob_key = None
        mood_check = None
        state_check = None

        # Handle "where <condition>"
        if self.current.type == TokenType.WHERE:
            self.advance()
            condition = self.parse_expression()

        # Handle "with key <string>"
        if self.current.type == TokenType.WITH:
            self.advance()
            if self.current.value == "key":
                self.advance()
                blob_key = self.parse_expression()

        # Handle "and mood Happy" or "and trust < 50"
        if self.current.type == TokenType.AND:
            self.advance()
            if self.current.type == TokenType.MOOD:
                self.advance()
                mood_check = self.expect(TokenType.IDENTIFIER, "Expected mood name").value
            else:
                state_name = self.expect(TokenType.IDENTIFIER, "Expected state name").value
                op = self.advance().value  # <, >, etc.
                val = self.parse_expression()
                state_check = (state_name, op, val)

        self.skip_newlines()
        body = self.parse_block()

        return CheckCase(
            line=line, column=col,
            type_name=type_names[0] if len(type_names) == 1 else None,
            type_names=type_names,
            condition=condition, blob_key=blob_key,
            mood_check=mood_check, state_check=state_check,
            body=body,
        )

    # ================================================
    # Loops
    # ================================================

    def parse_again(self) -> AgainLoop:
        tok = self.advance()
        self.skip_newlines()
        body = self.parse_block()
        return AgainLoop(line=tok.line, column=tok.column, terminators=[], body=body)

    def parse_pls(self) -> PlsLoop:
        tok = self.advance()
        count = self.parse_expression()
        counter_name = None
        if self.current.type == TokenType.AS:
            self.advance()
            counter_name = self.expect(TokenType.IDENTIFIER, "Expected counter variable name").value
        self.skip_newlines()
        body = self.parse_block()
        return PlsLoop(line=tok.line, column=tok.column, terminators=[], count=count, counter_name=counter_name, body=body)

    def parse_ugh(self) -> UghLoop:
        tok = self.advance()
        condition = self._parse_condition()
        self.skip_newlines()
        body = self.parse_block()
        return UghLoop(line=tok.line, column=tok.column, terminators=[], condition=condition, body=body)

    def parse_forever(self) -> ForeverLoop:
        tok = self.advance()
        self.skip_newlines()
        body = self.parse_block()
        return ForeverLoop(line=tok.line, column=tok.column, terminators=[], body=body)

    def parse_hopefully(self) -> HopefullyLoop:
        tok = self.advance()
        condition = self._parse_condition()
        self.skip_newlines()
        body = self.parse_block()
        return HopefullyLoop(line=tok.line, column=tok.column, terminators=[], condition=condition, body=body)

    def parse_reluctantly(self) -> ReluctantlyLoop:
        tok = self.advance()
        condition = self._parse_condition()
        self.skip_newlines()
        body = self.parse_block()
        return ReluctantlyLoop(line=tok.line, column=tok.column, terminators=[], condition=condition, body=body)

    def parse_never(self) -> NeverBlock:
        tok = self.advance()
        self.skip_newlines()
        body = self.parse_block()
        return NeverBlock(line=tok.line, column=tok.column, terminators=[], body=body)

    def parse_enough(self) -> EnoughStatement:
        tok = self.advance()
        terminators = self.parse_terminators()
        return EnoughStatement(line=tok.line, column=tok.column, terminators=terminators)

    # ================================================
    # Error Handling
    # ================================================

    def parse_try(self) -> TryCope:
        tok = self.advance()  # try
        self.skip_newlines()
        try_block = self.parse_block()

        cope_param = None
        cope_block = None
        deny_param = None
        deny_block = None

        self.skip_newlines()
        if self.current.type == TokenType.COPE:
            self.advance()
            if self.current.type == TokenType.LPAREN:
                self.advance()
                cope_param = self.expect(TokenType.IDENTIFIER).value
                self.expect(TokenType.RPAREN)
            self.skip_newlines()
            cope_block = self.parse_block()

        self.skip_newlines()
        if self.current.type == TokenType.DENY:
            self.advance()
            if self.current.type == TokenType.LPAREN:
                self.advance()
                deny_param = self.expect(TokenType.IDENTIFIER).value
                self.expect(TokenType.RPAREN)
            self.skip_newlines()
            deny_block = self.parse_block()

        return TryCope(
            line=tok.line, column=tok.column, terminators=[],
            try_block=try_block, cope_param=cope_param, cope_block=cope_block,
            deny_param=deny_param, deny_block=deny_block,
        )

    def parse_blame(self) -> BlameStatement:
        tok = self.advance()  # blame
        target = self.expect(TokenType.STRING, "Expected blame target").value
        self.expect(TokenType.FOR, "Expected 'for' after blame target")
        reason = self.expect(TokenType.STRING, "Expected blame reason").value
        terminators = self.parse_terminators()
        return BlameStatement(line=tok.line, column=tok.column, terminators=terminators, target=target, reason=reason)

    def parse_oops(self) -> OopsStatement:
        tok = self.advance()  # oops
        message = self.expect(TokenType.STRING, "Expected oops message").value
        terminators = self.parse_terminators()
        return OopsStatement(line=tok.line, column=tok.column, terminators=terminators, message=message)

    def parse_yolo(self) -> YoloBlock:
        tok = self.advance()  # yolo
        self.skip_newlines()
        body = self.parse_block()
        return YoloBlock(line=tok.line, column=tok.column, terminators=[], body=body)

    # ================================================
    # Gambling
    # ================================================

    def parse_bet(self) -> BetBlock:
        tok = self.advance()  # bet
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.REWARD, "Expected 'reward'")
        reward = self.parse_expression()
        self.expect(TokenType.RISK, "Expected 'risk'")
        risk = self.parse_expression()
        self.skip_newlines()
        body = self.parse_block()
        return BetBlock(line=tok.line, column=tok.column, terminators=[], condition=condition, reward=reward, risk=risk, body=body)

    def parse_jackpot(self) -> JackpotBlock:
        tok = self.advance()  # jackpot
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.skip_newlines()
        body = self.parse_block()
        return JackpotBlock(line=tok.line, column=tok.column, terminators=[], condition=condition, body=body)

    # ================================================
    # Print
    # ================================================

    def parse_print(self) -> PrintStatement:
        tok = self.advance()  # print
        self.expect(TokenType.LPAREN)
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        terminators = self.parse_terminators()
        return PrintStatement(line=tok.line, column=tok.column, terminators=terminators, expression=expr)

    # ================================================
    # Narrative
    # ================================================

    def parse_narrative_block(self, kind: str) -> Block:
        self.advance()  # prologue/epilogue
        self.skip_newlines()
        return self.parse_block()

    def parse_arc(self) -> ArcDef:
        tok = self.advance()  # arc
        name = self.expect(TokenType.STRING, "Expected arc name").value
        requires = None
        if self.current.type == TokenType.REQUIRES:
            self.advance()
            requires = self.expect(TokenType.STRING, "Expected required arc name").value
        self.skip_newlines()
        body = self.parse_block()
        return ArcDef(line=tok.line, column=tok.column, name=name, requires=requires, body=body)

    def parse_climax(self) -> ClimaxDef:
        tok = self.advance()  # climax
        requires = None
        if self.current.type == TokenType.REQUIRES:
            self.advance()
            requires = self.expect(TokenType.STRING, "Expected required arc name").value
        self.skip_newlines()
        body = self.parse_block()
        return ClimaxDef(line=tok.line, column=tok.column, requires=requires, body=body)

    def parse_skip(self) -> Statement:
        tok = self.advance()  # skip
        name = self.expect(TokenType.STRING, "Expected arc name to skip").value
        terminators = self.parse_terminators()
        # Reuse ForeshadowStatement for now (just stores a name)
        return ExpressionStatement(
            line=tok.line, column=tok.column, terminators=terminators,
            expression=StringLiteral(line=tok.line, column=tok.column, value=f"__skip__{name}"),
        )

    # ================================================
    # Time
    # ================================================

    def parse_foreshadow(self) -> ForeshadowStatement:
        tok = self.advance()
        name = self.expect(TokenType.IDENTIFIER, "Expected event name").value
        terminators = self.parse_terminators()
        return ForeshadowStatement(line=tok.line, column=tok.column, terminators=terminators, event_name=name)

    def parse_fulfill(self) -> FulfillStatement:
        tok = self.advance()
        name = self.expect(TokenType.IDENTIFIER, "Expected event name").value
        terminators = self.parse_terminators()
        return FulfillStatement(line=tok.line, column=tok.column, terminators=terminators, event_name=name)

    def parse_rewind(self) -> RewindStatement:
        tok = self.advance()
        count = self.parse_expression()
        terminators = self.parse_terminators()
        return RewindStatement(line=tok.line, column=tok.column, terminators=terminators, count=count)

    # ================================================
    # Chapters
    # ================================================

    def parse_chapter(self) -> ChapterDef:
        """Parse a chapter definition starting from the CHAPTER token."""
        tok = self.current
        name = tok.value
        self.advance()  # CHAPTER token
        self.skip_newlines()

        allies = []
        rivals = []

        # Check for allies/rivals headers
        while self.current.type in (TokenType.ALLIES, TokenType.RIVALS):
            if self.current.type == TokenType.ALLIES:
                allies = [s.strip() for s in self.current.value.split(",")]
                self.advance()
            elif self.current.type == TokenType.RIVALS:
                rivals = [s.strip() for s in self.current.value.split(",")]
                self.advance()
            self.skip_newlines()

        # Parse body until next chapter or EOF
        body = []
        while not self.at_end() and self.current.type != TokenType.CHAPTER:
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            self.skip_newlines()

        return ChapterDef(line=tok.line, column=tok.column, name=name, allies=allies, rivals=rivals, body=body)

    def parse_recall(self) -> RecallStatement:
        tok = self.advance()  # recall
        if self.current.type == TokenType.IDENTIFIER:
            first = self.advance()
            if self.current.type == TokenType.FROM:
                # recall X from Module
                self.advance()
                module = self.expect(TokenType.IDENTIFIER, "Expected module name").value
                terminators = self.parse_terminators()
                return RecallStatement(line=tok.line, column=tok.column, terminators=terminators, module=module, specific=first.value)
            else:
                # recall Module
                terminators = self.parse_terminators()
                return RecallStatement(line=tok.line, column=tok.column, terminators=terminators, module=first.value)
        raise self.error("Expected module name after 'recall'")

    # ================================================
    # Personalities
    # ================================================

    def parse_personality(self) -> PersonalityDef:
        tok = self.advance()  # personality
        name = self.expect(TokenType.IDENTIFIER, "Expected personality name").value

        parents = []
        traits = []
        resolves = {}

        # Inheritance: from Parent1, Parent2
        if self.current.type == TokenType.FROM:
            self.advance()
            parents.append(self.expect(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                parents.append(self.expect(TokenType.IDENTIFIER).value)

        # Traits: with Lucky, Resilient
        if self.current.type == TokenType.WITH:
            self.advance()
            traits.append(self.expect(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                traits.append(self.expect(TokenType.IDENTIFIER).value)

        self.skip_newlines()
        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        body = []
        while self.current.type != TokenType.RBRACE and not self.at_end():
            if self.current.type == TokenType.RESOLVE:
                self.advance()
                method = self.expect(TokenType.IDENTIFIER).value
                self.expect(TokenType.EQUALS)
                parent_ref = self.expect(TokenType.IDENTIFIER).value
                self.expect(TokenType.DOT)
                method_name = self.expect(TokenType.IDENTIFIER).value
                resolves[method] = parent_ref
                self.maybe_parse_terminators()
            else:
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
            self.skip_newlines()

        self.expect(TokenType.RBRACE)

        return PersonalityDef(
            line=tok.line, column=tok.column, terminators=[],
            name=name, parents=parents, traits=traits,
            body=body, resolves=resolves,
        )

    # ================================================
    # Concurrency
    # ================================================

    def parse_vibe(self) -> VibeBlock:
        tok = self.advance()  # vibe
        self.skip_newlines()
        body = self.parse_block()
        return VibeBlock(line=tok.line, column=tok.column, terminators=[], body=body)

    def parse_feel(self) -> FeelBlock:
        tok = self.advance()  # feel
        lock = self.parse_expression()
        self.skip_newlines()
        body = self.parse_block()
        return FeelBlock(line=tok.line, column=tok.column, terminators=[], lock=lock, body=body)

    # ================================================
    # Events
    # ================================================

    def parse_when(self) -> WhenBlock:
        tok = self.advance()  # when
        target = self.expect(TokenType.IDENTIFIER, "Expected event target").value

        event_type = ""
        event_arg = None

        if self.current.type == TokenType.CHANGES:
            self.advance()
            event_type = "changes"
        elif self.current.type == TokenType.MOOD:
            self.advance()
            event_type = "mood"
            event_arg = self.expect(TokenType.IDENTIFIER).value
        elif self.current.type == TokenType.CROSSES:
            self.advance()
            event_type = "crosses"
            event_arg = self.parse_expression()
        elif self.current.type == TokenType.IDENTIFIER:
            event_type = self.advance().value
        else:
            event_type = "changes"  # default

        self.skip_newlines()
        body = self.parse_block()
        return WhenBlock(
            line=tok.line, column=tok.column, terminators=[],
            target=target, event_type=event_type, event_arg=event_arg, body=body,
        )

    # ================================================
    # Debugging
    # ================================================

    def parse_wtf(self) -> WtfStatement:
        tok = self.advance()
        target = self.expect(TokenType.IDENTIFIER, "Expected variable name").value
        terminators = self.parse_terminators()
        return WtfStatement(line=tok.line, column=tok.column, terminators=terminators, target=target)

    def parse_huh(self) -> HuhStatement:
        tok = self.advance()
        target = self.expect(TokenType.IDENTIFIER, "Expected variable name").value
        terminators = self.parse_terminators()
        return HuhStatement(line=tok.line, column=tok.column, terminators=terminators, target=target)

    def parse_cry(self) -> CryStatement:
        tok = self.advance()
        message = self.expect(TokenType.STRING, "Expected cry message").value
        terminators = self.parse_terminators()
        return CryStatement(line=tok.line, column=tok.column, terminators=terminators, message=message)

    def parse_therapy(self) -> TherapyStatement:
        tok = self.advance()
        terminators = self.parse_terminators()
        return TherapyStatement(line=tok.line, column=tok.column, terminators=terminators)

    def parse_oracle(self) -> OracleStatement:
        tok = self.advance()
        question = self.expect(TokenType.STRING, "Expected oracle question").value
        terminators = self.parse_terminators()
        return OracleStatement(line=tok.line, column=tok.column, terminators=terminators, question=question)

    # ================================================
    # Self-Modification
    # ================================================

    def parse_grammar(self) -> Statement:
        tok = self.advance()  # grammar
        self.expect(TokenType.DOT)
        method = self.expect(TokenType.IDENTIFIER, "Expected 'alias' or 'remove'").value

        self.expect(TokenType.LPAREN)
        arg1 = self.expect(TokenType.STRING, "Expected string argument").value

        if method == "alias":
            self.expect(TokenType.COMMA)
            arg2 = self.expect(TokenType.STRING, "Expected string argument").value
            self.expect(TokenType.RPAREN)
            terminators = self.parse_terminators()
            return GrammarAlias(line=tok.line, column=tok.column, terminators=terminators, new_keyword=arg1, old_keyword=arg2)
        elif method == "remove":
            self.expect(TokenType.RPAREN)
            terminators = self.parse_terminators()
            return GrammarRemove(line=tok.line, column=tok.column, terminators=terminators, keyword=arg1)
        else:
            raise self.error(f"Unknown grammar method: {method}")

    def parse_pray(self) -> PrayStatement:
        tok = self.advance()  # pray
        self.expect(TokenType.FOR, "Expected 'for' after 'pray'")
        prayer = self.expect(TokenType.IDENTIFIER, "Expected prayer type").value
        terminators = self.parse_terminators()
        return PrayStatement(line=tok.line, column=tok.column, terminators=terminators, prayer=prayer)

    def parse_no(self) -> NoStatement:
        tok = self.advance()  # no
        feature = self.expect(TokenType.IDENTIFIER, "Expected feature name to ban").value
        terminators = self.parse_terminators()
        return NoStatement(line=tok.line, column=tok.column, terminators=terminators, feature=feature)

    def parse_exorcise(self) -> ExorciseStatement:
        tok = self.advance()  # exorcise
        name = self.expect(TokenType.IDENTIFIER, "Expected curse name").value
        terminators = self.parse_terminators()
        return ExorciseStatement(line=tok.line, column=tok.column, terminators=terminators, curse_name=name)

    # ================================================
    # Insanity
    # ================================================

    def parse_i_am_okay(self) -> IAmOkayStatement:
        tok = self.advance()  # single 'i am okay' token (TokenType.I)
        terminators = self.parse_terminators()
        return IAmOkayStatement(line=tok.line, column=tok.column, terminators=terminators)

    # ================================================
    # Delete
    # ================================================

    def parse_delete(self) -> DeleteStatement:
        tok = self.advance()
        name = self.expect(TokenType.IDENTIFIER, "Expected variable name").value
        terminators = self.parse_terminators()
        return DeleteStatement(line=tok.line, column=tok.column, terminators=terminators, variable=name)

    # ================================================
    # Console IO
    # ================================================

    def parse_shout(self) -> ShoutStatement:
        tok = self.advance()  # shout
        self.expect(TokenType.LPAREN)
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        terminators = self.parse_terminators()
        return ShoutStatement(line=tok.line, column=tok.column, terminators=terminators, expression=expr)

    # ================================================
    # Filesystem IO
    # ================================================

    def parse_open(self) -> OpenStatement:
        tok = self.advance()  # open
        path_expr = self.parse_expression()
        self.expect(TokenType.AS, "Expected 'as' after file path")
        name = self.expect(TokenType.IDENTIFIER, "Expected file handle name").value
        terminators = self.parse_terminators()
        return OpenStatement(line=tok.line, column=tok.column, terminators=terminators,
                             path=path_expr, handle_name=name)

    def parse_write(self) -> WriteStatement:
        tok = self.advance()  # write
        content = self.parse_expression()
        self.expect(TokenType.TO, "Expected 'to' after write content")
        name = self.expect(TokenType.IDENTIFIER, "Expected file handle name").value
        terminators = self.parse_terminators()
        return WriteStatement(line=tok.line, column=tok.column, terminators=terminators,
                              content=content, handle_name=name)

    def parse_append(self) -> AppendStatement:
        tok = self.advance()  # append
        content = self.parse_expression()
        self.expect(TokenType.TO, "Expected 'to' after append content")
        name = self.expect(TokenType.IDENTIFIER, "Expected file handle name").value
        terminators = self.parse_terminators()
        return AppendStatement(line=tok.line, column=tok.column, terminators=terminators,
                               content=content, handle_name=name)

    def parse_close(self) -> CloseStatement:
        tok = self.advance()  # close
        name = self.expect(TokenType.IDENTIFIER, "Expected file handle name").value
        terminators = self.parse_terminators()
        return CloseStatement(line=tok.line, column=tok.column, terminators=terminators, handle_name=name)

    # ================================================
    # Call Management
    # ================================================

    def parse_forget_calls(self) -> ForgetCallsStatement:
        tok = self.advance()  # forget
        self.expect(TokenType.CALLS, "Expected 'calls' after 'forget'")
        self.expect(TokenType.ON, "Expected 'on' after 'forget calls'")
        name = self.expect(TokenType.IDENTIFIER, "Expected function name").value
        terminators = self.parse_terminators()
        return ForgetCallsStatement(line=tok.line, column=tok.column, terminators=terminators, function_name=name)

    # ================================================
    # Identifier Statements (assignment, emotional ops, expr)
    # ================================================

    def parse_identifier_statement(self) -> Statement:
        """Handle: x = expr, x loves y, x forgets everyone, or just expr."""
        line, col = self.current.line, self.current.column

        # Check for assignment: ident = expr
        if self.peek().type == TokenType.EQUALS:
            name = self.advance().value
            self.advance()  # =
            value = self.parse_expression()
            terminators = self.parse_terminators()
            return Assignment(line=line, column=col, terminators=terminators, name=name, value=value)

        # Check for "x forgets everyone"
        if self.peek().type == TokenType.FORGETS:
            name = self.advance().value
            self.advance()  # forgets
            if self.current.type == TokenType.EVERYONE:
                self.advance()
                terminators = self.parse_terminators()
                return ForgetsEveryone(line=line, column=col, terminators=terminators, variable=name)
            # x forgets y — break emotional relationship
            target = self.expect(TokenType.IDENTIFIER).value
            terminators = self.parse_terminators()
            return ExpressionStatement(
                line=line, column=col, terminators=terminators,
                expression=EmotionalOp(line=line, column=col, left=VariableAccess(name=name), operator="forgets", right=VariableAccess(name=target)),
            )

        # Check for emotional operators: x loves y, etc.
        if self.peek().type in (
            TokenType.LOVES, TokenType.HATES, TokenType.FEARS,
            TokenType.ENVIES, TokenType.IGNORES, TokenType.MIRRORS,
            TokenType.HAUNTS,
        ):
            name = self.advance().value
            op = self.advance().value
            target = self.expect(TokenType.IDENTIFIER).value
            terminators = self.parse_terminators()
            return ExpressionStatement(
                line=line, column=col, terminators=terminators,
                expression=EmotionalOp(
                    line=line, column=col,
                    left=VariableAccess(name=name),
                    operator=op,
                    right=VariableAccess(name=target),
                ),
            )

        # Fall through to expression statement
        return self.parse_expression_statement()

    # ================================================
    # Expression Statements
    # ================================================

    def parse_expression_statement(self) -> ExpressionStatement:
        line, col = self.current.line, self.current.column
        expr = self.parse_expression()
        terminators = self.parse_terminators()
        return ExpressionStatement(line=line, column=col, terminators=terminators, expression=expr)

    # ================================================
    # Expressions — Precedence Climbing
    # ================================================

    def parse_expression(self) -> Expression:
        """Parse a full expression (lowest precedence)."""
        return self.parse_logical()

    def parse_logical(self) -> Expression:
        """Parse logical operators: and, or, nor, but not, xor, unless."""
        left = self.parse_comparison()

        while self.current.type in (
            TokenType.AND, TokenType.OR, TokenType.NOR,
            TokenType.BUT_NOT, TokenType.XOR, TokenType.UNLESS,
        ):
            op = self.advance().value
            right = self.parse_comparison()
            left = LogicalOp(line=left.line, column=left.column, left=left, operator=op, right=right)

        return left

    def parse_comparison(self) -> Expression:
        """Parse comparison operators."""
        left = self.parse_addition()

        while self.current.type in (
            TokenType.VIBES_EQUAL, TokenType.LOOSE_EQUAL,
            TokenType.STRICT_EQUAL, TokenType.IDENTITY_EQUAL,
            TokenType.EXTENDED_EQUAL, TokenType.NOT_EQUAL,
            TokenType.LESS, TokenType.GREATER,
            TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL,
        ):
            tok = self.advance()
            right = self.parse_addition()
            eq_count = tok.equal_count
            left = ComparisonOp(
                line=left.line, column=left.column,
                left=left, operator=tok.value, right=right,
                equal_count=eq_count,
            )

        return left

    def parse_addition(self) -> Expression:
        """Parse + - & with whitespace-sensitive precedence."""
        left = self.parse_multiplication()

        while self.current.type in (TokenType.PLUS, TokenType.MINUS, TokenType.AMPERSAND):
            tok = self.advance()
            right = self.parse_multiplication()
            left = BinaryOp(
                line=left.line, column=left.column,
                left=left, operator=tok.value, right=right,
                left_spaces=tok.spaces_before,
                right_spaces=tok.spaces_after,
            )

        return left

    def parse_multiplication(self) -> Expression:
        """Parse * / % with whitespace-sensitive precedence."""
        left = self.parse_power()

        while self.current.type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            tok = self.advance()
            right = self.parse_power()
            left = BinaryOp(
                line=left.line, column=left.column,
                left=left, operator=tok.value, right=right,
                left_spaces=tok.spaces_before,
                right_spaces=tok.spaces_after,
            )

        return left

    def parse_power(self) -> Expression:
        """Parse ^ (right-associative)."""
        left = self.parse_unary()

        if self.current.type == TokenType.CARET:
            tok = self.advance()
            right = self.parse_power()  # Right-associative
            left = BinaryOp(
                line=left.line, column=left.column,
                left=left, operator="^", right=right,
                left_spaces=tok.spaces_before,
                right_spaces=tok.spaces_after,
            )

        return left

    def parse_unary(self) -> Expression:
        """Parse unary operators: -, not."""
        if self.current.type == TokenType.MINUS:
            tok = self.advance()
            operand = self.parse_unary()
            return UnaryOp(line=tok.line, column=tok.column, operator="-", operand=operand)
        if self.current.type == TokenType.NOT:
            tok = self.advance()
            operand = self.parse_unary()
            return UnaryOp(line=tok.line, column=tok.column, operator="not", operand=operand)
        return self.parse_postfix()

    def parse_postfix(self) -> Expression:
        """Parse postfix operations: function calls, member access, index access."""
        expr = self.parse_primary()

        while True:
            if self.current.type == TokenType.LPAREN:
                # Function call
                self.advance()
                args = []
                while self.current.type != TokenType.RPAREN:
                    args.append(self.parse_expression())
                    if not self.match(TokenType.COMMA):
                        break
                self.expect(TokenType.RPAREN)
                expr = FunctionCall(line=expr.line, column=expr.column, callee=expr, arguments=args)
            elif self.current.type == TokenType.DOT:
                # Member access — accept any token as member name (keywords can be method names)
                self.advance()
                if self.current.value is not None:
                    member = self.current.value
                    self.advance()
                else:
                    raise ParseError(
                        self.current.line, self.current.column,
                        "Expected member name"
                    )
                # Check for method call
                if self.current.type == TokenType.LPAREN:
                    self.advance()
                    args = []
                    while self.current.type != TokenType.RPAREN:
                        args.append(self.parse_expression())
                        if not self.match(TokenType.COMMA):
                            break
                    self.expect(TokenType.RPAREN)
                    expr = FunctionCall(
                        line=expr.line, column=expr.column,
                        callee=MemberAccess(line=expr.line, column=expr.column, object=expr, member=member),
                        arguments=args,
                    )
                else:
                    expr = MemberAccess(line=expr.line, column=expr.column, object=expr, member=member)
            elif self.current.type == TokenType.LBRACKET:
                # Index access
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                expr = IndexAccess(line=expr.line, column=expr.column, object=expr, index=index)
            else:
                break

        return expr

    def parse_primary(self) -> Expression:
        """Parse primary expressions: literals, identifiers, parenthesized, etc."""
        tok = self.current

        # Number
        if tok.type == TokenType.NUMBER:
            self.advance()
            return NumberLiteral(line=tok.line, column=tok.column, value=tok.value)

        # String
        if tok.type == TokenType.STRING:
            self.advance()
            return StringLiteral(line=tok.line, column=tok.column, value=tok.value)

        # Booleans
        if tok.type == TokenType.YEP:
            self.advance()
            return BoolLiteral(line=tok.line, column=tok.column, value="yep")
        if tok.type == TokenType.NOPE:
            self.advance()
            return BoolLiteral(line=tok.line, column=tok.column, value="nope")
        if tok.type == TokenType.DUNNO:
            self.advance()
            return BoolLiteral(line=tok.line, column=tok.column, value="dunno")

        # Séance — accepts string OR identifier for variable name
        if tok.type == TokenType.SEANCE:
            self.advance()
            self.expect(TokenType.LPAREN)
            if self.current.type == TokenType.STRING:
                name = self.advance().value
            elif self.current.type == TokenType.IDENTIFIER:
                name = self.advance().value
            else:
                self.error("Expected variable name (string or identifier)")
            self.expect(TokenType.RPAREN)
            return SeanceCall(line=tok.line, column=tok.column, name=name)

        # Odds
        if tok.type == TokenType.ODDS:
            self.advance()
            self.expect(TokenType.LPAREN)
            cond = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return OddsCall(line=tok.line, column=tok.column, condition=cond)

        # Remember
        if tok.type == TokenType.REMEMBER:
            self.advance()
            var_name = self.expect(TokenType.IDENTIFIER, "Expected variable name").value
            index = self.parse_expression()
            return RememberCall(line=tok.line, column=tok.column, variable=var_name, index=index)

        # Become
        if tok.type == TokenType.BECOME:
            self.advance()
            pname = self.expect(TokenType.IDENTIFIER, "Expected personality name").value
            self.expect(TokenType.LPAREN)
            args = []
            while self.current.type != TokenType.RPAREN:
                args.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
            self.expect(TokenType.RPAREN)
            return BecomeCall(line=tok.line, column=tok.column, personality=pname, arguments=args)

        # Chill
        if tok.type == TokenType.CHILL:
            self.advance()
            expr = self.parse_expression()
            return FunctionCall(
                line=tok.line, column=tok.column,
                callee=VariableAccess(name="__chill__"),
                arguments=[expr],
            )

        # Graph
        if tok.type == TokenType.GRAPH:
            self.advance()
            self.expect(TokenType.DOT)
            method = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.LPAREN)
            args = []
            while self.current.type != TokenType.RPAREN:
                args.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
            self.expect(TokenType.RPAREN)
            return GraphAccess(line=tok.line, column=tok.column, method=method, arguments=args)

        # Sanity namespace
        if tok.type == TokenType.SANITY:
            self.advance()
            self.expect(TokenType.DOT)
            method = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.LPAREN)
            args = []
            while self.current.type != TokenType.RPAREN:
                args.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
            self.expect(TokenType.RPAREN)
            return SanityAccess(line=tok.line, column=tok.column, method=method, arguments=args)

        # Ask — read stdin line
        if tok.type == TokenType.ASK:
            self.advance()
            self.expect(TokenType.LPAREN)
            prompt = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return AskExpr(line=tok.line, column=tok.column, prompt=prompt)

        # Listen — read all stdin
        if tok.type == TokenType.LISTEN:
            self.advance()
            self.expect(TokenType.LPAREN)
            self.expect(TokenType.RPAREN)
            return ListenExpr(line=tok.line, column=tok.column)

        # Read — read file handle
        if tok.type == TokenType.READ_KW:
            self.advance()
            name = self.expect(TokenType.IDENTIFIER, "Expected file handle name").value
            return ReadExpr(line=tok.line, column=tok.column, handle_name=name)

        # Canvas — create a canvas
        if tok.type == TokenType.CANVAS:
            self.advance()
            self.expect(TokenType.LPAREN)
            title = self.parse_expression()
            self.expect(TokenType.COMMA)
            width = self.parse_expression()
            self.expect(TokenType.COMMA)
            height = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return CanvasExpr(line=tok.line, column=tok.column, title=title, width=width, height=height)

        # Mood lock declaration: mood("name")
        if tok.type == TokenType.MOOD:
            self.advance()
            self.expect(TokenType.LPAREN)
            name = self.expect(TokenType.STRING, "Expected lock name").value
            self.expect(TokenType.RPAREN)
            return FunctionCall(
                line=tok.line, column=tok.column,
                callee=VariableAccess(name="__mood_lock__"),
                arguments=[StringLiteral(value=name)],
            )

        # Vibe as expression
        if tok.type == TokenType.VIBE:
            self.advance()
            self.skip_newlines()
            body = self.parse_block()
            return FunctionCall(
                line=tok.line, column=tok.column,
                callee=VariableAccess(name="__vibe__"),
                arguments=[],
            )

        # List literal
        if tok.type == TokenType.LBRACKET:
            self.advance()
            elements = []
            while self.current.type != TokenType.RBRACKET:
                elements.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
            self.expect(TokenType.RBRACKET)
            return ListLiteral(line=tok.line, column=tok.column, elements=elements)

        # Blob literal
        if tok.type == TokenType.LBRACE:
            return self.parse_blob_literal()

        # Parenthesized expression
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        # Identifier
        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            return VariableAccess(line=tok.line, column=tok.column, name=tok.value)

        raise self.error(f"Unexpected token: {tok.type.name} ({tok.value!r})")

    def parse_blob_literal(self) -> BlobLiteral:
        tok = self.advance()  # {
        pairs = []
        self.skip_newlines()
        while self.current.type != TokenType.RBRACE:
            key = self.expect(TokenType.IDENTIFIER, "Expected blob key").value
            self.expect(TokenType.COLON, "Expected ':' after blob key")
            value = self.parse_expression()
            pairs.append((key, value))
            self.match(TokenType.COMMA)
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        return BlobLiteral(line=tok.line, column=tok.column, pairs=pairs)
