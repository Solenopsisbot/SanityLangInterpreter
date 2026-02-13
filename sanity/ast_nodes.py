"""AST node definitions for (In)SanityLang."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


# ============================================================
# Base
# ============================================================

@dataclass
class ASTNode:
    """Base for all AST nodes."""
    line: int = 0
    column: int = 0


@dataclass
class Statement(ASTNode):
    """Base for statements. Stores the terminator(s) applied to this statement."""
    terminators: list[str] = field(default_factory=list)  # e.g. ['.'], ['..', '~'], etc.


@dataclass
class Expression(ASTNode):
    """Base for expressions."""
    pass


# ============================================================
# Expressions
# ============================================================

@dataclass
class NumberLiteral(Expression):
    value: float = 0.0


@dataclass
class StringLiteral(Expression):
    value: str = ""


@dataclass
class BoolLiteral(Expression):
    """Yep, Nope, or Dunno."""
    value: str = "yep"  # "yep", "nope", or "dunno"


@dataclass
class VoidLiteral(Expression):
    pass


@dataclass
class ListLiteral(Expression):
    elements: list[Expression] = field(default_factory=list)


@dataclass
class BlobLiteral(Expression):
    pairs: list[tuple[str, Expression]] = field(default_factory=list)


@dataclass
class VariableAccess(Expression):
    name: str = ""


@dataclass
class MemberAccess(Expression):
    object: Expression = field(default_factory=Expression)
    member: str = ""


@dataclass
class IndexAccess(Expression):
    object: Expression = field(default_factory=Expression)
    index: Expression = field(default_factory=Expression)


@dataclass
class BinaryOp(Expression):
    left: Expression = field(default_factory=Expression)
    operator: str = ""
    right: Expression = field(default_factory=Expression)
    # For whitespace-sensitive precedence
    left_spaces: int = 0
    right_spaces: int = 0


@dataclass
class UnaryOp(Expression):
    operator: str = ""
    operand: Expression = field(default_factory=Expression)


@dataclass
class ComparisonOp(Expression):
    left: Expression = field(default_factory=Expression)
    operator: str = ""  # "~=", "==", "===", "====", "=====", etc.
    right: Expression = field(default_factory=Expression)
    equal_count: int = 2  # Number of = signs for extended checks


@dataclass
class LogicalOp(Expression):
    left: Expression = field(default_factory=Expression)
    operator: str = ""  # "and", "or", "nor", "but not", "xor", "unless"
    right: Expression = field(default_factory=Expression)


@dataclass
class EmotionalOp(Expression):
    left: Expression = field(default_factory=Expression)
    operator: str = ""  # "loves", "hates", "fears", "envies", "ignores", "mirrors", "haunts"
    right: Expression = field(default_factory=Expression)


@dataclass
class FunctionCall(Expression):
    callee: Expression = field(default_factory=Expression)
    arguments: list[Expression] = field(default_factory=list)


@dataclass
class SeanceCall(Expression):
    name: str = ""


@dataclass
class OddsCall(Expression):
    condition: Expression = field(default_factory=Expression)


@dataclass
class RememberCall(Expression):
    variable: str = ""
    index: Expression = field(default_factory=Expression)


@dataclass
class BecomeCall(Expression):
    personality: str = ""
    arguments: list[Expression] = field(default_factory=list)


@dataclass
class GraphAccess(Expression):
    """graph.edges(x), graph.distance(x,y), etc."""
    method: str = ""
    arguments: list[Expression] = field(default_factory=list)


@dataclass
class SanityAccess(Expression):
    """sanity.curses(), etc."""
    method: str = ""
    arguments: list[Expression] = field(default_factory=list)


# ============================================================
# Statements
# ============================================================

@dataclass
class Program(ASTNode):
    """Top-level program node."""
    chapters: list[ChapterDef] = field(default_factory=list)
    body: list[Statement] = field(default_factory=list)
    # Narrative structure (optional)
    prologue: Optional[Block] = None
    arcs: list[ArcDef] = field(default_factory=list)
    climax: Optional[ClimaxDef] = None
    epilogue: Optional[Block] = None


@dataclass
class Block(ASTNode):
    statements: list[Statement] = field(default_factory=list)


@dataclass
class ExpressionStatement(Statement):
    expression: Expression = field(default_factory=Expression)


@dataclass
class VarDeclaration(Statement):
    """Variable declaration: <keyword> <name> = <value>."""
    keyword: str = ""  # "sure", "maybe", "whatever", "swear", "pinky", "ghost", "dream", "whisper", "curse", "scream"
    name: str = ""
    value: Optional[Expression] = None
    # For pinky: the source variable
    source: Optional[str] = None
    # For curse: the type it applies to
    curse_type: Optional[str] = None


@dataclass
class Assignment(Statement):
    name: str = ""
    value: Expression = field(default_factory=Expression)


@dataclass
class MemberAssignment(Statement):
    object: Expression = field(default_factory=Expression)
    member: str = ""
    value: Expression = field(default_factory=Expression)


@dataclass
class IndexAssignment(Statement):
    object: Expression = field(default_factory=Expression)
    index: Expression = field(default_factory=Expression)
    value: Expression = field(default_factory=Expression)


@dataclass
class PrintStatement(Statement):
    expression: Expression = field(default_factory=Expression)


# --- Control Flow ---

@dataclass
class IfStatement(Statement):
    condition: Expression = field(default_factory=Expression)
    body: Block = field(default_factory=Block)
    but_clauses: list[ButClause] = field(default_factory=list)
    actually_block: Optional[Block] = None


@dataclass
class ButClause(ASTNode):
    condition: Expression = field(default_factory=Expression)
    body: Block = field(default_factory=Block)


@dataclass
class UnlessStatement(Statement):
    condition: Expression = field(default_factory=Expression)
    body: Block = field(default_factory=Block)


@dataclass
class SupposeStatement(Statement):
    condition: Expression = field(default_factory=Expression)
    body: Block = field(default_factory=Block)


@dataclass
class PretendStatement(Statement):
    condition: Expression = field(default_factory=Expression)
    body: Block = field(default_factory=Block)


# --- Pattern Matching ---

@dataclass
class CheckStatement(Statement):
    value: Expression = field(default_factory=Expression)
    cases: list[CheckCase] = field(default_factory=list)
    otherwise: Optional[Block] = None


@dataclass
class CheckCase(ASTNode):
    type_name: Optional[str] = None  # "Number", "Word", etc.
    type_names: list[str] = field(default_factory=list)  # for "is Yep or Nope"
    condition: Optional[Expression] = None  # for "where length > 3"
    blob_key: Optional[str] = None  # for "with key 'name'"
    mood_check: Optional[str] = None  # for "and mood Happy"
    state_check: Optional[tuple[str, str, Expression]] = None  # ("trust", "<", expr)
    body: Block = field(default_factory=Block)


# --- Loops ---

@dataclass
class AgainLoop(Statement):
    body: Block = field(default_factory=Block)


@dataclass
class PlsLoop(Statement):
    count: Expression = field(default_factory=Expression)
    counter_name: Optional[str] = None  # from "pls N as i"
    body: Block = field(default_factory=Block)


@dataclass
class UghLoop(Statement):
    condition: Expression = field(default_factory=Expression)
    body: Block = field(default_factory=Block)


@dataclass
class ForeverLoop(Statement):
    body: Block = field(default_factory=Block)


@dataclass
class HopefullyLoop(Statement):
    condition: Expression = field(default_factory=Expression)
    body: Block = field(default_factory=Block)


@dataclass
class ReluctantlyLoop(Statement):
    condition: Expression = field(default_factory=Expression)
    body: Block = field(default_factory=Block)


@dataclass
class NeverBlock(Statement):
    body: Block = field(default_factory=Block)


@dataclass
class EnoughStatement(Statement):
    pass


# --- Functions ---

@dataclass
class FunctionDecl(Statement):
    keyword: str = ""  # "does", "did", "will", "might", "should", "must"
    name: str = ""
    params: list[str] = field(default_factory=list)
    body: Block = field(default_factory=Block)
    # For "might": the when condition
    condition: Optional[Expression] = None
    # For secret functions
    is_secret: bool = False


@dataclass
class ReturnStatement(Statement):
    value: Optional[Expression] = None


# --- Error Handling ---

@dataclass
class TryCope(Statement):
    try_block: Block = field(default_factory=Block)
    cope_param: Optional[str] = None
    cope_block: Optional[Block] = None
    deny_param: Optional[str] = None
    deny_block: Optional[Block] = None


@dataclass
class BlameStatement(Statement):
    target: str = ""
    reason: str = ""


@dataclass
class OopsStatement(Statement):
    message: str = ""


@dataclass
class YoloBlock(Statement):
    body: Block = field(default_factory=Block)


# --- Gambling ---

@dataclass
class BetBlock(Statement):
    condition: Expression = field(default_factory=Expression)
    reward: Expression = field(default_factory=Expression)
    risk: Expression = field(default_factory=Expression)
    body: Block = field(default_factory=Block)


@dataclass
class JackpotBlock(Statement):
    condition: Expression = field(default_factory=Expression)
    body: Block = field(default_factory=Block)


# --- Narrative ---

@dataclass
class ArcDef(ASTNode):
    name: str = ""
    requires: Optional[str] = None
    body: Block = field(default_factory=Block)


@dataclass
class ClimaxDef(ASTNode):
    requires: Optional[str] = None
    body: Block = field(default_factory=Block)


# --- Time ---

@dataclass
class ForeshadowStatement(Statement):
    event_name: str = ""


@dataclass
class FulfillStatement(Statement):
    event_name: str = ""


@dataclass
class RewindStatement(Statement):
    count: Expression = field(default_factory=Expression)


# --- Chapters ---

@dataclass
class ChapterDef(ASTNode):
    name: str = ""
    allies: list[str] = field(default_factory=list)
    rivals: list[str] = field(default_factory=list)
    body: list[Statement] = field(default_factory=list)


@dataclass
class RecallStatement(Statement):
    module: str = ""
    specific: Optional[str] = None  # None = import all


# --- Personalities ---

@dataclass
class PersonalityDef(Statement):
    name: str = ""
    parents: list[str] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)
    body: list[Statement] = field(default_factory=list)
    resolves: dict[str, str] = field(default_factory=dict)  # method -> parent


# --- Concurrency ---

@dataclass
class VibeBlock(Statement):
    body: Block = field(default_factory=Block)


@dataclass
class ChillStatement(Statement):
    task: Expression = field(default_factory=Expression)


@dataclass
class MoodLockDecl(Statement):
    name: str = ""


@dataclass
class FeelBlock(Statement):
    lock: Expression = field(default_factory=Expression)
    body: Block = field(default_factory=Block)


# --- Events ---

@dataclass
class WhenBlock(Statement):
    """when <target> <event_type> { ... }"""
    target: str = ""
    event_type: str = ""  # "changes", "mood <X>", "crosses <N>", event name
    event_arg: Optional[Any] = None
    body: Block = field(default_factory=Block)


# --- Debugging ---

@dataclass
class WtfStatement(Statement):
    target: str = ""


@dataclass
class HuhStatement(Statement):
    target: str = ""


@dataclass
class CryStatement(Statement):
    message: str = ""


@dataclass
class TherapyStatement(Statement):
    pass


@dataclass
class OracleStatement(Statement):
    question: str = ""


# --- Self-Modification ---

@dataclass
class GrammarAlias(Statement):
    new_keyword: str = ""
    old_keyword: str = ""


@dataclass
class GrammarRemove(Statement):
    keyword: str = ""


@dataclass
class PrayStatement(Statement):
    prayer: str = ""  # "speed", "safety", "mercy", "chaos", "nothing"


@dataclass
class NoStatement(Statement):
    feature: str = ""  # "floats", "recursion", "negativity", etc.


@dataclass
class ExorciseStatement(Statement):
    curse_name: str = ""


# --- Insanity ---

@dataclass
class IAmOkayStatement(Statement):
    pass


# --- Emotional shortcuts ---

@dataclass
class ForgetsEveryone(Statement):
    variable: str = ""


@dataclass
class DeleteStatement(Statement):
    variable: str = ""


# --- Console IO ---

@dataclass
class AskExpr(Expression):
    """ask("prompt") — read a line from stdin."""
    prompt: Expression = field(default_factory=Expression)


@dataclass
class ListenExpr(Expression):
    """listen() — read all stdin lines."""
    pass


@dataclass
class ShoutStatement(Statement):
    """shout(expr) — print ALL CAPS to stdout, -2 SP."""
    expression: Expression = field(default_factory=Expression)


@dataclass
class WhisperStatement(Statement):
    """whisper(expr) — print to stderr. ROT13 if Paranoid."""
    expression: Expression = field(default_factory=Expression)


# --- Filesystem IO ---

@dataclass
class OpenStatement(Statement):
    """open "path" as name."""
    path: Expression = field(default_factory=Expression)
    handle_name: str = ""


@dataclass
class ReadExpr(Expression):
    """read handle — returns file content as Word."""
    handle_name: str = ""


@dataclass
class WriteStatement(Statement):
    """write expr to handle."""
    content: Expression = field(default_factory=Expression)
    handle_name: str = ""


@dataclass
class AppendStatement(Statement):
    """append expr to handle."""
    content: Expression = field(default_factory=Expression)
    handle_name: str = ""


@dataclass
class CloseStatement(Statement):
    """close handle."""
    handle_name: str = ""


# --- Graphics ---

@dataclass
class CanvasExpr(Expression):
    """canvas("title", width, height) — creates a canvas."""
    title: Expression = field(default_factory=Expression)
    width: Expression = field(default_factory=Expression)
    height: Expression = field(default_factory=Expression)


# --- Call Management ---

@dataclass
class ForgetCallsStatement(Statement):
    """forget calls on func — resets call counter."""
    function_name: str = ""
