"""Sanity Points tracking for (In)SanityLang."""
from __future__ import annotations


class SanityTracker:
    """Tracks and manages Sanity Points (SP) for a program execution."""

    def __init__(self, initial: int = 100, strict: bool = False,
                 lenient: bool = False, pray_mercy: bool = False,
                 audit: bool = False):
        self._sp = initial
        self.strict = strict       # --strict: double implicit costs
        self.lenient = lenient     # --lenient: cannot go below 10
        self.pray_mercy = pray_mercy  # --pray or "pray for mercy": halve penalties
        self.audit = audit         # --audit: track all SP changes
        self.is_runtime = False    # Some costs double at runtime
        self._listeners: list = []  # Event listeners for SP threshold crossing
        self._last_threshold = self._sp // 10 * 10
        # Audit log: [(reason, delta, new_sp)]
        self._audit_log: list[tuple[str, int, int]] = []
        self._audit_context: str = ""  # Set before SP-modifying calls

    @property
    def sp(self) -> int:
        return self._sp

    @sp.setter
    def sp(self, value: int):
        old = self._sp
        self._sp = value
        if self.lenient and self._sp < 10:
            self._sp = 10
        if self.audit and self._sp != old:
            delta = self._sp - old
            reason = self._audit_context or "direct SP change"
            self._audit_log.append((reason, delta, self._sp))
            self._audit_context = ""
        self._check_thresholds(old)

    def _modifier(self, amount: int) -> int:
        """Apply global modifiers to an SP change amount."""
        if amount < 0:  # It's a penalty
            if self.strict:
                amount *= 2
            if self.pray_mercy:
                amount //= 2
        return amount

    def _check_thresholds(self, old_sp: int):
        """Check if we crossed a 10-point threshold."""
        old_t = old_sp // 10 * 10
        new_t = self._sp // 10 * 10
        if old_t != new_t:
            for listener in self._listeners:
                listener(old_sp, self._sp)
            self._last_threshold = new_t

    def add_listener(self, fn):
        self._listeners.append(fn)

    @property
    def insanity_mode(self) -> bool:
        return self._sp <= 0

    def get_auto_terminator(self) -> str:
        """Get the auto-assigned terminator based on current SP (§1)."""
        if self._sp > 80:
            return "."
        elif self._sp >= 50:
            return "?"
        elif self._sp >= 20:
            return "~"
        else:
            return "!"

    # ============================================
    # SP Change Methods — one per action from §2
    # ============================================

    def _audit(self, reason: str):
        """Set audit context for the next SP change."""
        self._audit_context = reason

    def single_char_name(self):
        """Declaring a variable with a single-character name: -5 SP."""
        self._audit("single-char variable name")
        self.sp += self._modifier(-5)

    def long_name(self):
        """Declaring a variable with name > 20 chars: -2 SP (verbosity tax)."""
        self._audit("verbose variable name (>20 chars)")
        self.sp += self._modifier(-2)

    def override_sure(self):
        """Reassigning a sure variable via Override: -10 SP."""
        self._audit("overriding 'sure' variable")
        self.sp += self._modifier(-10)

    def whatever_declaration(self):
        """Using whatever declaration: -3 SP (doubled at runtime)."""
        cost = -6 if self.is_runtime else -3
        self._audit("'whatever' declaration")
        self.sp += self._modifier(cost)

    def first_function_call(self):
        """Calling a function for the first time: +1 SP."""
        self._audit("first function call")
        self.sp += 1

    def repetition_penalty(self):
        """Calling a function at 10+ calls: -1 SP."""
        self._audit("function repetition (10+ calls)")
        self.sp += self._modifier(-1)

    def useless_cope(self):
        """Cope block that doesn't use the error: -5 SP."""
        self._audit("useless cope block")
        self.sp += self._modifier(-5)

    def pinky_break(self):
        """A pinky bond breaking: -15 SP."""
        self._audit("pinky bond broken")
        self.sp += self._modifier(-15)

    def seance_use(self):
        """Using séance: -5 SP."""
        self._audit("séance invocation")
        self.sp += self._modifier(-5)

    def seance_ghost(self):
        """Séancing a ghost variable: -8 SP."""
        self._audit("séance on ghost variable")
        self.sp += self._modifier(-8)

    def trait_conflict(self):
        """A Trait conflict occurring: -3 SP."""
        self._audit("trait conflict")
        self.sp += self._modifier(-3)

    def bet_win(self, reward: int):
        """Winning a bet: +reward SP."""
        self._audit(f"bet won (+{reward})")
        self.sp += reward

    def bet_lose(self, risk: int):
        """Losing a bet: -risk SP."""
        self._audit(f"bet lost (-{risk})")
        self.sp += self._modifier(-risk)

    def trust_zero(self):
        """Variable trust reaching 0: -8 SP (doubled at runtime)."""
        cost = -16 if self.is_runtime else -8
        self._audit("variable trust reached 0")
        self.sp += self._modifier(cost)

    def skip_arc(self):
        """Using skip on a narrative arc: -10 SP."""
        self._audit("skipped narrative arc")
        self.sp += self._modifier(-10)

    def enter_scope(self):
        """Entering a new scope: +1 SP."""
        self._audit("entered scope")
        self.sp += 1

    def wasted_scope(self):
        """Leaving scope without using variables: -4 SP."""
        self._audit("wasted scope (no vars used)")
        self.sp += self._modifier(-4)

    def dream_fulfilled(self):
        """Dream variable fulfilled from previous run: +5 SP."""
        self._audit("dream variable fulfilled")
        self.sp += 5

    def curse_declaration(self):
        """Declaring a curse: -20 SP (doubled at runtime)."""
        cost = -40 if self.is_runtime else -20
        self._audit("curse declaration")
        self.sp += self._modifier(cost)

    def bond_formed(self):
        """Emotional Bond forming: +2 SP."""
        self._audit("emotional bond formed")
        self.sp += 2

    def bond_broken(self):
        """Emotional Bond breaking: -7 SP."""
        self._audit("emotional bond broken")
        self.sp += self._modifier(-7)

    def void_truthiness_check(self):
        """Checking Void for truthiness: -1 SP."""
        self._audit("void truthiness check")
        self.sp += self._modifier(-1)

    def ambiguous_precedence(self):
        """Ambiguous whitespace precedence: -2 SP."""
        self._audit("ambiguous whitespace precedence")
        self.sp += self._modifier(-2)

    def oops_penalty(self):
        """oops warning: -2 SP."""
        self._audit("oops warning")
        self.sp += self._modifier(-2)

    def yolo_swallow(self):
        """Yolo swallowing an error: -5 SP."""
        self._audit("yolo error swallow")
        self.sp += self._modifier(-5)

    def oracle_cost(self):
        """Oracle query: -3 SP."""
        self._audit("oracle query")
        self.sp += self._modifier(-3)

    def exorcise_cost(self):
        """Exorcising a curse: -25 SP."""
        self._audit("exorcise curse")
        self.sp += self._modifier(-25)

    def proactive_exorcise(self):
        """Exorcising a curse that doesn't exist: +5 SP."""
        self._audit("proactive exorcise (no curse)")
        self.sp += 5

    def ghost_tax(self, ghost_count: int):
        """Ghost haunting tax: -1 per ghost per 100 statements."""
        self._audit(f"ghost tax ({ghost_count} ghosts)")
        self.sp += self._modifier(-ghost_count)

    def should_not_called(self):
        """'should' function never called: -5 SP."""
        self._audit("'should' function never called")
        self.sp += self._modifier(-5)

    def unfulfilled_foreshadow(self):
        """Unfulfilled foreshadow at end: -5 SP."""
        self._audit("unfulfilled foreshadow")
        self.sp += self._modifier(-5)

    def i_am_okay(self):
        """Reset SP to 50."""
        self._audit("i am okay (SP reset)")
        self._sp = 50

    def hopefully_bonus(self):
        """Hopefully loop iteration: +1 SP."""
        self._audit("hopefully loop iteration")
        self.sp += 1

    def hopefully_penalty(self):
        """Hopefully loop past 100 iterations: -2 SP."""
        self._audit("hopefully loop past 100")
        self.sp += self._modifier(-2)

    def reset(self, value: int = 100):
        """Reset SP to a specific value."""
        self._audit(f"SP reset to {value}")
        self._sp = value

    def pray_for_chaos(self):
        """Enter insanity mode voluntarily."""
        self._audit("pray for chaos (insanity mode)")
        self._sp = 0

    def pray_for_nothing(self):
        """+1 SP for the gesture."""
        self._audit("pray for nothing")
        self.sp += 1

    def no_fun_at_parties(self):
        """'no feelings' + 'no gambling': +5 SP."""
        self._audit("no fun at parties bonus")
        self.sp += 5

    def jackpot_win(self):
        """Jackpot triggered: +50 SP."""
        self._audit("JACKPOT!")
        self.sp += 50

    def fresh_dream_start(self):
        """Dream file deleted, fresh start: +5 SP."""
        self._audit("fresh dream start")
        self.sp += 5

    def import_from_ally(self):
        """Import from an ally chapter: +3 SP."""
        self._audit("import from ally chapter")
        self.sp += 3

    def blessed_bonus(self):
        """Blessed variable per 100 statements: +1 SP."""
        self._audit("blessed variable bonus")
        self.sp += 1

    def chapter_trust_seance(self):
        """Séancing a secret from another chapter: -10 SP."""
        self._audit("séance on chapter secret")
        self.sp += self._modifier(-10)

    # ============================================
    # Audit Report
    # ============================================

    def generate_audit_report(self) -> str:
        """Generate a formatted audit report of all SP changes."""
        if not self._audit_log:
            return "[Audit] No SP changes recorded."

        lines = ["", "═" * 60, "  SP AUDIT REPORT", "═" * 60]

        gains = 0
        losses = 0
        for reason, delta, new_sp in self._audit_log:
            sign = "+" if delta > 0 else ""
            marker = "▲" if delta > 0 else "▼"
            lines.append(f"  {marker} {sign}{delta:>4}  → SP {new_sp:>4}  │ {reason}")
            if delta > 0:
                gains += delta
            else:
                losses += abs(delta)

        lines.append("─" * 60)
        lines.append(f"  Total gains:  +{gains}")
        lines.append(f"  Total losses: -{losses}")
        lines.append(f"  Net change:   {gains - losses:+d}")
        lines.append(f"  Final SP:     {self._sp}")
        lines.append(f"  Events:       {len(self._audit_log)}")
        if self.insanity_mode:
            lines.append("  ⚠  INSANITY MODE ACTIVE")
        lines.append("═" * 60)
        return "\n".join(lines)

