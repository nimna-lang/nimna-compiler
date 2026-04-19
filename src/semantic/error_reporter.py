# ============================================
# NIMNA Language — Error Message System
# File: src/semantic/error_reporter.py
# Compiler: nimac
# ============================================


# ============================================
# ANSI COLOR CODES
# ============================================

class Color:
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    GREEN   = "\033[92m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE   = "\033[97m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"

    @staticmethod
    def disable():
        """Disable all colors (for plain output)."""
        Color.RED     = ""
        Color.YELLOW  = ""
        Color.GREEN   = ""
        Color.BLUE    = ""
        Color.CYAN    = ""
        Color.MAGENTA = ""
        Color.WHITE   = ""
        Color.BOLD    = ""
        Color.DIM     = ""
        Color.RESET   = ""


# ============================================
# ERROR LEVELS
# ============================================

LEVEL_ERROR   = "error"
LEVEL_WARNING = "warning"
LEVEL_INFO    = "info"
LEVEL_HINT    = "hint"


# ============================================
# ERROR CODES
# ============================================

# Type errors
E001 = "E001"   # Type mismatch
E002 = "E002"   # Unknown type
E003 = "E003"   # Unsafe conversion

# Variable errors
E010 = "E010"   # Undeclared variable
E011 = "E011"   # Duplicate declaration
E012 = "E012"   # Constant reassignment
E013 = "E013"   # Use before declaration

# Function errors
E020 = "E020"   # Function not declared
E021 = "E021"   # Wrong argument count
E022 = "E022"   # Wrong argument type
E023 = "E023"   # Return type mismatch
E024 = "E024"   # Duplicate function

# Scope errors
E030 = "E030"   # Out of scope
E031 = "E031"   # Break outside loop
E032 = "E032"   # Skip outside loop
E033 = "E033"   # Give outside function

# Memory errors
E040 = "E040"   # Use after move
E041 = "E041"   # Use after release
E042 = "E042"   # Double release
E043 = "E043"   # Write to frozen
E044 = "E044"   # Move while borrowed

# Syntax errors
E050 = "E050"   # Unexpected token
E051 = "E051"   # Missing token
E052 = "E052"   # Invalid name


# ============================================
# NIMNA ERROR CLASS
# ============================================

class NIMNAError:
    """
    A single NIMNA error with full context.
    """

    def __init__(self, code, message, level=LEVEL_ERROR,
                 filename="<nimna>", line=None, column=None,
                 hint=None, source_line=None):
        self.code        = code
        self.message     = message
        self.level       = level
        self.filename    = filename
        self.line        = line
        self.column      = column
        self.hint        = hint
        self.source_line = source_line

    def __repr__(self):
        return (
            f"NIMNAError({self.code}, "
            f"line={self.line}, "
            f"msg={self.message[:30]})"
        )


# ============================================
# ERROR REPORTER CLASS
# ============================================

class ErrorReporter:
    """
    NIMNA Error Reporter

    Produces clear, colored, helpful error messages
    with line numbers and hints.

    Example output:
    ──────────────────────────────────────────
    error[E001]: Type mismatch
      --> main.nim:5:10
       |
     5 |     let age: Whole = 3.14
       |                      ^^^^ Decimal cannot be assigned to Whole
       |
       = hint: Use explicit conversion: Whole(value)
    ──────────────────────────────────────────
    """

    def __init__(self, filename="<nimna>", source_code="",
                 use_color=True):
        self.filename    = filename
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        self.errors      = []
        self.warnings    = []
        self.use_color   = use_color

        if not use_color:
            Color.disable()


    # ==========================================
    # ADD ERRORS
    # ==========================================

    def add(self, code, message, line=None, column=None,
            hint=None, level=LEVEL_ERROR):
        """Add an error or warning."""

        source_line = None
        if line and 0 < line <= len(self.source_lines):
            source_line = self.source_lines[line - 1]

        entry = NIMNAError(
            code        = code,
            message     = message,
            level       = level,
            filename    = self.filename,
            line        = line,
            column      = column,
            hint        = hint,
            source_line = source_line
        )

        if level == LEVEL_WARNING:
            self.warnings.append(entry)
        else:
            self.errors.append(entry)

        return entry

    def error(self, code, message, line=None,
              column=None, hint=None):
        """Add an error."""
        return self.add(code, message, line, column,
                        hint, LEVEL_ERROR)

    def warning(self, code, message, line=None,
                column=None, hint=None):
        """Add a warning."""
        return self.add(code, message, line, column,
                        hint, LEVEL_WARNING)

    def info(self, message, line=None):
        """Add an info message."""
        return self.add("I000", message, line,
                        level=LEVEL_INFO)


    # ==========================================
    # FORMAT SINGLE ERROR
    # ==========================================

    def format_error(self, err):
        """
        Format one error into a readable string.
        """

        c = Color
        lines = []

        # ── Header line ──────────────────────
        if err.level == LEVEL_ERROR:
            level_color = c.RED
            level_label = "error"
        elif err.level == LEVEL_WARNING:
            level_color = c.YELLOW
            level_label = "warning"
        else:
            level_color = c.CYAN
            level_label = "info"

        header = (
            f"{c.BOLD}{level_color}{level_label}"
            f"[{err.code}]{c.RESET}"
            f"{c.BOLD}: {err.message}{c.RESET}"
        )
        lines.append(header)

        # ── Location line ────────────────────
        if err.line:
            loc = f"{err.filename}:{err.line}"
            if err.column:
                loc += f":{err.column}"
            lines.append(
                f"  {c.BLUE}-->{c.RESET} {loc}"
            )

        # ── Source line display ───────────────
        if err.source_line and err.line:
            line_num   = str(err.line)
            pad        = len(line_num)
            empty_pad  = " " * pad

            lines.append(
                f"  {c.BLUE}{empty_pad} |{c.RESET}"
            )
            lines.append(
                f"  {c.BLUE}{line_num} |{c.RESET} "
                f"{err.source_line}"
            )

            # Column pointer
            if err.column:
                pointer_pad = " " * (err.column - 1)
                pointer     = "^"
                lines.append(
                    f"  {c.BLUE}{empty_pad} |{c.RESET} "
                    f"{pointer_pad}"
                    f"{c.RED}{pointer}{c.RESET}"
                )
            else:
                lines.append(
                    f"  {c.BLUE}{empty_pad} |{c.RESET}"
                )

        elif err.line:
            pad       = len(str(err.line))
            empty_pad = " " * pad
            lines.append(
                f"  {c.BLUE}{empty_pad} |{c.RESET}"
            )

        # ── Hint line ────────────────────────
        if err.hint:
            lines.append(
                f"  {c.BLUE}  ={c.RESET} "
                f"{c.GREEN}hint{c.RESET}: {err.hint}"
            )

        lines.append("")
        return "\n".join(lines)


    # ==========================================
    # PRINT ALL ERRORS
    # ==========================================

    def print_all(self):
        """Print all errors and warnings."""

        all_items = self.errors + self.warnings
        all_items.sort(
            key=lambda e: e.line if e.line else 0
        )

        for item in all_items:
            print(self.format_error(item))

        self._print_summary()

    def print_errors(self):
        """Print only errors."""
        for err in self.errors:
            print(self.format_error(err))
        self._print_summary()

    def print_warnings(self):
        """Print only warnings."""
        for w in self.warnings:
            print(self.format_error(w))

    def _print_summary(self):
        """Print error/warning count summary."""
        c = Color

        e_count = len(self.errors)
        w_count = len(self.warnings)

        if e_count == 0 and w_count == 0:
            print(
                f"{c.GREEN}{c.BOLD}✓ No errors found.{c.RESET}"
            )
            return

        parts = []
        if e_count > 0:
            parts.append(
                f"{c.RED}{c.BOLD}"
                f"{e_count} error(s){c.RESET}"
            )
        if w_count > 0:
            parts.append(
                f"{c.YELLOW}{c.BOLD}"
                f"{w_count} warning(s){c.RESET}"
            )

        print(
            f"{c.BOLD}nimac{c.RESET} finished with "
            + ", ".join(parts)
        )


    # ==========================================
    # GET AS STRING
    # ==========================================

    def get_all_as_string(self):
        """Return all errors as a single string."""
        parts = []
        for item in self.errors + self.warnings:
            parts.append(self.format_error(item))
        return "\n".join(parts)


    # ==========================================
    # FACTORY METHODS
    # ==========================================

    def type_mismatch(self, from_type, to_type, line,
                      column=None):
        """Report a type mismatch error."""
        return self.error(
            code    = E001,
            message = f"Type mismatch: cannot assign "
                      f"'{from_type}' to '{to_type}'",
            line    = line,
            column  = column,
            hint    = f"Use explicit conversion: "
                      f"{to_type}(value)"
        )

    def unknown_type(self, type_name, line):
        """Report unknown type error."""
        return self.error(
            code    = E002,
            message = f"Unknown type '{type_name}'",
            line    = line,
            hint    = "Valid types: Whole, Text, Decimal, "
                      "Truth, Collection, ..."
        )

    def undeclared_variable(self, name, line):
        """Report undeclared variable error."""
        return self.error(
            code    = E010,
            message = f"'{name}' is not declared",
            line    = line,
            hint    = f"Declare it: let {name}: Type = value"
        )

    def duplicate_declaration(self, name, first_line, line):
        """Report duplicate declaration error."""
        return self.error(
            code    = E011,
            message = f"'{name}' is already declared "
                      f"(first at line {first_line})",
            line    = line,
            hint    = "Use a different name or remove "
                      "the duplicate declaration."
        )

    def constant_reassignment(self, name, line):
        """Report constant reassignment error."""
        return self.error(
            code    = E012,
            message = f"Cannot reassign constant '{name}'",
            line    = line,
            hint    = "Use 'let' instead of 'constant' "
                      "if you need to reassign."
        )

    def function_not_found(self, name, line):
        """Report function not declared error."""
        return self.error(
            code    = E020,
            message = f"Function '{name}' is not declared",
            line    = line,
            hint    = f"Define it: fn {name}() {{ ... }}"
        )

    def wrong_arg_count(self, name, expected, got, line):
        """Report wrong argument count error."""
        return self.error(
            code    = E021,
            message = f"'{name}' expects {expected} "
                      f"argument(s) but got {got}",
            line    = line,
            hint    = f"Check the function signature."
        )

    def return_type_mismatch(self, func_name, expected,
                              got, line):
        """Report return type mismatch error."""
        return self.error(
            code    = E023,
            message = f"Return type mismatch in "
                      f"'{func_name}': expected "
                      f"'{expected}' but got '{got}'",
            line    = line,
            hint    = "Change return type or convert value."
        )

    def break_outside_loop(self, line):
        """Report break outside loop error."""
        return self.error(
            code    = E031,
            message = "'break' used outside of a loop",
            line    = line,
            hint    = "'break' can only be used "
                      "inside a loop body."
        )

    def skip_outside_loop(self, line):
        """Report skip outside loop error."""
        return self.error(
            code    = E032,
            message = "'skip' used outside of a loop",
            line    = line,
            hint    = "'skip' can only be used "
                      "inside a loop body."
        )

    def give_outside_function(self, line):
        """Report give outside function error."""
        return self.error(
            code    = E033,
            message = "'give' used outside of a function",
            line    = line,
            hint    = "'give' can only be used "
                      "inside a function body."
        )

    def use_after_move(self, name, move_line, line):
        """Report use after move error."""
        return self.error(
            code    = E040,
            message = f"Use after move: '{name}' was "
                      f"moved at line {move_line}",
            line    = line,
            hint    = "Use 'shared' keyword if multiple "
                      "owners are needed."
        )

    def use_after_release(self, name, release_line, line):
        """Report use after release error."""
        return self.error(
            code    = E041,
            message = f"Use after release: '{name}' was "
                      f"released at line {release_line}",
            line    = line,
            hint    = "Do not use a variable after "
                      "releasing its memory."
        )

    def double_release(self, name, first_line, line):
        """Report double release error."""
        return self.error(
            code    = E042,
            message = f"Double release: '{name}' was "
                      f"already released at line {first_line}",
            line    = line,
            hint    = "Remove the duplicate 'release' call."
        )

    def write_to_frozen(self, name, line):
        """Report write to frozen variable error."""
        return self.error(
            code    = E043,
            message = f"Cannot write to frozen "
                      f"variable '{name}'",
            line    = line,
            hint    = "Remove 'freeze' or use a "
                      "different variable."
        )

    def unused_variable(self, name, declare_line):
        """Report unused variable warning."""
        return self.warning(
            code    = "W001",
            message = f"Variable '{name}' declared at "
                      f"line {declare_line} is never used",
            line    = declare_line,
            hint    = "Prefix with '_' to suppress: "
                      f"_{name}"
        )

    def division_by_zero(self, line):
        """Report division by zero error."""
        return self.error(
            code    = E001,
            message = "Division by zero detected",
            line    = line,
            hint    = "Check the divisor value."
        )


    # ==========================================
    # STATUS
    # ==========================================

    def has_errors(self):
        return len(self.errors) > 0

    def has_warnings(self):
        return len(self.warnings) > 0

    def error_count(self):
        return len(self.errors)

    def warning_count(self):
        return len(self.warnings)

    def clear(self):
        self.errors   = []
        self.warnings = []

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings
