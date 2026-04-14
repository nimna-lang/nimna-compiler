# ============================================
# NIMNA Language — AST Node Classes
# File: src/ast/nodes.py
# Compiler: nimac
# ============================================


# ============================================
# BASE NODE
# ============================================

class Node:
    """Base class for all NIMNA AST nodes."""

    def __init__(self, line=None, column=None):
        self.line   = line
        self.column = column

    def __repr__(self):
        return f"{self.__class__.__name__}()"


# ============================================
# PROGRAM NODE
# ============================================

class Program(Node):
    """
    Root node of every NIMNA program.

    Example:
        module main
        bring nimna.io
        fn main() { ... }
    """

    def __init__(self, statements, line=None, column=None):
        super().__init__(line, column)
        self.statements = statements

    def __repr__(self):
        return f"Program(statements={len(self.statements)})"


# ============================================
# MODULE & IMPORT NODES
# ============================================

class ModuleStatement(Node):
    """
    Module declaration.

    Example:
        module main
    """

    def __init__(self, name, line=None, column=None):
        super().__init__(line, column)
        self.name = name

    def __repr__(self):
        return f"ModuleStatement(name={self.name})"


class BringStatement(Node):
    """
    Import statement.

    Example:
        bring nimna.io
        bring nimna.math from std
    """

    def __init__(self, module_path, alias=None, line=None, column=None):
        super().__init__(line, column)
        self.module_path = module_path
        self.alias       = alias

    def __repr__(self):
        return f"BringStatement(path={self.module_path})"


# ============================================
# DECLARATION NODES
# ============================================

class LetStatement(Node):
    """
    Variable declaration.

    Example:
        let name: Text  = "NIMNA"
        let age: Whole  = 25
        let x           = 100
    """

    def __init__(self, name, declared_type, value, line=None, column=None):
        super().__init__(line, column)
        self.name          = name
        self.declared_type = declared_type
        self.value         = value

    def __repr__(self):
        return f"LetStatement(name={self.name}, type={self.declared_type})"


class ConstantStatement(Node):
    """
    Constant declaration.

    Example:
        constant MAX: Whole = 100
        constant APP_NAME: Text = "NIMNA"
    """

    def __init__(self, name, declared_type, value, line=None, column=None):
        super().__init__(line, column)
        self.name          = name
        self.declared_type = declared_type
        self.value         = value

    def __repr__(self):
        return f"ConstantStatement(name={self.name}, type={self.declared_type})"


# ============================================
# FUNCTION NODES
# ============================================

class FunctionDeclaration(Node):
    """
    Function declaration.

    Example:
        fn add(a: Whole, b: Whole) -> Whole {
            give a + b
        }
    """

    def __init__(self, name, params, return_type, body,
                 is_async=False, line=None, column=None):
        super().__init__(line, column)
        self.name        = name
        self.params      = params        # List of Parameter nodes
        self.return_type = return_type   # String or None
        self.body        = body          # List of statements
        self.is_async    = is_async

    def __repr__(self):
        return f"FunctionDeclaration(name={self.name}, async={self.is_async})"


class Parameter(Node):
    """
    Function parameter.

    Example:
        a: Whole
        name: Text
    """

    def __init__(self, name, param_type, line=None, column=None):
        super().__init__(line, column)
        self.name       = name
        self.param_type = param_type

    def __repr__(self):
        return f"Parameter(name={self.name}, type={self.param_type})"


class ReturnStatement(Node):
    """
    Return statement using 'give' keyword.

    Example:
        give a + b
        give "Hello"
        give nothing
    """

    def __init__(self, value, line=None, column=None):
        super().__init__(line, column)
        self.value = value

    def __repr__(self):
        return f"ReturnStatement(value={self.value})"


# ============================================
# OBJECT & RECORD NODES
# ============================================

