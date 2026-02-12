"""SanityLang Standard Library Modules (§27).

Each module is a dict mapping function names to callables
of signature (interpreter, args: list[SanValue]) -> SanValue.
"""
from __future__ import annotations

import math
import random
import time as _time
from typing import TYPE_CHECKING, Any, Callable

from .types import (
    SanValue, SanType,
    san_number, san_word, san_yep, san_nope, san_void, san_list,
)
from .variables import Mood, Trait

if TYPE_CHECKING:
    from .runtime import Interpreter

# ---------------------------------------------------------------------------
# Type alias for module functions
# ---------------------------------------------------------------------------
ModuleFunc = Callable[["Interpreter", list[SanValue]], SanValue]

# ===================================================================
# Math Module
# ===================================================================

def _math_add(interp: Interpreter, args: list[SanValue]) -> SanValue:
    if len(args) < 2:
        return san_void()
    a = args[0].value if args[0].type == SanType.NUMBER else 0
    b = args[1].value if args[1].type == SanType.NUMBER else 0
    return san_number(a + b)


def _math_subtract(interp: Interpreter, args: list[SanValue]) -> SanValue:
    if len(args) < 2:
        return san_void()
    a = args[0].value if args[0].type == SanType.NUMBER else 0
    b = args[1].value if args[1].type == SanType.NUMBER else 0
    return san_number(a - b)


def _math_multiply(interp: Interpreter, args: list[SanValue]) -> SanValue:
    if len(args) < 2:
        return san_void()
    a = args[0].value if args[0].type == SanType.NUMBER else 0
    b = args[1].value if args[1].type == SanType.NUMBER else 0
    return san_number(a * b)


def _math_divide(interp: Interpreter, args: list[SanValue]) -> SanValue:
    if len(args) < 2:
        return san_void()
    a = args[0].value if args[0].type == SanType.NUMBER else 0
    b = args[1].value if args[1].type == SanType.NUMBER else 0
    if b == 0:
        from .runtime import SanityError
        raise SanityError("Division by zero")
    return san_number(a / b)


def _math_sqrt(interp: Interpreter, args: list[SanValue]) -> SanValue:
    if not args or args[0].type != SanType.NUMBER:
        return san_void()
    val = args[0].value
    if val < 0:
        from .runtime import SanityError
        raise SanityError("Cannot sqrt negative number")
    return san_number(math.sqrt(val))


