"""Core interpreter runtime for (In)SanityLang — Part 1: Setup & Expression evaluation."""
from __future__ import annotations
import random
import time
import json
import os
import hashlib
from pathlib import Path
from typing import Any, Optional

from .ast_nodes import *
from .tokens import TokenType
from .types import (
    SanValue, SanType, san_number, san_word, san_yep, san_nope,
    san_dunno, san_void, san_list, san_blob,
    coerce, is_truthy, is_void, type_name,
    vibes_equal, loose_equal, strict_equal, levenshtein_distance,
)
from .variables import Variable, Mood, Trait, Environment
from .sanity_points import SanityTracker
from .lexer import Lexer
from .parser import Parser
from .stdlib import is_stdlib_module, call_stdlib


class SanityError(Exception):
    """Runtime error in SanityLang."""
    def __init__(self, message: str, blame: str = "", mood: str = "Neutral"):
        super().__init__(message)
        self.blame = blame
        self.mood = mood


class BreakSignal(Exception):
    """Signal for 'enough.' (break)."""
    pass


class ReturnSignal(Exception):
    """Signal for return statements."""
    def __init__(self, value: SanValue, terminators: list[str]):
        self.value = value
        self.terminators = terminators


class Interpreter:
    """The main (In)SanityLang interpreter."""

    def __init__(self, source_path: str = "<repl>", flags: dict | None = None,
                 program_args: list[str] | None = None):
        self.source_path = source_path
        self.flags = flags or {}
        self.program_args = program_args or []

        # Sanity Points
        self.sp = SanityTracker(
            initial=0 if self.flags.get("chaos") else 100,
            strict=self.flags.get("strict", False),
            lenient=self.flags.get("lenient", False),
            pray_mercy=self.flags.get("pray", False),
            audit=self.flags.get("audit", False),
        )

        # Environment
        self.global_env = Environment(scope_id=0)
        self.current_env = self.global_env
        self.scope_counter = 0

        # Statement counter (global, for Age/timing)
        self.stmt_counter = 0

        # Afterlife
        self.afterlife: dict[str, list[tuple[SanValue, Mood, int, int]]] = {}  # name -> [(value, mood, scars, séance_count)]

        # Ghost tracking
        self.ghost_count = 0

        # Function call counts
        self.call_counts: dict[str, int] = {}

        # Functions storage
        self.functions: dict[str, tuple[FunctionDecl, Environment]] = {}

        # Memoization caches (for 'did' functions)
        self.memo_caches: dict[str, dict] = {}

        # Foreshadow tracking
        self.foreshadowed: dict[str, bool] = {}  # name -> fulfilled

        # Event listeners
        self.listeners: dict[str, list[tuple[Block, Environment]]] = {}

        # Oops counter
        self.oops_count = 0

        # Yolo error counts per block
        self.yolo_error_count = 0

        # Banned features
        self.banned: set[str] = set()

        # Grammar state
        self.grammar_aliases: dict[str, str] = {}
        self.grammar_removed: set[str] = set()

        # Prayers
        self.prayers: set[str] = set()

        # Dream file path
        self.dream_path = f"{source_path}.dream" if source_path != "<repl>" else None

        # Blame file path
        self.blame_path = f"{source_path}.blame" if source_path != "<repl>" else None

        # Therapy log file path
        self.therapy_path = f"{source_path}.therapy" if source_path != "<repl>" else None

        # Jackpot counters
        self.jackpot_counts: dict[int, int] = {}  # line -> check count

        # Bet loss tracking per variable (for Unlucky trait)
        self.bet_losses: dict[str, int] = {}

        # Active curses in scope
        self.active_curses: set[str] = set()

        # Statement history for rewind
        self.stmt_history: list[Statement] = []

        # Output capture (for testing)
        self.output: list[str] = []

        # Personality definitions
        self.personalities: dict[str, PersonalityDef] = {}

        # Relationship graph edges
        self.graph_edges: dict[str, set[str]] = {}

        # Emotional relationships — {rel_type: {a: {b, c, ...}}}
        self.relationships: dict[str, dict[str, set[str]]] = {
            "hates": {},
            "fears": {},
            "envies": {},
            "ignores": {},
            "mirrors": {},
            "haunts": {},
        }
        # Mirror delayed values: var_name -> value from previous statement
        self.mirror_pending: dict[str, SanValue] = {}

        # Chapter definitions
        self.chapters: dict[str, ChapterDef] = {}
        self.chapter_trust: dict[str, int] = {}  # name -> trust (0-100, default 70)
        self.chapter_allies: dict[str, set[str]] = {}  # name -> set of allied chapter names
        self.chapter_rivals: dict[str, set[str]] = {}  # name -> set of rival chapter names

        # No-mood flag
        self.no_mood = self.flags.get("no_mood", False)

        # Insanity mode effects
        self._insanity_swap_counter = 0

        # Loop interaction tracking
        self.ugh_quit_probability: float = 0.0

        # Cached return values (for return with '..' terminator)
        self.cached_returns: dict[str, SanValue] = {}

        # Track function names whose most recent call was their first call (for excited mood)
        self._first_call_results: set[str] = set()

        # File handles for filesystem IO
        self.file_handles: dict[str, object] = {}  # handle_name -> SanFileHandle

        # IO terminator state
        self._print_cache: set[str] = set()     # For '..' — cached strings never re-printed
        self._last_print: str = ""               # For '~' — previous print content
        self._write_cache: set[str] = set()      # For '..' — cached writes (content hashes)

    # ================================================
    # Main execution
    # ================================================

    def run(self, source: str) -> SanValue:
        """Run a SanityLang program from source string."""
        lexer = Lexer(source, aliases=self.grammar_aliases)
        lexer.removed_keywords = self.grammar_removed
        tokens = lexer.tokenize()
        parser = Parser(tokens, sanity_points=self.sp.sp)
        program = parser.parse()
        return self.execute_program(program)

    def execute_program(self, program: Program) -> SanValue:
        """Execute a parsed Program."""
        self.sp.is_runtime = True

        # Populate built-in args and flags (§29)
        self._populate_args_and_flags()

        # Register chapters
        for ch in program.chapters:
            self.chapters[ch.name] = ch
            self.chapter_trust.setdefault(ch.name, 70)
            if ch.allies:
                self.chapter_allies[ch.name] = set(ch.allies)
            if ch.rivals:
                self.chapter_rivals[ch.name] = set(ch.rivals)

        # Execute must functions
        for name, (decl, env) in list(self.functions.items()):
            if decl.keyword == "must":
                self._call_function(name, [], decl, env)

        # Load dream variables
        self._load_dreams()

        # Narrative structure
        if program.prologue:
            self._exec_block(program.prologue)

        # Execute arcs in order
        completed_arcs: set[str] = set()
        for arc in program.arcs:
            if arc.requires and arc.requires not in completed_arcs:
                # Required arc not completed, make variables uncertain
                pass
            else:
                self._exec_block(arc.body)
                completed_arcs.add(arc.name)

        # Climax
        if program.climax:
            self._exec_block(program.climax.body)

        # Main body
        result = san_void()
        for stmt in program.body:
            result = self.execute(stmt)

        # Epilogue (always runs)
        if program.epilogue:
            try:
                self._exec_block(program.epilogue)
            except Exception:
                pass  # Epilogue always runs, even after crashes

        # Save dream variables
        self._save_dreams()

        # Check unfulfilled foreshadows
        for name, fulfilled in self.foreshadowed.items():
            if not fulfilled:
                self.sp.unfulfilled_foreshadow()

        # Check uncalled 'should' functions
        for name, (decl, env) in self.functions.items():
            if decl.keyword == "should" and self.call_counts.get(name, 0) == 0:
                self.sp.should_not_called()

        # Penalize unclosed file handles (-5 SP each)
        unclosed = list(self.file_handles.keys())
        if unclosed:
            for hname in unclosed:
                fh = self.file_handles[hname]
                if hasattr(fh, 'close'):
                    fh.close()
                self.sp.file_unclosed_penalty()
            if len(unclosed) >= 3:
                self.output.append(
                    "[SanityLang] You're leaking file handles. "
                    "This is going on your permanent record."
                )
            self.file_handles.clear()

        return result

    # ================================================
    # Statement execution
    # ================================================

    def execute(self, node: Statement) -> SanValue:
        """Execute a statement node."""
        self.stmt_counter += 1
        self.stmt_history.append(node)

        # Ghost tax every 100 statements
        if self.stmt_counter % 100 == 0 and self.ghost_count > 0:
            self.sp.ghost_tax(self.ghost_count)

        # Periodic variable lifecycle checks (every 50 statements)
        if self.stmt_counter % 50 == 0:
            for var in self.current_env.all_variables().values():
                var.check_whatever_mutation(self.stmt_counter)
                var.check_mood_decay(self.stmt_counter)
                var.check_sad_from_neglect(self.stmt_counter)
                # Unobserve if not accessed for 200+ statements
                if var.observed and (self.stmt_counter - var.last_accessed) >= 200:
                    var.observed = False
                # Popular / Lonely trait from graph degree
                edge_count = len(self.graph_edges.get(var.name, set()))
                if edge_count >= 5 and Trait.POPULAR not in var.traits:
                    self._gain_trait(var, Trait.POPULAR)
                if edge_count == 0 and (self.stmt_counter - var.last_accessed) >= 100:
                    if Trait.LONELY not in var.traits:
                        self._gain_trait(var, Trait.LONELY)
                # Popular trust bonus / Lonely trust penalty
                if Trait.POPULAR in var.traits:
                    var.trust = min(100, var.trust + 1)
                if Trait.LONELY in var.traits:
                    var.trust = max(0, var.trust - 1)
                    if var.mood == Mood.NEUTRAL:
                        var.mood = Mood.SAD
                        var.mood_set_at = self.stmt_counter

        # Insanity mode effects
        if self.sp.insanity_mode:
            self._apply_insanity_effects()

        # Dispatch
        result = self._dispatch(node)

        # Mirror sync: apply pending mirror values AFTER statement executes
        for target_name, pending_val in list(self.mirror_pending.items()):
            var = self.current_env.get(target_name)
            if var:
                var.value = pending_val
        # Prepare next tick's mirror values
        self.mirror_pending.clear()
        for mirrorer, targets in self.relationships["mirrors"].items():
            for target in targets:
                source_var = self.current_env.get(target)
                if source_var:
                    self.mirror_pending[mirrorer] = source_var.value.copy()

        # Apply terminators
        if hasattr(node, 'terminators') and node.terminators:
            result = self._apply_terminators(result, node.terminators)

        return result

    def _dispatch(self, node: Statement) -> SanValue:
        """Dispatch to the appropriate handler."""
        if isinstance(node, VarDeclaration):
            return self._exec_var_decl(node)
        if isinstance(node, Assignment):
            return self._exec_assignment(node)
        if isinstance(node, PrintStatement):
            return self._exec_print(node)
        if isinstance(node, ExpressionStatement):
            return self.evaluate(node.expression)
        if isinstance(node, IfStatement):
            return self._exec_if(node)
        if isinstance(node, UnlessStatement):
            return self._exec_unless(node)
        if isinstance(node, SupposeStatement):
            return self._exec_suppose(node)
        if isinstance(node, PretendStatement):
            return self._exec_pretend(node)
        if isinstance(node, CheckStatement):
            return self._exec_check(node)
        if isinstance(node, AgainLoop):
            return self._exec_again(node)
        if isinstance(node, PlsLoop):
            return self._exec_pls(node)
        if isinstance(node, UghLoop):
            return self._exec_ugh(node)
        if isinstance(node, ForeverLoop):
            return self._exec_forever(node)
        if isinstance(node, HopefullyLoop):
            return self._exec_hopefully(node)
        if isinstance(node, ReluctantlyLoop):
            return self._exec_reluctantly(node)
        if isinstance(node, NeverBlock):
            # Never block doesn't execute, but variables declared inside
            # are sent to the afterlife for séance access
            env = Environment(parent=self.current_env, scope_id=self._new_scope_id())
            old_env = self.current_env
            self.current_env = env
            try:
                for stmt in node.body.statements:
                    if isinstance(stmt, VarDeclaration):
                        # Evaluate and define the variable
                        val = self.evaluate(stmt.value) if stmt.value else san_void()
                        var = Variable(name=stmt.name, value=val, keyword=stmt.keyword, decl_line=stmt.line)
                        env.define(stmt.name, var)
            except Exception:
                pass  # Never block errors are silently ignored
            finally:
                # Send all declared variables to the afterlife
                for name, var in env.variables.items():
                    self._send_to_afterlife(name, var.value, var.mood, var.scars)
                self.current_env = old_env
            return san_void()
        if isinstance(node, EnoughStatement):
            raise BreakSignal()
        if isinstance(node, FunctionDecl):
            return self._exec_func_decl(node)
        if isinstance(node, ReturnStatement):
            return self._exec_return(node)
        if isinstance(node, TryCope):
            return self._exec_try(node)
        if isinstance(node, BlameStatement):
            return self._exec_blame(node)
        if isinstance(node, OopsStatement):
            return self._exec_oops(node)
        if isinstance(node, YoloBlock):
            return self._exec_yolo(node)
        if isinstance(node, BetBlock):
            return self._exec_bet(node)
        if isinstance(node, JackpotBlock):
            return self._exec_jackpot(node)
        if isinstance(node, ForeshadowStatement):
            return self._exec_foreshadow(node)
        if isinstance(node, FulfillStatement):
            return self._exec_fulfill(node)
        if isinstance(node, RewindStatement):
            return self._exec_rewind(node)
        if isinstance(node, RecallStatement):
            return self._exec_recall(node)
        if isinstance(node, PersonalityDef):
            return self._exec_personality_def(node)
        if isinstance(node, WhenBlock):
            return self._exec_when(node)
        if isinstance(node, WtfStatement):
            return self._exec_wtf(node)
        if isinstance(node, HuhStatement):
            return self._exec_huh(node)
        if isinstance(node, CryStatement):
            return self._exec_cry(node)
        if isinstance(node, TherapyStatement):
            return self._exec_therapy(node)
        if isinstance(node, OracleStatement):
            return self._exec_oracle(node)
        if isinstance(node, GrammarAlias):
            return self._exec_grammar_alias(node)
        if isinstance(node, GrammarRemove):
            return self._exec_grammar_remove(node)
        if isinstance(node, PrayStatement):
            return self._exec_pray(node)
        if isinstance(node, NoStatement):
            return self._exec_no(node)
        if isinstance(node, ExorciseStatement):
            return self._exec_exorcise(node)
        if isinstance(node, IAmOkayStatement):
            return self._exec_i_am_okay(node)
        if isinstance(node, ForgetsEveryone):
            return self._exec_forgets_everyone(node)
        if isinstance(node, DeleteStatement):
            return self._exec_delete(node)
        if isinstance(node, VibeBlock):
            # Simplified: run body synchronously (no real concurrency)
            return self._exec_block(node.body)
        # Console IO
        if isinstance(node, ShoutStatement):
            return self._exec_shout(node)
        if isinstance(node, WhisperStatement):
            return self._exec_whisper_stmt(node)
        # Filesystem IO
        if isinstance(node, OpenStatement):
            return self._exec_open(node)
        if isinstance(node, WriteStatement):
            return self._exec_write(node)
        if isinstance(node, AppendStatement):
            return self._exec_append(node)
        if isinstance(node, CloseStatement):
            return self._exec_close(node)
        # Call management
        if isinstance(node, ForgetCallsStatement):
            return self._exec_forget_calls(node)
        return san_void()

    # ================================================
    # Expression evaluation
    # ================================================

    def evaluate(self, node: Expression) -> SanValue:
        """Evaluate an expression node."""
        if isinstance(node, NumberLiteral):
            return san_number(node.value)
        if isinstance(node, StringLiteral):
            val = node.value
            # String interpolation: {varname}
            if "{" in val:
                import re
                def replace_var(m):
                    vname = m.group(1)
                    var = self.current_env.get(vname)
                    if var:
                        var.record_access(self.stmt_counter)
                        return str(var.value)
                    return m.group(0)
                val = re.sub(r'\{(\w+)\}', replace_var, val)
            return san_word(val)
        if isinstance(node, BoolLiteral):
            if node.value == "yep":
                return san_yep()
            if node.value == "nope":
                return san_nope()
            return san_dunno()
        if isinstance(node, VoidLiteral):
            return san_void()
        if isinstance(node, ListLiteral):
            return san_list([self.evaluate(e) for e in node.elements])
        if isinstance(node, BlobLiteral):
            return san_blob({k: self.evaluate(v) for k, v in node.pairs})
        if isinstance(node, VariableAccess):
            return self._eval_var_access(node)
        if isinstance(node, BinaryOp):
            return self._eval_binary(node)
        if isinstance(node, UnaryOp):
            return self._eval_unary(node)
        if isinstance(node, ComparisonOp):
            return self._eval_comparison(node)
        if isinstance(node, LogicalOp):
            return self._eval_logical(node)
        if isinstance(node, EmotionalOp):
            return self._eval_emotional(node)
        if isinstance(node, FunctionCall):
            return self._eval_function_call(node)
        if isinstance(node, MemberAccess):
            return self._eval_member_access(node)
        if isinstance(node, IndexAccess):
            return self._eval_index_access(node)
        if isinstance(node, SeanceCall):
            return self._eval_seance(node)
        if isinstance(node, OddsCall):
            return self._eval_odds(node)
        if isinstance(node, RememberCall):
            return self._eval_remember(node)
        if isinstance(node, BecomeCall):
            return self._eval_become(node)
        if isinstance(node, GraphAccess):
            return self._eval_graph(node)
        if isinstance(node, SanityAccess):
            return self._eval_sanity(node)
        # Console IO expressions
        if isinstance(node, AskExpr):
            return self._eval_ask(node)
        if isinstance(node, ListenExpr):
            return self._eval_listen(node)
        # Filesystem IO expressions
        if isinstance(node, ReadExpr):
            return self._eval_read(node)
        # Graphics expressions
        if isinstance(node, CanvasExpr):
            return self._eval_canvas(node)
        return san_void()

    def _eval_var_access(self, node: VariableAccess) -> SanValue:
        var = self.current_env.get(node.name)
        if not var:
            raise SanityError(f"Variable '{node.name}' is not defined")

        # Ghost check
        if var.keyword == "ghost":
            raise SanityError(f"Variable '{node.name}' is a ghost. Use séance to access it.")

        # Whisper scope check
        if var.keyword == "whisper" and not self.current_env.has_local(node.name):
            return san_void()

        var.record_access(self.stmt_counter)

        # Envies convergence: converge 10% toward envied variable's value
        envied_by = self.relationships["envies"].get(node.name)
        if envied_by:
            for envied_name in envied_by:
                envied_var = self.current_env.get(envied_name)
                if envied_var and var.value.type == SanType.NUMBER and envied_var.value.type == SanType.NUMBER:
                    diff = envied_var.value.value - var.value.value
                    var.value = san_number(var.value.value + diff * 0.1)

        # Jealous convergence: if another var with same name exists in a parent scope
        if var.mood == Mood.JEALOUS and var.observed:
            shadow = self._find_shadow_var(node.name)
            if shadow and shadow.value.type == SanType.NUMBER and var.value.type == SanType.NUMBER:
                diff = shadow.value.value - var.value.value
                var.value = san_number(var.value.value + diff * 0.1)

        # Grief state
        if var.grief_remaining > 0:
            var.grief_remaining -= 1
            return san_void()

        # Trust check — at 0, 20% chance of returning Void
        if var.trust <= 0 and random.random() < 0.2:
            return san_void()

        # Unlucky trait — 10% chance of Void
        if var.has_trait(Trait.UNLUCKY) and random.random() < 0.1:
            return san_void()

        # Uncertainty — 15% chance of using previous value
        if var.is_uncertain and var.previous_value and random.random() < 0.15:
            return var.previous_value

        return var.value

    def _eval_binary(self, node: BinaryOp) -> SanValue:
        # Whitespace precedence: detect ambiguous spacing (-2 SP)
        if node.left_spaces == node.right_spaces and node.left_spaces > 0:
            # Equal spacing on both sides — ambiguous, costs SP
            self.sp.ambiguous_precedence()

        # Ignores check: collect all variable names in expression
        left_vars = self._collect_variable_names(node.left)
        right_vars = self._collect_variable_names(node.right)
        for lv_name in left_vars:
            for rv_name in right_vars:
                ignores_set = self.relationships["ignores"].get(lv_name, set())
                if rv_name in ignores_set:
                    raise SanityError(f"'{lv_name}' ignores '{rv_name}' — they cannot appear in the same expression")
                reverse_set = self.relationships["ignores"].get(rv_name, set())
                if lv_name in reverse_set:
                    raise SanityError(f"'{rv_name}' ignores '{lv_name}' — they cannot appear in the same expression")

        left = self.evaluate(node.left)
        right = self.evaluate(node.right)

        # Angry swap: if both operand variables are Angry, swap their values
        if isinstance(node.left, VariableAccess) and isinstance(node.right, VariableAccess):
            lvar = self.current_env.get(node.left.name)
            rvar = self.current_env.get(node.right.name)
            if lvar and rvar and lvar.mood == Mood.ANGRY and rvar.mood == Mood.ANGRY:
                lvar.value, rvar.value = rvar.value.copy(), lvar.value.copy()
                left, right = lvar.value, rvar.value

        # Void propagation
        if is_void(left) or is_void(right):
            return san_void()
        # Dunno propagation
        if left.type == SanType.DUNNO or right.type == SanType.DUNNO:
            return san_dunno()

        op = node.operator

        # Coerce types
        left_c, right_c, l_coerced, r_coerced = coerce(left, right, op)

        # Track scars from coercion
        if l_coerced and isinstance(node.left, VariableAccess):
            var = self.current_env.get(node.left.name)
            if var and not var.has_trait(Trait.RESILIENT):
                var.add_scar()
        if r_coerced and isinstance(node.right, VariableAccess):
            var = self.current_env.get(node.right.name)
            if var and not var.has_trait(Trait.RESILIENT):
                var.add_scar()

        # Concatenation
        if op == "&":
            return san_word(str(left_c.value) + str(right_c.value))

        # Arithmetic
        if left_c.type == SanType.NUMBER and right_c.type == SanType.NUMBER:
            lv, rv = left_c.value, right_c.value
            # Insanity noise
            if self.sp.insanity_mode:
                noise = abs(self.sp.sp) / 10.0 / 100.0
                lv *= (1 + random.uniform(-noise, noise))
                rv *= (1 + random.uniform(-noise, noise))

            if op == "+":
                result = lv + rv
            elif op == "-":
                result = lv - rv
            elif op == "*":
                result = lv * rv
            elif op == "/":
                if rv == 0:
                    raise SanityError("Division by zero")
                result = lv / rv
            elif op == "%":
                if rv == 0:
                    raise SanityError("Modulo by zero")
                result = lv % rv
            elif op == "^":
                result = lv ** rv
            else:
                raise SanityError(f"Unknown operator: {op}")

            # Apply mood modifiers from source variables
            if isinstance(node.left, VariableAccess):
                var = self.current_env.get(node.left.name)
                if var:
                    result = var.apply_mood_to_number(result)

            # Curse variation
            # (simplified — full curse system would check imported curses)

            return san_number(result)

        # Word operations
        if left_c.type == SanType.WORD and right_c.type == SanType.WORD:
            if op == "+":
                return san_word(left_c.value + right_c.value)
            raise SanityError(f"Cannot apply '{op}' to Words")

        raise SanityError(f"Type error: {left.type.value} {op} {right.type.value}")

    def _eval_unary(self, node: UnaryOp) -> SanValue:
        operand = self.evaluate(node.operand)
        if node.operator == "-":
            if operand.type == SanType.NUMBER:
                val = -operand.value
                if "negativity" in self.banned:
                    val = abs(val)
                return san_number(val)
            raise SanityError(f"Cannot negate {operand.type.value}")
        if node.operator == "not":
            return san_nope() if is_truthy(operand) else san_yep()
        return san_void()

    def _eval_comparison(self, node: ComparisonOp) -> SanValue:
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)

        # Afraid comparison side: right-side Afraid variable returns Void
        if isinstance(node.right, VariableAccess):
            rvar = self.current_env.get(node.right.name)
            if rvar and rvar.mood == Mood.AFRAID:
                return san_void()

        op = node.operator
        result = False

        if op == "~=":
            result = vibes_equal(left, right)
        elif op == "==":
            result = loose_equal(left, right)
        elif op == "===":
            result = strict_equal(left, right)
        elif op == "====":
            # Identity — same variable reference
            if isinstance(node.left, VariableAccess) and isinstance(node.right, VariableAccess):
                result = node.left.name == node.right.name
            else:
                result = False
        elif op == "!=":
            result = not loose_equal(left, right)
        elif op == "<":
            if left.type == SanType.NUMBER and right.type == SanType.NUMBER:
                result = left.value < right.value
        elif op == ">":
            if left.type == SanType.NUMBER and right.type == SanType.NUMBER:
                result = left.value > right.value
        elif op == "<=":
            if left.type == SanType.NUMBER and right.type == SanType.NUMBER:
                result = left.value <= right.value
        elif op == ">=":
            if left.type == SanType.NUMBER and right.type == SanType.NUMBER:
                result = left.value >= right.value
        else:
            # Extended equal ===== and beyond
            result = strict_equal(left, right)
            if result and node.equal_count >= 5:
                # Check mood
                lv = self.current_env.get(node.left.name) if isinstance(node.left, VariableAccess) else None
                rv = self.current_env.get(node.right.name) if isinstance(node.right, VariableAccess) else None
                if lv and rv:
                    if node.equal_count >= 5:
                        result = result and lv.mood == rv.mood
                    if node.equal_count >= 6:
                        result = result and lv.trust == rv.trust
                    if node.equal_count >= 7:
                        result = result and lv.age == rv.age
                    if node.equal_count >= 8:
                        result = result and lv.scars == rv.scars
                    if node.equal_count >= 9:
                        result = result and lv.doubt == rv.doubt
                    if node.equal_count >= 10:
                        result = result and len(lv.bonds) == len(rv.bonds)

        return san_yep() if result else san_nope()

    def _eval_logical(self, node: LogicalOp) -> SanValue:
        left = self.evaluate(node.left)
        op = node.operator

        if op == "and":
            if not is_truthy(left):
                return san_nope()
            right = self.evaluate(node.right)
            return san_yep() if is_truthy(right) else san_nope()
        if op == "or":
            if is_truthy(left):
                return san_yep()
            right = self.evaluate(node.right)
            return san_yep() if is_truthy(right) else san_nope()
        if op == "nor":
            if is_truthy(left):
                return san_nope()
            right = self.evaluate(node.right)
            return san_nope() if is_truthy(right) else san_yep()
        if op == "but not":
            right = self.evaluate(node.right)
            return san_yep() if is_truthy(left) and not is_truthy(right) else san_nope()
        if op == "xor":
            right = self.evaluate(node.right)
            l, r = is_truthy(left), is_truthy(right)
            return san_yep() if l != r else san_nope()
        if op == "unless":
            right = self.evaluate(node.right)
            return san_yep() if is_truthy(left) and not is_truthy(right) else san_nope()

        return san_nope()

    def _eval_emotional(self, node: EmotionalOp) -> SanValue:
        """Handle emotional operators: loves, hates, fears, envies, ignores, mirrors, haunts, forgets."""
        left_name = node.left.name if isinstance(node.left, VariableAccess) else None
        right_name = node.right.name if isinstance(node.right, VariableAccess) else None
        op = node.operator

        if not left_name or not right_name:
            raise SanityError("Emotional operators require variable names")

        left_var = self.current_env.get(left_name)
        right_var = self.current_env.get(right_name)
        if not left_var or not right_var:
            raise SanityError(f"Variable not found for emotional operator")

        # Add graph edge
        self._add_graph_edge(left_name, right_name)

        if op == "loves":
            # Create pinky-style bond
            if right_name not in left_var.bonds:
                left_var.bonds.append(right_name)
                right_var.bonds.append(left_name)
                self.sp.bond_formed()
        elif op == "hates":
            # Can never hold same value
            self.relationships["hates"].setdefault(left_name, set()).add(right_name)
            self.relationships["hates"].setdefault(right_name, set()).add(left_name)
        elif op == "fears":
            # When right changes, left becomes Afraid
            self.relationships["fears"].setdefault(left_name, set()).add(right_name)
        elif op == "envies":
            # a converges toward b on access
            self.relationships["envies"].setdefault(left_name, set()).add(right_name)
        elif op == "ignores":
            # Cannot appear in same expression
            self.relationships["ignores"].setdefault(left_name, set()).add(right_name)
        elif op == "mirrors":
            # a always equals b with 1-statement delay
            self.relationships["mirrors"].setdefault(left_name, set()).add(right_name)
        elif op == "haunts":
            # When a is deleted, b becomes Afraid for 100 statements
            self.relationships["haunts"].setdefault(left_name, set()).add(right_name)
        elif op == "forgets":
            # Remove all relationships between a and b
            if right_name in left_var.bonds:
                left_var.bonds.remove(right_name)
            if left_name in right_var.bonds:
                right_var.bonds.remove(left_name)
            self._remove_graph_edge(left_name, right_name)
            # Clear from all relationship dicts
            for rel_type in self.relationships:
                if left_name in self.relationships[rel_type]:
                    self.relationships[rel_type][left_name].discard(right_name)
                if right_name in self.relationships[rel_type]:
                    self.relationships[rel_type][right_name].discard(left_name)

        return san_yep()

    def _eval_function_call(self, node: FunctionCall) -> SanValue:
        # Get function name
        if isinstance(node.callee, VariableAccess):
            name = node.callee.name
        elif isinstance(node.callee, MemberAccess):
            # Check for stdlib module call first: Math.add(...), Words.reverse(...), etc.
            if isinstance(node.callee.object, VariableAccess) and is_stdlib_module(node.callee.object.name):
                args = [self.evaluate(a) for a in node.arguments]
                return call_stdlib(node.callee.object.name, node.callee.member, self, args)
            # Regular method call on object
            obj = self.evaluate(node.callee.object)
            return self._call_method(obj, node.callee.member, [self.evaluate(a) for a in node.arguments])
        else:
            raise SanityError("Cannot call non-function")

        # Built-in special names
        if name == "__chill__":
            # chill (await)
            return self.evaluate(node.arguments[0]) if node.arguments else san_void()
        if name == "__mood_lock__":
            return san_void()

        # Look up function
        if name not in self.functions:
            raise SanityError(f"Function '{name}' is not defined")

        decl, closure_env = self.functions[name]
        args = [self.evaluate(a) for a in node.arguments]
        return self._call_function(name, args, decl, closure_env)

    def _call_function(self, name: str, args: list[SanValue],
                       decl: FunctionDecl, closure_env: Environment) -> SanValue:
        # Check 'might' condition
        if decl.keyword == "might" and decl.condition:
            cond = self.evaluate(decl.condition)
            if not is_truthy(cond):
                return san_void()

        # Will (stub) — returns Dunno
        if decl.keyword == "will" and not decl.body.statements:
            return san_dunno()

        # Cached return ('..') — always return the locked value
        if name in self.cached_returns:
            return self.cached_returns[name]

        # Call counting
        count = self.call_counts.get(name, 0) + 1
        self.call_counts[name] = count

        # Add graph edge for function call relationships
        self._add_graph_edge(name, f"__caller_{self.current_env.scope_id}")

        if count == 1:
            self.sp.first_function_call()
        elif count >= 10:
            self.sp.repetition_penalty()

        # 25-call refactor suggestion
        if count == 25:
            self.output.append(f"[compiler] Function '{name}' has been called 25 times. Maybe refactor?")

        # Memoization for 'did'
        if decl.keyword == "did":
            cache = self.memo_caches.setdefault(name, {})
            key = tuple(str(a) for a in args)
            if key in cache:
                return cache[key]

        # Resentful — 5% chance of Void at 100+ calls
        if count >= 100 and random.random() < 0.05:
            return san_void()

        # Create function scope — closure copy semantics
        func_env = Environment(parent=closure_env, scope_id=self._new_scope_id())
        self.sp.enter_scope()

        # Copy captured variables (copies, not references) unless scream
        for var_name, var in closure_env.all_variables().items():
            if var.keyword == "scream":
                # Live reference — don't copy
                func_env.define(var_name, var)
            else:
                # Copy the variable
                copied_var = Variable(
                    name=var.name, value=var.value,
                    keyword=var.keyword, decl_line=var.decl_line
                )
                copied_var.mood = var.mood
                copied_var.traits = set(var.traits)
                copied_var.trust = var.trust
                copied_var.scars = var.scars
                func_env.define(var_name, copied_var)

        # Bind parameters (overwrite any captured vars with same name)
        for i, param in enumerate(decl.params):
            val = args[i] if i < len(args) else san_void()
            func_env.define(param, Variable(
                name=param, value=val, keyword="sure", decl_line=decl.line
            ))

        # Execute body
        old_env = self.current_env
        self.current_env = func_env
        result = san_void()
        return_terminators: list[str] = []

        try:
            for stmt in decl.body.statements:
                result = self.execute(stmt)
        except ReturnSignal as ret:
            result = ret.value
            return_terminators = ret.terminators
        finally:
            self.current_env = old_env

        # Process return terminators
        for term in return_terminators:
            if term == "..":
                # Cache permanently
                self.cached_returns[name] = result
            elif term == "~":
                # Uncertain return
                if result.type == SanType.NUMBER:
                    result = SanValue(SanType.NUMBER, result.value)
                result = SanValue(result.type, result.value)  # copy
                # Mark as uncertain — caller should tag assigned var
            elif term == "!":
                # Forceful — result is clean, no trait propagation
                pass  # Traits are on variables, not values
            elif term == "?":
                # Debug print + mark Observed
                msg = f"[?] {result}"
                self.output.append(msg)

        # Tired function at 50+ calls
        if count >= 50:
            if result.type == SanType.NUMBER:
                result = san_number(result.value - 1)
            elif result.type == SanType.WORD and len(result.value) > 0:
                result = san_word(result.value[:-1])

        # Cache for 'did'
        if decl.keyword == "did":
            cache = self.memo_caches.setdefault(name, {})
            key = tuple(str(a) for a in args)
            cache[key] = result
            if len(cache) > 1000:
                oldest = next(iter(cache))
                self._send_to_afterlife(f"__memo_{name}_{oldest}", cache.pop(oldest), Mood.NEUTRAL, 0)

        # Excited mood on first call — track on interpreter
        if count == 1:
            self._first_call_results.add(name)
        else:
            self._first_call_results.discard(name)

        return result

    def _eval_member_access(self, node: MemberAccess) -> SanValue:
        obj = self.evaluate(node.object)
        if obj.type == SanType.BLOB:
            val = obj.value.get(node.member)
            return val if val else san_void()
        if obj.type == SanType.LIST:
            if node.member == "length":
                return san_number(len(obj.value))
        return san_void()

    def _eval_index_access(self, node: IndexAccess) -> SanValue:
        obj = self.evaluate(node.object)
        idx = self.evaluate(node.index)
        if obj.type == SanType.LIST:
            if idx.type == SanType.NUMBER:
                i = int(idx.value)
                if 0 <= i < len(obj.value):
                    return obj.value[i]
            return san_void()
        if obj.type == SanType.WORD:
            if idx.type == SanType.NUMBER:
                i = int(idx.value)
                if 0 <= i < len(obj.value):
                    return san_word(obj.value[i])
            return san_void()
        return san_void()

    def _eval_seance(self, node: SeanceCall) -> SanValue:
        self.sp.seance_use()
        name = node.name

        # Check for live ghost variable first
        var = self.current_env.get(name)
        if var and var.keyword == "ghost":
            var.record_access(self.stmt_counter)
            return var.value

        if name not in self.afterlife or not self.afterlife[name]:
            return san_void()

        entries = self.afterlife[name]
        # Get latest
        value, mood, scars, count = entries[-1]
        if count >= 3:
            entries.pop()  # Moved on
            return san_void()

        # Increment séance count
        entries[-1] = (value, mood, scars, count + 1)

        # Mood-based results
        if mood == Mood.AFRAID:
            return san_void()

        result = value.copy()

        # If died Angry, receiving variable also becomes Angry
        # (handled by caller when assigning)

        return result

    def _eval_odds(self, node: OddsCall) -> SanValue:
        # Simplified odds — evaluate condition and return percentage
        try:
            result = self.evaluate(node.condition)
            if is_truthy(result):
                return san_number(random.randint(60, 100))
            return san_number(random.randint(0, 40))
        except Exception:
            return san_number(50)

    def _eval_remember(self, node: RememberCall) -> SanValue:
        var = self.current_env.get(node.variable)
        if not var:
            return san_void()
        var.observed = True
        idx_val = self.evaluate(node.index)
        idx = int(idx_val.value) if idx_val.type == SanType.NUMBER else 0
        if 0 < idx <= len(var.history):
            return var.history[idx - 1]
        return san_void()

    def _eval_become(self, node: BecomeCall) -> SanValue:
        if node.personality not in self.personalities:
            raise SanityError(f"Personality '{node.personality}' is not defined")
        pdef = self.personalities[node.personality]
        # Create instance as a Blob
        instance = {}
        inst_env = Environment(parent=self.current_env, scope_id=self._new_scope_id())

        for stmt in pdef.body:
            if isinstance(stmt, VarDeclaration):
                val = self.evaluate(stmt.value) if stmt.value else san_void()
                instance[stmt.name] = val
            elif isinstance(stmt, FunctionDecl):
                self.functions[f"{node.personality}.{stmt.name}"] = (stmt, inst_env)

        return san_blob(instance)

    def _eval_graph(self, node: GraphAccess) -> SanValue:
        method = node.method
        if method == "edges":
            if node.arguments:
                name = self.evaluate(node.arguments[0])
                if name.type == SanType.WORD:
                    edges = self.graph_edges.get(name.value, set())
                    return san_list([san_word(e) for e in edges])
            return san_list([])
        if method == "distance":
            return san_number(-1)  # Simplified
        if method == "connected":
            return san_yep()
        if method == "isolated":
            isolated = [
                san_word(name)
                for name, edges in self.graph_edges.items()
                if len(edges) == 0
            ]
            return san_list(isolated)
        return san_void()

    def _eval_sanity(self, node: SanityAccess) -> SanValue:
        if node.method == "curses":
            return san_list([])  # Simplified
        return san_void()

    # ================================================
    # Console IO expression evaluators
    # ================================================

    def _eval_ask(self, node: AskExpr) -> SanValue:
        """Evaluate ask("prompt") — read a line from stdin, return as word."""
        # SP cost: -1
        self.sp.change(-1, "ask()")

        # Check --no-input flag
        if self.flags.get("no_input"):
            return san_word("")

        prompt_val = self.evaluate(node.prompt)
        prompt_str = str(prompt_val)
        try:
            result = input(prompt_str)
        except EOFError:
            result = ""

        # Simple sentiment analysis for mood assignment
        positive_words = {"yes", "yeah", "yep", "sure", "ok", "good", "great", "love", "happy"}
        negative_words = {"no", "nope", "nah", "bad", "hate", "sad", "angry", "worst"}
        words = set(result.lower().split())
        if words & positive_words:
            mood = Mood.HAPPY
        elif words & negative_words:
            mood = Mood.SAD
        else:
            mood = Mood.NEUTRAL

        # The result gets TAINTED trait (untrusted input)
        # This is tracked at the variable level when assigned
        # Store mood info on the interpreter for the next assignment
        self._last_input_mood = mood

        return san_word(result)

    def _eval_listen(self, node: ListenExpr) -> SanValue:
        """Evaluate listen() — read all stdin until EOF."""
        import sys

        # SP cost: -2
        self.sp.change(-2, "listen()")

        # Check --no-input flag
        if self.flags.get("no_input"):
            return san_word("")

        try:
            lines = sys.stdin.read()
        except Exception:
            lines = ""

        self._last_input_mood = Mood.OVERWHELMED  # Bulk input is overwhelming
        return san_word(lines)

    # ================================================
    # Filesystem IO expression evaluators
    # ================================================

    def _eval_read(self, node: ReadExpr) -> SanValue:
        """Evaluate read handle — read file contents."""
        from .filehandle import SanFileHandle

        handle_name = node.handle_name
        fh = self.file_handles.get(handle_name)
        if fh is None or not isinstance(fh, SanFileHandle):
            raise SanityError(f"No open file handle '{handle_name}'")
        if not fh.is_open:
            raise SanityError(f"File handle '{handle_name}' is closed")

        # SP cost scales with file size
        cost = fh.sp_cost_for_size(base_cost=3)
        self.sp._audit(f"read {handle_name}")
        self.sp.sp += self.sp._modifier(-cost)

        # Read terminator effects
        terms = getattr(node, 'terminators', [])

        # '..' cached — return cached content without hitting disk again
        cache_key = f"read:{handle_name}"
        if '..' in terms and cache_key in self.cached_returns:
            return self.cached_returns[cache_key]

        try:
            content = fh.read()
        except Exception as e:
            raise SanityError(f"Failed to read '{handle_name}': {e}")

        result = san_word(content)

        # '..' cache the result
        if '..' in terms:
            self.cached_returns[cache_key] = result

        # '?' debug — log handle state
        if '?' in terms:
            debug_msg = f"[read debug] {handle_name}: Mood={fh.mood.name}, Trust={fh.trust}, SP={fh.sp}"
            self.output.append(debug_msg)
            print(debug_msg)

        # Mark handle as Observed
        fh.observed = True

        return result

    # ================================================
    # Graphics expression evaluators
    # ================================================

    def _eval_canvas(self, node: CanvasExpr) -> SanValue:
        """Evaluate canvas("title", w, h) — create a canvas.

        Creates a SanCanvas (headless by default). The canvas is stored
        in self.canvases and returned as a Blob with canvas metadata.
        """
        from .canvas import SanCanvas

        title = str(self.evaluate(node.title))
        width_val = self.evaluate(node.width)
        height_val = self.evaluate(node.height)
        width = int(str(width_val)) if width_val else 800
        height = int(str(height_val)) if height_val else 600

        # SP cost: -3 for canvas creation
        self.sp.canvas_create()

        headless = self.flags.get("headless", True)  # Default headless
        canvas = SanCanvas(title, width, height, headless=headless)

        # Store canvas reference
        if not hasattr(self, 'canvases'):
            self.canvases: dict[str, SanCanvas] = {}
        self.canvases[title] = canvas

        if not headless:
            msg = f"[Canvas '{title}' ({width}x{height}) — use --headless for non-graphical mode]"
            self.output.append(msg)
            print(msg)

        # Return a blob with canvas info
        return san_blob({
            "title": san_word(title),
            "width": san_word(str(width)),
            "height": san_word(str(height)),
        })

    def _call_method(self, obj: SanValue, method: str, args: list[SanValue]) -> SanValue:
        """Call a method on a SanValue object."""
        if obj.type == SanType.LIST:
            if method == "length":
                return san_number(len(obj.value))
            if method == "push" and args:
                obj.value.append(args[0])
                return san_void()
            if method == "pop":
                return obj.value.pop() if obj.value else san_void()
        if obj.type == SanType.WORD:
            if method == "length":
                return san_number(len(obj.value))
            if method == "upper":
                return san_word(obj.value.upper())
            if method == "lower":
                return san_word(obj.value.lower())
            if method == "reverse":
                return san_word(obj.value[::-1])
            if method == "split":
                sep = args[0].value if args and args[0].type == SanType.WORD else " "
                return san_list([san_word(s) for s in obj.value.split(sep)])
        if obj.type == SanType.BLOB:
            # Instance method call
            for name, (decl, env) in self.functions.items():
                if name.endswith(f".{method}"):
                    return self._call_function(name, args, decl, env)
        return san_void()

    # ================================================
    # Graph helpers
    # ================================================

    def _add_graph_edge(self, a: str, b: str):
        self.graph_edges.setdefault(a, set()).add(b)
        self.graph_edges.setdefault(b, set()).add(a)

    def _remove_graph_edge(self, a: str, b: str):
        if a in self.graph_edges:
            self.graph_edges[a].discard(b)
        if b in self.graph_edges:
            self.graph_edges[b].discard(a)

    def _new_scope_id(self) -> int:
        self.scope_counter += 1
        return self.scope_counter

    def _send_to_afterlife(self, name: str, value: SanValue, mood: Mood, scars: int):
        """Send a variable's value to the Afterlife."""
        self.afterlife.setdefault(name, []).append((value, mood, scars, 0))

    def _collect_variable_names(self, node: Expression) -> set[str]:
        """Collect all variable names referenced in an expression."""
        names: set[str] = set()
        if isinstance(node, VariableAccess):
            names.add(node.name)
        elif isinstance(node, (BinaryOp, ComparisonOp, LogicalOp)):
            names |= self._collect_variable_names(node.left)
            names |= self._collect_variable_names(node.right)
        elif isinstance(node, UnaryOp):
            names |= self._collect_variable_names(node.operand)
        elif isinstance(node, FunctionCall):
            if isinstance(node.callee, VariableAccess):
                names.add(node.callee.name)
            for arg in node.arguments:
                names |= self._collect_variable_names(arg)
        return names

    def _references_variable(self, node: Expression) -> set[str]:
        """Recursively collect all VariableAccess names from an expression tree."""
        names: set[str] = set()
        if isinstance(node, VariableAccess):
            names.add(node.name)
        elif isinstance(node, BinaryOp):
            names |= self._references_variable(node.left)
            names |= self._references_variable(node.right)
        elif isinstance(node, UnaryOp):
            names |= self._references_variable(node.operand)
        elif isinstance(node, FunctionCall):
            if isinstance(node.callee, VariableAccess):
                pass  # function name doesn't count
            for arg in node.arguments:
                names |= self._references_variable(arg)
        return names

    # ================================================
    # Phase 6: Mood / Trait / Bond helpers
    # ================================================

    def _gain_trait(self, var: Variable, trait: Trait):
        """Add a trait to a variable, applying interactions and propagating through bonds."""
        # Blessed removes Cursed
        if trait == Trait.BLESSED and Trait.CURSED in var.traits:
            var.traits.discard(Trait.CURSED)
        if trait == Trait.CURSED and Trait.BLESSED in var.traits:
            return  # Can't curse a blessed variable

        var.traits.add(trait)

        # Elder + Tired cancel out
        if Trait.ELDER in var.traits and Trait.TIRED in var.traits:
            var.traits.discard(Trait.TIRED)

        # Lonely + Volatile = Erratic (we keep both, handled at access time)

        # Propagate trait through emotional bonds
        for bonded_name in var.bonds:
            bonded = self.current_env.get(bonded_name)
            if bonded and trait not in bonded.traits:
                # Paranoid rejects new traits from bonds
                if Trait.PARANOID in bonded.traits:
                    continue
                bonded.traits.add(trait)
                # Apply same interactions on the bonded var
                if Trait.ELDER in bonded.traits and Trait.TIRED in bonded.traits:
                    bonded.traits.discard(Trait.TIRED)
                if Trait.BLESSED in bonded.traits and Trait.CURSED in bonded.traits:
                    bonded.traits.discard(Trait.CURSED)

    def _set_mood(self, var: Variable, mood: Mood):
        """Set a variable's mood and propagate through bonds (1-hop)."""
        if Trait.ELDER in var.traits:
            return  # Elder: immune to mood changes
        var.mood = mood
        var.mood_set_at = self.stmt_counter
        self._propagate_mood(var)

    def _propagate_mood(self, var: Variable):
        """Propagate mood to bonded variables (1 hop, 1 operation delay via caller)."""
        for bonded_name in var.bonds:
            bonded = self.current_env.get(bonded_name)
            if bonded and bonded.mood != var.mood:
                if Trait.ELDER not in bonded.traits:
                    bonded.mood = var.mood
                    bonded.mood_set_at = self.stmt_counter

    def _find_shadow_var(self, name: str) -> "Variable | None":
        """Find a same-named variable in a parent scope (for Jealous convergence)."""
        env = self.current_env.parent
        while env:
            if name in env.variables:
                return env.variables[name]
            env = env.parent
        return None