class ObjectDeclaration(Node):
    """
    Object (class) declaration.

    Example:
        object Animal {
            open name: Text
            fn speak() { }
        }

        object Dog grow Animal {
            fn speak() { }
        }
    """

    def __init__(self, name, parent, fields, methods,
                 line=None, column=None):
        super().__init__(line, column)
        self.name    = name
        self.parent  = parent    # String or None
        self.fields  = fields    # List of FieldDeclaration
        self.methods = methods   # List of FunctionDeclaration

    def __repr__(self):
        return f"ObjectDeclaration(name={self.name}, parent={self.parent})"


class RecordDeclaration(Node):
    """
    Record (struct) declaration.

    Example:
        record Person {
            name : Text
            age  : Whole
        }
    """

    def __init__(self, name, fields, line=None, column=None):
        super().__init__(line, column)
        self.name   = name
        self.fields = fields    # List of FieldDeclaration

    def __repr__(self):
        return f"RecordDeclaration(name={self.name})"


class FieldDeclaration(Node):
    """
    Field inside object or record.

    Example:
        open  name: Text
        hidden age: Whole
    """

    def __init__(self, name, field_type, is_public=True,
                 line=None, column=None):
        super().__init__(line, column)
        self.name       = name
        self.field_type = field_type
        self.is_public  = is_public

    def __repr__(self):
        access = "open" if self.is_public else "hidden"
        return f"FieldDeclaration({access} {self.name}: {self.field_type})"


# ============================================
# CONTROL FLOW NODES
# ============================================

class IfStatement(Node):
    """
    If-elif-else statement.

    Example:
        if age >= 18 {
            give "Adult"
        } elif age >= 13 {
            give "Teenager"
        } else {
            give "Child"
        }
    """

    def __init__(self, condition, then_body, elif_clauses,
                 else_body, line=None, column=None):
        super().__init__(line, column)
        self.condition    = condition
        self.then_body    = then_body      # List of statements
        self.elif_clauses = elif_clauses   # List of (condition, body) tuples
        self.else_body    = else_body      # List of statements or None

    def __repr__(self):
        return f"IfStatement(elif_count={len(self.elif_clauses)})"


class MatchStatement(Node):
    """
    Match statement.

    Example:
        match age {
            18 => nimna.io.print("Adult")
            _  => nimna.io.print("Other")
        }
    """

    def __init__(self, subject, arms, line=None, column=None):
        super().__init__(line, column)
        self.subject = subject    # Expression
        self.arms    = arms       # List of MatchArm

    def __repr__(self):
        return f"MatchStatement(arms={len(self.arms)})"


class MatchArm(Node):
    """
    Single arm in a match statement.

    Example:
        18 => nimna.io.print("Adult")
        _  => nimna.io.print("Other")
    """

    def __init__(self, pattern, body, is_wildcard=False,
                 line=None, column=None):
        super().__init__(line, column)
        self.pattern     = pattern
        self.body        = body
        self.is_wildcard = is_wildcard

    def __repr__(self):
        return f"MatchArm(wildcard={self.is_wildcard})"


# ============================================
# LOOP NODES
# ============================================

class ForLoop(Node):
    """
    For loop with range.

    Example:
        for i from 0..5 {
            nimna.io.print("{i}")
        }
    """

    def __init__(self, variable, range_expr, body,
                 line=None, column=None):
        super().__init__(line, column)
        self.variable   = variable
        self.range_expr = range_expr
        self.body       = body

    def __repr__(self):
        return f"ForLoop(var={self.variable})"


class WhileLoop(Node):
    """
    While loop.

    Example:
        while count < 10 {
            count += 1
        }
    """

    def __init__(self, condition, body, line=None, column=None):
        super().__init__(line, column)
        self.condition = condition
        self.body      = body

    def __repr__(self):
        return f"WhileLoop()"


class DoUntilLoop(Node):
    """
    Do-Until loop.

    Example:
        do {
            x += 1
        } until x == 5
    """

    def __init__(self, body, condition, line=None, column=None):
        super().__init__(line, column)
        self.body      = body
        self.condition = condition

    def __repr__(self):
        return f"DoUntilLoop()"


