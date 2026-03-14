"""
solescript_parser.py
====================
Pure-Python implementation of the SoleScript DSL parser.

Architecture mirrors what ANTLR4 would auto-generate from SoleScript.g4:

  Lexer   (SoleScriptLexer)   – tokenises source text
  Parser  (SoleScriptParser)  – recursive-descent, one method per grammar rule
  AST     (Node hierarchy)    – typed dataclass nodes
  Visitor (ASTVisitor)        – base visitor / pretty-printer
  Semantic (SemanticAnalyzer) – enforces SR1-SR9

Usage
-----
    python solescript_parser.py              # runs built-in demo program
    python solescript_parser.py file.sole    # parses an external file

Requirements: Python 3.9+ (stdlib only – no ANTLR runtime needed here).
When the ANTLR4 tool + runtime ARE available you can instead run:

    java -jar antlr-4.x-complete.jar -Dlanguage=Python3 -visitor SoleScript.g4
    pip install antlr4-python3-runtime==4.x
    # then use the generated Lexer/Parser classes directly.
"""

from __future__ import annotations
import math
import re
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Any


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  TOKEN TYPES  (mirrors ANTLR token vocabulary)
# ═══════════════════════════════════════════════════════════════════════════════

class TT(Enum):
    # Block-structure keywords (G3-G7)
    FOOT         = auto()
    OBSERVATIONS = auto()
    LAST         = auto()
    BOOT         = auto()
    EXPORT       = auto()
    # Shoe-component keywords (G10)
    VAMP         = auto()
    TONGUE       = auto()
    QUARTER      = auto()   # "Quarter" optionally followed by a digit
    TOEBOX       = auto()
    OUTSOLE      = auto()
    HEEL         = auto()
    SHANK        = auto()
    INSOLE       = auto()
    COUNTER      = auto()
    LINING       = auto()
    # Keyword-values (G16)
    DIABETIC     = auto()
    EGYPTIAN     = auto()
    GREEK        = auto()
    ROMAN        = auto()
    CELTIC       = auto()
    GERMANIC     = auto()
    SQUARE       = auto()
    PEASANT      = auto()
    # Literals
    NUMBER       = auto()   # G13
    UNIT         = auto()   # 'mm' | 'cm'
    STRING       = auto()   # G15
    ID           = auto()   # G12
    # Punctuation
    LBRACE       = auto()
    RBRACE       = auto()
    LBRACKET     = auto()
    RBRACKET     = auto()
    COLON        = auto()
    COMMA        = auto()
    # Meta
    EOF          = auto()


# Keyword look-up table (all case-sensitive per Lexical Rules)
_KEYWORDS: dict[str, TT] = {
    "Foot":         TT.FOOT,
    "Observations": TT.OBSERVATIONS,
    "Last":         TT.LAST,
    "Boot":         TT.BOOT,
    "Export":       TT.EXPORT,
    "Vamp":         TT.VAMP,
    "Tongue":       TT.TONGUE,
    "ToeBox":       TT.TOEBOX,
    "Outsole":      TT.OUTSOLE,
    "Heel":         TT.HEEL,
    "Shank":        TT.SHANK,
    "Insole":       TT.INSOLE,
    "Counter":      TT.COUNTER,
    "Lining":       TT.LINING,
    "Diabetic":     TT.DIABETIC,
    "Egyptian":     TT.EGYPTIAN,
    "Greek":        TT.GREEK,
    "Roman":        TT.ROMAN,
    "Celtic":       TT.CELTIC,
    "Germanic":     TT.GERMANIC,
    "Square":       TT.SQUARE,
    "Peasant":      TT.PEASANT,
}

_SHOE_COMP_TYPES = {
    TT.VAMP, TT.TONGUE, TT.QUARTER, TT.TOEBOX,
    TT.OUTSOLE, TT.HEEL, TT.SHANK, TT.INSOLE, TT.COUNTER, TT.LINING,
}

_KEYWORD_VAL_TYPES = {
    TT.DIABETIC, TT.EGYPTIAN, TT.GREEK, TT.ROMAN,
    TT.CELTIC, TT.GERMANIC, TT.SQUARE, TT.PEASANT,
}


@dataclass
class Token:
    type:  TT
    value: str
    line:  int
    col:   int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  LEXER  (SoleScriptLexer)
# ═══════════════════════════════════════════════════════════════════════════════

class LexerError(Exception):
    pass


