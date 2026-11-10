# Resume JSON

Every field is optional except `name`. Text can use `**bold**` and `*italic*` sparingly.

```json
{
  "name": "Anjali Nair",
  "headline": "Data Analyst · SQL, Power BI, Python",
  "contact": {"phone": "+91 98470 12345", "email": "a@example.com", "location": "Kochi, Kerala",
              "linkedin": "linkedin.com/in/...", "github": "github.com/...", "website": "...", "other": ["..."]},
  "summary": "2–3 sentences.",
  "experience": [{"role": "", "org": "", "location": "", "start": "Jun 2023", "end": "Present", "bullets": [""]}],
  "projects":   [{"name": "", "context": "College / Freelance / Personal", "link": "", "date": "2024", "bullets": [""]}],
  "education":  [{"degree": "", "school": "", "location": "", "score": "CGPA 8.4/10", "start": "2018", "end": "2021",
                   "details": ["Final-year project: ..."]}],
  "skills": [{"group": "Analysis", "items": ["SQL", "Python"]}],
  "certifications": [{"name": "", "issuer": "", "date": "2024"}],
  "achievements": ["..."],
  "volunteering": ["..."],
  "languages": ["Malayalam (native)", "English (fluent)", "Hindi (conversational)"],
  "extra": [{"title": "Publications", "items": ["..."]}],
  "personal": {"Notice period": "30 days", "Willing to relocate": "Yes"},
  "style": {
    "template": "clean",
    "page": "A4",
    "pages": 1,
    "accent": "#2D5BFF",
    "size": 10,
    "margins": "normal",
    "preset": "experienced",
    "order": ["summary", "experience", "projects", "skills", "education", "certifications", "languages"],
    "titles": {"experience": "Work History"},
    "hide": ["languages"],
    "photo": "photo.jpg",
    "custom": {"header": "centered", "head": "short", "skills": "chips", "entry": "stack", "name": "serif", "strip": true}
  }
}
```

Style options:
- `template`: clean, elegant, compact (ATS-safe) · sidebar, timeline, monogram (designer)
- `page`: A4 or Letter · `pages`: 1 or 2 (auto-fit tightens spacing and size down to a readable minimum)
- `accent`: any hex colour · `size`: body size in pt
- `margins`: narrow (12 mm), normal (15 mm), wide (19 mm)
- `preset`: experienced (work first) or fresher (education and projects first); `order` overrides it
- `titles`: rename any section · `hide`: leave sections out without deleting data
- `custom`: mix parts into your own design: `header` plain/centered/tint/monogram/sidebar · `head` bar/line/short/smallcaps
  · `skills` chips/rows · `entry` stack/timeline · `name` display/serif · `strip` true/false
- `photo`: path to a JPG/PNG next to the JSON, shown round; only when the person wants it
- language levels: native/fluent = 5 dots, professional/advanced/good = 4, conversational/intermediate/spoken = 3,
  basic = 2, beginner = 1 (dots show in the sidebar template; other templates list the names)

Command-line flags override the style block: `--template --page --pages --accent --margins --preset --size --photo`.
