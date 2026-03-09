# DSL-SoleScript

A Domain-Specific Language (DSL) for orthopedic footwear pattern design. SoleScript lets clinicians and engineers describe a custom orthopedic boot in a structured, declarative way — capturing patient foot measurements, clinical observations, shoe-last geometry, and boot assembly — and then exporting 2D patterns from that description.

> **Course:** FAF-241, Team 3

---

## Table of Contents

- [What is SoleScript?](#what-is-solescript)
- [Language Overview](#language-overview)
  - [Foot Block](#foot-block)
  - [Observations Block](#observations-block)
  - [Last Block](#last-block)
  - [Boot Block](#boot-block)
  - [Export Directive](#export-directive)
- [Full Example](#full-example)
- [Grammar Rules](#grammar-rules)
- [Semantic Rules](#semantic-rules)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [ANTLR4 Generated Files](#antlr4-generated-files)

---

## What is SoleScript?

SoleScript ("sole" as in the bottom of a shoe + "script") is a language for describing orthopedic footwear from measurement to export. A SoleScript program reads like a structured specification:

1. **Measure** the patient's foot.
2. **Record** clinical notes and pressure points.
3. **Define** the shoe last (the mold around which the boot is built).
4. **Assemble** the boot by listing its components.
5. **Export** the boot to trigger 2D pattern generation.

The language is fully declarative — there are no loops, conditionals, or variables. Every construct is a named block that can be referenced by later blocks.

---

## Language Overview

### Foot Block

Declares a patient's foot measurements. All values are given in `mm` or `cm`. The attributes `length` and `ball_girth` are mandatory.

```solescript
Foot patient_foot {
    length      : 265 mm
    ball_girth  : 245 mm
    width       : 98 mm
    heel_width  : 62 mm
    arch_height : 18 mm
}
```

### Observations Block

Records clinical information about the patient. `condition` accepts a keyword from a fixed taxonomy. `pressure_points` is a list of quoted strings.

```solescript
Observations clinical_obs {
    condition       : Diabetic
    pressure_points : ["heel", "metatarsal", "toe_tip"]
}
```

**Supported condition keywords:** `Diabetic`, `Egyptian`, `Greek`, `Roman`, `Celtic`, `Germanic`, `Square`, `Peasant`

### Last Block

Defines the shoe last — the physical mold around which the boot is constructed. It must reference a previously declared `Foot` block and cannot reference itself.

```solescript
Last standard_last {
    reference_foot : patient_foot
    heel_height    : 22 mm
    toe_spring     : 10 mm
    width_fitting  : 98 mm
}
```

### Boot Block

Assembles the boot by listing shoe components. It must reference a declared `Last` block. Each component is declared as an empty block `{ }`. The `Quarter` component optionally takes a numeric suffix.

```solescript
Boot orthopedic_boot {
    reference_last : standard_last
    Outsole   { }
    Insole    { }
    Vamp      { }
    Tongue    { }
    Quarter 1 { }
    ToeBox    { }
    Heel      { }
    Shank     { }
    Counter   { }
    Lining    { }
}
```

**Available components:** `Outsole`, `Insole`, `Vamp`, `Tongue`, `Quarter`, `ToeBox`, `Heel`, `Shank`, `Counter`, `Lining`

### Export Directive

Triggers 2D pattern generation for the named boot. The target must be a declared `Boot` block.

```solescript
Export orthopedic_boot
```

---

## Full Example

The file `test.sole` contains a complete, annotated SoleScript program exercising every grammar and semantic rule:

```solescript
// Foot declaration (measurements in mm)
Foot patient_foot {
    length      : 265 mm
    ball_girth  : 245 mm
    width       : 98 mm
    heel_width  : 62 mm
    arch_height : 18 mm
}

// Clinical observations
Observations clinical_obs {
    condition       : Diabetic
    pressure_points : ["heel", "metatarsal", "toe_tip"]
}

// Shoe last derived from the foot
Last standard_last {
    reference_foot : patient_foot
    heel_height    : 22 mm
    toe_spring     : 10 mm
    width_fitting  : 98 mm
}

// Boot assembly with all 10 shoe components
Boot orthopedic_boot {
    reference_last : standard_last
    Outsole  { }
    Insole   { }
    Vamp     { }
    Tongue   { }
    Quarter 1 { }
    ToeBox   { }
    Heel     { }
    Shank    { }
    Counter  { }
    Lining   { }
}

// Export triggers 2D pattern generation
Export orthopedic_boot
```

---

## Grammar Rules

The formal grammar is defined in `SoleScript.g4` (ANTLR4 format). There are 16 grammar rules:

| Rule | Name | Production |
|------|------|------------|
| G1 | `program` | `statement* EOF` |
| G2 | `statement` | `foot_decl \| obs_decl \| last_decl \| boot_decl \| export_decl` |
| G3 | `foot_decl` | `Foot id '{' attr_list '}'` |
| G4 | `obs_decl` | `Observations id '{' attr_list '}'` |
| G5 | `last_decl` | `Last id '{' attr_list '}'` |
| G6 | `boot_decl` | `Boot id '{' attr_list comp_list '}'` |
| G7 | `export_decl` | `Export id` |
| G8 | `attr_list` | `(id ':' value)*` |
| G9 | `comp_list` | `(shoe_comp '{' '}')*` |
| G10 | `shoe_comp` | one of the 10 component keywords (`Vamp`, `Tongue`, `Quarter`, etc.) |
| G11 | `value` | `number UNIT \| id \| '[' string+ ']' \| keyword_val` |
| G12-G16 | lexer rules | `ID`, `NUMBER`, `UNIT` (`mm`/`cm`), `STRING`, whitespace/comment skip |

All keywords are **case-sensitive**. Comments use `//` and are ignored by the lexer.

---

## Semantic Rules

After parsing, the semantic analyzer (in `solescript_parser.py`) enforces 9 domain-specific rules:

| Rule | Name | Description |
|------|------|-------------|
| SR1 | UniqueDeclaration | No two blocks can share the same name |
| SR2 | ReferenceIntegrity | All `id` references must point to a declared name; `Export` must target a `Boot` |
| SR3 | MeasurementPositivity | All dimensional values (`N mm`/`N cm`) must be greater than 0 |
| SR4 | TypeMatching | `pressure_points` must be a string list (`["...", "..."]`) |
| SR5 | MandatoryParameters | A `Foot` block must include both `length` and `ball_girth` |
| SR6 | ConditionExclusivity | An `Observations` block cannot declare more than one foot-shape keyword condition |
| SR7 | ComponentScope | Shoe components may only appear inside a `Boot` block (enforced structurally by the parser) |
| SR8 | SelfRefProhibition | A `Last` block cannot reference its own name as `reference_foot` |
| SR9 | DependencyResolution | `Boot.reference_last` must point to a declared `Last` block specifically |

---

## Architecture

The parser pipeline is implemented as a single, self-contained file (`solescript_parser.py`) with no external dependencies.

```
Source text (.sole)
      │
      ▼
 SoleScriptLexer          Hand-written tokenizer → list of Token objects
      │
      ▼
 SoleScriptParser         Recursive-descent parser → typed AST
      │
      ▼
 SemanticAnalyzer         Two-pass visitor: collect symbols, then validate SR1-SR9
      │
      ▼
 ASTPrinter (optional)    Visitor that prints an indented ASCII tree for debugging
```

**Key classes:**

| Class | Role |
|---|---|
| `SoleScriptLexer` | Character-by-character tokenizer; handles keywords, identifiers, numbers, strings, units, comments |
| `SoleScriptParser` | One method per grammar rule (e.g., `_parse_foot_decl()`); builds a typed AST using dataclasses |
| `ASTVisitor` | Abstract base class; dispatches `visit_*` calls by node type name |
| `ASTPrinter` | Concrete visitor; pretty-prints the AST as an indented tree |
| `SemanticAnalyzer` | Concrete visitor; enforces SR1–SR9, returns a list of error messages |

**AST node types:** `ProgramNode`, `FootDeclNode`, `ObsDeclNode`, `LastDeclNode`, `BootDeclNode`, `ExportDeclNode`, `AttrEntryNode`, `CompEntryNode`, `DimensionValueNode`, `IdValueNode`, `StringListValueNode`, `KeywordValueNode`

---

## Requirements

### Standalone parser (recommended)

- Python 3.9 or later
- No external packages required — uses only the standard library

### ANTLR4 generated files (optional)

- Java (to run the ANTLR tool and regenerate parser files)
- `antlr4-python3-runtime==4.13.1` Python package

```bash
pip install antlr4-python3-runtime==4.13.1
```

---

## Usage

### Running the standalone parser

```bash
# Parse a .sole file
python solescript_parser.py test.sole

# Run the built-in demo program (no file argument needed)
python solescript_parser.py
```

The parser prints:
1. The tokenized output
2. The AST as an indented tree
3. Any semantic errors found, or a confirmation that the program is valid

### Using the public API

```python
from solescript_parser import parse

source = """
Foot my_foot {
    length     : 265 mm
    ball_girth : 245 mm
}
Export my_boot
"""

ast, errors = parse(source)

if errors:
    for error in errors:
        print("Error:", error)
else:
    print("Valid program:", ast)
```

### Regenerating ANTLR files (optional)

If you modify `SoleScript.g4`, regenerate the parser with:

```bash
java -jar antlr-4.13.1-complete.jar -Dlanguage=Python3 -visitor SoleScript.g4
```

Move the generated files into the `generated/` directory.

---

## Project Structure

```
DSL-SoleScript/
├── SoleScript.g4                  # Formal ANTLR4 grammar (source of truth, 16 rules)
├── solescript_parser.py           # Standalone Python parser — lexer, parser, AST, semantic analyzer
├── test.sole                      # Annotated example SoleScript program
├── antlr-4.13.1-complete.jar      # ANTLR4 tool for regenerating the generated/ files
└── generated/                     # ANTLR4-generated Python source (requires antlr4 runtime)
    ├── SoleScriptLexer.py         # ATN-based lexer
    ├── SoleScriptParser.py        # ATN-based parser with context objects per rule
    ├── SoleScriptListener.py      # Event-driven listener interface (enter*/exit* per rule)
    ├── SoleScriptVisitor.py       # Visitor interface (visit* per rule)
    ├── SoleScript.interp          # Interpreter data for ANTLR tooling
    ├── SoleScript.tokens          # Token name → integer mappings
    ├── SoleScriptLexer.interp     # Lexer-specific interpreter data
    └── SoleScriptLexer.tokens     # Lexer token mappings
```

---

## ANTLR4 Generated Files

The `generated/` directory contains parser code automatically produced by the ANTLR4 tool from `SoleScript.g4`. These files are an alternative to the standalone parser and require the ANTLR runtime to function.

- **`SoleScriptLexer.py`** — ATN-based lexer. Tokenizes source text into a token stream.
- **`SoleScriptParser.py`** — ATN-based parser. Parses the token stream into a concrete parse tree, with a typed context object per grammar rule.
- **`SoleScriptListener.py`** — Parse tree listener interface. Implement `enterFoot_decl` / `exitFoot_decl` (etc.) to react to rule entry and exit during a tree walk.
- **`SoleScriptVisitor.py`** — Parse tree visitor interface. Implement `visitFoot_decl` (etc.) to compute values during a tree traversal.

The standalone `solescript_parser.py` does not use these files and has no runtime dependency on ANTLR.
