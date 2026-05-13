"""Parent selection based on validation metrics stored in FactorPool."""
from typing import List

from factors.factor_pool import FactorPool
from utils.logger import get_logger

logger = get_logger(__name__)


class ParentSelector:
    def __init__(self, pool: FactorPool):
        self.pool = pool

    def select_top(self, top_k: int = 5) -> List[str]:
        scores = {fid: self.compute_score(fid) for fid in self.pool.list_ids()}
        scores = {fid: score for fid, score in scores.items() if score > 0}
        top = sorted(scores, key=scores.get, reverse=True)[:top_k]
        logger.info("parent top %s = %s", top_k, [(fid, scores[fid]) for fid in top])
        return top

    def score_many(self, factor_ids: List[str]) -> dict:
        return {fid: self.compute_score(fid) for fid in factor_ids}

    def compute_score(self, factor_id: str) -> float:
        ic = self.pool.get_ic_result(factor_id)
        node = self.pool.get(factor_id)
        if ic is None or node is None:
            return 0.0
        adj_ic = abs(ic.get("adjusted_ic", ic.get("ic_mean", 0)))
        ic_ir = abs(ic.get("ic_ir", 0))
        long_short = abs(ic.get("long_short_mean", 0))
        complexity_penalty = node.get_node_count() * 0.001
        return adj_ic * 0.4 + ic_ir * 0.4 + long_short * 0.2 - complexity_penalty