class SoleScriptLexer:
    """
    Hand-written lexer that tokenises SoleScript source text.
    Mirrors the ANTLR-generated Lexer class.
    """

    def __init__(self, source: str) -> None:
        self._src  = source
        self._pos  = 0
        self._line = 1
        self._col  = 1
        self._tokens: list[Token] = []
        self._tokenise()

    # ------------------------------------------------------------------
    # Public interface (same as ANTLR CommonTokenStream)
    # ------------------------------------------------------------------

    def get_all_tokens(self) -> list[Token]:
        return self._tokens

    # ------------------------------------------------------------------
    # Internal tokenisation
    # ------------------------------------------------------------------

    def _tokenise(self) -> None:
        while self._pos < len(self._src):
            self._skip_whitespace_and_comments()
            if self._pos >= len(self._src):
                break

            ch = self._src[self._pos]

            # --- Single-char punctuation ---
            punct = {'{': TT.LBRACE, '}': TT.RBRACE,
                     '[': TT.LBRACKET, ']': TT.RBRACKET,
                     ':': TT.COLON,   ',': TT.COMMA}
            if ch in punct:
                self._tokens.append(Token(punct[ch], ch, self._line, self._col))
                self._advance()
                continue

            # --- String literal (G15) ---
            if ch == '"':
                self._tokens.append(self._read_string())
                continue

            # --- Number (G13 / G14) ---
            if ch.isdigit():
                self._tokens.append(self._read_number())
                continue

            # --- Identifier / keyword (G12) ---
            if ch.isalpha() or ch == '_':
                self._tokens.append(self._read_word())
                continue

            raise LexerError(
                f"Unexpected character {ch!r} at line {self._line}, col {self._col}"
            )

        self._tokens.append(Token(TT.EOF, "", self._line, self._col))

    def _skip_whitespace_and_comments(self) -> None:
        while self._pos < len(self._src):
            ch = self._src[self._pos]
            if ch in (' ', '\t', '\r', '\n'):
                self._advance()
            elif self._src[self._pos:self._pos+2] == '//':
                while self._pos < len(self._src) and self._src[self._pos] != '\n':
                    self._advance()
            else:
                break

    def _advance(self, n: int = 1) -> None:
        for _ in range(n):
            if self._pos < len(self._src):
                if self._src[self._pos] == '\n':
                    self._line += 1
                    self._col   = 1
                else:
                    self._col += 1
                self._pos += 1

    def _read_string(self) -> Token:
        """G15: '"' (any char except '"')* '"' """
        start_line, start_col = self._line, self._col
        self._advance()  # consume opening "
        buf = ['"']
        while self._pos < len(self._src) and self._src[self._pos] != '"':
            buf.append(self._src[self._pos])
            self._advance()
        if self._pos >= len(self._src):
            raise LexerError(f"Unterminated string at line {start_line}")
        buf.append('"')
        self._advance()  # consume closing "
        return Token(TT.STRING, "".join(buf), start_line, start_col)

    def _read_number(self) -> Token:
        """G13: digit+ ('.' digit+)? """
        start_line, start_col = self._line, self._col
        buf = []
        while self._pos < len(self._src) and self._src[self._pos].isdigit():
            buf.append(self._src[self._pos])
            self._advance()
        if (self._pos < len(self._src) and self._src[self._pos] == '.'
                and self._pos+1 < len(self._src) and self._src[self._pos+1].isdigit()):
            buf.append('.')
            self._advance()
            while self._pos < len(self._src) and self._src[self._pos].isdigit():
                buf.append(self._src[self._pos])
                self._advance()
        return Token(TT.NUMBER, "".join(buf), start_line, start_col)

    def _read_word(self) -> Token:
        """G12 / keywords / units.  Also handles 'Quarter 1' multi-word token."""
        start_line, start_col = self._line, self._col
        buf = []
        while self._pos < len(self._src) and (self._src[self._pos].isalnum()
                                               or self._src[self._pos] == '_'):
            buf.append(self._src[self._pos])
            self._advance()
        word = "".join(buf)

        # Unit check first (so 'mm'/'cm' don't match as IDs)
        if word in ('mm', 'cm'):
            return Token(TT.UNIT, word, start_line, start_col)

        # Quarter can be followed by optional whitespace + digit  e.g. "Quarter 1"
        if word == 'Quarter':
            saved_pos, saved_line, saved_col = self._pos, self._line, self._col
            # skip spaces
            while self._pos < len(self._src) and self._src[self._pos] == ' ':
                self._advance()
            if self._pos < len(self._src) and self._src[self._pos].isdigit():
                digit = self._src[self._pos]
                self._advance()
                return Token(TT.QUARTER, f"Quarter {digit}", start_line, start_col)
            else:
                # restore position, plain 'Quarter'
                self._pos, self._line, self._col = saved_pos, saved_line, saved_col
                return Token(TT.QUARTER, word, start_line, start_col)

        tt = _KEYWORDS.get(word, TT.ID)
        return Token(tt, word, start_line, start_col)


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  AST NODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ProgramNode:
    statements: List[Any]  # list of *Decl nodes

@dataclass
class FootDeclNode:
    name:      str
    attr_list: List["AttrEntryNode"]

@dataclass
class ObsDeclNode:
    name:      str
    attr_list: List["AttrEntryNode"]

@dataclass
class LastDeclNode:
    name:      str
    attr_list: List["AttrEntryNode"]

@dataclass
class BootDeclNode:
    name:      str
    attr_list: List["AttrEntryNode"]
    comp_list: List["CompEntryNode"]

@dataclass
class ExportDeclNode:
    name: str

@dataclass
class AttrEntryNode:
    key:   str
    value: Any   # DimensionValueNode | IdValueNode | StringListValueNode | KeywordValueNode

@dataclass
class CompEntryNode:
    component: str   # e.g. "Vamp", "Quarter 1"

@dataclass
class DimensionValueNode:
    number: float
    unit:   str   # 'mm' or 'cm'

@dataclass
class IdValueNode:
    name: str

@dataclass
class StringListValueNode:
    values: List[str]   # raw string contents (without quotes)

@dataclass
class KeywordValueNode:
    keyword: str   # e.g. "Diabetic", "Egyptian"


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  PARSER  (SoleScriptParser)
# ═══════════════════════════════════════════════════════════════════════════════

class ParseError(Exception):
    pass


