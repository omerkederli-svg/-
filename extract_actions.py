#!/usr/bin/env python3
"""Deterministic pre-pass over raw meeting notes for the
Meeting Notes to Actions skill.

This does NOT produce the final record. It does the mechanical part:
split the raw text into lines, classify candidate lines into
decisions / commitments / unresolved threads, flag ownerless
commitments, and detect relative dates. The reasoning passes
(judgement on settlement, verb rewriting, de-duplication) stay
with the model - this just makes sure nothing is missed.

Usage:
    python extract_actions.py notes.txt
    python extract_actions.py notes.txt --meeting-date 2026-03-02
    cat notes.txt | python extract_actions.py --meeting-date 2026-03-02

Output: JSON on stdout.

Stdlib only. Python 3.8+.

-*- coding: utf-8 -*-
"""

import argparse
import datetime as dt
import json
import re
import sys
from typing import Dict, List, Optional

# --------------------------------------------------------------------------
# Lexicons
# --------------------------------------------------------------------------

# A settled choice. Strong signal: explicit decision markers.
# NOTE: these are strong enough to beat an UNRESOLVED marker that appears
# later in the same line (e.g. "decided X, revisit in 6 months" is a
# decision that carries a review trigger, not an unresolved thread).
DECISION_MARKERS = [
    r"\bdecided\b",
    r"\bdecision\b",
    r"\bwe(?:'| a)?re going with\b",
    r"\bgoing with\b",
    r"\bsettled on\b",
    r"\bagreed (?:to|on)\b",
    r"\bapproved\b",
    r"\bfinal(?:ized|ised)\b",
    r"\bsigned off\b",
    r"\bconfirmed\b",
    r"\bresolved (?:to|that)\b",
]

# A choice that was NOT settled. These override the decision markers only
# when the decision marker is absent or weaker - adjudicated in
# _adjudicate_decision() below.
UNRESOLVED_MARKERS = [
    r"\btabled\b",
    r"\bdeferred\b",
    r"\bparking lot\b",
    r"\btake (?:it|this) offline\b",
    r"\bdiscuss offline\b",
    r"\brevisit\b",
    r"\bno decision\b",
    r"\bended without\b",
    r"\bstill (?:open|unresolved)\b",
    r"\bunresolved\b",
    r"\bpend(?:ing|s)\b",
    r"\bTBD\b",
    r"\bnot settled\b",
]

# Phrases that mark an *unsettled debate* rather than a commitment:
# opinion-stating verbs plus a disagreeing counterpart. A line matching
# these is an Open Question even if it also trips a commitment marker.
DEBATE_MARKERS = [
    r"\b(?:thinks|thinks that|believes|argues|wants|prefers|proposes|suggests|pushing|pushes|favou?rs|advocates)\b",
    r"\bvs\.?\b",
    r"\bversus\b",
]

# A settled-choice marker that outranks a debate reading when both fire
# (e.g. "decided: go with $49, sarah thinks X, marc pushing Y").
STRONG_SETTLE_MARKERS = [
    r"\bdecided\b",
    r"\bdecision\b",
    r"\bsettled on\b",
    r"\bwe(?:'| a)?re going with\b",
    r"\bagreed (?:to|on)\b",
    r"\bapproved\b",
    r"\bsigned off\b",
]

# First-person or assigned promise.
# Deliberately narrow: bare "we should" is NOT here, because "we should
# do X" is as often an opinion in a debate as a commitment. It is caught
# by SOFT_COMMITMENT_MARKERS, and only promoted when no debate signal fires.
COMMITMENT_MARKERS = [
    r"\bI(?:'| a)?ll\b",
    r"\bI will\b",
    r"\bI(?:'| a)?m going to\b",
    r"\bwe(?:'| a)?ll\b",
    r"\bwe will\b",
    r"\b(?:he|she|they)(?:'| a)?ll\b",
    r"\bwill (?:send|get|draft|set up|book|review|schedule|update|prepare|share|confirm|route)\b",
    r"\bneed(?:s)? to\b",
    r"\bhas to\b",
    r"\baction item\b",
    r"\bTODO\b",
    r"\bowner:\b",
    r"\bby (?:mon|tues|wednes|thurs|fri|satur|sun)day\b",
    r"\bwill own\b",
    r"\btake(?:s)? (?:on|care of)\b",
]

