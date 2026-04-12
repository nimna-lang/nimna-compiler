// NIMNA Sample Program
// Testing all lexer features

module main

bring nimna.io
bring nimna.math

/*
   This program tests:
   - Variables
   - Functions
   - Loops
   - Conditions
   - Comments
*/

// Constants
constant MAX_SIZE: Whole = 100
constant PI: Decimal = 3.14159

// Simple function
fn add(a: Whole, b: Whole) -> Whole {
    give a + b
}

// Function with conditions
fn check_age(age: Whole) -> Text {
    if age >= 18 {
        give "Adult"
    } else {
        give "Minor"
    }
}

// Main function
fn main() {

    // Variables
    let name: Text    = "NIMNA"
    let version: Decimal = 1.0
    let active: Truth = true
    let count: Whole  = 0

    // Print output
    nimna.io.print("Welcome to {name} v{version}!")

    // Loop test
    for i in 0..10 {
        let result: Whole = add(i, count)
        nimna.io.print("Result: {result}")
    }

    // Condition test
    let age: Whole  = 25
    let status: Text = check_age(age)
    nimna.io.print("Status: {status}")

    // Match test
    match count {
        0  => nimna.io.print("Zero")
        1  => nimna.io.print("One")
        _  => nimna.io.print("Other")
    }

}
