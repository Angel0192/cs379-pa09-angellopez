"""
PA 7: The Parameter Simulator -- starter.

Complete bind_parameters, commit_value_result, and Closure below.
Cell, evaluate(), and FunctionDecl are already provided -- do not
modify them. See the assignment, Part B, for the
full requirements.

Value-result binding has two steps: bind_parameters runs at call time
and records each caller destination; commit_value_result runs after
the simulated body and copies the final local values back in parameter
order. The handout specifies both steps.

Design note 2: variables are stored as Cell objects (a mutable box),
not raw values, specifically so reference-mode parameters can share
the exact same storage as the caller's variable -- see Part A,
Questions 1-2, for why "bind directly to the caller's slot" requires
this instead of just copying a plain value.
"""

from typing import Any, List, Tuple

from parser import BinOp, Number, Variable
from symtable import Environment


class Cell:
    """Given: a mutable box. Two names that share the SAME Cell are aliased."""

    __slots__ = ("value",)

    def __init__(self, value: Any) -> None:
        self.value = value


class FunctionDecl:
    """Given: a minimal function declaration -- params and a single expr body."""

    __slots__ = ("params", "body")

    def __init__(self, params: List[str], body) -> None:
        self.params = params
        self.body = body


def evaluate(node, env: Environment):
    """Given: evaluate a PA3 expression AST node against `env` (Cells are transparently dereferenced)."""
    if isinstance(node, Number):
        return node.value
    if isinstance(node, Variable):
        val = env.resolve(node.name)
        return val.value if isinstance(val, Cell) else val
    if isinstance(node, BinOp):
        if node.op == "neg":
            return -evaluate(node.left, env)
        left = evaluate(node.left, env)
        right = evaluate(node.right, env)
        return {"+": lambda a, b: a + b, "-": lambda a, b: a - b, "*": lambda a, b: a * b, "/": lambda a, b: a / b}[node.op](left, right)
    raise ValueError(f"cannot evaluate node: {node!r}")


def assign_through(env: Environment, name: str, value: Any) -> None:
    """Given: write `value` into whatever Cell `name` resolves to (mutates in place, does not rebind)."""
    cell = env.resolve(name)
    if not isinstance(cell, Cell):
        raise TypeError(f"'{name}' is not bound to a Cell -- did you forget to wrap it?")
    cell.value = value


VALID_MODES = ("value", "reference", "value-result")


def _caller_cell(arg_node, caller_env: Environment, param_name: str, mode: str) -> Cell:
    """
    Reference and value-result parameters need a writable destination,
    so their argument must be a caller variable. Return the caller's
    Cell for that variable (looked up through the caller's scope chain).
    """
    if not isinstance(arg_node, Variable):
        raise TypeError(
            f"parameter '{param_name}' is {mode}-mode, so its argument must be a "
            f"caller variable, not an expression: {arg_node!r}"
        )
    cell = caller_env.resolve(arg_node.name)
    if not isinstance(cell, Cell):
        raise TypeError(f"caller variable '{arg_node.name}' is not stored in a Cell")
    return cell


def bind_parameters(param_specs: List[Tuple[str, str]], arg_nodes: list, caller_env: Environment, callee_record) -> None:
    """
    Populate callee_record.locals_env according to each parameter's mode.

    value        -> new private Cell holding the evaluated argument
    reference    -> the caller's own Cell (aliased: writes show immediately)
    value-result -> new private Cell holding a copy of the caller's value,
                    plus a recorded destination for commit_value_result
    """
    if len(param_specs) != len(arg_nodes):
        raise TypeError(f"expected {len(param_specs)} arguments, got {len(arg_nodes)}")

    locals_env = callee_record.locals_env
    # Value-result destinations, recorded at CALL time, in parameter order.
    callee_record.pending_writeback = []

    for (param_name, mode), arg_node in zip(param_specs, arg_nodes):
        if mode not in VALID_MODES:
            raise ValueError(f"unknown parameter mode '{mode}' for '{param_name}'")

        if mode == "value":
            # Copy in: the callee gets its own box; the caller's box is untouched.
            locals_env.define(param_name, Cell(evaluate(arg_node, caller_env)))

        elif mode == "reference":
            # Alias: the parameter name points at the caller's existing box.
            locals_env.define(param_name, _caller_cell(arg_node, caller_env, param_name, mode))

        else:  # value-result
            # Copy in now, remember where to copy out at return.
            caller_cell = _caller_cell(arg_node, caller_env, param_name, mode)
            locals_env.define(param_name, Cell(caller_cell.value))
            callee_record.pending_writeback.append((param_name, caller_cell))


def commit_value_result(callee_record, caller_env: Environment) -> None:
    """
    Run after the callee body finishes: copy each value-result parameter's
    FINAL local value back into its recorded caller Cell, left to right in
    parameter declaration order. Later copies overwrite earlier ones when
    two parameters share a destination (the P(a, a) case).
    """
    pending = getattr(callee_record, "pending_writeback", [])
    for param_name, caller_cell in pending:
        local_cell = callee_record.locals_env.resolve(param_name)
        caller_cell.value = local_cell.value
    # Copy-back happens exactly once per call.
    callee_record.pending_writeback = []


class Closure:
    """A function value that carries the environment it was defined in."""

    def __init__(self, declaration: FunctionDecl, defining_env: Environment) -> None:
        self.declaration = declaration
        self.defining_env = defining_env

    def call(self, args: list, caller_env: Environment):
        """
        Build a fresh call environment whose parent is the DEFINING
        environment (the lexical/static link), not the caller's. Bind each
        parameter to a new Cell holding the already-evaluated argument, then
        evaluate the body there. caller_env is deliberately unused for name
        lookup -- that is what makes scoping lexical rather than dynamic.
        """
        params = self.declaration.params
        if len(args) != len(params):
            raise TypeError(f"expected {len(params)} arguments, got {len(args)}")

        call_env = Environment(parent=self.defining_env)
        for name, value in zip(params, args):
            call_env.define(name, Cell(value))
        return evaluate(self.declaration.body, call_env)