# Soft commitment: a suggestion that may be an assignment, promoted to a
# commitment only when no debate signal is present on the same line.
SOFT_COMMITMENT_MARKERS = [
    r"\bwe should\b",
    r"\bwe need to\b",
    r"\blet(?:'| u)?s\b",
]

# Questions raised, whether or not they were answered.
QUESTION_MARKERS = [
    r"\?",
    r"\bwho(?:'| i)?s going to\b",
    r"\bwho will\b",
    r"\bwe need someone to\b",
    r"\bneed someone\b",
    r"\bnobody volunteered\b",
    r"\bno(?:body| one) (?:named|volunteered|took)\b",
    r"\bopen question",
    r"\bunclear\b",
]

# A "ghost commitment": work that the group agreed is needed, with nobody
# named to do it. These MUST surface as action rows owned by UNASSIGNED -
# they are the highest-value output of the whole skill, because an
# unowned commitment is exactly the one that evaporates.
GHOST_COMMITMENT_MARKERS = [
    r"\bneed(?:s)? someone to\b",
    r"\bneed(?:s)? to\b.*\bnobody\b",
    r"\bnobody volunteered\b",
    r"\bno(?:body| one) (?:named|volunteered|took|owns)\b",
    r"\bsomeone should\b",
    r"\bwe need\b",
    r"\bunassigned\b",
    r"\bwho(?:'| i)?s going to\b",
]

# Signals that two source lines refer to the same commitment, for the
# de-duplication pass. Crude content-word overlap; the model confirms.
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "to", "of", "for", "in", "on",
    "at", "by", "with", "from", "is", "are", "was", "were", "be", "been",
    "it", "its", "this", "that", "these", "those", "we", "i", "he", "she",
    "they", "ll", "will", "get", "got", "said", "say", "says", "yeah",
    "also", "later", "again", "mentioned", "pushing", "thinks", "should",
    "today", "tomorrow", "week", "s", "d", "ve", "re", "m", "t",
}

# Relative date expressions and their resolution.
RELATIVE_DATES = {
    r"\btoday\b": 0,
    r"\btomorrow\b": 1,
    r"\btonight\b": 0,
    r"\bend of (?:the )?day\b": 0,
    r"\bEOD\b": 0,
    r"\bEOW\b": None,       # end of week - resolver handles separately
    r"\bend of (?:the )?week\b": None,
    r"\bnext week\b": 7,
    r"\bearly next week\b": 3,
}

# Bare weekday names: resolve forward to the next occurrence if meeting date known.
WEEKDAYS = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}

# Vague urgency - acknowledged but never resolved into a date.
VAGUE_DATES = [r"\bsoon\b", r"\bASAP\b", r"\bright away\b", r"\bwhen possible\b",
               r"\bat some point\b", r"\bnext sprint\b", r"\bQ[1-4]\b"]

# Verbs that reliably start a real action (used to detect topic-phrased rows).
ACTION_VERBS = {"send", "draft", "set", "book", "schedule", "review", "update",
                "prepare", "share", "confirm", "route", "align", "investigate",
                "obtain", "decide", "file", "publish", "circulate", "follow",
                "reach", "create", "write", "build", "test", "fix", "migrate",
                "run", "organize", "organise", "compile", "collect", "check",
                "verify", "close", "open", "migrate", "notify", "escalate",
                "document", "present", "negotiate", "approve", "deliver"}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _search_any(patterns: List[str], text: str) -> Optional[str]:
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def _mentions(patterns: List[str], text: str) -> List[str]:
    out = []
    for p in patterns:
        for m in re.finditer(p, text, flags=re.IGNORECASE):
            out.append(m.group(0))
    return out


def _extract_named_people(text: str) -> List[str]:
    """Collect capitalised name-like tokens. Crude on purpose: the model
    decides who owns what; this only feeds the 'is there a name here'
    signal that drives the UNASSIGNED flag."""
    names = []
    # Capitalised word not at sentence start, or a name after a colon.
    for m in re.finditer(r"(?<![.!?]\s)(?<!^)\b([A-Z][a-z]{1,15})\b", text):
        tok = m.group(1)
        if tok.lower() in WEEKDAYS:
            continue
        if tok.lower() in {"the", "this", "that", "and", "but", "for", "with",
                           "from", "into", "then", "when", "also", "legal",
                           "design", "sales", "beta", "tbd", "ok", "okay",
                           "monday", "tuesday", "wednesday", "thursday",
                           "friday", "saturday", "sunday"}:
            continue
        names.append(tok)
    # Explicit "Name:" speaker labels are strong signals.
    for m in re.finditer(r"(?:^|[-•*]\s*)([a-z]{2,15})\s*:", text):
        names.append(m.group(1))
    # De-dupe, preserve order.
    seen, out = set(), []
    for n in names:
        k = n.lower()
        if k not in seen:
            seen.add(k)
            out.append(n)
    return out


