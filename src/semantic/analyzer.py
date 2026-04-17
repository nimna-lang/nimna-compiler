# ============================================
# NIMNA Language — Semantic Analyzer
# File: src/semantic/analyzer.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../lexer')
sys.path.insert(0, '../ast')

from nodes import (
    Program, ModuleStatement, BringStatement,
    LetStatement, ConstantStatement,
    FunctionDeclaration, Parameter, ReturnStatement, RaiseStatement,
    ObjectDeclaration, RecordDeclaration, FieldDeclaration,
    IfStatement, MatchStatement, MatchArm,
    ForLoop, WhileLoop, DoUntilLoop, ForeachLoop, ParallelLoop,
    BreakStatement, SkipStatement,
    AttemptStatement,
    BinaryExpression, UnaryExpression, AssignmentExpression,
    TypeCastExpression, TypeConstructorExpression,
    RangeExpression, PipelineExpression,
    CallExpression, MemberAccessExpression, IndexExpression,
    IntegerLiteral, DecimalLiteral, TextLiteral, LetterLiteral,
    TruthLiteral, NothingLiteral, CollectionLiteral,
    Identifier, AwaitExpression, LaunchExpression,
)


# ============================================
# TYPE RULES
# ============================================

SAFE_CONVERSIONS = {
    "Tiny"    : {"Short", "Whole", "Long", "Huge",
                 "Decimal", "Precise", "Exact", "Text"},
    "Short"   : {"Whole", "Long", "Huge",
                 "Decimal", "Precise", "Exact", "Text"},
    "Whole"   : {"Long", "Huge", "Decimal", "Precise", "Exact", "Text"},
    "Long"    : {"Huge", "Precise", "Exact", "Text"},
    "Huge"    : {"Precise", "Exact", "Text"},
    "Decimal" : {"Precise", "Exact", "Text"},
    "Precise" : {"Exact", "Text"},
    "Exact"   : {"Text"},
    "Text"    : {"Whole", "Decimal", "Truth"},
    "Truth"   : {"Whole", "Text"},
    "Letter"  : {"Text", "Whole"},
}

UNSAFE_CONVERSIONS = {
    ("Decimal", "Whole")  : "Data loss — decimal part will be cut.",
    ("Decimal", "Tiny")   : "Data loss — decimal part will be cut.",
    ("Decimal", "Short")  : "Data loss — decimal part will be cut.",
    ("Precise", "Decimal"): "Precision loss possible.",
    ("Precise", "Whole")  : "Data loss possible.",
    ("Long",    "Whole")  : "Overflow possible.",
    ("Long",    "Short")  : "Overflow possible.",
    ("Long",    "Tiny")   : "Overflow possible.",
    ("Huge",    "Long")   : "Overflow possible.",
    ("Huge",    "Whole")  : "Overflow possible.",
    ("Whole",   "Short")  : "Overflow possible.",
    ("Whole",   "Tiny")   : "Overflow possible.",
}

VALID_TYPES = {
    "Tiny", "Short", "Whole", "Long", "Huge",
    "Decimal", "Precise", "Exact",
    "Text", "Letter", "Symbol",
    "Truth", "Bit",
    "Sequence", "Collection", "Mapping",
    "Unique", "Bundle",
    "Maybe", "Outcome", "Task",
    "Flow", "Action", "Wild", "Nothing",
}

NUMERIC_TYPES  = {"Tiny", "Short", "Whole", "Long", "Huge",
                  "Decimal", "Precise", "Exact"}
WHOLE_TYPES    = {"Tiny", "Short", "Whole", "Long", "Huge"}
DECIMAL_TYPES  = {"Decimal", "Precise", "Exact"}


# ============================================
# SYMBOL
# ============================================

class Symbol:
    """Single entry in the Symbol Table."""

    def __init__(self, name, kind, nimna_type,
                 scope_level, line, is_constant=False):
        self.name        = name
        self.kind        = kind
        self.nimna_type  = nimna_type
        self.scope_level = scope_level
        self.line        = line
        self.is_constant = is_constant
        self.is_assigned = False
        self.params      = []
        self.return_type = None

    def __repr__(self):
        return (
            f"Symbol(name={self.name}, kind={self.kind}, "
            f"type={self.nimna_type}, scope={self.scope_level}, "
            f"line={self.line})"
        )


# ============================================
# SEMANTIC ERROR
# ============================================

