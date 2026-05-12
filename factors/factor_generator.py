"""Random factor generator with reproducible expression IDs."""
import random

from evolution.constraints import ConstraintChecker
from factors.expression_tree import ExprNode
from factors.operators import (
    BINARY_WINDOW_OPS,
    FIELDS,
    UNARY_SCALAR_OPS,
    UNARY_WINDOW_OPS,
    random_param,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class FactorGenerator:
    """Generate random expression-tree factors."""

    _next_id = 0

    def __init__(self, checker: ConstraintChecker = None):
        self.checker = checker or ConstraintChecker()

    def generate_random(self) -> ExprNode:
        depth = random.randint(1, 3)
        return self._random_subtree(depth)

    def _random_subtree(self, max_depth: int) -> ExprNode:
        if max_depth <= 0:
            return self._random_leaf()
        if random.random() < 0.35:
            return self._random_leaf()
        return self._random_internal(max_depth)

    def _random_leaf(self) -> ExprNode:
        return ExprNode(op=random.choice(FIELDS), is_leaf=True)

    def _random_internal(self, max_depth: int) -> ExprNode:
        if random.random() < 0.80:
            pool = list(UNARY_WINDOW_OPS.values()) + list(UNARY_SCALAR_OPS.values())
            op_def = random.choice(pool)
            return ExprNode(
                op=op_def.name,
                left=self._random_subtree(max_depth - 1),
                param=random_param(op_def),
                is_leaf=False,
            )

        op_def = random.choice(list(BINARY_WINDOW_OPS.values()))
        return ExprNode(
            op=op_def.name,
            left=self._random_subtree(max_depth - 1),
            right=self._random_subtree(max_depth - 1),
            param=random_param(op_def),
            is_leaf=False,
        )

    def generate_pool(self, size: int) -> list:
        factors = []
        attempts = 0
        max_attempts = size * 8

        while len(factors) < size and attempts < max_attempts:
            attempts += 1
            node = self.generate_random()
            if self.checker.validate(node):
                fid = f"alpha_{FactorGenerator._next_id:04d}"
                FactorGenerator._next_id += 1
                factors.append((fid, node, self._explain_factor(node)))

        logger.info("generated %s initial factors in %s attempts", len(factors), attempts)
        return factors

    def _explain_factor(self, node: ExprNode) -> str:
        return f"[{node.op}] expression={node}"
