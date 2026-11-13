# Skeptical review: how to run it

Our professor asks us to red-team the repo with an AI coding agent before each checkpoint
(FIN331 Quick Reference, *Starter prompts for coding agents*, #5).

## The prompt

```text
Review this repo like a skeptical finance professor.
Look for look-ahead bias and leakage, merges without validate, unit
and frequency mismatches, hard-coded paths or keys, and steps that
don't reproduce from run_all.py. List issues ranked by severity; don't fix
anything.
```

## How to run it

1. Pull the latest branch and rebuild everything first, so the agent reviews what we'd submit:
   ```bash
   git switch checkpoint-2
   git pull
   python run_all.py
   ```
2. Open a coding agent (Claude Code, Codex, or Copilot) **in the repo root** and paste the prompt above.
3. Save the agent's answer, unedited, as `audits/NN_skeptical_review_output.md`
   (`00` for Checkpoint 2, `02` for the next checkpoint, and so on). Note the date, branch, and agent at the top.
4. Write the team's response in `audits/NN_self_audit.md`: which findings are real, what we
   fixed, what's still open, and the 10-point checklist.

## Runs so far

| Checkpoint | Output | Self-audit |
|---|---|---|
| 2 | [`00_skeptical_review_output.md`](00_skeptical_review_output.md) | [`01_self_audit.md`](01_self_audit.md) |
