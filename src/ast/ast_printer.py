# ============================================
# NIMNA Language — AST Tree Printer
# File: src/ast/ast_printer.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../lexer')
sys.path.insert(0, '../ast')

from nodes import *


class ASTPrinter:
    """
    NIMNA AST Tree Printer

    Prints the complete AST tree in a
    readable indented format.
    """

    def __init__(self):
        self.indent_level = 0
        self.indent_char  = "  "

    def indent(self):
        return self.indent_char * self.indent_level

    def print_node(self, node, label=""):
        if node is None:
            print(f"{self.indent()}{label}None")
            return

        prefix = f"{self.indent()}{label}" if label else self.indent()

        # ── Program ──────────────────────────
        if isinstance(node, Program):
            print(f"{prefix}Program ({len(node.statements)} statements)")
            self.indent_level += 1
            for stmt in node.statements:
                self.print_node(stmt)
            self.indent_level -= 1

        # ── Module ───────────────────────────
        elif isinstance(node, ModuleStatement):
            print(f"{prefix}ModuleStatement → '{node.name}'")

        # ── Bring ────────────────────────────
        elif isinstance(node, BringStatement):
            alias = f" from {node.alias}" if node.alias else ""
            print(f"{prefix}BringStatement → '{node.module_path}'{alias}")

        # ── Let ──────────────────────────────
        elif isinstance(node, LetStatement):
            type_str = f": {node.declared_type}" if node.declared_type else ""
            print(f"{prefix}LetStatement → '{node.name}'{type_str}")
            self.indent_level += 1
            self.print_node(node.value, "value: ")
            self.indent_level -= 1

        # ── Constant ─────────────────────────
        elif isinstance(node, ConstantStatement):
            type_str = f": {node.declared_type}" if node.declared_type else ""
            print(f"{prefix}ConstantStatement → '{node.name}'{type_str}")
            self.indent_level += 1
            self.print_node(node.value, "value: ")
            self.indent_level -= 1

        # ── Function ─────────────────────────
        elif isinstance(node, FunctionDeclaration):
            async_str = "async " if node.is_async else ""
            ret_str   = f" -> {node.return_type}" if node.return_type else ""
            params    = ", ".join(f"{p.name}:{p.param_type}" for p in node.params)
            print(f"{prefix}{async_str}FunctionDeclaration → '{node.name}'({params}){ret_str}")
            self.indent_level += 1
            for stmt in node.body:
                self.print_node(stmt)
            self.indent_level -= 1

        # ── Return ───────────────────────────
        elif isinstance(node, ReturnStatement):
            print(f"{prefix}ReturnStatement")
            self.indent_level += 1
            self.print_node(node.value, "value: ")
            self.indent_level -= 1

        # ── Raise ────────────────────────────
        elif isinstance(node, RaiseStatement):
            print(f"{prefix}RaiseStatement")
            self.indent_level += 1
            self.print_node(node.value, "value: ")
            self.indent_level -= 1

        # ── Object ───────────────────────────
        elif isinstance(node, ObjectDeclaration):
            parent = f" grow {node.parent}" if node.parent else ""
            print(f"{prefix}ObjectDeclaration → '{node.name}'{parent}")
            self.indent_level += 1
            for field in node.fields:
                self.print_node(field)
            for method in node.methods:
                self.print_node(method)
            self.indent_level -= 1

        # ── Record ───────────────────────────
        elif isinstance(node, RecordDeclaration):
            print(f"{prefix}RecordDeclaration → '{node.name}'")
            self.indent_level += 1
            for field in node.fields:
                self.print_node(field)
            self.indent_level -= 1

        # ── Field ────────────────────────────
        elif isinstance(node, FieldDeclaration):
            access = "open" if node.is_public else "hidden"
            print(f"{prefix}FieldDeclaration → {access} '{node.name}': {node.field_type}")

        # ── If ───────────────────────────────
        elif isinstance(node, IfStatement):
            print(f"{prefix}IfStatement")
            self.indent_level += 1
            self.print_node(node.condition, "condition: ")
            print(f"{self.indent()}then:")
            self.indent_level += 1
            for stmt in node.then_body:
                self.print_node(stmt)
            self.indent_level -= 1
            for elif_cond, elif_body in node.elif_clauses:
                print(f"{self.indent()}elif:")
                self.indent_level += 1
                self.print_node(elif_cond, "condition: ")
                for stmt in elif_body:
                    self.print_node(stmt)
                self.indent_level -= 1
            if node.else_body:
                print(f"{self.indent()}else:")
                self.indent_level += 1
                for stmt in node.else_body:
                    self.print_node(stmt)
                self.indent_level -= 1
            self.indent_level -= 1

        # ── Match ────────────────────────────
        elif isinstance(node, MatchStatement):
            print(f"{prefix}MatchStatement ({len(node.arms)} arms)")
            self.indent_level += 1
            self.print_node(node.subject, "subject: ")
            for i, arm in enumerate(node.arms):
                self.print_node(arm, f"arm[{i}]: ")
            self.indent_level -= 1

        # ── Match Arm ────────────────────────
        elif isinstance(node, MatchArm):
            wildcard = "(wildcard)" if node.is_wildcard else ""
            print(f"{prefix}MatchArm {wildcard}")
            self.indent_level += 1
            if not node.is_wildcard:
                self.print_node(node.pattern, "pattern: ")
            for stmt in node.body:
                self.print_node(stmt)
            self.indent_level -= 1

        # ── For Loop ─────────────────────────
        elif isinstance(node, ForLoop):
            print(f"{prefix}ForLoop → var='{node.variable}'")
            self.indent_level += 1
            self.print_node(node.range_expr, "range: ")
            for stmt in node.body:
                self.print_node(stmt)
            self.indent_level -= 1

        # ── While Loop ───────────────────────
        elif isinstance(node, WhileLoop):
            print(f"{prefix}WhileLoop")
            self.indent_level += 1
            self.print_node(node.condition, "condition: ")
            for stmt in node.body:
                self.print_node(stmt)
            self.indent_level -= 1

        # ── Do-Until Loop ────────────────────
        elif isinstance(node, DoUntilLoop):
            print(f"{prefix}DoUntilLoop")
            self.indent_level += 1
            for stmt in node.body:
                self.print_node(stmt)
            self.print_node(node.condition, "until: ")
            self.indent_level -= 1

        # ── Foreach Loop ─────────────────────
        elif isinstance(node, ForeachLoop):
            print(f"{prefix}ForeachLoop → var='{node.variable}'")
            self.indent_level += 1
            self.print_node(node.collection, "collection: ")
            for stmt in node.body:
                self.print_node(stmt)
            self.indent_level -= 1

        # ── Parallel Loop ────────────────────
        elif isinstance(node, ParallelLoop):
            print(f"{prefix}ParallelLoop → var='{node.variable}'")
            self.indent_level += 1
            self.print_node(node.range_expr, "range: ")
            for stmt in node.body:
                self.print_node(stmt)
            self.indent_level -= 1

        # ── Break / Skip ─────────────────────
        elif isinstance(node, BreakStatement):
            print(f"{prefix}BreakStatement")

        elif isinstance(node, SkipStatement):
            print(f"{prefix}SkipStatement")

        # ── Attempt ──────────────────────────
        elif isinstance(node, AttemptStatement):
            has_always = node.always_body is not None
            print(f"{prefix}AttemptStatement (always={has_always})")
            self.indent_level += 1
            print(f"{self.indent()}attempt:")
            self.indent_level += 1
            for stmt in node.attempt_body:
                self.print_node(stmt)
            self.indent_level -= 1
            print(f"{self.indent()}rescue '{node.rescue_var}':")
            self.indent_level += 1
            for stmt in node.rescue_body:
                self.print_node(stmt)
            self.indent_level -= 1
            if node.always_body:
                print(f"{self.indent()}always:")
                self.indent_level += 1
                for stmt in node.always_body:
                    self.print_node(stmt)
                self.indent_level -= 1
            self.indent_level -= 1

        # ── Binary Expression ────────────────
        elif isinstance(node, BinaryExpression):
            print(f"{prefix}BinaryExpression '{node.operator}'")
            self.indent_level += 1
            self.print_node(node.left,  "left:  ")
            self.print_node(node.right, "right: ")
            self.indent_level -= 1

        # ── Unary Expression ─────────────────
        elif isinstance(node, UnaryExpression):
            print(f"{prefix}UnaryExpression '{node.operator}'")
            self.indent_level += 1
            self.print_node(node.operand, "operand: ")
            self.indent_level -= 1

        # ── Assignment ───────────────────────
        elif isinstance(node, AssignmentExpression):
            print(f"{prefix}AssignmentExpression '{node.name}' {node.operator}")
            self.indent_level += 1
            self.print_node(node.value, "value: ")
            self.indent_level -= 1

        # ── Type Cast ────────────────────────
        elif isinstance(node, TypeCastExpression):
            print(f"{prefix}TypeCastExpression → {node.target_type}")
            self.indent_level += 1
            self.print_node(node.value, "value: ")
            self.indent_level -= 1

        # ── Type Constructor ─────────────────
        elif isinstance(node, TypeConstructorExpression):
            print(f"{prefix}TypeConstructorExpression → {node.type_name}()")
            self.indent_level += 1
            self.print_node(node.argument, "arg: ")
            self.indent_level -= 1

        # ── Range ────────────────────────────
        elif isinstance(node, RangeExpression):
            kind = "inclusive" if node.inclusive else "exclusive"
            inf  = " (infinite)" if node.infinite else ""
            print(f"{prefix}RangeExpression [{kind}]{inf}")
            self.indent_level += 1
            self.print_node(node.start, "start: ")
            if not node.infinite:
                self.print_node(node.end, "end:   ")
            self.indent_level -= 1

        # ── Pipeline ─────────────────────────
        elif isinstance(node, PipelineExpression):
            print(f"{prefix}PipelineExpression |>")
            self.indent_level += 1
            self.print_node(node.left,  "left:  ")
            self.print_node(node.right, "right: ")
            self.indent_level -= 1

        # ── Call Expression ──────────────────
        elif isinstance(node, CallExpression):
            func_name = self._get_name(node.function)
            print(f"{prefix}CallExpression → {func_name}({len(node.arguments)} args)")
            self.indent_level += 1
            for i, arg in enumerate(node.arguments):
                self.print_node(arg, f"arg[{i}]: ")
            self.indent_level -= 1

        # ── Member Access ────────────────────
        elif isinstance(node, MemberAccessExpression):
            full = self._get_name(node)
            print(f"{prefix}MemberAccess → {full}")

        # ── Index ────────────────────────────
        elif isinstance(node, IndexExpression):
            print(f"{prefix}IndexExpression")
            self.indent_level += 1
            self.print_node(node.collection, "collection: ")
            self.print_node(node.index,      "index:      ")
            self.indent_level -= 1

        # ── Literals ─────────────────────────
        elif isinstance(node, IntegerLiteral):
            print(f"{prefix}IntegerLiteral → {node.value}")

        elif isinstance(node, DecimalLiteral):
            print(f"{prefix}DecimalLiteral → {node.value}")

        elif isinstance(node, TextLiteral):
            val = repr(node.value) if len(node.value) <= 30 else repr(node.value[:30]) + "..."
            print(f"{prefix}TextLiteral → {val}")

        elif isinstance(node, LetterLiteral):
            print(f"{prefix}LetterLiteral → {repr(node.value)}")

        elif isinstance(node, TruthLiteral):
            print(f"{prefix}TruthLiteral → {node.value}")

        elif isinstance(node, NothingLiteral):
            print(f"{prefix}NothingLiteral → nothing")

        elif isinstance(node, CollectionLiteral):
            print(f"{prefix}CollectionLiteral ({len(node.elements)} elements)")
            self.indent_level += 1
            for i, elem in enumerate(node.elements):
                self.print_node(elem, f"[{i}]: ")
            self.indent_level -= 1

        # ── Identifier ───────────────────────
        elif isinstance(node, Identifier):
            print(f"{prefix}Identifier → '{node.name}'")

        # ── Await / Launch ───────────────────
        elif isinstance(node, AwaitExpression):
            print(f"{prefix}AwaitExpression")
            self.indent_level += 1
            self.print_node(node.value, "value: ")
            self.indent_level -= 1

        elif isinstance(node, LaunchExpression):
            print(f"{prefix}LaunchExpression")
            self.indent_level += 1
            self.print_node(node.value, "value: ")
            self.indent_level -= 1

        else:
            print(f"{prefix}UnknownNode → {type(node).__name__}")


    def _get_name(self, node):
        """Resolve member access chain to string."""
        if isinstance(node, Identifier):
            return node.name
        elif isinstance(node, MemberAccessExpression):
            obj = self._get_name(node.object_expr)
            return f"{obj}.{node.member}"
        return str(node)
