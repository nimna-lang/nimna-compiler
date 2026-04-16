# ============================================
# NIMNA — Parser Test
# ============================================

import sys
sys.path.insert(0, 'src/lexer')
sys.path.insert(0, 'src/parser')
sys.path.insert(0, 'src/ast')

from lexer import NIMNALexer
from parser import NIMNAParser

print("=== NIMNA Parser Test ===")
print("")

passed = 0
failed = 0

def parse_code(code, test_name):
    global passed, failed
    lexer  = NIMNALexer(code, filename="test.nim")
    tokens = lexer.tokenize()
    parser = NIMNAParser(tokens, filename="test.nim")
    ast    = parser.parse()
    if parser.has_errors():
        print(f"  ❌ {test_name}")
        for e in parser.get_errors():
            print(f"     {e}")
        failed += 1
    else:
        print(f"  ✅ {test_name} — {len(ast.statements)} statement(s)")
        passed += 1
    return ast, parser


# Test 1
print("Test 1 — Module and Bring:")
parse_code("""
module main
bring nimna.io
bring nimna.math
""", "module + bring")
print("")

# Test 2
print("Test 2 — Variable Declarations:")
parse_code("""
let name   : Text    = "NIMNA"
let age    : Whole   = 25
let score  : Decimal = 98.5
let active : Truth   = true
let x               = 100
""", "let statements")
print("")

# Test 3
print("Test 3 — Function Declaration:")
parse_code("""
fn add(a: Whole, b: Whole) -> Whole {
    give a + b
}
""", "function declaration")
print("")

# Test 4
print("Test 4 — Object Declaration:")
parse_code("""
object Animal {
    open name  : Text
    open sound : Text
    fn speak() {
        give nothing
    }
}
""", "object declaration")
print("")

# Test 5
print("Test 5 — If-Elif-Else:")
parse_code("""
if age >= 18 {
    give "Adult"
} elif age >= 13 {
    give "Teenager"
} else {
    give "Child"
}
""", "if-elif-else")
print("")

# Test 6
print("Test 6 — All 5 Loops:")
parse_code("""
for i from 0..5 {
    give i
}
while count < 10 {
    count += 1
}
do {
    x += 1
} until x == 5
foreach fruit from fruits {
    give fruit
}
parallel for i from 0..100 {
    give i
}
""", "all 5 loops")
print("")

# Test 7
print("Test 7 — Match Statement:")
parse_code("""
match age {
    18 => give "Just adult"
    25 => give "Mid twenties"
    _  => give "Other"
}
""", "match statement")
print("")

# Test 8
print("Test 8 — Attempt-Rescue-Always:")
parse_code("""
attempt {
    let result = divide(10, 0)
} rescue error {
    give "Error caught"
} always {
    give "Done"
}
""", "attempt-rescue-always")
print("")

# Test 9
print("Test 9 — Complete NIMNA Program:")
parse_code("""
module main
bring nimna.io
bring nimna.math
constant MAX : Whole = 100
record Person {
    name  : Text
    age   : Whole
}
object Animal {
    open name : Text
    fn speak() {
        nimna.io.print("hello")
    }
}
fn check_age(age: Whole) -> Text {
    if age >= 18 {
        give "Adult"
    } else {
        give "Minor"
    }
}
fn main() {
    let name   : Text  = nimna.io.input("Name: ")
    let age    : Whole = nimna.io.input("Age: ")
    let status : Text  = check_age(age)
    nimna.io.print("Status: {status}")
    for i from 0..5 {
        nimna.io.print("{i}")
    }
    let fruits : Collection = ["Apple", "Mango"]
    foreach fruit from fruits {
        nimna.io.print("{fruit}")
    }
}
""", "complete NIMNA program")
print("")

print("=" * 40)
print(f"Passed : {passed}")
print(f"Failed : {failed}")
print(f"Total  : {passed + failed}")
if failed == 0:
    print("✅ ALL TESTS PASSED!")
else:
    print(f"❌ {failed} TEST(S) FAILED")
print("")
