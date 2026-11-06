# The Ralph Loop: a complete guide

> "In its purest form, Ralph is a Bash loop." (Geoffrey Huntley, who created the technique)

**Contents:**
[What it is](#what-it-is) · [Where it came from](#where-it-came-from) · [How it works](#how-it-works) ·
[Run it: 3 ways](#run-it-3-ways) · [Writing a good Ralph prompt](#writing-a-good-ralph-prompt) ·
[Huntley's rules](#huntleys-rules-from-the-original-post) · [When to use it, when not](#when-to-use-it-when-not) ·
[Cost and safety](#cost-and-safety) · [Troubleshooting](#troubleshooting)

---

## What it is

AI coding agents stop when the work *looks* done. The Ralph Loop doesn't let them stop there: every time
the agent tries to finish, it gets **the same task again**. It looks at the files and git history it left
last round, sees what's still broken, and keeps going until the job is really done or a limit is reached.

It's named after **Ralph Wiggum** from *The Simpsons*: not the smartest kid, but he never stops trying.

## Where it came from

| When | What happened |
|---|---|
| 14 Jul 2025 | Geoffrey Huntley publishes *"Ralph Wiggum as a 'software engineer'"* with a one-line Bash loop ([ghuntley.com/ralph](https://ghuntley.com/ralph/)) |
| 2025 | Results he reports: a $50k USD contract delivered for $297 in model costs; a whole programming language ("CURSED") built with Ralph; a Y Combinator hackathon team "put a coding agent in a while loop and it shipped 6 repos overnight" |
| Late 2025 | Anthropic ships it as an official Claude Code plugin, `ralph-loop` ([source](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-loop)) |
| End of 2025 | The technique goes viral among AI developers |

The results above are as reported by Huntley and in the plugin README, not independent studies.

## How it works

**The original** is literally this:

```bash
while :; do cat PROMPT.md | claude-code ; done
```

Run the agent with the same prompt file, forever. Each run starts fresh, but the code, tests, notes and
git history from earlier runs are still on disk, so every round builds on the last one.

**The official plugin** does the same thing inside your Claude Code session, using a **Stop hook**:

```
you start /ralph-loop "task..."
        │
        ▼
 Claude works on the task ──► tries to stop
        ▲                         │
        │            Stop hook checks:
        │            did it print the completion promise (e.g. DONE)?
        │            hit --max-iterations?
        │               │ no                 │ yes
        └── same prompt fed back ◄─┘          ▼
                                        loop ends, you review
```

What makes it work isn't the loop alone. It's **backpressure**: tests, a type checker, a linter or a
build that say *pass* or *fail*. Each round Claude runs them, reads what broke and fixes it. Without a
check, the loop just repeats "looks done" more times.

## Run it: 3 ways

### A. The official plugin (easiest, inside Claude Code)

```text
/plugin install ralph-loop@claude-plugins-official
```

```text
/ralph-loop "Build a REST API for todos. Requirements: CRUD operations, input validation, tests. Output <promise>COMPLETE</promise> when done." --completion-promise "COMPLETE" --max-iterations 20
```

| Command / option | What it does |
|---|---|
| `/ralph-loop "<prompt>"` | Start the loop with this task |
| `--max-iterations <n>` | Stop after n rounds. **Default is unlimited, so always set it** |
| `--completion-promise "<text>"` | The exact phrase that means "done" (exact text match) |
| `/cancel-ralph` | Stop the loop now |

Tip: for a long task, put the prompt in a file (see [templates/PROMPT.md](templates/PROMPT.md)) and
start with `/ralph-loop "Follow the instructions in PROMPT.md" --completion-promise "DONE" --max-iterations 20`.

### B. Built into Claude Code: `/goal`

No plugin needed. You give a finish condition, and after every turn a separate small model checks whether
it's met. If not, Claude keeps going.

```text
/goal all tests in tests/ pass and lint is clean, or stop after 20 turns
```

- `/goal` with nothing after it shows the status: turns, time, token spend, last reason.
- `/goal clear` stops it.
- Works headless too: `claude -p "/goal CHANGELOG.md has an entry for every PR merged this week"`.

The checker only reads the conversation, so write a condition Claude's own output can prove ("`npm test`
exits 0", not "the code is good"). Docs: [code.claude.com/docs/en/goal](https://code.claude.com/docs/en/goal)

### C. The original Bash loop, with a safety cap

For people who want to see the raw idea. This version stops after 10 rounds and caps each run:

```bash
for i in $(seq 1 10); do
  echo "=== Ralph round $i ==="
  claude -p "$(cat PROMPT.md)" --max-turns 30
  grep -q "DONE" STATUS.md 2>/dev/null && break   # your prompt tells Claude to write DONE here when finished
done
```

Run it in its own git branch or a fresh folder, so you can throw the result away if it goes wrong.

## Writing a good Ralph prompt

From the plugin README and Huntley's post, a Ralph prompt needs four things:

1. **Clear completion criteria.** List measurable conditions (endpoints, validation, tests passing, docs)
   and the exact promise to print when all are true.
2. **Phases.** Split a big project into phases, each with its own tests.
3. **Self-correction.** Ask for a test-first cycle: write a failing test, implement, run, fix, repeat.
4. **Escape hatches.** Say what to do when stuck: write down the blocker, what was tried, and alternatives.
   Because the promise is an exact match, it can't tell "done" from "blocked", so `--max-iterations`
   is your real safety net.

A ready template: **[templates/PROMPT.md](templates/PROMPT.md)**, plus a task list Claude keeps up to date
each round: **[templates/fix_plan.md](templates/fix_plan.md)**.

## Huntley's rules (from the original post)

- **One thing per loop.** "Ask Ralph to do one thing per loop. Only one thing." Small steps fail less.
- **Specs first.** Before looping, have a long conversation with the AI to write the specs, one file per
  topic in a `specs/` folder. Ralph reads them every round.
- **A plan file.** `fix_plan.md` holds the to-do list. Claude picks the next item, finishes it, updates the list.
- **Backpressure.** After each change, run the tests for the code that changed. Tests and static analysis
  are what reject bad work. Without a type checker or static analysis, expect "a bonfire of outcomes".
- **No placeholders.** Claude tends to write minimal or placeholder code, so the prompt must demand full
  implementations.
- **Don't assume it's missing.** Tell Ralph to search the code before assuming something isn't
  implemented, or it may write it twice.
- **Tune it like a guitar.** When Ralph does something dumb, don't blame the tool. Add a rule to the
  prompt (his example: a sign at the playground slide, "SLIDE DOWN, DON'T JUMP, LOOK AROUND").
- **Greenfield only.** Huntley wouldn't use it on an existing codebase: it's for new projects.
- **Expect broken mornings.** Sometimes you wake up to code that doesn't compile, and have to decide
  whether to rescue it or reset. That's why you run it on a branch.

## When to use it, when not

| ✅ Good fit | ❌ Poor fit |
|---|---|
| Clear, checkable goal: tests that must pass, a build that must be green | Needs human judgment or design decisions |
| New (greenfield) projects you can leave running | Existing production code, or debugging a live system |
| Iterating: getting a test suite green, migrations, refactors with tests | One-shot jobs, unclear success criteria |

## Cost and safety

- **Every round costs tokens.** Unlimited rounds can mean an unlimited bill. Always set
  `--max-iterations`, a turn limit in `/goal`, or `--max-turns` / `--max-budget-usd` with `claude -p`.
- **Contain it.** Use a separate git branch or worktree, and permission rules that limit what it can touch.
- **Check the result yourself.** Anthropic's advice for any unattended run: it should know what "done"
  looks like, be able to check its own work, have a cap on turns or spend, and **a person approves the
  result at the end**. ([Claude Code best practices](https://code.claude.com/docs/en/best-practices))

## Troubleshooting

| Problem | Fix |
|---|---|
| The loop never ends | Your completion promise doesn't exactly match what Claude prints, or the task can't succeed. Set `--max-iterations`; use `/cancel-ralph` |
| It "finishes" but things are broken | No real check. Add tests/build/lint to the prompt and ask for the command output as proof |
| It keeps rewriting the same thing | Ask for one item per round, keep `fix_plan.md`, tell it to search before writing |
| Windows: hook errors | The hook needs Git for Windows; point `hooks.json` at `C:/Program Files/Git/bin/bash.exe` (not `usr/bin`) as the plugin README explains |

---

More links: **[references.md](references.md)**
