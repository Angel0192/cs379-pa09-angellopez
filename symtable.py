"""
PA 4: The USILang Symbol Table -- starter.

Complete Environment and check_program below. See
PA_04_The_USILang_Symbol_Table.md, Part B, for the full requirements.
"""

from typing import Optional

from parser import Assignment, BinOp, Declaration, Number, Program, Variable


class SemanticError(Exception):
    pass


class Environment:
    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self.parent = parent
        self._names: dict = {}  # name -> declaration line, THIS scope only

    def define(self, name: str, line: int) -> None:
        """
        Store name -> line in THIS scope. Raise SemanticError if `name`
        is already defined in THIS scope (not a parent scope --
        shadowing a parent name is allowed).
        """
        # Checks if the variable already exits in scope
        if name in self._names:
            orig_line = self._names[name]
            # Raise Error detailing the duplicate variable
            raise SemanticError(f"Duplicate declarion of {name!r} (line {line}; originally declared line {orig_line}).")
        
        # If its not found in this scope, store it
        self._names[name] = line

    def resolve(self, name: str) -> int:
        """
        Look up `name` in this scope, then climb `parent` links.
        Return the declaration line, or raise SemanticError if not
        found anywhere in the chain.
        """
        # Checks if the variable already exits in scope
        if name in self._names:
            return self._names[name]
        
        # If not found here, recursively climb up to the parent scope if it exists
        if self.parent is not None:
            return self.parent.resolve(name)
        
        raise SemanticError(f"Use of undeclared varaible {name!r}.")
    
def resolve_expr(expr, env: Environment) -> None:
    
    # If its a variable node, check that it has been declared
    if isinstance(expr, Variable):
        env.resolve(expr.name)
        
    # If its a binary operation, recursively check both sides of the expression
    elif isinstance(expr, BinOp):
        resolve_expr(expr.left, env)
        resolve_expr(expr.right, env)


def check_program(ast: Program) -> Environment:
    """
    Walk `ast.statements` in order, using one top-level Environment.
    For a Declaration: resolve every Variable in its expr BEFORE
    defining the new name (so `let x = x;` fails as use-before-decl).
    For an Assignment: resolve the assigned-to name, then resolve
    every Variable in its expr. Errors must surface at the first
    offending statement, not be collected and reported together.
    """
    env = Environment(parent=None)
    
    # Iterate through each statement in the AST program
    for stmt in ast.statements:
        
        if isinstance(stmt, Declaration):
            # Resolve variables in the expression first
            resolve_expr(stmt.expr, env)
            env.define(stmt.name, stmt.line)
        elif isinstance(stmt, Assignment):
            env.resolve(stmt.name)
            resolve_expr(stmt.expr, env)
    
    return env