#!/usr/bin/env python3
"""Check a resume: job-ad keyword match, recruiter-software (ATS) readability, and AI-sounding writing
(our phrase list plus the patterns of blader's Humanizer, MIT, see references/humanizer-blader.md).

Usage:
  python check_resume.py resume.json [--jd job_ad.txt] [--pdf Name_Resume.pdf]

Prints three reports:
  1. JOB MATCH   which important words of the job ad appear in the resume, and which are missing
                 (missing ones are only to be added if the person really has that skill or experience)
  2. ATS CHECK   the PDF's text can be extracted in reading order, with contact details found
  3. WRITING     phrases that sound AI-written or empty, weak bullet openings, bullets without a result
"""
import argparse, json, re, subprocess, sys
from collections import Counter

STOP = set("""a an the and or of to in for on with at by from as is are be been being this that these those it its
we you your our their they he she will shall would should can could may might must not no yes than then so such
into over under about across per via etc also more most other others any all each every some what which who whom
whose when where why how do does did done have has had having job role work working team teams candidate candidates
experience years year months month required requirements preferred plus strong good excellent ability able skills
skill knowledge understanding including include includes responsible responsibilities looking join company
opportunity position apply applicants using use used well new must-have nice-to-have preparing assisting assist
day-to-day daily ensure ensuring handle handling manage managing support supporting freshers fresher ms like
looking minimum maximum least based basic good great etc candidates salary location immediate joiners""".split())

AI_PHRASES = [
    "spearheaded", "leveraged", "leveraging", "leverage", "synergy", "synergies", "results-driven", "results driven", "dynamic",
    "passionate", "detail-oriented", "detail oriented", "go-getter", "self-starter", "team player", "hard-working",
    "hardworking", "proven track record", "track record", "seamlessly", "seamless", "robust", "cutting-edge",
    "state-of-the-art", "utilize", "utilized", "utilizing", "orchestrated", "championed", "pivotal", "instrumental",
    "fostered", "fostering", "foster", "tapestry", "delve", "realm", "navigate", "navigating", "holistic", "innovative solutions",
    "thought leader", "best-in-class", "world-class", "drive results", "think outside the box", "value-add",
    "responsible for", "duties included", "worked on", "helped with", "various", "multiple tasks", "etc.",
    "to work in a reputed organization", "reputed organisation", "reputed organization", "seeking a challenging",
]
# Patterns from blader's Humanizer (MIT, references/humanizer-blader.md), numbered as there.
HUMANIZER = {
    "§1 not X but Y": [r"\bnot (just|only|merely) [^.;]{1,60}\bbut\b", r"\bit'?s not [^.;]{1,40}, it'?s\b",
                       r"\bnot [^.;]{1,40}\. (it|this) (is|means)\b"],
    "§2 one-line closer": [r"\b(that is|that's) (the real win|what i bring|what matters)\b", r"\blet that sink in\b",
                           r"\bread that again\b"],
    "§3 deep-sounding saying": [r"\bthe real question is\b", r"\bat (its|my) core\b", r"\bwhat really matters\b",
                                r"\bis the language of\b", r"\bthe heart of\b"],
    "§4 staged run-up": [r"\bi am writing to express\b", r"\bhere'?s what i bring\b", r"\blet'?s dive in\b",
                         r"\bhere'?s the thing\b", r"\bwithout further ado\b", r"^\s*honestly\?"],
    "§12 overused AI word": [r"\b(crucial|enhance[ds]?|enhancing|bolstered|garner(ed)?|showcas(e|ed|ing)|meticulous(ly)?|"
                             r"vibrant|intricate|intricacies|interplay|testament|underscore[sd]?|landscape|delve|"
                             r"enduring|valuable|additionally|align(ed)? with|deep dive)\b"],
    "§13 inflated significance": [r"\bplay(ed|s)? a (key|pivotal|crucial|vital) role\b", r"\bstands? as a testament\b",
                                  r"\bsetting the stage\b", r"\bevolving landscape\b", r"\bindelible mark\b",
                                  r"\bexciting times ahead\b", r"\bthe future looks bright\b"],
    "§15 shallow -ing tail": [r", (ensuring|highlighting|underscoring|emphasizing|reflecting|symbolizing|contributing to|"
                              r"cultivating|fostering|encompassing|showcasing)\b"],
    "§16 sales language": [r"\b(renowned|groundbreaking|breathtaking|stunning|diverse array|exemplifies|commitment to|"
                           r"nestled|in the heart of|must-visit)\b"],
    "§18 avoiding is/has": [r"\b(serve[sd]?|stood|stands|functioned) as (a|an|the)\b", r"\bboasts?\b"],
    "§22 chatbot residue": [r"\bi hope this helps\b", r"\bcertainly!", r"\bgreat question\b", r"\bof course!",
                            r"\blet me know if\b"],
}


def humanizer_check(text, label):
    low = text.lower(); found = []
    for name, pats in HUMANIZER.items():
        hits = sorted({m.group(0).strip(" ,") for pat in pats for m in re.finditer(pat, low, re.M)})
        if hits:
            found.append(f"{name}: " + ", ".join(f"'{h}'" for h in hits[:4]))
    # §8 dashes: count em dashes, and en dashes that aren't number/date ranges
    dashes = len(re.findall(r"—|--", text)) + len(re.findall(r"(?<![0-9A-Za-z]) – (?![0-9]|Present|present)", text))
    if dashes:
        found.append(f"§8 dashes: {dashes} (use commas, colons or full stops)")
    print(f"   humanizer ({label}): " + ("clean ✓" if not found else ""))
    for f in found:
        print(f"     ! {f}")
    return found


