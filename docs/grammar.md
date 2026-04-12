# NIMNA Language — Grammar Rules
# Compiler: nimac
# Version: 1.0

---

## 1. PROGRAM STRUCTURE

program
    : statement*
    ;

statement
    : let_statement
    | constant_statement
    | function_declaration
    | object_declaration
    | record_declaration
    | if_statement
    | for_loop
    | while_loop
    | do_until_loop
    | foreach_loop
    | parallel_loop
    | match_statement
    | return_statement
    | attempt_statement
    | bring_statement
    | module_statement
    | expression_statement
    ;

---

## 2. DECLARATIONS

### Variable Declaration
let_statement
    : 'let' IDENTIFIER ':' type_name '=' expression
    | 'let' IDENTIFIER '=' expression
    ;

### Constant Declaration
constant_statement
    : 'constant' IDENTIFIER ':' type_name '=' expression
    | 'constant' IDENTIFIER '=' expression
    ;

---

## 3. FUNCTIONS

function_declaration
    : 'fn' IDENTIFIER '(' parameter_list? ')' '->' type_name '{' statement* '}'
    | 'fn' IDENTIFIER '(' parameter_list? ')' '{' statement* '}'
    | 'async' 'fn' IDENTIFIER '(' parameter_list? ')' '->' type_name '{' statement* '}'
    ;

parameter_list
    : parameter (',' parameter)*
    ;

parameter
    : IDENTIFIER ':' type_name
    ;

return_statement
    : 'give' expression
    ;

---

## 4. OBJECT SYSTEM

object_declaration
    : 'object' IDENTIFIER '{' object_body '}'
    | 'object' IDENTIFIER 'extend' IDENTIFIER '{' object_body '}'
    ;

object_body
    : (field_declaration | method_declaration)*
    ;

field_declaration
    : 'open' IDENTIFIER ':' type_name
    | 'hidden' IDENTIFIER ':' type_name
    ;

method_declaration
    : function_declaration
    ;

---

## 5. RECORD (Struct)

record_declaration
    : 'record' IDENTIFIER '{' field_declaration* '}'
    ;

---

## 6. CONTROL FLOW

### If Statement
if_statement
    : 'if' expression '{' statement* '}'
    | 'if' expression '{' statement* '}' 'else' '{' statement* '}'
    | 'if' expression '{' statement* '}' 'elif' expression '{' statement* '}'
    ;

### Match Statement
match_statement
    : 'match' expression '{' match_arm* '}'
    ;

match_arm
    : expression '=>' expression
    | expression '=>' '{' statement* '}'
    | '_' '=>' expression
    ;

---

## 7. LOOPS

### For Loop
for_loop
    : 'for' IDENTIFIER 'in' expression '{' statement* '}'
    ;

### While Loop
while_loop
    : 'while' expression '{' statement* '}'
    ;

### Do-Until Loop
do_until_loop
    : 'do' '{' statement* '}' 'until' expression
    ;

### Foreach Loop
foreach_loop
    : 'foreach' IDENTIFIER 'in' expression '{' statement* '}'
    ;

### Parallel Loop
parallel_loop
    : 'parallel' 'for' IDENTIFIER 'in' expression '{' statement* '}'
    ;

---

## 8. ERROR HANDLING

attempt_statement
    : 'attempt' '{' statement* '}' 'rescue' IDENTIFIER '{' statement* '}'
    | 'attempt' '{' statement* '}' 'rescue' IDENTIFIER '{' statement* '}' 'always' '{' statement* '}'
    ;

---

## 9. MODULES

module_statement
    : 'module' IDENTIFIER
    ;

bring_statement
    : 'bring' module_path
    | 'bring' module_path 'from' IDENTIFIER
    ;

module_path
    : IDENTIFIER ('.' IDENTIFIER)*
    ;

---

## 10. EXPRESSIONS

expression
    : assignment_expression
    ;

