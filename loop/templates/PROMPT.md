# PROMPT.md: a Ralph Loop prompt template

<!-- Copy this file into your project, fill in the [brackets], and start the loop:
     /ralph-loop "Follow the instructions in PROMPT.md" --completion-promise "DONE" --max-iterations 20
     Every round Claude reads this same file again, so everything it needs must be written here. -->

## Goal

Build [what you want, in one or two sentences].

## Read first, every round

- `specs/` : the requirements, one file per topic
- `fix_plan.md` : the task list (update it every round)
- The existing code: **search before you assume something is missing**, so nothing gets written twice

## Each round, do exactly ONE item

1. Pick the most important unchecked item in `fix_plan.md`.
2. Write or update a test for it first, and run it. It should fail.
3. Implement it **fully**: no placeholders, no TODO stubs, no fake data.
4. Run ALL checks:
   - Tests: `[your test command, e.g. npm test]`
   - Build / types: `[e.g. npm run build]`
   - Lint: `[e.g. npm run lint]`
5. If anything fails, read the output, fix the real cause, run the checks again.
   Never edit, skip or delete a test just to make it pass.
6. Tick the item in `fix_plan.md`, add anything new you discovered, and commit with a clear message.

## Done means

All of these are true, **and you have seen the passing output in this round**:

- [ ] Every item in `fix_plan.md` is ticked
- [ ] All tests pass
- [ ] The build and lint are clean
- [ ] [any other finish line, e.g. "the app starts and the home page loads"]

Only then, write `DONE` on the last line of your reply.

## If you're stuck

If the same item fails 3 rounds in a row, stop working on it. Write in `fix_plan.md` under **Blocked**:
what fails, what you tried, and 2 ideas to try next. Move to the next item.

## Rules (add a line every time the loop does something dumb: tune it like a guitar)

- Don't change files outside this project.
- Don't add new libraries without a reason written in `fix_plan.md`.
- [your rule]
