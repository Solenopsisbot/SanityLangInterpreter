# (In)SanityLang Specification v0.1-confused

> (In)SanityLang is a general-purpose programming language. Every feature is simple. Every feature interacts with every other feature. Good luck.

File extension: `.san`

---

## 1. Statements & Terminators

Every statement ends with a terminator. There are five terminators. Each one changes how the statement behaves.

| Terminator | Name | Effect |
|---|---|---|
| `.` | Period | Statement runs normally. |
| `..` | Emphasis | Statement runs, and its result is cached permanently. Running the same statement again returns the cached value instead of re-executing. |
| `~` | Uncertain | Statement runs, but the return value is wrapped in an Uncertainty container. Any operation on an Uncertain value has a 15% chance of using the value from the *previous* operation on that variable instead. |
| `!` | Forceful | Statement runs and ignores all Trait effects (see §14) on any variables involved. Also bypasses Mood checks on any Moods involved (see §17). |
| `?` | Questioning | Statement runs, but also prints debug information. Additionally, any variable assigned in a Questioning statement becomes Observed (see §6). |

Terminators stack. `..~` means "cache the result AND wrap it in Uncertainty." Stacking order matters — they apply left-to-right. `~..` means "wrap in Uncertainty first, THEN cache the Uncertain value" (so the cached value is always the same Uncertain wrapper, which still has the 15% chance internally).

