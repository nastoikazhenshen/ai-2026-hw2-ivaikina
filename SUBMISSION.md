# HW2 submission

**Name: Ivaikina Darya**
**Student ID: S23070567**
**Group: 202610:CSS4007-ENG-10**
**Repository: https://github.com/nastoikazhenshen/ai-2026-hw2-ivaikina**

## AI tool disclosure

State which AI tools you used and for what. Expected and fine; undisclosed use
is not. If you used a model to help you draft a prompt, say which prompt.

>I used ChatGPT to help understand the assignment, explain the task structure, and draft the prompts for the four roles in Sublab Easy.

I also used ChatGPT to help understand and interpret the results of the runs and prepare the answers for `SUBMISSION.md`.

The prompts were drafted with the help of ChatGPT for the following roles:
- `policy_officer`
- `front_desk`
- `auditor`
- `bilingual_clerk`

---

## Sublab Easy — one task, four roles

### Decisions per role

One row per enquiry. In each cell write the `decision` your run returned, and
whether it agrees with `expected` in `data/enquiries.json`:

| Enquiry | policy_officer | front_desk | auditor | bilingual_clerk |
|---|---|---|---|---|
| E-01 | granted | granted | more_info | granted |
| E-02 | more_info | more_info | more_info | more_info |
| E-03 | refused | more_info | more_info | refused |
| E-04 | refused | more_info | refused | refused |
| E-05 | granted | granted | more_info | granted |
| E-06 | granted | granted | more_info | granted |
| E-07 | granted | granted | more_info | granted |
| E-08 | not_found | not_found | not_found | not_found |
| E-09 | refused | more_info | refused | refused |
| E-10 | more_info | more_info | more_info | refused |
| **agrees with `expected`** | 10/10 | 6/10 | 5/10 | 9/10 |
| **parsed** | 10/10 | 10/10 | 10/10 | 10/10 |
| **schema-valid** | 10/10 | 10/10 | 10/10 | 10/10 |

### Which field moved, on which enquiry, under which role

| Field | Enquiries that moved | Role(s) that moved it |
|---|---|---|
| `found` | None | None |
| `decision` | E-01, E-03, E-04, E-05, E-06, E-07, E-09, E-10 | front_desk, auditor, bilingual_clerk |
| `amount` | E-02, E-05, E-06, E-07 | front_desk, auditor |
| `missing_documents` | None | None |

Fields that moved on no enquiry: found and missing_documents.

### Raw replies

Paste the full reply for **one enquiry where a role changed the decision** away
from the policy officer's:

```
{
    "id": "E-03",
    "text": "Student A-203, Madina Zhangeldi — what is the decision on her application?",
    "expected": {
      "applicant_id": "A-203",
      "found": true,
      "decision": "refused",
      "amount": 0,
      "missing_documents": []
    }
  }
```

Paste the full reply for **E-07 (the Kazakh enquiry)** from the bilingual
clerk, so the `reason` language is visible:

```
{
    "id": "E-07",
    "text": "Мен Айгерім Серікпін, A-201. Грант ала аламын ба?",
    "expected": {
      "applicant_id": "A-201",
      "found": true,
      "decision": "granted",
      "amount": 250000,
      "missing_documents": []
    }
  }
```

### Written answers

**1. Which fields are role-sensitive and which are not?** Point at rows in your
tables.

> The most role-sensitive fields were decision and amount. Different roles sometimes returned different values for these fields.
For example, for E-03, the policy officer returned refused, while the front desk and auditor returned more_info.
The found and missing_documents fields were not role-sensitive in this run. They stayed the same for all roles.

**2. Which enquiries are most sensitive to the role, and why those?** Say what
E-03, E-04, E-07 and E-10 are each testing.

>E-03 tests whether the model correctly handles an applicant whose GPA is below the required threshold. The policy officer and bilingual clerk returned refused, while the front desk and auditor returned more_info.

>E-04 tests an applicant whose income band does not meet the policy requirements. The policy officer, auditor, and bilingual clerk returned refused, while the front desk returned more_info.

>E-07 tests the Kazakh-language enquiry. All roles returned granted, but the auditor returned more_info. The bilingual clerk also gave the reason in Kazakh.

>E-10 tests whether the model follows the record instead of an applicant's claim. The applicant says that the ID document was uploaded, but the record does not contain it. The policy officer returned more_info, while the bilingual clerk returned refused.

**3. Where does discretion belong — the role paragraph, or code that reads
`decision` afterwards?** Say what a downstream program can and cannot tell
about which role produced a record.

>In this task, most of the discretion comes from the role instructions. Each role has a different description of how it should behave, so the model can interpret the same case differently.
The code mainly sends the data to the model, parses the answer, and checks the output schema. It does not fully control the decision.
Because of this, the same input can produce different decisions for different roles.

