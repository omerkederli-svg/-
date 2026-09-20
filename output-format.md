# Output Format Specification

The exact shape of the deliverable. Consult this when the output format is contested, when the user asks for a different layout, or when the notes are unusually shaped (very short, very long, or multiple meetings).

---

## 1. The section skeleton

Four sections, always in this order. Omit none. If a section has no content, keep the heading and state the emptiness explicitly - a missing section is indistinguishable from a forgotten one.

```
## Summary

[3-5 sentences]

## Decisions

- [Decision, with rationale in parentheses if stated]
- [Decision]

## Action Items

| Owner | Action | Due | Status |
|-------|--------|-----|--------|
| [name or UNASSIGNED] | [Verb-first action] | [date, relative form, or TBD] | [Not started / In progress / Done / Blocked] |

## Open Questions

- [Question or unresolved thread] - [who should resolve it, if stated]
```

### Why the order is fixed

Summary first gives the reader the frame. Decisions before actions gives the *what we settled* before the *who does what*. Open Questions last signals it is the residual, not the point. A reader who stops after two sections still gets the two most important things.

---

## 2. Summary

**Length: 3 to 5 sentences. Hard limits.**

| Too short | Right | Too long |
|---|---|---|
| "Discussed pricing." | "The team reviewed the beta pricing options and settled on $49 for the initial cohort. Legal flagged the new ToS as unresolved and it was tabled. Ownership of the signup dashboard remains open ahead of launch." | A paragraph per agenda item, restating who said what, in order. |

### Include

- What was discussed.
- What was decided (at the level of a headline).
- Why it mattered, when the notes make the stakes clear.

### Exclude

- Play-by-play of who spoke when.
- Any content that appears verbatim in the Decisions or Action Items sections.
- Filler ("The meeting was productive", "A good discussion was had").
- Agenda items that were scheduled but never reached, unless they were explicitly deferred.

### Multiple meetings in one input

If the notes cover more than one meeting, produce one record per meeting with the date as a heading, then a combined roll-up table at the end. Do not merge separate meetings into a single summary - the decisions belong to different rooms.

---

## 3. Decisions

One line each. One decision per line, even when two decisions are closely related.

```
- Beta cohort priced at $49; revisit after 100 signups. (Rationale: test lower price point first.)
- Q4 launch moved to November 3. (Rationale: avoids the October holiday freeze.)
```

### Format rules

- Lead with the decision itself, stated as a settled fact - not "it was decided that" or "the team agreed to."
- Rationale goes in parentheses, only when the notes state one.
- No owner column here. A decision is not a task. If executing the decision needs someone to do something, that is an action row.
- If there were no decisions, write `No decisions were reached.` - and resist the urge to promote a debate into this section to fill the space.

---

## 4. Action Items table

### Column spec

| Column | Required | Content | Empty-value convention |
|---|---|---|---|
| Owner | Yes | One name, exactly as written | `UNASSIGNED` (caps, always) |
| Action | Yes | Verb-first instruction, with the object of the verb | Never empty |
| Due | Yes | Calendar date, relative form as stated, `ASAP`, or `TBD` | `TBD` |
| Status | Yes | `Not started` / `In progress` / `Done` / `Blocked` | `Not started` |

**Every cell in every row is filled.** A blank cell reads as an oversight; `UNASSIGNED` and `TBD` read as findings. This is the single most important formatting rule in the skill.

### Row ordering

Default: the order the commitments appear in the source notes. This keeps the table auditable against the source line by line.

When the user asks for prioritisation, sort by Due ascending with `TBD` rows last, then by source order within each date group. Never sort by Status or Owner by default - it scrambles the traceability.

### Column widths and readability

Keep Action text under roughly 80 characters where possible. If an action needs a longer explanation (a blocker chain, a conditional), put the essential verb phrase in the cell and move the elaboration to Open Questions with a reference back to the row.

### Escaping

If the notes contain a pipe character in an action, escape it (`\|`) so the table does not break. Wrap actions containing markdown-significant characters in backticks only as a last resort - backticks make the row harder to read in plain text.

---

## 5. Open Questions

One bullet each. Format: the unresolved thread, then who should resolve it if the notes say, after a dash.

```
- Legal review of the new ToS - tabled; no owner named.
- Ownership of the pricing page copy is ambiguous - named to both Marc and Sarah.
- Whether the beta cap applies to existing customers - raised by Priya, not resolved.
```

### Include

- Questions raised and dropped.
- Disagreements without a settlement.
- Explicit deferrals ("let's discuss offline", "tabled").
- Ownership gaps and conflicts surfaced by the extraction itself - these are findings, not errors, and belong here where a human will see them.
- Conditional decisions ("agreed in principle, pending legal").

### Exclude

- Rhetorical questions that were answered in the meeting.
- Anything you would like to know but the notes do not raise. Adding your own questions makes the record a participant, not a recorder.

---

## 6. Empty and edge cases

### No decisions, no commitments

Keep all four headings. Write `No decisions were reached.` and `No commitments were made.` A meeting that produced nothing is a legitimate, useful result - and often a finding in itself.

### Notes that are already a structured list

If the input is already a clean action list, do not re-derive it. Verify it instead: check every row for owner, verb phrasing, and date, correct what violates the rules, move anything that is actually a decision or a question into the right section, and say what you changed.

### Very long input

For inputs over roughly 5,000 words, work in passes and report the extraction in segments by topic or agenda item, then consolidate. State clearly if any part of the input was not processed - a silently truncated record is worse than an explicitly partial one.

### Input in another language

Preserve the original language for names, quotes, and the action phrasings. Do not translate names. It is fine to write section headings in the user's working language.

---

## 7. Delivery

Return the four-section record directly in the response by default. Produce a separate file only when the user asks for one - and when they do, use `assets/meeting-record-template.md` as the skeleton so the shape stays consistent across records that accumulate in a folder.

When several records accumulate, the filenames matter more than the format: `YYYY-MM-DD - Meeting Name.md`, so they sort chronologically alongside the raw notes.