class ForeachLoop(Node):
    """
    Foreach loop over a collection.

    Example:
        foreach fruit from fruits {
            nimna.io.print("{fruit}")
        }
    """

    def __init__(self, variable, collection, body,
                 line=None, column=None):
        super().__init__(line, column)
        self.variable   = variable
        self.collection = collection
        self.body       = body

    def __repr__(self):
        return f"ForeachLoop(var={self.variable})"


class ParallelLoop(Node):
    """
    Parallel for loop.

    Example:
        parallel for i from 0..1000 {
            process(i)
        }
    """

    def __init__(self, variable, range_expr, body,
                 line=None, column=None):
        super().__init__(line, column)
        self.variable   = variable
        self.range_expr = range_expr
        self.body       = body

    def __repr__(self):
        return f"ParallelLoop(var={self.variable})"


class BreakStatement(Node):
    """
    Break out of a loop.

    Example:
        break
    """

    def __repr__(self):
        return "BreakStatement()"


class SkipStatement(Node):
    """
    Skip current iteration (continue).

    Example:
        skip
    """

    def __repr__(self):
        return "SkipStatement()"


# ============================================
# ERROR HANDLING NODES
# ============================================

class AttemptStatement(Node):
    """
    Attempt-rescue-always error handling.

    Example:
        attempt {
            let result = divide(10, 0)
        } rescue error {
            nimna.io.print("Error: {error}")
        } always {
            nimna.io.print("Done!")
        }
    """

    def __init__(self, attempt_body, rescue_var, rescue_body,
                 always_body=None, line=None, column=None):
        super().__init__(line, column)
        self.attempt_body = attempt_body
        self.rescue_var   = rescue_var
        self.rescue_body  = rescue_body
        self.always_body  = always_body

    def __repr__(self):
        has_always = self.always_body is not None
        return f"AttemptStatement(always={has_always})"


class RaiseStatement(Node):
    """
    Raise an error.

    Example:
        raise fault("Something went wrong")
    """

    def __init__(self, value, line=None, column=None):
        super().__init__(line, column)
        self.value = value

    def __repr__(self):
        return f"RaiseStatement()"


# ============================================
# EXPRESSION NODES
# ============================================

class BinaryExpression(Node):
    """
    Binary operation between two expressions.

    Example:
        a + b
        age >= 18
        x * 2
    """

    def __init__(self, left, operator, right, line=None, column=None):
        super().__init__(line, column)
        self.left     = left
        self.operator = operator
        self.right    = right

    def __repr__(self):
        return f"BinaryExpression(op={self.operator})"


class UnaryExpression(Node):
    """
    Unary operation on one expression.

    Example:
        !!active
        -age
    """

    def __init__(self, operator, operand, line=None, column=None):
        super().__init__(line, column)
        self.operator = operator
        self.operand  = operand

    def __repr__(self):
        return f"UnaryExpression(op={self.operator})"


class AssignmentExpression(Node):
    """
    Assignment to a variable.

    Example:
        age = 25
        count += 1
        score *= 2
    """

    def __init__(self, name, operator, value, line=None, column=None):
        super().__init__(line, column)
        self.name     = name
        self.operator = operator
        self.value    = value

    def __repr__(self):
        return f"AssignmentExpression(name={self.name}, op={self.operator})"


class TypeCastExpression(Node):
    """
    Type casting using 'as' keyword.

    Example:
        age as Decimal
        score as Whole
    """

    def __init__(self, value, target_type, line=None, column=None):
        super().__init__(line, column)
        self.value       = value
        self.target_type = target_type

    def __repr__(self):
        return f"TypeCastExpression(target={self.target_type})"


