"""强制输出格式 - 决策分析 → 可执行代码 → 需要反馈的数据列表"""
from typing import List, Dict, Any
from datetime import datetime


class Reporter:
    """标准化步骤报告生成器"""

    @staticmethod
    def report(step_id: int, step_name: str,
               decision_analysis: str,
               executable_code: str = "",
               data_feedback_list: List[str] = None,
               results: Any = None) -> Dict:
        """生成标准化步骤报告"""
        return {
            "step_id": step_id,
            "step_name": step_name,
            "decision_analysis": decision_analysis,
            "executable_code": executable_code,
            "data_feedback_list": data_feedback_list or [],
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def print_report(report: Dict):
        """格式化打印步骤报告"""
        print("\n" + "=" * 60)
        print(f"[Step {report['step_id']}] {report['step_name']}")
        print("=" * 60)

        print(f"\n## 决策分析\n{report['decision_analysis']}")

        if report.get("executable_code"):
            print(f"\n## 可执行代码\n```python\n{report['executable_code']}\n```")

        if report.get("data_feedback_list"):
            print("\n## 需要反馈的数据")
            for i, item in enumerate(report["data_feedback_list"], 1):
                print(f"  {i}. {item}")

        print("\n" + "-" * 60)

    @staticmethod
    def evolution_log(generation: int, parents: List[str],
                      new_factors: List[str],
                      metrics: Dict,
                      overfitting_diagnosis: str) -> str:
        """生成进化日志"""
        lines = [
            f"\n{'='*60}",
            f"第 {generation} 代进化日志",
            f"{'='*60}",
            f"父本: {parents}",
            f"新增因子: {new_factors}",
            f"评估指标: {metrics}",
            f"\n过拟合诊断:\n{overfitting_diagnosis}",
        ]
        return "\n".join(lines)

    @staticmethod
    def drawdown_report(stage: str, action: str,
                        before_metrics: Dict,
                        after_metrics: Dict) -> str:
        """生成回撤改进报告"""
        lines = [
            f"\n--- 回撤改进: {stage} ---",
            f"操作: {action}",
            f"改进前 MaxDD: {before_metrics.get('max_drawdown', 'N/A')}",
            f"改进后 MaxDD: {after_metrics.get('max_drawdown', 'N/A')}",
        ]
        return "\n".join(lines)
