"""Token types for (In)SanityLang."""
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    # === Literals ===
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # === Declaration Keywords ===
    SURE = auto()
    MAYBE = auto()
    WHATEVER = auto()
    SWEAR = auto()
    PINKY = auto()
    GHOST = auto()
    DREAM = auto()
    WHISPER = auto()
    CURSE = auto()
    SCREAM = auto()

    # === Function Keywords ===
    DOES = auto()
    DID = auto()
    WILL = auto()
    MIGHT = auto()
    SHOULD = auto()
    MUST = auto()
    RETURN = auto()

    # === Control Flow ===
    IF = auto()
    BUT = auto()
    ACTUALLY = auto()
    UNLESS = auto()
    SUPPOSE = auto()
    PRETEND = auto()
    CHECK = auto()
    IS = auto()
    OTHERWISE = auto()
    WHERE = auto()
    WITH = auto()

    # === Loops ===
    AGAIN = auto()
    PLS = auto()
    AS = auto()
    UGH = auto()
    FOREVER = auto()
    HOPEFULLY = auto()
    RELUCTANTLY = auto()
    NEVER = auto()
    ENOUGH = auto()

    # === Boolean Literals ===
    YEP = auto()
    NOPE = auto()
    DUNNO = auto()

    # === Logical Operators ===
    AND = auto()
    OR = auto()
    NOR = auto()
    BUT_NOT = auto()
    XOR = auto()
    NOT = auto()
    # UNLESS is also a binary logical op (reused from control flow)

    # === Emotional Operators ===
    LOVES = auto()
    HATES = auto()
    FEARS = auto()
    ENVIES = auto()
    IGNORES = auto()
    MIRRORS = auto()
    HAUNTS = auto()
    FORGETS = auto()
    EVERYONE = auto()

    # === Comparison ===
    VIBES_EQUAL = auto()      # ~=
    LOOSE_EQUAL = auto()      # ==
    STRICT_EQUAL = auto()     # ===
    IDENTITY_EQUAL = auto()   # ====
    EXTENDED_EQUAL = auto()   # ===== and beyond (stores count)
    NOT_EQUAL = auto()        # !=
    LESS = auto()             # <
    GREATER = auto()          # >
    LESS_EQUAL = auto()       # <=
    GREATER_EQUAL = auto()    # >=

    # === Arithmetic ===
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    CARET = auto()            # ^ (power)
    AMPERSAND = auto()        # & (concatenation)

    # === Assignment ===
    EQUALS = auto()           # =

    # === Terminators ===
    PERIOD = auto()           # .
    EMPHASIS = auto()         # ..
    UNCERTAIN = auto()        # ~
    FORCEFUL = auto()         # !  (as terminator)
    QUESTIONING = auto()      # ?  (as terminator)

    # === Delimiters ===
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    COLON = auto()

    # === Error Handling ===
    TRY = auto()
    COPE = auto()
    DENY = auto()
    BLAME = auto()
    FOR = auto()
    OOPS = auto()
    YOLO = auto()

    # === Afterlife / Ghosts ===
    SEANCE = auto()           # séance (also seance)
    DELETE = auto()

    # === Gambling ===
    BET = auto()
    REWARD = auto()
    RISK = auto()
    ODDS = auto()
    JACKPOT = auto()

    # === Narrative ===
    PROLOGUE = auto()
    ARC = auto()
    CLIMAX = auto()
    EPILOGUE = auto()
    REQUIRES = auto()
    SKIP = auto()

    # === Time ===
    FORESHADOW = auto()
    FULFILL = auto()
    REMEMBER = auto()
    REWIND = auto()

    # === Chapters ===
    CHAPTER = auto()
    RECALL = auto()
    FROM = auto()
    SECRET = auto()
    ALLIES = auto()
    RIVALS = auto()

    # === Personalities ===
    PERSONALITY = auto()
    BECOME = auto()
    RESOLVE = auto()

    # === Concurrency ===
    VIBE = auto()
    CHILL = auto()
    MOOD = auto()
    FEEL = auto()

    # === Events ===
    WHEN = auto()
    CHANGES = auto()
    CROSSES = auto()

    # === Debugging ===
    WTF = auto()
    HUH = auto()
    CRY = auto()
    THERAPY = auto()
    ORACLE = auto()
    PRINT = auto()

    # === Self-Modification ===
    GRAMMAR = auto()
    PRAY = auto()
    NO = auto()
    EXORCISE = auto()

    # === Insanity ===
    I = auto()
    AM = auto()
    OKAY = auto()

    # === Graph ===
    GRAPH = auto()

    # === Sanity Namespace ===
    SANITY = auto()

    # === Special ===
    EOF = auto()
    NEWLINE = auto()

    # === Misc ===
    DOT = auto()              # Single dot when NOT a terminator (e.g. member access)
    TRIPLE_DASH = auto()      # --- (chapter header delimiter)


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int
    # For whitespace-sensitive precedence: spaces before/after this token
    spaces_before: int = 0
    spaces_after: int = 0
    # For extended equality: how many = signs
    equal_count: int = 0

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"


