"""Factor pool with structure de-duplication and validation metrics."""
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from factors.expression_tree import ExprNode


class FactorPool:
    def __init__(self):
        self._factors: Dict[str, ExprNode] = {}
        self._structure_hashes: set = set()
        self._factor_values: Dict[str, pd.Series] = {}
        self._ic_results: Dict[str, dict] = {}
        self._generation: Dict[str, int] = {}

    def add(self, factor_id: str, node: ExprNode, generation: int = 0) -> bool:
        structure_hash = node.structure_hash()
        if structure_hash in self._structure_hashes:
            return False
        if factor_id in self._factors:
            self._structure_hashes.discard(self._factors[factor_id].structure_hash())
            self._ic_results.pop(factor_id, None)
        self._factors[factor_id] = node
        self._structure_hashes.add(structure_hash)
        self._generation[factor_id] = generation
        return True

    def remove(self, factor_id: str) -> None:
        if factor_id not in self._factors:
            return
        self._structure_hashes.discard(self._factors[factor_id].structure_hash())
        self._factors.pop(factor_id, None)
        self._factor_values.pop(factor_id, None)
        self._ic_results.pop(factor_id, None)
        self._generation.pop(factor_id, None)

    def get(self, factor_id: str) -> Optional[ExprNode]:
        return self._factors.get(factor_id)

    def list_ids(self) -> List[str]:
        return list(self._factors.keys())

    def size(self) -> int:
        return len(self._factors)

    def update_values(self, values: Dict[str, pd.Series]) -> None:
        self._factor_values.update(values)

    def update_ic_results(self, results: Dict[str, dict]) -> None:
        self._ic_results.update(results)

    def get_ic_result(self, factor_id: str) -> Optional[dict]:
        return self._ic_results.get(factor_id)

    def get_generation(self, factor_id: str) -> int:
        return self._generation.get(factor_id, 0)

    def correlation_with_pool(self, new_values: pd.Series) -> float:
        if not self._factor_values:
            return 0.0
        scores = []
        for values in self._factor_values.values():
            common_idx = new_values.dropna().index.intersection(values.dropna().index)
            if len(common_idx) < 10:
                continue
            corr = new_values[common_idx].corr(values[common_idx], method="spearman")
            if not pd.isna(corr):
                scores.append(abs(corr))
        return float(np.mean(scores)) if scores else 0.0

    def get_low_correlation_factors(self, max_corr: float = 0.85) -> List[str]:
        selected = []
        for fid in self.list_ids():
            values = self._factor_values.get(fid)
            if values is None or not selected:
                selected.append(fid)
                continue
            corrs = []
            for sid in selected:
                selected_values = self._factor_values.get(sid)
                if selected_values is None:
                    continue
                common_idx = values.dropna().index.intersection(selected_values.dropna().index)
                if len(common_idx) >= 10:
                    corrs.append(abs(values[common_idx].corr(selected_values[common_idx], method="spearman")))
            avg_corr = float(np.nanmean(corrs)) if corrs else 0.0
            if avg_corr < max_corr:
                selected.append(fid)
        return selected