class SoleScriptParser:
    """
    Recursive-descent parser.  One method per grammar rule (G1-G16).
    Mirrors the structure of an ANTLR-generated Parser class.
    """

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos    = 0

    # ------------------------------------------------------------------
    # Token-stream helpers (mirrors ANTLR TokenStream API)
    # ------------------------------------------------------------------

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _peek(self, offset: int = 1) -> Token:
        idx = self._pos + offset
        if idx < len(self._tokens):
            return self._tokens[idx]
        return self._tokens[-1]  # EOF

    def _consume(self, expected: TT | None = None) -> Token:
        tok = self._current()
        if expected is not None and tok.type != expected:
            raise ParseError(
                f"Line {tok.line}:{tok.col}  "
                f"Expected {expected.name} but got {tok.type.name} ({tok.value!r})"
            )
        self._pos += 1
        return tok

    def _match(self, *types: TT) -> bool:
        return self._current().type in types

    # ------------------------------------------------------------------
    # G1: program → statement*
    # ------------------------------------------------------------------

    def parse_program(self) -> ProgramNode:
        stmts = []
        while not self._match(TT.EOF):
            stmts.append(self._parse_statement())
        self._consume(TT.EOF)
        return ProgramNode(statements=stmts)

    # ------------------------------------------------------------------
    # G2: statement → foot_decl | obs_decl | last_decl | boot_decl | export_decl
    # ------------------------------------------------------------------

    def _parse_statement(self) -> Any:
        tt = self._current().type
        if tt == TT.FOOT:
            return self._parse_foot_decl()
        elif tt == TT.OBSERVATIONS:
            return self._parse_obs_decl()
        elif tt == TT.LAST:
            return self._parse_last_decl()
        elif tt == TT.BOOT:
            return self._parse_boot_decl()
        elif tt == TT.EXPORT:
            return self._parse_export_decl()
        else:
            tok = self._current()
            raise ParseError(
                f"Line {tok.line}:{tok.col}  "
                f"Expected statement keyword (Foot/Observations/Last/Boot/Export) "
                f"but got {tok.type.name} ({tok.value!r})"
            )

    # ------------------------------------------------------------------
    # G3: foot_decl → Foot id '{' attr_list '}'
    # ------------------------------------------------------------------

    def _parse_foot_decl(self) -> FootDeclNode:
        self._consume(TT.FOOT)
        name      = self._parse_id()
        self._consume(TT.LBRACE)
        attr_list = self._parse_attr_list()
        self._consume(TT.RBRACE)
        return FootDeclNode(name=name, attr_list=attr_list)

    # ------------------------------------------------------------------
    # G4: obs_decl → Observations id '{' attr_list '}'
    # ------------------------------------------------------------------

    def _parse_obs_decl(self) -> ObsDeclNode:
        self._consume(TT.OBSERVATIONS)
        name      = self._parse_id()
        self._consume(TT.LBRACE)
        attr_list = self._parse_attr_list()
        self._consume(TT.RBRACE)
        return ObsDeclNode(name=name, attr_list=attr_list)

    # ------------------------------------------------------------------
    # G5: last_decl → Last id '{' attr_list '}'
    # ------------------------------------------------------------------

    def _parse_last_decl(self) -> LastDeclNode:
        self._consume(TT.LAST)
        name      = self._parse_id()
        self._consume(TT.LBRACE)
        attr_list = self._parse_attr_list()
        self._consume(TT.RBRACE)
        return LastDeclNode(name=name, attr_list=attr_list)

    # ------------------------------------------------------------------
    # G6: boot_decl → Boot id '{' attr_list comp_list '}'
    # ------------------------------------------------------------------

    def _parse_boot_decl(self) -> BootDeclNode:
        self._consume(TT.BOOT)
        name      = self._parse_id()
        self._consume(TT.LBRACE)
        attr_list = self._parse_attr_list()
        comp_list = self._parse_comp_list()
        self._consume(TT.RBRACE)
        return BootDeclNode(name=name, attr_list=attr_list, comp_list=comp_list)

    # ------------------------------------------------------------------
    # G7: export_decl → Export id
    # ------------------------------------------------------------------

    def _parse_export_decl(self) -> ExportDeclNode:
        self._consume(TT.EXPORT)
        name = self._parse_id()
        return ExportDeclNode(name=name)

    # ------------------------------------------------------------------
    # G8: attr_list → (id ':' value)*
    # ------------------------------------------------------------------

    def _parse_attr_list(self) -> list[AttrEntryNode]:
        entries = []
        # attr entries start with an ID; stop when we see '}' or a shoe_comp
        while (self._current().type == TT.ID
               and not self._current().type in _SHOE_COMP_TYPES):
            entries.append(self._parse_attr_entry())
        return entries

    def _parse_attr_entry(self) -> AttrEntryNode:
        key = self._parse_id()
        self._consume(TT.COLON)
        val = self._parse_value()
        return AttrEntryNode(key=key, value=val)

    # ------------------------------------------------------------------
    # G9: comp_list → (shoe_comp '{' '}')*
    # ------------------------------------------------------------------

    def _parse_comp_list(self) -> list[CompEntryNode]:
        entries = []
        while self._current().type in _SHOE_COMP_TYPES:
            entries.append(self._parse_comp_entry())
        return entries

    def _parse_comp_entry(self) -> CompEntryNode:
        comp = self._parse_shoe_comp()
        self._consume(TT.LBRACE)
        self._consume(TT.RBRACE)
        return CompEntryNode(component=comp)

    # ------------------------------------------------------------------
    # G10: shoe_comp → Vamp | Tongue | Quarter | ToeBox | Outsole | Heel | …
    # ------------------------------------------------------------------

    def _parse_shoe_comp(self) -> str:
        tok = self._current()
        if tok.type in _SHOE_COMP_TYPES:
            self._pos += 1
            return tok.value
        raise ParseError(
            f"Line {tok.line}:{tok.col}  "
            f"Expected shoe component keyword, got {tok.type.name} ({tok.value!r})"
        )

    # ------------------------------------------------------------------
    # G11: value → number unit | id | '[' string+ ']' | keyword_val
    # ------------------------------------------------------------------

    def _parse_value(self) -> Any:
        tt = self._current().type

        # alt 1: dimension  → number unit
        if tt == TT.NUMBER:
            return self._parse_dimension_value()

        # alt 3: string list  → '[' string+ ']'
        if tt == TT.LBRACKET:
            return self._parse_string_list_value()

        # alt 4: keyword_val
        if tt in _KEYWORD_VAL_TYPES:
            kw = self._consume().value
            return KeywordValueNode(keyword=kw)

        # alt 2: identifier reference
        if tt == TT.ID:
            name = self._parse_id()
            return IdValueNode(name=name)

        tok = self._current()
        raise ParseError(
            f"Line {tok.line}:{tok.col}  "
            f"Expected a value (number, id, string list, or keyword), "
            f"got {tok.type.name} ({tok.value!r})"
        )

    def _parse_dimension_value(self) -> DimensionValueNode:
        num_tok  = self._consume(TT.NUMBER)
        unit_tok = self._consume(TT.UNIT)
        return DimensionValueNode(number=float(num_tok.value), unit=unit_tok.value)

    def _parse_string_list_value(self) -> StringListValueNode:
        self._consume(TT.LBRACKET)
        strings = []
        # G11 requires at least one string
        strings.append(self._parse_string())
        while self._match(TT.COMMA):
            self._consume(TT.COMMA)
            strings.append(self._parse_string())
        # also allow space-separated strings (no comma) per G11
        while self._match(TT.STRING):
            strings.append(self._parse_string())
        self._consume(TT.RBRACKET)
        return StringListValueNode(values=strings)

    def _parse_string(self) -> str:
        tok = self._consume(TT.STRING)
        # strip surrounding quotes
        return tok.value[1:-1]

    # ------------------------------------------------------------------
    # G12: id  (the lexer already produced a TT.ID token)
    # ------------------------------------------------------------------

    def _parse_id(self) -> str:
        tok = self._consume(TT.ID)
        return tok.value

    # G13/G14 handled inside _parse_dimension_value via NUMBER token


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  VISITOR BASE  (mirrors ANTLR-generated visitor)
# ═══════════════════════════════════════════════════════════════════════════════

