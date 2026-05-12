# claudets 工程治理方案

## 1. 设计目标

本配置包把 Claude Code 在 claudets 项目中的行为分为三层：

```text
CLAUDE.md：长期项目记忆与总规则
agents：专业审查角色
hooks：强制执行前/后守门
commands：高频工作流快捷入口
```

## 2. 为什么不只靠 agent

agent 适合专业判断，但不一定每次都会自动触发。  
hooks 是生命周期钩子，可以在工具调用前后强制执行检查。

## 3. 推荐工作流

```text
用户提出任务
→ UserPromptSubmit 注入项目规则
→ Claude 读取 CLAUDE.md
→ 必要时调用 agent
→ PreToolUse 执行前守门
→ Claude 修改/运行
→ PostToolUse 自动检查
→ Stop 要求交付摘要
```

## 4. 当前 agents

- project-architect：全局工程架构
- data-contract-steward：数据契约
- research-methodology-reviewer：研究方法
- backtest-governance-reviewer：回测治理
- implementation-quality-reviewer：代码质量
- report-governance-reviewer：报告治理
- release-handoff-manager：交付摘要

## 5. 当前 commands

- /project-audit：全局审查
- /preflight：执行前计划
- /postcheck：执行后检查
- /report-review：报告审查
- /handoff：交付摘要
- /runbook：运行手册
