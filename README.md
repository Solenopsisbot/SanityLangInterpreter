# (In)SanityLang

> *"Every feature is simple. Every feature interacts with every other feature. Good luck."*

An interpreter for **(In)SanityLang** — an esoteric programming language where your code has feelings, your variables have trust issues, and your sanity is a finite resource.

Built in Python. Powered by existential dread.

---

## ✨ What Is This?

SanityLang is an esoteric language with a **Sanity Points (SP)** system. Every action — declaring variables, calling functions, writing messy code — costs SP. When SP hits zero, you enter **Insanity Mode**, where the rules of reality bend: bets invert, errors become haiku, and your variables start lying to you.

### Key Concepts

| Concept | What It Means |
|---------|---------------|
| **Sanity Points (SP)** | Starts at 100. Everything costs SP. Hit 0 and enter Insanity Mode. |
| **Variable Keywords** | `sure` (constant), `maybe` (mutable, gains Doubt), `whatever` (spontaneously mutates), `swear` (truly immutable, crashes on reassign) |
| **Emotional Operators** | `loves`, `hates`, `fears`, `envies`, `ignores`, `mirrors`, `haunts`, `forgets` |
| **Moods & Traits** | Variables develop moods (Angry, Afraid, Excited, Jealous) and traits (Lucky, Cursed, Elder, Popular) |
| **Ghost Variables** | Can only be accessed via `séance()` |
| **Functions** | `does` (normal), `did` (memoized), `will` (stub), `might` (50/50), `should` (guilt on skip), `must` (crashes if unused) |
| **Gambling** | `bet(condition) reward N risk M { ... }` — win or lose SP |
| **Narrative Structure** | `prologue`, `epilogue`, `arc`, `foreshadow`, `fulfill` |
| **Chapters** | Module system with trust scores and secret filtering |

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install & Run

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/SanityLangInterpreter.git
cd SanityLangInterpreter

# Install dependencies
uv sync

# Run an example
uv run sanity examples/hello.san

# Start the REPL
uv run sanity --repl
```

## 📝 Language Overview

### Variables

```
sure name = "Alice".         // Constant (can override with sure, costs SP)
maybe count = 0.             // Mutable (tracks Doubt, breaks at Doubt 5)
whatever chaos = 42.         // Spontaneously mutates every 50 statements
swear TRUTH = "immutable".   // Crashes the program if reassigned
ghost hidden = 99.           // Can only be accessed via séance("hidden")
whisper local = 1.           // Only accessible in its declaring scope
```

### Functions

```
does greet(name) {
    print("Hello, " & name).
}

did fib(n) {                 // Memoized — caches results
    if n <= 1 { return n. }
    return fib(n - 1) + fib(n - 2).
}

might crash() {              // 50% chance of actually running
    return "surprise!".
}
```

### Control Flow

```
if x > 10 {
    print("big").
} but x > 5 {
    print("medium").
} actually {
    print("small").
}

unless raining {
    print("going outside").
}

check value {
    is Number { print("it's a number"). }
    is Word   { print("it's a string"). }
    otherwise { print("it's something else"). }
}
```

### Loops

```
pls 10 as i {                // Counted loop (i goes 1..10)
    print(i).
}

again {                      // Infinite loop
    print("looping").
    if done { enough. }      // Break with `enough`
}
```

### Error Handling

```
try {
    oops "something broke".  // Throw an error
} cope {
    print("handled it").     // Catch and recover
}

therapy.                     // Print program state diagnostics
```

### Gambling

```
sure luck = 1.
bet(luck == 1) reward 20 risk 10 {
    print("won!").           // Runs if condition is true, +20 SP
}
// If condition is false: body skipped, -10 SP

no gambling.                 // Ban all gambling for the rest of the program
```

### Narrative

```
prologue {                   // Runs before everything else
    print("Once upon a time...").
}

foreshadow doom.             // Declare a future event
fulfill doom.                // Mark it as fulfilled

epilogue {                   // Runs after everything else
    print("The end.").
}
```

## 🏗️ Standard Library

| Module | Functions |
|--------|-----------|
| `Math` | `add`, `subtract`, `multiply`, `divide`, `sqrt`, `PI`, `random` |
| `Words` | `length`, `reverse`, `upper`, `lower`, `split`, `join` |
| `Time` | `now`, `wait`, `elapsed` |
| `Lists` | `sort`, `filter`, `map`, `reduce`, `shuffle` |
| `Graph` | `edges`, `distance`, `connected`, `isolated` |
| `Chaos` | `embrace`, `destabilize`, `scramble` |
| `Zen` | `breathe`, `meditate`, `cleanse` |
| `Fate` | `foreshadow`, `fulfill`, `predict`, `odds` |

```
sure pi = Math.PI().
sure reversed = Words.reverse("hello").   // "olleh"
sure result = Math.add(10, 20).           // 30
```

## ⚙️ Compiler Flags

| Flag | Effect |
|------|--------|
| `--strict` | Double all implicit SP costs |
| `--lenient` | SP cannot go below 10 (prevents Insanity Mode) |
| `--chaos` | Start in Insanity Mode (SP = 0) |
| `--no-mood` | Disable Variable Moods |
| `--pray` | Halve all SP penalties |
| `--audit` | Track every SP change, print report at end |
| `--i-know-what-im-doing` | Required to run `.insanity` files |
| `--repl` | Force interactive REPL mode |

```bash
# Run with audit mode to see every SP change
uv run sanity --audit examples/fibonacci.san

# Chaos mode — start at SP 0
uv run sanity --chaos examples/chaos.san

# Lenient mode — can't die
uv run sanity --lenient examples/hello.san
```

## 📂 Project Structure

```
SanityLangInterpreter/
├── sanity/                  # Interpreter source
│   ├── __init__.py          # Package exports
│   ├── main.py              # CLI entry point
│   ├── lexer.py             # Tokenizer
│   ├── tokens.py            # Token types & keywords
│   ├── parser.py            # AST parser
│   ├── ast_nodes.py         # AST node definitions
│   ├── runtime.py           # Tree-walking interpreter
│   ├── runtime_statements.py # Statement execution
│   ├── sanity_points.py     # SP tracking system
│   ├── types.py             # SanityLang type system
│   ├── variables.py         # Variable model (moods, traits, bonds)
│   └── stdlib.py            # Standard library modules
├── examples/                # Example programs
│   ├── hello.san            # Hello world + basics
│   ├── fibonacci.san        # Recursive fib with memoization
│   ├── chaos.san            # Insanity mode demo
│   └── fate.san             # Narrative & gambling
├── tests/                   # Test suite (579 tests)
├── SPEC.md                  # Full language specification
├── pyproject.toml           # Project configuration
└── README.md                # You are here
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test class
uv run pytest tests/test_programs.py -k "TestMultiFeaturePrograms"
```

**579 tests** covering all language features, including 31 multi-feature integration tests.

## 📖 Specification

The full language specification is in [SPEC.md](SPEC.md) — all 37KB of it. It covers every feature in excruciating detail, including the interactions between Sanity Points, Variable Moods, Emotional Bonds, Relationship Graphs, and the 47 other systems that make this language deeply unhinged.

## 📜 License

MIT — because even chaos deserves freedom.
