import sys
from token_types import TokenType
from token import Token
from nodes import *

class NIMNAParser:
    def __init__(self, tokens, filename="<nimna>"):
        self.tokens   = tokens
        self.filename = filename
        self.pos      = 0
        self.errors   = []

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, None, 0, 0)

    def advance(self):
        token = self.current()
        self.pos += 1
        return token

    def skip_newlines(self):
        while self.current().token_type == TokenType.NEWLINE:
            self.advance()

    def is_keyword(self, keyword):
        t = self.current()
        return t.token_type == TokenType.KEYWORD and t.value == keyword

    def is_eof(self):
        return self.current().token_type == TokenType.EOF

    def expect(self, token_type):
        self.skip_newlines()
        token = self.current()
        if token.token_type != token_type:
            self.errors.append(
                f"[Line {token.line}] Expected '{token_type}' but got '{token.token_type}' ('{token.value}')."
            )
            return None
        return self.advance()

    def parse(self):
        statements = []
        while not self.is_eof():
            self.skip_newlines()
            if self.is_eof():
                break
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
        return Program(statements=statements, line=1, column=1)

    def parse_statement(self):
        self.skip_newlines()
        token = self.current()
        if token.token_type == TokenType.KEYWORD:
            if token.value == "module":   return self.parse_module()
            elif token.value == "bring":  return self.parse_bring()
            elif token.value == "let":    return self.parse_let()
            elif token.value == "constant": return self.parse_constant()
            elif token.value == "fn":     return self.parse_function()
            elif token.value == "async":  return self.parse_async_function()
            elif token.value == "object": return self.parse_object()
            elif token.value == "record": return self.parse_record()
            elif token.value == "if":     return self.parse_if()
            elif token.value == "match":  return self.parse_match()
            elif token.value == "for":    return self.parse_for()
            elif token.value == "while":  return self.parse_while()
            elif token.value == "do":     return self.parse_do_until()
            elif token.value == "foreach": return self.parse_foreach()
            elif token.value == "parallel": return self.parse_parallel()
            elif token.value == "attempt": return self.parse_attempt()
            elif token.value == "give":   return self.parse_return()
            elif token.value == "raise":  return self.parse_raise()
            elif token.value == "break":
                self.advance()
                return BreakStatement(line=token.line, column=token.column)
            elif token.value == "skip":
                self.advance()
                return SkipStatement(line=token.line, column=token.column)
        return self.parse_expression()

    def parse_module(self):
        token = self.advance()
        self.skip_newlines()
        name_token = self.expect(TokenType.IDENTIFIER)
        if not name_token: return None
        return ModuleStatement(name=name_token.value, line=token.line, column=token.column)

    def parse_bring(self):
        token = self.advance()
        self.skip_newlines()
        path = self._parse_dotted_path()
        from_items = None
        if self.is_keyword("from"):
            self.advance()
            self.skip_newlines()
            from_items = []
            while self.current().token_type == TokenType.IDENTIFIER:
                from_items.append(self.advance().value)
                if self.current().token_type == TokenType.COMMA:
                    self.advance(); self.skip_newlines()
                else:
                    break
        return BringStatement(module_path=path, alias=from_items, line=token.line, column=token.column)

    def _parse_dotted_path(self):
        parts = []
        if self.current().token_type == TokenType.IDENTIFIER:
            parts.append(self.advance().value)
        while self.current().token_type == TokenType.DOT:
            self.advance()
            if self.current().token_type == TokenType.IDENTIFIER:
                parts.append(self.advance().value)
        return ".".join(parts)

    def parse_let(self):
        token = self.advance()
        self.skip_newlines()
        name_token = self.expect(TokenType.IDENTIFIER)
        if not name_token: return None
        declared_type = None
        if self.current().token_type == TokenType.COLON:
            self.advance(); self.skip_newlines()
            declared_type = self._parse_type_name()
        if self.current().token_type != TokenType.ASSIGN:
            self.errors.append(f"[Line {token.line}] Expected '=' in let statement.")
            return None
        self.advance(); self.skip_newlines()
        value = self.parse_expression()
        return LetStatement(name=name_token.value, declared_type=declared_type, value=value, line=token.line, column=token.column)

    def parse_constant(self):
        token = self.advance()
        self.skip_newlines()
        name_token = self.expect(TokenType.IDENTIFIER)
        if not name_token: return None
        declared_type = None
        if self.current().token_type == TokenType.COLON:
            self.advance(); self.skip_newlines()
            declared_type = self._parse_type_name()
        if self.current().token_type != TokenType.ASSIGN:
            self.errors.append(f"[Line {token.line}] Expected '=' in constant.")
            return None
        self.advance(); self.skip_newlines()
        value = self.parse_expression()
        return ConstantStatement(name=name_token.value, declared_type=declared_type, value=value, line=token.line, column=token.column)

    def parse_function(self):
        token = self.advance()
        return self._parse_function_core(is_async=False, line=token.line, column=token.column)

    def parse_async_function(self):
        token = self.advance()
        if not self.is_keyword("fn"):
            self.errors.append(f"[Line {token.line}] Expected 'fn' after 'async'.")
            return None
        self.advance()
        return self._parse_function_core(is_async=True, line=token.line, column=token.column)

    def _parse_function_core(self, is_async, line, column):
        self.skip_newlines()
        name_token = self.expect(TokenType.IDENTIFIER)
        if not name_token: return None
        if self.current().token_type != TokenType.LPAREN:
            self.errors.append(f"[Line {line}] Expected '(' after function name.")
            return None
        self.advance()
        params = self._parse_parameters()
        if self.current().token_type != TokenType.RPAREN:
            self.errors.append(f"[Line {line}] Expected ')' after parameters.")
            return None
        self.advance()
        return_type = None
        if self.current().token_type == TokenType.ARROW:
            self.advance(); self.skip_newlines()
            return_type = self._parse_type_name()
        body = self._parse_block()
        return FunctionDeclaration(name=name_token.value, params=params, return_type=return_type, body=body, is_async=is_async, line=line, column=column)

    def _parse_parameters(self):
        params = []
        self.skip_newlines()
        while self.current().token_type != TokenType.RPAREN and not self.is_eof():
            self.skip_newlines()
            name_token = self.expect(TokenType.IDENTIFIER)
            if not name_token: break
            self.expect(TokenType.COLON)
            self.skip_newlines()
            param_type = self._parse_type_name()
            params.append(Parameter(name=name_token.value, param_type=param_type, line=name_token.line))
            if self.current().token_type == TokenType.COMMA:
                self.advance(); self.skip_newlines()
            else:
                break
        return params

    def _parse_block(self):
        self.skip_newlines()
        if self.current().token_type != TokenType.LBRACE:
            self.errors.append(f"[Line {self.current().line}] Expected '{{'.")
            return []
        self.advance()
        statements = []
        while self.current().token_type != TokenType.RBRACE and not self.is_eof():
            self.skip_newlines()
            if self.current().token_type == TokenType.RBRACE:
                break
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
        self.skip_newlines()
        if self.current().token_type == TokenType.RBRACE:
            self.advance()
        self.skip_newlines()
        return statements

    def _parse_type_name(self):
        token = self.current()
        if token.token_type.startswith("TYPE_"):
            self.advance(); return token.value
        if token.token_type == TokenType.IDENTIFIER:
            self.advance(); return token.value
        self.errors.append(f"[Line {token.line}] Expected type name, got '{token.value}'.")
        return None

    def parse_object(self):
        token = self.advance()
        self.skip_newlines()
        name_token = self.expect(TokenType.IDENTIFIER)
        if not name_token: return None
        parent = None
        if self.is_keyword("grow"):
            self.advance(); self.skip_newlines()
            parent_token = self.expect(TokenType.IDENTIFIER)
            if parent_token: parent = parent_token.value
        self.skip_newlines()
        self.advance()  # skip '{'
        self.skip_newlines()
        fields = []; methods = []
        while self.current().token_type != TokenType.RBRACE and not self.is_eof():
            self.skip_newlines()
            if self.current().token_type == TokenType.RBRACE: break
            if self.is_keyword("open") or self.is_keyword("hidden"):
                field = self._parse_field()
                if field: fields.append(field)
            elif self.is_keyword("fn") or self.is_keyword("async"):
                method = self.parse_statement()
                if method: methods.append(method)
            else:
                self.advance()
        self.skip_newlines()
        if self.current().token_type == TokenType.RBRACE: self.advance()
        return ObjectDeclaration(name=name_token.value, parent=parent, fields=fields, methods=methods, line=token.line, column=token.column)

    def parse_record(self):
        token = self.advance()
        self.skip_newlines()
        name_token = self.expect(TokenType.IDENTIFIER)
        if not name_token: return None
        self.skip_newlines()
        self.advance()  # skip '{'
        self.skip_newlines()
        fields = []
        while self.current().token_type != TokenType.RBRACE and not self.is_eof():
            self.skip_newlines()
            if self.current().token_type == TokenType.RBRACE: break
            field_name = self.expect(TokenType.IDENTIFIER)
            if not field_name: break
            self.expect(TokenType.COLON)
            self.skip_newlines()
            field_type = self._parse_type_name()
            fields.append(FieldDeclaration(name=field_name.value, field_type=field_type, is_public=True, line=field_name.line))
            self.skip_newlines()
        if self.current().token_type == TokenType.RBRACE: self.advance()
        return RecordDeclaration(name=name_token.value, fields=fields, line=token.line, column=token.column)

    def _parse_field(self):
        token = self.advance()
        is_public = (token.value == "open")
        self.skip_newlines()
        name_token = self.expect(TokenType.IDENTIFIER)
        if not name_token: return None
        self.expect(TokenType.COLON)
        self.skip_newlines()
        field_type = self._parse_type_name()
        return FieldDeclaration(name=name_token.value, field_type=field_type, is_public=is_public, line=token.line, column=token.column)

    def parse_if(self):
        token = self.advance()
        self.skip_newlines()
        condition = self.parse_expression()
        then_body = self._parse_block()
        elif_clauses = []; else_body = []
        while self.is_keyword("elif"):
            self.advance(); self.skip_newlines()
            elif_cond = self.parse_expression()
            elif_body = self._parse_block()
            elif_clauses.append((elif_cond, elif_body))
        if self.is_keyword("else"):
            self.advance()
            else_body = self._parse_block()
        return IfStatement(condition=condition, then_body=then_body, elif_clauses=elif_clauses, else_body=else_body, line=token.line, column=token.column)

    def parse_match(self):
        token = self.advance()
        self.skip_newlines()
        subject = self.parse_expression()
        self.skip_newlines()
        self.advance()  # skip '{'
        self.skip_newlines()
        arms = []
        while self.current().token_type != TokenType.RBRACE and not self.is_eof():
            self.skip_newlines()
            if self.current().token_type == TokenType.RBRACE: break
            if self.current().token_type == TokenType.WILDCARD:
                self.advance(); self.skip_newlines()
                if self.current().token_type == TokenType.MATCH_ARM: self.advance()
                self.skip_newlines()
                arm_body = self._parse_match_arm_body()
                arms.append(MatchArm(pattern=None, body=arm_body, is_wildcard=True, line=token.line))
            else:
                pattern = self.parse_expression()
                self.skip_newlines()
                if self.current().token_type == TokenType.MATCH_ARM: self.advance()
                self.skip_newlines()
                arm_body = self._parse_match_arm_body()
                arms.append(MatchArm(pattern=pattern, body=arm_body, is_wildcard=False, line=token.line))
            self.skip_newlines()
        if self.current().token_type == TokenType.RBRACE: self.advance()
        return MatchStatement(subject=subject, arms=arms, line=token.line, column=token.column)

    def _parse_match_arm_body(self):
        self.skip_newlines()
        if self.current().token_type == TokenType.LBRACE:
            return self._parse_block()
        if self.is_keyword("give"):
            stmt = self.parse_return()
            return [stmt] if stmt else []
        if self.is_keyword("raise"):
            stmt = self.parse_raise()
            return [stmt] if stmt else []
        expr = self.parse_expression()
        return [expr] if expr else []

    def parse_for(self):
        token = self.advance()
        self.skip_newlines()
        var_token = self.expect(TokenType.IDENTIFIER)
        if not var_token: return None
        self.skip_newlines()
        if not self.is_keyword("from"):
            self.errors.append(f"[Line {token.line}] Expected 'from' in for loop.")
            return None
        self.advance(); self.skip_newlines()
        range_expr = self.parse_expression()
        body = self._parse_block()
        return ForLoop(variable=var_token.value, range_expr=range_expr, body=body, line=token.line, column=token.column)

    def parse_while(self):
        token = self.advance()
        self.skip_newlines()
        condition = self.parse_expression()
        body = self._parse_block()
        return WhileLoop(condition=condition, body=body, line=token.line, column=token.column)

    def parse_do_until(self):
        token = self.advance()
        self.skip_newlines()
        body = self._parse_block()
        self.skip_newlines()
        if not self.is_keyword("until"):
            self.errors.append(f"[Line {token.line}] Expected 'until' after do block.")
            return None
        self.advance(); self.skip_newlines()
        condition = self.parse_expression()
        return DoUntilLoop(body=body, condition=condition, line=token.line, column=token.column)

    def parse_foreach(self):
        token = self.advance()
        self.skip_newlines()
        var_token = self.expect(TokenType.IDENTIFIER)
        if not var_token: return None
        self.skip_newlines()
        if not self.is_keyword("from"):
            self.errors.append(f"[Line {token.line}] Expected 'from' in foreach loop.")
            return None
        self.advance(); self.skip_newlines()
        collection = self.parse_expression()
        self.skip_newlines()
        body = self._parse_block()
        return ForeachLoop(variable=var_token.value, collection=collection, body=body, line=token.line, column=token.column)

    def parse_parallel(self):
        token = self.advance()
        self.skip_newlines()
        if not self.is_keyword("for"):
            self.errors.append(f"[Line {token.line}] Expected 'for' after 'parallel'.")
            return None
        self.advance(); self.skip_newlines()
        var_token = self.expect(TokenType.IDENTIFIER)
        if not var_token: return None
        self.skip_newlines()
        if not self.is_keyword("from"):
            self.errors.append(f"[Line {token.line}] Expected 'from' in parallel loop.")
            return None
        self.advance(); self.skip_newlines()
        range_expr = self.parse_expression()
        body = self._parse_block()
        return ParallelLoop(variable=var_token.value, range_expr=range_expr, body=body, line=token.line, column=token.column)

    def parse_attempt(self):
        token = self.advance()
        attempt_body = self._parse_block()
        self.skip_newlines()
        if not self.is_keyword("rescue"):
            self.errors.append(f"[Line {token.line}] Expected 'rescue' after attempt.")
            return None
        self.advance(); self.skip_newlines()
        rescue_var_token = self.expect(TokenType.IDENTIFIER)
        rescue_var = rescue_var_token.value if rescue_var_token else "error"
        rescue_body = self._parse_block()
        self.skip_newlines()
        always_body = None
        if self.is_keyword("always"):
            self.advance()
            always_body = self._parse_block()
        return AttemptStatement(attempt_body=attempt_body, rescue_var=rescue_var, rescue_body=rescue_body, always_body=always_body, line=token.line, column=token.column)

    def parse_return(self):
        token = self.advance()
        self.skip_newlines()
        value = self.parse_expression()
        return ReturnStatement(value=value, line=token.line, column=token.column)

    def parse_raise(self):
        token = self.advance()
        self.skip_newlines()
        value = self.parse_expression()
        return RaiseStatement(value=value, line=token.line, column=token.column)

    def parse_expression(self):
        return self.parse_assignment()

    def parse_assignment(self):
        left = self.parse_logical()
        assign_ops = {
            TokenType.ASSIGN: "=", TokenType.PLUS_ASSIGN: "+=",
            TokenType.MINUS_ASSIGN: "-=", TokenType.MULTIPLY_ASSIGN: "*=",
            TokenType.DIVIDE_ASSIGN: "/=", TokenType.REMAIN_ASSIGN: "%=",
            TokenType.POWER_ASSIGN: "**=",
        }
        if self.current().token_type in assign_ops:
            op = assign_ops[self.current().token_type]
            token = self.advance(); self.skip_newlines()
            right = self.parse_expression()
            if isinstance(left, Identifier):
                return AssignmentExpression(name=left.name, operator=op, value=right, line=token.line, column=token.column)
        return left

    def parse_logical(self):
        left = self.parse_comparison()
        while self.current().token_type in (TokenType.AND, TokenType.OR):
            op = self.advance().value; self.skip_newlines()
            right = self.parse_comparison()
            left = BinaryExpression(left, op, right)
        return left

    def parse_comparison(self):
        left = self.parse_range()
        comp_ops = {TokenType.EQUAL:"==",TokenType.NOT_EQUAL:"!=",TokenType.GREATER:">",TokenType.LESS:"<",TokenType.GREATER_EQ:">=",TokenType.LESS_EQ:"<="}
        while self.current().token_type in comp_ops:
            op = comp_ops[self.current().token_type]; self.advance(); self.skip_newlines()
            right = self.parse_range()
            left = BinaryExpression(left, op, right)
        return left

    def parse_range(self):
        left = self.parse_additive()
        range_ops = {TokenType.RANGE_EX:"..",TokenType.RANGE_IN:"..=",TokenType.RANGE_INF:"..."}
        if self.current().token_type in range_ops:
            op = range_ops[self.current().token_type]; self.advance()
            if op == "...": return RangeExpression(left, None, infinite=True)
            self.skip_newlines()
            right = self.parse_additive()
            return RangeExpression(left, right, inclusive=(op=="..="))
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.current().token_type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value; self.skip_newlines()
            right = self.parse_multiplicative()
            left = BinaryExpression(left, op, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_power()
        while self.current().token_type in (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.REMAINDER):
            op = self.advance().value; self.skip_newlines()
            right = self.parse_power()
            left = BinaryExpression(left, op, right)
        return left

    def parse_power(self):
        left = self.parse_unary()
        if self.current().token_type == TokenType.POWER:
            op = self.advance().value; self.skip_newlines()
            right = self.parse_unary()
            return BinaryExpression(left, op, right)
        return left

    def parse_unary(self):
        if self.current().token_type == TokenType.NOT:
            op = self.advance().value; operand = self.parse_unary()
            return UnaryExpression(op, operand)
        if self.current().token_type == TokenType.MINUS:
            op = self.advance().value; operand = self.parse_unary()
            return UnaryExpression(op, operand)
        return self.parse_cast()

    def parse_cast(self):
        expr = self.parse_pipeline()
        if self.is_keyword("as"):
            self.advance(); self.skip_newlines()
            target_type = self._parse_type_name()
            return TypeCastExpression(value=expr, target_type=target_type)
        return expr

    def parse_pipeline(self):
        left = self.parse_primary()
        while self.current().token_type == TokenType.PIPE_FORWARD:
            self.advance(); self.skip_newlines()
            right = self.parse_primary()
            left = PipelineExpression(left, right)
        return left

    def parse_primary(self):
        token = self.current()
        if token.token_type == TokenType.INTEGER:
            self.advance(); return IntegerLiteral(token.value, token.line, token.column)
        elif token.token_type == TokenType.DECIMAL:
            self.advance(); return DecimalLiteral(token.value, token.line, token.column)
        elif token.token_type == TokenType.TEXT:
            self.advance(); return TextLiteral(token.value, token.line, token.column)
        elif token.token_type == TokenType.LETTER:
            self.advance(); return LetterLiteral(token.value, token.line, token.column)
        elif token.token_type == TokenType.TRUTH_TRUE:
            self.advance(); return TruthLiteral(True, token.line, token.column)
        elif token.token_type == TokenType.TRUTH_FALSE:
            self.advance(); return TruthLiteral(False, token.line, token.column)
        elif token.token_type == TokenType.NOTHING:
            self.advance(); return NothingLiteral(token.line, token.column)
        elif token.token_type == TokenType.LBRACKET:
            return self._parse_collection()
        elif token.token_type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        elif token.token_type.startswith("TYPE_"):
            type_name = token.value; self.advance()
            if self.current().token_type == TokenType.LPAREN:
                self.advance(); self.skip_newlines()
                arg = self.parse_expression()
                self.expect(TokenType.RPAREN)
                return TypeConstructorExpression(type_name=type_name, argument=arg, line=token.line, column=token.column)
            return Identifier(type_name, token.line, token.column)
        elif token.token_type == TokenType.IDENTIFIER:
            return self._parse_identifier_or_call()
        elif token.token_type == TokenType.KEYWORD and token.value == "await":
            self.advance(); self.skip_newlines()
            value = self.parse_expression()
            return AwaitExpression(value, token.line, token.column)
        elif token.token_type == TokenType.KEYWORD and token.value == "launch":
            self.advance(); self.skip_newlines()
            value = self.parse_expression()
            return LaunchExpression(value, token.line, token.column)
        else:
            if token.token_type not in (TokenType.NEWLINE, TokenType.EOF):
                self.errors.append(f"[Line {token.line}] Unexpected token '{token.value}' ({token.token_type}).")
            self.advance()
            return None

    def _parse_identifier_or_call(self):
        token = self.advance()
        node = Identifier(token.value, token.line, token.column)
        while self.current().token_type == TokenType.DOT:
            self.advance()
            member_token = self.expect(TokenType.IDENTIFIER)
            if not member_token: break
            node = MemberAccessExpression(object_expr=node, member=member_token.value, line=member_token.line, column=member_token.column)
        if self.current().token_type == TokenType.LPAREN:
            self.advance()
            arguments = self._parse_arguments()
            self.expect(TokenType.RPAREN)
            node = CallExpression(function=node, arguments=arguments, line=token.line, column=token.column)
        elif self.current().token_type == TokenType.LBRACKET:
            self.advance()
            index = self.parse_expression()
            self.expect(TokenType.RBRACKET)
            node = IndexExpression(node, index, token.line, token.column)
        return node

    def _parse_arguments(self):
        args = []; self.skip_newlines()
        while self.current().token_type != TokenType.RPAREN and not self.is_eof():
            self.skip_newlines()
            arg = self.parse_expression()
            if arg is not None: args.append(arg)
            if self.current().token_type == TokenType.COMMA:
                self.advance(); self.skip_newlines()
            else:
                break
        return args

    def _parse_collection(self):
        token = self.advance(); elements = []; self.skip_newlines()
        while self.current().token_type != TokenType.RBRACKET and not self.is_eof():
            self.skip_newlines()
            elem = self.parse_expression()
            if elem is not None: elements.append(elem)
            if self.current().token_type == TokenType.COMMA:
                self.advance(); self.skip_newlines()
            else:
                break
        self.expect(TokenType.RBRACKET)
        return CollectionLiteral(elements=elements, line=token.line, column=token.column)

    def get_errors(self): return self.errors
    def has_errors(self): return len(self.errors) > 0
