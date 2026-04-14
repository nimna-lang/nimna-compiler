# ============================================
# NIMNA Language — ObjectDeclaration Handler
# File: src/ast/object_handler.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../lexer')

from nodes import (
    ObjectDeclaration,
    RecordDeclaration,
    FieldDeclaration,
    FunctionDeclaration,
    Parameter,
)


# ============================================
# VALID FIELD TYPES
# ============================================

VALID_FIELD_TYPES = {
    "Tiny", "Short", "Whole", "Long", "Huge",
    "Decimal", "Precise", "Exact",
    "Text", "Letter", "Symbol",
    "Truth", "Bit",
    "Sequence", "Collection", "Mapping", "Unique", "Bundle",
    "Maybe", "Outcome", "Task", "Flow",
    "Action", "Wild", "Nothing",
}


# ============================================
# OBJECT DECLARATION HANDLER CLASS
# ============================================

class ObjectHandler:
    """
    NIMNA ObjectDeclaration Handler

    Processes object declarations and validates:
    - Object name
    - Parent object (grow keyword)
    - Fields (open / hidden)
    - Methods
    - Duplicate field names
    - Duplicate method names
    """

    def __init__(self, filename="<nimna>"):
        self.filename       = filename
        self.errors         = []
        self.warnings       = []
        self.declared_objs  = set()


    def create_object(self, name, parent, fields, methods,
                      line=None, column=None):
        """
        Create a validated ObjectDeclaration node.

        Parameters:
            name    : str  — Object name
            parent  : str  — Parent object name or None
            fields  : list — List of FieldDeclaration nodes
            methods : list — List of FunctionDeclaration nodes
            line    : int  — Line number
            column  : int  — Column number

        Returns:
            ObjectDeclaration node or None if invalid
        """

        # Step 1: Validate object name
        name_valid, name_error = self._validate_name(name)
        if not name_valid:
            self.errors.append(f"[Line {line}] {name_error}")
            return None

        # Step 2: Check duplicate object name
        if name in self.declared_objs:
            self.errors.append(
                f"[Line {line}] Object '{name}' is already declared."
            )
            return None

        # Step 3: Validate parent name
        if parent:
            parent_valid, parent_error = self._validate_name(parent)
            if not parent_valid:
                self.errors.append(
                    f"[Line {line}] Invalid parent name: {parent_error}"
                )
                return None

            # Object cannot grow itself
            if parent == name:
                self.errors.append(
                    f"[Line {line}] Object '{name}' cannot grow itself."
                )
                return None

        # Step 4: Validate fields
        field_errors = self._validate_fields(fields, line)
        if field_errors:
            self.errors.extend(field_errors)
            return None

        # Step 5: Validate methods
        method_errors = self._validate_methods(methods, line)
        if method_errors:
            self.errors.extend(method_errors)
            return None

        # Step 6: Check field and method name conflicts
        field_names  = {f.name for f in fields}
        method_names = {m.name for m in methods}
        conflicts    = field_names & method_names

        if conflicts:
            self.errors.append(
                f"[Line {line}] Name conflict in '{name}': "
                f"'{', '.join(conflicts)}' used as both field and method."
            )
            return None

        # Step 7: Empty object warning
        if not fields and not methods:
            self.warnings.append(
                f"[Line {line}] Object '{name}' is empty."
            )

        # Step 8: Register object name
        self.declared_objs.add(name)

        # Step 9: Create and return node
        return ObjectDeclaration(
            name    = name,
            parent  = parent,
            fields  = fields,
            methods = methods,
            line    = line,
            column  = column
        )


    def create_record(self, name, fields, line=None, column=None):
        """
        Create a validated RecordDeclaration node.

        Example:
            record Person {
                name : Text
                age  : Whole
            }
        """

        # Step 1: Validate record name
        name_valid, name_error = self._validate_name(name)
        if not name_valid:
            self.errors.append(f"[Line {line}] {name_error}")
            return None

        # Step 2: Validate fields
        field_errors = self._validate_fields(fields, line)
        if field_errors:
            self.errors.extend(field_errors)
            return None

        # Step 3: Empty record warning
        if not fields:
            self.warnings.append(
                f"[Line {line}] Record '{name}' has no fields."
            )

        return RecordDeclaration(
            name   = name,
            fields = fields,
            line   = line,
            column = column
        )


    def create_field(self, name, field_type, is_public=True,
                     line=None, column=None):
        """
        Create a validated FieldDeclaration node.

        Example:
            open   name : Text
            hidden age  : Whole
        """

        # Validate field name
        if not name or not (name[0].isalpha() or name[0] == '_'):
            self.errors.append(
                f"[Line {line}] Invalid field name '{name}'."
            )
            return None

        # Validate field type
        if field_type not in VALID_FIELD_TYPES:
            self.errors.append(
                f"[Line {line}] Unknown field type '{field_type}' "
                f"for field '{name}'."
            )
            return None

        return FieldDeclaration(
            name       = name,
            field_type = field_type,
            is_public  = is_public,
            line       = line,
            column     = column
        )


    def _validate_name(self, name):
        """Validate object or record name."""

        if not name:
            return False, "Name cannot be empty."

        if not name[0].isupper():
            return False, (
                f"Object/Record name '{name}' must start with "
                f"an uppercase letter. Example: 'Animal' not 'animal'."
            )

        if not (name[0].isalpha() or name[0] == '_'):
            return False, (
                f"Name '{name}' must start with a letter."
            )

        return True, ""


    def _validate_fields(self, fields, line):
        """Validate all fields — check duplicates and types."""

        errors     = []
        seen_names = set()

        for field in fields:
            if field.name in seen_names:
                errors.append(
                    f"[Line {line}] Duplicate field name '{field.name}'."
                )
            else:
                seen_names.add(field.name)

            if field.field_type not in VALID_FIELD_TYPES:
                errors.append(
                    f"[Line {line}] Unknown type '{field.field_type}' "
                    f"for field '{field.name}'."
                )

        return errors


    def _validate_methods(self, methods, line):
        """Validate all methods — check for duplicates."""

        errors     = []
        seen_names = set()

        for method in methods:
            if method.name in seen_names:
                errors.append(
                    f"[Line {line}] Duplicate method '{method.name}'."
                )
            else:
                seen_names.add(method.name)

        return errors


    def get_summary(self, node):
        """Get human readable object summary."""

        if isinstance(node, ObjectDeclaration):
            parent_str = f" grow {node.parent}" if node.parent else ""
            open_fields   = [f for f in node.fields if f.is_public]
            hidden_fields = [f for f in node.fields if not f.is_public]
            return (
                f"object {node.name}{parent_str}\n"
                f"  Open fields   : {len(open_fields)}\n"
                f"  Hidden fields : {len(hidden_fields)}\n"
                f"  Methods       : {len(node.methods)}"
            )

        elif isinstance(node, RecordDeclaration):
            return (
                f"record {node.name}\n"
                f"  Fields : {len(node.fields)}"
            )

        return str(node)


    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0

    def clear(self):
        self.errors   = []
        self.warnings = []

    def reset(self):
        self.errors        = []
        self.warnings      = []
        self.declared_objs = set()
