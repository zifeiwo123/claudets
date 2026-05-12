"""Expression constraints for factor generation."""
from config.settings import MAX_TREE_DEPTH, MAX_WINDOW
from factors.expression_tree import ExprNode
from utils.logger import get_logger

logger = get_logger(__name__)


class ConstraintChecker:
    def __init__(self, max_depth: int = MAX_TREE_DEPTH, max_window: int = MAX_WINDOW):
        self.max_depth = max_depth
        self.max_window = max_window

    def validate(self, node: ExprNode) -> bool:
        return (
            self.check_depth(node)
            and self.check_window(node)
            and self.check_no_self_correlation(node)
            and self.check_no_raw_level_alpha(node)
        )

    def check_depth(self, node: ExprNode) -> bool:
        depth = node.get_depth()
        if depth > self.max_depth:
            logger.debug("depth exceeds limit: %s > %s", depth, self.max_depth)
            return False
        return True

    def check_window(self, node: ExprNode) -> bool:
        if node.is_leaf:
            return True
        if node.param is not None and node.param > self.max_window:
            logger.debug("window exceeds limit: %s > %s", node.param, self.max_window)
            return False
        return (
            self.check_window(node.left) if node.left else True
        ) and (
            self.check_window(node.right) if node.right else True
        )

    def check_no_self_correlation(self, node: ExprNode) -> bool:
        if node.is_leaf:
            return True
        if node.op == "ts_corr" and node.left and node.right:
            if node.left.to_python() == node.right.to_python():
                logger.debug("reject self-correlation ts_corr(X, X)")
                return False
        left_ok = self.check_no_self_correlation(node.left) if node.left else True
        right_ok = self.check_no_self_correlation(node.right) if node.right else True
        return left_ok and right_ok

    def check_no_raw_level_alpha(self, node: ExprNode) -> bool:
        raw_fields = {"open", "high", "low", "close", "volume", "amount"}
        identity_ops = {"scale", "signed_power"}

        def is_raw_or_identity(n: ExprNode) -> bool:
            if n.is_leaf:
                return n.op in raw_fields
            if n.op in identity_ops and n.left is not None:
                return is_raw_or_identity(n.left)
            return False

        if is_raw_or_identity(node):
            logger.debug("reject raw-level/identity alpha: %s", node)
            return False
        return True