If you write a statement with no terminator, the compiler picks one for you based on the current Sanity score:
- SP > 80: picks `.`
- SP 50-80: picks `?` (it's worried about you)
- SP 20-50: picks `~`
- SP < 20: picks `!` (panic mode)

---

## 2. Sanity Points

Every program starts at 100 SP. SP affects compiler and runtime behavior throughout the spec — specific interactions are documented in each section.

SP changes from actions:

| Action | SP Change |
|---|---|
| Declaring a variable with a single-character name | -5 |
| Declaring a variable with a name longer than 20 characters | -2 (verbosity tax) |
| Reassigning a `sure` variable via Override (see §3) | -10 |
| Using `whatever` declaration | -3 |
| Calling a function that has never been called before | +1 (exploration bonus) |
| Calling a function for the 10th+ time | -1 per call (repetition penalty) |
| Writing a `cope` block that doesn't use the error | -5 |
| A `pinky` bond breaking | -15 |
| Using `séance` to access a dead variable | -5 |
| A Trait conflict occurring (see §14) | -3 |
| Winning a `bet` | +reward amount |
| Losing a `bet` | -risk amount |
| A variable's Trust reaching 0 | -8 |
| Using `skip` on a narrative Arc | -10 |
| Entering a new scope | +1 |
| Leaving a scope without using any of its variables | -4 (wasted scope) |
| A `dream` variable being fulfilled from a previous run | +5 |
| Declaring a `curse` | -20 |
| An Emotional Bond forming (see §3) | +2 |
| An Emotional Bond breaking | -7 |
| Unclosed file handle at scope exit (see §30) | -5 per handle |
| Processing untrusted input without checking Trust (see §28) | -3 |
| Canvas SP reaching 0 (see §31) | -10 to program SP |
| Writing to a file with Angry handle (see §30) | -5 (silent failure) |
| Using `shout` (see §28) | -2 (aggression tax) |
| Reading a file (see §30) | -0.5 per MB (resource strain, rounded up) |
| Drawing during Visual Insanity Mode (see §31) | -1 per draw call |

SP is checked at compile time AND at runtime. Some things that cost SP at compile time cost double at runtime (specifically: `whatever` declarations, Trust reaching 0, and `curse` declarations).

When SP ≤ 0, the program enters Insanity Mode. See §19.

---

## 3. Variables & Declarations

### Declaration Keywords

| Keyword | Can Reassign | Can Mutate | Side Effects |
|---|---|---|---|
| `sure` | No (without Override) | No | None |
| `maybe` | Yes | Yes | Each reassignment increments the variable's Doubt counter. At Doubt 5, the variable becomes Uncertain permanently (behaves as if every statement using it ended with `~`). |
| `whatever` | Yes | Yes | Value may spontaneously change to a nearby value (±10% for Numbers, random character swap for Words) once every 50 statements. SP: -3. |
| `swear` | No | No | Attempting reassignment crashes the program AND writes the failed assignment to a `.blame` file with a timestamp. |
| `pinky` | Linked | Linked | Creates a bond between this variable and its source. Changing either changes both. Deleting either deletes both. |
| `ghost` | No | No | Variable cannot be accessed directly. Must use `séance`. See §11. |
| `dream` | Deferred | Deferred | Value comes from a previous execution. See §12. |
| `whisper` | No | No | Variable is only accessible within the same block scope. Attempting to access it from a parent or child scope returns `Void`. Does not error — just silently returns `Void`. |
| `curse` | No | No | Value propagates as a modifier to all variables of the same type in any Chapter that imports this one. See §13. |
| `scream` | Yes | Yes | Every mutation triggers an Event (see §18) that all active `when` listeners receive. |

### Override

You can override a `sure` variable by redeclaring it with `sure` again. The old value goes to the Afterlife (see §11). Costs -10 SP. The new declaration must use the same type, or the variable gains a Scar (see Variable State below).

```
sure name = "Alice".
sure name = "Bob".   // Override. Old "Alice" goes to Afterlife. -10 SP.
```

### Emotional Bonds

When two variables are declared within 3 lines of each other and share a type, they form an Emotional Bond. Bonded variables:
- Cannot be different types (attempting to reassign one to a different type also changes the other).
- Share Trait effects (see §14). If one gains a Trait, the other gains it too.
- If one is deleted, the other enters Grief state: its value becomes `Void` for the next 5 accesses, then recovers.

```
sure x = 10.
sure y = 20.    // x and y are Emotionally Bonded (both Numbers, within 3 lines).
sure z = "hi".  // z is NOT bonded with x or y (different type).
```

Bonds are transitive. If A is bonded with B, and B is bonded with C, then A is bonded with C.

### Variable State

Every variable tracks hidden state:

| State | Default | What Changes It |
|---|---|---|
| Trust | 100 | Decreases by 10 each time the variable is involved in an error. At 0: variable becomes read-only AND every read has 20% chance of returning `Void` instead. |
| Doubt | 0 | Increases by 1 each `maybe` reassignment. At 5: permanent Uncertainty. |
| Age | 0 | Increases by 1 each statement executed (global counter). Affects Trait eligibility (see §14). Variables with Age > 500 gain the Elder Trait automatically. |
| Scars | 0 | +1 each time the variable survives a type change, an Override, or an error in an expression it's part of. Variables with 3+ Scars gain the Resilient Trait. |
| Mood | Neutral | Changes based on operations. See §4. |

---

## 4. Variable Moods

Every variable has a Mood. Mood affects how the variable behaves in operations.

| Mood | Triggered By | Effect |
|---|---|---|
| Neutral | Default | Normal behavior. |
| Happy | Being part of a successful `bet`, or being accessed exactly 7 times | Numeric operations on this variable get +1 to the result. Word operations append "!" to the result. |
| Sad | Being part of a failed `bet`, or not being accessed for 100+ statements | Numeric operations get -1. Word operations drop the last character. |
| Angry | Trust dropping below 50, or being involved in 3+ errors | Operations involving this variable and another Angry variable cause both values to swap. |
| Afraid | Being named in a `blame` statement, or having an Emotional Bond break | Variable cannot be on the left side of a comparison. Attempting `afraidVar == x` is fine, but `x == afraidVar` causes afraidVar to return `Void`. (Yes, comparison side matters.) |
| Excited | Being the return value of a function called for the first time | The variable's value is duplicated — it becomes a List of two copies of itself. If you don't expect this, your types break. |
| Jealous | When another variable with the same name exists in a child scope | This variable slowly converges toward the other variable's value: 10% closer per access. |

Moods propagate through Emotional Bonds. If variable A is Happy and bonded with B, B becomes Happy after A's next operation. The propagation takes 1 operation to travel per bond.

Moods decay after 200 statements and return to Neutral, EXCEPT Angry, which only decays if the variable's Trust recovers above 50.

---

## 5. Types

### Core Types

| Type | Literal |
|---|---|
| `Number` | `42`, `3.14`, `-7` |
| `Word` | `"hello"`, `'hello'` |
| `Yep` | `yep` |
| `Nope` | `nope` |
| `Dunno` | `dunno` |
| `Void` | Cannot be created directly. Returned by failed operations. |
| `List` | `[1, 2, 3]` |
| `Blob` | `{name: "Alice", age: 30}` |

### Type Coercion Rules

When an operation involves different types, coercion follows these rules in order:
1. If either value is `Void`, the result is `Void`.
2. If either value is `Dunno`, the result is `Dunno`.
3. `Yep` coerces to `1` or `"yep"` depending on the other operand's type.
4. `Nope` coerces to `0` or `"nope"`.
5. Numbers and Words: the Number side wins for `+`, `-`, `*`, `/`. The Word side wins for `&` (concatenation).
6. A List coerces to its length in numeric context, or its string representation in Word context.

Each coercion adds 1 Scar to the coerced variable.

### Truthiness

| Value | Truthy? |
|---|---|
| `0` | Nope |
| `""` (empty Word) | Nope |
| `nope` | Nope |
| `dunno` | Sometimes Yep, sometimes Nope. The result is consistent within a single scope but may differ across scopes. |
| `void` | Nope. Also -1 SP for checking. |
| Empty List `[]` | Nope, but the List's Mood becomes Sad. |
| Everything else | Yep |

---

## 6. Observation

A variable becomes **Observed** when:
- It is used in a `?` (Questioning) statement.
- It is passed to `wtf` or `huh` (see §20).
- It is printed.

Observed variables behave differently from unobserved ones:
- An unobserved `Dunno` value can be either truthy or falsy, decided at the moment of first observation and locked in.
- An unobserved Uncertain value (from `~`) doesn't collapse its probability — it remains in superposition. Observing it collapses it.
- An unobserved variable with the Jealous mood doesn't converge toward its shadow. Observation triggers the convergence.

A variable can become **Unobserved** again if it's not accessed for 200 statements. This means its `Dunno` and Uncertainty behaviors reset.

---

## 7. Operators

### Arithmetic

Standard: `+`, `-`, `*`, `/`, `%`, `^` (power).

Whitespace determines precedence. Tighter binding = higher precedence:
```
1 + 2*3     // 7 (2*3 first, tighter)
1+2 * 3     // 9 ((1+2) first, tighter)
1 + 2 * 3   // Ambiguous. Uses default math precedence but costs -2 SP.
```

### Comparison

| Operator | Strictness | Details |
|---|---|---|
| `~=` | Vibes | Same type and within 20% of each other for Numbers, or Levenshtein distance ≤ 3 for Words. |
| `==` | Loose | Same value after coercion. |
| `===` | Strict | Same value and same type. |
| `====` | Identity | Same variable (same memory reference). |

Each level of `=` you add beyond `====` adds an additional check:
- `=====` also checks that both variables have the same Mood.
- `======` also checks same Trust level.
- `=======` also checks same Age.
- And so on. Each `=` adds the next Variable State check in order: Mood, Trust, Age, Scars, Doubt, Bond count.

### Logical

| Operator | Meaning |
|---|---|
| `and` | Both must be truthy. |
| `or` | Either must be truthy. |
| `nor` | Neither must be truthy. |
| `but not` | First must be truthy, second must not. (Not commutative.) |
| `xor` | Exactly one must be truthy. |
| `unless` (binary) | `a unless b` = `a and (not b)`. |

### Emotional Operators

| Operator | Effect |
|---|---|
| `a loves b` | Creates a `pinky`-style bond between a and b. |
| `a hates b` | a and b can never hold the same value. If one is assigned a value the other holds, the assignment is rejected. |
| `a fears b` | Whenever b changes, a triggers a `cope` block if one is registered. |
| `a envies b` | a converges toward b's value by 10% on each access. |
| `a ignores b` | a and b cannot appear in the same expression. Compiler error if they do. |
| `a mirrors b` | a always equals b, but with a 1-statement delay. |
| `a haunts b` | When a is deleted, b's mood becomes Afraid for 100 statements. |

Emotional operators create entries in the Relationship Graph (see §9). They persist until explicitly broken with `a forgets b`.

---

## 8. Functions

### Declaration

| Keyword | Behavior |
|---|---|
| `does` | Standard function. |
| `did` | Memoized. Every unique input set returns the cached result. Cache persists across the entire runtime. If the cache grows past 1000 entries, the oldest entries go to the Afterlife. |
| `will` | Stub. Returns `Dunno` until a real body is provided. Can be called. |
| `might` | Conditional. Takes a `when` clause. Function only exists when the condition is true. Calling it when it doesn't exist returns `Void`. |
| `should` | Must be called at least once before the program ends, or the compiler emits a warning AND -5 SP. |
| `must` | Auto-called at program start. Also callable manually. |

### Call Counting

Every function tracks how many times it has been called. This count affects behavior:

| Call Count | Effect |
|---|---|
| 1st call | Return value's Mood is set to Excited (see §4). |
| 2nd-9th call | Normal. +1 SP for first call only. |
| 10th+ call | -1 SP per call. Compiler suggests "maybe refactor?" at 25 calls. |
| 50th+ call | Function gains the Tired Trait (see §14). Return values get -1 numeric or drop last character. |
| 100th+ call | Function becomes Resentful. 5% chance per call of returning `Void` instead of the real value. |

### Closures & Scope Capture

Functions capture variables from their enclosing scope. But captured variables are **copies**, not references — UNLESS the variable was declared with `scream`, in which case it's a live reference.

If a captured variable has an Emotional Bond with another variable, both are captured (even if only one is referenced).

### Return Behavior

The terminator on the `return` statement matters:

```
does compute() {
   return 42.    // Normal return.
   return 42..   // Cached: this function always returns 42 from now on, regardless of logic.
   return 42~    // Uncertain return: caller gets an Uncertain value.
   return 42!    // Forceful: strips all Traits from the return value.
   return 42?    // Debug: prints the return value and marks it Observed.
}
```

---

## 9. The Relationship Graph

Every variable, function, and Personality (see §15) is a node in the Relationship Graph. Edges are created by:

- Emotional Bonds (§3)
- Emotional Operators (§7)
- `pinky` declarations
- Function call relationships (caller → callee)
- Trait sharing (§14)
- `curse` propagation (§13)

The Relationship Graph affects:
1. **Garbage collection priority**: Variables with more incoming edges live longer.
2. **Error propagation**: Errors travel along edges. A variable that errors causes bonded variables to lose 5 Trust.
3. **Mood propagation**: Moods spread along edges, one hop per operation.
4. **Insanity Mode behavior**: In Insanity Mode, variable name swaps only happen between connected nodes.

You can query the graph:
```
sure connections = graph.edges(x).  // Returns List of all variables connected to x.
sure distance = graph.distance(x, y). // Shortest path length. Dunno if not connected.
```

---

## 10. Control Flow

### Branching

```
if (cond) { ... }
but (cond2) { ... }     // else-if
actually { ... }         // else

unless (cond) { ... }    // Inverse if

suppose (cond) { ... }   // Compiler skips the condition check. If cond is false at 
                          // runtime, all variables modified inside become Uncertain.

pretend (cond) { ... }   // Block runs regardless. But all assignments inside are 
                          // tagged Pretend. Pretend values can't escape the block —
                          // they become Void outside it.
```

### Pattern Matching

```
check value {
   is Number { ... }
   is Word { ... }
   is Yep or Nope { ... }
   is Void { ... }           // Costs -1 SP. Why are you checking for Void?
   is List where length > 3 { ... }
   is Blob with key "name" { ... }
   otherwise { ... }
}
```

`check` also accounts for variable state if you want:
```
check value {
   is Number and mood Happy { ... }
   is Number and trust < 50 { ... }
   is Word and scars > 2 { ... }
}
```

### Loops

| Keyword | Behavior |
|---|---|
| `again { ... }` | Loop until `enough.` is called. |
| `pls N { ... }` | Loop N times. `pls N as i` gives you a counter. |
| `pls N as i` | Counter `i` starts at 1 (not 0). If current SP < 50, counter starts at 0 instead. |
| `ugh (cond) { ... }` | While loop. Each iteration, there's a 1% cumulative chance the loop just quits (the "ugh I give up" mechanic). So iteration 1 has 1% quit chance, iteration 100 has 100% quit chance (it WILL quit). |
| `forever { ... }` | Infinite. Can only be stopped by a `mercy.san` file existing in the same directory or by the OS killing the process. |
| `hopefully (cond) { ... }` | While loop that grants +1 SP per iteration (optimism bonus). But if the loop runs more than 100 iterations, it switches to -2 SP per iteration (hope is fading). |
| `reluctantly (cond) { ... }` | While loop. Execution speed halves each iteration (1ms delay, 2ms, 4ms...). |
| `never { ... }` | Block never executes. But it IS compiled and type-checked. Variables declared inside exist in a special Never scope that can be referenced by `séance`. |

### Loop Interactions

A `pls` loop inside an `ugh` loop: the inner loop's count is affected by the outer loop's quit probability. Specifically, the inner count is multiplied by `(1 - quit_probability)`. So a `pls 100` on the 50th iteration of an `ugh` loop only runs ~50 times.

A `hopefully` loop inside a `bet` block: the SP gains from `hopefully` are multiplied by the bet's reward multiplier.

---

## 11. The Afterlife & Ghosts

When a variable is deleted (goes out of scope, is Overridden, or is explicitly deleted), its last value goes to the **Afterlife**, a persistent store.

Access the Afterlife:
```
sure oldVal = séance("variableName").
```

Rules:
- `séance` costs -5 SP.
- It returns the most recently deceased variable with that name. If multiple died, you get the latest.
- A variable can be séanced up to 3 times. After that, it "moves on" and is gone forever.
- If a `ghost` variable is séanced (ghosts are technically alive but invisible), it works but costs -8 SP instead.
- Séancing a variable that died Angry gives you its value but also makes the receiving variable Angry.
- Séancing a variable that died Afraid gives you `Void`.
- Séancing a variable that had Scars > 3 gives you the value, but the receiving variable inherits 1 Scar.

### Ghost Variables

Declared with `ghost`. Cannot be accessed directly. `séance` is the only way. Ghosts:
- Don't appear in `graph.edges()` queries.
- Don't form Emotional Bonds (they're invisible).
- Don't age (Age stays at 0).
- Contribute to SP: -1 per ghost per 100 statements (haunting tax).
- If you have more than 5 ghosts, the compiler warns: "Your codebase is haunted."

