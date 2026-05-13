"""Evolution termination checks."""
from typing import Dict, List

import numpy as np

from config.settings import (
    EVOLUTION_MAX_GENERATIONS,
    EVOLUTION_MIN_IMPROVEMENT,
    EVOLUTION_PARENT_SCORE_EPS,
    EVOLUTION_STAGNATION_ROUNDS,
)
from factors.factor_pool import FactorPool
from utils.logger import get_logger

logger = get_logger(__name__)


class TerminationChecker:
    def __init__(self, pool: FactorPool):
        self.pool = pool
        self.generation_history: List[Dict] = []

    def check_overfit(self, train_results: Dict[str, dict], val_results: Dict[str, dict]) -> bool:
        for fid, train in train_results.items():
            val = val_results.get(fid)
            if val is None:
                continue
            train_ic = abs(train.get("ic_mean", 0))
            val_ic = abs(val.get("ic_mean", 0))
            if train_ic > 0.10 and val_ic < 0.01:
                logger.warning("overfit risk: %s train_ic=%.4f val_ic=%.4f", fid, train_ic, val_ic)
                return True
        return False

    def record_generation(self, gen: int, train_results: dict, val_results: dict) -> None:
        def median_abs_ic(results: Dict[str, dict]) -> float:
            values = [abs(v.get("ic_mean", 0)) for v in results.values()]
            return float(np.median(values)) if values else 0.0

        def best_validation_score(results: Dict[str, dict]) -> float:
            values = [
                abs(v.get("ic_ir", 0)) * 0.5 + abs(v.get("ic_mean", 0)) * 2.0
                for v in results.values()
            ]
            return float(max(values)) if values else 0.0

        self.generation_history.append({
            "generation": gen,
            "train_ic_median": median_abs_ic(train_results),
            "val_ic_median": median_abs_ic(val_results),
            "train_ic_max": max((abs(v.get("ic_mean", 0)) for v in train_results.values()), default=0),
            "val_ic_max": max((abs(v.get("ic_mean", 0)) for v in val_results.values()), default=0),
            "val_best_score": best_validation_score(val_results),
        })

    def check_no_improvement(self, generation: int) -> bool:
        if len(self.generation_history) < EVOLUTION_STAGNATION_ROUNDS + 1:
            return False
        recent = self.generation_history[-(EVOLUTION_STAGNATION_ROUNDS + 1):]
        baseline = recent[0]["val_best_score"]
        best_recent = max(item["val_best_score"] for item in recent[1:])
        improved = best_recent > baseline + EVOLUTION_MIN_IMPROVEMENT
        if not improved:
            logger.warning(
                "validation score stalled: baseline=%.6f best_recent=%.6f generation=%s",
                baseline,
                best_recent,
                generation,
            )
        return not improved

    def check_parent_degeneracy(self, parent_scores: dict) -> bool:
        if len(parent_scores) < 3:
            return False
        scores = list(parent_scores.values())
        spread = max(scores) - min(scores)
        degenerate = spread <= EVOLUTION_PARENT_SCORE_EPS
        if degenerate:
            logger.warning("parent scores are degenerate: %s", parent_scores)
        return degenerate

    def should_terminate(self, train_results: dict, val_results: dict, generation: int, parent_scores: dict = None) -> tuple:
        self.record_generation(generation, train_results, val_results)
        if self.check_overfit(train_results, val_results):
            return True, "overfit"
        if self.check_no_improvement(generation):
            return True, "no_improvement"
        if parent_scores and self.check_parent_degeneracy(parent_scores):
            return True, "parent_degeneracy"
        if generation >= EVOLUTION_MAX_GENERATIONS:
            return True, "max_generations"
        return False, ""

    def get_overfitting_diagnosis(self, train_results: dict, val_results: dict) -> str:
        lines = ["=== overfit diagnosis ==="]
        for fid, train in train_results.items():
            val = val_results.get(fid)
            if val is None:
                continue
            t_ic = train.get("ic_mean", 0)
            v_ic = val.get("ic_mean", 0)
            flag = "WARN" if abs(t_ic) > 0.1 and abs(v_ic) < 0.01 else "OK"
            lines.append(f"  {flag} {fid}: train_IC={t_ic:.4f}, val_IC={v_ic:.4f}, diff={abs(t_ic-v_ic):.4f}")
        return "\n".join(lines)
