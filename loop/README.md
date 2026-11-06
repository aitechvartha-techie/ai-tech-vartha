# 🔁 LOOP pack: make AI actually finish the job

AI-യോട് ജോലി ഏൽപ്പിച്ചാൽ പകുതി ചെയ്തിട്ട് "Done" എന്ന് പറയുന്നുണ്ടോ? ഈ pack അതിനുള്ളതാണ്.
(Does your AI say "Done" after doing half the job? This pack is for that.)

From the **AI Tech Vartha** Short on the Ralph Loop. Three things inside:

1. [The loop prompt](#1-the-loop-prompt) I use all the time: works in any AI coding tool
2. [The Ralph Loop plugin](#2-the-ralph-loop-plugin-claude-code): Anthropic's official one, for Claude Code
3. [The loop-until-done skill](#3-the-loop-until-done-skill-claude-code): install once, Claude follows the loop by itself

---

## 1. The loop prompt

Works in Claude Code, Cursor, Copilot, ChatGPT and others. Copy it, then add your task at the end:

```text
Before you start, restate what I'm asking for as a short checklist of requirements,
and ask me about anything unclear. Don't start coding until I confirm.

Then work in a loop:
1. For each requirement, write a test (or a small check script) first, and run it.
   It should fail, because the feature doesn't exist yet.
2. Build the feature in small steps. After each step, run ALL the checks
   (tests + build + lint), not just the new one, so nothing that worked before breaks.
3. If anything fails, read the error output, find the real cause, fix it, and run the
   checks again. Never edit or delete a test just to make it pass.
4. Stop when every check passes, or after 10 attempts. If you hit the limit, stop and
   tell me what is still failing and why. Don't keep guessing.
5. Finish with evidence: the exact commands you ran and their output, and which test
   covers which requirement. "All tests pass" without the output doesn't count.

My task:
```

## 2. The Ralph Loop plugin (Claude Code)

The Ralph Loop keeps giving Claude the same task every time it tries to stop, until the job is done
or a limit is reached. It's named after Ralph Wiggum from The Simpsons, who never stops trying.
Developer Geoffrey Huntley started the technique; Anthropic now ships it as an official plugin.

**Install** (inside Claude Code):

```text
/plugin install ralph-loop@claude-plugins-official
```

**Run it. Always set a limit:**

```text
/ralph-loop "Build X. Done = all tests in tests/ pass and the build is clean. Output DONE when finished." --max-iterations 10 --completion-promise "DONE"
```

**Stop it:** `/cancel-ralph`

Good to know (from the plugin's own notes):

- Use it for tasks with a clear finish line, like tests that must pass. Not for design decisions or
  debugging a live production system.
- `--max-iterations` is your safety net. Every round costs tokens, so without a limit the cost keeps going up.
- `--completion-promise` is an exact text match, so give it one clear word like `DONE`.

Source: [anthropics/claude-plugins-official › ralph-loop](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-loop)

Also built into Claude Code: `/goal all tests in tests/ pass and lint is clean` keeps Claude going
until that condition is met.

## 3. The loop-until-done skill (Claude Code)

A Claude Code skill that makes Claude follow the loop above on its own whenever you ask it to build or
fix something: requirements first, tests first, run every check, fix until all pass, at most 10 rounds,
then show the evidence.

**Install** (one command, macOS / Linux / WSL):

```bash
mkdir -p ~/.claude/skills/loop-until-done && curl -fsSL https://raw.githubusercontent.com/aitechvartha-techie/ai-tech-vartha/main/loop/skills/loop-until-done/SKILL.md -o ~/.claude/skills/loop-until-done/SKILL.md
```

Or download [`SKILL.md`](skills/loop-until-done/SKILL.md) and put it in `~/.claude/skills/loop-until-done/`.
Then start a new Claude Code session. It's used automatically, or you can ask for it: *"use loop-until-done"*.

---

## Why this works

Anthropic's own Claude Code guide says the most useful thing you can do is give Claude a check that
comes back **pass or fail**. With it, Claude makes the change, runs the check, reads what broke and
fixes it before running the check again. Without it, "looks done" is all it has, and *you* become the
tester. → [Claude Code best practices](https://code.claude.com/docs/en/best-practices)

In the 2025 Stack Overflow Developer Survey, 66% of developers named "AI solutions that are almost right,
but not quite" as a frustration they run into.

---

ഇത്തരം AI tips-നായി **AI Tech Vartha** subscribe ചെയ്യൂ, follow ചെയ്യൂ 🔔
(YouTube · Instagram · Facebook)
