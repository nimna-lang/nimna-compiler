# NIMNA Language — Complete Grammar Rules
# Compiler : nimac
# Version  : 2.0 (Updated)
# Style    : Python readability + Java curly braces

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

## 2. MODULE & IMPORTS

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

Example:
    module main
    bring nimna.io
    bring nimna.math

---

## 3. VARIABLE & CONSTANT DECLARATIONS

let_statement
    : 'let' IDENTIFIER ':' type_name '=' expression
    | 'let' IDENTIFIER '=' expression
    ;

constant_statement
    : 'constant' IDENTIFIER ':' type_name '=' expression
    | 'constant' IDENTIFIER '=' expression
    ;

Example:
    let name    : Text    = "NIMNA"
    let age     : Whole   = 25
    let score   : Decimal = 98.5
    let active  : Truth   = true
    constant MAX : Whole  = 100

---

## 4. FUNCTIONS

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

Example:
    fn add(a: Whole, b: Whole) -> Whole {
        give a + b
    }

    async fn fetch(url: Text) -> Task {
        let data = await nimna.io.get(url)
        give data
    }

---

## 5. OBJECT SYSTEM

object_declaration
    : 'object' IDENTIFIER '{' object_body '}'
    | 'object' IDENTIFIER 'grow' IDENTIFIER '{' object_body '}'
    ;

object_body
    : (field_declaration | method_declaration)*
    ;

field_declaration
    : 'open'   IDENTIFIER ':' type_name
    | 'hidden' IDENTIFIER ':' type_name
    ;

method_declaration
    : function_declaration
    ;

Example:
    object Animal {
        open name  : Text
        open sound : Text

        fn speak() {
            nimna.io.print("{name} says {sound}")
        }
    }

    object Dog grow Animal {
        fn speak() {
            nimna.io.print("{name} says Woof!")
        }
    }

---

## 6. RECORD (Data Structure)

record_declaration
    : 'record' IDENTIFIER '{' field_declaration* '}'
    ;

Example:
    record Person {
        name : Text
        age  : Whole
        gpa  : Decimal
    }

---

## 7. CONTROL FLOW

### If Statement
if_statement
    : 'if' expression '{' statement* '}'
    | 'if' expression '{' statement* '}' 'else' '{' statement* '}'
    | 'if' expression '{' statement* '}' 'elif' expression '{' statement* '}' ('else' '{' statement* '}')?
    ;

Example:
    if age >= 18 {
        nimna.io.print("Adult")
    } elif age >= 13 {
        nimna.io.print("Teenager")
    } else {
        nimna.io.print("Child")
    }

### Match Statement
match_statement
    : 'match' expression '{' match_arm* '}'
    ;

match_arm
    : expression '=>' expression
    | expression '=>' '{' statement* '}'
    | '_'        '=>' expression
    | '_'        '=>' '{' statement* '}'
    ;

Example:
    match age {
        18  => nimna.io.print("Just adult!")
        25  => nimna.io.print("Mid twenties!")
        _   => nimna.io.print("Other age")
    }

---

## 8. LOOPS

### For Loop
for_loop
    : 'for' IDENTIFIER 'from' range_expression '{' statement* '}'
    ;

Example:
    for i from 0..5 {
        nimna.io.print("{i}")
    }

### While Loop
while_loop
    : 'while' expression '{' statement* '}'
    ;

Example:
    let count: Whole = 0
    while count < 10 {
        nimna.io.print("{count}")
        count += 1
    }

### Do-Until Loop
do_until_loop
    : 'do' '{' statement* '}' 'until' expression
    ;

Example:
    let x: Whole = 0
    do {
        nimna.io.print("{x}")
        x += 1
    } until x == 5

### Foreach Loop
foreach_loop
    : 'foreach' IDENTIFIER 'from' expression '{' statement* '}'
    ;

Example:
    let fruits: Collection = ["Apple", "Mango", "Banana"]
    foreach fruit from fruits {
        nimna.io.print("{fruit}")
    }

### Parallel Loop
parallel_loop
    : 'parallel' 'for' IDENTIFIER 'from' range_expression '{' statement* '}'
    ;

Example:
    parallel for i from 0..1000 {
        process(i)
    }

---

## 9. ERROR HANDLING

attempt_statement
    : 'attempt' '{' statement* '}'
      'rescue' IDENTIFIER '{' statement* '}'
    | 'attempt' '{' statement* '}'
      'rescue' IDENTIFIER '{' statement* '}'
      'always' '{' statement* '}'
    ;

Example:
    attempt {
        let result = nimna.math.divide(10, 0)
        nimna.io.print("Result: {result}")
    } rescue error {
        nimna.io.print("Error: {error}")
    } always {
        nimna.io.print("Done!")
    }

---

## 10. EXPRESSIONS

expression
    : assignment_expression
    ;

assignment_expression
    : IDENTIFIER '='   expression
    | IDENTIFIER '+='  expression
    | IDENTIFIER '-='  expression
    | IDENTIFIER '*='  expression
    | IDENTIFIER '/='  expression
    | IDENTIFIER '%='  expression
    | IDENTIFIER '**=' expression
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
    | '-'  unary_expression
    | pipeline_expression
    ;

pipeline_expression
    : cast_expression ('|>' cast_expression)*
    ;

cast_expression
    : primary_expression ('as' type_name)?
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
    | IDENTIFIER '.' IDENTIFIER '.' IDENTIFIER '(' argument_list? ')'
    ;

argument_list
    : expression (',' expression)*
    ;

Example:
    nimna.io.print("Hello")
    nimna.io.print(x)
    nimna.io.print("Value: {x}")
    add(10, 20)