class ASTVisitor:
    """Base visitor.  Override the visit_* methods you care about."""

    def visit(self, node: Any) -> Any:
        method = f"visit_{type(node).__name__}"
        return getattr(self, method, self.generic_visit)(node)

    def generic_visit(self, node: Any) -> None:
        pass

    def visit_ProgramNode(self, node: ProgramNode) -> None:
        for stmt in node.statements:
            self.visit(stmt)

    def visit_FootDeclNode(self, node: FootDeclNode) -> None:
        for e in node.attr_list: self.visit(e)

    def visit_ObsDeclNode(self, node: ObsDeclNode) -> None:
        for e in node.attr_list: self.visit(e)

    def visit_LastDeclNode(self, node: LastDeclNode) -> None:
        for e in node.attr_list: self.visit(e)

    def visit_BootDeclNode(self, node: BootDeclNode) -> None:
        for e in node.attr_list: self.visit(e)
        for c in node.comp_list: self.visit(c)

    def visit_ExportDeclNode(self, node: ExportDeclNode) -> None:
        pass

    def visit_AttrEntryNode(self, node: AttrEntryNode) -> None:
        self.visit(node.value)

    def visit_CompEntryNode(self, node: CompEntryNode) -> None:
        pass

    def visit_DimensionValueNode(self, node: DimensionValueNode) -> None:
        pass

    def visit_IdValueNode(self, node: IdValueNode) -> None:
        pass

    def visit_StringListValueNode(self, node: StringListValueNode) -> None:
        pass

    def visit_KeywordValueNode(self, node: KeywordValueNode) -> None:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  PRETTY-PRINTER  (concrete visitor)
# ═══════════════════════════════════════════════════════════════════════════════

class ASTPrinter(ASTVisitor):
    """Prints the AST as an indented tree (for debugging / educational output)."""

    def __init__(self) -> None:
        self._indent = 0

    def _p(self, text: str) -> None:
        print("  " * self._indent + text)

    def _indented(self, fn):
        self._indent += 1
        fn()
        self._indent -= 1

    def visit_ProgramNode(self, node: ProgramNode) -> None:
        self._p("⟨program⟩")
        self._indented(lambda: [self.visit(s) for s in node.statements])

    def visit_FootDeclNode(self, node: FootDeclNode) -> None:
        self._p(f"⟨foot_decl⟩  Foot {node.name}")
        self._indented(lambda: [self.visit(e) for e in node.attr_list])

    def visit_ObsDeclNode(self, node: ObsDeclNode) -> None:
        self._p(f"⟨obs_decl⟩  Observations {node.name}")
        self._indented(lambda: [self.visit(e) for e in node.attr_list])

    def visit_LastDeclNode(self, node: LastDeclNode) -> None:
        self._p(f"⟨last_decl⟩  Last {node.name}")
        self._indented(lambda: [self.visit(e) for e in node.attr_list])

    def visit_BootDeclNode(self, node: BootDeclNode) -> None:
        self._p(f"⟨boot_decl⟩  Boot {node.name}")
        self._indented(lambda: (
            [self.visit(e) for e in node.attr_list],
            [self.visit(c) for c in node.comp_list],
        ))

    def visit_ExportDeclNode(self, node: ExportDeclNode) -> None:
        self._p(f"⟨export_decl⟩  Export {node.name}")

    def visit_AttrEntryNode(self, node: AttrEntryNode) -> None:
        self._p(f"⟨attr_entry⟩  {node.key} :")
        self._indented(lambda: self.visit(node.value))

    def visit_CompEntryNode(self, node: CompEntryNode) -> None:
        self._p(f"⟨comp_entry⟩  {node.component} {{ }}")

    def visit_DimensionValueNode(self, node: DimensionValueNode) -> None:
        self._p(f"⟨value:dimension⟩  {node.number} {node.unit}")

    def visit_IdValueNode(self, node: IdValueNode) -> None:
        self._p(f"⟨value:id⟩  {node.name}")

    def visit_StringListValueNode(self, node: StringListValueNode) -> None:
        self._p(f"⟨value:string_list⟩  {node.values}")

    def visit_KeywordValueNode(self, node: KeywordValueNode) -> None:
        self._p(f"⟨value:keyword⟩  {node.keyword}")


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  SEMANTIC ANALYSER  (SR1-SR9 from the spec)
# ═══════════════════════════════════════════════════════════════════════════════

