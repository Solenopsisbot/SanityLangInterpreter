"""Core interpreter runtime for (In)SanityLang — Part 2: Statement executors and helpers."""
from __future__ import annotations
import random
import time
import json
import os
from pathlib import Path
from typing import Any

from .ast_nodes import *
from .types import (
    SanValue, SanType, san_number, san_word, san_yep, san_nope,
    san_dunno, san_void, san_list, san_blob, is_truthy, is_void,
)
from .variables import Variable, Mood, Trait, Environment
from .runtime import Interpreter, SanityError, BreakSignal, ReturnSignal


def _install_statement_executors():
    """Install all statement executor methods onto the Interpreter class."""

    def _exec_var_decl(self, node: VarDeclaration) -> SanValue:
        name = node.name
        keyword = node.keyword

        # Feature bans
        if keyword == "ghost" and "ghosts" in self.banned:
            raise SanityError("ghosts are banned (no ghosts)")
        if keyword == "dream" and "time" in self.banned:
            raise SanityError("dream variables are banned (no time)")

        # SP for name length
        if len(name) == 1:
            self.sp.single_char_name()
        elif len(name) > 20:
            self.sp.long_name()

        # SP for whatever
        if keyword == "whatever":
            self.sp.whatever_declaration()

        # SP for curse
        if keyword == "curse":
            self.sp.curse_declaration()

        # Evaluate value
        value = self.evaluate(node.value) if node.value else san_void()

        # Override / re-declaration checks
        existing = self.current_env.get(name)
        if existing:
            # Swear variables can NEVER be reassigned by any keyword
            if existing.keyword == "swear":
                self._write_blame(f"Attempted to reassign swear variable '{name}'")
                raise SanityError(f"Cannot reassign swear variable '{name}'! Program crashed.",
                                  blame=name)

            if keyword == "sure" and existing.keyword == "sure":
                # Override — old goes to afterlife, fall through to create new var
                self._send_to_afterlife(name, existing.value, existing.mood, existing.scars)
                self.sp.override_sure()
                if existing.value.type != value.type:
                    existing.add_scar()
                # Fall through to create new variable below

            elif keyword == "sure" and existing.keyword != "sure":
                # Cannot override non-sure variable with sure
                raise SanityError(f"Cannot reassign '{existing.keyword}' variable '{name}' with 'sure'.")

            elif keyword == "maybe" and existing.keyword == "maybe":
                # Re-declaring a maybe variable = reassignment with doubt tracking
                existing.doubt += 1
                if existing.doubt >= 5:
                    existing.is_uncertain = True
                existing.previous_value = existing.value
                existing.value = value
                existing.history.append(value.copy())
                # Scream events
                if existing.keyword == "scream":
                    self._fire_event(name, "changes")
                return value

            else:
                raise SanityError(
                    f"Variable '{name}' already exists and cannot be re-declared with keyword '{keyword}'."
                )


        # Ghost tracking
        if keyword == "ghost":
            self.ghost_count += 1
            if self.ghost_count > 5:
                self.output.append("[SanityLang] Warning: Your codebase is haunted.")

        # Create variable
        var = Variable(
            name=name, value=value, keyword=keyword,
            decl_line=node.line,
        )

        # Record in history
        var.history.append(value.copy())

        # Define in environment
        self.current_env.define(name, var)

        # Detect emotional bonds
        new_bonds = self.current_env.detect_bonds()
        for a, b in new_bonds:
            self.sp.bond_formed()
            self._add_graph_edge(a, b)

        # Excited mood: first function call result → duplicate into list
        if isinstance(node.value, FunctionCall):
            call_name = None
            if isinstance(node.value.callee, VariableAccess):
                call_name = node.value.callee.name
            if call_name and call_name in self._first_call_results:
                self._set_mood(var, Mood.EXCITED)
                # Duplicate value into a list of two copies
                dup = SanValue([value.copy(), value.copy()], SanType.LIST)
                var.value = dup
                self._first_call_results.discard(call_name)
                return dup

        return value

    def _exec_assignment(self, node: Assignment) -> SanValue:
        name = node.name
        var = self.current_env.get(name)
        if not var:
            raise SanityError(f"Variable '{name}' is not defined")

        # Keyword checks
        if var.keyword == "sure":
            raise SanityError(f"Cannot reassign 'sure' variable '{name}'. Use override (redeclare with sure).")
        if var.keyword == "swear":
            self._write_blame(f"Attempted to reassign swear variable '{name}'")
            raise SanityError(f"Cannot reassign swear variable '{name}'! Program crashed.", blame=name)
        if var.keyword == "ghost":
            raise SanityError(f"Cannot assign to ghost variable '{name}'")

        old_value = var.value
        new_value = self.evaluate(node.value)

        # Hates enforcement: cannot hold same value as a hated variable
        hated_targets = self.relationships["hates"].get(name, set())
        for hated_name in hated_targets:
            hated_var = self.current_env.get(hated_name)
            if hated_var and hated_var.value.value == new_value.value:
                raise SanityError(
                    f"'{name}' hates '{hated_name}' — cannot hold the same value ({new_value.value})"
                )

        # Maybe — increment doubt
        if var.keyword == "maybe":
            var.doubt += 1
            if var.doubt >= 5:
                var.is_uncertain = True

        # Trust = 0 check — read-only
        if var.trust <= 0:
            return old_value  # Silently reject

        # Record history
        var.previous_value = old_value
        var.value = new_value
        var.history.append(new_value.copy())

        # Pinky propagation
        if var.pinky_source:
            source = self.current_env.get(var.pinky_source)
            if source:
                source.value = new_value.copy()

        # Fears trigger: if any variable fears this one, set their mood to AFRAID
        for fearer_name, feared_set in self.relationships["fears"].items():
            if name in feared_set:
                fearer_var = self.current_env.get(fearer_name)
                if fearer_var:
                    fearer_var.mood = Mood.AFRAID

        # Scream events
        if var.keyword == "scream":
            self._fire_event(name, "changes")

        # Excited mood: first function call result → duplicate into list
        if isinstance(node.value, FunctionCall):
            call_name = None
            if isinstance(node.value.callee, VariableAccess):
                call_name = node.value.callee.name
            if call_name and call_name in self._first_call_results:
                self._set_mood(var, Mood.EXCITED)
                dup = SanValue([new_value.copy(), new_value.copy()], SanType.LIST)
                var.value = dup
                self._first_call_results.discard(call_name)
                return dup

        return new_value

    def _exec_print(self, node: PrintStatement) -> SanValue:
        value = self.evaluate(node.expression)
        text = str(value)
        self.output.append(text)
        print(text)

        # Printing makes variables Observed
        if isinstance(node.expression, VariableAccess):
            var = self.current_env.get(node.expression.name)
            if var:
                var.observed = True
        return value

    def _exec_block(self, block: Block) -> SanValue:
        """Execute a block of statements in a new scope."""
        env = Environment(parent=self.current_env, scope_id=self._new_scope_id())
        self.sp.enter_scope()
        old_env = self.current_env
        self.current_env = env
        result = san_void()

        try:
            for stmt in block.statements:
                result = self.execute(stmt)
        finally:
            # Check for wasted scope
            if not env.used_vars and env.variables:
                self.sp.wasted_scope()
            self.current_env = old_env

        return result

    # --- Control Flow ---

    def _exec_if(self, node: IfStatement) -> SanValue:
        cond = self.evaluate(node.condition)
        should_invert = self.sp.insanity_mode and random.random() < 0.1

        if is_truthy(cond) != should_invert:
            return self._exec_block(node.body)

        for but_clause in node.but_clauses:
            bcond = self.evaluate(but_clause.condition)
            if is_truthy(bcond) != should_invert:
                return self._exec_block(but_clause.body)

        if node.actually_block:
            return self._exec_block(node.actually_block)

        return san_void()

    def _exec_unless(self, node: UnlessStatement) -> SanValue:
        cond = self.evaluate(node.condition)
        if not is_truthy(cond):
            return self._exec_block(node.body)
        return san_void()

    def _exec_suppose(self, node: SupposeStatement) -> SanValue:
        cond = self.evaluate(node.condition)
        result = self._exec_block(node.body)
        if not is_truthy(cond):
            # Make all modified variables uncertain
            for var in self.current_env.variables.values():
                var.is_uncertain = True
        return result

    def _exec_pretend(self, node: PretendStatement) -> SanValue:
        # Block runs regardless, but assignments are tagged Pretend
        env = Environment(parent=self.current_env, scope_id=self._new_scope_id())
        old_env = self.current_env
        self.current_env = env
        result = san_void()
        try:
            for stmt in node.body.statements:
                result = self.execute(stmt)
            # Mark all new variables as pretend
            for var in env.variables.values():
                var.is_pretend = True
        finally:
            self.current_env = old_env
        return san_void()  # Pretend values become Void outside

    def _exec_check(self, node: CheckStatement) -> SanValue:
        value = self.evaluate(node.value)
        type_str = value.type.value

        for case in node.cases:
            match = False
            # Type check
            if case.type_names:
                match = type_str in case.type_names
            elif case.type_name:
                match = type_str == case.type_name

            # Where condition
            if match and case.condition:
                cond_result = self.evaluate(case.condition)
                match = is_truthy(cond_result)

            # Mood check
            if match and case.mood_check:
                if isinstance(node.value, VariableAccess):
                    var = self.current_env.get(node.value.name)
                    if var:
                        match = var.mood.value == case.mood_check

            if match:
                # Is Void check costs SP
                if case.type_name == "Void" or (case.type_names and "Void" in case.type_names):
                    self.sp.void_truthiness_check()
                return self._exec_block(case.body)

        if node.otherwise:
            return self._exec_block(node.otherwise)
        return san_void()

    # --- Loops ---

    def _exec_again(self, node: AgainLoop) -> SanValue:
        result = san_void()
        while True:
            try:
                result = self._exec_block(node.body)
            except BreakSignal:
                break
        return result

    def _exec_pls(self, node: PlsLoop) -> SanValue:
        count_val = self.evaluate(node.count)
        if count_val.type != SanType.NUMBER:
            raise SanityError("pls loop count must be a Number")
        count = int(count_val.value)
        result = san_void()

        # SP < 50: counter starts at 0, otherwise 1
        start = 0 if self.sp.sp < 50 else 1

        # pls-in-ugh interaction: reduce count by outer ugh quit probability
        if self.ugh_quit_probability > 0:
            count = int(count * (1 - self.ugh_quit_probability))
            if count < 0:
                count = 0

        end = count + start

        for i in range(start, end):
            actual_i = i
            if self.sp.insanity_mode:
                actual_i += random.choice([-1, 0, 1])

            env = Environment(parent=self.current_env, scope_id=self._new_scope_id())
            if node.counter_name:
                env.define(node.counter_name, Variable(
                    name=node.counter_name,
                    value=san_number(actual_i),
                    keyword="sure",
                    decl_line=node.line,
                ))
            old_env = self.current_env
            self.current_env = env
            try:
                for stmt in node.body.statements:
                    result = self.execute(stmt)
            except BreakSignal:
                self.current_env = old_env
                break
            finally:
                self.current_env = old_env
        return result

    def _exec_ugh(self, node: UghLoop) -> SanValue:
        result = san_void()
        iteration = 0
        old_quit_prob = self.ugh_quit_probability
        while True:
            iteration += 1
            quit_chance = 0.01 * iteration
            if self.sp.insanity_mode:
                quit_chance *= 2
            # Track quit probability for nested pls loops
            self.ugh_quit_probability = min(quit_chance, 1.0)
            if random.random() < quit_chance:
                break
            cond = self.evaluate(node.condition)
            if not is_truthy(cond):
                break
            try:
                result = self._exec_block(node.body)
            except BreakSignal:
                break
        self.ugh_quit_probability = old_quit_prob
        return result

    def _exec_forever(self, node: ForeverLoop) -> SanValue:
        result = san_void()
        mercy_path = os.path.join(os.path.dirname(self.source_path), "mercy.san") if self.source_path != "<repl>" else None
        while True:
            if mercy_path and os.path.exists(mercy_path):
                break
            try:
                result = self._exec_block(node.body)
            except BreakSignal:
                break
        return result

    def _exec_hopefully(self, node: HopefullyLoop) -> SanValue:
        result = san_void()
        iteration = 0
        while True:
            cond = self.evaluate(node.condition)
            if not is_truthy(cond):
                break
            iteration += 1
            if iteration <= 100:
                self.sp.hopefully_bonus()
            else:
                self.sp.hopefully_penalty()
            try:
                result = self._exec_block(node.body)
            except BreakSignal:
                break
        return result

    def _exec_reluctantly(self, node: ReluctantlyLoop) -> SanValue:
        result = san_void()
        delay_ms = 1
        while True:
            cond = self.evaluate(node.condition)
            if not is_truthy(cond):
                break
            time.sleep(delay_ms / 1000.0)
            delay_ms *= 2
            if delay_ms > 10000:
                delay_ms = 10000  # Cap at 10 seconds
            try:
                result = self._exec_block(node.body)
            except BreakSignal:
                break
        return result

    # --- Functions ---

    def _exec_func_decl(self, node: FunctionDecl) -> SanValue:
        self.functions[node.name] = (node, self.current_env)
        # Auto-call 'must' functions
        if node.keyword == "must":
            self._call_function(node.name, [], node, self.current_env)
        return san_void()

    def _exec_return(self, node: ReturnStatement) -> SanValue:
        value = self.evaluate(node.value) if node.value else san_void()
        raise ReturnSignal(value, node.terminators)

    # --- Error Handling ---

    def _exec_try(self, node: TryCope) -> SanValue:
        try:
            return self._exec_block(node.try_block)
        except SanityError as e:
            error_blob = san_blob({
                "message": san_word(str(e)),
                "source": san_word(""),
                "blame": san_word(e.blame),
                "mood": san_word(e.mood),
            })

            if node.cope_block:
                env = Environment(parent=self.current_env, scope_id=self._new_scope_id())
                if node.cope_param:
                    env.define(node.cope_param, Variable(
                        name=node.cope_param, value=error_blob,
                        keyword="sure", decl_line=node.line,
                    ))
                    # Check if cope uses the error
                    # (simplified: we check if param appears in any statement)
                else:
                    self.sp.useless_cope()
                old_env = self.current_env
                self.current_env = env
                try:
                    return self._exec_block(node.cope_block)
                finally:
                    self.current_env = old_env

            if node.deny_block:
                self._write_blame(str(e))
                # Source variable trust -10
                if e.blame:
                    var = self.current_env.get(e.blame)
                    if var:
                        var.lose_trust(10)
                return san_void()

        return san_void()

    def _exec_blame(self, node: BlameStatement) -> SanValue:
        target = node.target
        reason = node.reason

        # If target is a variable, affect it
        var = self.current_env.get(target)
        if var:
            var.lose_trust(20)
            var.mood = Mood.AFRAID
            var.mood_set_at = self.stmt_counter

        # If target is a chapter, penalize its trust
        if target in self.chapter_trust:
            self.chapter_trust[target] = max(0, self.chapter_trust[target] - 10)

        self._write_blame(f"{target}: {reason}")
        raise SanityError(reason, blame=target)

    def _exec_oops(self, node: OopsStatement) -> SanValue:
        self.sp.oops_penalty()
        self.oops_count += 1

        if self.oops_count >= 10:
            raise SanityError(f"Too many oops! Escalated: {node.message}")
        raise SanityError(f"oops: {node.message}")

    def _exec_yolo(self, node: YoloBlock) -> SanValue:
        saved_count = 0
        env = Environment(parent=self.current_env, scope_id=self._new_scope_id())
        old_env = self.current_env
        self.current_env = env

        for stmt in node.body.statements:
            try:
                self.execute(stmt)
            except (SanityError, Exception):
                saved_count += 1
                self.sp.yolo_swallow()

        self.current_env = old_env

        if saved_count >= 10:
            for var in env.variables.values():
                var.traits.add(Trait.CURSED)

        return san_void()

    # --- Gambling ---

    def _exec_bet(self, node: BetBlock) -> SanValue:
        if "gambling" in self.banned:
            raise SanityError("gambling is banned (no gambling)")

        cond = self.evaluate(node.condition)
        reward_val = self.evaluate(node.reward)
        risk_val = self.evaluate(node.risk)
        reward = int(reward_val.value) if reward_val.type == SanType.NUMBER else 0
        risk = int(risk_val.value) if risk_val.type == SanType.NUMBER else 0

        # Collect variables involved in condition for trait effects
        cond_vars = self._collect_variable_names(node.condition)

        won = is_truthy(cond)
        if self.sp.insanity_mode:
            won = not won  # Inverted in insanity mode

        if won:
            self.sp.bet_win(reward)
            # Winners gain Lucky trait
            for vname in cond_vars:
                var = self.current_env.get(vname)
                if var:
                    var.traits.add(Trait.LUCKY)
            return self._exec_block(node.body)
        else:
            self.sp.bet_lose(risk)
            # Track losses per variable; 3+ losses = Unlucky
            for vname in cond_vars:
                self.bet_losses[vname] = self.bet_losses.get(vname, 0) + 1
                if self.bet_losses[vname] >= 3:
                    var = self.current_env.get(vname)
                    if var:
                        var.traits.add(Trait.UNLUCKY)
            return san_void()

    def _exec_jackpot(self, node: JackpotBlock) -> SanValue:
        if "gambling" in self.banned:
            raise SanityError("gambling is banned (no gambling)")

        key = node.line
        count = self.jackpot_counts.get(key, 0) + 1
        self.jackpot_counts[key] = count

        cond = self.evaluate(node.condition)
        if is_truthy(cond) and count % 100 == 0:
            self.sp.jackpot_win()
            return self._exec_block(node.body)
        return san_void()

    # --- Time ---

    def _exec_foreshadow(self, node: ForeshadowStatement) -> SanValue:
        if "time" in self.banned:
            raise SanityError("time features are banned (no time)")
        self.foreshadowed[node.event_name] = False
        return san_void()

    def _exec_fulfill(self, node: FulfillStatement) -> SanValue:
        if "time" in self.banned:
            raise SanityError("time features are banned (no time)")
        self.foreshadowed[node.event_name] = True
        self._fire_event(node.event_name, node.event_name)
        return san_void()

    def _exec_rewind(self, node: RewindStatement) -> SanValue:
        if "time" in self.banned:
            raise SanityError("time features are banned (no time)")
        count_val = self.evaluate(node.count)
        count = int(count_val.value) if count_val.type == SanType.NUMBER else 0
        count = min(count, len(self.stmt_history))

        if count > 0:
            stmts_to_replay = self.stmt_history[-count:]
            for stmt in stmts_to_replay:
                self.execute(stmt)
        return san_void()

    # --- Chapters ---

    def _exec_recall(self, node: RecallStatement) -> SanValue:
        if node.module not in self.chapters:
            raise SanityError(f"Chapter '{node.module}' not found")

        chapter = self.chapters[node.module]
        mod_name = node.module
        trust = self.chapter_trust.get(mod_name, 70)

        # Trust < 10: require forceful terminator (!)
        if trust < 10:
            if not hasattr(node, 'terminators') or "!" not in (node.terminators or []):
                raise SanityError(
                    f"Chapter '{mod_name}' has critically low trust ({trust}). "
                    f"Use forceful terminator (!) to proceed: recall {mod_name}!"
                )

        # Trust < 50: emit warning
        if trust < 50:
            self.output.append(f"[compiler] Warning: Chapter '{mod_name}' has low trust ({trust})")

        # Alliance / Rivalry SP effects
        # Determine current chapter context (simplified: use global scope)
        for ch_name, allies in self.chapter_allies.items():
            if mod_name in allies:
                self.sp.import_from_ally()
        for ch_name, rivals in self.chapter_rivals.items():
            if mod_name in rivals:
                self.output.append(
                    f"[compiler] Warning: Importing from rival '{mod_name}' — "
                    f"errors will blame the importer"
                )

        # Execute chapter body in a new scope
        env = Environment(parent=self.global_env, scope_id=self._new_scope_id())
        old_env = self.current_env
        self.current_env = env

        # Track functions registered before chapter execution
        funcs_before = set(self.functions.keys())

        # Trust < 30: auto-wrap in try/cope
        if trust < 30:
            try:
                for stmt in chapter.body:
                    self.execute(stmt)
            except SanityError as e:
                self.current_env = old_env
                self.chapter_trust[mod_name] = max(0, trust - 5)
                self.output.append(
                    f"[compiler] Auto-caught error from low-trust chapter '{mod_name}': {e}"
                )
                return san_void()
        else:
            try:
                for stmt in chapter.body:
                    self.execute(stmt)
            except SanityError:
                self.current_env = old_env
                self.chapter_trust[mod_name] = max(0, trust - 5)
                raise

        self.current_env = old_env

        # Collect functions registered during chapter execution
        funcs_after = set(self.functions.keys())
        chapter_funcs = funcs_after - funcs_before

        # Import into current scope
        if node.specific:
            # Import specific item
            var = env.get(node.specific)
            if var:
                # Secret filtering: skip whisper-keyword vars
                if var.keyword == "whisper":
                    raise SanityError(
                        f"Cannot recall secret item '{node.specific}' from Chapter '{mod_name}'"
                    )
                self.current_env.define(node.specific, var)
            # Check if it's a function
            func_key = node.specific
            if func_key in chapter_funcs:
                func_decl, func_env = self.functions[func_key]
                if getattr(func_decl, 'is_secret', False):
                    del self.functions[func_key]
                    raise SanityError(
                        f"Cannot recall secret function '{node.specific}' from Chapter '{mod_name}'"
                    )
                # Keep in self.functions — already registered
        else:
            # Import all non-secret items
            for name, var in env.variables.items():
                if var.keyword == "whisper":
                    continue  # Skip secrets
                self.current_env.define(name, var)

            # Remove secret functions from registration
            for func_name in chapter_funcs:
                if func_name in self.functions:
                    func_decl, func_env = self.functions[func_name]
                    if getattr(func_decl, 'is_secret', False):
                        del self.functions[func_name]

        # Curse propagation: curse-keyword vars modify same-type vars in current scope
        for name, var in env.variables.items():
            if var.keyword == "curse" and var.value.type == SanType.NUMBER:
                # Apply curse modifier to all same-type vars in current scope
                for target_name, target_var in self.current_env.all_variables().items():
                    if target_var.value.type == SanType.NUMBER and target_name != name:
                        modifier = var.value.value
                        target_var.value = san_number(target_var.value.value + modifier)
                        self._gain_trait(target_var, Trait.CURSED)

        # Trust growth: +2 for successful import
        self.chapter_trust[mod_name] = min(100, self.chapter_trust.get(mod_name, 70) + 2)

        return san_void()

    # --- Personalities ---

    def _exec_personality_def(self, node: PersonalityDef) -> SanValue:
        self.personalities[node.name] = node
        # Register methods
        for stmt in node.body:
            if isinstance(stmt, FunctionDecl):
                self.functions[f"{node.name}.{stmt.name}"] = (stmt, self.current_env)
        return san_void()

    # --- Events ---

    def _exec_when(self, node: WhenBlock) -> SanValue:
        key = f"{node.target}:{node.event_type}"
        self.listeners.setdefault(key, []).append((node.body, self.current_env))
        return san_void()

    def _fire_event(self, target: str, event_type: str):
        key = f"{target}:{event_type}"
        for body, env in self.listeners.get(key, []):
            old_env = self.current_env
            self.current_env = env
            try:
                self._exec_block(body)
            finally:
                self.current_env = old_env

        # Also fire with wildcard
        key2 = f"any:{event_type}"
        for body, env in self.listeners.get(key2, []):
            old_env = self.current_env
            self.current_env = env
            try:
                self._exec_block(body)
            finally:
                self.current_env = old_env

    # --- Debugging ---

    def _exec_wtf(self, node: WtfStatement) -> SanValue:
        var = self.current_env.get(node.target)
        if not var:
            msg = f"[wtf] Variable '{node.target}' not found"
        else:
            var.observed = True
            msg = (
                f"[wtf] {var.name}:\n"
                f"  type:   {var.value.type.value}\n"
                f"  value:  {var.value}\n"
                f"  mood:   {var.mood.value}\n"
                f"  trust:  {var.trust}\n"
                f"  age:    {var.age}\n"
                f"  scars:  {var.scars}\n"
                f"  doubt:  {var.doubt}\n"
                f"  traits: {', '.join(t.value for t in var.traits) or 'none'}\n"
                f"  bonds:  {', '.join(var.bonds) or 'none'}\n"
                f"  edges:  {', '.join(self.graph_edges.get(var.name, set())) or 'none'}"
            )
        self.output.append(msg)
        print(msg)
        return san_void()

    def _exec_huh(self, node: HuhStatement) -> SanValue:
        var = self.current_env.get(node.target)
        if not var:
            msg = f"[huh] Variable '{node.target}' not found"
        else:
            var.observed = True
            msg = f"[huh] {var.name}: {var.value.type.value} = {var.value}"
        self.output.append(msg)
        print(msg)
        return san_void()

    def _exec_cry(self, node: CryStatement) -> SanValue:
        msg = f"[CRASH] {node.message}"
        self.output.append(msg)
        print(msg)
        raise SanityError(node.message)

    def _exec_therapy(self, node: TherapyStatement) -> SanValue:
        all_vars = self.current_env.all_variables()
        ghost_count = sum(1 for v in all_vars.values() if v.keyword == "ghost")
        bond_chains = []
        for v in all_vars.values():
            bond_chains.append(len(v.bonds))

        msg = (
            f"[therapy] Program State:\n"
            f"  SP:            {self.sp.sp}\n"
            f"  Variables:     {len(all_vars)}\n"
            f"  Ghosts:        {ghost_count}\n"
            f"  Statements:    {self.stmt_counter}\n"
            f"  Functions:     {len(self.functions)}\n"
            f"  Graph edges:   {sum(len(e) for e in self.graph_edges.values()) // 2}\n"
            f"  Longest chain: {max(bond_chains) if bond_chains else 0}\n"
            f"  Insanity Mode: {'YES' if self.sp.insanity_mode else 'no'}"
        )
        self.output.append(msg)
        print(msg)

        # Write to .san.therapy file
        if self.therapy_path:
            import datetime
            with open(self.therapy_path, "a") as f:
                f.write(f"\n--- Session: {datetime.datetime.now().isoformat()} ---\n")
                f.write(msg + "\n")

        return san_void()

    def _exec_oracle(self, node: OracleStatement) -> SanValue:
        self.sp.oracle_cost()
        # Oracle gives a best-effort answer based on static analysis
        answers = [
            "Probably.", "Unlikely.", "The stars say yes.",
            "Ask again later.", "Without a doubt... maybe.",
            "Signs point to Void.", "Your variables are concerned about you.",
        ]
        answer = random.choice(answers)
        msg = f"[oracle] Q: {node.question}\n         A: {answer}"
        self.output.append(msg)
        print(msg)
        return san_word(answer)

    # --- Self-Modification ---

    def _exec_grammar_alias(self, node: GrammarAlias) -> SanValue:
        self.grammar_aliases[node.new_keyword] = node.old_keyword
        return san_void()

    def _exec_grammar_remove(self, node: GrammarRemove) -> SanValue:
        self.grammar_removed.add(node.keyword)
        return san_void()

    def _exec_pray(self, node: PrayStatement) -> SanValue:
        prayer = node.prayer

        if prayer == "speed" and "safety" in self.prayers:
            self.sp.sp -= 5  # Indecisive
            self.prayers.discard("safety")
            return san_void()
        if prayer == "safety" and "speed" in self.prayers:
            self.sp.sp -= 5
            self.prayers.discard("speed")
            return san_void()

        self.prayers.add(prayer)

        if prayer == "mercy":
            self.sp.pray_mercy = True
        elif prayer == "chaos":
            self.sp.pray_for_chaos()
        elif prayer == "nothing":
            self.sp.pray_for_nothing()
        return san_void()

    def _exec_no(self, node: NoStatement) -> SanValue:
        feature = node.feature
        self.banned.add(feature)

        # Fun message
        if "feelings" in self.banned and "gambling" in self.banned:
            self.output.append("[SanityLang] You must be fun at parties. +5 SP.")
            self.sp.no_fun_at_parties()

        return san_void()

    def _exec_exorcise(self, node: ExorciseStatement) -> SanValue:
        curse_name = node.curse_name
        found = False
        if curse_name and curse_name in self.active_curses:
            self.active_curses.discard(curse_name)
            found = True
        if found:
            self.sp.exorcise_cost()  # -25 SP to remove
        else:
            self.sp.sp += 5  # +5 SP for being proactive
        return san_void()

    def _exec_i_am_okay(self, node: IAmOkayStatement) -> SanValue:
        # Check if any variable is Angry
        for var in self.current_env.all_variables().values():
            if var.mood == Mood.ANGRY:
                msg = f"[SanityLang] No you're not. ({var.name} is still Angry)"
                self.output.append(msg)
                print(msg)
                return san_void()
        self.sp.i_am_okay()
        return san_void()

    def _exec_forgets_everyone(self, node: ForgetsEveryone) -> SanValue:
        var = self.current_env.get(node.variable)
        if var:
            for bonded in var.bonds[:]:
                other = self.current_env.get(bonded)
                if other and node.variable in other.bonds:
                    other.bonds.remove(node.variable)
                self._remove_graph_edge(node.variable, bonded)
            var.bonds.clear()
        return san_void()

    def _exec_delete(self, node: DeleteStatement) -> SanValue:
        var = self.current_env.get(node.variable)
        if var:
            self._send_to_afterlife(var.name, var.value, var.mood, var.scars)

            # Handle pinky bonds — delete both
            if var.pinky_source:
                source = self.current_env.get(var.pinky_source)
                if source:
                    self._send_to_afterlife(source.name, source.value, source.mood, source.scars)
                    self.sp.pinky_break()

            # Handle emotional bonds — grief
            for bonded_name in var.bonds:
                bonded = self.current_env.get(bonded_name)
                if bonded:
                    bonded.grief_remaining = 5
                    self.sp.bond_broken()

            # Haunts: when a deleted variable haunts another, set the target's mood to AFRAID
            haunts_targets = self.relationships["haunts"].get(node.variable, set())
            for target_name in haunts_targets:
                target_var = self.current_env.get(target_name)
                if target_var:
                    target_var.mood = Mood.AFRAID
                    target_var.grief_remaining = 100  # Afraid for 100 statements

            # Clean up relationships for deleted variable
            for rel_type in self.relationships:
                self.relationships[rel_type].pop(node.variable, None)
                for key, targets in self.relationships[rel_type].items():
                    targets.discard(node.variable)

            if var.keyword == "ghost":
                self.ghost_count -= 1
        return san_void()

    # --- Terminators ---

    def _apply_terminators(self, value: SanValue, terminators: list[str]) -> SanValue:
        """Apply stacked terminators to a result value, left to right."""
        for term in terminators:
            if term == ".":
                pass  # Normal
            elif term == "..":
                # Cache permanently — simplified by just returning the value
                pass
            elif term == "~":
                if "uncertainty" not in self.banned:
                    # Mark all variables involved in the most recent statement as uncertain
                    for var in self.current_env.all_variables().values():
                        if var.last_accessed == self.stmt_counter:
                            var.is_uncertain = True
            elif term == "!":
                # Forceful — strip traits from all recently-accessed variables
                for var in self.current_env.all_variables().values():
                    if var.last_accessed == self.stmt_counter:
                        var.traits.clear()
            elif term == "?":
                # Debug print + mark Observed
                msg = f"[?] {value}"
                self.output.append(msg)
                print(msg)
                # Mark recently-accessed variables as Observed
                for var in self.current_env.all_variables().values():
                    if var.last_accessed == self.stmt_counter:
                        var.observed = True
                        # Collapse Dunno on observation
                        if var.value.type == SanType.DUNNO:
                            import random as _rng
                            var.value = san_yep() if _rng.random() < 0.5 else san_nope()
        return value

    # --- Insanity Mode ---

    def _apply_insanity_effects(self):
        self._insanity_swap_counter += 1
        if self._insanity_swap_counter >= 20:
            self._insanity_swap_counter = 0
            all_vars = self.current_env.all_variables()
            names = list(all_vars.keys())
            if len(names) >= 2:
                a, b = random.sample(names, 2)
                va = self.current_env.get(a)
                vb = self.current_env.get(b)
                if va and vb and a in self.graph_edges.get(b, set()):
                    va.value, vb.value = vb.value, va.value

    # --- Dream persistence ---

    def _load_dreams(self):
        if not self.dream_path or not os.path.exists(self.dream_path):
            return
        try:
            with open(self.dream_path, "r") as f:
                data = json.load(f)
            for name, info in data.items():
                var = self.current_env.get(name)
                if var and var.keyword == "dream":
                    val_type = info.get("type", "Void")
                    val = info.get("value")
                    if val_type == "Number":
                        var.value = san_number(val)
                    elif val_type == "Word":
                        var.value = san_word(val)
                    elif val_type == "Yep":
                        var.value = san_yep()
                    elif val_type == "Nope":
                        var.value = san_nope()
                    else:
                        var.value = san_void()
                    self.sp.dream_fulfilled()
        except (json.JSONDecodeError, KeyError):
            pass

    def _save_dreams(self):
        if not self.dream_path:
            return
        dreams = {}
        for name, var in self.current_env.all_variables().items():
            if var.keyword == "dream":
                dreams[name] = {
                    "type": var.value.type.value,
                    "value": var.value.value,
                }
        if dreams:
            with open(self.dream_path, "w") as f:
                json.dump(dreams, f, indent=2, default=str)

    # --- Blame file ---

    def _write_blame(self, message: str):
        if not self.blame_path:
            return
        import datetime
        with open(self.blame_path, "a") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] {message}\n")

    # Install all methods
    methods = {
        '_exec_var_decl': _exec_var_decl,
        '_exec_assignment': _exec_assignment,
        '_exec_print': _exec_print,
        '_exec_block': _exec_block,
        '_exec_if': _exec_if,
        '_exec_unless': _exec_unless,
        '_exec_suppose': _exec_suppose,
        '_exec_pretend': _exec_pretend,
        '_exec_check': _exec_check,
        '_exec_again': _exec_again,
        '_exec_pls': _exec_pls,
        '_exec_ugh': _exec_ugh,
        '_exec_forever': _exec_forever,
        '_exec_hopefully': _exec_hopefully,
        '_exec_reluctantly': _exec_reluctantly,
        '_exec_func_decl': _exec_func_decl,
        '_exec_return': _exec_return,
        '_exec_try': _exec_try,
        '_exec_blame': _exec_blame,
        '_exec_oops': _exec_oops,
        '_exec_yolo': _exec_yolo,
        '_exec_bet': _exec_bet,
        '_exec_jackpot': _exec_jackpot,
        '_exec_foreshadow': _exec_foreshadow,
        '_exec_fulfill': _exec_fulfill,
        '_exec_rewind': _exec_rewind,
        '_exec_recall': _exec_recall,
        '_exec_personality_def': _exec_personality_def,
        '_exec_when': _exec_when,
        '_fire_event': _fire_event,
        '_exec_wtf': _exec_wtf,
        '_exec_huh': _exec_huh,
        '_exec_cry': _exec_cry,
        '_exec_therapy': _exec_therapy,
        '_exec_oracle': _exec_oracle,
        '_exec_grammar_alias': _exec_grammar_alias,
        '_exec_grammar_remove': _exec_grammar_remove,
        '_exec_pray': _exec_pray,
        '_exec_no': _exec_no,
        '_exec_exorcise': _exec_exorcise,
        '_exec_i_am_okay': _exec_i_am_okay,
        '_exec_forgets_everyone': _exec_forgets_everyone,
        '_exec_delete': _exec_delete,
        '_apply_terminators': _apply_terminators,
        '_apply_insanity_effects': _apply_insanity_effects,
        '_load_dreams': _load_dreams,
        '_save_dreams': _save_dreams,
        '_write_blame': _write_blame,
    }
    for name, method in methods.items():
        setattr(Interpreter, name, method)


# Auto-install on import
_install_statement_executors()