---

## 12. TYPE CONSTRUCTOR (Type Casting)

type_constructor
    : type_name '(' expression ')'
    ;

Example:
    let num : Whole   = Whole("25")
    let dec : Decimal = Decimal(num)
    let str : Text    = Text(100)

---

## 13. PRINT SYSTEM

Two print functions:

nimna.io.print()  → New line automatically add hoti hai
nimna.io.write()  → Same line pe print hota hai

Example:
    nimna.io.print("Hello")    // Hello + newline
    nimna.io.print("World")    // World + newline
    // Output:
    // Hello
    // World

    nimna.io.write("Hello ")   // Hello (no newline)
    nimna.io.write("World")    // World (no newline)
    // Output:
    // Hello World

---

## 14. INPUT SYSTEM

nimna.io.input()  → Text return karta hai
                    Declared type dekh ke auto-convert hota hai

Example:
    let name : Text    = nimna.io.input("Name: ")
    let age  : Whole   = nimna.io.input("Age: ")
    let price: Decimal = nimna.io.input("Price: ")

---

## 15. STRING INTERPOLATION

Text literals mein curly braces se variable values insert karo.

Example:
    let name : Text  = "NIMNA"
    let age  : Whole = 25

    nimna.io.print("Hello {name}!")
    // Output: Hello NIMNA!

    nimna.io.print("Age is {age}")
    // Output: Age is 25

    nimna.io.print("Sum is {10 + 20}")
    // Output: Sum is 30

---

## 16. AUTO TYPE CONVERSION RULES

### Allowed (Automatic)
Tiny    → Short, Whole, Long, Huge, Decimal, Precise, Exact, Text
Short   → Whole, Long, Huge, Decimal, Precise, Exact, Text
Whole   → Long, Huge, Decimal, Precise, Exact, Text
Long    → Huge, Precise, Exact, Text
Decimal → Precise, Exact, Text
Precise → Exact, Text
Text    → Whole, Decimal, Truth (sirf input se)

### Not Allowed (Error)
Decimal → Whole   → Data loss possible
Long    → Whole   → Overflow possible
Whole   → Tiny    → Overflow possible
Text    → Whole   → Variable se variable nahi (sirf input se)

---

## 17. TYPE NAMES — All 25

Whole Numbers  : Tiny, Short, Whole, Long, Huge
Decimal Numbers: Decimal, Precise, Exact
Text Types     : Text, Letter, Symbol
Logical        : Truth
Raw            : Bit
Collections    : Sequence, Collection, Mapping, Unique, Bundle
Special        : Maybe, Outcome, Task, Flow, Action, Wild, Nothing

---

## 18. OPERATOR PRECEDENCE (High to Low)

1.  ( )              → Grouping
2.  fn() [ ]         → Function call, index
3.  **               → Power
4.  !! - (unary)     → Logical NOT, negation
5.  * / %            → Multiply, divide, remainder
6.  + -              → Add, subtract
7.  .. ..= ...       → Range
8.  >> <<            → Bit shift
9.  > < >= <=        → Comparison
10. == !=            → Equality
11. &                → Bitwise AND
12. ^                → Bitwise XOR
13. |                → Bitwise OR
14. &&               → Logical AND
15. ||               → Logical OR
16. |> <|            → Pipeline
17. as               → Type cast
18. ?? ?: ?. ?!      → Null safety
19. = += -= *= /=    → Assignment

---

## 19. COMPLETE NIMNA STYLE EXAMPLE

module main

bring nimna.io
bring nimna.math

constant APP_NAME : Text  = "NIMNA App"
constant MAX_AGE  : Whole = 100

record Person {
    name : Text
    age  : Whole
    gpa  : Decimal
}

object Animal {
    open name  : Text
    open sound : Text

    fn speak() {
        nimna.io.print("{name} says {sound}")
    }
}

object Dog grow Animal {
    fn speak() {
        nimna.io.print("{name} says Woof!")
    }
}

fn add(a: Whole, b: Whole) -> Whole {
    give a + b
}

fn check_age(age: Whole) -> Text {
    if age >= 18 {
        give "Adult"
    } elif age >= 13 {
        give "Teenager"
    } else {
        give "Child"
    }
}

fn main() {

    let name   : Text    = "Ali"
    let age    : Whole   = 25
    let score  : Decimal = 98.5
    let active : Truth   = true

    nimna.io.print("Welcome to {APP_NAME}!")
    nimna.io.print("Name: {name}, Age: {age}")

    let user_name : Text  = nimna.io.input("Enter name: ")
    let user_age  : Whole = nimna.io.input("Enter age: ")

    let status : Text = check_age(user_age)
    nimna.io.print("Status: {status}")

    for i from 0..5 {
        nimna.io.print("Count: {i}")
    }

    let fruits : Collection = ["Apple", "Mango", "Banana"]
    foreach fruit from fruits {
        nimna.io.print("Fruit: {fruit}")
    }

    let count : Whole = 0
    while count < 5 {
        nimna.io.print("{count}")
        count += 1
    }

    match age {
        18  => nimna.io.print("Just adult!")
        25  => nimna.io.print("Mid twenties!")
        _   => nimna.io.print("Other age")
    }

    attempt {
        let result = nimna.math.divide(10, 0)
        nimna.io.print("Result: {result}")
    } rescue error {
        nimna.io.print("Error: {error}")
    } always {
        nimna.io.print("Done!")
    }

    let x   : Text    = "100"
    let num : Whole   = Whole(x)
    let dec : Decimal = Decimal(num)

    nimna.io.write("Same ")
    nimna.io.write("Line ")
    nimna.io.write("Output")

}
