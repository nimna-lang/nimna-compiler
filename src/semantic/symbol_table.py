# ============================================
# NIMNA Language — Symbol Table
# File: src/semantic/symbol_table.py
# Compiler: nimac
# ============================================


# ============================================
# SYMBOL KINDS
# ============================================

KIND_VARIABLE = "variable"
KIND_CONSTANT = "constant"
KIND_FUNCTION = "function"
KIND_PARAM    = "param"
KIND_OBJECT   = "object"
KIND_RECORD   = "record"
KIND_FIELD    = "field"
KIND_MODULE   = "module"
KIND_CONSTANT = "constant"


# ============================================
# SYMBOL ENTRY
# ============================================

class Symbol:
    """
    One entry in the Symbol Table.

    Stores all information about a declared name:
    variable, function, object, record, or parameter.
    """

    def __init__(self, name, kind, nimna_type,
                 scope_level, line, is_constant=False):
        self.name        = name
        self.kind        = kind
        self.nimna_type  = nimna_type
        self.scope_level = scope_level
        self.line        = line
        self.is_constant = is_constant
        self.is_assigned = False
        self.is_used     = False
        self.params      = []
        self.return_type = None
        self.fields      = {}

    def mark_used(self):
        self.is_used = True

    def mark_assigned(self):
        self.is_assigned = True

    def __repr__(self):
        return (
            f"Symbol("
            f"name={self.name}, "
            f"kind={self.kind}, "
            f"type={self.nimna_type}, "
            f"scope={self.scope_level}, "
            f"line={self.line})"
        )

    def summary(self):
        const_str  = " [const]"   if self.is_constant else ""
        used_str   = " [used]"    if self.is_used     else " [unused]"
        assign_str = " [assigned]" if self.is_assigned else ""
        return (
            f"{self.kind:<10} {self.name:<20} "
            f"{self.nimna_type:<15} "
            f"scope={self.scope_level} "
            f"line={self.line}"
            f"{const_str}{used_str}{assign_str}"
        )


# ============================================
# SCOPE
# ============================================

class Scope:
    """
    A single scope level in the symbol table.

    Examples:
        Global scope  (level 0)
        Function scope (level 1)
        Block scope   (level 2)
    """

    def __init__(self, level, scope_type="block", name=None):
        self.level      = level
        self.scope_type = scope_type
        self.name       = name
        self.symbols    = {}

    def declare(self, symbol):
        """Add a symbol to this scope."""
        self.symbols[symbol.name] = symbol

    def lookup(self, name):
        """Find a symbol in this scope only."""
        return self.symbols.get(name, None)

    def has(self, name):
        """Check if name exists in this scope."""
        return name in self.symbols

    def all_symbols(self):
        """Return all symbols in this scope."""
        return list(self.symbols.values())

    def unused_variables(self):
        """Return all unused variables in this scope."""
        return [
            sym for sym in self.symbols.values()
            if sym.kind in (KIND_VARIABLE, KIND_PARAM)
            and not sym.is_used
        ]

    def __repr__(self):
        name_str = f" ({self.name})" if self.name else ""
        return (
            f"Scope(level={self.level}, "
            f"type={self.scope_type}{name_str}, "
            f"symbols={len(self.symbols)})"
        )


# ============================================
# SYMBOL TABLE
# ============================================

