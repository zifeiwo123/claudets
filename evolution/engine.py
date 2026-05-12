"""Genetic-programming evolution engine for factor expressions."""
from typing import Dict, List

import pandas as pd

from evaluation.ic_analysis import ICAnalyzer
from evaluation.stratification import StratificationTester
from evolution.constraints import ConstraintChecker
from evolution.crossover import CrossoverOperator
from evolution.mutator import Mutator
from evolution.selector import ParentSelector
from evolution.termination import TerminationChecker
from factors.factor_compute import FactorCompute
from factors.factor_generator import FactorGenerator
from factors.factor_pool import FactorPool
from utils.logger import get_logger

logger = get_logger(__name__)

MAX_STOCKS = 400


class EvolutionEngine:
    """Evolve factors using train evaluation and validation selection."""

    def __init__(self, train_data: pd.DataFrame, val_data: pd.DataFrame,
                 universe: List[str] = None, max_stocks: int = MAX_STOCKS):
        self.universe = universe
        self.train_compute = FactorCompute(train_data, max_stocks=max_stocks, universe=universe)
        self.val_compute = FactorCompute(val_data, max_stocks=max_stocks, universe=universe)
        self.pool = FactorPool()
        self.checker = ConstraintChecker()
        self.generator = FactorGenerator(self.checker)
        self.selector = ParentSelector(self.pool)
        self.mutator = Mutator(self.checker)
        self.crossover = CrossoverOperator(self.checker)
        self.termination = TerminationChecker(self.pool)
        self.fwd_train = self._compute_forward_returns(self.train_compute)
        self.fwd_val = self._compute_forward_returns(self.val_compute)
        self.current_generation = 0
        self.evolution_log: List[Dict] = []

    def initialize(self, n_factors: int = 16) -> List[str]:
        ids = []
        for fid, node, explanation in self.generator.generate_pool(n_factors):
            if self.pool.add(fid, node, generation=0):
                ids.append(fid)
                logger.info("seed %s: %s", fid, explanation)
        self.current_generation = 0
        return ids

    def evaluate_generation(self, factor_ids: List[str]) -> tuple:
        train_results = {}
        val_results = {}

        for fid in factor_ids:
            node = self.pool.get(fid)
            if node is None:
                continue

            try:
                fv_train = self.train_compute.compute(node, fid)
                ic_train = ICAnalyzer(fv_train, self.fwd_train).compute_ic_summary()
                ls_train = StratificationTester(fv_train, self.fwd_train).compute_long_short_returns()
                ic_train["long_short_mean"] = float(ls_train.mean()) if len(ls_train) > 0 else 0.0
                train_results[fid] = ic_train
            except Exception as exc:
                logger.warning("train evaluation failed for %s: %s", fid, exc)
                continue

            try:
                fv_val = self.val_compute.compute(node, fid)
                ic_val = ICAnalyzer(fv_val, self.fwd_val).compute_ic_summary()
                ls_val = StratificationTester(fv_val, self.fwd_val).compute_long_short_returns()
                direction = 1 if ic_val.get("ic_mean", 0) >= 0 else -1
                ic_val.update({
                    "long_short_mean": float(ls_val.mean()) if len(ls_val) > 0 else 0.0,
                    "direction": direction,
                    "adjusted_ic": ic_val.get("ic_mean", 0) * direction,
                    "train_ic_mean": ic_train.get("ic_mean", 0),
                    "train_ic_ir": ic_train.get("ic_ir", 0),
                })
                val_results[fid] = ic_val
            except Exception as exc:
                logger.warning("validation evaluation failed for %s: %s", fid, exc)
                continue

        self.pool.update_ic_results(val_results)
        return train_results, val_results

    def evolve_one_generation(self) -> Dict:
        self.current_generation += 1
        gen = self.current_generation
        all_ids = self.pool.list_ids()
        train_results, val_results = self.evaluate_generation(all_ids)
        diagnosis = self.termination.get_overfitting_diagnosis(train_results, val_results)

        should_stop, reason = self.termination.should_terminate(train_results, val_results, gen)
        if should_stop:
            return {
                "generation": gen,
                "terminated": True,
                "reason": reason,
                "n_factors": self.pool.size(),
                "diagnosis": diagnosis,
            }

        parents = self.selector.select_top(top_k=5)
        if len(parents) < 2:
            return {"generation": gen, "terminated": True, "reason": "insufficient_parents", "n_factors": self.pool.size()}

        new_factors = []
        for pid in parents:
            parent_node = self.pool.get(pid)
            if parent_node is None:
                continue
            for _ in range(2):
                mutant = self.mutator.mutate(parent_node)
                if mutant and self.checker.validate(mutant):
                    nid = f"alpha_{FactorGenerator._next_id:04d}"
                    FactorGenerator._next_id += 1
                    new_factors.append((nid, mutant, gen, f"mutate({pid})"))

        for i in range(len(parents)):
            for j in range(i + 1, len(parents)):
                p1 = self.pool.get(parents[i])
                p2 = self.pool.get(parents[j])
                if p1 is None or p2 is None:
                    continue
                for child in self.crossover.crossover(p1, p2):
                    if child and self.checker.validate(child):
                        nid = f"alpha_{FactorGenerator._next_id:04d}"
                        FactorGenerator._next_id += 1
                        new_factors.append((nid, child, gen, f"crossover({parents[i]},{parents[j]})"))

        added = 0
        for fid, node, gen_num, origin in new_factors:
            if self.pool.add(fid, node, generation=gen_num):
                added += 1
                logger.info("added %s gen=%s origin=%s expr=%s", fid, gen_num, origin, node)
            if added >= 15:
                break

        log_entry = {
            "generation": gen,
            "terminated": False,
            "parents": parents,
            "new_factors": added,
            "pool_size": self.pool.size(),
            "train_top_ic": max((abs(v.get("ic_mean", 0)) for v in train_results.values()), default=0),
            "val_top_ic": max((abs(v.get("ic_mean", 0)) for v in val_results.values()), default=0),
            "diagnosis": diagnosis,
        }
        self.evolution_log.append(log_entry)
        return log_entry

    def run(self) -> Dict:
        if self.pool.size() == 0:
            self.initialize()

        while True:
            result = self.evolve_one_generation()
            if result.get("terminated"):
                break

        return {
            "total_generations": self.current_generation,
            "final_pool_size": self.pool.size(),
            "factor_ids": self.pool.list_ids(),
            "evolution_log": self.evolution_log,
        }

    def _compute_forward_returns(self, compute: FactorCompute) -> pd.Series:
        close = compute._data["close"]
        fwd = close.shift(-1) / close - 1
        result = fwd.stack(dropna=False)
        result.index.names = ["trade_date", "ts_code"]
        return result
