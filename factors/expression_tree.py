"""Expression-tree AST for alpha factors."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List, Optional

from factors.operators import FIELDS


@dataclass
class ExprNode:
    op: str
    left: Optional["ExprNode"] = None
    right: Optional["ExprNode"] = None
    param: Optional[float] = None
    is_leaf: bool = False

    def to_python(self) -> str:
        if self.is_leaf:
            if self.op in FIELDS:
                return f"_data['{self.op}']"
            return f"{self.param}"
        return OPERATOR_COMPILERS[self.op](self)

    def get_depth(self) -> int:
        if self.is_leaf:
            return 0
        left_depth = self.left.get_depth() if self.left else 0
        right_depth = self.right.get_depth() if self.right else 0
        return 1 + max(left_depth, right_depth)

    def get_node_count(self) -> int:
        if self.is_leaf:
            return 1
        count = 1
        if self.left:
            count += self.left.get_node_count()
        if self.right:
            count += self.right.get_node_count()
        return count

    def clone(self) -> "ExprNode":
        return ExprNode(
            op=self.op,
            left=self.left.clone() if self.left else None,
            right=self.right.clone() if self.right else None,
            param=self.param,
            is_leaf=self.is_leaf,
        )

    def structure_hash(self) -> str:
        if self.is_leaf:
            key = f"LEAF:{self.op}:{self.param}"
        else:
            left_hash = self.left.structure_hash() if self.left else ""
            right_hash = self.right.structure_hash() if self.right else ""
            key = f"{self.op}|{self.param}|{left_hash}|{right_hash}"
        return hashlib.md5(key.encode("utf-8")).hexdigest()[:12]

    def get_all_subtrees(self) -> List["ExprNode"]:
        nodes = [self]
        if self.left:
            nodes.extend(self.left.get_all_subtrees())
        if self.right:
            nodes.extend(self.right.get_all_subtrees())
        return nodes

    def replace_subtree(self, old: "ExprNode", new: "ExprNode") -> bool:
        if self is old:
            self.op = new.op
            self.left = new.left
            self.right = new.right
            self.param = new.param
            self.is_leaf = new.is_leaf
            return True
        if self.left and self.left.replace_subtree(old, new):
            return True
        if self.right and self.right.replace_subtree(old, new):
            return True
        return False

    def to_dict(self) -> dict:
        data = {"op": self.op, "is_leaf": self.is_leaf}
        if self.param is not None:
            data["param"] = self.param
        if self.left:
            data["left"] = self.left.to_dict()
        if self.right:
            data["right"] = self.right.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ExprNode":
        return cls(
            op=data["op"],
            left=cls.from_dict(data["left"]) if "left" in data else None,
            right=cls.from_dict(data["right"]) if "right" in data else None,
            param=data.get("param"),
            is_leaf=data.get("is_leaf", False),
        )

    def __repr__(self) -> str:
        if self.is_leaf:
            return self.op if self.param is None else str(self.param)
        op_str = f"{self.op}(w={self.param})" if self.param is not None else self.op
        if self.right:
            return f"{op_str}({self.left}, {self.right})"
        return f"{op_str}({self.left})"


def _ts_expr(inner: str, window: int, agg: str) -> str:
    return f"_ts_func({inner}, {window}, '{agg}')"


def compile_ts_mean(node): return _ts_expr(node.left.to_python(), int(node.param), "mean")
def compile_ts_std(node): return _ts_expr(node.left.to_python(), int(node.param), "std")
def compile_ts_min(node): return _ts_expr(node.left.to_python(), int(node.param), "min")
def compile_ts_max(node): return _ts_expr(node.left.to_python(), int(node.param), "max")


def compile_ts_zscore(node):
    inner = node.left.to_python()
    window = int(node.param)
    return f"(({inner}) - _ts_func({inner}, {window}, 'mean')) / (_ts_func({inner}, {window}, 'std') + 1e-10)"


def compile_ts_rank(node): return f"_ts_rank({node.left.to_python()}, {int(node.param)})"
def compile_ts_corr(node): return f"_ts_corr({node.left.to_python()}, {node.right.to_python()}, {int(node.param)})"
def compile_delta(node): return f"({node.left.to_python()} - {node.left.to_python()}.shift({int(node.param)}))"
def compile_delay(node): return f"{node.left.to_python()}.shift({int(node.param)})"
def compile_rank(node): return f"{node.left.to_python()}.rank(axis=1, pct=True)"
def compile_scale(node): return f"({node.left.to_python()}) * {node.param}"
def compile_signed_power(node): return f"np.sign({node.left.to_python()}) * np.abs({node.left.to_python()}) ** {node.param}"


OPERATOR_COMPILERS = {
    "ts_mean": compile_ts_mean,
    "ts_std": compile_ts_std,
    "ts_min": compile_ts_min,
    "ts_max": compile_ts_max,
    "ts_corr": compile_ts_corr,
    "ts_rank": compile_ts_rank,
    "ts_zscore": compile_ts_zscore,
    "delta": compile_delta,
    "delay": compile_delay,
    "rank": compile_rank,
    "scale": compile_scale,
    "signed_power": compile_signed_power,
}