class SemanticError(Exception):
    pass


class SemanticAnalyzer(ASTVisitor):
    """
    Enforces static semantic rules SR1-SR9.
    Run after a successful parse:   SemanticAnalyzer().check(ast)
    """

    def __init__(self) -> None:
        # symbol table: name → node type (string)
        self._declared: dict[str, str] = {}
        self._errors:   list[str]      = []
        self._context:  str            = ""   # current block type

    def check(self, tree: ProgramNode) -> list[str]:
        """Returns list of semantic error messages (empty = valid)."""
        self._declared.clear()
        self._errors.clear()
        # First pass: collect all declarations (for forward-ref check)
        for stmt in tree.statements:
            self._register(stmt)
        # Second pass: validate references and constraints
        self.visit(tree)
        return self._errors

    def _register(self, stmt: Any) -> None:
        """SR1: Unique Declaration.  Export is a reference, not a new declaration."""
        if isinstance(stmt, ExportDeclNode):
            return   # not a declaration — SR2 handles the reference check
        name = getattr(stmt, "name", None)
        if name is None:
            return
        node_type = type(stmt).__name__
        if name in self._declared:
            self._errors.append(
                f"SR1 (UniqueDeclaration): '{name}' is already declared "
                f"(as {self._declared[name]})."
            )
        else:
            self._declared[name] = node_type

    # --- Visitors ---

    def visit_FootDeclNode(self, node: FootDeclNode) -> None:
        self._context = "foot"
        keys = {e.key for e in node.attr_list}
        # SR5: Mandatory parameters
        for mandatory in ("length", "ball_girth"):
            if mandatory not in keys:
                self._errors.append(
                    f"SR5 (MandatoryParameters): foot '{node.name}' "
                    f"is missing mandatory attribute '{mandatory}'."
                )
        for e in node.attr_list:
            self.visit(e)

    def visit_ObsDeclNode(self, node: ObsDeclNode) -> None:
        self._context = "obs"
        # SR6: Conflicting conditions
        conditions = [
            e.value.keyword
            for e in node.attr_list
            if e.key == "condition"
            and isinstance(e.value, KeywordValueNode)
        ]
        exclusive = {"Egyptian", "Greek", "Roman", "Celtic", "Germanic", "Square", "Peasant"}
        found = [c for c in conditions if c in exclusive]
        if len(found) > 1:
            self._errors.append(
                f"SR6 (ConditionExclusivity): observation '{node.name}' "
                f"has conflicting foot-shape conditions: {found}."
            )
        for e in node.attr_list:
            self.visit(e)

    def visit_LastDeclNode(self, node: LastDeclNode) -> None:
        self._context = "last"
        for e in node.attr_list:
            # SR8: Self-reference prohibition
            if isinstance(e.value, IdValueNode) and e.value.name == node.name:
                self._errors.append(
                    f"SR8 (SelfRefProhibition): last '{node.name}' "
                    f"references itself in attribute '{e.key}'."
                )
            self.visit(e)

    def visit_BootDeclNode(self, node: BootDeclNode) -> None:
        self._context = "boot"
        for e in node.attr_list:
            # SR9: boot must reference a declared last_decl
            if e.key == "reference_last" and isinstance(e.value, IdValueNode):
                ref = e.value.name
                decl_type = self._declared.get(ref)
                if decl_type != "LastDeclNode":
                    self._errors.append(
                        f"SR9 (DependencyResolution): boot '{node.name}' references "
                        f"'{ref}' which is not a validated Last declaration "
                        f"(found: {decl_type or 'undefined'})."
                    )
            self.visit(e)
        for c in node.comp_list:
            self.visit(c)

    def visit_AttrEntryNode(self, node: AttrEntryNode) -> None:
        val = node.value
        # SR2: Reference integrity for id values
        if isinstance(val, IdValueNode):
            ref = val.name
            if ref not in self._declared:
                self._errors.append(
                    f"SR2 (ReferenceIntegrity): attribute '{node.key}' references "
                    f"undeclared identifier '{ref}'."
                )
        # SR3: Measurement positivity
        if isinstance(val, DimensionValueNode):
            if val.number <= 0:
                self._errors.append(
                    f"SR3 (MeasurementPositivity): attribute '{node.key}' "
                    f"has non-positive value {val.number} {val.unit}."
                )
        # SR4: pressure_points must be string list
        if node.key == "pressure_points" and not isinstance(val, StringListValueNode):
            self._errors.append(
                f"SR4 (TypeMatching): 'pressure_points' must be a string list, "
                f"got {type(val).__name__}."
            )

    def visit_CompEntryNode(self, node: CompEntryNode) -> None:
        # SR7: components are only valid inside boot_decl — enforced structurally
        # by the parser; nothing extra needed here.
        pass

    def visit_ExportDeclNode(self, node: ExportDeclNode) -> None:
        # SR2: export target must be a declared boot_decl
        decl_type = self._declared.get(node.name)
        if decl_type != "BootDeclNode":
            self._errors.append(
                f"SR2 (ReferenceIntegrity): Export target '{node.name}' "
                f"is not a declared Boot (found: {decl_type or 'undefined'})."
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 8.  PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def parse(source: str) -> tuple[ProgramNode, list[str]]:
    """
    Lex + parse + semantic-analyse a SoleScript source string.

    Returns
    -------
    (ast, errors)
        ast    – ProgramNode (even on semantic errors)
        errors – list of SemanticError messages; empty means fully valid
    Raises LexerError or ParseError on syntax problems.
    """
    lexer  = SoleScriptLexer(source)
    tokens = lexer.get_all_tokens()
    parser = SoleScriptParser(tokens)
    ast    = parser.parse_program()
    errors = SemanticAnalyzer().check(ast)
    return ast, errors


# ═══════════════════════════════════════════════════════════════════════════════
# 9.  CLI / DEMO
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# 10.  INTERPRETER
# ═══════════════════════════════════════════════════════════════════════════════

class Interpreter(ASTVisitor):
    """
    Concrete visitor that walks the validated AST, resolves cross-references
    into runtime Python dicts, and triggers pattern generation on Export.
    """

    def __init__(self) -> None:
        self._env: dict = {}
        self._output_stem: str = "export"

    def run(self, tree: ProgramNode, output_stem: str = "export") -> None:
        """Execute the full program AST.  Must be called after SemanticAnalyzer passes."""
        self._output_stem = output_stem
        self.visit(tree)

    # ------------------------------------------------------------------
    # Value evaluation helpers
    # ------------------------------------------------------------------

    def _eval(self, value: Any) -> Any:
        if isinstance(value, DimensionValueNode):
            return value.number * (10.0 if value.unit == "cm" else 1.0)
        if isinstance(value, IdValueNode):
            return self._env.get(value.name, value.name)
        if isinstance(value, StringListValueNode):
            return list(value.values)
        if isinstance(value, KeywordValueNode):
            return value.keyword
        return None

    def _eval_attrs(self, attr_list: list) -> dict:
        return {e.key: self._eval(e.value) for e in attr_list}

    # ------------------------------------------------------------------
    # Declaration visitors — populate _env
    # ------------------------------------------------------------------

    def visit_FootDeclNode(self, node: FootDeclNode) -> None:
        obj = self._eval_attrs(node.attr_list)
        obj["__type__"] = "Foot"
        self._env[node.name] = obj

    def visit_ObsDeclNode(self, node: ObsDeclNode) -> None:
        obj = self._eval_attrs(node.attr_list)
        obj["__type__"] = "Observations"
        self._env[node.name] = obj

    def visit_LastDeclNode(self, node: LastDeclNode) -> None:
        obj = self._eval_attrs(node.attr_list)
        obj["__type__"] = "Last"
        self._env[node.name] = obj

    def visit_BootDeclNode(self, node: BootDeclNode) -> None:
        obj = self._eval_attrs(node.attr_list)
        obj["__type__"] = "Boot"
        obj["components"] = [c.component for c in node.comp_list]
        self._env[node.name] = obj

    # ------------------------------------------------------------------
    # Export visitor — trigger backend
    # ------------------------------------------------------------------

    def visit_ExportDeclNode(self, node: ExportDeclNode) -> None:
        boot = self._env.get(node.name)
        if not isinstance(boot, dict):
            raise RuntimeError(f"Export: '{node.name}' not found in environment.")
        # Resolve reference chain:  Boot → Last → Foot
        last_ref = boot.get("reference_last")
        last = (self._env.get(last_ref, {})
                if isinstance(last_ref, str) else (last_ref or {}))
        foot_ref = last.get("reference_foot")
        foot = (self._env.get(foot_ref, {})
                if isinstance(foot_ref, str) else (foot_ref or {}))

        gen      = PatternGenerator(foot, last, boot)
        patterns = gen.generate()

        out_path = f"{self._output_stem}_patterns.svg"
        SVGExporter.export(patterns, out_path, foot, last, node.name)
        print(f"  \u2713  {len(patterns)} pattern(s) written \u2192 '{out_path}'")


# ═══════════════════════════════════════════════════════════════════════════════
# 11.  PATTERN GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class PatternGenerator:
    """
    Computes approximate 2-D flat-pattern polygons for every shoe component
    declared in a Boot block.

    Coordinate system (all values in mm):
        Origin  = heel centre, posterior end
        +X      = towards toe (anterior)
        +Y      = lateral (outer / fibular) side
        -Y      = medial (inner / tibial / arch) side
    """

    def __init__(self, foot: dict, last: dict, boot: dict) -> None:
        self.L   = float(foot.get("length",        260.0))
        self.W   = float(foot.get("width",           95.0))   # full width at ball
        self.HW  = float(foot.get("heel_width",      60.0))   # full heel width
        self.AH  = float(foot.get("arch_height",     15.0))
        self.HH  = float(last.get("heel_height",     20.0))
        self.TS  = float(last.get("toe_spring",       8.0))
        self.WF  = float(last.get("width_fitting",  self.W))
        self.components: List[str] = boot.get("components", [])
        self._bx: float = 0.59 * self.L   # ball-of-foot X position

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def generate(self) -> dict:
        """Return {component_name: [(x, y), ...]} for every declared component."""
        dispatch = {
            "Outsole": self._outsole,
            "Insole":  self._insole,
            "Lining":  self._lining,
            "Shank":   self._shank,
            "Heel":    self._heel_block,
            "Counter": self._counter,
            "ToeBox":  self._toebox,
            "Vamp":    self._vamp,
            "Tongue":  self._tongue,
        }
        patterns: dict = {}
        for comp in self.components:
            base = comp.split()[0]
            if base == "Quarter":
                num = int(comp.split()[1]) if len(comp.split()) > 1 else 1
                patterns[comp] = self._quarter(num)
            elif base in dispatch:
                patterns[comp] = dispatch[base]()
        return patterns

    # ------------------------------------------------------------------
    # Shared plantar foot outline
    # ------------------------------------------------------------------

    def _foot_pts(self, inset: float = 0.0) -> List[tuple]:
        """
        Approximate plantar footprint polygon.
        inset > 0  ->  smaller (e.g. insole),  inset < 0  ->  larger (e.g. outsole border).
        """
        L  = self.L
        W  = self.W  / 2 - inset
        HW = self.HW / 2 - inset
        bx = self._bx
        right_side = [
            (L,       +W  * 0.12),
            (0.87*L,  +W  * 0.60),
            (0.72*L,  +W  * 0.90),
            (bx,      +W        ),
            (0.25*L,  +W  * 0.82),
            (0.08*L,  +HW * 1.35),
            (0.0,     +HW       ),
        ]
        heel_arc = [
            (-0.04*L, +HW * 0.55),
            (-0.05*L,  0.0      ),
            (-0.04*L, -HW * 0.55),
        ]
        left_side = [
            (0.0,     -HW       ),
            (0.08*L,  -HW * 1.20),
            (0.20*L,  -W  * 0.48),
            (0.42*L,  -W  * 0.32),
            (bx,      -W  * 0.88),
            (0.92*L,  -W  * 0.28),
        ]
        return right_side + heel_arc + left_side

    # ------------------------------------------------------------------
    # Component generators
    # ------------------------------------------------------------------

    def _outsole(self) -> List[tuple]:
        return self._foot_pts(inset=-3.0)

    def _insole(self) -> List[tuple]:
        return self._foot_pts(inset=2.0)

    def _lining(self) -> List[tuple]:
        return self._foot_pts(inset=4.5)

    def _shank(self) -> List[tuple]:
        """Narrow arch-support plate from heel to ball."""
        bx = self._bx
        hw = 11.0
        return [
            (0.0,  -hw       ),
            (bx,   -hw * 0.6 ),
            (bx,   +hw * 0.6 ),
            (0.0,  +hw       ),
        ]

    def _heel_block(self) -> List[tuple]:
        """Heel block developed flat as a rectangle."""
        w = self.HW * 1.15
        d = self.L  * 0.30
        return [
            (0.0, 0.0),
            (d,   0.0),
            (d,   w  ),
            (0.0, w  ),
        ]

    def _counter(self) -> List[tuple]:
        """Heel counter stiffener — asymmetric trapezoid developed flat."""
        HW = self.HW
        lh = self.HH * 0.85
        mh = self.HH * 0.95
        d  = self.L  * 0.28
        return [
            ( 0.0,  0.0      ),
            ( d,    0.0      ),
            ( d,    HW * 0.5 ),
            ( 0.0,  HW       ),
            (-lh,   HW       ),
            (-mh,   HW * 0.5 ),
            (-lh,   0.0      ),
        ]

    def _toebox(self) -> List[tuple]:
        """Toe cap — oval strip over the toe area."""
        W  = self.W
        bx = self._bx
        L  = self.L
        hw = W  * 0.52
        d  = (L - bx) * 0.80 + self.TS
        th = 16.0
        return [
            (0.0,      -hw        ),
            (d,        -hw * 0.50 ),
            (d + th,    0.0       ),
            (d,        +hw * 0.50 ),
            (0.0,      +hw        ),
        ]

    def _vamp(self) -> List[tuple]:
        """Main front upper panel — trapezoidal flat development."""
        bx = self._bx
        W  = self.W
        th = W  * 0.42
        bh = W  * 0.56
        h  = bx * 0.68
        return [
            (0.0, -th),
            (0.0, +th),
            (h,   +bh),
            (h,   -bh),
        ]

    def _tongue(self) -> List[tuple]:
        """Tongue — tapered panel."""
        L   = self.L
        tw  = self.W  * 0.27
        th  = L       * 0.46
        tip = tw      * 0.55
        return [
            (0.0,  -tw / 2),
            (th,   -tip / 2),
            (th,   +tip / 2),
            (0.0,  +tw / 2),
        ]

    def _quarter(self, side: int = 1) -> List[tuple]:
        """
        Quarter side panel.  side=1 -> lateral,  side=2 -> medial.
        Trapezoid, developed flat.
        """
        L       = self.L
        bx      = self._bx
        HH      = self.HH
        h_back  = HH * 2.40
        h_front = HH * 1.30
        width   = L - bx + bx * 0.30
        return [
            (0.0,   0.0    ),
            (width, 0.0    ),
            (width, h_front),
            (0.0,   h_back ),
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# 12.  SVG EXPORTER
# ═══════════════════════════════════════════════════════════════════════════════

class SVGExporter:
    """Renders 2-D component patterns to an SVG file in a labelled grid layout."""

    COLS    = 3      # components per grid row
    PAD     = 20.0   # cell inner padding (mm, pre-scale)
    GAP     = 12.0   # gap between grid cells (px)
    SCALE   = 1.8    # mm -> SVG user units (px)
    TITLE_H = 22.0   # reserved height for component name label (px)

    @classmethod
    def export(
        cls,
        patterns: dict,
        path: str,
        foot: dict,
        last: dict,
        boot_name: str = "boot",
    ) -> None:
        S   = cls.SCALE
        PAD = cls.PAD * S
        GAP = cls.GAP
        TH  = cls.TITLE_H

        # --- normalise each polygon to (0, 0) origin and compute cell size ---
        cells: list = []
        for name, pts in patterns.items():
            if not pts:
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            minx, maxx = min(xs), max(xs)
            miny, maxy = min(ys), max(ys)
            norm = [((x - minx) * S, (y - miny) * S) for x, y in pts]
            cw   = (maxx - minx) * S + 2 * PAD
            ch   = (maxy - miny) * S + 2 * PAD + TH
            cells.append((name, norm, cw, ch))

        if not cells:
            print("  \u26a0  No patterns to export.")
            return

        cols = cls.COLS
        rows = (len(cells) + cols - 1) // cols

        col_ws = [0.0] * cols
        row_hs = [0.0] * rows
        for i, (_, _, cw, ch) in enumerate(cells):
            col_ws[i % cols]  = max(col_ws[i % cols],  cw)
            row_hs[i // cols] = max(row_hs[i // cols], ch)

        header = TH * 2.8
        svg_w  = sum(col_ws) + GAP * (cols + 1)
        svg_h  = sum(row_hs) + GAP * (rows + 1) + header

        out: list = []
        out.append('<?xml version="1.0" encoding="UTF-8"?>')
        out.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{svg_w:.1f}" height="{svg_h:.1f}" '
            f'viewBox="0 0 {svg_w:.1f} {svg_h:.1f}">'
        )
        out.append(
            '  <defs><style>'
            '.bg{fill:#f0f4f8}'
            '.cell{fill:#ffffff;stroke:#b0c4d8;stroke-width:1}'
            '.pat{fill:#d6eaf8;stroke:#1a5276;stroke-width:1.5;stroke-linejoin:round}'
            '.hdr{font:bold 15px sans-serif;fill:#1a5276}'
            '.meta{font:10px sans-serif;fill:#5d6d7e}'
            '.lbl{font:bold 11px sans-serif;fill:#2e4057}'
            '</style></defs>'
        )
        out.append(f'  <rect width="{svg_w:.1f}" height="{svg_h:.1f}" class="bg"/>')
        out.append(
            f'  <text x="{svg_w/2:.1f}" y="{TH:.1f}" '
            f'class="hdr" text-anchor="middle">'
            f'SoleScript \u25b8 {boot_name} \u2014 2D Component Patterns</text>'
        )
        meta = (
            f"length {foot.get('length', '?')} mm  \u00b7  "
            f"width {foot.get('width', '?')} mm  \u00b7  "
            f"ball\u00b7girth {foot.get('ball_girth', '?')} mm  \u00b7  "
            f"heel\u00b7height {last.get('heel_height', '?')} mm"
        )
        out.append(
            f'  <text x="{svg_w/2:.1f}" y="{TH*1.9:.1f}" '
            f'class="meta" text-anchor="middle">{meta}</text>'
        )

        for i, (name, pts, cw, ch) in enumerate(cells):
            c   = i % cols
            r   = i // cols
            cx  = GAP + sum(col_ws[:c]) + GAP * c
            cy  = header + GAP + sum(row_hs[:r]) + GAP * r
            ccw = col_ws[c]
            cch = row_hs[r]
            ox  = cx + PAD
            oy  = cy + PAD + TH
            out.append(
                f'  <rect x="{cx:.1f}" y="{cy:.1f}" '
                f'width="{ccw:.1f}" height="{cch:.1f}" rx="5" class="cell"/>'
            )
            out.append(
                f'  <text x="{cx + ccw/2:.1f}" y="{cy + TH*0.85:.1f}" '
                f'class="lbl" text-anchor="middle">{name}</text>'
            )
            pts_str = " ".join(f"{ox+px:.1f},{oy+py:.1f}" for px, py in pts)
            out.append(f'  <polygon points="{pts_str}" class="pat"/>')

        out.append("</svg>")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out))