---

## 12. Dream Variables

Declared with `dream`. Their values persist across program runs via `.san.dream` files.

```
dream counter = 0.
counter = counter + 1.
print(counter).  // 1 on first run, 2 on second, etc.
```

Rules:
- On first run, a `dream` variable's initial value is used.
- On subsequent runs, the value from the end of the last run is loaded.
- If the `.san.dream` file is deleted, all `dream` variables revert to initial values. +5 SP (fresh start bonus).
- If the `.san.dream` file is manually edited, all `dream` variables gain the Scar state and their Trust drops by 20 (tampering detected).
- `dream` variables cannot have Emotional Bonds with non-dream variables (they exist on different temporal planes).
- `dream` variables CAN bond with other `dream` variables. These bonds persist across runs.

---

## 13. Curses

`curse` declarations create values that silently modify all variables of the same type in any Chapter (see §16) that imports this one.

```
--- Chapter: Chaos ---
curse wobble: Number = 0.05.
```

Any Chapter that does `recall Chaos` will find ALL their Number operations gain ±5% random variation. The importing code has no indication this is happening unless they check the Relationship Graph.

Curses stack. If you import two Chapters that each have a Number curse, the effects compound.

Curses can be removed:
```
exorcise wobble.  // -25 SP cost. Removes the curse from the current scope.
```

If you `exorcise` a curse you didn't import (it doesn't exist in your scope), you gain +5 SP for being proactive.

You can detect curses:
```
sure curses = sanity.curses().  // Returns List of active curses in current scope.
```

---

## 14. Traits

Traits are passive modifiers that attach to variables (and Personalities—see §15). They modify behavior silently.

### How Traits Are Gained