class TypeConstructorExpression(Node):
    """
    Type constructor for explicit conversion.

    Example:
        Whole("25")
        Decimal(age)
        Text(100)
    """

    def __init__(self, type_name, argument, line=None, column=None):
        super().__init__(line, column)
        self.type_name = type_name
        self.argument  = argument

    def __repr__(self):
        return f"TypeConstructorExpression(type={self.type_name})"


class RangeExpression(Node):
    """
    Range expression.

    Example:
        0..5    (exclusive)
        0..=5   (inclusive)
        0...    (infinite)
    """

    def __init__(self, start, end, inclusive=False,
                 infinite=False, line=None, column=None):
        super().__init__(line, column)
        self.start     = start
        self.end       = end
        self.inclusive = inclusive
        self.infinite  = infinite

    def __repr__(self):
        kind = "inclusive" if self.inclusive else "exclusive"
        return f"RangeExpression({kind})"


class PipelineExpression(Node):
    """
    Pipeline expression.

    Example:
        data |> process |> display
    """

    def __init__(self, left, right, line=None, column=None):
        super().__init__(line, column)
        self.left  = left
        self.right = right

    def __repr__(self):
        return f"PipelineExpression()"


class NullSafetyExpression(Node):
    """
    Null safety operations.

    Example:
        value ?? default
        obj?.field
        value ?! "Error"
    """

    def __init__(self, operator, left, right=None,
                 line=None, column=None):
        super().__init__(line, column)
        self.operator = operator
        self.left     = left
        self.right    = right

    def __repr__(self):
        return f"NullSafetyExpression(op={self.operator})"


# ============================================
# CALL & ACCESS NODES
# ============================================

class CallExpression(Node):
    """
    Function call expression.

    Example:
        add(10, 20)
        nimna.io.print("Hello")
        check_age(user_age)
    """

    def __init__(self, function, arguments, line=None, column=None):
        super().__init__(line, column)
        self.function  = function     # Identifier or MemberAccess
        self.arguments = arguments    # List of expressions

    def __repr__(self):
        return f"CallExpression(args={len(self.arguments)})"


class MemberAccessExpression(Node):
    """
    Member access using dot notation.

    Example:
        nimna.io
        nimna.io.print
        person.name
    """

    def __init__(self, object_expr, member, line=None, column=None):
        super().__init__(line, column)
        self.object_expr = object_expr
        self.member      = member

    def __repr__(self):
        return f"MemberAccessExpression(member={self.member})"


class IndexExpression(Node):
    """
    Index access for sequences and collections.

    Example:
        fruits[0]
        matrix[1][2]
    """

    def __init__(self, collection, index, line=None, column=None):
        super().__init__(line, column)
        self.collection = collection
        self.index      = index

    def __repr__(self):
        return f"IndexExpression()"


# ============================================
# LITERAL NODES
# ============================================

class IntegerLiteral(Node):
    """
    Whole number literal.

    Example:
        25
        100
        -5
    """

    def __init__(self, value, line=None, column=None):
        super().__init__(line, column)
        self.value = value

    def __repr__(self):
        return f"IntegerLiteral({self.value})"


class DecimalLiteral(Node):
    """
    Decimal number literal.

    Example:
        3.14
        98.5
        -2.71
    """

    def __init__(self, value, line=None, column=None):
        super().__init__(line, column)
        self.value = value

    def __repr__(self):
        return f"DecimalLiteral({self.value})"


class TextLiteral(Node):
    """
    Text string literal.

    Example:
        "Hello NIMNA"
        "Welcome {name}!"
    """

    def __init__(self, value, line=None, column=None):
        super().__init__(line, column)
        self.value = value

    def __repr__(self):
        return f"TextLiteral({repr(self.value)})"


class LetterLiteral(Node):
    """
    Single character literal.

    Example:
        'A'
        'z'
    """

    def __init__(self, value, line=None, column=None):
        super().__init__(line, column)
        self.value = value

    def __repr__(self):
        return f"LetterLiteral({repr(self.value)})"


