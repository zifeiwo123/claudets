"""Operator definitions for expression-tree factor generation."""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class OperatorDef:
    name: str
    arity: int
    has_param: bool
    param_range: Optional[tuple] = None


FIELDS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "returns",
    "amplitude",
    "d_ret_5d",
    "d_ret_20d",
    "d_vol_20d",
    "d_downside_vol_20d",
    "d_range_20d",
    "d_intraday_strength_5d",
    "d_volume_z20",
    "d_amount_z20",
]

UNARY_WINDOW_OPS = {
    "ts_mean": OperatorDef("ts_mean", 1, True, (5, 60, 5)),
    "ts_std": OperatorDef("ts_std", 1, True, (5, 60, 5)),
    "ts_min": OperatorDef("ts_min", 1, True, (5, 60, 5)),
    "ts_max": OperatorDef("ts_max", 1, True, (5, 60, 5)),
    "ts_zscore": OperatorDef("ts_zscore", 1, True, (5, 60, 5)),
    "ts_rank": OperatorDef("ts_rank", 1, True, (5, 60, 5)),
    "delta": OperatorDef("delta", 1, True, (1, 20, 1)),
    "delay": OperatorDef("delay", 1, True, (1, 20, 1)),
}

BINARY_WINDOW_OPS = {
    "ts_corr": OperatorDef("ts_corr", 2, True, (5, 60, 5)),
}

UNARY_SCALAR_OPS = {
    "rank": OperatorDef("rank", 1, False),
    "signed_power": OperatorDef("signed_power", 1, True, (0.5, 3.0, 0.5)),
    "scale": OperatorDef("scale", 1, True, (0.1, 3.0, 0.1)),
}

ALL_OPERATORS: Dict[str, OperatorDef] = {}
ALL_OPERATORS.update(UNARY_WINDOW_OPS)
ALL_OPERATORS.update(BINARY_WINDOW_OPS)
ALL_OPERATORS.update(UNARY_SCALAR_OPS)


def get_operator(name: str) -> Optional[OperatorDef]:
    return ALL_OPERATORS.get(name)


def get_random_operator(arity: int = None) -> OperatorDef:
    import random

    if arity == 1:
        pool = list(UNARY_WINDOW_OPS.values()) + list(UNARY_SCALAR_OPS.values())
    elif arity == 2:
        pool = list(BINARY_WINDOW_OPS.values())
    else:
        pool = list(ALL_OPERATORS.values())
    return random.choice(pool)


def random_param(op_def: OperatorDef):
    import random

    if op_def.param_range is None:
        return None
    mn, mx, step = op_def.param_range
    values = []
    value = mn
    while value <= mx:
        values.append(round(value, 2))
        value += step
    return random.choice(values)