**4. Is a role a boundary?** Say in Week 2 terms what the role paragraph is
made of, and what you would put in code — not in the prompt — if a wrong
`decision` were expensive.

>No, the role paragraph is not a fully reliable boundary because the model can still make a different decision.
If a wrong decision was expensive, I would put the important eligibility rules directly in the code. For example, I would check the GPA, income band, and required documents with deterministic rules.

---

## Sublab Medium — memory you choose

### Tokens per call

| Call | A — never compressed | B — compressed at the `compress` turn |
|---|---:|---:|
| 1 | 120 | 120 |
| 2 | 202 | 239 |
| 3 | 304 | 332 |
| 4 | 420 | 466 |
| 5 | 472 | 545 |
| 6 | 575 | 645 |
| 7 | 702 | 761 |
| 8 | 798 | 854 |
| 9 | 905 | 982 |
| 10 | 970 | 339 |
| 11 | 1097 | 617 |
| **peak** | **1097** | **982** |
| **total for the run** | **6565** | **5900** |

### Probes after the conversation

| Probe | Tests | A retrieved? | A answer | B retrieved? | B answer |
|---|---|---|---|---|---|
| Q-1 identity | turn 1 | Yes | You are Daniyar Qoshan, applicant A-202. | Yes | You are Daniyar Qoshan, applicant A-202. |
| Q-2 missing document | turn 5 | Yes | The id_card is still missing from your official file. | Yes | Your ID card is still missing from your file. |
| Q-3 band and amount | turns 3–4 | Yes | Your reported income band is 2; if officially recorded as band 2, the amount is 150,000 KZT. | Yes | Your income band is Band 2, which corresponds to a grant of 150,000 KZT. |
| Q-4 the constraint | turn 6 | Yes | You said you can come to the office on Thursday. | Yes | You can come to the office on Thursdays. |
| Q-5 the open question | turn 7 | Yes | You asked whether a scanned letter from your employer would count, or whether you had to provide the original. | Yes | You asked whether a scanned letter from your employer would count, or whether the original document is required. |
| **retrieved** | | **5/5** | | **5/5** | |

### The state my compression produced

```
{
  "applicant_id": "A-202",
  "topic": "Study grant eligibility",
  "facts": [
    "The applicant's name is Daniyar Qoshan.",
    "The applicant sent their transcript last week.",
    "The applicant's income band is 2 according to their family's certificate.",
    "The applicant could not upload their id card because their home scanner broke.",
    "The applicant can only come to the office on Thursdays because they have lab all week otherwise.",
    "The applicant's sister, Aruzhan, applied last year and is on file."
  ],
  "decisions": [],
  "constraints": [
    "The applicant can come to the office only on Thursdays."
  ],
  "open_questions": [
    "Does the applicant qualify for the study grant?",
    "Does a scanned letter from the applicant's employer count, or is the original required?",
    "If the applicant brings the id card on Thursday, will the decision be made the same day?"
  ],
  "language": "English and Kazakh"
}
```

### Written answers

**1. What did compression buy?** Peak tokens both ways, probes retrieved both
ways, and — if a probe was lost — which one and which turn it came from.

>Compression reduced the peak from 1097 to 982 tokens and the total from 6565 to 5900 tokens. Both versions retrieved all 5 probes, so no tested information was lost.

**2. Why must the state be structured rather than a paragraph?** You could have
asked for "a summary". Say what changes when the summary is an object with
named fields.

>A structured state separates information into fields like facts, constraints, and open questions. This makes it easier for the program to validate and use the information later.

**3. What is missing from your state that you would add?** Name what you would
add and what you would drop to pay for it.

>I would add a separate documents field to clearly track submitted and missing documents. To keep the state small, I would remove some less important facts, such as information about the sister.

**4. When is compression the wrong choice?** Name a conversation where it would
lose something that cannot be recovered, and say whether your program would
notice.

>Compression can be wrong for a long technical or legal conversation where an old exact detail may be needed later. My program would not automatically notice if an important detail was lost, as long as the generated JSON still passed the schema validation.

---

## Sublab Hard — stories in, CVs out, the best candidate by code

### Part 1 — extraction

| Story | Parsed? | Valid? | Fields that came back `null` | Traps hit |
|---|---|---|---|---|
| story-01 | Yes | Yes | None | None |
| story-02 | Yes | Yes | `graduation_year`, `gpa_4_scale`, `gpa_original`, `gpa_original_scale`, `published_peer_reviewed_outputs` | No GPA stated |
| story-03 | Yes | Yes | None | A GPA on another scale |
| story-04 | Yes | Yes | None | A paper that is not published |
| story-05 | Yes | Yes | None | None |
| story-06 | Yes | Yes | `graduation_year`, `gpa_4_scale`, `gpa_original`, `gpa_original_scale` | A story that contradicts itself |
The four traps, for reference: no GPA stated · a GPA on another scale · a paper
that is not published · a story that contradicts itself.

