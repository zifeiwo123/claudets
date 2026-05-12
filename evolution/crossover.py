"""Crossover operators for factor expression trees."""
import random

from evolution.constraints import ConstraintChecker
from factors.expression_tree import ExprNode
from utils.logger import get_logger

logger = get_logger(__name__)


class CrossoverOperator:
    def __init__(self, checker: ConstraintChecker = None):
        self.checker = checker or ConstraintChecker()

    def crossover(self, parent1: ExprNode, parent2: ExprNode, max_retries: int = 10) -> tuple:
        for _ in range(max_retries):
            child1 = parent1.clone()
            child2 = parent2.clone()
            nodes1 = [n for n in child1.get_all_subtrees() if not n.is_leaf]
            nodes2 = [n for n in child2.get_all_subtrees() if not n.is_leaf]
            if not nodes1 or not nodes2:
                return None, None
            sub1 = random.choice(nodes1)
            compatible = [n for n in nodes2 if (n.right is None) == (sub1.right is None)]
            if not compatible:
                continue
            sub2 = random.choice(compatible)
            replacement1 = sub2.clone()
            replacement2 = sub1.clone()
            _overwrite_node(sub1, replacement1)
            _overwrite_node(sub2, replacement2)
            if self.checker.validate(child1) and self.checker.validate(child2):
                return child1, child2
        logger.debug("crossover retries exhausted")
        return None, None


def _overwrite_node(target: ExprNode, replacement: ExprNode) -> None:
    target.op = replacement.op
    target.left = replacement.left
    target.right = replacement.right
    target.param = replacement.param
    target.is_leaf = replacement.is_leaf
