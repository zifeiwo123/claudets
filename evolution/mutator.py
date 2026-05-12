"""Mutation operators for factor expression trees."""
import random

from evolution.constraints import ConstraintChecker
from factors.expression_tree import ExprNode
from factors.operators import FIELDS, UNARY_SCALAR_OPS, get_operator, get_random_operator, random_param
from utils.logger import get_logger

logger = get_logger(__name__)


class Mutator:
    def __init__(self, checker: ConstraintChecker = None):
        self.checker = checker or ConstraintChecker()

    def mutate(self, node: ExprNode, max_retries: int = 10) -> ExprNode:
        strategies = [
            self._mutate_replace_operator,
            self._mutate_adjust_window,
            self._mutate_adjust_coefficient,
            self._mutate_replace_leaf,
            self._mutate_insert_transform,
        ]
        for _ in range(max_retries):
            mutant = node.clone()
            mutant = random.choice(strategies)(mutant)
            if self.checker.validate(mutant):
                return mutant
        logger.debug("mutation retries exhausted; returning clone")
        return node.clone()

    def _mutate_replace_operator(self, node: ExprNode) -> ExprNode:
        internal = [n for n in node.get_all_subtrees() if not n.is_leaf]
        if not internal:
            return node
        target = random.choice(internal)
        op_def = get_operator(target.op)
        if op_def is None:
            return node
        new_op = get_random_operator(arity=op_def.arity)
        target.op = new_op.name
        target.param = random_param(new_op) if new_op.has_param else None
        return node

    def _mutate_adjust_window(self, node: ExprNode) -> ExprNode:
        param_nodes = [n for n in node.get_all_subtrees() if n.param is not None]
        if not param_nodes:
            return node
        target = random.choice(param_nodes)
        delta = random.choice([-10, -5, 5, 10])
        target.param = max(1, min(60, target.param + delta))
        return node

    def _mutate_adjust_coefficient(self, node: ExprNode) -> ExprNode:
        candidates = [n for n in node.get_all_subtrees() if n.op in {"scale", "signed_power"}]
        if not candidates:
            return node
        target = random.choice(candidates)
        if target.op == "scale":
            target.param = round(random.uniform(0.1, 3.0), 1)
        else:
            target.param = round(random.uniform(0.5, 3.0), 1)
        return node

    def _mutate_replace_leaf(self, node: ExprNode) -> ExprNode:
        leaves = [n for n in node.get_all_subtrees() if n.is_leaf and n.op in FIELDS]
        if leaves:
            random.choice(leaves).op = random.choice(FIELDS)
        return node

    def _mutate_insert_transform(self, node: ExprNode) -> ExprNode:
        candidates = [n for n in node.get_all_subtrees() if not n.is_leaf]
        if not candidates:
            return node
        target = random.choice(candidates)
        wrap_op = random.choice(list(UNARY_SCALAR_OPS.keys()) + ["ts_zscore"])
        op_def = get_operator(wrap_op)
        original = target.clone()
        target.op = wrap_op
        target.left = original
        target.right = None
        target.param = random_param(op_def) if op_def and op_def.has_param else None
        target.is_leaf = False
        return node
