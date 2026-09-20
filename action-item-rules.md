# Action Item Rules

The complete rule set for turning a commitment found in meeting notes into a row in the action table. Consult this when a row is ambiguous, when two rules appear to conflict, or when the user disputes a classification.

The guiding principle behind every rule below: **the record must be reconstructable from the raw notes alone.** If a reader cannot point at the source line that justifies a cell's value, the value is wrong.

---

## 1. Owner

### The rule

Exactly one name per action, preserved exactly as written in the notes.

| Situation | Write | Never write |
|---|---|---|
| One person named as owner | `Marc` | `Marc T.` (if notes said `marc`) |
| No owner named | `UNASSIGNED` | A guessed name |
| Two people share it | `Marc` (+ note "joint with Sarah") only if the notes truly assign both | `Marc, Sarah` silently, hiding the split |
| A team is named | The team as written: `design team` | An assumed individual inside it |
| A pronoun only | Look back one sentence for the antecedent; if none is unambiguous, `UNASSIGNED` | `they` or `the team` |

### Why UNASSIGNED is mandatory, not a fallback

An ownerless action is a real, valuable finding. It means the group agreed work was needed and nobody stepped up. Writing `UNASSIGNED` surfaces that in review while it is still fixable. Substituting a plausible name converts a visible gap into an invisible one - and the work dies quietly at the deadline, which is exactly the failure this skill exists to prevent.

### Never infer an owner from these signals

- **The note-taker.** Taking notes is not volunteering to do the work.
- **The meeting organizer.** Convening is not owning.
- **"Whoever mentioned it."** Raising a topic is not committing to it.
- **Seniority.** The most senior person is not the default owner.
- **Prior ownership.** Past ownership of a similar task is not an assignment for this one.
- **The only person present who could do it.** Plausibility is not a source.

### Name preservation

Do not fix capitalization, correct spellings, expand nicknames, or normalize `sarah` to `Sarah` when the notes are inconsistent. Names are identifiers, not prose. Normalizing creates a silent merge of two people who might be distinct; preserving an odd spelling costs nothing and keeps the record auditable against the source.

### Multi-owner actions

If a task genuinely needs two owners, keep one row with the lead owner in the Owner column and record the split in the Action cell: `Send revised SOW to legal (Sarah drafts, Marc reviews)`. Do not create two rows - two rows means two commitments to track, and this is one deliverable.

---

## 2. Action

### The rule

Phrase as a verb-first instruction. The test: **can a person start doing this on Monday morning?**

| Topic (wrong) | Action (right) |
|---|---|
| `Pricing page` | `Send updated pricing page copy to design` |
| `Q3 offsite` | `Book venue for Q3 offsite` |
| `Dashboard` | `Set up the signup dashboard before launch` |
| `Legal review` | `Route the new ToS to legal for review` |
| `Budget question` | `Confirm Q4 budget ceiling with finance` |
| `Migration` | `Draft the migration cutover plan` |

### Verb/noun rewrite lexicon

Common noun forms in meeting notes and the verb that carries the actual work:

| Noun form | Verb-first rewrite |
|---|---|
| decision on X | Decide X |
| approval of X | Approve X |
| review of X | Review X |
| discussion of X | Discuss X / Schedule a discussion on X |
| alignment on X | Align on X / Circulate X for alignment |
| sign-off on X | Obtain sign-off on X |
| follow-up with X | Follow up with X |
| update to X | Update X |
| sync on X | Sync on X / Set up a sync on X |
| investigation of X | Investigate X |

### Specificity

Keep the level of detail the notes support - no more. If the notes say "send the deck to legal," do not write "send the Q4 pricing deck v3 to legal for compliance review." Adding the reviewer, the version, or the purpose is fabrication even when it is likely true.

Conversely, keep the object: "Send the draft" is too thin if the notes said which draft. The action cell should carry the object of the verb wherever the notes named one.

### Preserve the promise's own framing

If the notes quote a person - `marc: "I'll get the updated pricing page copy to design by Thursday"` - the action cell should read close to `Send updated pricing page copy to design`, converting first person to the imperative. Do not re-scope it into something broader or narrower.

---

## 3. Due

### The rule

Only write a date when the notes state one, or when a relative date can be resolved. Otherwise write `TBD`.

