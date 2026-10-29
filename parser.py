"""
PA 3: The USILang Parser -- starter.

Complete the parsing functions below. AST node types are already
defined -- do not modify them. See the assignment,
Part B, for the full requirements.
"""

from dataclasses import dataclass, field
from typing import List

from lexer import Token, tokenize


@dataclass
class Program:
    statements: list


@dataclass
class Declaration:
    name: str
    expr: object
    line: int


@dataclass
class Assignment:
    name: str
    expr: object
    line: int


@dataclass
class BinOp:
    op: str
    left: object
    right: object
    line: int


@dataclass
class Number:
    value: int
    line: int


@dataclass
class Variable:
    name: str
    line: int


class ParseError(Exception):
    pass


class _ParserState:
    """Given: a small cursor wrapper over the token list. Not required to use, but handy."""

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, type_: str) -> Token:
        tok = self.peek()
        if tok.type != type_:
            raise ParseError(f"Line {tok.line}: expected {type_}, found {tok.type} ({tok.lexeme!r}).")
        return self.advance()


def parse_factor(state: _ParserState):
    tok = state.peek()
    
    if tok.type == "NUMBER":
        state.advance()
        return Number(int(tok.lexeme), tok.line)
    elif tok.type == "IDENT":
        state.advance()
        return Variable(tok.lexeme, tok.line)
    elif tok.type == "LPAREN":
        state.advance()
        expr = parse_expr(state)
        state.expect("RPAREN")
        return expr
    else:
        raise ParseError(f"Line {tok.line}: expecte expression, found {tok.type} ({tok.lexeme!r}).")
    


def parse_term(state: _ParserState):
    node = parse_factor(state)
    
    while state.peek().type in ("STAR", "SLASH"):
        op_tok = state.advance()
        right = parse_factor(state)
        node = BinOp(op_tok.lexeme, node, right, op_tok.line)
    
    return node


def parse_expr(state: _ParserState):
    node = parse_term(state)
    
    while state.peek().type in ("PLUS", "MINUS"):
        op_tok = state.advance()
        
        right = parse_term(state)
        
        node = BinOp(op_tok.lexeme, node, right, op_tok.line)
    
    return node


def parse_declaration(state: _ParserState) -> Declaration:
    let_tok = state.expect("LET")
    
    ident_tok = state.expect("IDENT")
    
    state.expect("ASSIGN")
    
    expr = parse_expr(state)
    
    state.expect("SEMI")
    
    return Declaration(ident_tok.lexeme, expr, let_tok.line)


def parse_assignment(state: _ParserState) -> Assignment:
    ident_tok = state.expect("IDENT")
    
    state.expect("ASSIGN")
    
    expr = parse_expr(state)
    
    state.expect("SEMI")
    
    return Assignment(ident_tok.lexeme, expr, ident_tok.line)


def parse_statement(state: _ParserState):
    current_token_type = state.peek().type
    
    if current_token_type == "LET":
        return parse_declaration(state)
    else:
        return parse_assignment(state)


def parse_program(state: _ParserState) -> Program:
    statements = []
    
    while state.peek().type != "EOF":
        stmt = parse_statement(state)
        statements.append(stmt)

    return Program(statements)

def parse(tokens: List[Token]) -> Program:
    state = _ParserState(tokens)
    return parse_program(state)