# Keywords mapping
KEYWORDS: dict[str, TokenType] = {
    # Declarations
    "sure": TokenType.SURE,
    "maybe": TokenType.MAYBE,
    "whatever": TokenType.WHATEVER,
    "swear": TokenType.SWEAR,
    "pinky": TokenType.PINKY,
    "ghost": TokenType.GHOST,
    "dream": TokenType.DREAM,
    "whisper": TokenType.WHISPER,
    "curse": TokenType.CURSE,
    "scream": TokenType.SCREAM,

    # Functions
    "does": TokenType.DOES,
    "did": TokenType.DID,
    "will": TokenType.WILL,
    "might": TokenType.MIGHT,
    "should": TokenType.SHOULD,
    "must": TokenType.MUST,
    "return": TokenType.RETURN,
    "give": TokenType.RETURN,

    # Control flow
    "if": TokenType.IF,
    "but": TokenType.BUT,
    "actually": TokenType.ACTUALLY,
    "unless": TokenType.UNLESS,
    "suppose": TokenType.SUPPOSE,
    "pretend": TokenType.PRETEND,
    "check": TokenType.CHECK,
    "is": TokenType.IS,
    "otherwise": TokenType.OTHERWISE,
    "where": TokenType.WHERE,
    "with": TokenType.WITH,

    # Loops
    "again": TokenType.AGAIN,
    "pls": TokenType.PLS,
    "as": TokenType.AS,
    "ugh": TokenType.UGH,
    "forever": TokenType.FOREVER,
    "hopefully": TokenType.HOPEFULLY,
    "reluctantly": TokenType.RELUCTANTLY,
    "never": TokenType.NEVER,
    "enough": TokenType.ENOUGH,

    # Booleans
    "yep": TokenType.YEP,
    "nope": TokenType.NOPE,
    "dunno": TokenType.DUNNO,

    # Logical
    "and": TokenType.AND,
    "or": TokenType.OR,
    "nor": TokenType.NOR,
    "xor": TokenType.XOR,
    "not": TokenType.NOT,

    # Emotional
    "loves": TokenType.LOVES,
    "hates": TokenType.HATES,
    "fears": TokenType.FEARS,
    "envies": TokenType.ENVIES,
    "ignores": TokenType.IGNORES,
    "mirrors": TokenType.MIRRORS,
    "haunts": TokenType.HAUNTS,
    "forgets": TokenType.FORGETS,
    "everyone": TokenType.EVERYONE,

    # Error handling
    "try": TokenType.TRY,
    "cope": TokenType.COPE,
    "deny": TokenType.DENY,
    "blame": TokenType.BLAME,
    "for": TokenType.FOR,
    "oops": TokenType.OOPS,
    "yolo": TokenType.YOLO,

    # Afterlife
    "séance": TokenType.SEANCE,
    "seance": TokenType.SEANCE,
    "delete": TokenType.DELETE,

    # Gambling
    "bet": TokenType.BET,
    "reward": TokenType.REWARD,
    "risk": TokenType.RISK,
    "odds": TokenType.ODDS,
    "jackpot": TokenType.JACKPOT,

    # Narrative
    "prologue": TokenType.PROLOGUE,
    "arc": TokenType.ARC,
    "climax": TokenType.CLIMAX,
    "epilogue": TokenType.EPILOGUE,
    "requires": TokenType.REQUIRES,
    "skip": TokenType.SKIP,

    # Time
    "foreshadow": TokenType.FORESHADOW,
    "fulfill": TokenType.FULFILL,
    "remember": TokenType.REMEMBER,
    "rewind": TokenType.REWIND,

    # Chapters
    "recall": TokenType.RECALL,
    "from": TokenType.FROM,
    "secret": TokenType.SECRET,

    # Personalities
    "personality": TokenType.PERSONALITY,
    "become": TokenType.BECOME,
    "resolve": TokenType.RESOLVE,

    # Concurrency
    "vibe": TokenType.VIBE,
    "chill": TokenType.CHILL,
    "mood": TokenType.MOOD,
    "feel": TokenType.FEEL,

    # Events
    "when": TokenType.WHEN,
    "changes": TokenType.CHANGES,
    "crosses": TokenType.CROSSES,

    # Debugging
    "wtf": TokenType.WTF,
    "huh": TokenType.HUH,
    "cry": TokenType.CRY,
    "therapy": TokenType.THERAPY,
    "oracle": TokenType.ORACLE,
    "print": TokenType.PRINT,

    # Self-modification
    "grammar": TokenType.GRAMMAR,
    "pray": TokenType.PRAY,
    "no": TokenType.NO,
    "exorcise": TokenType.EXORCISE,

    # Insanity escape — 'i' is NOT a keyword to avoid collision with variable names
    # The parser handles 'i am okay' by checking for IDENTIFIER 'i'
    "am": TokenType.AM,
    "okay": TokenType.OKAY,

    # Graph
    "graph": TokenType.GRAPH,

    # Sanity namespace
    "sanity": TokenType.SANITY,
}
