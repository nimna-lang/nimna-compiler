# ============================================
# NIMNA Language — Comment Handler
# File: src/lexer/comment_handler.py
# Compiler: nimac
# ============================================


# ============================================
# COMMENT HANDLER CLASS
# ============================================

class CommentHandler:
    """
    NIMNA Comment Handler

    Handles two types of comments:
    1. Single-line comments  : // comment text
    2. Multi-line comments   : /* comment text */

    Comments are completely skipped by the compiler.
    Line and column tracking is maintained during skip.
    """

    def __init__(self, source, pos, line, column, filename="<nimna>"):
        self.source   = source
        self.pos      = pos
        self.line     = line
        self.column   = column
        self.filename = filename


    def current_char(self):
        """Return current character or None."""
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None


    def peek_char(self, offset=1):
        """Peek ahead without moving position."""
        peek_pos = self.pos + offset
        if peek_pos < len(self.source):
            return self.source[peek_pos]
        return None


    def advance(self):
        """Move forward one character."""
        char        = self.source[self.pos]
        self.pos   += 1
        if char == '\n':
            self.line  += 1
            self.column = 1
        else:
            self.column += 1
        return char


    # ============================================
    # SINGLE LINE COMMENT
    # ============================================

    def skip_single_line(self):
        """
        Skip a single-line comment.
        Starts after // and ends at newline.

        Example:
            // This is a single line comment
            let x: Whole = 10  // Inline comment

        Returns:
            (pos, line, column, comment_text)
        """

        comment_text = ""

        # Skip both '/' characters
        self.advance()  # first /
        self.advance()  # second /

        # Skip any leading space after //
        if self.current_char() == ' ':
            self.advance()

        # Read until end of line or end of file
        while self.current_char() and self.current_char() != '\n':
            comment_text += self.advance()

        return (
            self.pos,
            self.line,
            self.column,
            comment_text.strip()
        )


    # ============================================
    # MULTI LINE COMMENT
    # ============================================

    def skip_multi_line(self):
        """
        Skip a multi-line comment.
        Starts after /* and ends at */.
        Supports nested structure tracking.

        Example:
            /* This is
               a multi-line
               comment */

        Returns:
            (pos, line, column, comment_text, error)
        """

        comment_text  = ""
        start_line    = self.line
        start_column  = self.column

        # Skip opening '/*'
        self.advance()  # /
        self.advance()  # *

        # Skip optional space after /*
        if self.current_char() == ' ':
            self.advance()

        # Read until closing */
        while self.current_char():

            # Check for closing */
            if (self.current_char() == '*' and
                self.peek_char() == '/'):
                self.advance()  # skip *
                self.advance()  # skip /
                break

            # End of file without closing */
            if self.pos >= len(self.source) - 1:
                return (
                    self.pos,
                    self.line,
                    self.column,
                    comment_text,
                    (
                        f"Unclosed multi-line comment '/*' "
                        f"opened at line {start_line}, "
                        f"column {start_column}. "
                        f"Missing closing '*/'."
                    )
                )

            comment_text += self.advance()

        return (
            self.pos,
            self.line,
            self.column,
            comment_text.strip(),
            None
        )


    # ============================================
    # DETECT COMMENT TYPE
    # ============================================

    def is_single_line_comment(self):
        """
        Check if current position starts a single-line comment.
        """
        return (
            self.current_char() == '/' and
            self.peek_char() == '/'
        )


    def is_multi_line_comment(self):
        """
        Check if current position starts a multi-line comment.
        """
        return (
            self.current_char() == '/' and
            self.peek_char() == '*'
        )


    def detect_and_skip(self):
        """
        Auto detect comment type and skip it.

        Returns:
            dict with keys:
                type         : 'single' or 'multi'
                text         : comment content
                pos          : updated position
                line         : updated line
                column       : updated column
                error        : error message or None
        """

        if self.is_single_line_comment():
            pos, line, col, text = self.skip_single_line()
            return {
                "type"   : "single",
                "text"   : text,
                "pos"    : pos,
                "line"   : line,
                "column" : col,
                "error"  : None
            }

        elif self.is_multi_line_comment():
            pos, line, col, text, error = self.skip_multi_line()
            return {
                "type"   : "multi",
                "text"   : text,
                "pos"    : pos,
                "line"   : line,
                "column" : col,
                "error"  : error
            }

        return None


# ============================================
# STANDALONE HELPER FUNCTIONS
# ============================================

def strip_comments_from_source(source):
    """
    Remove all comments from source code.
    Returns clean source code string.
    """

    result = ""
    pos    = 0

    while pos < len(source):

        # Single line comment
        if (pos + 1 < len(source) and
            source[pos] == '/' and
            source[pos + 1] == '/'):
            while pos < len(source) and source[pos] != '\n':
                pos += 1

        # Multi line comment
        elif (pos + 1 < len(source) and
              source[pos] == '/' and
              source[pos + 1] == '*'):
            pos += 2
            while pos < len(source):
                if (pos + 1 < len(source) and
                    source[pos] == '*' and
                    source[pos + 1] == '/'):
                    pos += 2
                    break
                pos += 1

        # Regular character
        else:
            result += source[pos]
            pos    += 1

    return result


def count_comments(source):
    """
    Count total comments in source code.

    Returns:
        dict with single_line and multi_line counts
    """

    single_count = 0
    multi_count  = 0
    pos          = 0

    while pos < len(source):

        if (pos + 1 < len(source) and
            source[pos] == '/' and
            source[pos + 1] == '/'):
            single_count += 1
            while pos < len(source) and source[pos] != '\n':
                pos += 1

        elif (pos + 1 < len(source) and
              source[pos] == '/' and
              source[pos + 1] == '*'):
            multi_count += 1
            pos += 2
            while pos < len(source):
                if (pos + 1 < len(source) and
                    source[pos] == '*' and
                    source[pos + 1] == '/'):
                    pos += 2
                    break
                pos += 1

        else:
            pos += 1

    return {
        "single_line" : single_count,
        "multi_line"  : multi_count,
        "total"       : single_count + multi_count
    }