| Trait | Gained When |
|---|---|
| Elder | Variable Age > 500. |
| Resilient | Variable has 3+ Scars. |
| Tired | Function called 50+ times. Variable accessed 200+ times. |
| Lucky | Variable was part of a winning `bet`. |
| Unlucky | Variable was part of 3+ losing `bet`s. |
| Paranoid | Variable's Trust dropped below 30 at any point. |
| Popular | Variable has 5+ edges in the Relationship Graph. |
| Lonely | Variable has 0 edges in the Relationship Graph for 100+ statements. |
| Cursed | Variable is affected by a `curse`. |
| Blessed | Variable was `exorcise`d from a curse. |
| Volatile | Variable is declared with `scream`. |
| Attentive | Variable was created by `listen` (see §28). |
| Tainted | Variable was assigned from `args` or `ask` input (see §28, §29). |
| Creative | Variable is associated with canvas operations (see §31). |

### Trait Effects

| Trait | Effect |
|---|---|
| Elder | Immune to Mood changes. Immune to `whatever` spontaneous changes. |
| Resilient | Type coercion no longer adds Scars. Trust decay is halved. |
| Tired | All operations involving this variable take 1ms longer (simulated). -1 to numeric results. |
| Lucky | 10% chance of `bet`s involving this variable auto-winning regardless of condition. |
| Unlucky | 10% chance of operations producing `Void` instead of the real result. |
| Paranoid | Cannot be coerced to another type. Rejects Emotional Bonds. Rejects `pinky`. |
| Popular | +1 Trust per 50 statements (social support). |
| Lonely | -1 Trust per 50 statements (isolation penalty). Mood tends toward Sad. |
| Cursed | See §13. Cursor operations have ±curse_value% variation. |
| Blessed | Immune to curses. +1 SP per 100 statements. |
| Volatile | Every mutation fires an Event (see §18). Makes the variable visible across scopes. |
| Attentive | Resists Mood changes from Emotional Bonds (stays focused). Trust decay halved. |
| Tainted | Trust capped at 70 until explicitly `cleanse`d via Zen module. Cannot gain Lucky Trait. |
| Creative | +1 SP per 50 statements (creative bonus). Immune to Lonely Trait effects. |

### Trait Interactions

- **Elder + Tired**: Cancel out. Variable is experienced enough to handle fatigue.
- **Lucky + Unlucky**: Both remain. Each operation flips a coin: Lucky effect or Unlucky effect.
- **Paranoid + Popular**: Paranoid blocks new bonds, but existing bonds remain. Popular's Trust bonus still applies.
- **Lonely + Volatile**: Contradiction. Variable becomes Erratic: value randomly shifts by ±1 each access.
- **Resilient + Cursed**: Curse effect is halved.
- **Blessed + Cursed**: Impossible. Blessed removes Cursed.
- **Tainted + Paranoid**: Both remain. Variable rejects all bonds AND has capped Trust. Essentially quarantined.
- **Creative + Tired**: Creative wins. The variable is "inspired through exhaustion" — Tired effects are suppressed.
- **Attentive + Lonely**: Attentive prevents Mood from tending Sad. But Lonely Trust decay still applies at half rate (Attentive halves it).
- **Tainted + Blessed**: Tainted is removed. Blessed purifies the input.

Traits propagate through Emotional Bonds. If A gains Lucky, all variables bonded with A gain Lucky after A's next operation.

---

## 15. Personalities (Classes)

```
personality Dog {
   sure name = "Rex".
   maybe energy = 100.
   
   does bark() {
      energy = energy - 10.
      return "Woof!".
   }
}

sure myDog = become Dog().
```

### Inheritance

```
personality Puppy from Dog {
   maybe energy = 200.
   
   does zoomies() {
      energy = energy - 50.
      return "NYOOOM".
   }
}
```

Multiple inheritance is allowed. If two parents define the same method, you must resolve:
```
personality CatDog from Dog, Cat {
   resolve speak = Dog.speak.
}
```

If you don't resolve a conflict, the method randomly picks a parent on each call. The choice depends on the current SP: even SP → first parent, odd SP → second parent.

### Personality Traits

Personalities can have Traits just like variables:
```
personality Hero with Lucky, Resilient {
   ...
}
```

All instances of a traited Personality inherit those Traits. Instances can gain additional Traits through normal means.

### Instance Mood

Instances have Moods. The Mood is the average of the Moods of all their member variables. If most members are Angry, the instance is Angry, and calling methods on it has a 10% chance of the method refusing to execute (returns `Void`).

### Evolution

Instances evolve based on method call patterns:
- If `bark()` is called 100 times, the Dog gains the Tired Trait.
- If `energy` drops below 0, the instance enters Despair state: all method calls return `"I can't do this anymore"` as a Word.
- If energy exceeds 200, the instance enters Manic state: all method calls execute twice.

### Instance Death

If an instance's internal SP reaches 0 (instances have their own SP, starting at 100, affected by the same table as the main program), the instance dies:
- All references become `ghost` references.
- The instance goes to the Afterlife.
- Accessing it via `séance` returns a read-only copy.

---

## 16. Chapters (Modules)

```
--- Chapter: Utils ---
sure version = "1.0".

does helpers() { ... }
```

### Recall (Import)

```
recall Utils.                // Import everything.
recall helpers from Utils.   // Import specific.
```

### Chapter Trust

Chapters have a Trust score (0-100), starting at 70. Trust changes:
- -5 when an export causes an error in another Chapter.
- -10 when a Chapter is the source of a `blame`.
- +2 per successful import that doesn't error for 100 statements.

Low-trust Chapters:
- Trust < 50: Compiler warns on `recall`.
- Trust < 30: All imports are automatically wrapped in `try/cope`.
- Trust < 10: `recall` requires `!` terminator (Forceful) to proceed.

### Chapter Secrets

```
secret does internalHelper() { ... }
```

`secret` items can't be `recall`ed. But they CAN be accessed via `séance` from another Chapter (-10 SP, -20 Trust for the importing Chapter).

### Chapter Alliances & Rivalries

```
--- Chapter: Frontend ---
--- allies: Design ---
--- rivals: Backend ---
```

Importing from an ally: +3 SP per import.
Importing from a rival: All imports execute 25% slower and errors in imported functions blame the importing Chapter.

---

## 17. Concurrency

### Vibe (Async Task)

```
sure task = vibe {
   return heavyCompute().
}
sure result = chill task.   // Wait for completion.
```

### Mood Lock (Mutex)

```
sure lock = mood("database").

vibe {
   feel lock {
      write(data).
   }
}
```

Mood locks have Moods (obviously):
- If a lock is acquired too frequently (>50 times in 10 seconds), it becomes Stressed. Stressed locks have +10ms latency.
- If a lock is held for too long (>5 seconds), it becomes Resentful. Resentful locks have a 5% chance of releasing early.
- A lock that is never contended for 60 seconds becomes Lonely and automatically releases (useless lock cleanup).

### Vibe Interactions with Variables

Variables accessed from multiple vibes:
- `sure`: safe (immutable).
- `maybe`: race condition possible. No protection. The last write wins. -5 SP per race.
- `scream`: safe (Events serialize access).
- `whatever`: pure chaos across vibes. Don't.

---

## 18. Events