class SemanticError:
    """A single semantic error with location and hint."""

    def __init__(self, message, line=None, column=None,
                 hint=None, filename="<nimna>"):
        self.message  = message
        self.line     = line
        self.column   = column
        self.hint     = hint
        self.filename = filename

    def __str__(self):
        location = f"Line {self.line}" if self.line else "Unknown"
        if self.column:
            location += f", Column {self.column}"
        hint_str = f"\n  Hint    : {self.hint}" if self.hint else ""
        return (
            f"\n[NIMNA Error] {self.message}\n"
            f"  File    : {self.filename}\n"
            f"  Location: {location}"
            f"{hint_str}"
        )


# ============================================
# NIMNA SEMANTIC ANALYZER
# ============================================

class NIMNASemanticAnalyzer:
    """
    NIMNA Semantic Analyzer

    Traverses AST and performs:
    - Symbol resolution
    - Type checking
    - Scope analysis
    - Function validation
    - Auto conversion checking
    """

    def __init__(self, filename="<nimna>"):
        self.filename            = filename
        self.errors              = []
        self.warnings            = []
        self.scope_stack         = [{}]
        self.scope_level         = 0
        self.current_function    = None
        self.current_return_type = None


    # ==========================================
    # SCOPE MANAGEMENT
    # ==========================================

    def enter_scope(self):
        self.scope_level += 1
        self.scope_stack.append({})

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
            self.scope_level -= 1

    def current_scope(self):
        return self.scope_stack[-1]

    def declare(self, name, kind, nimna_type, line, is_constant=False):
        scope = self.current_scope()
        if name in scope:
            self.add_error(
                f"'{name}' is already declared in this scope.",
                line=line,
                hint=f"First declared at line {scope[name].line}."
            )
            return False
        symbol = Symbol(name, kind, nimna_type,
                        self.scope_level, line, is_constant)
        scope[name] = symbol
        return True

    def lookup(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None


    # ==========================================
    # ERROR AND WARNING MANAGEMENT
    # ==========================================

    def add_error(self, message, line=None, column=None, hint=None):
        self.errors.append(SemanticError(
            message=message,
            line=line,
            column=column,
            hint=hint,
            filename=self.filename
        ))

    def add_warning(self, message, line=None):
        self.warnings.append(
            f"[NIMNA Warning] {message} (Line {line})"
        )

    def has_errors(self):
        return len(self.errors) > 0

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings


    # ==========================================
    # TYPE UTILITIES
    # ==========================================

    def is_compatible(self, from_type, to_type):
        if from_type is None or to_type is None:
            return True, ""
        if from_type == to_type:
            return True, ""
        if from_type == "Wild" or to_type == "Wild":
            return True, ""
        if from_type in SAFE_CONVERSIONS:
            if to_type in SAFE_CONVERSIONS[from_type]:
                return True, ""
        key = (from_type, to_type)
        if key in UNSAFE_CONVERSIONS:
            reason = UNSAFE_CONVERSIONS[key]
            return False, (
                f"Cannot assign '{from_type}' to '{to_type}'. {reason}"
            )
        return False, (
            f"Type mismatch: '{from_type}' is not compatible with '{to_type}'."
        )

    def get_binary_result_type(self, left_type, operator, right_type):
        if operator in ("==", "!=", ">", "<", ">=", "<="):
            return "Truth"
        if operator in ("&&", "||"):
            return "Truth"
        if operator in ("..", "..=", "..."):
            return "Range"
        if operator == "+" and left_type == "Text":
            return "Text"
        if left_type in DECIMAL_TYPES or right_type in DECIMAL_TYPES:
            return "Decimal"
        if left_type in WHOLE_TYPES and right_type in WHOLE_TYPES:
            order = ["Tiny", "Short", "Whole", "Long", "Huge"]
            li = order.index(left_type)  if left_type  in order else 2
            ri = order.index(right_type) if right_type in order else 2
            return order[max(li, ri)]
        return left_type if left_type else right_type


    # ==========================================
    # MAIN ANALYZE
    # ==========================================

    def analyze(self, ast):
        """Main entry point — analyze complete AST."""
        self._pre_scan(ast)
        for stmt in ast.statements:
            self.analyze_statement(stmt)
        return not self.has_errors()

    def _pre_scan(self, ast):
        """Register top-level declarations for forward references."""
        for stmt in ast.statements:
            if isinstance(stmt, FunctionDeclaration):
                self.declare(
                    name=stmt.name, kind="function",
                    nimna_type=stmt.return_type or "Nothing",
                    line=stmt.line
                )
                sym = self.lookup(stmt.name)
                if sym:
                    sym.params      = stmt.params
                    sym.return_type = stmt.return_type

            elif isinstance(stmt, ObjectDeclaration):
                self.declare(
                    name=stmt.name, kind="object",
                    nimna_type=stmt.name, line=stmt.line
                )

            elif isinstance(stmt, RecordDeclaration):
                self.declare(
                    name=stmt.name, kind="record",
                    nimna_type=stmt.name, line=stmt.line
                )

            elif isinstance(stmt, ConstantStatement):
                self.declare(
                    name=stmt.name, kind="variable",
                    nimna_type=stmt.declared_type or "Wild",
                    line=stmt.line, is_constant=True
                )


    # ==========================================
    # STATEMENT ANALYSIS
    # ==========================================

    def analyze_statement(self, stmt):
        if stmt is None:
            return
        if isinstance(stmt, ModuleStatement):
            pass
        elif isinstance(stmt, BringStatement):
            pass
        elif isinstance(stmt, LetStatement):
            self.analyze_let(stmt)
        elif isinstance(stmt, ConstantStatement):
            self.analyze_constant(stmt)
        elif isinstance(stmt, FunctionDeclaration):
            self.analyze_function(stmt)
        elif isinstance(stmt, ObjectDeclaration):
            self.analyze_object(stmt)
        elif isinstance(stmt, RecordDeclaration):
            self.analyze_record(stmt)
        elif isinstance(stmt, IfStatement):
            self.analyze_if(stmt)
        elif isinstance(stmt, MatchStatement):
            self.analyze_match(stmt)
        elif isinstance(stmt, ForLoop):
            self.analyze_for(stmt)
        elif isinstance(stmt, WhileLoop):
            self.analyze_while(stmt)
        elif isinstance(stmt, DoUntilLoop):
            self.analyze_do_until(stmt)
        elif isinstance(stmt, ForeachLoop):
            self.analyze_foreach(stmt)
        elif isinstance(stmt, ParallelLoop):
            self.analyze_parallel(stmt)
        elif isinstance(stmt, AttemptStatement):
            self.analyze_attempt(stmt)
        elif isinstance(stmt, ReturnStatement):
            self.analyze_return(stmt)
        elif isinstance(stmt, RaiseStatement):
            self.analyze_expression(stmt.value)
        elif isinstance(stmt, (BreakStatement, SkipStatement)):
            pass
        else:
            self.analyze_expression(stmt)


    # ==========================================
    # DECLARATIONS
    # ==========================================

    def analyze_let(self, stmt):
        value_type = self.analyze_expression(stmt.value)
        if stmt.declared_type:
            if stmt.declared_type not in VALID_TYPES:
                self.add_error(
                    f"Unknown type '{stmt.declared_type}'.",
                    line=stmt.line,
                    hint="Valid types: Whole, Text, Decimal, Truth, ..."
                )
                return
            if value_type and value_type != "Wild":
                compatible, err_msg = self.is_compatible(
                    value_type, stmt.declared_type
                )
                if not compatible:
                    self.add_error(
                        err_msg, line=stmt.line,
                        hint=f"Use '{stmt.declared_type}(value)' for explicit conversion."
                    )
                    return
        self.declare(
            name=stmt.name, kind="variable",
            nimna_type=stmt.declared_type or value_type or "Wild",
            line=stmt.line
        )
        sym = self.lookup(stmt.name)
        if sym:
            sym.is_assigned = True

    def analyze_constant(self, stmt):
        value_type = self.analyze_expression(stmt.value)
        if stmt.declared_type and value_type:
            compatible, err_msg = self.is_compatible(
                value_type, stmt.declared_type
            )
            if not compatible:
                self.add_error(err_msg, line=stmt.line)


    # ==========================================
    # FUNCTIONS
    # ==========================================

    def analyze_function(self, stmt):
        prev_function    = self.current_function
        prev_return_type = self.current_return_type
        self.current_function    = stmt.name
        self.current_return_type = stmt.return_type
        self.enter_scope()
        for param in stmt.params:
            self.declare(
                name=param.name, kind="param",
                nimna_type=param.param_type, line=stmt.line
            )
        for s in stmt.body:
            self.analyze_statement(s)
        self.exit_scope()
        self.current_function    = prev_function
        self.current_return_type = prev_return_type


    # ==========================================
    # OBJECT AND RECORD
    # ==========================================

    def analyze_object(self, stmt):
        if stmt.parent:
            parent_sym = self.lookup(stmt.parent)
            if not parent_sym:
                self.add_error(
                    f"Parent object '{stmt.parent}' not found.",
                    line=stmt.line,
                    hint=f"Declare '{stmt.parent}' before '{stmt.name}'."
                )
        self.enter_scope()
        for field in stmt.fields:
            self.declare(
                name=field.name, kind="field",
                nimna_type=field.field_type, line=stmt.line
            )
        for method in stmt.methods:
            self.analyze_function(method)
        self.exit_scope()

    def analyze_record(self, stmt):
        self.enter_scope()
        for field in stmt.fields:
            self.declare(
                name=field.name, kind="field",
                nimna_type=field.field_type, line=stmt.line
            )
        self.exit_scope()


    # ==========================================
    # CONTROL FLOW
    # ==========================================

    def analyze_if(self, stmt):
        self.analyze_expression(stmt.condition)
        self.enter_scope()
        for s in stmt.then_body:
            self.analyze_statement(s)
        self.exit_scope()
        for elif_cond, elif_body in stmt.elif_clauses:
            self.analyze_expression(elif_cond)
            self.enter_scope()
            for s in elif_body:
                self.analyze_statement(s)
            self.exit_scope()
        if stmt.else_body:
            self.enter_scope()
            for s in stmt.else_body:
                self.analyze_statement(s)
            self.exit_scope()

    def analyze_match(self, stmt):
        self.analyze_expression(stmt.subject)
        for arm in stmt.arms:
            if not arm.is_wildcard:
                self.analyze_expression(arm.pattern)
            self.enter_scope()
            for s in arm.body:
                self.analyze_statement(s)
            self.exit_scope()


    # ==========================================
    # LOOPS
    # ==========================================

    def analyze_for(self, stmt):
        self.analyze_expression(stmt.range_expr)
        self.enter_scope()
        self.declare(
            name=stmt.variable, kind="variable",
            nimna_type="Whole", line=stmt.line
        )
        for s in stmt.body:
            self.analyze_statement(s)
        self.exit_scope()

    def analyze_while(self, stmt):
        self.analyze_expression(stmt.condition)
        self.enter_scope()
        for s in stmt.body:
            self.analyze_statement(s)
        self.exit_scope()

    def analyze_do_until(self, stmt):
        self.enter_scope()
        for s in stmt.body:
            self.analyze_statement(s)
        self.exit_scope()
        self.analyze_expression(stmt.condition)

    def analyze_foreach(self, stmt):
        self.analyze_expression(stmt.collection)
        self.enter_scope()
        self.declare(
            name=stmt.variable, kind="variable",
            nimna_type="Wild", line=stmt.line
        )
        for s in stmt.body:
            self.analyze_statement(s)
        self.exit_scope()

    def analyze_parallel(self, stmt):
        self.analyze_expression(stmt.range_expr)
        self.enter_scope()
        self.declare(
            name=stmt.variable, kind="variable",
            nimna_type="Whole", line=stmt.line
        )
        for s in stmt.body:
            self.analyze_statement(s)
        self.exit_scope()


    # ==========================================
    # ERROR HANDLING
    # ==========================================

    def analyze_attempt(self, stmt):
        self.enter_scope()
        for s in stmt.attempt_body:
            self.analyze_statement(s)
        self.exit_scope()
        self.enter_scope()
        self.declare(
            name=stmt.rescue_var, kind="variable",
            nimna_type="Text", line=0
        )
        for s in stmt.rescue_body:
            self.analyze_statement(s)
        self.exit_scope()
        if stmt.always_body:
            self.enter_scope()
            for s in stmt.always_body:
                self.analyze_statement(s)
            self.exit_scope()

    def analyze_return(self, stmt):
        value_type = self.analyze_expression(stmt.value)
        if self.current_return_type and value_type:
            if value_type == "Wild" or self.current_return_type == "Wild":
                return
            compatible, err_msg = self.is_compatible(
                value_type, self.current_return_type
            )
            if not compatible:
                self.add_error(
                    f"Return type mismatch in '{self.current_function}'. "
                    f"Expected '{self.current_return_type}' but got '{value_type}'.",
                    line=stmt.line,
                    hint="Change return type or convert the value."
                )


    # ==========================================
    # EXPRESSIONS
    # ==========================================

    def analyze_expression(self, expr):
        """Analyze expression and return its NIMNA type."""
        if expr is None:
            return None

        if isinstance(expr, IntegerLiteral):   return "Whole"
        if isinstance(expr, DecimalLiteral):   return "Decimal"
        if isinstance(expr, TextLiteral):      return "Text"
        if isinstance(expr, LetterLiteral):    return "Letter"
        if isinstance(expr, TruthLiteral):     return "Truth"
        if isinstance(expr, NothingLiteral):   return "Nothing"

        if isinstance(expr, CollectionLiteral):
            for elem in expr.elements:
                self.analyze_expression(elem)
            return "Collection"

        if isinstance(expr, Identifier):
            return self.analyze_identifier(expr)

        if isinstance(expr, BinaryExpression):
            return self.analyze_binary(expr)

        if isinstance(expr, UnaryExpression):
            operand_type = self.analyze_expression(expr.operand)
            return operand_type

        if isinstance(expr, AssignmentExpression):
            return self.analyze_assignment(expr)

        if isinstance(expr, TypeCastExpression):
            self.analyze_expression(expr.value)
            return expr.target_type

        if isinstance(expr, TypeConstructorExpression):
            self.analyze_expression(expr.argument)
            return expr.type_name

        if isinstance(expr, RangeExpression):
            self.analyze_expression(expr.start)
            if expr.end:
                self.analyze_expression(expr.end)
            return "Range"

        if isinstance(expr, PipelineExpression):
            self.analyze_expression(expr.left)
            return self.analyze_expression(expr.right)

        if isinstance(expr, CallExpression):
            return self.analyze_call(expr)

        if isinstance(expr, MemberAccessExpression):
            self.analyze_expression(expr.object_expr)
            return "Wild"

        if isinstance(expr, IndexExpression):
            self.analyze_expression(expr.collection)
            self.analyze_expression(expr.index)
            return "Wild"

        if isinstance(expr, AwaitExpression):
            return self.analyze_expression(expr.value)

        if isinstance(expr, LaunchExpression):
            return self.analyze_expression(expr.value)

        return None

    def analyze_identifier(self, expr):
        sym = self.lookup(expr.name)
        if sym is None:
            self.add_error(
                f"'{expr.name}' is not declared.",
                line=expr.line,
                hint=f"Declare it with: let {expr.name}: Type = value"
            )
            return None
        return sym.nimna_type

    def analyze_binary(self, expr):
        left_type  = self.analyze_expression(expr.left)
        right_type = self.analyze_expression(expr.right)

        if (expr.operator == "/" and
                isinstance(expr.right, IntegerLiteral) and
                expr.right.value == 0):
            self.add_error(
                "Division by zero detected.",
                line=expr.line,
                hint="Check the divisor value."
            )
            return left_type

        if (expr.operator == "+" and
                left_type == "Text" and
                right_type not in (None, "Text", "Wild")):
            self.add_error(
                f"Cannot concatenate 'Text' with '{right_type}'.",
                line=expr.line,
                hint="Convert to Text first using Text(value)."
            )
            return "Text"

        return self.get_binary_result_type(
            left_type, expr.operator, right_type
        )

    def analyze_assignment(self, expr):
        sym = self.lookup(expr.name)
        if sym is None:
            self.add_error(
                f"'{expr.name}' is not declared.",
                line=expr.line,
                hint=f"Declare it first: let {expr.name}: Type = value"
            )
            return None
        if sym.is_constant:
            self.add_error(
                f"Cannot reassign constant '{expr.name}'.",
                line=expr.line,
                hint="Use 'let' instead of 'constant' if reassignment is needed."
            )
            return sym.nimna_type
        value_type = self.analyze_expression(expr.value)
        if value_type and sym.nimna_type and sym.nimna_type != "Wild":
            compatible, err_msg = self.is_compatible(
                value_type, sym.nimna_type
            )
            if not compatible:
                self.add_error(err_msg, line=expr.line)
        return sym.nimna_type

    def analyze_call(self, expr):
        for arg in expr.arguments:
            self.analyze_expression(arg)
        if isinstance(expr.function, Identifier):
            func_name = expr.function.name
            sym       = self.lookup(func_name)
            if sym and sym.kind == "function":
                expected = len(sym.params)
                got      = len(expr.arguments)
                if got != expected:
                    self.add_error(
                        f"'{func_name}' expects {expected} argument(s) but got {got}.",
                        line=expr.line,
                        hint="Check the function signature."
                    )
                return sym.return_type
        return "Wild"
