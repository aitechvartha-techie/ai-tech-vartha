#!/usr/bin/env python3
"""Grade a resume (0-100) against a job description and list what to ask and what to fix.
Used by the review loop: grade -> ask -> rewrite -> rebuild -> grade again.

Usage:
  python grade_resume.py resume.json [--jd job_description.txt] [--pdf Name_Resume.pdf] [--json grade.json]

Parts (out of 100; without a job description, the job parts are left out and the rest is scaled up):
  Job match         30  share of the job description's main words found in the resume
  Keywords in use   10  matched words that appear in work/projects, not only in Skills
  Evidence          20  bullets with a number or visible result
  Human writing     15  no AI-sounding phrases or Humanizer patterns
  Bullet quality    10  strong openings, varied first words, not too long
  Structure         10  headline, short summary, contact, grouped skills, dates
  Fit and ATS        5  within the page limit and readable as text
"""
import argparse, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_resume as C  # noqa: E402


def bullets_of(d):
    out = []
    for sec in ("experience", "projects"):
        for e in d.get(sec, []) or []:
            for b in e.get("bullets", []) or []:
                out.append((sec, e.get("role") or e.get("name") or "", b))
    return out


def jd_keywords(jd):
    """Main asks of the job as short phrases: runs of content words between stop words and punctuation
    (e.g. "tally prime", "petty cash", "vendor payments", "bank reconciliation")."""
    phrases, seen = [], set()
    for chunk in re.split(r"[,;:.()\n!?]|\s[–-]\s", jd):
        toks = [w.strip(".-/").lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9+#./-]*[A-Za-z0-9+#]|[A-Za-z]", chunk)]
        run = []
        for w in toks + ["and"]:
            if w in C.STOP or len(w) < 2:
                if run:
                    for i in range(0, len(run), 3):
                        ph = " ".join(run[i:i + 3])
                        short_junk = len(ph) <= 3 and ph.upper() not in jd   # "com" from B.Com, but keep TDS, GST
                        if ph not in seen and not short_junk:
                            seen.add(ph); phrases.append(ph)
                run = []
            else:
                run.append(w)
    return phrases[:30]


def has(k, text):
    stem = re.escape(k[:-1] if k.endswith("s") and len(k) > 4 else k)
    return re.search(r"(?<![a-z0-9])" + stem + r"(s|es)?(?![a-z0-9])", text) is not None


def humanizer_hits(text):
    low = text.lower(); hits = []
    for name, pats in C.HUMANIZER.items():
        for pat in pats:
            for m in re.finditer(pat, low, re.M):
                hits.append((name, m.group(0).strip(" ,")))
    hits += [("AI phrase", p) for p in C.AI_PHRASES if re.search(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", low)]
    return hits


def grade(d, jd=None, pdf=None, pages_limit=1):
    parts, ask, fix = {}, [], []
    text = C.resume_text(d).lower()
    work = " ".join(b for _, _, b in bullets_of(d)).lower() + " " + " ".join(
        (e.get("role", "") + " " + e.get("name", "")) for s in ("experience", "projects") for e in d.get(s, []) or []).lower()
    bl = bullets_of(d)

    if jd:
        keys = jd_keywords(jd)
        found = [k for k in keys if has(k, text)]
        missing = [k for k in keys if k not in found]
        parts["Job match"] = (round(30 * len(found) / max(1, len(keys))), 30)
        meta = " ".join([d.get("headline", ""), d.get("summary", ""), (d.get("contact") or {}).get("location", "")]
                        + [str(v) for v in (d.get("personal") or {}).values()]
                        + [str(x) for x in (d.get("languages") or [])]).lower()   # languages don't need a bullet
        found_skills = [k for k in found if not has(k, meta)]   # a city or the job title isn't a skill to show
        in_use = [k for k in found_skills if has(k, work)]
        parts["Keywords in use"] = (round(10 * len(in_use) / max(1, len(found_skills))), 10)
        for k in missing[:5]:
            ask.append(f"The job asks for '{k}'. Have you done or used this? If yes, where (which job or project) and how?")
        only_skills = [k for k in found_skills if k not in in_use][:4]
        for k in only_skills:
            fix.append(f"'{k}' is only listed, not shown: add it to the bullet where you actually used it (if you did).")

    with_result = [b for _, _, b in bl if re.search(r"\d|%|₹|\blakh|\bcrore|\bper (day|week|month)", b.lower())]
    parts["Evidence"] = (round(20 * len(with_result) / max(1, len(bl))) if bl else 0, 20)
    for sec, where, b in [x for x in bl if x[2] not in with_result][:3]:
        ask.append(f"At {where}: \"{b[:70]}…\" Roughly how many, how often, how much, or what changed because of it?")

    hits = humanizer_hits(C.resume_text(d))
    parts["Human writing"] = (max(0, 15 - 3 * len(hits)), 15)
    for name, h in hits[:6]:
        fix.append(f"Rewrite '{h}' ({name}).")

    q = 10
    weak = [b for _, _, b in bl if b.strip().lower().startswith(C.WEAK_OPENERS)]
    starts = {}
    for _, _, b in bl:
        if b.split(): starts[b.split()[0].lower()] = starts.get(b.split()[0].lower(), 0) + 1
    rep = [w for w, n in starts.items() if n >= 3]
    long_ = [b for _, _, b in bl if len(b.split()) > 32]
    q -= 2 * len(weak) + 2 * len(rep) + len(long_)
    parts["Bullet quality"] = (max(0, q), 10)
    fix += [f"Weak opening: \"{b[:60]}…\"" for b in weak[:3]]
    fix += [f"Too many bullets start with '{w}': vary the verbs." for w in rep]
    fix += [f"Shorten: \"{b[:60]}…\" ({len(b.split())} words)" for b in long_[:2]]

    s = 10
    if not d.get("headline"): s -= 2; fix.append("Add a headline: the target role plus 2-3 strongest skills.")
    summ = d.get("summary", "")
    if not summ: s -= 3; ask.append("In one line: what job are you aiming for, and what are you best at?")
    elif len(summ.split()) > 70: s -= 2; fix.append(f"Summary is {len(summ.split())} words: cut to 2-3 sentences.")
    c = d.get("contact", {}) or {}
    if not c.get("email") or not c.get("phone"): s -= 2; ask.append("What email and phone number should employers use?")
    sk = d.get("skills")
    if not sk: s -= 2; ask.append("Which tools, software or skills do you use for real at work?")
    elif not (isinstance(sk, list) and sk and isinstance(sk[0], dict)): s -= 1; fix.append("Group the skills (2-4 groups).")
    if any(not (e.get("start") or e.get("end")) for e in d.get("experience", []) or []):
        s -= 1; ask.append("Some jobs have no dates: when did each start and end (month and year)?")
    parts["Structure"] = (max(0, s), 10)

    f = 5
    if pdf and os.path.exists(pdf):
        try:
            info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
            n = int(re.search(r"Pages:\s+(\d+)", info).group(1))
            if n > pages_limit: f -= 3; fix.append(f"PDF is {n} pages, limit {pages_limit}: shorten.")
            txt = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout
            if c.get("email") and c["email"] not in txt: f -= 2; fix.append("Email not readable as text in the PDF.")
        except Exception:
            pass
    parts["Fit and ATS"] = (f, 5)

    got = sum(v for v, _ in parts.values()); out_of = sum(m for _, m in parts.values())
    score = round(100 * got / out_of)
    return {"score": score, "parts": {k: f"{v}/{m}" for k, (v, m) in parts.items()}, "ask": ask, "fix": fix}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json"); ap.add_argument("--jd"); ap.add_argument("--pdf"); ap.add_argument("--json-out", "--json", dest="jout")
    a = ap.parse_args()
    d = json.load(open(a.json, encoding="utf-8"))
    jd = open(a.jd, encoding="utf-8").read() if a.jd else None
    g = grade(d, jd, a.pdf, int((d.get("style") or {}).get("pages", 1)))
    band = "strong, ready to send" if g["score"] >= 85 else "good, a round of fixes will help" if g["score"] >= 70 else "needs work"
    print(f"SCORE {g['score']}/100  ({band})")
    print("  " + " · ".join(f"{k} {v}" for k, v in g["parts"].items()))
    if g["ask"]:
        print("\nASK THE PERSON (only they know):"); [print(f"  - {x}") for x in g["ask"]]
    if g["fix"]:
        print("\nFIX IN THE TEXT (Claude can do these):"); [print(f"  - {x}") for x in g["fix"]]
    if a.jout:
        json.dump(g, open(a.jout, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