`scream` variables emit Events on every mutation. Other code can listen:

```
scream score = 0.

when score changes {
   print("Score is now {score}").
}

score = 10.  // Triggers the listener.
```

`when` also works with Moods:
```
when score mood Happy {
   print("Score is feeling good!").
}
```

Events are also emitted by:
- Personality instances entering/leaving states (Despair, Manic, Death).
- Trait acquisition.
- SP crossing thresholds (every 10-point boundary).
- Emotional Bond formation/breaking.
- `fulfill` and `foreshadow` resolution.

You can `when` any of these:
```
when sanity crosses 50 {
   print("Halfway to insanity.").
}

when anyBond breaks {
   print("Someone got hurt.").
}
```

---

## 19. Insanity Mode

Triggered when SP ≤ 0.

Effects:
1. Variable names may swap along Relationship Graph edges every 20 statements.
2. `pls` loop counters gain ±1 random offset each iteration.
3. Numeric operations gain ±(|SP| / 10)% noise.
4. Word operations randomly capitalize one character per operation.
5. `if` branches have a 10% chance of running the wrong branch.
6. All compiler messages become haiku.
7. The Relationship Graph gains random edges between unrelated variables.
8. `bet` win probabilities are inverted.
9. `maybe` variables reassign themselves spontaneously every 30 statements.
10. The `ugh` loop's quit probability doubles.

Escaping Insanity Mode:
```
i am okay.    // Resets SP to 50. Only works if no variable in scope is Angry.
```

If any variable in scope IS Angry, `i am okay` is rejected:
```
[SanityLang] No you're not. (x is still Angry)
```

You must resolve the anger first:
```
x forgets everyone.   // Clears all Emotional Operators involving x. 
                       // x's Mood decays normally after this.
```

---

## 20. Debugging

| Keyword | Output |
|---|---|
| `wtf x` | Full report: type, value, mood, trust, age, scars, doubt, traits, bonds, graph edges. Makes x Observed. |
| `huh x` | Quick report: type and value only. Makes x Observed. |
| `cry "msg"` | Halts execution. Prints stack trace with Mood annotations for each frame. |
| `therapy` | Analyzes the entire program state: SP, variable count, ghost count, active curses, Relationship Graph density, longest Emotional Bond chain, warnings. |
| `oracle "question"` | Compiler attempts to answer based on static analysis. Answers are not guaranteed to be correct and cost -3 SP regardless. |

---

## 21. Error Handling

```
try { ... }
cope (error) { ... }      // Like catch. Error is a Blob with {message, source, blame, mood}.
deny (error) { ... }       // Error is suppressed. But logged in .san.blame file. 
                            // Source variable's Trust -10.
```

### Blame

```
blame "Dave" for "breaking prod".
// Throws an error. The error's .blame field is "Dave".
// If Dave is a variable in scope, Dave's Trust -20 and Mood becomes Afraid.
```

### Oops

```
oops "something minor".
// Logs a warning. Does not halt. But SP -2.
// If oops is called 10+ times in one execution, it escalates to a real error.
```

### Yolo

```
yolo {
   dangerousStuff().
}
// All errors inside are silently swallowed.
// Each swallowed error costs -5 SP (you don't see them, but you pay).
// If yolo swallows 10+ errors, the block's variables all gain the Cursed Trait.
```

---

## 22. Gambling

### Bet

```
bet (users > 1000) reward 10 risk 20 {
   print("popular!").
}
// If condition is true: +10 SP, block runs.
// If false: -20 SP, block is skipped.
// Variables used in the condition are affected:
//   Winners gain Lucky Trait.
//   Losers (from 3+ lost bets) gain Unlucky Trait.
```

### Odds

```
sure chance = odds(x > 100).
// Returns a Number 0-100 representing the compiler's best guess.
// Based on x's current value, Mood, Trust, and Traits.
// If x is Lucky: odds are inflated by 10%.
// If x is Unlucky: odds are deflated by 10%.
```

### Jackpot

```
jackpot (condition) {
   // Runs if condition is true AND it's been false the last 99 times it was checked.
   // Basically: runs once per 100 checks, on average.
   // When it runs: +50 SP.
}
```

---

## 23. Narrative Structure

Programs can optionally be structured as narratives:

```
prologue {
   // Runs first. Always.
}

arc "Setup" {
   // A named section. Runs in order.
}

arc "Conflict" requires "Setup" {
   // Only runs if "Setup" completed without errors.
}

climax requires "Conflict" {
   // The main event.
}

epilogue {
   // Runs last. Always. Even after crashes. Like a finally for the whole program.
}
```

`skip "arc name"` skips an arc. -10 SP. If a later arc requires the skipped one, the later arc's variables all start as Uncertain.

---

## 24. Time

### Foreshadow / Fulfill

```
foreshadow eventName.

// ... later ...
fulfill eventName.   // Triggers any `when eventName` listeners.
```

Unfulfilled foreshadows at program end: -5 SP each and a compiler warning.

### Remember

```
sure x = 10.
x = 20.
x = 30.
print(remember x 1).  // 10 (first value).
print(remember x 2).  // 20 (second value).
```

`remember` costs 0 SP but makes the variable Observed.

### Rewind

```
rewind 3.  // Re-executes the last 3 statements.
```

Rewind does NOT undo SP changes from the original execution. You pay SP twice.

Variables modified during the rewound statements keep their rewound values, but their Age increases from the re-execution, which might trigger new Trait acquisitions.

---

## 25. The `no` Keyword

Bans things from your program:

```
no floats.          // Decimal numbers become errors.
no recursion.       // Self-referencing function calls error.
no negativity.      // Negative numbers become their absolutes silently.
no uncertainty.     // ~ terminator is banned.
no ghosts.          // ghost declarations error. Existing ghosts die permanently.
no feelings.        // All Emotional Operators error. Emotional Bonds can't form.
no gambling.        // bet, odds, jackpot all error.
no time.            // remember, rewind, foreshadow, dream all error.
```

`no` declarations interact: `no feelings` + `no gambling` triggers the compiler message "You must be fun at parties. +5 SP."

Banning something that's already been used: the ban applies retroactively. All affected statements re-execute without the banned feature. If this changes program state, those changes apply. SP costs are not refunded.

---

## 26. Self-Modification

### Grammar Modification

```
grammar.alias("yeet", "throw").     // yeet is now valid as throw.
grammar.alias("fr", "sure").        // fr x = 10. is now valid.
grammar.remove("unless").           // unless is no longer valid syntax.
```

Grammar changes apply to all code AFTER the modification statement, including code in recalled Chapters that hasn't been parsed yet.

If you remove a keyword used in a `when` block, the listener silently deactivates.

### Compiler Prayers

```
pray for speed.      // Compiler optimizes aggressively. Some runtime checks removed.
pray for safety.     // All operations are bounds-checked and type-checked at runtime.
pray for mercy.      // SP penalties halved in the current scope.
pray for chaos.      // Enter Insanity Mode voluntarily.
pray for nothing.    // No effect. +1 SP for the gesture.
```

