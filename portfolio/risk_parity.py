"""风险平价/最大回撤最小化优化（基于cvxpy）"""
import numpy as np
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


class RiskParityOptimizer:
    """风险平价与风险最小化优化器"""

    def __init__(self, factor_returns: pd.DataFrame):
        """
        factor_returns: pd.DataFrame index=trade_date, columns=factor_ids
                        每期各因子的多空收益
        """
        self.factor_returns = factor_returns.dropna()

    def risk_parity_weights(self) -> pd.Series:
        """
        风险平价权重优化。
        minimize sum_i sum_j (w_i*sigma_i^2 - w_j*sigma_j^2)^2
        subject to sum(w)=1, w>=0
        """
        try:
            import cvxpy as cp
        except ImportError:
            logger.warning("cvxpy未安装，回退到等权")
            n = self.factor_returns.shape[1]
            return pd.Series(1.0 / n, index=self.factor_returns.columns)

        n = self.factor_returns.shape[1]
        cov = self.factor_returns.cov().values
        vars_ = np.diag(cov)
        if np.any(vars_ <= 0):
            vars_ = np.maximum(vars_, 1e-8)

        w = cp.Variable(n)
        risk_contribs = cp.multiply(w, vars_)

        obj = 0
        for i in range(n):
            for j in range(n):
                obj += (risk_contribs[i] - risk_contribs[j]) ** 2

        constraints = [cp.sum(w) == 1, w >= 0.025]
        prob = cp.Problem(cp.Minimize(obj), constraints)

        try:
            prob.solve(solver=cp.ECOS, max_iters=5000)
        except Exception:
            try:
                prob.solve(solver=cp.OSQP, max_iter=5000)
            except Exception:
                logger.warning("风险平价优化失败，使用等权")
                return pd.Series(1.0 / n, index=self.factor_returns.columns)

        if w.value is None:
            return pd.Series(1.0 / n, index=self.factor_returns.columns)

        weights = pd.Series(np.maximum(w.value, 0), index=self.factor_returns.columns)
        weights = weights / weights.sum()
        logger.info(f"风险平价权重: {weights.to_dict()}")
        return weights

    def min_cvar_weights(self, alpha: float = 0.05) -> pd.Series:
        """
        最小CVaR权重优化（作为最大回撤最小化的代理）。
        minimize CVaR_alpha(-w'R)
        subject to sum(w)=1, w>=0
        """
        try:
            import cvxpy as cp
        except ImportError:
            logger.warning("cvxpy未安装")
            n = self.factor_returns.shape[1]
            return pd.Series(1.0 / n, index=self.factor_returns.columns)

        returns = self.factor_returns.values
        T, n = returns.shape

        w = cp.Variable(n)
        z = cp.Variable(T)
        gamma = cp.Variable()

        portfolio_returns = returns @ w
        obj = gamma + (1.0 / (alpha * T)) * cp.sum(z)

        constraints = [
            z >= -portfolio_returns - gamma,
            z >= 0,
            cp.sum(w) == 1,
            w >= 0.025,
        ]

        prob = cp.Problem(cp.Minimize(obj), constraints)

        try:
            prob.solve(solver=cp.ECOS, max_iters=5000)
        except Exception:
            try:
                prob.solve(solver=cp.OSQP, max_iter=5000)
            except Exception:
                logger.warning("CVaR优化失败")
                return self.risk_parity_weights()

        if w.value is None:
            return self.risk_parity_weights()

        weights = pd.Series(np.maximum(w.value, 0), index=self.factor_returns.columns)
        weights = weights / weights.sum()
        logger.info(f"最小CVaR权重: {weights.to_dict()}")
        return weights