def _resolve_relative(text: str, meeting_date: Optional[dt.date]) -> Dict[str, Optional[str]]:
    """Find date expressions. Resolution only when meeting_date is known."""
    found = {"raw": None, "resolved": None, "kind": None}

    # Absolute ISO / written dates pass through.
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if m:
        return {"raw": m.group(1), "resolved": m.group(1), "kind": "absolute"}

    m = re.search(r"\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b", text)
    if m:
        return {"raw": m.group(1), "resolved": m.group(1), "kind": "absolute"}

    # "by Thursday" and friends.
    m = re.search(r"\b(?:by|on|before)\s+(mon|tues?|wed(?:nes)?|thur?s?|fri|sat(?:ur)?|sun)(?:day)?\b",
                  text, flags=re.IGNORECASE)
    if m:
        wd_name = m.group(1).lower()
        wd = WEEKDAYS.get(wd_name)
        if wd is None:
            for k, v in WEEKDAYS.items():
                if k.startswith(wd_name):
                    wd = v
                    break
        raw = m.group(0)
        resolved = None
        if wd is not None and meeting_date is not None:
            delta = (wd - meeting_date.weekday()) % 7
            delta = delta or 7          # "by Thursday" means the coming Thursday
            resolved = (meeting_date + dt.timedelta(days=delta)).isoformat()
        return {"raw": raw.strip(), "resolved": resolved, "kind": "weekday"}

    # Offset phrases.
    for pat, offset in RELATIVE_DATES.items():
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            resolved = None
            if meeting_date is not None and offset is not None:
                resolved = (meeting_date + dt.timedelta(days=offset)).isoformat()
            elif meeting_date is not None and "week" in m.group(0).lower():
                # end of / next week -> the coming Friday
                delta = (4 - meeting_date.weekday()) % 7 or 7
                resolved = (meeting_date + dt.timedelta(days=delta)).isoformat()
            return {"raw": m.group(0), "resolved": resolved, "kind": "relative"}

    # Vague urgency: reported, never resolved.
    m = re.search("|".join(VAGUE_DATES), text, flags=re.IGNORECASE)
    if m:
        return {"raw": m.group(0), "resolved": None, "kind": "vague"}

    return found