| Notes say | Meeting date known? | Write |
|---|---|---|
| `by Thursday` | Yes (meeting was Mon 2026-03-02) | The resolved calendar date |
| `by Thursday` | No | `Thursday` - keep the relative form exactly |
| `end of month` | Yes, and month is unambiguous | The resolved date |
| `soon` | - | `TBD` |
| `ASAP` | - | `ASAP` (it is stated urgency, not a date) |
| `next sprint` | Only if sprint boundaries are supplied | Otherwise `next sprint` |
| nothing | - | `TBD` |

### Do not infer urgency

`TBD` is not a failure to be fixed by guessing a sensible date. A guessed due date that turns out to be wrong costs trust in every other cell in the table. If the user needs the date, the correct move is to say which actions are undated so they can go ask - not to fill it in.

### Relative dates

A relative date like "Friday" is only resolvable when the meeting date is known. Resolve it to a calendar date and, for clarity, you may keep the original in parentheses: `2026-03-06 (Friday)`. When the meeting date is not known, keep `Friday` verbatim - resolving it against today's date is wrong, because the notes may be a week old.

### Dates that were discussed but not promised

"Revisit after 100 signups" is a trigger condition, not a due date. Record it in the Decisions line (`revisit after 100 signups`) rather than pressing a date into the Due column.

---

## 4. Status

The default is `Not started`. Override only on explicit evidence in the notes.

| Notes say | Status |
|---|---|
| nothing about progress | `Not started` |
| `I already sent it` / `in progress` | `In progress` |
| `done` / `finished` | `Done` |
| `blocked on legal` | `Blocked` - and note the blocker in the Action cell if it is not already there |
| `waiting for X` | `Blocked` or `Waiting` - pick one and stay consistent within the document |

Do not upgrade status because the deadline is close, because the owner is diligent, or because the work seems trivial. Status is a report from the source, not an inference about people.

### Blocked items

A blocked commitment is still a commitment and still belongs in the table - it is among the most valuable rows, because the blocker is usually what needs unblocking. Keep owner and due date; add the blocker where the notes put it.

---

## 5. De-duplication

Collapse repeated mentions of the same commitment into one row.

### Merge rule

Keep:
- the **most specific phrasing** of the action, and
- the **latest stated date**.

Discard earlier, vaguer mentions.

### Recognising a duplicate

Two mentions are the same commitment when they share owner **and** object of the verb, even if the wording differs:

```
- marc: "I'll get the updated pricing page copy to design by Thursday"
- also sarah mentioned the pricing page again later, marc said "yeah yeah Thursday"
```

One row: `Marc | Send updated pricing page copy to design | Thursday | Not started`.

### Not duplicates

- Same object, different owner - two rows (and one of them may be an ownership conflict worth flagging).
- Same owner, different object - two rows.
- A commitment and a decision about the same thing - one action row, one decision line. They live in different sections; that is not duplication.

### Ownership conflicts

If two people are named as owner of the same deliverable across the notes, do not silently pick one. Keep the row with whichever owner is better evidenced and flag the conflict in Open Questions: `Ownership of the pricing page copy is ambiguous - named to both Marc and Sarah.`

### Recurring commitments

A standing commitment (`we'll review this weekly`) is not a single action. Either record it once with an explicit recurring framing in the Action cell (`Run the weekly pricing review`) or move it to Open Questions if no owner was set. Do not emit one row per recurrence.

---

## 6. Decisions vs. Open Questions

The dividing line is **settlement**, not enthusiasm.

| The notes | Lands in |
|---|---|
| `decided: go with $49` | Decisions |
| `we're going with quarterly billing` | Decisions |
| `sarah thinks we should test $49, marc pushing $59` | Open Questions (unsettled) |
| `tabled` | Open Questions |
| `let's discuss offline` | Open Questions |
| `agreed in principle, pending legal` | Open Questions - conditional, not done |
| `no decision, revisit next week` | Open Questions |

A strong-sounding opinion is not a decision. The most common error in meeting records is promoting the loudest position to a conclusion, which then gets executed in a direction nobody actually agreed to.

### Decisions with rationale

Record the rationale when the notes state one, in parentheses: `Beta cohort priced at $49; revisit after 100 signups. (Rationale: test lower price point first.)` If no rationale was given, do not supply one.

---

## 7. Thin notes

If the material has no verbs and no names, it is not extractable. Say so plainly and return only what is genuinely there - typically a partial summary and an Open Questions list. Do not pad the table with inferred work to make the output look complete. An honest three-line record beats a speculative fifteen-row one.