`pray for speed` + `pray for safety` = cancel out. Compiler ignores both. -5 SP for indecisiveness.

---

## 27. Standard Library Modules

| Module | Key Functions | Quirks |
|---|---|---|
| `Math` | `add`, `subtract`, `multiply`, `divide`, `sqrt`, `PI`, `random` | `PI` returns a slightly different value each access (3.1415 ± 0.0001). `random` is affected by Lucky/Unlucky Traits. |
| `Words` | `length`, `reverse`, `upper`, `lower`, `split`, `join` | `reverse` on a Sad Word also reverses the Mood to Happy. `upper` on an Angry Word returns all caps with random exclamation marks. |
| `Time` | `now`, `wait`, `elapsed` | `now` has ±100ms jitter. `wait(ms)` waits approximately `ms` milliseconds (±10%). The jitter is affected by the current SP: lower SP = more jitter. |
| `Lists` | `sort`, `filter`, `map`, `reduce`, `shuffle` | `sort` on a list with Sad Mood sorts in reverse. `shuffle` respects Emotional Bonds: bonded elements stay adjacent. |
| `Graph` | `edges`, `distance`, `connected`, `isolated` | Queries the Relationship Graph. `isolated()` returns all variables with no connections (Lonely candidates). |
| `Chaos` | `embrace`, `destabilize`, `scramble` | `embrace()` sets SP to 0 (enters Insanity Mode). `destabilize(x)` randomizes x's Mood. `scramble()` randomizes all variable names once. |
| `Zen` | `breathe`, `meditate`, `cleanse` | `breathe()` pauses 5 seconds, +5 SP. `meditate()` sets all variable Moods to Neutral, but takes 10 seconds. `cleanse()` removes all Traits from all variables in scope, -30 SP (fresh start). |
| `Fate` | `foreshadow`, `fulfill`, `predict`, `odds` | Higher-level versions of built-in time/gambling features. `predict(x)` uses x's history and Traits to guess future value. |
| `IO` | `ask`, `listen`, `shout`, `whisper` | See §28. `IO.buffer()` returns all unread stdin as a List. `IO.flush()` forces all pending output. `IO.silence()` suppresses all output for N statements. |
| `Files` | `open`, `read`, `write`, `append`, `close`, `exists`, `delete`, `list_dir` | See §30. `Files.temp()` returns a temp file handle (auto-deletes at scope end, Mood: Neutral). `Files.cwd()` returns current directory as a Word. |
| `Canvas` | `canvas`, `pixel`, `line`, `rect`, `circle`, `text`, `sprite`, `show` | See §31. `Canvas.screenshot()` captures current window. `Canvas.fps()` returns current framerate as a Number with Lucky/Unlucky Trait effects. |
| `Args` | `args`, `flags`, `env` | See §29. `Args.env(key)` returns environment variables (Trust 20, even lower than args). `Args.count()` returns arg count. |

---

## 28. Console IO

SanityLang has built-in console IO. All input is considered untrusted by default.

### Output

`print` writes to stdout as you'd expect. But SanityLang has additional output modes:

```
print("Normal output").         // stdout, normal
shout("LOUD OUTPUT").           // stdout, ALL CAPS forced. -2 SP.
whisper("secret output").       // stderr. If the variable has Paranoid Trait, output is ROT13.
```

`shout` ignores any Sad Mood modifiers on the variable — it forces the text through unmodified (and uppercased). This is the only way to guarantee un-altered output.

`whisper` respects all Mood modifiers. A Sad variable whispered drops its last character. An Angry variable whispered adds random caps.

The terminator on print/shout/whisper matters:

```
print("hello").     // Normal. Output: hello
print("hello")..    // Cached. This exact string will never be printed again — duplicates are silently dropped.
print("hello")~     // Uncertain output. 15% chance of printing the PREVIOUS print's content instead.
print("hello")!     // Forceful. Ignores ALL Trait effects on the variable.
print("hello")?     // Debug. Also prints the variable's Mood, Trust, and Traits alongside the value.
```

### Input

#### `ask`

Reads a single line from stdin:

```
sure name = ask("What's your name? ").
```