# ═══════════════════════════════════════════════════════════════════════════════
# 9.  CLI / DEMO
# ═══════════════════════════════════════════════════════════════════════════════

_DEMO_PROGRAM = """\
// Step 1: patient foot measurements
Foot patient_foot {
    length     : 250 mm
    ball_girth : 240 mm
    width      : 95 mm
}

// Step 2: clinical observations
Observations clinical_obs {
    condition       : Diabetic
    pressure_points : ["heel", "metatarsal"]
}

// Step 3: shoe last derived from foot
Last my_last {
    reference_foot : patient_foot
    heel_height    : 20 mm
    toe_spring     : 8 mm
}

// Step 4: boot assembly
Boot orthopedic_boot {
    reference_last : my_last
    Outsole  { }
    Vamp     { }
    Quarter 1 { }
    Tongue   { }
}

// Step 5: generate 2D patterns
Export orthopedic_boot
"""


def main() -> None:
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as fh:
            source = fh.read()
        label = sys.argv[1]
    else:
        source = _DEMO_PROGRAM
        label  = "<demo>"

    print("=" * 60)
    print(f"SoleScript Parser  —  input: {label}")
    print("=" * 60)

    try:
        ast, sem_errors = parse(source)
    except (LexerError, ParseError) as exc:
        print(f"\n[SYNTAX ERROR]  {exc}")
        sys.exit(1)

    print("\n── AST ──")
    ASTPrinter().visit(ast)

    print("\n── Semantic Analysis ──")
    if sem_errors:
        for err in sem_errors:
            print(f"  ✗  {err}")
        sys.exit(1)
    else:
        print("  ✓  All semantic rules passed (SR1-SR9).")

    print("\n── Pattern Generation ──")
    stem = sys.argv[1].rsplit(".", 1)[0] if len(sys.argv) > 1 else "demo"
    Interpreter().run(ast, output_stem=stem)

    print("\n── Token Stream (first 30) ──")
    lexer  = SoleScriptLexer(source)
    tokens = lexer.get_all_tokens()
    for tok in tokens[:30]:
        print(f"  {tok}")
    if len(tokens) > 30:
        print(f"  … ({len(tokens) - 30} more tokens)")


if __name__ == "__main__":
    main()