class TruthLiteral(Node):
    """
    Boolean literal.

    Example:
        true
        false
    """

    def __init__(self, value, line=None, column=None):
        super().__init__(line, column)
        self.value = value

    def __repr__(self):
        return f"TruthLiteral({self.value})"


class NothingLiteral(Node):
    """
    Null literal.

    Example:
        nothing
    """

    def __repr__(self):
        return "NothingLiteral()"


class CollectionLiteral(Node):
    """
    Collection (array/list) literal.

    Example:
        ["Apple", "Mango", "Banana"]
        [1, 2, 3, 4, 5]
    """

    def __init__(self, elements, line=None, column=None):
        super().__init__(line, column)
        self.elements = elements

    def __repr__(self):
        return f"CollectionLiteral(count={len(self.elements)})"


class MappingLiteral(Node):
    """
    Mapping (dictionary) literal.

    Example:
        {"name": "NIMNA", "version": 1}
    """

    def __init__(self, pairs, line=None, column=None):
        super().__init__(line, column)
        self.pairs = pairs    # List of (key, value) tuples

    def __repr__(self):
        return f"MappingLiteral(pairs={len(self.pairs)})"


class BundleLiteral(Node):
    """
    Bundle (tuple) literal.

    Example:
        (25, "Ali", true)
    """

    def __init__(self, elements, line=None, column=None):
        super().__init__(line, column)
        self.elements = elements

    def __repr__(self):
        return f"BundleLiteral(count={len(self.elements)})"


# ============================================
# IDENTIFIER NODE
# ============================================

class Identifier(Node):
    """
    Variable or function name reference.

    Example:
        age
        name
        add
    """

    def __init__(self, name, line=None, column=None):
        super().__init__(line, column)
        self.name = name

    def __repr__(self):
        return f"Identifier({self.name})"


# ============================================
# ASYNC NODES
# ============================================

class AwaitExpression(Node):
    """
    Await expression for async functions.

    Example:
        await nimna.io.get(url)
        await fetchData()
    """

    def __init__(self, value, line=None, column=None):
        super().__init__(line, column)
        self.value = value

    def __repr__(self):
        return f"AwaitExpression()"


class LaunchExpression(Node):
    """
    Launch a concurrent task.

    Example:
        launch processData()
        launch heavyComputation(data)
    """

    def __init__(self, value, line=None, column=None):
        super().__init__(line, column)
        self.value = value

    def __repr__(self):
        return f"LaunchExpression()"


# ============================================
# ALL NODE TYPES LIST
# ============================================

ALL_NODE_TYPES = [
    # Program
    "Program",

    # Module
    "ModuleStatement",
    "BringStatement",

    # Declarations
    "LetStatement",
    "ConstantStatement",

    # Functions
    "FunctionDeclaration",
    "Parameter",
    "ReturnStatement",

    # OOP
    "ObjectDeclaration",
    "RecordDeclaration",
    "FieldDeclaration",

    # Control Flow
    "IfStatement",
    "MatchStatement",
    "MatchArm",

    # Loops
    "ForLoop",
    "WhileLoop",
    "DoUntilLoop",
    "ForeachLoop",
    "ParallelLoop",
    "BreakStatement",
    "SkipStatement",

    # Error Handling
    "AttemptStatement",
    "RaiseStatement",

    # Expressions
    "BinaryExpression",
    "UnaryExpression",
    "AssignmentExpression",
    "TypeCastExpression",
    "TypeConstructorExpression",
    "RangeExpression",
    "PipelineExpression",
    "NullSafetyExpression",

    # Calls
    "CallExpression",
    "MemberAccessExpression",
    "IndexExpression",

    # Literals
    "IntegerLiteral",
    "DecimalLiteral",
    "TextLiteral",
    "LetterLiteral",
    "TruthLiteral",
    "NothingLiteral",
    "CollectionLiteral",
    "MappingLiteral",
    "BundleLiteral",

    # Identifier
    "Identifier",

    # Async
    "AwaitExpression",
    "LaunchExpression",
]
