# claudets 项目级 Claude Code 治理包

这是专门给当前 `claudets` 工程使用的 Claude Code 配置包。  
它不是通用模板，也不是继续执着于之前那几个 bug 的修复包，而是一个“全局工程治理包”。

包含：

```text
CLAUDE.md                       项目总规则
.claude/agents/                 项目专用 subagent
.claude/commands/               项目专用 slash command
.claude/hooks/                  执行前/执行后/结束前自动守门
.claude/settings.json           hooks 与权限配置
docs/                           说明文档
```

---

## 1. 安装方式

### 第一步：备份旧配置

在项目根目录执行：

```powershell
cd C:\Users\liuji\Desktop\claudets

if (Test-Path .claude) { Rename-Item .claude .claude_backup_old }
if (Test-Path CLAUDE.md) { Rename-Item CLAUDE.md CLAUDE_old.md }
```

如果你已经手动删了旧的，也可以跳过。

---

### 第二步：解压本包

把压缩包里的内容复制到：

```text
C:\Users\liuji\Desktop\claudets
```

最终结构应为：

```text
claudets/
  CLAUDE.md
  .claude/
    settings.json
    agents/
    commands/
    hooks/
  docs/
  main.py
  ...
```

---

### 第三步：启动 Claude Code

Windows PowerShell 里建议用：

```powershell
cd C:\Users\liuji\Desktop\claudets
claude.cmd
```

如果你已经修过 PowerShell 执行策略，也可以直接：

```powershell
claude
```

---

## 2. 启用检查

进入 Claude Code 后依次输入：

```text
/agents
```

确认能看到这些项目 agent：

```text
project-architect
data-contract-steward
research-methodology-reviewer
backtest-governance-reviewer
implementation-quality-reviewer
report-governance-reviewer
release-handoff-manager
```

再输入：

```text
/hooks
```

确认能看到：

```text
UserPromptSubmit
PreToolUse
PostToolUse
Stop
```

然后输入 `/`，应该能看到项目 commands，例如：

```text
/project-audit
/preflight
/postcheck
/report-review
/handoff
/runbook
```

---

## 3. 推荐第一次使用

第一次不要直接让它改代码，先跑全局审查：

```text
/project-audit
```

或者直接说：

```text
从全局工程角度审查 claudets，不要先改代码，先给我工程结构、数据契约、研究方法、回测治理、代码质量、报告治理的整体方案。
```

---

## 4. 以后日常怎么用

### 做任何大改前

```text
/preflight 我想调整因子生成和报告输出，先判断影响范围和最小修改计划
```

### 改完后

```text
/postcheck
```

### 看报告

```text
/report-review
```

### 收尾

```text
/handoff
```

---

## 5. hooks 会自动做什么

### UserPromptSubmit

每次你发消息后，自动给 Claude 注入简短项目规则。

### PreToolUse

Claude 准备执行 Bash/Edit/Write/MultiEdit 前会检查：

```text
危险命令
直接改数据库/密钥/大结果
写入 token
未确认就跑长耗时回测或报告生成
```

不合格会阻止。

### PostToolUse

Claude 修改文件后会自动检查：

```text
Python compileall
明文 token
错误成本扣法
事后 clip 回撤
dt.start_time 周频日期
因子方向疑似问题
```

有问题会反馈给 Claude 继续修。

### Stop

如果本轮改过文件，Claude 准备结束时会被阻止一次，要求补交付摘要。第二次允许结束，避免死循环。

---

## 6. 注意

这个包是“工程治理包”，不是“自动收益优化器”。  
它的目标是让 Claude Code 每次工作更稳，不是替你盲目调参。
