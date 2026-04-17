# NIMNA Semantic Analyzer — Architecture

## Overview

The NIMNA Semantic Analyzer traverses the AST and performs:

1. **Symbol Resolution** — Are all variables declared?
2. **Type Checking** — Are types compatible?
3. **Scope Analysis** — Is variable accessible here?
4. **Function Validation** — Correct args and return type?
5. **Auto Conversion** — Safe type promotions?
6. **Error Collection** — Friendly error messages?

---

## Symbol Table Structure

Each entry in the symbol table contains:

| Field       | Type   | Description                    |
|-------------|--------|--------------------------------|
| name        | str    | Variable or function name      |
| kind        | str    | variable / function / object   |
| nimna_type  | str    | Whole, Text, Decimal, etc.     |
| scope_level | int    | 0=global, 1=function, 2=block  |
| line        | int    | Where it was declared          |
| is_constant | bool   | Is it a constant?              |
| is_assigned | bool   | Has it been assigned a value?  |

---

## Scope Levels

```
Level 0 — Global Scope
    module main
    constant MAX = 100
    fn add() {           <- Level 1 — Function Scope
        if x > 0 {       <- Level 2 — Block Scope
            let y = 5    <- Level 2
        }
    }
```

---

## Type Compatibility Table

| From    | To      | Allowed | Note                   |
|---------|---------|---------|------------------------|
| Tiny    | Short   | Yes     | Auto promote           |
| Tiny    | Whole   | Yes     | Auto promote           |
| Whole   | Decimal | Yes     | Auto promote           |
| Decimal | Whole   | No      | Data loss              |
| Text    | Whole   | Input   | Only from input()      |
| Whole   | Text    | Yes     | Auto convert           |
| Truth   | Whole   | Yes     | true=1, false=0        |

---

## Error Message Format

```
[NIMNA Error] Type Mismatch
  File    : main.nim
  Location: Line 5, Column 10
  Message : Cannot assign 'Decimal' to 'Whole'. Data loss possible.
  Hint    : Use Decimal type or explicit conversion: Whole(value)
```

---

## Analysis Order

1. Collect all top-level declarations (functions, objects, records)
2. Analyze each statement in order
3. For each expression, resolve types
4. Report all errors at end
