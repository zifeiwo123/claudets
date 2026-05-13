"""Expression constraints for factor generation."""
from config.settings import MAX_TREE_DEPTH, MAX_WINDOW
from factors.expression_tree import ExprNode
from factors.operators import DAILY_FEATURE_FIELDS, RAW_LEVEL_FIELDS
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
            and self.check_has_daily_feature(node)
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
        def has_raw_level(n: ExprNode) -> bool:
            if n.is_leaf:
                return n.op in RAW_LEVEL_FIELDS
            left_bad = has_raw_level(n.left) if n.left else False
            right_bad = has_raw_level(n.right) if n.right else False
            return left_bad or right_bad

        if has_raw_level(node):
            logger.debug("reject raw price/liquidity exposure: %s", node)
            return False
        return True

    def check_has_daily_feature(self, node: ExprNode) -> bool:
        daily_fields = set(DAILY_FEATURE_FIELDS)

        def has_daily(n: ExprNode) -> bool:
            if n.is_leaf:
                return n.op in daily_fields
            left_ok = has_daily(n.left) if n.left else False
            right_ok = has_daily(n.right) if n.right else False
            return left_ok or right_ok

        if not has_daily(node):
            logger.debug("reject alpha without daily-derived feature: %s", node)
            return False
        return True