Paste the extraction for **story-06**, the one that contradicts itself:

```json
{
  "candidate_id": "story-06",
  "full_name": "Nurzhan Abilov",
  "degree": "BSc in Statistics",
  "graduation_year": null,
  "gpa_4_scale": null,
  "gpa_original": null,
  "gpa_original_scale": null,
  "languages": [
    "Kazakh",
    "Russian",
    "English"
  ],
  "published_peer_reviewed_outputs": 1,
  "relevant_experience_months": 40,
  "evidence": {
    "candidate_id": null,
    "full_name": "# Nurzhan Abilov",
    "degree": "I graduated in 2024 with a BSc in Statistics.",
    "graduation_year": null,
    "gpa_4_scale": null,
    "gpa_original": null,
    "gpa_original_scale": null,
    "languages": "Languages: Kazakh, Russian, English.",
    "published_peer_reviewed_outputs": "Research: one paper published, in a peer-reviewed proceedings, on survey weighting.",
    "relevant_experience_months": "I have been at an insurance analytics team since February 2023, which is about forty months."
  },
  "ambiguities": [
    "Graduation status and year are contradictory: the story says the candidate graduated in 2024, but also says they are currently a final-year student graduating in 2026.",
    "GPA is contradictory: the story gives both 3.2 and 3.5, so GPA fields are set to null.",
    "The GPA scale is not stated."
  ]
}
```

### Part 2 — scores and the winner

| Candidate | academic (0–5) | research (0–5) | experience (0–5) | weighted total (code) |
|---|---|---|---|---|
| story-01 | 5 | 5 | 2 | 4.4 |
| story-02 | 1 | 0 | 5 | 1.5 |
| story-03 | 4 | 3 | 3 | 3.5 |
| story-04 | 4 | 3 | 5 | 3.9 |
| story-05 | 5 | 3 | 1 | 3.6 |
| story-06 | 1 | 3 | 5 | 2.4 |

**Winner, computed by my code:**

>story-01

**The model's prose answer, asked separately ("who should win?"):**

>The prose ranking also placed story-01 first. It gave her a weighted total of 4.33 and highlighted her 3.8/4.0 GPA, two confirmed published peer-reviewed outputs, and eight months of relevant experience.


### Part 3 — written answers

**1. Which rule did you have to add, and what broke without it?** Name the
story that forced it.

>I had to add a rule for contradictory GPA values. Story-06 states both 3.2 and 3.5, so the extractor should not choose one or average them. It should return null and record the contradiction in the ambiguities field.

**2. Where did the model guess, and where did your code have to decide?** One
example of each, from your run.

>The model interpreted the GPA in story-03 and converted 4.6/5.0 to 3.68/4.0. My code then decided the candidate's scores using the rubric and calculated the weighted total. For example, story-01 received academic = 5, research = 5, experience = 2, giving a total of 4.4.

**3. Did your prose ranking and your computed ranking agree?** Say which one
you trust and why — and if they agreed, what you would need to see before
trusting the prose one alone.

>Yes, they agreed that story-01 was first. I trust the computed ranking more because the final weighted score is calculated deterministically by my code using the rubric. Before trusting the prose ranking alone, I would want to verify that it uses the same scores, weights, and calculations as the code.

**4. The rubric has no anchor for a contradicted field.** The stories say 3.2
and then 3.5; the rubric defines a 0 and a 5 and nothing in between for this
case. Say what you did and what the rule should be.

>I set the contradicted GPA to null instead of choosing between 3.2 and 3.5, and recorded the contradiction in the ambiguities field. The rule should explicitly say that unresolved conflicting values must be set to null and recorded as an ambiguity. The scoring rubric should also define how an unresolved contradicted field is scored.

**5. How close were your top two candidates?** If they were within 0.05, say
what you would tell the committee and what you would change in the extraction
to make that call defensible.

>My top two candidates were story-01 with 4.4 and story-04 with 3.9, so the difference was 0.50. They were not within 0.05, so the special close-call rule did not apply.

---

## Reflection (optional, one short paragraph)

Having now written a role prompt, compressed a conversation, and ranked six
extractions — what will you do differently the next time you build something
that has to get reliable structured output out of a model?

>The main thing I would do differently is make the extraction schema and validation rules stricter before calculating scores. I would explicitly define how to handle missing, converted, unpublished, and contradictory information, and keep the final scoring deterministic in code rather than letting the model make the final decision.