def _content_words(text: str) -> set:
    words = re.findall(r"[a-z]{3,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def find_duplicate_groups(commitments: List[Dict]) -> List[Dict]:
    """Group commitment lines that probably describe the same thing.

    Heuristic: content-word overlap of >= 2 words. This deliberately
    over-flags - the model makes the final merge call, guided by the
    rule "same owner and same object of the verb = one row".
    """
    groups: List[Dict] = []
    claimed = set()
    for i, a in enumerate(commitments):
        if i in claimed:
            continue
        wa = _content_words(a["source"])
        group = [a]
        for j in range(i + 1, len(commitments)):
            if j in claimed:
                continue
            b = commitments[j]
            wb = _content_words(b["source"])
            if len(wa & wb) >= 2:
                group.append(b)
                claimed.add(j)
        if len(group) > 1:
            claimed.add(i)
            groups.append({
                "source_lines": [g["n"] for g in group],
                "note": "Likely the same commitment. Collapse into one row, "
                        "keeping the most specific phrasing and the latest date.",
                "lines": [g["source"] for g in group],
            })
    return groups


def _is_verb_first(action_text: str) -> bool:
    cleaned = re.sub(r"^[\s\-•*0-9.)]+", "", action_text).strip().lower()
    if not cleaned:
        return False
    first = re.split(r"[\s,:]+", cleaned)[0]
    return first in ACTION_VERBS


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------

def _adjudicate_decision(text: str) -> Optional[str]:
    """Decide whether a line that touches decision territory is a genuine
    settled decision or an unresolved thread.

    The hard case: "decided: go with $49, revisit after 100 signups".
    Both a settle marker ("decided") and an unresolved marker ("revisit")
    fire. The settle marker wins when it is a strong one, because the
    "revisit" is a review trigger attached *to the decision*, not evidence
    the decision is open.

    Returns "decision", "unresolved", or None when neither applies.
    """
    strong = _search_any(STRONG_SETTLE_MARKERS, text)
    soft = _search_any(DECISION_MARKERS, text)
    unresolved = _search_any(UNRESOLVED_MARKERS, text)

    if strong:
        # A strong settle marker beats an unresolved marker elsewhere on
        # the line. "no decision" is the exception: it negates by name.
        if unresolved and re.search(r"\bno decision\b|\bnot settled\b", text, re.I):
            return "unresolved"
        return "decision"
    if soft and not unresolved:
        return "decision"
    if unresolved:
        return "unresolved"
    return None


def classify_line(text: str, meeting_date: Optional[dt.date]) -> Optional[Dict]:
    """Classify one source line. Returns None for blank/structural lines."""
    stripped = text.strip()
    if not stripped or len(stripped) < 3:
        return None

    decision_hit = _search_any(DECISION_MARKERS, stripped)
    unresolved_hit = _search_any(UNRESOLVED_MARKERS, stripped)
    hard_commit = _search_any(COMMITMENT_MARKERS, stripped)
    soft_commit = _search_any(SOFT_COMMITMENT_MARKERS, stripped)
    debate_hit = _search_any(DEBATE_MARKERS, stripped)
    question_hit = _search_any(QUESTION_MARKERS, stripped)
    date_info = _resolve_relative(stripped, meeting_date)
    people = _extract_named_people(stripped)

    verdict = _adjudicate_decision(stripped)
    ghost_hit = _search_any(GHOST_COMMITMENT_MARKERS, stripped)
    has_work_verb = _is_verb_first(stripped) or bool(
        re.search(r"\b(?:set up|send|draft|book|review|update|prepare|share|"
                  r"confirm|route|schedule|create|write|build|test|fix|"
                  r"compile|collect|check|verify|document|present)\b",
                  stripped, re.I)
    )

    # Priority ladder. Order matters:
    #   1. A settled decision outranks everything else on the line.
    #   2. A ghost commitment - work agreed as needed, owner unnamed -
    #      outranks a plain question reading, because it must become an
    #      UNASSIGNED action row. This is the skill's highest-value case.
    #   3. A debate (opinions in conflict) is an open question, and it
    #      suppresses a *soft* commitment ("we should...") but not a hard
    #      one ("I'll...").
    #   4. A hard commitment is an action item unless the line is really
    #      an explicit deferral.
    #   5. A soft commitment counts only when no debate signal fired.
    is_ghost = bool(ghost_hit) and has_work_verb and verdict != "decision"
    if verdict == "decision":
        category = "decision"
    elif is_ghost:
        category = "commitment"
    elif debate_hit and not hard_commit:
        category = "unresolved"
    elif hard_commit and not (unresolved_hit and not soft_commit and not hard_commit):
        category = "commitment"
    elif soft_commit and not debate_hit and not unresolved_hit:
        category = "commitment"
    elif unresolved_hit or question_hit or verdict == "unresolved":
        category = "unresolved"
    else:
        category = "context"

    # An explicit deferral never carries work forward as a live action,
    # even if it names a person - "Marc said he'd look at it later, tabled".
    if unresolved_hit and category == "commitment" and not hard_commit and not is_ghost:
        category = "unresolved"

    flags: List[str] = []
    if category == "commitment":
        if is_ghost and not people:
            flags.append("OWNERLESS")
        elif not people:
            flags.append("OWNERLESS")
        if date_info["raw"] is None:
            flags.append("UNDATED")
        elif date_info["resolved"] is None and meeting_date is None:
            flags.append("RELATIVE_DATE_UNRESOLVED")
        if date_info["kind"] == "vague":
            flags.append("VAGUE_DATE")
        if is_ghost:
            flags.append("GHOST_COMMITMENT")
        # Two mentions of the same thing, by the same person, is the
        # canonical duplicate shape the de-dup pass must collapse.
        if hard_commit and re.search(r"\b(?:also|again|later|as (?:I )?said)\b",
                                     stripped, re.I):
            flags.append("POSSIBLE_DUPLICATE")

    return {
        "n": None,                       # assigned by caller
        "source": stripped,
        "category": category,
        "markers": {
            "decision": decision_hit,
            "unresolved": unresolved_hit,
            "commitment": hard_commit or soft_commit,
            "debate": debate_hit,
            "question": question_hit,
        },
        "people_mentioned": people,
        "date": date_info if date_info["raw"] else None,
        "flags": flags,
        "looks_verb_first": _is_verb_first(stripped) if category == "commitment" else None,
    }


def analyse(raw: str, meeting_date: Optional[dt.date]) -> Dict:
    # Strip common quoting / markdown noise but keep line structure.
    lines = raw.splitlines()

    # Ignore a leading fenced code block marker pair if the whole input is fenced.
    items: List[Dict] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            continue
        rec = classify_line(line, meeting_date)
        if rec is None:
            continue
        rec["n"] = i + 1
        items.append(rec)

    buckets: Dict[str, List[Dict]] = {
        "decision": [], "commitment": [], "unresolved": [], "context": []
    }
    for it in items:
        buckets[it["category"]].append(it)

    commitments = buckets["commitment"]
    ownerless = [c for c in commitments if "OWNERLESS" in c["flags"]]
    undated = [c for c in commitments if "UNDATED" in c["flags"]]
    ghosts = [c for c in commitments if "GHOST_COMMITMENT" in c["flags"]]

    # De-duplication pre-pass: include context lines too, because a repeat
    # mention often reads as context ("also sarah mentioned the pricing
    # page again later") rather than as a fresh commitment.
    dedup_pool = commitments + buckets["context"]
    duplicates = find_duplicate_groups(dedup_pool)

    return {
        "meeting_date": meeting_date.isoformat() if meeting_date else None,
        "counts": {
            "total_lines": len(lines),
            "classified": len(items),
            "decisions": len(buckets["decision"]),
            "commitments": len(commitments),
            "unresolved": len(buckets["unresolved"]),
            "context": len(buckets["context"]),
            "ownerless": len(ownerless),
            "undated": len(undated),
            "ghost_commitments": len(ghosts),
        },
        "candidate_decisions": buckets["decision"],
        "candidate_commitments": commitments,
        "candidate_unresolved": buckets["unresolved"],
        "context_lines": buckets["context"],
        "possible_duplicate_groups": duplicates,
        "warnings": _warnings(items, meeting_date),
    }


def _warnings(items: List[Dict], meeting_date: Optional[dt.date]) -> List[str]:
    w = []
    commits = [i for i in items if i["category"] == "commitment"]
    if not commits:
        w.append("No candidate commitments found. Either the notes record no "
                 "owners/commitments, or the phrasing is unusual - re-read the "
                 "source manually before concluding the list is empty.")
    if commits and all(i["people_mentioned"] == [] for i in commits):
        w.append("No names found anywhere in the candidate commitments. Every "
                 "row will be UNASSIGNED - confirm the notes really do not name "
                 "owners rather than assuming the name extraction failed.")
    if meeting_date is None and any(
        i["date"] and i["date"]["kind"] in ("relative", "weekday") for i in items
    ):
        w.append("Relative dates present but no meeting date supplied. Keep the "
                 "raw relative form (e.g. 'Thursday') in the Due column; do not "
                 "resolve against today's date.")
    return w


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Pre-pass extraction of decisions, commitments and open "
                    "threads from raw meeting notes."
    )
    ap.add_argument("path", nargs="?", help="Path to the notes file. Omit to read stdin.")
    ap.add_argument("--meeting-date", dest="meeting_date",
                    help="Meeting date as YYYY-MM-DD. Required to resolve "
                         "relative dates into calendar dates.")
    ap.add_argument("--pretty", action="store_true", help="Indent the JSON output.")
    args = ap.parse_args()

    if args.path:
        with open(args.path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        print(json.dumps({"error": "empty input"}, ensure_ascii=False))
        return 2

    mdate = None
    if args.meeting_date:
        try:
            mdate = dt.date.fromisoformat(args.meeting_date)
        except ValueError:
            print(json.dumps(
                {"error": f"invalid --meeting-date {args.meeting_date!r}; expected YYYY-MM-DD"},
                ensure_ascii=False))
            return 2

    result = analyse(raw, mdate)
    print(json.dumps(result, ensure_ascii=False,
                     indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
