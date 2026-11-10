# Writing a resume that sounds like a person

Recruiters skim. They also spot AI-written resumes in seconds: the same inflated verbs, the same empty
adjectives, no real detail. Write the way a sharp, modest professional would describe their own work to a peer.

## The bullet formula
**Did what → to/with what → so what (a number or a visible change).**

| Weak | Strong |
|---|---|
| Responsible for billing in the shop. | Handled billing for about 150 customers a day at a busy supermarket counter, with no cash shortages in 8 months. |
| Worked on a dashboard project. | Built a Power BI sales dashboard for 42 stores that replaced 6 manual Excel reports. |
| Helped the team with social media. | Ran the clinic's Instagram page; posts went from 2 to 12 a month and enquiries by DM roughly doubled. |
| Taught students. | Taught Physics to three Class 11 batches (about 120 students); my section's pass rate rose from 82% to 94%. |
| Leveraged cutting-edge tools to drive results. | (delete: says nothing) |

Rules:
- Start with a plain past-tense verb (present tense for the current job). Vary first words; never the same first
  word three times in one job.
- One idea per bullet, 12–28 words. No full stop needed at the end, but be consistent.
- Numbers: count, frequency, money (₹, lakh, crore are fine for Indian employers), time saved, %, rank, scale.
  Only real ones. "About" and "roughly" are honest and fine.
- If there's no number, show a visible change ("…managers now check it every Monday", "…still in use").
- Put the job ad's words where the work happened ("…prepared GSTR-1 and GSTR-3B drafts…"), not only in Skills.
- Keep tool names exact: Power BI, Tally Prime, AutoCAD, Google Ads, SAP FICO, React, Excel.

## Words to avoid (the checker flags them)
spearheaded, leveraged, synergy, results-driven, dynamic, passionate, detail-oriented, go-getter, self-starter,
team player, hard-working, proven track record, seamless(ly), robust, cutting-edge, state-of-the-art, utilize(d),
orchestrated, championed, pivotal, instrumental, fostered, tapestry, delve, realm, navigate, holistic,
"responsible for", "duties included", "worked on", "helped with", "various", "etc.", and the old Indian
"Objective: to work in a reputed organization…" line.

Prefer: built, wrote, set up, ran, cut, sold, fixed, trained, planned, handled, opened, grew, reduced, tested,
designed, answered, prepared, checked, served, taught, led (only if they really led people).

## Style tells to remove
- Long dashes (—) everywhere, three-item lists in every sentence, "not only X but also Y".
- Adjectives about personality (dedicated, motivated, enthusiastic). Show it through results instead.
- Same sentence shape in every bullet. Mix short and longer ones.
- Overclaiming: "expert", "mastery", "guru". Say what they did.

## Summary (2–3 sentences)
Pattern: *[Role] with [N years / background] in [field]. [What they do best, with tools]. [One proof].*

> Accounts assistant with a B.Com and a 3-month internship at a CA firm. I enter bills in Tally Prime, draft
> GST returns and reconcile bank statements, and in my last month none of my GST drafts needed corrections.

Freshers: replace years with the degree and the best internship or project.

## Field notes (Kerala / India job market)
- **IT / software**: projects with links (GitHub, live demo) matter as much as jobs. Name the stack per bullet.
- **Accounts / finance**: Tally Prime, GST returns by name, TDS, reconciliation, audit support, volumes per month.
- **Nursing / healthcare**: ward or department, patient load per shift, registrations and licences with numbers and
  validity (e.g. Kerala Nursing Council), BLS/ACLS.
- **Teaching**: board (CBSE/State/ICSE), classes and subjects, batch sizes, results, activities run.
- **Sales / retail / hospitality**: targets vs achieved, average bill, customers per day, ratings, upsells.
- **Engineering / site**: project value, size, tools (AutoCAD, Revit, STAAD), safety record, team size.
- **Career change**: lead with transferable proof and a recent course or project in the new field; one honest
  line for gaps ("2022–2023: career break for family care; completed Google Data Analytics course").

## Cover letter / portal message
150–220 words. Paragraph 1: the role, where they saw it, one line on why this company. Paragraph 2: one proof
story with a number that matches the ad's main need. Paragraph 3: availability and a simple close. No "I am
writing to express my keen interest", no "I believe I would be a great fit".

## Humanizer pass (blader's Humanizer, bundled in `humanizer-blader.md`)
After writing, run a humanizer pass. Read `humanizer-blader.md` once and apply it **fully to prose** (summary,
cover letter, LinkedIn About, messages to HR) and **lightly to bullets**. The patterns that show up most in
resumes:

| # | Pattern | How it looks in a resume | Fix |
|---|---|---|---|
| 1 | Not X but Y | "Not just an analyst, but a storyteller with data." | State the fact: "I turn sales data into weekly reports managers use." |
| 2 | One-line closers | Cover letter ending "That is what I bring." | End on the last concrete fact or the availability line. |
| 3 | Sayings that sound deep | "Data is the language of business." | Cut; say what you did. |
| 4 | Staged run-up | "I am writing to express my keen interest…", "Here's what I bring:" | Start with the role and one proof. |
| 6 | Forced triads | "innovative, driven and detail-oriented"; three-item lists in every bullet | Keep only items that are each real and distinct. |
| 7 | Repeated openings | Five bullets starting "Managed…" | Vary the verbs; merge. |
| 8 | Dashes | "Built a dashboard — cutting report time — for 42 stores" | Commas or a new sentence. (Date ranges like Jun 2023 – Present are fine.) |
| 12 | Overused AI words | crucial, enhance, robust, pivotal, showcase, meticulous, vibrant, key (adj), valuable, landscape | Plain words. |
| 13 | Inflated significance | "played a pivotal role in shaping the team's success" | Say the result with a number. |
| 15 | Shallow -ing tails | "…, ensuring seamless delivery and fostering collaboration" | Cut the tail or state the real result. |
| 16 | Sales language | "renowned", "groundbreaking", "diverse array" | State what it is. |
| 18 | Avoiding is/has | "served as the point of contact" | "was the point of contact". |
| 19 | Bold as decoration | bold on every skill | Bold only names that need it (none in most bullets). |
| 22 | Chatbot residue | "I hope this helps", "Certainly!" left in a cover letter | Remove. |

Not for resumes: §11 (missing subjects): bullets without "I" are the normal resume style.
`check_resume.py` flags these automatically (in the resume JSON, and in any prose file passed with `--text`).