assignment_expression
    : IDENTIFIER '=' expression
    | IDENTIFIER '+=' expression
    | IDENTIFIER '-=' expression
    | IDENTIFIER '*=' expression
    | IDENTIFIER '/=' expression
    | logical_expression
    ;

logical_expression
    : comparison_expression (('&&' | '||') comparison_expression)*
    ;

comparison_expression
    : range_expression (('==' | '!=' | '>' | '<' | '>=' | '<=') range_expression)*
    ;

range_expression
    : additive_expression (('..' | '..=' | '...') additive_expression)?
    ;

additive_expression
    : multiplicative_expression (('+' | '-') multiplicative_expression)*
    ;

multiplicative_expression
    : power_expression (('*' | '/' | '%') power_expression)*
    ;

power_expression
    : unary_expression ('**' unary_expression)?
    ;

unary_expression
    : '!!' unary_expression
    | '-' unary_expression
    | pipeline_expression
    ;

pipeline_expression
    : cast_expression ('|>' cast_expression)*
    ;

cast_expression
    : primary_expression ('as' type_name)?
    | primary_expression (':' type_name)?
    ;

primary_expression
    : INTEGER_LITERAL
    | DECIMAL_LITERAL
    | TEXT_LITERAL
    | LETTER_LITERAL
    | 'true'
    | 'false'
    | 'nothing'
    | IDENTIFIER
    | function_call
    | type_constructor
    | '(' expression ')'
    ;

---

## 11. FUNCTION CALL

function_call
    : IDENTIFIER '(' argument_list? ')'
    | IDENTIFIER '.' IDENTIFIER '(' argument_list? ')'
    ;

argument_list
    : expression (',' expression)*
    ;

---

## 12. TYPE CONSTRUCTOR (Type Casting)

type_constructor
    : type_name '(' expression ')'
    ;

---

## 13. TYPE NAMES

type_name
    : 'Tiny'
    | 'Short'
    | 'Whole'
    | 'Long'
    | 'Huge'
    | 'Decimal'
    | 'Precise'
    | 'Exact'
    | 'Text'
    | 'Letter'
    | 'Symbol'
    | 'Truth'
    | 'Bit'
    | 'Sequence'
    | 'Collection'
    | 'Mapping'
    | 'Unique'
    | 'Bundle'
    | 'Maybe'
    | 'Outcome'
    | 'Task'
    | 'Flow'
    | 'Action'
    | 'Wild'
    | 'Nothing'
    | IDENTIFIER
    ;

---

## 14. AUTO CONVERSION RULES

### Allowed (Automatic)
Tiny    → Short, Whole, Long, Huge, Decimal, Precise, Exact, Text
Short   → Whole, Long, Huge, Decimal, Precise, Exact, Text
Whole   → Long, Huge, Decimal, Precise, Exact, Text
Long    → Huge, Precise, Exact, Text
Decimal → Precise, Exact, Text
Precise → Exact, Text
Text    → Whole, Decimal, Truth (only from input)

### Not Allowed (Error)
Decimal → Whole   (data loss)
Long    → Whole   (overflow)
Whole   → Tiny    (overflow)
Text    → Whole   (only from input — not variable to variable)

---

## 15. OPERATOR PRECEDENCE (High to Low)

1. ()                    — Grouping
2. fn() []              — Function call, index
3. **                   — Power
4. !! - (unary)         — Unary NOT, negation
5. * / %                — Multiply, divide, remainder
6. + -                  — Add, subtract
7. .. ..= ...           — Range
8. >> <<                — Bit shift
9. > < >= <=            — Comparison
10. == !=               — Equality
11. &                   — Bitwise AND
12. ^                   — Bitwise XOR
13. |                   — Bitwise OR
14. &&                  — Logical AND
15. ||                  — Logical OR
16. |> <|               — Pipeline
17. as :TypeName        — Type cast
18. ?? ?: ?. ?!         — Null safety
19. = += -= *= /=       — Assignment