Rules:
- The returned Word has **Trust 50** (we don't fully trust user input).
- The returned Word gains the **Tainted Trait** automatically.
- The Word's **Mood** is set by naive sentiment analysis of the content:
  - Input contains "!", positive words, emoji → Happy
  - Input contains "no", "bad", negative words → Sad
  - Input contains profanity, ALL CAPS → Angry
  - Input is empty → Afraid
  - Otherwise → Neutral
- The variable receiving the `ask` result inherits the Mood.
- If an Emotional Bond is formed between an `ask` result and another variable, the other variable also gains Tainted.

Terminator effects on `ask`:

```
sure name = ask("Name? ").       // Normal.
sure name = ask("Name? ")..      // Cached: same prompt returns same answer without re-asking.
sure name = ask("Name? ")~       // If user doesn't respond in 5 seconds, a random Word is used.
sure name = ask("Name? ")!       // Forceful: returned value has NO Traits (not even Tainted).
sure name = ask("Name? ")?       // Debug: also prints what Mood the input was assigned.
```

#### `listen`

Reads stdin continuously until EOF:

```
sure lines = listen().
// lines is a List of Words. Each line is an element.
```

Rules:
- The returned List gains the **Attentive Trait**.
- Each line element has Trust 50 and Tainted Trait.
- If the user takes more than 10 seconds between lines, all accumulated input so far has its Trust reduced by 5 per 10-second gap (impatience penalty).
- If the user sends more than 100 lines, the List gains the **Overwhelmed** Mood (new — see below). Overwhelmed Lists have a 5% chance of dropping an element on each access.
- In Insanity Mode, `listen` input characters are shuffled within each line.

### New Mood: Overwhelmed

| Mood | Triggered By | Effect |
|---|---|---|
| Overwhelmed | A List exceeding 100 elements via `listen`, or a file handle reading >10,000 lines | 5% chance of dropping an element/line per access. Numeric operations on the variable randomly skip. Overwhelmed propagates through Emotional Bonds but decays by 1 hop (bonded variables get a milder version: 2% drop chance). |

---

## 29. Command-Line Arguments

### `args`

A built-in `sure` List of Words containing all command-line arguments.

```
// $ sanityc run program.san hello world --verbose

print(args).  // ["program.san", "hello", "world", "--verbose"]
```

Rules:
- `args` is immutable (`sure` List).
- The List starts with **Trust 30**.
- Each element Word has **Doubt 3** (nearly Uncertain — two more `maybe` reassignments and it becomes permanently Uncertain).
- Each element has the **Tainted Trait**.
- `args[0]` is the program name. It has the **Elder Trait** (it existed before the program started). Accessing it costs 0 SP.
- Assigning any `args` element to another variable creates an Emotional Bond between them. The receiving variable inherits the low Trust and Tainted Trait. This means the taint spreads through your codebase via bonds.

### `flags`

A built-in `sure` Blob that auto-parses `--key=value` and `-k value` patterns:

```
// $ sanityc run program.san --name=Hakka -v --count=42

print(flags.name).   // "Hakka" (Word, Trust 30, Tainted)
print(flags.v).      // yep (Yep, Trust 30, Tainted)
print(flags.count).  // "42" (Word, not Number! You must coerce manually.)
print(flags.missing).// Void (not an error)
```

Coercing a flag value to a Number adds a Scar to the variable (type coercion as usual) AND keeps the Tainted Trait.

### Special Flags

If the user passes these flags to the *program* (not just the compiler):

| Flag | Effect |
|---|---|
| `--chaos` | Program starts at 50 SP instead of 100. |
| `--help` | Program lists all `should` functions with signatures, then exits. |
| `--mercy` | Equivalent to `pray for mercy` at program start. |
| `--trust-me` | All `args` and `flags` values start with Trust 70 instead of 30. |

### Iterating Args

`args` in a `pls` loop works normally. But `args` in an `ugh` loop: the ugh quit probability starts at 5% per iteration instead of the usual 1% (args are annoying to parse and the runtime knows it).

`args` in a `hopefully` loop: no SP bonus (there's nothing hopeful about argument parsing).

---

## 30. Filesystem IO

### Opening Files

```
open "data.txt" as file.
```

File handles are **Personality instances**. They have Moods, Traits, Trust (starting at 70), their own SP (starting at 100), and participate in the Relationship Graph.

The file handle's **starting Mood** depends on the file extension:

| Extension | Starting Mood | Rationale |
|---|---|---|
| `.san` | Happy | One of us! |
| `.txt` | Neutral | Plain and simple. |
| `.json` | Paranoid | Strict format, easily broken. |
| `.csv` | Sad | Nobody actually enjoys CSV. |
| `.log` | Tired | It's seen things. |
| `.md` | Happy | Documentation is appreciated. |
| `.yaml` / `.yml` | Afraid | One wrong indent and it's over. |
| `.xml` | Angry | Self-explanatory. |
| `.env` | Paranoid | Contains secrets. Trust starts at 40 instead of 70. |
| Unknown extension | Afraid | We don't know what you are. |
| No extension | Dunno | Could be anything. Mood is Dunno too. |

### Reading

```
sure content = read file.
```

Returns the entire file as a Word. The returned Word inherits the file handle's **Trust** and **Mood**.

```
sure lines = file.lines().
```

Returns a List of Words, one per line. List Mood depends on file size:
- < 100 lines → Happy
- 100-1000 lines → Neutral
- 1000-10000 lines → Tired
- > 10000 lines → Overwhelmed (see §28)

Reading a file costs **-0.5 SP per megabyte** (rounded up). A 500KB file costs -1 SP. A 10MB file costs -5 SP. A 200MB file costs -100 SP (instant Insanity Mode from a single read). Files over 1MB also set the file handle's Mood to Tired.

#### Read Terminator Effects

```
sure content = read file.     // Normal read.
sure content = read file..    // Cached: re-reading returns the same content without hitting disk.
sure content = read file~     // May return the file's PREVIOUS contents (from .san.dream cache).
sure content = read file!     // Forceful: strips all Traits from the returned value.
sure content = read file?     // Debug: also prints the file handle's Mood, Trust, and SP.
```

### Writing

```
write "hello world" to file.
append "another line" to file.
```

Rules:
- If the file handle is **Angry**, the write **fails silently**. Content is redirected to `.san.blame`. The handle's Trust drops by 10. -5 SP.
- If the file handle is **Afraid**, the write works but takes 2x as long (double confirmation internal process).
- If the file handle is **Tired**, writes have a 5% chance of being truncated (last 10% of content dropped).
- If the file handle's Trust is < 30, writes are automatically backed up to a `.san.backup` file.
- Writing to a file with the `~` terminator: the write is buffered but may or may not actually flush to disk (Uncertain write).
- Writing to a file with `..`: the write is cached — writing the same content again is a no-op.

### Closing

```
close file.
```

The handle goes to the Afterlife. It can be `séance`d to get a read-only handle to re-read the last known contents.

**Forgetting to close a handle**: when the scope exits, unclosed handles ghost themselves automatically. Each unclosed handle costs **-5 SP**. If you have 3+ unclosed handles, the compiler warns: "You're leaking file handles. This is going on your permanent record."

### File Handle Interactions

- File handles opened within 3 lines of each other form **Emotional Bonds** (same as variables). If one handle becomes Angry (write error), bonded handles become Afraid.
- File handles participate in the **Relationship Graph**. A file that is read and then its contents assigned to a variable creates an edge from handle → variable.
- `read` makes the file handle **Observed** (see §6). An Observed file handle cannot have its Mood change silently — all Mood changes are logged.
- A file handle with the **Cursed Trait** (from importing a cursed Chapter that opened it): read/write operations have ±curse_value% character corruption.

### Path Interpolation

File paths can use `{interpolation}`:

```
sure dir = "data".
open "{dir}/output.txt" as file.
```

But: the interpolated variable must have **Trust ≥ 50**. If Trust < 50, the operation is rejected:

```
[SanityLang] Path interpolation rejected: 'dir' has Trust 35. Potential path traversal.
```

This means `args` values (Trust 30) **cannot** be used directly in file paths without Trust boosting. To boost Trust:

```
sure safePath = cleanse(args[1]).  // Removes Tainted, sets Trust to 70.
open "{safePath}/data.txt" as file.
```

`cleanse` is from the Zen module and costs -5 SP.

### Other File Operations

```
sure exists = file.exists().      // Yep or Nope. Makes the handle Observed.
file.delete().                     // Deletes the file. Handle enters Grief Mood.
                                   // Any variable that was read from this file gains a Scar.
sure size = file.size().           // Returns Number (bytes).
sure modified = file.modified().   // Returns Number (unix timestamp, with ±100ms Time jitter).
```

### Directory Operations

```
sure entries = Files.list_dir("./data").
// Returns a List of Blobs: [{name: "file.txt", kind: "file"}, {name: "subdir", kind: "dir"}, ...]
// The List has same Trust as the path variable used.
// Each entry Blob has the starting Mood of its extension (as per the table above).
```

---

## 31. Graphics

SanityLang has a built-in immediate-mode graphics system. Because why the fuck not.

### Creating a Canvas

```
sure screen = canvas("My App", 800, 600).
```

The canvas is a **Personality instance** with:
- Its own **SP** (starts at 100, separate from program SP).
- Its own **Mood** (starts at Happy — fresh blank canvas).
- Its own **Trust** (starts at 100).
- Its own **Traits** (starts with Creative).
- Participation in the **Relationship Graph**.

### Drawing Primitives

```
screen.pixel(x, y, "red").                       // Single pixel.
screen.line(x1, y1, x2, y2, "blue").             // Line.
screen.rect(x, y, width, height, "green").       // Filled rectangle.
screen.rect(x, y, width, height, "green", nope). // Outline only (pass nope for fill).
screen.circle(x, y, radius, "yellow").           // Circle.
screen.text(x, y, "Hello!", 16).                 // Text with font size.
```

Colors can be Words (`"red"`, `"blue"`, `"#FF0000"`) or Blobs (`{r: 255, g: 0, b: 0}`).

#### Drawing SP Costs

Each draw operation costs the **canvas's** SP (not the program's):

| Operation | Canvas SP Cost |
|---|---|
| `pixel` | 0 |
| `line` | -1 |
| `rect` | -2 |
| `circle` | -3 |
| `text` | -5 |
| `sprite` (see below) | -3 |
| `clear` | -1 |

When canvas SP ≤ 0: **Visual Insanity Mode**. Effects:
- Colors shift hue by a random amount each frame.
- Lines gain ±3px wobble per endpoint.
- Text renders in random sizes (±30% of specified).
- Rectangles may have rounded corners at random radii.
- Circles become ellipses.
- -10 to **program** SP when canvas SP first hits 0.

Canvas SP recovers +1 per `show()` call (the canvas rests between frames).

#### Mood Effects on Rendering

The Mood of the **variable being rendered** (not the canvas) affects how it looks:

| Mood | Visual Effect |
|---|---|
| Happy | Subtle glow / brightness boost. |
| Sad | 30% transparency applied. |
| Angry | Color overridden to bold red. Text is bold. |
| Afraid | Rendered 20% smaller than specified. |
| Excited | Rendered with a pulsing animation (size oscillates ±5%). |
| Tired | Rendered with reduced saturation. |
| Overwhelmed | Rendered with visual noise/static effect. |
| Neutral | No modification. |

If the **canvas itself** is Angry (e.g., from bonded file handle errors), all rendering has a red tint overlay.

If the **canvas itself** is Sad, the entire canvas has a desaturation filter.

### Displaying

Graphics are **double-buffered**. Nothing appears until you call `show()`:

```
screen.clear().
screen.rect(0, 0, 800, 600, "black").
screen.text(400, 300, "Hello World", 32).
screen.show().   // Frame is now visible. Canvas SP +1.
```

### Input Handling

```
screen.onClick(does (x, y) {
   print("Clicked at {x}, {y}").
}).

screen.onKey(does (key) {
   print("Pressed: {key}").
}).

screen.onMouseMove(does (x, y) {
   // Called every frame the mouse moves.
}).
```

Rules:
- Callback function parameters (`x`, `y`, `key`) have **Trust 30** and **Tainted Trait** (untrusted input from the user's meat fingers).
- If the canvas is **Afraid** (from a bonded error), click/key handlers are **disabled for 50 statements**. Mouse events still fire.
- Handler functions follow all normal function rules: call counting, Tired Trait at 50+ calls, Resentful at 100+ calls. This means a click handler called 100+ times has a 5% chance of returning Void per click. Plan accordingly.
- If the `key` Word has Angry Mood (user mashing keyboard sends angry-seeming input), the key's value may be ALL CAPS regardless of actual case.

### Sprites

```
sure player = screen.sprite("hero.png", 100, 200).
player.x = 150.
player.y = 250.
player.show().   // Renders the sprite on the canvas.
```

Sprites are **Personality instances**:
- They have Moods, Traits, Trust, their own SP.
- They participate in the Relationship Graph.
- A sprite loaded from a file forms an Emotional Bond with the file handle that loaded the image.
- Sprites with the **Tired Trait** move 10% slower in animations (position updates are multiplied by 0.9).
- Sprites can form **Emotional Bonds** with other sprites if created within 3 lines. Bonded sprites maintain their relative distance — moving one moves the other to preserve the offset.

```
sure player = screen.sprite("hero.png", 100, 200).
sure pet = screen.sprite("cat.png", 120, 200).     // Bonded! Offset: (20, 0)

player.x = 300.  // pet.x automatically becomes 320. That's the deal.
```

Sprites with the **Afraid** Mood render with slight jitter (±1px per frame).

### Game Loop

```
screen.every(16, does () {
   // Called approximately every 16ms (~60fps).
   screen.clear().
   updateGameState().
   drawEverything().
   screen.show().
}).
```

The `ms` timing is affected by program SP jitter (same as `Time.wait` — lower SP = more frame timing jitter). At SP < 20, frame timing can vary by ±50%, making the game feel "drunk."

The callback follows all function call counting rules. After 50 calls (50 frames), the callback gains Tired Trait. After 100 calls, it's Resentful. This means a game loop will start glitching after ~100 frames unless you account for it.

To reset a function's call count:

```
forget calls on myCallback.  // Resets call counter to 0. Costs -5 SP.
```

### Canvas State

```
screen.save("screenshot.png").   // Saves to file. Creates a file handle bonded with the canvas.
screen.clear().                   // Clears the canvas. All pixel data goes to the Afterlife.

// Restore a cleared canvas:
sure oldState = séance("screen").  // Gets the last canvas state from the Afterlife.
screen.restore(oldState).          // Restores it. Costs -5 SP for the séance.
```

### Canvas and `no` Bans

`no graphics.` disables the entire §31. Any canvas operations become compile errors.

A program with `no graphics` that tries to `open` a `.png` file:
```
[SanityLang] You banned graphics but you're opening a .png? What are you doing with it? (-3 SP, suspicion)
```

---

## Appendix A: File Types

| Extension | Purpose |
|---|---|
| `.san` | Source file |
| `.san.dream` | Dream variable persistence |
| `.san.blame` | Blame and error logs |
| `.san.therapy` | Therapy session logs |
| `.san.backup` | Automatic backup from low-Trust file writes (see §30) |
| `.san.canvas` | Canvas state persistence for séance restoration (see §31) |
| `mercy.san` | Place in directory to kill `forever` loops |

---

## Appendix B: Compiler Flags

| Flag | Effect |
|---|---|
| `--strict` | All implicit SP costs are doubled. |
| `--lenient` | SP cannot go below 10 (prevents Insanity Mode). |
| `--chaos` | Program starts in Insanity Mode. |
| `--no-mood` | Disables Variable Moods. (Variables still have the state, but it has no effect.) |
| `--audit` | Extra SP tracking, report at end. |
| `--pray` | Equivalent to `pray for mercy` globally. |
| `--i-know-what-im-doing` | Required to compile `.insanity` files. |
| `--headless` | Disables canvas window. All draw calls render to buffer only. `show()` is a no-op. |
| `--no-input` | All `ask` calls return `Dunno`. `listen` returns empty List. |
| `--trust-all` | All input (args, ask, files, keys) starts with Trust 100. You're living dangerously. |
| `--target <t>` | Compilation target: `native`, `js`, `python`, `c`, `english`, `haiku`, `therapy`, `cursed` (outputs DreamBerd). |

---

## Appendix C: If You're Struggling

If this is too complicated for you, just go and use brainfuck instead.
