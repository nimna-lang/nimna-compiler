# ============================================
# NIMNA Language — Memory Safety Checker
# File: src/semantic/memory_checker.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../semantic')

from symbol_table import SymbolTable, KIND_VARIABLE, KIND_PARAM


# ============================================
# OWNERSHIP STATES
# ============================================

STATE_OWNED    = "owned"      # Variable owns its value
STATE_BORROWED = "borrowed"   # Temporarily borrowed
STATE_SHARED   = "shared"     # Shared reference
STATE_MOVED    = "moved"      # Ownership transferred
STATE_FROZEN   = "frozen"     # Immutable reference
STATE_RELEASED = "released"   # Memory released


# ============================================
# MEMORY KEYWORDS
# ============================================

MEMORY_KEYWORDS = {
    "own", "borrow", "shared",
    "freeze", "release",
    "guard", "shield", "managed",
    "raw", "fence",
}


# ============================================
# MEMORY ENTRY
# ============================================

class MemoryEntry:
    """
    Tracks ownership state of one variable.
    """

    def __init__(self, name, state=STATE_OWNED, line=0):
        self.name      = name
        self.state     = state
        self.line      = line
        self.borrow_count   = 0
        self.is_frozen      = False
        self.is_managed     = False

    def __repr__(self):
        return (
            f"MemoryEntry(name={self.name}, "
            f"state={self.state}, "
            f"borrows={self.borrow_count})"
        )


# ============================================
# MEMORY CHECKER CLASS
# ============================================

