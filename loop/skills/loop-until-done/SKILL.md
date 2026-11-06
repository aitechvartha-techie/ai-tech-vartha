---
name: loop-until-done
description: Build or fix code in a check-driven loop - restate the requirements, write tests first, then change, run every check, read failures and fix until all checks pass (capped at 10 rounds), and finish with evidence. Use when asked to build a feature or app, fix a bug, or "make it actually work", and whenever the work should not be called done until it is verified.
---

# Loop until done

AI coding tools stop when the work *looks* done. This skill makes "done" mean *verified*: the work only
counts as finished when a check that returns pass or fail says so.

## 1. Agree on what "done" means (before any code)

- Restate the request as a short numbered checklist of requirements.
- List anything unclear or assumed, and ask the user. Don't start coding until they confirm.
- Name the check that will prove each requirement: a test, the build, a linter, a script that compares
  output, or a screenshot next to the expected result.

## 2. Write the checks first

- For each requirement, write a test (or a small check script) and run it. It should fail now, because
  the feature doesn't exist yet. If it passes already, the test isn't testing the new behaviour: fix it.
- Note the exact command that runs ALL checks (tests + build + lint). Use it every round.

## 3. The loop

Repeat, at most **10 rounds** (or the limit the user gives):

1. Make one small change toward the next failing requirement.
2. Run the full check command, not only the newest test, so nothing that worked before breaks.
3. If anything fails, read the actual output, find the real cause, and fix that cause.
4. Never edit, skip or delete a test just to make it pass. If a test is wrong, say why and ask first.
5. Never claim a result you didn't see in the output.

Stop when every check passes. If the limit is reached, stop and report what still fails, what you tried,
and your best guess at the cause. Don't keep guessing past the limit.

## 4. Finish with evidence

- The exact command(s) you ran and their final output.
- Which test covers which requirement from step 1.
- Anything not covered by a check (say it plainly, so the user can test it by hand).

"All tests pass" without the output doesn't count.

## Why this works

Anthropic's Claude Code guide calls giving Claude a pass-or-fail check the most useful thing you can do:
with it, Claude makes the change, runs the check, reads what broke and fixes it before checking again.
Without it, "looks done" is all it has, and you become the tester.
https://code.claude.com/docs/en/best-practices