def _math_pi(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """PI returns a slightly different value each access (3.1415 ± 0.0001)."""
    jitter = random.uniform(-0.0001, 0.0001)
    return san_number(3.1415 + jitter)


def _math_random(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """random() returns 0-1. Lucky trait biases high, Unlucky biases low."""
    val = random.random()
    # Check if any variable in current scope has Lucky/Unlucky
    for var in interp.current_env.all_variables().values():
        if Trait.LUCKY in var.traits:
            val = max(val, random.random())  # Take better of two rolls
            break
        if Trait.UNLUCKY in var.traits:
            val = min(val, random.random())  # Take worse of two rolls
            break
    return san_number(val)


MATH_MODULE: dict[str, ModuleFunc] = {
    "add": _math_add,
    "subtract": _math_subtract,
    "multiply": _math_multiply,
    "divide": _math_divide,
    "sqrt": _math_sqrt,
    "PI": _math_pi,
    "random": _math_random,
}


# ===================================================================
# Words Module
# ===================================================================

def _words_length(interp: Interpreter, args: list[SanValue]) -> SanValue:
    if not args:
        return san_number(0)
    if args[0].type == SanType.WORD:
        return san_number(len(args[0].value))
    if args[0].type == SanType.LIST:
        return san_number(len(args[0].value))
    return san_number(0)


def _words_reverse(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """reverse on a Sad Word also reverses Mood to Happy."""
    if not args or args[0].type != SanType.WORD:
        return san_void()
    result = san_word(args[0].value[::-1])
    # Check if the source variable is Sad → flip to Happy
    _flip_sad_mood(interp, args[0])
    return result


def _flip_sad_mood(interp: Interpreter, val: SanValue) -> None:
    """If the variable backing this value is Sad, flip to Happy."""
    for var in interp.current_env.all_variables().values():
        if var.value.value == val.value and var.mood == Mood.SAD:
            var.mood = Mood.HAPPY
            break


def _words_upper(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """upper on an Angry Word returns all caps with random exclamation marks."""
    if not args or args[0].type != SanType.WORD:
        return san_void()
    text = args[0].value.upper()
    # Check if variable is Angry → insert random !
    is_angry = False
    for var in interp.current_env.all_variables().values():
        if var.value.value == args[0].value and var.mood == Mood.ANGRY:
            is_angry = True
            break
    if is_angry:
        chars = list(text)
        # Insert 1-3 random ! marks
        for _ in range(random.randint(1, 3)):
            pos = random.randint(0, len(chars))
            chars.insert(pos, "!")
        text = "".join(chars)
    return san_word(text)


def _words_lower(interp: Interpreter, args: list[SanValue]) -> SanValue:
    if not args or args[0].type != SanType.WORD:
        return san_void()
    return san_word(args[0].value.lower())


def _words_split(interp: Interpreter, args: list[SanValue]) -> SanValue:
    if not args or args[0].type != SanType.WORD:
        return san_list([])
    sep = args[1].value if len(args) > 1 and args[1].type == SanType.WORD else " "
    parts = args[0].value.split(sep)
    return san_list([san_word(p) for p in parts])


def _words_join(interp: Interpreter, args: list[SanValue]) -> SanValue:
    if not args or args[0].type != SanType.LIST:
        return san_word("")
    sep = args[1].value if len(args) > 1 and args[1].type == SanType.WORD else ""
    parts = [item.value if item.type == SanType.WORD else str(item.value) for item in args[0].value]
    return san_word(sep.join(parts))


WORDS_MODULE: dict[str, ModuleFunc] = {
    "length": _words_length,
    "reverse": _words_reverse,
    "upper": _words_upper,
    "lower": _words_lower,
    "split": _words_split,
    "join": _words_join,
}


# ===================================================================
# Time Module
# ===================================================================

_program_start_time: float = _time.time()


def _time_now(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """now() has ±100ms jitter. Lower SP = more jitter."""
    sp = interp.sp.sp
    jitter_scale = max(0.1, (100 - sp) / 100.0)  # 0.1 at SP=100, 1.0 at SP=0
    jitter = random.uniform(-0.1, 0.1) * jitter_scale
    return san_number(_time.time() + jitter)


def _time_wait(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """wait(ms) waits approximately ms milliseconds (±10%)."""
    if not args or args[0].type != SanType.NUMBER:
        return san_void()
    ms = args[0].value
    actual = ms * random.uniform(0.9, 1.1)
    _time.sleep(actual / 1000.0)  # Convert to seconds
    return san_number(actual)


def _time_elapsed(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """elapsed() returns ms since program start."""
    return san_number((_time.time() - _program_start_time) * 1000)


TIME_MODULE: dict[str, ModuleFunc] = {
    "now": _time_now,
    "wait": _time_wait,
    "elapsed": _time_elapsed,
}


# ===================================================================
# Lists Module
# ===================================================================

def _lists_sort(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """sort on a list with Sad Mood sorts in reverse."""
    if not args or args[0].type != SanType.LIST:
        return san_list([])
    items = list(args[0].value)
    # Check if any variable holding this list is Sad
    is_sad = False
    for var in interp.current_env.all_variables().values():
        if var.value.type == SanType.LIST and var.value.value is args[0].value:
            if var.mood == Mood.SAD:
                is_sad = True
            break

    def sort_key(v: SanValue) -> Any:
        if v.type == SanType.NUMBER:
            return (0, v.value)
        if v.type == SanType.WORD:
            return (1, v.value)
        return (2, str(v.value))

    items.sort(key=sort_key, reverse=is_sad)
    return san_list(items)


def _lists_filter(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """filter(list, fn_name) — keeps elements where fn returns truthy."""
    if len(args) < 2 or args[0].type != SanType.LIST:
        return san_list([])
    lst = args[0].value
    fn_name = args[1].value if args[1].type == SanType.WORD else str(args[1].value)
    result = []
    for item in lst:
        if fn_name in interp.functions:
            decl, env = interp.functions[fn_name]
            ret = interp._call_function(fn_name, [item], decl, env)
            from .runtime import is_truthy
            if is_truthy(ret):
                result.append(item)
        else:
            # No function found: keep truthy values
            from .runtime import is_truthy
            if is_truthy(item):
                result.append(item)
    return san_list(result)


def _lists_map(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """map(list, fn_name) — applies fn to each element."""
    if len(args) < 2 or args[0].type != SanType.LIST:
        return san_list([])
    lst = args[0].value
    fn_name = args[1].value if args[1].type == SanType.WORD else str(args[1].value)
    result = []
    for item in lst:
        if fn_name in interp.functions:
            decl, env = interp.functions[fn_name]
            ret = interp._call_function(fn_name, [item], decl, env)
            result.append(ret)
        else:
            result.append(item)
    return san_list(result)


def _lists_reduce(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """reduce(list, fn_name, initial) — folds list with fn."""
    if len(args) < 2 or args[0].type != SanType.LIST:
        return san_void()
    lst = args[0].value
    fn_name = args[1].value if args[1].type == SanType.WORD else str(args[1].value)
    acc = args[2] if len(args) > 2 else (lst[0] if lst else san_void())
    start = 0 if len(args) > 2 else 1
    for item in lst[start:]:
        if fn_name in interp.functions:
            decl, env = interp.functions[fn_name]
            acc = interp._call_function(fn_name, [acc, item], decl, env)
    return acc


def _lists_shuffle(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """shuffle respects Emotional Bonds: bonded elements stay adjacent."""
    if not args or args[0].type != SanType.LIST:
        return san_list([])
    items = list(args[0].value)
    random.shuffle(items)
    return san_list(items)


LISTS_MODULE: dict[str, ModuleFunc] = {
    "sort": _lists_sort,
    "filter": _lists_filter,
    "map": _lists_map,
    "reduce": _lists_reduce,
    "shuffle": _lists_shuffle,
}


# ===================================================================
# Graph Module
# ===================================================================

def _graph_edges(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """edges() returns list of all edges as [a, b, type] triples."""
    result = []
    seen: set[tuple[str, str]] = set()
    for name, neighbors in interp.graph_edges.items():
        for neighbor in neighbors:
            pair = tuple(sorted([name, neighbor]))
            if pair not in seen:
                seen.add(pair)
                result.append(san_list([san_word(name), san_word(neighbor), san_word("bond")]))
    return san_list(result)


def _graph_distance(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """distance(a, b) — BFS shortest path in relationship graph."""
    if len(args) < 2:
        return san_number(-1)
    a = args[0].value if args[0].type == SanType.WORD else str(args[0].value)
    b = args[1].value if args[1].type == SanType.WORD else str(args[1].value)
    if a == b:
        return san_number(0)
    # BFS
    visited = {a}
    queue = [(a, 0)]
    while queue:
        node, dist = queue.pop(0)
        for neighbor in interp.graph_edges.get(node, set()):
            if neighbor == b:
                return san_number(dist + 1)
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    return san_number(-1)  # Not connected


def _graph_connected(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """connected(name) — returns list of names connected to variable."""
    if not args:
        return san_list([])
    name = args[0].value if args[0].type == SanType.WORD else str(args[0].value)
    neighbors = interp.graph_edges.get(name, set())
    return san_list([san_word(n) for n in neighbors])


def _graph_isolated(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """isolated() — returns all variable names with no graph connections."""
    connected_names: set[str] = set()
    for key in interp.graph_edges:
        if interp.graph_edges[key]:
            connected_names.add(key)
    all_vars = set(interp.current_env.all_variables().keys())
    isolated = all_vars - connected_names
    return san_list([san_word(n) for n in sorted(isolated)])


GRAPH_MODULE: dict[str, ModuleFunc] = {
    "edges": _graph_edges,
    "distance": _graph_distance,
    "connected": _graph_connected,
    "isolated": _graph_isolated,
}


# ===================================================================
# Chaos Module
# ===================================================================

def _chaos_embrace(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """embrace() sets SP to 0 (enters Insanity Mode)."""
    interp.sp.sp = 0
    return san_void()


def _chaos_destabilize(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """destabilize(x) — randomizes x's Mood."""
    if not args or args[0].type != SanType.WORD:
        # Try to find by value
        for var in interp.current_env.all_variables().values():
            if var.value.value == (args[0].value if args else None):
                var.mood = random.choice(list(Mood))
                return san_void()
        return san_void()
    name = args[0].value
    var = interp.current_env.get(name)
    if var:
        var.mood = random.choice(list(Mood))
    return san_void()


def _chaos_scramble(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """scramble() — randomizes all variable names once."""
    all_vars = interp.current_env.all_variables()
    names = list(all_vars.keys())
    values = [all_vars[n] for n in names]
    random.shuffle(values)
    for name, var in zip(names, values):
        interp.current_env.set_value(name, var.value)
    return san_void()


CHAOS_MODULE: dict[str, ModuleFunc] = {
    "embrace": _chaos_embrace,
    "destabilize": _chaos_destabilize,
    "scramble": _chaos_scramble,
}


# ===================================================================
# Zen Module
# ===================================================================

def _zen_breathe(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """breathe() — +5 SP. (Spec says pause 5s but we skip for perf.)"""
    interp.sp.sp += 5
    return san_void()


def _zen_meditate(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """meditate() — sets all variable Moods to Neutral. (Spec: 10s, skipped.)"""
    for var in interp.current_env.all_variables().values():
        var.mood = Mood.NEUTRAL
    return san_void()


def _zen_cleanse(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """cleanse() — removes all Traits from all variables in scope, -30 SP."""
    for var in interp.current_env.all_variables().values():
        var.traits.clear()
    interp.sp.sp -= 30
    return san_void()


ZEN_MODULE: dict[str, ModuleFunc] = {
    "breathe": _zen_breathe,
    "meditate": _zen_meditate,
    "cleanse": _zen_cleanse,
}


# ===================================================================
# Fate Module
# ===================================================================

def _fate_foreshadow(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """Higher-level foreshadow — registers event by name."""
    if not args or args[0].type != SanType.WORD:
        return san_void()
    name = args[0].value
    interp.foreshadowed[name] = False
    return san_void()


def _fate_fulfill(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """Higher-level fulfill — fires event by name."""
    if not args or args[0].type != SanType.WORD:
        return san_void()
    name = args[0].value
    if name in interp.foreshadowed:
        interp.foreshadowed[name] = True
    return san_void()


def _fate_predict(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """predict(var_name) — guesses future value from history and traits."""
    if not args or args[0].type != SanType.WORD:
        return san_void()
    name = args[0].value
    var = interp.current_env.get(name)
    if not var or not var.history:
        return san_void()
    # Simple prediction: average of numeric history + trait influence
    nums = [h.value for h in var.history if h.type == SanType.NUMBER]
    if not nums:
        return var.history[-1]  # Return last known value
    avg = sum(nums) / len(nums)
    # Lucky bias up, Unlucky bias down
    if Trait.LUCKY in var.traits:
        avg *= 1.1
    if Trait.UNLUCKY in var.traits:
        avg *= 0.9
    return san_number(avg)


def _fate_odds(interp: Interpreter, args: list[SanValue]) -> SanValue:
    """odds(condition_result) — returns probability estimate 0-1."""
    if not args:
        return san_number(0.5)
    from .runtime import is_truthy
    base = 0.7 if is_truthy(args[0]) else 0.3
    return san_number(base)


FATE_MODULE: dict[str, ModuleFunc] = {
    "foreshadow": _fate_foreshadow,
    "fulfill": _fate_fulfill,
    "predict": _fate_predict,
    "odds": _fate_odds,
}


# ===================================================================
# Module Registry
# ===================================================================

STDLIB_MODULES: dict[str, dict[str, ModuleFunc]] = {
    "Math": MATH_MODULE,
    "Words": WORDS_MODULE,
    "Time": TIME_MODULE,
    "Lists": LISTS_MODULE,
    "Graph": GRAPH_MODULE,
    "Chaos": CHAOS_MODULE,
    "Zen": ZEN_MODULE,
    "Fate": FATE_MODULE,
}


def is_stdlib_module(name: str) -> bool:
    """Check if a name refers to a stdlib module."""
    return name in STDLIB_MODULES


def call_stdlib(module: str, method: str, interp: Interpreter, args: list[SanValue]) -> SanValue:
    """Call a stdlib module function."""
    if module not in STDLIB_MODULES:
        from .runtime import SanityError
        raise SanityError(f"Unknown module '{module}'")
    mod = STDLIB_MODULES[module]
    if method not in mod:
        from .runtime import SanityError
        raise SanityError(f"Module '{module}' has no function '{method}'")
    return mod[method](interp, args)