WEAK_OPENERS = ("responsible", "worked", "helped", "assisted in", "involved", "participated", "handled various",
                "duties", "tasked")


def resume_text(d):
    out = []
    def walk(x):
        if isinstance(x, str): out.append(x)
        elif isinstance(x, dict):
            for k, v in x.items():
                if k != "style": walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(d)
    return "\n".join(out)


def terms(text):
    words = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]*[A-Za-z0-9+#]|[A-Za-z]", text)
    toks = [w.strip(".-/").lower() for w in words]
    uni = [t for t in toks if t not in STOP and len(t) > 1]
    bi = [f"{a} {b}" for a, b in zip(toks, toks[1:]) if a not in STOP and b not in STOP and len(a) > 1 and len(b) > 1]
    return Counter(uni), Counter(bi)


def job_match(d, jd):
    r = resume_text(d).lower()
    u, b = terms(jd)
    picked = [w for w, n in b.most_common(40) if n >= 2][:12] + [w for w, n in u.most_common(80)][:40]
    seen, keys = set(), []
    for k in picked:
        if k not in seen and not any(k in s for s in seen if " " in s):
            seen.add(k); keys.append(k)
    keys = keys[:35]
    def has(k):
        stem = re.escape(k[:-1] if k.endswith("s") and len(k) > 4 else k)
        return re.search(r"(?<![a-z0-9])" + stem + r"(s|es)?(?![a-z0-9])", r) is not None
    hit = [k for k in keys if has(k)]
    miss = [k for k in keys if k not in hit]
    pct = round(100 * len(hit) / max(1, len(keys)))
    print(f"\n1. JOB MATCH  {pct}% of the job ad's main words appear ({len(hit)}/{len(keys)})")
    print("   found:   " + (", ".join(hit) or "-"))
    print("   missing: " + (", ".join(miss) or "-"))
    print("   Only add a missing word if it is true for this person. Use the ad's exact wording (e.g. 'Power BI', "
          "not 'PowerBI') and place it where the work was done, not only in Skills.")


def ats_check(pdf, d):
    print("\n2. ATS CHECK")
    try:
        txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, timeout=30).stdout
    except Exception:
        try:
            from pypdf import PdfReader
            txt = "\n".join(p.extract_text() or "" for p in PdfReader(pdf).pages)
        except Exception as e:
            print(f"   could not read the PDF text ({e}); skip"); return
    ok = True
    c = d.get("contact", {}) or {}
    for k in ("email", "phone"):
        v = c.get(k)
        if v and re.sub(r"\s", "", v) not in re.sub(r"\s", "", txt):
            print(f"   ✗ {k} not found as text in the PDF"); ok = False
    if d.get("name") and d["name"].split()[0].lower() not in txt.lower():
        print("   ✗ name not found as text"); ok = False
    for e in d.get("experience", []) or []:
        if e.get("role") and e["role"].lower()[:20] not in txt.lower():
            print(f"   ✗ role '{e['role']}' not readable"); ok = False
    words = len(txt.split())
    print(f"   {'✓' if ok else '!'} text is selectable: {words} words read back as real text (no images of text)")
    if words > 750:
        print(f"   ! {words} words is long for one page; most recruiters skim in under a minute")


def writing_check(d):
    print("\n3. WRITING")
    text = resume_text(d)
    low = text.lower()
    found = sorted({p for p in AI_PHRASES if re.search(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", low)})
    print("   AI-sounding / empty phrases: " + (", ".join(found) if found else "none ✓"))
    bul = []
    for sec in ("experience", "projects"):
        for e in d.get(sec, []) or []:
            bul += e.get("bullets", []) or []
    weak = [b for b in bul if b.strip().lower().startswith(WEAK_OPENERS)]
    noresult = [b for b in bul if not re.search(r"\d|%|₹|\blakh|\bcrore|\bper (day|week|month)", b.lower())]
    starts = Counter(b.split()[0].lower() for b in bul if b.split())
    rep = [w for w, n in starts.items() if n >= 3]
    long_ = [b for b in bul if len(b.split()) > 32]
    print(f"   bullets: {len(bul)}; weak openings: {len(weak)}; without a number or result: {len(noresult)}"
          + (f"; same first word 3+ times: {', '.join(rep)}" if rep else "") + (f"; over 32 words: {len(long_)}" if long_ else ""))
    for b in weak[:4]:
        print(f"     weak: {b[:90]}")
    if len(noresult) > len(bul) * 0.6 and bul:
        print("   ! most bullets have no result. Ask the person for real numbers (how many, how often, how much, how fast). "
              "Never invent them.")
    humanizer_check(text, "resume")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json"); ap.add_argument("--jd"); ap.add_argument("--pdf")
    ap.add_argument("--text", action="append", help="a prose file to check too (cover letter, LinkedIn About)")
    a = ap.parse_args()
    d = json.load(open(a.json, encoding="utf-8"))
    if a.jd:
        job_match(d, open(a.jd, encoding="utf-8").read())
    else:
        print("\n1. JOB MATCH  (no job ad given: pass --jd job_ad.txt)")
    if a.pdf:
        ats_check(a.pdf, d)
    writing_check(d)
    for f in a.text or []:
        t = open(f, encoding="utf-8").read()
        print(f"\n4. PROSE  {f}")
        low = t.lower()
        ai = sorted({p for p in AI_PHRASES if re.search(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", low)})
        print("   AI-sounding / empty phrases: " + (", ".join(ai) if ai else "none ✓"))
        humanizer_check(t, f.split("/")[-1])


if __name__ == "__main__":
    main()
