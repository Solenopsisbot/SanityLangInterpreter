"""Variable and Environment system for (In)SanityLang."""
from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Optional
import random

from .types import SanValue, SanType, san_void


class Mood(Enum):
    NEUTRAL = "Neutral"
    HAPPY = "Happy"
    SAD = "Sad"
    ANGRY = "Angry"
    AFRAID = "Afraid"
    EXCITED = "Excited"
    JEALOUS = "Jealous"


class Trait(Enum):
    ELDER = "Elder"
    RESILIENT = "Resilient"
    TIRED = "Tired"
    LUCKY = "Lucky"
    UNLUCKY = "Unlucky"
    PARANOID = "Paranoid"
    POPULAR = "Popular"
    LONELY = "Lonely"
    CURSED = "Cursed"
    BLESSED = "Blessed"
    VOLATILE = "Volatile"


@dataclass
class Variable:
    """A SanityLang variable with full state tracking."""
    name: str
    value: SanValue
    keyword: str  # sure, maybe, whatever, swear, pinky, ghost, dream, whisper, curse, scream
    decl_line: int = 0

    # Hidden state (§3)
    trust: int = 100
    doubt: int = 0
    age: int = 0
    scars: int = 0
    mood: Mood = Mood.NEUTRAL
    mood_set_at: int = 0  # Statement counter when mood was set

    # Traits
    traits: set[Trait] = field(default_factory=set)

    # Observation
    observed: bool = False
    last_accessed: int = 0  # Statement counter

    # Emotional Bonds
    bonds: list[str] = field(default_factory=list)  # Names of bonded variables

    # Pinky source
    pinky_source: Optional[str] = None

    # Whatever mutation counter
    whatever_counter: int = 0

    # Access counter (for mood triggers)
    access_count: int = 0

    # Error counter (for mood triggers)
    error_count: int = 0

    # Bet participation
    bet_losses: int = 0

    # Value history (for remember)
    history: list[SanValue] = field(default_factory=list)

    # Grief state
    grief_remaining: int = 0

    # Pretend flag
    is_pretend: bool = False

    # Uncertainty wrapper
    is_uncertain: bool = False
    previous_value: Optional[SanValue] = None

    def add_scar(self):
        self.scars += 1
        if self.scars >= 3 and Trait.RESILIENT not in self.traits:
            self.traits.add(Trait.RESILIENT)

    def lose_trust(self, amount: int = 10):
        self.trust = max(0, self.trust - amount)
        if self.trust < 50 and self.mood != Mood.ANGRY:
            self.mood = Mood.ANGRY
        if self.trust < 30:
            self.traits.add(Trait.PARANOID)

    def record_access(self, stmt_counter: int):
        self.access_count += 1
        self.last_accessed = stmt_counter
        self.age = stmt_counter
        if self.access_count == 7:
            self.mood = Mood.HAPPY
            self.mood_set_at = stmt_counter
        if self.access_count >= 200 and Trait.TIRED not in self.traits:
            self.traits.add(Trait.TIRED)
        if self.age > 500 and Trait.ELDER not in self.traits:
            self.traits.add(Trait.ELDER)

    def check_mood_decay(self, stmt_counter: int):
        if self.mood == Mood.NEUTRAL:
            return
        if self.mood == Mood.ANGRY:
            if self.trust >= 50:
                elapsed = stmt_counter - self.mood_set_at
                if elapsed >= 200:
                    self.mood = Mood.NEUTRAL
        else:
            elapsed = stmt_counter - self.mood_set_at
            if elapsed >= 200:
                self.mood = Mood.NEUTRAL

    def check_sad_from_neglect(self, stmt_counter: int):
        if stmt_counter - self.last_accessed >= 100 and self.mood == Mood.NEUTRAL:
            self.mood = Mood.SAD
            self.mood_set_at = stmt_counter

    def apply_mood_to_number(self, result: float | int) -> float | int:
        if Trait.ELDER in self.traits:
            return result  # Immune to mood
        if self.mood == Mood.HAPPY:
            return result + 1
        if self.mood == Mood.SAD:
            return result - 1
        if Trait.TIRED in self.traits:
            return result - 1
        return result

    def apply_mood_to_word(self, result: str) -> str:
        if Trait.ELDER in self.traits:
            return result
        if self.mood == Mood.HAPPY:
            return result + "!"
        if self.mood == Mood.SAD and len(result) > 0:
            return result[:-1]
        if Trait.TIRED in self.traits and len(result) > 0:
            return result[:-1]
        return result

    def has_trait(self, trait: Trait) -> bool:
        return trait in self.traits

    def check_whatever_mutation(self, stmt_counter: int):
        """Whatever variables mutate every 50 statements."""
        if self.keyword != "whatever":
            return
        if Trait.ELDER in self.traits:
            return  # Immune
        self.whatever_counter += 1
        if self.whatever_counter >= 50:
            self.whatever_counter = 0
            if self.value.type == SanType.NUMBER:
                shift = self.value.value * 0.1 * random.choice([-1, 1])
                self.value = SanValue(self.value.value + shift, SanType.NUMBER)
            elif self.value.type == SanType.WORD and len(self.value.value) > 0:
                s = list(self.value.value)
                i = random.randint(0, len(s) - 1)
                s[i] = chr(random.randint(97, 122))
                self.value = SanValue("".join(s), SanType.WORD)


class Environment:
    """Scoped variable storage."""

    def __init__(self, parent: Optional[Environment] = None, scope_id: int = 0):
        self.parent = parent
        self.scope_id = scope_id
        self.variables: dict[str, Variable] = {}
        self.used_vars: set[str] = set()  # Track which vars were accessed
        self.decl_order: list[tuple[str, int]] = []  # (name, line) for bond detection

    def define(self, name: str, variable: Variable):
        self.variables[name] = variable
        self.decl_order.append((name, variable.decl_line))

    def get(self, name: str) -> Optional[Variable]:
        if name in self.variables:
            self.used_vars.add(name)
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def set_value(self, name: str, value: SanValue) -> bool:
        if name in self.variables:
            self.variables[name].value = value
            return True
        if self.parent:
            return self.parent.set_value(name, value)
        return False

    def has(self, name: str) -> bool:
        if name in self.variables:
            return True
        if self.parent:
            return self.parent.has(name)
        return False

    def has_local(self, name: str) -> bool:
        return name in self.variables

    def all_variables(self) -> dict[str, Variable]:
        result = {}
        if self.parent:
            result.update(self.parent.all_variables())
        result.update(self.variables)
        return result

    def detect_bonds(self) -> list[tuple[str, str]]:
        """Detect Emotional Bonds: variables within 3 lines of each other, same type."""
        bonds = []
        for i, (name_a, line_a) in enumerate(self.decl_order):
            for j, (name_b, line_b) in enumerate(self.decl_order):
                if i >= j:
                    continue
                if abs(line_a - line_b) <= 3:
                    var_a = self.variables.get(name_a)
                    var_b = self.variables.get(name_b)
                    if var_a and var_b and var_a.value.type == var_b.value.type:
                        if name_b not in var_a.bonds:
                            var_a.bonds.append(name_b)
                            var_b.bonds.append(name_a)
                            bonds.append((name_a, name_b))
        return bonds