class SymbolTable:
    """
    NIMNA Symbol Table

    Manages all scopes and symbols for the
    entire program.

    Usage:
        table = SymbolTable()
        table.enter_scope("function", "main")
        table.declare("age", "variable", "Whole", line=5)
        sym = table.lookup("age")
        table.exit_scope()
    """

    def __init__(self, filename="<nimna>"):
        self.filename    = filename
        self.scope_stack = [Scope(level=0, scope_type="global")]
        self.errors      = []
        self.warnings    = []


    # ==========================================
    # SCOPE MANAGEMENT
    # ==========================================

    def enter_scope(self, scope_type="block", name=None):
        """Enter a new scope."""
        level = len(self.scope_stack)
        new_scope = Scope(level=level, scope_type=scope_type, name=name)
        self.scope_stack.append(new_scope)

    def exit_scope(self):
        """
        Exit current scope.
        Warns about unused variables before exiting.
        """
        if len(self.scope_stack) <= 1:
            return

        current = self.current_scope()
        unused  = current.unused_variables()

        for sym in unused:
            if not sym.name.startswith("_"):
                self.warnings.append(
                    f"[NIMNA Warning] Variable '{sym.name}' "
                    f"declared at line {sym.line} is never used."
                )

        self.scope_stack.pop()

    def current_scope(self):
        """Return current scope."""
        return self.scope_stack[-1]

    def global_scope(self):
        """Return global scope."""
        return self.scope_stack[0]

    def scope_depth(self):
        """Return current scope depth."""
        return len(self.scope_stack) - 1


    # ==========================================
    # SYMBOL DECLARATION
    # ==========================================

    def declare(self, name, kind, nimna_type, line,
                is_constant=False):
        """
        Declare a new symbol in current scope.

        Returns:
            Symbol if success, None if duplicate
        """
        current = self.current_scope()

        if current.has(name):
            existing = current.lookup(name)
            self.errors.append(
                f"[Line {line}] '{name}' is already declared "
                f"in this scope (first declared at line {existing.line})."
            )
            return None

        symbol = Symbol(
            name        = name,
            kind        = kind,
            nimna_type  = nimna_type,
            scope_level = self.scope_depth(),
            line        = line,
            is_constant = is_constant
        )
        current.declare(symbol)
        return symbol

    def declare_function(self, name, return_type, params, line):
        """
        Declare a function symbol with parameters and return type.
        """
        sym = self.declare(
            name       = name,
            kind       = KIND_FUNCTION,
            nimna_type = return_type or "Nothing",
            line       = line
        )
        if sym:
            sym.params      = params
            sym.return_type = return_type
        return sym

    def declare_object(self, name, fields, line):
        """
        Declare an object symbol with its fields.
        """
        sym = self.declare(
            name       = name,
            kind       = KIND_OBJECT,
            nimna_type = name,
            line       = line
        )
        if sym:
            sym.fields = {f.name: f.field_type for f in fields}
        return sym

    def declare_record(self, name, fields, line):
        """
        Declare a record symbol with its fields.
        """
        sym = self.declare(
            name       = name,
            kind       = KIND_RECORD,
            nimna_type = name,
            line       = line
        )
        if sym:
            sym.fields = {f.name: f.field_type for f in fields}
        return sym


    # ==========================================
    # SYMBOL LOOKUP
    # ==========================================

    def lookup(self, name):
        """
        Look up a symbol across all scopes.
        Searches from innermost to outermost scope.

        Returns:
            Symbol or None
        """
        for scope in reversed(self.scope_stack):
            sym = scope.lookup(name)
            if sym is not None:
                return sym
        return None

    def lookup_current(self, name):
        """Look up only in current scope."""
        return self.current_scope().lookup(name)

    def lookup_global(self, name):
        """Look up only in global scope."""
        return self.global_scope().lookup(name)

    def exists(self, name):
        """Check if name exists in any scope."""
        return self.lookup(name) is not None

    def exists_in_current(self, name):
        """Check if name exists in current scope only."""
        return self.current_scope().has(name)


    # ==========================================
    # SYMBOL USAGE
    # ==========================================

    def mark_used(self, name):
        """Mark a symbol as used."""
        sym = self.lookup(name)
        if sym:
            sym.mark_used()

    def mark_assigned(self, name):
        """Mark a symbol as assigned."""
        sym = self.lookup(name)
        if sym:
            sym.mark_assigned()


    # ==========================================
    # QUERIES
    # ==========================================

    def get_all_symbols(self):
        """Return all symbols from all scopes."""
        all_symbols = []
        for scope in self.scope_stack:
            all_symbols.extend(scope.all_symbols())
        return all_symbols

    def get_all_functions(self):
        """Return all declared functions."""
        return [
            sym for sym in self.get_all_symbols()
            if sym.kind == KIND_FUNCTION
        ]

    def get_all_variables(self):
        """Return all declared variables."""
        return [
            sym for sym in self.get_all_symbols()
            if sym.kind in (KIND_VARIABLE, KIND_CONSTANT)
        ]

    def get_all_objects(self):
        """Return all declared objects."""
        return [
            sym for sym in self.get_all_symbols()
            if sym.kind == KIND_OBJECT
        ]

    def get_all_records(self):
        """Return all declared records."""
        return [
            sym for sym in self.get_all_symbols()
            if sym.kind == KIND_RECORD
        ]

    def get_unused_variables(self):
        """Return all unused variables."""
        return [
            sym for sym in self.get_all_variables()
            if not sym.is_used
        ]


    # ==========================================
    # DISPLAY
    # ==========================================

    def print_table(self):
        """Print the complete symbol table."""
        print("=" * 65)
        print("NIMNA SYMBOL TABLE")
        print("=" * 65)
        for scope in self.scope_stack:
            scope_name = f" ({scope.name})" if scope.name else ""
            print(f"\nScope Level {scope.level} [{scope.scope_type}{scope_name}]")
            print("-" * 65)
            if scope.symbols:
                for sym in scope.symbols.values():
                    print(f"  {sym.summary()}")
            else:
                print("  (empty)")
        print("=" * 65)

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0