class MemoryChecker:
    """
    NIMNA Memory Safety Checker

    Validates ownership rules:
    1. own    — Variable owns its value exclusively
    2. borrow — Temporary read-only access
    3. shared — Multiple owners allowed
    4. freeze — Make immutable
    5. release — Free memory early
    6. guard   — Safe access check
    7. Use after move detection
    8. Double release detection
    9. Borrow while frozen check
    """

    def __init__(self, symbol_table, filename="<nimna>"):
        self.table    = symbol_table
        self.filename = filename
        self.errors   = []
        self.warnings = []
        # name → MemoryEntry
        self.memory_map = {}


    # ==========================================
    # OWNERSHIP OPERATIONS
    # ==========================================

    def declare_owned(self, name, line):
        """
        Declare variable with 'own' ownership.
        Full exclusive ownership.
        """
        self.memory_map[name] = MemoryEntry(
            name  = name,
            state = STATE_OWNED,
            line  = line
        )
        return True


    def declare_shared(self, name, line):
        """
        Declare variable with 'shared' ownership.
        Multiple references allowed.
        """
        self.memory_map[name] = MemoryEntry(
            name  = name,
            state = STATE_SHARED,
            line  = line
        )
        return True


    def declare_managed(self, name, line):
        """
        Declare variable as 'managed'.
        Garbage collected — no manual release needed.
        """
        entry = MemoryEntry(
            name  = name,
            state = STATE_OWNED,
            line  = line
        )
        entry.is_managed = True
        self.memory_map[name] = entry
        return True


    def borrow(self, name, line):
        """
        Borrow a variable — temporary read access.

        Rules:
        - Cannot borrow a moved variable
        - Cannot borrow a released variable
        - Can borrow owned or shared variables
        """

        entry = self.memory_map.get(name)

        if entry is None:
            # Not in memory map — OK (simple variable)
            return True

        if entry.state == STATE_MOVED:
            self.errors.append(
                f"[Line {line}] Cannot borrow '{name}' — "
                f"ownership was already moved. "
                f"Variable moved at line {entry.line}."
            )
            return False

        if entry.state == STATE_RELEASED:
            self.errors.append(
                f"[Line {line}] Cannot borrow '{name}' — "
                f"memory was already released at line {entry.line}."
            )
            return False

        entry.borrow_count += 1
        entry.state = STATE_BORROWED
        return True


    def return_borrow(self, name, line):
        """
        Return a borrowed reference.
        """
        entry = self.memory_map.get(name)
        if entry and entry.state == STATE_BORROWED:
            entry.borrow_count = max(0, entry.borrow_count - 1)
            if entry.borrow_count == 0:
                entry.state = STATE_OWNED
        return True


    def freeze(self, name, line):
        """
        Freeze a variable — make immutable.

        Rules:
        - Cannot freeze a moved variable
        - Cannot freeze a released variable
        - Cannot write to a frozen variable
        """

        entry = self.memory_map.get(name)

        if entry is None:
            return True

        if entry.state == STATE_MOVED:
            self.errors.append(
                f"[Line {line}] Cannot freeze '{name}' — "
                f"ownership was already moved."
            )
            return False

        if entry.state == STATE_RELEASED:
            self.errors.append(
                f"[Line {line}] Cannot freeze '{name}' — "
                f"memory already released."
            )
            return False

        entry.is_frozen = True
        entry.state     = STATE_FROZEN
        return True


    def release(self, name, line):
        """
        Manually release memory with 'release' keyword.

        Rules:
        - Cannot release already released memory
        - Cannot release a moved variable
        - Managed variables auto-release (warning)
        """

        entry = self.memory_map.get(name)

        if entry is None:
            self.warnings.append(
                f"[Line {line}] 'release' called on '{name}' "
                f"which has no tracked ownership."
            )
            return True

        if entry.state == STATE_RELEASED:
            self.errors.append(
                f"[Line {line}] Double release detected for '{name}'. "
                f"Memory was already released at line {entry.line}."
            )
            return False

        if entry.state == STATE_MOVED:
            self.errors.append(
                f"[Line {line}] Cannot release '{name}' — "
                f"ownership was already moved."
            )
            return False

        if entry.is_managed:
            self.warnings.append(
                f"[Line {line}] '{name}' is managed memory. "
                f"Manual release is not needed — "
                f"it will be auto-released."
            )

        entry.state = STATE_RELEASED
        entry.line  = line
        return True


    def check_write(self, name, line):
        """
        Check if writing to a variable is allowed.

        Rules:
        - Cannot write to frozen variable
        - Cannot write to moved variable
        - Cannot write to released variable
        """

        entry = self.memory_map.get(name)

        if entry is None:
            return True

        if entry.is_frozen or entry.state == STATE_FROZEN:
            self.errors.append(
                f"[Line {line}] Cannot write to '{name}' — "
                f"it is frozen (immutable). "
                f"Use 'release' to unfreeze first."
            )
            return False

        if entry.state == STATE_MOVED:
            self.errors.append(
                f"[Line {line}] Cannot write to '{name}' — "
                f"ownership was moved at line {entry.line}."
            )
            return False

        if entry.state == STATE_RELEASED:
            self.errors.append(
                f"[Line {line}] Cannot write to '{name}' — "
                f"memory was released at line {entry.line}. "
                f"This is a use-after-free error."
            )
            return False

        return True


    def check_read(self, name, line):
        """
        Check if reading a variable is allowed.

        Rules:
        - Cannot read moved variable
        - Cannot read released variable
        """

        entry = self.memory_map.get(name)

        if entry is None:
            return True

        if entry.state == STATE_MOVED:
            self.errors.append(
                f"[Line {line}] Cannot read '{name}' — "
                f"ownership was moved at line {entry.line}. "
                f"Use 'shared' if multiple owners needed."
            )
            return False

        if entry.state == STATE_RELEASED:
            self.errors.append(
                f"[Line {line}] Use-after-free: '{name}' was "
                f"released at line {entry.line}."
            )
            return False

        return True


    def move_ownership(self, from_name, to_name, line):
        """
        Transfer ownership from one variable to another.

        Rules:
        - Cannot move already moved variable
        - Cannot move released variable
        - After move, original is invalid
        """

        entry = self.memory_map.get(from_name)

        if entry is None:
            return True

        if entry.state == STATE_MOVED:
            self.errors.append(
                f"[Line {line}] Cannot move '{from_name}' — "
                f"ownership was already moved at line {entry.line}."
            )
            return False

        if entry.state == STATE_RELEASED:
            self.errors.append(
                f"[Line {line}] Cannot move '{from_name}' — "
                f"memory already released."
            )
            return False

        if entry.state == STATE_BORROWED:
            self.errors.append(
                f"[Line {line}] Cannot move '{from_name}' — "
                f"it is currently borrowed."
            )
            return False

        # Transfer ownership
        new_entry = MemoryEntry(
            name  = to_name,
            state = STATE_OWNED,
            line  = line
        )
        new_entry.is_managed = entry.is_managed
        self.memory_map[to_name] = new_entry

        # Mark original as moved
        entry.state = STATE_MOVED
        entry.line  = line
        return True


    # ==========================================
    # STATE QUERIES
    # ==========================================

    def get_state(self, name):
        """Get ownership state of a variable."""
        entry = self.memory_map.get(name)
        if entry:
            return entry.state
        return STATE_OWNED

    def is_frozen(self, name):
        """Check if variable is frozen."""
        entry = self.memory_map.get(name)
        return entry.is_frozen if entry else False

    def is_moved(self, name):
        """Check if variable ownership was moved."""
        entry = self.memory_map.get(name)
        return entry.state == STATE_MOVED if entry else False

    def is_released(self, name):
        """Check if variable memory was released."""
        entry = self.memory_map.get(name)
        return entry.state == STATE_RELEASED if entry else False

    def is_managed(self, name):
        """Check if variable is managed memory."""
        entry = self.memory_map.get(name)
        return entry.is_managed if entry else False


    # ==========================================
    # ERROR AND WARNING GETTERS
    # ==========================================

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0

    def clear(self):
        self.errors     = []
        self.warnings   = []
        self.memory_map = {}
